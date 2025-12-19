from __future__ import annotations

import json
from typing import Dict, Any, List

import streamlit as st
import streamlit.components.v1 as components


def _default_config_for(exercise_name: str) -> Dict[str, Any]:
    """Best-effort mapping from exercise label to an animation archetype."""
    s = (exercise_name or "").lower()

    # Spanish/English keywords
    if any(k in s for k in ["sentadilla", "squat"]):
        kind = "squat"
    elif any(k in s for k in ["peso muerto", "deadlift", "hinge"]):
        kind = "hinge"
    elif any(k in s for k in ["press banca", "bench", "banca"]):
        kind = "bench"
    elif any(k in s for k in ["press militar", "overhead", "militar", "shoulder press"]):
        kind = "ohp"
    elif any(k in s for k in ["remo", "row"]):
        kind = "row"
    elif any(k in s for k in ["dominad", "pull-up", "pull up", "chin-up", "chin up"]):
        kind = "pullup"
    elif any(k in s for k in ["jalón", "jalon", "pulldown"]):
        kind = "pulldown"
    elif any(k in s for k in ["curl", "bíceps", "biceps"]):
        kind = "curl"
    elif any(k in s for k in ["tríceps", "triceps", "pushdown", "extensión tríceps", "extension triceps"]):
        kind = "pushdown"
    elif any(k in s for k in ["zancada", "lunge"]):
        kind = "lunge"
    elif any(k in s for k in ["plancha", "plank"]):
        kind = "plank"
    else:
        kind = "generic"

    return {
        "kind": kind,
        "tempo_ms": 2400,
        "amplitude": 1.0,
        "show_arrows": True,
        "show_joints": True,
    }


