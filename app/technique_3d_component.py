from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st
import streamlit.components.v1 as components
import html as html_lib
import os

# Compat: Streamlit versions may not have cache_data
def _cache_data(**kwargs):
    if hasattr(st, 'cache_data'):
        return st.cache_data(**kwargs)  # type: ignore[attr-defined]
    if hasattr(st, 'cache'):
        return st.cache(**{k:v for k,v in kwargs.items() if k in {'show_spinner'}})  # type: ignore[attr-defined]
    # no-op decorator
    def _decorator(fn):
        return fn
    return _decorator



def _assets_dir() -> Path:
    return Path("assets")


@_cache_data(show_spinner=False)
def _read_glb_base64(glb_path: str) -> str:
    p = Path(glb_path)
    b = p.read_bytes()
    return base64.b64encode(b).decode("ascii")


def render_mannequin_3d(exercise_id: str, cues: List[str] | None = None) -> None:
    """
    Renderiza una mini-animación 3D (frontal + lateral) usando un maniquí GLB.

    Requiere colocar el archivo en:
      assets/3d/mannequin.glb
    """
    try:
        cues = cues or []
        glb_file = _assets_dir() / "3d" / "mannequin.glb"
        if not glb_file.exists():
            st.write("⚠️ Falta el modelo 3D. Coloca `mannequin.glb` en `assets/3d/mannequin.glb`.")
            st.text(str(glb_file))
            return
        # Si es enorme, avisa (en móvil puede ir lento). Usamos os.path.getsize por compatibilidad.
        try:
            size_mb = os.path.getsize(glb_file) / (1024 * 1024)
            if size_mb > 15:
                st.write(f"⚠️ El GLB pesa ~{size_mb:.1f} MB. En móvil puede ir lento; intenta bajarlo a 2–10 MB.")
        except Exception:
            # Si falla el size (entornos raros), no bloqueamos el render.
            pass

    
        glb_b64 = _read_glb_base64(str(glb_file))
    
        # Config simple por ejercicio (ROM/tempo). Ajustable.
        ex_cfg: Dict[str, Any] = {
            "bench_press": {"name": "Press banca", "mode": "bench"},
            "squat": {"name": "Sentadilla", "mode": "squat"},
            "deadlift": {"name": "Peso muerto", "mode": "hinge"},
        }
        cfg = ex_cfg.get(exercise_id, {"name": exercise_id, "mode": "generic"})
    
        # Cues: normalizamos para evitar fallos con truthiness/slicing de tipos raros
        cues_list: List[str] = []
        try:
            if cues is None:
                cues_list = []
            elif isinstance(cues, (list, tuple)):
                cues_list = [str(x) for x in cues]
            elif isinstance(cues, str):
                cues_list = [cues]
            else:
                # iterable cualquiera
                cues_list = [str(x) for x in list(cues)]
        except Exception:
            cues_list = []
    
        cues_list = [c.strip() for c in cues_list if c is not None and str(c).strip()][:4]
        cues_html = "".join([f"<li>{html_lib.escape(c)}</li>" for c in cues_list])
        cues_block = (
            f"<ul style='margin:6px 0 0 18px; padding:0; font-size:12px; opacity:.9'>{cues_html}</ul>"
            if len(cues_list) > 0 else ""
        )
    
    
        # Nota: usamos Three.js por CDN para simplicidad. Si quieres offline, se puede empaquetar.
        page_html = f\"\"\"
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body {{ margin: 0; font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial; }}
  .wrap {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 10px; }}
  .panel {{ border: 1px solid rgba(0,0,0,.12); border-radius: 12px; overflow: hidden; position: relative; background: #fff; }}
  .title {{ position:absolute; left:10px; top:10px; font-size:12px; opacity:.85; background: rgba(255,255,255,.85); padding: 4px 8px; border-radius: 999px; }}
  canvas {{ width: 100%; height: 260px; display:block; }}
  .foot {{ padding: 0 10px 10px 10px; font-size: 12px; opacity:.85; }}
  @media (max-width: 720px) {{
        .wrap {{ grid-template-columns: 1fr; }}
        canvas {{ height: 240px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="panel">
        <div class="title">Frontal</div>
        <canvas id="c1"></canvas>
        <div class="foot"><b>{cfg["name"]}</b>{cues_block}</div>
  </div>
  <div class="panel">
        <div class="title">Lateral</div>
        <canvas id="c2"></canvas>
        <div class="foot"><span style="opacity:.9">Modo:</span> {cfg["mode"]}</div>
  </div>
</div>
    
<script type="module">
import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import {{ GLTFLoader }} from "https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js";
    
const isMobile = window.matchMedia && window.matchMedia("(max-width: 720px)").matches;
const maxDPR = isMobile ? 1.25 : 2.0;
    
function b64ToArrayBuffer(b64) {{
  const binary = atob(b64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i=0; i<len; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}}
    
function makeRenderer(canvas) {{
  const r = new THREE.WebGLRenderer({{ canvas, antialias: !isMobile, alpha: true }});
  r.setPixelRatio(Math.min(window.devicePixelRatio || 1, maxDPR));
  r.setSize(canvas.clientWidth, canvas.clientHeight, false);
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.ACESFilmicToneMapping;
  r.toneMappingExposure = 1.0;
  r.shadowMap.enabled = !isMobile; // sombras solo en desktop
  r.shadowMap.type = THREE.PCFSoftShadowMap;
  return r;
}}
    
function makeCamera(kind) {{
  const cam = new THREE.PerspectiveCamera(35, 1, 0.01, 100);
  if (kind === "front") {{
        cam.position.set(0, 1.55, 3.2);
  }} else {{
        cam.position.set(3.2, 1.55, 0);
  }}
  cam.lookAt(0, 1.1, 0);
  return cam;
}}
    
const canvas1 = document.getElementById("c1");
const canvas2 = document.getElementById("c2");
const renderer1 = makeRenderer(canvas1);
const renderer2 = makeRenderer(canvas2);
    
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);
    
const key = new THREE.DirectionalLight(0xffffff, 1.1);
key.position.set(2.5, 4.0, 2.5);
key.castShadow = !isMobile;
scene.add(key);
    
const fill = new THREE.DirectionalLight(0xffffff, 0.6);
fill.position.set(-2.5, 2.0, 1.0);
scene.add(fill);
    
const rim = new THREE.DirectionalLight(0xffffff, 0.35);
rim.position.set(-2.5, 3.0, -2.5);
scene.add(rim);
    
const amb = new THREE.AmbientLight(0xffffff, 0.35);
scene.add(amb);
    
// Suelo
const floorGeo = new THREE.PlaneGeometry(10, 10);
const floorMat = new THREE.MeshStandardMaterial({{ color: 0xf4f4f4, roughness: 1.0, metalness: 0.0 }});
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI / 2;
floor.position.y = 0;
floor.receiveShadow = !isMobile;
scene.add(floor);
    
const cameraFront = makeCamera("front");
const cameraSide = makeCamera("side");
    
// Carga GLB desde base64
const loader = new GLTFLoader();
const arrayBuffer = b64ToArrayBuffer("{glb_b64}");
let mannequin = null;
let bones = {{}};
let joints = [];
    
function findBone(root, patterns) {{
  // patterns: array of regex strings
  let found = null;
  root.traverse((o) => {{
        if (!o.isBone || found) return;
        const n = (o.name || "").toLowerCase();
        for (const p of patterns) {{
          const r = new RegExp(p);
          if (r.test(n)) {{ found = o; break; }}
        }}
  }});
  return found;
}}
    
function addJointMarker(color=0x111111) {{
  const g = new THREE.SphereGeometry(0.03, 16, 16);
  const m = new THREE.MeshStandardMaterial({{ color, roughness: 0.7, metalness: 0.0 }});
  const s = new THREE.Mesh(g, m);
  s.castShadow = !isMobile;
  scene.add(s);
  return s;
}}
    
function attachMarkers() {{
  joints = [];
  const defs = [
        ["hip", bones.hips],
        ["kneeL", bones.kneeL],
        ["kneeR", bones.kneeR],
        ["elbowL", bones.elbowL],
        ["elbowR", bones.elbowR],
        ["shoulderL", bones.shoulderL],
        ["shoulderR", bones.shoulderR],
  ];
  for (const [id, b] of defs) {{
        if (!b) continue;
        joints.push({{ id, bone: b, marker: addJointMarker(0x222222) }});
  }}
}}
    
function addTrajectoryArrow() {{
  // Flecha genérica; se ajusta según modo
  const dir = new THREE.Vector3(0, 1, 0);
  const origin = new THREE.Vector3(0, 1.0, 0);
  const len = 0.7;
  const arrow = new THREE.ArrowHelper(dir, origin, len, 0x000000);
  scene.add(arrow);
  return arrow;
}}
const arrow = addTrajectoryArrow();
    
function setArrowForMode(mode) {{
  if (mode === "bench") {{
        arrow.position.set(0, 1.0, 0.35);
        arrow.setDirection(new THREE.Vector3(0, 1, 0).normalize());
        arrow.setLength(0.55);
  }} else if (mode === "squat") {{
        arrow.position.set(0, 1.0, 0);
        arrow.setDirection(new THREE.Vector3(0, 1, 0).normalize());
        arrow.setLength(0.45);
  }} else if (mode === "hinge") {{
        arrow.position.set(0, 1.05, 0);
        arrow.setDirection(new THREE.Vector3(0, 0.8, -0.4).normalize());
        arrow.setLength(0.55);
  }} else {{
        arrow.position.set(0, 1.0, 0);
        arrow.setDirection(new THREE.Vector3(0, 1, 0).normalize());
        arrow.setLength(0.5);
  }}
}}
setArrowForMode("{cfg['mode']}");
    
loader.parse(arrayBuffer, "", (gltf) => {{
  mannequin = gltf.scene;
  mannequin.traverse((o) => {{
        if (o.isMesh) {{
          o.castShadow = !isMobile;
          o.receiveShadow = !isMobile;
          // Material mate "mannequin"
          if (o.material) {{
            o.material.roughness = 0.9;
            o.material.metalness = 0.0;
          }}
        }}
  }});
  mannequin.position.set(0, 0, 0);
  scene.add(mannequin);
    
  // Mapeo de huesos robusto por patrones
  bones.hips      = findBone(mannequin, ["^hips$", "pelvis", "hip"]);
  bones.spine     = findBone(mannequin, ["spine", "chest", "torso"]);
  bones.thighL    = findBone(mannequin, ["left.*upleg", "thigh.*l", "upleg.*l", "l.*thigh"]);
  bones.thighR    = findBone(mannequin, ["right.*upleg", "thigh.*r", "upleg.*r", "r.*thigh"]);
  bones.kneeL     = findBone(mannequin, ["left.*leg$", "calf.*l", "leg.*l$", "l.*calf"]);
  bones.kneeR     = findBone(mannequin, ["right.*leg$", "calf.*r", "leg.*r$", "r.*calf"]);
  bones.shoulderL = findBone(mannequin, ["left.*arm$", "upperarm.*l", "arm.*l$", "l.*upperarm"]);
  bones.shoulderR = findBone(mannequin, ["right.*arm$", "upperarm.*r", "arm.*r$", "r.*upperarm"]);
  bones.elbowL    = findBone(mannequin, ["left.*forearm", "lowerarm.*l", "forearm.*l", "l.*forearm"]);
  bones.elbowR    = findBone(mannequin, ["right.*forearm", "lowerarm.*r", "forearm.*r", "r.*forearm"]);
    
  attachMarkers();
}}, (err) => {{
  console.error(err);
}});
    
function clamp(v, a, b) {{ return Math.max(a, Math.min(b, v)); }}
function lerp(a,b,t) {{ return a + (b-a)*t; }}
    
// Animación: simple pero creíble
let t0 = performance.now();
let lastFrame = 0;
const targetFps = isMobile ? 30 : 60;
const frameMs = 1000 / targetFps;
    
function animate(ts) {{
  requestAnimationFrame(animate);
  if (ts - lastFrame < frameMs) return;
  lastFrame = ts;
    
  if (mannequin) {{
        const t = (ts - t0) / 1000;
        const phase = (Math.sin(t * 2.2) + 1) / 2; // 0..1
        // “pico” más claro en bottom
        const depth = phase < 0.5 ? (phase/0.5) : (1 - (phase-0.5)/0.5);
        const d = clamp(depth, 0, 1);
    
        const mode = "{cfg['mode']}";
        if (mode === "squat") {{
          // hip + knee flexion
          if (bones.hips) bones.hips.rotation.x = lerp(0.0, -0.55, d);
          if (bones.thighL) bones.thighL.rotation.x = lerp(0.0, -0.85, d);
          if (bones.thighR) bones.thighR.rotation.x = lerp(0.0, -0.85, d);
          if (bones.kneeL) bones.kneeL.rotation.x = lerp(0.0,  1.10, d);
          if (bones.kneeR) bones.kneeR.rotation.x = lerp(0.0,  1.10, d);
        }} else if (mode === "hinge") {{
          // deadlift hinge
          if (bones.hips) bones.hips.rotation.x = lerp(0.0, -0.70, d);
          if (bones.spine) bones.spine.rotation.x = lerp(0.0,  0.20, d);
          if (bones.thighL) bones.thighL.rotation.x = lerp(0.0, -0.35, d);
          if (bones.thighR) bones.thighR.rotation.x = lerp(0.0, -0.35, d);
          if (bones.kneeL) bones.kneeL.rotation.x = lerp(0.0,  0.55, d);
          if (bones.kneeR) bones.kneeR.rotation.x = lerp(0.0,  0.55, d);
        }} else if (mode === "bench") {{
          // press: elbow extend + slight shoulder movement
          const press = (Math.sin(t * 2.6) + 1) / 2;
          const p = clamp(press, 0, 1);
          if (bones.shoulderL) bones.shoulderL.rotation.z = lerp(0.35, 0.10, p);
          if (bones.shoulderR) bones.shoulderR.rotation.z = lerp(-0.35, -0.10, p);
          if (bones.elbowL) bones.elbowL.rotation.x = lerp(1.35, 0.20, p);
          if (bones.elbowR) bones.elbowR.rotation.x = lerp(1.35, 0.20, p);
        }}
    
        // Actualiza markers
        for (const j of joints) {{
          const v = new THREE.Vector3();
          j.bone.getWorldPosition(v);
          j.marker.position.copy(v);
        }}
  }}
    
  // Resize si cambió tamaño
  const w1 = canvas1.clientWidth, h1 = canvas1.clientHeight;
  const w2 = canvas2.clientWidth, h2 = canvas2.clientHeight;
  if (canvas1.width !== Math.floor(w1 * renderer1.getPixelRatio()) || canvas1.height !== Math.floor(h1 * renderer1.getPixelRatio())) {{
        renderer1.setSize(w1, h1, false);
        cameraFront.aspect = w1 / h1;
        cameraFront.updateProjectionMatrix();
  }}
  if (canvas2.width !== Math.floor(w2 * renderer2.getPixelRatio()) || canvas2.height !== Math.floor(h2 * renderer2.getPixelRatio())) {{
        renderer2.setSize(w2, h2, false);
        cameraSide.aspect = w2 / h2;
        cameraSide.updateProjectionMatrix();
  }}
    
  renderer1.render(scene, cameraFront);
  renderer2.render(scene, cameraSide);
}}
requestAnimationFrame(animate);
</script>
</body>
</html>
"""
        components.html(page_html, height=620, scrolling=False)
    except Exception as e:
        st.error('Error cargando mini-animación 3D')
        st.exception(e)
        return