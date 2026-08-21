from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional
import html as html_lib

import streamlit as st
import streamlit.components.v1 as components


def _assets_dir() -> Path:
    # Ruta absoluta robusta (Cloud/local)
    return (Path(__file__).resolve().parent.parent / "assets").resolve()


def _cache_data(**kwargs):
    if hasattr(st, 'cache_data'):
        return st.cache_data(**kwargs)  # type: ignore[attr-defined]
    if hasattr(st, 'cache'):
        return st.cache(**{k:v for k,v in kwargs.items() if k in {'show_spinner'}})  # type: ignore[attr-defined]
    def deco(fn):
        return fn
    return deco

@_cache_data(show_spinner=False)
def _read_glb_base64(glb_path: str) -> str:
    p = Path(glb_path)
    data = p.read_bytes()
    return base64.b64encode(data).decode("ascii")


def _normalize_cues(cues: Optional[List[str]]) -> List[str]:
    if cues is None:
        return []
    if isinstance(cues, str):
        return [cues.strip()] if cues.strip() else []
    if isinstance(cues, (list, tuple)):
        out = [str(x).strip() for x in cues if x is not None and str(x).strip()]
        return out
    # Fallback: iterable cualquiera
    try:
        out = [str(x).strip() for x in list(cues) if x is not None and str(x).strip()]  # type: ignore[arg-type]
        return out
    except Exception:
        return []


def render_mannequin_3d(exercise_id: str, cues: Optional[List[str]] = None) -> None:
    """Mini-animación 3D (frontal + lateral) usando un maniquí GLB.

    Requiere colocar el archivo en:
      assets/3d/mannequin.glb
    """
    try:
        glb_file = _assets_dir() / "3d" / "mannequin.glb"
        if not glb_file.exists():
            # Evitamos st.warning/st.code por compatibilidad con builds raras
            st.text("Falta el modelo 3D. Coloca mannequin.glb en assets/3d/mannequin.glb")
            st.text(f"Ruta esperada: {glb_file}")
            return

        # Aviso suave si pesa mucho (sin stat/getsize)
        try:
            size_mb = len(glb_file.read_bytes()) / (1024 * 1024)
            if size_mb > 15:
                st.text(f"⚠️ El GLB pesa ~{size_mb:.1f} MB. En móvil puede ir lento; ideal 2–10 MB.")
        except Exception:
            pass

        glb_b64 = _read_glb_base64(str(glb_file))

        cues_list = _normalize_cues(cues)[:4]
        cues_html = "".join([f"<li>{html_lib.escape(c)}</li>" for c in cues_list])
        cues_block = (
            f"<ul style='margin:6px 0 0 18px; padding:0; font-size:12px; opacity:.9'>{cues_html}</ul>"
            if len(cues_list) > 0 else ""
        )

        ex_cfg: Dict[str, Any] = {
            "bench_press": {"name": "Press banca", "mode": "bench"},
            "squat": {"name": "Sentadilla", "mode": "squat"},
            "deadlift": {"name": "Peso muerto", "mode": "hinge"},
        }
        cfg = ex_cfg.get(exercise_id, {"name": exercise_id, "mode": "generic"})

        page_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    body {{ margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; }}
    .wrap {{ display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .panel {{ border-radius: 14px; border: 1px solid rgba(0,0,0,.08); overflow:hidden; }}
    .hdr {{ padding:10px 12px; border-bottom: 1px solid rgba(0,0,0,.08); font-size: 13px; opacity:.9; }}
    canvas {{ width:100%; height:260px; display:block; background: linear-gradient(180deg, rgba(0,0,0,.02), rgba(0,0,0,.00)); }}
    .cues {{ padding: 8px 12px 12px 12px; font-size: 12px; opacity:.95; }}
    .title {{ font-weight:600; margin-bottom: 4px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <div class="hdr">Frontal</div>
      <canvas id="c1"></canvas>
      <div class="cues"><div class="title">{html_lib.escape(str(cfg["name"]))}</div>{cues_block}</div>
    </div>
    <div class="panel">
      <div class="hdr">Lateral</div>
      <canvas id="c2"></canvas>
      <div class="cues"><div class="title">{html_lib.escape(str(cfg["name"]))}</div>{cues_block}</div>
    </div>
  </div>

  <script type="module">
    import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
    import {{ GLTFLoader }} from "https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js";

    const glbB64 = "{glb_b64}";

    function b64ToArrayBuffer(b64) {{
      const binary = atob(b64);
      const len = binary.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
      return bytes.buffer;
    }}

    function setupScene(canvas, cameraPos) {{
      const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.25)); // móvil-friendly
      renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

      const scene = new THREE.Scene();

      const camera = new THREE.PerspectiveCamera(35, canvas.clientWidth / canvas.clientHeight, 0.01, 100);
      camera.position.set(...cameraPos);
      camera.lookAt(0, 1.0, 0);

      const key = new THREE.DirectionalLight(0xffffff, 1.0);
      key.position.set(2, 3, 2);
      scene.add(key);

      const fill = new THREE.DirectionalLight(0xffffff, 0.55);
      fill.position.set(-2, 2, -2);
      scene.add(fill);

      const amb = new THREE.AmbientLight(0xffffff, 0.45);
      scene.add(amb);

      return {{ renderer, scene, camera }};
    }}

    const s1 = setupScene(document.getElementById("c1"), [0, 1.35, 3.0]);
    const s2 = setupScene(document.getElementById("c2"), [3.0, 1.35, 0]);

    const loader = new GLTFLoader();
    const arrayBuffer = b64ToArrayBuffer(glbB64);
    const blob = new Blob([arrayBuffer], {{ type: "model/gltf-binary" }});
    const url = URL.createObjectURL(blob);

    function applyMaterial(root) {{
      root.traverse((o) => {{
        if (o.isMesh) {{
          o.material = new THREE.MeshStandardMaterial({{
            color: 0xdddddd,
            roughness: 0.7,
            metalness: 0.05
          }});
        }}
      }});
    }}

    let model1, model2;
    loader.load(url, (gltf) => {{
      model1 = gltf.scene;
      model2 = gltf.scene.clone(true);
      applyMaterial(model1);
      applyMaterial(model2);

      model1.position.set(0, 0, 0);
      model2.position.set(0, 0, 0);

      s1.scene.add(model1);
      s2.scene.add(model2);

      URL.revokeObjectURL(url);
      animate();
    }});

    let t0 = performance.now();
    function animate() {{
      requestAnimationFrame(animate);
      const t = (performance.now() - t0) / 1000;
      const sway = Math.sin(t * 2.0) * 0.03;
      if (model1) model1.rotation.y = sway;
      if (model2) model2.rotation.y = sway;

      s1.renderer.render(s1.scene, s1.camera);
      s2.renderer.render(s2.scene, s2.camera);
    }}

    function onResize() {{
      for (const s of [s1, s2]) {{
        const c = s.renderer.domElement;
        const w = c.clientWidth;
        const h = c.clientHeight;
        s.renderer.setSize(w, h, false);
        s.camera.aspect = w / h;
        s.camera.updateProjectionMatrix();
      }}
    }}
    window.addEventListener("resize", onResize);
  </script>
</body>
</html>"""

        components.html(page_html, height=360, scrolling=False)

    except Exception as e:
        st.text("Error en el componente 3D:")
        st.text(str(e))
