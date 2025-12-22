from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Any, List, Optional

import streamlit as st
import streamlit.components.v1 as components
import html as html_lib


def _assets_dir() -> Path:
    """Return absolute path to assets directory (robust for Streamlit Cloud)."""
    # This file lives at: <repo>/app/technique_3d_component.py
    # assets folder is expected at: <repo>/assets
    here = Path(__file__).resolve()
    repo_root = here.parents[1]
    return repo_root / "assets"


def render_mannequin_3d(exercise_id: str, cues: Optional[List[str]] = None) -> None:
    """
    Renderiza una mini-animación 3D (frontal + lateral) usando un maniquí GLB.

    Requiere colocar el archivo en:
      assets/3d/mannequin.glb
    """
    try:
        # Normaliza cues de forma segura
        cues_list: List[str] = []
        try:
            if cues is None:
                cues_list = []
            elif isinstance(cues, (list, tuple)):
                cues_list = [str(x) for x in cues]
            elif isinstance(cues, str):
                cues_list = [cues]
            else:
                cues_list = [str(x) for x in list(cues)]
        except Exception:
            cues_list = []
        cues_list = [c.strip() for c in cues_list if c is not None and str(c).strip()][:4]
        cues_html = "".join([f"<li>{html_lib.escape(c)}</li>" for c in cues_list])
        cues_block = (
            f"<ul style='margin:6px 0 0 18px; padding:0; font-size:12px; opacity:.9'>{cues_html}</ul>"
            if len(cues_list) > 0 else ""
        )

        glb_file = _assets_dir() / "3d" / "mannequin.glb"
        if not glb_file.exists():
            st.warning("Falta el modelo 3D. Coloca mannequin.glb en assets/3d/mannequin.glb")
            st.code(str(glb_file))
            return

        # Lee el GLB sin depender de Path.stat/os.path (compatibilidad máxima)
        try:
            glb_bytes = glb_file.read_bytes()
        except Exception as e:
            st.error("No se pudo leer mannequin.glb")
            st.code(str(glb_file))
            st.exception(e)
            return

        size_mb = len(glb_bytes) / (1024 * 1024)
        if size_mb > 15:
            st.warning(f"El GLB pesa ~{size_mb:.1f} MB. En móvil puede ir lento; intenta bajarlo a 2–10 MB.")

        glb_b64 = base64.b64encode(glb_bytes).decode("ascii")

        ex_cfg: Dict[str, Any] = {
            "bench_press": {"name": "Press banca", "mode": "bench"},
            "squat": {"name": "Sentadilla", "mode": "squat"},
            "deadlift": {"name": "Peso muerto", "mode": "hinge"},
        }
        cfg = ex_cfg.get(exercise_id, {"name": str(exercise_id), "mode": "generic"})

        page_html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }}
    .wrap {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; padding:10px; }}
    .card {{ border:1px solid rgba(0,0,0,.1); border-radius:14px; overflow:hidden; box-shadow: 0 8px 18px rgba(0,0,0,.06); }}
    .hdr {{ padding:10px 12px; background: rgba(0,0,0,.03); display:flex; justify-content:space-between; align-items:center; }}
    .ttl {{ font-weight:600; font-size:13px; opacity:.85; }}
    .sub {{ font-size:12px; opacity:.7; }}
    canvas {{ display:block; width:100%; height:260px; }}
    .note {{ padding:10px 12px; font-size:12px; opacity:.8; }}
    @media (max-width: 720px) {{
      .wrap {{ grid-template-columns: 1fr; }}
      canvas {{ height:240px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="hdr"><div><div class="ttl">Vista frontal</div><div class="sub">{html_lib.escape(cfg.get("name",""))}</div></div></div>
      <div id="c1"></div>
      <div class="note">Cues:{cues_block}</div>
    </div>
    <div class="card">
      <div class="hdr"><div><div class="ttl">Vista lateral</div><div class="sub">{html_lib.escape(cfg.get("name",""))}</div></div></div>
      <div id="c2"></div>
      <div class="note">Modo: {html_lib.escape(cfg.get("mode","generic"))}</div>
    </div>
  </div>

<script type="module">
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import {{ GLTFLoader }} from 'https://unpkg.com/three@0.160.0/examples/jsm/loaders/GLTFLoader.js';

const glbB64 = "{glb_b64}";
function b64ToArrayBuffer(b64) {{
  const binaryString = atob(b64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes.buffer;
}}

function makeScene(containerId, view) {{
  const container = document.getElementById(containerId);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xffffff);

  const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
  camera.position.set(view === "front" ? 0 : 3.2, 1.6, view === "front" ? 3.2 : 0);
  camera.lookAt(0, 1.2, 0);

  const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.setSize(container.clientWidth, 260);
  container.appendChild(renderer.domElement);

  // Lights (mobile-friendly)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 1.0));
  const key = new THREE.DirectionalLight(0xffffff, 0.8);
  key.position.set(3, 6, 4);
  scene.add(key);

  // Ground
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(10, 10),
    new THREE.MeshStandardMaterial({{ color: 0xf4f4f4 }})
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = 0;
  scene.add(ground);

  const loader = new GLTFLoader();
  const glb = b64ToArrayBuffer(glbB64);

  return new Promise((resolve, reject) => {{
    loader.parse(glb, '', (gltf) => {{
      const model = gltf.scene;
      model.traverse((o) => {{
        if (o.isMesh) {{
          o.material = new THREE.MeshStandardMaterial({{ color: 0xe6e6e6, roughness: 0.7, metalness: 0.05 }});
        }}
      }});
      model.position.set(0, 0, 0);
      scene.add(model);

      const clock = new THREE.Clock();
      function animate() {{
        const t = clock.getElapsedTime();
        model.rotation.y = Math.sin(t * 0.5) * 0.15;
        renderer.render(scene, camera);
        requestAnimationFrame(animate);
      }}
      animate();

      const ro = new ResizeObserver(() => {{
        renderer.setSize(container.clientWidth, 260);
        camera.aspect = container.clientWidth / 260;
        camera.updateProjectionMatrix();
      }});
      ro.observe(container);

      resolve(true);
    }}, (err) => reject(err));
  }});
}}

Promise.all([makeScene("c1","front"), makeScene("c2","side")]).catch((e) => {{
  document.body.innerHTML = "<div style='padding:12px;font-family:system-ui'>Error cargando 3D: " + (e?.message || e) + "</div>";
}});
</script>
</body>
</html>
"""

        components.html(page_html, height=640, scrolling=False)
    except Exception as e:
        st.error("Error cargando mini-animación 3D")
        st.exception(e)