def render_minimal_3d_animation(exercise_name: str, cues: List[str] | None = None, *, height: int = 520) -> None:
    """
    Renders a minimal, reusable 3D stick-figure mannequin animation with two fixed angles (frontal + lateral).

    Notes:
    - Uses Three.js via CDN.
    - If CDN fails (no internet), it shows a fallback message.
    """
    cfg = _default_config_for(exercise_name)
    cues = cues or []

    payload = {
        "exercise": exercise_name,
        "config": cfg,
        "cues": [c for c in cues if str(c).strip()][:4],
    }

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }}
    .wrap {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 12px; }}
    .card {{ border: 1px solid rgba(0,0,0,.1); border-radius: 14px; overflow: hidden; background: rgba(255,255,255,.7); }}
    .head {{ padding: 8px 10px; font-size: 12px; opacity: .8; border-bottom: 1px solid rgba(0,0,0,.08); }}
    canvas {{ display:block; width:100%; height:240px; }}
    .cues {{ padding: 10px; font-size: 12px; line-height: 1.35; }}
    .pill {{ display:inline-block; padding: 3px 8px; margin: 4px 6px 0 0; border-radius: 999px; border: 1px solid rgba(0,0,0,.12); opacity:.9; }}
    .fallback {{ padding: 12px; font-size: 13px; }}
    @media (max-width: 900px) {{ .wrap {{ grid-template-columns: 1fr; }} canvas {{ height: 260px; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="head">Vista frontal</div>
      <canvas id="c1"></canvas>
      <div class="cues" id="cues1"></div>
    </div>
    <div class="card">
      <div class="head">Vista lateral</div>
      <canvas id="c2"></canvas>
      <div class="cues" id="cues2"></div>
    </div>
  </div>

  <script>
    const DATA = {json.dumps(payload)};
    const cues = (DATA.cues || []).map(t => String(t));
    const cuesHTML = cues.length ? cues.map(t => `<span class="pill">${{t.replaceAll('<','&lt;').replaceAll('>','&gt;')}}</span>`).join('') : `<span style="opacity:.7">Cues: (no definidos)</span>`;
    document.getElementById("cues1").innerHTML = cuesHTML;
    document.getElementById("cues2").innerHTML = cuesHTML;
  </script>

  <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
  <script>
    function showFallback(msg) {{
      document.body.innerHTML = `<div class="fallback"><b>Mini-animación no disponible</b><br/>${{msg}}</div>`;
    }}

    if (!window.THREE) {{
      showFallback("No se pudo cargar Three.js (¿sin internet / CDN bloqueado?).");
    }} else {{
      const kind = (DATA.config && DATA.config.kind) || "generic";
      const tempo = (DATA.config && DATA.config.tempo_ms) || 2400;
      const amp = (DATA.config && DATA.config.amplitude) || 1.0;
      const showArrows = !!(DATA.config && DATA.config.show_arrows);
      const showJoints = !!(DATA.config && DATA.config.show_joints);

      function makeScene(canvas, cameraPos) {{
        const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
        const scene = new THREE.Scene();

        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
        camera.position.set(cameraPos[0], cameraPos[1], cameraPos[2]);
        camera.lookAt(0, 1.2, 0);

        const light1 = new THREE.DirectionalLight(0xffffff, 1.0);
        light1.position.set(3, 6, 4);
        scene.add(light1);
        scene.add(new THREE.AmbientLight(0xffffff, 0.6));

        // Ground
        const g = new THREE.PlaneGeometry(10, 10, 1, 1);
        const m = new THREE.MeshStandardMaterial({{ color: 0xffffff, transparent: true, opacity: 0.2 }});
        const ground = new THREE.Mesh(g, m);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = 0;
        scene.add(ground);

        // Stick figure group
        const grp = new THREE.Group();
        scene.add(grp);

        const matBody = new THREE.MeshStandardMaterial({{ color: 0x222222, roughness: 0.6, metalness: 0.0 }});
        const matJoint = new THREE.MeshStandardMaterial({{ color: 0xaa0000, roughness: 0.4, metalness: 0.0 }});
        const matArrow = new THREE.MeshStandardMaterial({{ color: 0x0066cc, roughness: 0.4, metalness: 0.0 }});

        function capsule(radius, length) {{
          const geo = new THREE.CapsuleGeometry(radius, length, 8, 16);
          return new THREE.Mesh(geo, matBody);
        }}

        // Base skeleton (very simplified)
        const torso = capsule(0.10, 0.55); torso.position.set(0, 1.25, 0);
        const head = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 16), matBody); head.position.set(0, 1.65, 0);
        const pelvis = capsule(0.10, 0.20); pelvis.position.set(0, 0.95, 0);

        const upperArmL = capsule(0.07, 0.28); upperArmL.position.set(-0.28, 1.33, 0);
        const lowerArmL = capsule(0.06, 0.24); lowerArmL.position.set(-0.46, 1.20, 0);

        const upperArmR = capsule(0.07, 0.28); upperArmR.position.set(0.28, 1.33, 0);
        const lowerArmR = capsule(0.06, 0.24); lowerArmR.position.set(0.46, 1.20, 0);

        const thighL = capsule(0.08, 0.38); thighL.position.set(-0.15, 0.62, 0);
        const shinL  = capsule(0.07, 0.34); shinL.position.set(-0.15, 0.22, 0);

        const thighR = capsule(0.08, 0.38); thighR.position.set(0.15, 0.62, 0);
        const shinR  = capsule(0.07, 0.34); shinR.position.set(0.15, 0.22, 0);

        grp.add(torso, head, pelvis, upperArmL, lowerArmL, upperArmR, lowerArmR, thighL, shinL, thighR, shinR);

        // Joints highlights
        const joints = [];
        function joint(x,y,z) {{
          const s = new THREE.Mesh(new THREE.SphereGeometry(0.06, 12, 12), matJoint);
          s.position.set(x,y,z);
          grp.add(s);
          joints.push(s);
        }}
        if (showJoints) {{
          joint(0, 1.37, 0); // sternum-ish
          joint(-0.30, 1.34, 0); joint(0.30, 1.34, 0); // shoulders
          joint(-0.50, 1.18, 0); joint(0.50, 1.18, 0); // elbows
          joint(-0.15, 0.80, 0); joint(0.15, 0.80, 0); // hips
          joint(-0.15, 0.42, 0); joint(0.15, 0.42, 0); // knees
        }}

        // Trajectory arrow (simple line)
        let arrow = null;
        if (showArrows) {{
          const pts = [new THREE.Vector3(0,1.10,0), new THREE.Vector3(0,0.55,0)];
          const geo = new THREE.BufferGeometry().setFromPoints(pts);
          const line = new THREE.Line(geo, new THREE.LineBasicMaterial({{ color: 0x0066cc, transparent:true, opacity:0.8 }}));
          scene.add(line);
          arrow = line;
        }}

        function resize() {{
          const rect = canvas.getBoundingClientRect();
          const w = Math.max(1, rect.width);
          const h = Math.max(1, rect.height);
          renderer.setSize(w, h, false);
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
        }}
        resize();
        window.addEventListener("resize", resize);

        return {{ renderer, scene, camera, grp, parts: {{
          torso, pelvis, upperArmL, lowerArmL, upperArmR, lowerArmR, thighL, shinL, thighR, shinR, head
        }}, arrow, resize }};
      }}

      const s1 = makeScene(document.getElementById("c1"), [0, 1.6, 3.4]); // frontal
      const s2 = makeScene(document.getElementById("c2"), [3.2, 1.6, 0]); // lateral

      function applyPose(parts, t01) {{
        // t01 goes 0..1..0 (loop)
        // helpers
        const swing = Math.sin(t01 * Math.PI); // 0->1->0
        const a = amp;

        // Reset-ish
        parts.grp && (parts.grp.rotation.set(0,0,0));

        // Generic subtle breathing
        parts.torso.position.y = 1.25 + 0.02 * Math.sin(t01 * Math.PI*2);

        if (kind === "squat") {{
          // Knee/hip flexion: lower torso and rotate thighs/shins a bit
          const depth = 0.45 * swing * a;
          parts.torso.position.y = 1.25 - depth;
          parts.pelvis.position.y = 0.95 - depth*0.8;

          parts.thighL.rotation.x = -0.9 * swing * a;
          parts.thighR.rotation.x = -0.9 * swing * a;
          parts.shinL.rotation.x  =  0.7 * swing * a;
          parts.shinR.rotation.x  =  0.7 * swing * a;

        }} else if (kind === "hinge") {{
          // Hip hinge: rotate torso forward
          parts.torso.rotation.x = 0.9 * swing * a;
          parts.head.position.y = 1.65 - 0.12*swing*a;

        }} else if (kind === "bench") {{
          // Bench press: arms extend up/down (we fake it in standing)
          parts.upperArmL.rotation.z =  0.9 * swing * a;
          parts.lowerArmL.rotation.z =  0.7 * swing * a;
          parts.upperArmR.rotation.z = -0.9 * swing * a;
          parts.lowerArmR.rotation.z = -0.7 * swing * a;

        }} else if (kind === "ohp") {{
          // Overhead press: arms raise
          parts.upperArmL.rotation.x = -1.2 * swing * a;
          parts.upperArmR.rotation.x = -1.2 * swing * a;
          parts.lowerArmL.rotation.x = -0.8 * swing * a;
          parts.lowerArmR.rotation.x = -0.8 * swing * a;

        }} else if (kind === "row") {{
          // Row: elbows pull back
          parts.upperArmL.rotation.x =  0.8 * swing * a;
          parts.upperArmR.rotation.x =  0.8 * swing * a;
          parts.lowerArmL.rotation.x =  0.6 * swing * a;
          parts.lowerArmR.rotation.x =  0.6 * swing * a;

          parts.torso.rotation.x = 0.6 * a;

        }} else if (kind === "pullup" || kind === "pulldown") {{
          // Pull: arms pull down
          parts.upperArmL.rotation.x = -1.0 * swing * a;
          parts.upperArmR.rotation.x = -1.0 * swing * a;
          parts.lowerArmL.rotation.x = -0.8 * swing * a;
          parts.lowerArmR.rotation.x = -0.8 * swing * a;

        }} else if (kind === "curl") {{
          // Biceps curl: elbow flexion
          parts.lowerArmL.rotation.x = -1.4 * swing * a;
          parts.lowerArmR.rotation.x = -1.4 * swing * a;

        }} else if (kind === "pushdown") {{
          // Triceps pushdown: elbows extend down
          parts.lowerArmL.rotation.x =  1.2 * swing * a;
          parts.lowerArmR.rotation.x =  1.2 * swing * a;

        }} else if (kind === "lunge") {{
          const depth = 0.28 * swing * a;
          parts.torso.position.y = 1.25 - depth;
          parts.thighL.rotation.x = -0.7 * swing * a;
          parts.shinL.rotation.x  =  0.6 * swing * a;
          // keep right more stable
        }} else if (kind === "plank") {{
          parts.torso.rotation.x = 1.45;
          parts.pelvis.rotation.x = 1.45;
          parts.torso.position.y = 0.85;
          parts.pelvis.position.y = 0.60;
          parts.head.position.y = 1.05;
        }} else {{
          // generic: small arm swing
          parts.upperArmL.rotation.x = -0.5 * swing * a;
          parts.upperArmR.rotation.x = -0.5 * swing * a;
        }}
      }}

      function loop(ts) {{
        const t = (ts % tempo) / tempo;         // 0..1
        const t01 = t < 0.5 ? (t*2) : (2 - t*2); // triangle wave 0..1..0

        applyPose({{...s1.parts}}, t01);
        applyPose({{...s2.parts}}, t01);

        if (s1.arrow) {{
          // adapt arrow length depending on kind
          const y1 = (kind === "bench" || kind === "ohp") ? 1.55 : 1.10;
          const y2 = (kind === "bench" || kind === "ohp") ? 1.05 : 0.55;
          const pts = [new THREE.Vector3(0,y1,0), new THREE.Vector3(0,y2,0)];
          s1.arrow.geometry.setFromPoints(pts);
          s2.arrow.geometry.setFromPoints(pts);
        }}

        s1.renderer.render(s1.scene, s1.camera);
        s2.renderer.render(s2.scene, s2.camera);

        requestAnimationFrame(loop);
      }}
      requestAnimationFrame(loop);
    }}
  </script>
</body>
</html>
"""
    components.html(html, height=height, scrolling=False)
