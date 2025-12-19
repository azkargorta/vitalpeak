from __future__ import annotations

import math
import tempfile
from typing import Any, Literal, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

try:
    import mediapipe as mp
except Exception as e:  # pragma: no cover
    mp = None
    _MP_IMPORT_ERROR = e
else:
    _MP_IMPORT_ERROR = None


Exercise = Literal["squat", "deadlift", "bench_press"]


app = FastAPI(title="VitalPeak Posture Service", version="0.1.0")


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle ABC (degrees)."""
    ba = a - b
    bc = c - b
    nba = np.linalg.norm(ba)
    nbc = np.linalg.norm(bc)
    if nba == 0 or nbc == 0:
        return 180.0
    cosang = float(np.clip(np.dot(ba, bc) / (nba * nbc), -1.0, 1.0))
    return math.degrees(math.acos(cosang))


def _torso_angle_deg(hip: np.ndarray, shoulder: np.ndarray) -> float:
    """Angle of torso vs vertical (degrees, 0 = perfectly vertical)."""
    v = shoulder - hip
    nv = np.linalg.norm(v)
    if nv == 0:
        return 0.0
    vertical = np.array([0.0, -1.0])  # up
    v2 = np.array([v[0], v[1]]) / nv
    cosang = float(np.clip(np.dot(v2, vertical), -1.0, 1.0))
    return abs(math.degrees(math.acos(cosang)))


def _pick_side(lms: list[Any]) -> str:
    """Pick left/right side based on landmark visibility."""
    if mp is None:
        return "right"
    PL = mp.solutions.pose.PoseLandmark
    left_ids = [PL.LEFT_HIP, PL.LEFT_KNEE, PL.LEFT_ANKLE, PL.LEFT_SHOULDER, PL.LEFT_ELBOW, PL.LEFT_WRIST]
    right_ids = [PL.RIGHT_HIP, PL.RIGHT_KNEE, PL.RIGHT_ANKLE, PL.RIGHT_SHOULDER, PL.RIGHT_ELBOW, PL.RIGHT_WRIST]

    def score(ids):
        s = 0.0
        for i in ids:
            lm = lms[int(i)]
            s += float(getattr(lm, "visibility", 0.0) or 0.0)
        return s

    return "left" if score(left_ids) >= score(right_ids) else "right"


def _lm_xy(lms: list[Any], which: str, name: str) -> tuple[np.ndarray, float]:
    """Return (xy, visibility). xy is normalized [0..1]."""
    PL = mp.solutions.pose.PoseLandmark
    idx = {
        ("left", "hip"): PL.LEFT_HIP,
        ("left", "knee"): PL.LEFT_KNEE,
        ("left", "ankle"): PL.LEFT_ANKLE,
        ("left", "shoulder"): PL.LEFT_SHOULDER,
        ("left", "elbow"): PL.LEFT_ELBOW,
        ("left", "wrist"): PL.LEFT_WRIST,
        ("right", "hip"): PL.RIGHT_HIP,
        ("right", "knee"): PL.RIGHT_KNEE,
        ("right", "ankle"): PL.RIGHT_ANKLE,
        ("right", "shoulder"): PL.RIGHT_SHOULDER,
        ("right", "elbow"): PL.RIGHT_ELBOW,
        ("right", "wrist"): PL.RIGHT_WRIST,
    }[(which, name)]
    lm = lms[int(idx)]
    return np.array([float(lm.x), float(lm.y)], dtype=np.float32), float(getattr(lm, "visibility", 0.0) or 0.0)


def _signal_reps(y: list[float], min_amp: float = 0.06) -> int:
    """Very simple rep estimator based on peak/valley cycles."""
    if len(y) < 8:
        return 0
    y = np.array(y, dtype=np.float32)
    y_s = np.convolve(y, np.ones(5) / 5, mode="same")
    dy = np.diff(y_s)
    # valley when dy goes negative->positive
    reps = 0
    last_valley = None
    for i in range(1, len(dy)):
        if dy[i - 1] < 0 and dy[i] >= 0:
            valley = float(y_s[i])
            if last_valley is None:
                last_valley = valley
                continue
            # amplitude since last valley
            amp = abs(valley - last_valley)
            if amp >= min_amp:
                reps += 1
                last_valley = valley
    return reps


def _analyze(video_path: str, exercise: Exercise) -> dict[str, Any]:
    if mp is None:
        raise RuntimeError(f"mediapipe no importable: {_MP_IMPORT_ERROR}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "exercise": exercise,
            "camera": "side",
            "status": "no_eval",
            "score": 20,
            "top_cues": [{"title": "No pude abrir el vídeo", "detail": "Revisa el formato y vuelve a intentarlo."}],
            "keyframes": [{"label": "start", "notes": ""}, {"label": "mid", "notes": ""}, {"label": "end", "notes": ""}],
            "metrics": {},
        }

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = (total / fps) if fps else 0

    # sample up to ~180 frames
    max_frames = 180
    stride = max(1, int(round(total / max_frames))) if total else 1

    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    hip_y_series: list[float] = []
    wrist_y_series: list[float] = []

    torso_max = 0.0
    knee_forward_max = 0.0
    depth_best = -1.0

    back_neutral_min = 180.0
    bar_drift_max = 0.0
    wrist_stack_max = 0.0

    ok_frames = 0
    i = 0
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        if i % stride != 0:
            i += 1
            continue
        i += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = pose.process(rgb)
        if not res.pose_landmarks:
            continue
        lms = res.pose_landmarks.landmark
        side = _pick_side(lms)

        hip, v_hip = _lm_xy(lms, side, "hip")
        knee, v_knee = _lm_xy(lms, side, "knee")
        ankle, v_ankle = _lm_xy(lms, side, "ankle")
        shoulder, v_sh = _lm_xy(lms, side, "shoulder")
        elbow, v_el = _lm_xy(lms, side, "elbow")
        wrist, v_wr = _lm_xy(lms, side, "wrist")

        vis = min(v_hip, v_knee, v_ankle, v_sh)
        if vis < 0.35:
            continue

        ok_frames += 1

        # common signals
        hip_y_series.append(float(hip[1]))
        wrist_y_series.append(float(wrist[1]))

        # squat-specific
        if exercise == "squat":
            torso = _torso_angle_deg(hip, shoulder)
            torso_max = max(torso_max, torso)
            knee_forward = abs(float(knee[0] - ankle[0]))
            knee_forward_max = max(knee_forward_max, knee_forward)
            depth = float(hip[1] - knee[1])  # >0 means hip lower than knee
            depth_best = max(depth_best, depth)

        # deadlift-specific
        if exercise == "deadlift":
            # back neutral proxy: angle shoulder-hip-knee (closer to 180 is straighter)
            back_ang = _angle(shoulder, hip, knee)
            back_neutral_min = min(back_neutral_min, back_ang)
            bar_drift = abs(float(wrist[0] - hip[0]))
            bar_drift_max = max(bar_drift_max, bar_drift)

        # bench-specific (very approximate)
        if exercise == "bench_press":
            wrist_stack = abs(float(wrist[0] - elbow[0]))
            wrist_stack_max = max(wrist_stack_max, wrist_stack)

        if ok_frames >= max_frames:
            break

    cap.release()
    pose.close()

    # basic quality gate
    if ok_frames < 10:
        return {
            "exercise": exercise,
            "camera": "side",
            "status": "no_eval",
            "score": 25,
            "top_cues": [
                {
                    "title": "No se puede evaluar",
                    "detail": "No se detecta bien el cuerpo. Regraba en lateral, con el cuerpo entero y buena luz.",
                }
            ],
            "keyframes": [{"label": "start", "notes": ""}, {"label": "mid", "notes": ""}, {"label": "end", "notes": ""}],
            "metrics": {"ok_frames": ok_frames, "duration_sec": int(round(duration)) if duration else None},
        }

    # rep estimation
    if exercise == "bench_press":
        reps_est = _signal_reps(wrist_y_series, min_amp=0.035)
    else:
        reps_est = _signal_reps(hip_y_series, min_amp=0.05)

    # score + cues
    score = 90
    cues: list[tuple[int, str, str]] = []  # (penalty, title, detail)
    metrics: dict[str, Any] = {
        "reps_est": int(reps_est),
        "duration_sec": int(round(duration)) if duration else None,
        "ok_frames": int(ok_frames),
        "torso_angle_max_deg": round(float(torso_max), 1),
        "knee_forward_max": "unknown",
        "rom": "unknown",
        "back_neutral_proxy": "unknown",
        "bar_path_proxy": "unknown",
    }

    if exercise == "squat":
        # depth heuristic
        if depth_best < 0.02:
            score -= 18
            cues.append((18, "Rango de movimiento", "Baja un poco más si tu movilidad lo permite (cadera al nivel de la rodilla o ligeramente por debajo)."))
            metrics["rom"] = "short"
        else:
            metrics["rom"] = "ok"

        if torso_max > 35:
            score -= 12
            cues.append((12, "Torso más estable", "Reduce la inclinación del tronco y mantén la espalda neutra durante la bajada/subida."))

        if knee_forward_max > 0.09:
            score -= 6
            cues.append((6, "Rodilla y equilibrio", "Controla que la rodilla no se desplace demasiado hacia delante: busca equilibrio medio-pie."))
            metrics["knee_forward_max"] = "high"
        else:
            metrics["knee_forward_max"] = "ok"

    elif exercise == "deadlift":
        if back_neutral_min < 155:
            score -= 18
            cues.append((18, "Espalda neutra", "Evita redondear la espalda: piensa en 'pecho arriba' y tensión en dorsales antes de despegar."))
            metrics["back_neutral_proxy"] = "risk"
        else:
            metrics["back_neutral_proxy"] = "ok"

        if bar_drift_max > 0.13:
            score -= 10
            cues.append((10, "Barra más pegada", "Mantén la barra cerca del cuerpo (rozando la pierna) para mejorar palanca y seguridad."))
            metrics["bar_path_proxy"] = "drifts"
        else:
            metrics["bar_path_proxy"] = "ok"

        # torso angle metric can be useful too
        metrics["torso_angle_max_deg"] = round(float(torso_max), 1)

    else:  # bench_press
        if wrist_stack_max > 0.075:
            score -= 12
            cues.append((12, "Muñeca sobre codo", "Apila muñeca sobre codo para empujar más estable y reducir estrés articular."))

        metrics["bar_path_proxy"] = "unknown"  # no bar tracking in MVP
        metrics["back_neutral_proxy"] = "unknown"
        metrics["rom"] = "unknown"
        metrics["knee_forward_max"] = "unknown"

    score = max(20, min(100, score))
    cues.sort(key=lambda x: x[0], reverse=True)
    top = [{"title": t, "detail": d} for _, t, d in cues[:3]]

    if score >= 80:
        status = "ok" if len(top) <= 1 else "improve"
    else:
        status = "improve"

    # simple keyframe notes (kept short)
    keyframes = [
        {"label": "start", "notes": "Inicio: postura y colocación."},
        {"label": "mid", "notes": "Parte media: controla el recorrido."},
        {"label": "end", "notes": "Final: bloqueo estable."},
    ]

    return {
        "exercise": exercise,
        "camera": "side",
        "status": status,
        "score": int(score),
        "top_cues": top,
        "keyframes": keyframes,
        "metrics": metrics,
    }


@app.post("/analyze")
async def analyze(
    exercise: Exercise = Form(...),
    camera: str = Form("side"),
    video: UploadFile = File(...),
) -> dict[str, Any]:
    if mp is None:
        raise HTTPException(status_code=500, detail=f"mediapipe no disponible: {_MP_IMPORT_ERROR}")
    if camera != "side":
        raise HTTPException(status_code=400, detail="Solo se acepta cámara lateral (side) en el MVP")

    raw = await video.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Vídeo vacío")

    # Write temp file
    suffix = ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(raw)
        path = f.name

    try:
        return _analyze(path, exercise)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
