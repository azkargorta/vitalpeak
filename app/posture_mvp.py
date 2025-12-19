from __future__ import annotations

import base64
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass
from typing import Any, Literal, Optional

import cv2

from openai import OpenAI

from .supabase_utils import (
    db_delete,
    db_insert,
    db_select,
    get_supabase_bucket,
    get_supabase_client,
    supabase_config_status,
    storage_remove,
    storage_signed_url,
    storage_upload_bytes,
)


Exercise = Literal["squat", "deadlift", "bench_press"]


@dataclass
class PostureResult:
    analysis: dict[str, Any]
    analysis_id: str
    video_url: str
    keyframe_urls: dict[str, str]


def _b64_jpeg(img_bgr) -> bytes:
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("No se pudo codificar el frame a JPG")
    return bytes(buf)


def extract_keyframes(video_path: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Extract 3 keyframes (start/mid/end) from a video.

    This is intentionally simple for MVP. We also return basic metadata.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir el vídeo")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = (total / fps) if fps else 0

    if total <= 0:
        raise RuntimeError("Vídeo sin frames")

    # 10%, 50%, 90%
    idxs = {
        "start": max(0, int(total * 0.10)),
        "mid": max(0, int(total * 0.50)),
        "end": max(0, int(total * 0.90)),
    }

    frames: dict[str, bytes] = {}
    for label, idx in idxs.items():
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok or frame is None:
            # fallback: try read sequentially
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok2, frame2 = cap.read()
            if not ok2 or frame2 is None:
                raise RuntimeError("No se pudo leer frames del vídeo")
            frame = frame2
        frames[label] = _b64_jpeg(frame)
    cap.release()

    meta = {
        "fps": float(fps) if fps else None,
        "total_frames": int(total),
        "duration_sec": int(round(duration)) if duration else None,
    }
    return frames, meta


def _vision_prompt(exercise: Exercise) -> str:
    # Simple MVP prompt: 3 cues max, lateral camera.
    exercise_name = {
        "squat": "sentadilla",
        "deadlift": "peso muerto",
        "bench_press": "press banca",
    }[exercise]
    return (
        "Eres un entrenador personal experto.\n"
        "Vas a evaluar un ejercicio grabado con cámara lateral (90°).\n"
        f"Ejercicio: {exercise_name}.\n\n"
        "Devuelve SOLO JSON válido con ESTE esquema (sin markdown, sin texto extra):\n"
        "{\n"
        "  \"exercise\": \"squat|deadlift|bench_press\",\n"
        "  \"camera\": \"side\",\n"
        "  \"status\": \"ok|improve|no_eval\",\n"
        "  \"score\": 0-100,\n"
        "  \"top_cues\": [\n"
        "    {\"title\": \"...\", \"detail\": \"...\"}\n"
        "  ],\n"
        "  \"keyframes\": [\n"
        "    {\"label\": \"start\", \"notes\": \"...\"},\n"
        "    {\"label\": \"mid\", \"notes\": \"...\"},\n"
        "    {\"label\": \"end\", \"notes\": \"...\"}\n"
        "  ],\n"
        "  \"metrics\": {\n"
        "    \"reps_est\": 0,\n"
        "    \"rom\": \"ok|short|unknown\",\n"
        "    \"torso_angle_max_deg\": 0,\n"
        "    \"knee_forward_max\": \"ok|high|unknown\",\n"
        "    \"back_neutral_proxy\": \"ok|risk|unknown\",\n"
        "    \"bar_path_proxy\": \"ok|drifts|unknown\"\n"
        "  }\n"
        "}\n\n"
        "REGLAS:\n"
        "- Si no puedes evaluar con fiabilidad (no se ve cuerpo entero/pies/barra, mala luz, encuadre malo), status=no_eval y score<=40.\n"
        "- top_cues: máximo 3 elementos (si status=ok, pueden ser 0-1 cues tipo refinamiento).\n"
        "- Sé concreto y accionable.\n"
    )


def _safe_json_load(s: str) -> Optional[dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        # try to extract first JSON object
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start : end + 1])
            except Exception:
                return None
        return None


def analyze_and_store_posture(
    *,
    user_id: str,
    exercise: Exercise,
    video_bytes: bytes,
    vision_model: str = "gpt-4o-mini",
    openai_api_key: Optional[str] = None,
    signed_url_ttl_sec: int = 3600,
) -> PostureResult:
    """MVP: Extract 3 frames, ask vision model for JSON feedback, store in Supabase."""

    # --- Supabase config
    sb = get_supabase_client()
    if sb is None:
        st = supabase_config_status()
        # Don't leak secrets values; only show which keys are present.
        raise RuntimeError(
            "Supabase no está configurado o no se detectan las claves necesarias. "
            "Configura en Streamlit Secrets SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY (o SUPABASE_SERVICE_KEY). "
            "También acepto formato anidado TOML [supabase] url=... service_role_key=... . "
            f"Detectado: has_url={st.get('has_url')}, has_key={st.get('has_key')}, "
            f"keys={st.get('secrets_keys', [])}"
        )
    bucket = get_supabase_bucket("posture")

    # --- Save video temp
    tmpdir = tempfile.mkdtemp(prefix="vitalpeak_posture_")
    video_path = os.path.join(tmpdir, "upload.mp4")
    with open(video_path, "wb") as f:
        f.write(video_bytes)

    # --- Extract frames
    frames, meta = extract_keyframes(video_path)

    # --- Vision request
    api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY (Streamlit Secrets)")
    client = OpenAI(api_key=api_key)

    # Build multi-part message with 3 images
    content = [
        {"type": "text", "text": _vision_prompt(exercise)},
        {
            "type": "text",
            "text": "Frames (start/mid/end) del mismo vídeo. Evalúa la técnica global.",
        },
    ]
    for lbl in ["start", "mid", "end"]:
        b64 = base64.b64encode(frames[lbl]).decode("utf-8")
        content.append({"type": "text", "text": f"Frame: {lbl}"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            }
        )

    resp = client.chat.completions.create(
        model=vision_model,
        messages=[{"role": "user", "content": content}],
        temperature=0.2,
        max_tokens=900,
    )
    text = (resp.choices[0].message.content or "").strip()
    analysis = _safe_json_load(text)

    if not isinstance(analysis, dict):
        analysis = {
            "exercise": exercise,
            "camera": "side",
            "status": "no_eval",
            "score": 20,
            "top_cues": [
                {
                    "title": "No pude leer el resultado",
                    "detail": "Vuelve a intentarlo. Asegúrate de que se ve el cuerpo entero, pies y barra (si aplica).",
                }
            ],
            "keyframes": [
                {"label": "start", "notes": ""},
                {"label": "mid", "notes": ""},
                {"label": "end", "notes": ""},
            ],
            "metrics": {
                "reps_est": 0,
                "rom": "unknown",
                "torso_angle_max_deg": 0,
                "knee_forward_max": "unknown",
                "back_neutral_proxy": "unknown",
                "bar_path_proxy": "unknown",
            },
        }

    # normalize fields
    analysis.setdefault("exercise", exercise)
    analysis.setdefault("camera", "side")
    analysis.setdefault("top_cues", [])
    analysis.setdefault("keyframes", [])
    analysis.setdefault("metrics", {})
    # enforce top_cues max 3
    if isinstance(analysis.get("top_cues"), list):
        analysis["top_cues"] = analysis["top_cues"][:3]

    # --- Store to Supabase
    analysis_id = str(uuid.uuid4())
    ts = int(time.time())
    base_prefix = f"{user_id}/{analysis_id}_{ts}"
    video_key = f"videos/{base_prefix}.mp4"
    kf_keys = {
        "start": f"keyframes/{base_prefix}_start.jpg",
        "mid": f"keyframes/{base_prefix}_mid.jpg",
        "end": f"keyframes/{base_prefix}_end.jpg",
    }

    storage_upload_bytes(sb, bucket, video_key, video_bytes, "video/mp4", upsert=True)
    for lbl, key in kf_keys.items():
        storage_upload_bytes(sb, bucket, key, frames[lbl], "image/jpeg", upsert=True)

    row = {
        "user_id": user_id,
        "exercise": exercise,
        "camera": "side",
        "status": analysis.get("status", "no_eval"),
        "score": int(analysis.get("score", 0) or 0),
        "top_cues": analysis.get("top_cues", []),
        "metrics": analysis.get("metrics", {}),
        "video_path": video_key,
        "keyframes": [
            {"label": "start", "path": kf_keys["start"]},
            {"label": "mid", "path": kf_keys["mid"]},
            {"label": "end", "path": kf_keys["end"]},
        ],
        "duration_sec": meta.get("duration_sec"),
        "model_version": "mvp_openai_vision_v1",
    }

    inserted = db_insert(sb, "posture_analyses", row)
    # inserted may be list with one element
    if isinstance(inserted, list) and inserted:
        db_id = inserted[0].get("id")
    elif isinstance(inserted, dict):
        db_id = inserted.get("id")
    else:
        db_id = None
    if db_id:
        analysis_id = str(db_id)

    video_url = storage_signed_url(sb, bucket, video_key, expires_sec=signed_url_ttl_sec)
    keyframe_urls = {lbl: storage_signed_url(sb, bucket, key, expires_sec=signed_url_ttl_sec) for lbl, key in kf_keys.items()}

    return PostureResult(
        analysis=analysis,
        analysis_id=analysis_id,
        video_url=video_url,
        keyframe_urls=keyframe_urls,
    )


def list_posture_history(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase_client()
    if sb is None:
        return []
    # supabase-py doesn't expose ORDER BY easily via helper; use query builder
    res = (
        sb.table("posture_analyses")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def get_signed_urls_for_record(record: dict[str, Any], ttl_sec: int = 3600) -> tuple[str, dict[str, str]]:
    sb = get_supabase_client()
    if sb is None:
        return "", {}
    bucket = get_supabase_bucket("posture")
    video_path = record.get("video_path") or ""
    video_url = storage_signed_url(sb, bucket, video_path, expires_sec=ttl_sec) if video_path else ""
    kf_urls: dict[str, str] = {}
    for kf in (record.get("keyframes") or []):
        lbl = kf.get("label")
        path = kf.get("path")
        if lbl and path:
            kf_urls[str(lbl)] = storage_signed_url(sb, bucket, str(path), expires_sec=ttl_sec)
    return video_url, kf_urls


def delete_posture_record(user_id: str, record_id: str) -> None:
    sb = get_supabase_client()
    if sb is None:
        return
    bucket = get_supabase_bucket("posture")
    # Read record to get paths
    recs = (
        sb.table("posture_analyses")
        .select("*")
        .eq("id", record_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    ).data
    if not recs:
        return
    rec = recs[0]
    paths: list[str] = []
    if rec.get("video_path"):
        paths.append(rec["video_path"])
    for kf in (rec.get("keyframes") or []):
        if kf.get("path"):
            paths.append(kf["path"])
    storage_remove(sb, bucket, paths)
    db_delete(sb, "posture_analyses", id=record_id, user_id=user_id)
