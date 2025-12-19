from __future__ import annotations

import json
from typing import Dict, List, Optional

import streamlit as st
import streamlit.components.v1 as components


def default_animations() -> Dict[str, dict]:
    """Configuración mínima por ejercicio.

    exercise_id se usa para elegir el patrón de movimiento (plantilla única).
    """
    return {
        "squat": {
            "pattern": "squat",
            "title": "Sentadilla",
            "highlights": ["hip", "knee", "ankle"],
            "cues": ["Empuja el suelo", "Costillas abajo", "Rodillas siguen el pie"],
        },
        "deadlift": {
            "pattern": "deadlift",
            "title": "Peso muerto",
            "highlights": ["hip", "knee", "spine"],
            "cues": ["Bisagra de cadera", "Barra pegada", "Quita la holgura"],
        },
        "bench_press": {
            "pattern": "bench",
            "title": "Press banca",
            "highlights": ["shoulder", "elbow", "wrist"],
            "cues": ["Escápulas atrás y abajo", "Muñeca sobre codo", "Trayectoria estable"],
        },
    }


def render_minimal_3d_animation(
    exercise_id: str,
    *,
    cues: Optional[List[str]] = None,
    height: int = 460,
) -> None:
    """Mini-animación 3D minimal (plantilla reutilizable)."""

    cfg = default_animations().get(exercise_id, {
        "pattern": "generic",
        "title": exercise_id,
        "highlights": [],
        "cues": cues or [],
    })
    if cues:
        cfg["cues"] = cues[:3]

    payload = json.dumps(cfg)

    html = f"""
<div style="font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;">
  <div style="display:flex; gap:12px; flex-wrap:wrap;">
    <div style="flex:1; min-width:300px;">
      <div style="font-size:13px; opacity:.75; margin:2px 0 6px;">Vista lateral</div>
      <div id="vp_canvas_side" style="width:100%; height:{height}px; border:1px solid rgba(0,0,0,.08); border-radius:12px; overflow:hidden;"></div>
    </div>
    <div style="flex:1; min-width:300px;">
      <div style="font-size:13px; opacity:.75; margin:2px 0 6px;">Vista frontal</div>
      <div id="vp_canvas_front" style="width:100%; height:{height}px; border:1px solid rgba(0,0,0,.08); border-radius:12px; overflow:hidden;"></div>
    </div>
  </div>
  <div style="margin-top:10px; font-size:13px; line-height:1.3; opacity:.85;">
    <b>Cues</b>: <span id="vp_cues"></span>
  </div>
</div>

<script>
  const VP_CFG = {payload};
  const cues = (VP_CFG.cues || []).filter(Boolean);
  document.getElementById('vp_cues').textContent = cues.length ? cues.join(' · ') : '—';

  const loadScript = (src) => new Promise((resolve, reject) => {{
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  }});

  async function boot() {{
    if (!window.THREE) {{
      await loadScript('https://unpkg.com/three@0.160.0/build/three.min.js');
    }}

    function makeRenderer(containerId) {{
      const el = document.getElementById(containerId);
      const w = el.clientWidth;
      const h = el.clientHeight;
      const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
      renderer.setSize(w, h);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      el.appendChild(renderer.domElement);
      return {{ el, renderer }};
    }}

    function addLights(scene) {{
      const a = new THREE.AmbientLight(0xffffff, 0.85);
      scene.add(a);
      const d = new THREE.DirectionalLight(0xffffff, 0.55);
      d.position.set(2.5, 4.0, 2.0);
      scene.add(d);
    }}

    function addFloor(scene) {{
      const g = new THREE.PlaneGeometry(10, 10);
      const m = new THREE.MeshPhongMaterial({{ color: 0xf4f4f4, transparent:true, opacity: 0.65 }});
      const p = new THREE.Mesh(g, m);
      p.rotation.x = -Math.PI/2;
      p.position.y = 0;
      scene.add(p);
      const grid = new THREE.GridHelper(10, 10, 0xdddddd, 0xeeeeee);
      grid.position.y = 0.001;
      scene.add(grid);
    }}

    function cyl(len, r, color, opacity=1) {{
      const geo = new THREE.CylinderGeometry(r, r, len, 14);
      const mat = new THREE.MeshStandardMaterial({{ color, roughness: 0.7, metalness: 0.05, transparent: opacity < 1, opacity }});
      const mesh = new THREE.Mesh(geo, mat);
      return mesh;
    }}

    function sphere(r, color, opacity=1) {{
      const geo = new THREE.SphereGeometry(r, 18, 18);
      const mat = new THREE.MeshStandardMaterial({{ color, roughness: 0.5, metalness: 0.08, transparent: opacity < 1, opacity }});
      return new THREE.Mesh(geo, mat);
    }}

    function buildStandingFigure(scene) {{
      const root = new THREE.Group();
      scene.add(root);

      // Body dimensions
      const pelvisY = 1.05;
      const torsoLen = 0.85;
      const thighLen = 0.75;
      const shinLen = 0.75;
      const upperArmLen = 0.55;
      const foreArmLen = 0.55;

      const bodyColor = 0x2f2f2f;
      const jointColor = 0xffc04d;

      // Pelvis
      const pelvis = sphere(0.08, jointColor);
      pelvis.position.set(0, pelvisY, 0);
      root.add(pelvis);

      // Torso
      const torsoPivot = new THREE.Group();
      torsoPivot.position.set(0, pelvisY, 0);
      root.add(torsoPivot);
      const torso = cyl(torsoLen, 0.06, bodyColor);
      torso.position.y = torsoLen/2;
      torsoPivot.add(torso);
      const neck = sphere(0.06, jointColor);
      neck.position.y = torsoLen;
      torsoPivot.add(neck);
      const head = sphere(0.12, bodyColor, 0.95);
      head.position.y = torsoLen + 0.22;
      torsoPivot.add(head);

      function buildLeg(sideSign) {{
        const hip = new THREE.Group();
        hip.position.set(0.12 * sideSign, pelvisY, 0);
        root.add(hip);
        const hipBall = sphere(0.06, jointColor);
        hip.add(hipBall);

        const thigh = cyl(thighLen, 0.05, bodyColor);
        thigh.position.y = -thighLen/2;
        hip.add(thigh);

        const knee = new THREE.Group();
        knee.position.y = -thighLen;
        hip.add(knee);
        const kneeBall = sphere(0.055, jointColor);
        knee.add(kneeBall);

        const shin = cyl(shinLen, 0.045, bodyColor);
        shin.position.y = -shinLen/2;
        knee.add(shin);

        const ankle = new THREE.Group();
        ankle.position.y = -shinLen;
        knee.add(ankle);
        const ankleBall = sphere(0.05, jointColor);
        ankle.add(ankleBall);

        const foot = new THREE.Mesh(
          new THREE.BoxGeometry(0.22, 0.06, 0.38),
          new THREE.MeshStandardMaterial({{ color: bodyColor, roughness: 0.85 }})
        );
        foot.position.set(0, -0.03, 0.12);
        ankle.add(foot);

        return {{ hip, knee, ankle, hipBall, kneeBall, ankleBall }};
      }}

      function buildArm(sideSign) {{
        const shoulder = new THREE.Group();
        shoulder.position.set(0.22 * sideSign, pelvisY + torsoLen, 0);
        root.add(shoulder);
        const shoulderBall = sphere(0.055, jointColor);
        shoulder.add(shoulderBall);

        const upper = cyl(upperArmLen, 0.04, bodyColor);
        upper.position.y = -upperArmLen/2;
        shoulder.add(upper);

        const elbow = new THREE.Group();
        elbow.position.y = -upperArmLen;
        shoulder.add(elbow);
        const elbowBall = sphere(0.05, jointColor);
        elbow.add(elbowBall);

        const fore = cyl(foreArmLen, 0.035, bodyColor);
        fore.position.y = -foreArmLen/2;
        elbow.add(fore);

        const wrist = new THREE.Group();
        wrist.position.y = -foreArmLen;
        elbow.add(wrist);
        const wristBall = sphere(0.045, jointColor);
        wrist.add(wristBall);

        const hand = sphere(0.045, bodyColor);
        hand.position.y = -0.05;
        wrist.add(hand);

        return {{ shoulder, elbow, wrist, shoulderBall, elbowBall, wristBall }};
      }}

      const legL = buildLeg(-1);
      const legR = buildLeg(1);
      const armL = buildArm(-1);
      const armR = buildArm(1);

      // Simple bar (for deadlift / bench)
      const bar = new THREE.Mesh(
        new THREE.CylinderGeometry(0.03, 0.03, 1.4, 16),
        new THREE.MeshStandardMaterial({{ color: 0x1a1a1a, roughness: 0.4, metalness: 0.25 }})
      );
      bar.rotation.z = Math.PI/2;
      bar.position.set(0, 0.65, 0.20);
      root.add(bar);

      // Trajectory arrow helper (updated during animation)
      const arrowDir = new THREE.Vector3(0, 1, 0);
      const arrow = new THREE.ArrowHelper(arrowDir, new THREE.Vector3(0, 0.5, 0.2), 0.6, 0x6b8cff, 0.14, 0.08);
      scene.add(arrow);

      return {{
        root,
        torsoPivot,
        legL, legR,
        armL, armR,
        bar,
        arrow,
      }};
    }}

    function buildBenchFigure(scene) {{
      const root = new THREE.Group();
      scene.add(root);
      const bodyColor = 0x2f2f2f;
      const jointColor = 0xffc04d;

      // Bench
      const bench = new THREE.Mesh(
        new THREE.BoxGeometry(2.1, 0.10, 0.55),
        new THREE.MeshStandardMaterial({{ color: 0xf0f0f0, roughness: 0.9 }})
      );
      bench.position.set(0, 0.55, 0);
      root.add(bench);

      // Lying torso (along X)
      const torso = cyl(0.95, 0.06, bodyColor);
      torso.rotation.z = Math.PI/2;
      torso.position.set(0, 0.68, 0);
      root.add(torso);
      const head = sphere(0.12, bodyColor, 0.95);
      head.position.set(-0.58, 0.75, 0);
      root.add(head);

      // Shoulders
      const shoulderL = new THREE.Group();
      shoulderL.position.set(0.05, 0.72, -0.18);
      root.add(shoulderL);
      shoulderL.add(sphere(0.055, jointColor));

      const shoulderR = new THREE.Group();
      shoulderR.position.set(0.05, 0.72, 0.18);
      root.add(shoulderR);
      shoulderR.add(sphere(0.055, jointColor));

      function buildBenchArm(shoulder) {{
        const upperLen = 0.42;
        const foreLen = 0.42;

        const upper = cyl(upperLen, 0.04, bodyColor);
        upper.position.y = -upperLen/2;
        shoulder.add(upper);

        const elbow = new THREE.Group();
        elbow.position.y = -upperLen;
        shoulder.add(elbow);
        elbow.add(sphere(0.05, jointColor));

        const fore = cyl(foreLen, 0.035, bodyColor);
        fore.position.y = -foreLen/2;
        elbow.add(fore);

        const wrist = new THREE.Group();
        wrist.position.y = -foreLen;
        elbow.add(wrist);
        wrist.add(sphere(0.045, jointColor));

        const hand = sphere(0.045, bodyColor);
        hand.position.y = -0.05;
        wrist.add(hand);

        return {{ shoulder, elbow, wrist }};
      }}

      const armL = buildBenchArm(shoulderL);
      const armR = buildBenchArm(shoulderR);

      // Bar above chest
      const bar = new THREE.Mesh(
        new THREE.CylinderGeometry(0.03, 0.03, 1.4, 16),
        new THREE.MeshStandardMaterial({{ color: 0x1a1a1a, roughness: 0.4, metalness: 0.25 }})
      );
      bar.rotation.x = Math.PI/2;
      bar.position.set(0.15, 1.05, 0);
      root.add(bar);

      const arrow = new THREE.ArrowHelper(new THREE.Vector3(0, 1, 0), new THREE.Vector3(0.15, 0.78, 0), 0.5, 0x6b8cff, 0.14, 0.08);
      scene.add(arrow);

      return {{ root, armL, armR, bar, arrow }};
    }}

    function setupScene(containerId, view) {{
      const {{ el, renderer }} = makeRenderer(containerId);
      const scene = new THREE.Scene();
      addLights(scene);
      addFloor(scene);

      const camera = new THREE.PerspectiveCamera(42, el.clientWidth / el.clientHeight, 0.1, 50);
      if (view === 'side') {{
        camera.position.set(3.2, 2.4, 0.2);
      }} else {{
        camera.position.set(0.2, 2.4, 3.2);
      }}
      camera.lookAt(0, 1.0, 0);

      const state = {{ el, renderer, scene, camera, view }};
      window.addEventListener('resize', () => {{
        const w = el.clientWidth;
        const h = el.clientHeight;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      }});
      return state;
    }}

    const side = setupScene('vp_canvas_side', 'side');
    const front = setupScene('vp_canvas_front', 'front');

    // Build figure(s) based on pattern
    let figSide, figFront;
    if (VP_CFG.pattern === 'bench') {{
      figSide = buildBenchFigure(side.scene);
      figFront = buildBenchFigure(front.scene);
    }} else {{
      figSide = buildStandingFigure(side.scene);
      figFront = buildStandingFigure(front.scene);
    }}

    function clamp(x, a, b) {{ return Math.max(a, Math.min(b, x)); }}

    function animateStanding(fig, t) {{
      // t in [0,1]
      const down = 0.5 - 0.5*Math.cos(t * 2*Math.PI); // 0..1
      const pattern = VP_CFG.pattern;

      if (pattern === 'squat') {{
        const hip = THREE.MathUtils.degToRad(-10 - 55*down);
        const knee = THREE.MathUtils.degToRad(5 + 80*down);
        fig.legL.hip.rotation.x = hip;
        fig.legR.hip.rotation.x = hip;
        fig.legL.knee.rotation.x = -knee;
        fig.legR.knee.rotation.x = -knee;
        fig.torsoPivot.rotation.x = THREE.MathUtils.degToRad(5 + 18*down);
        fig.bar.position.y = 0.75 + 0.15*down;
        fig.bar.position.z = 0.22;
        fig.arrow.position.set(0, 0.35, 0.22);
        fig.arrow.setDirection(new THREE.Vector3(0, 1, 0));
        fig.arrow.setLength(0.55);
      }}

      if (pattern === 'deadlift') {{
        const hip = THREE.MathUtils.degToRad(-15 - 45*down);
        const knee = THREE.MathUtils.degToRad(0 + 30*down);
        fig.legL.hip.rotation.x = hip;
        fig.legR.hip.rotation.x = hip;
        fig.legL.knee.rotation.x = -knee;
        fig.legR.knee.rotation.x = -knee;
        fig.torsoPivot.rotation.x = THREE.MathUtils.degToRad(8 + 32*down);

        // Bar path (vertical, close to shins)
        const yLow = 0.30;
        const yHigh = 1.05;
        fig.bar.position.set(0, yLow + (yHigh - yLow)*clamp(down, 0, 1), 0.18);
        fig.arrow.position.set(0, 0.28, 0.18);
        fig.arrow.setDirection(new THREE.Vector3(0, 1, 0));
        fig.arrow.setLength(0.85);
      }}

      // Generic: small bend
      if (pattern === 'generic') {{
        const hip = THREE.MathUtils.degToRad(-8 - 25*down);
        const knee = THREE.MathUtils.degToRad(0 + 25*down);
        fig.legL.hip.rotation.x = hip;
        fig.legR.hip.rotation.x = hip;
        fig.legL.knee.rotation.x = -knee;
        fig.legR.knee.rotation.x = -knee;
        fig.torsoPivot.rotation.x = THREE.MathUtils.degToRad(6 + 12*down);
        fig.bar.position.y = 0.65 + 0.2*down;
      }}
    }}

    function animateBench(fig, t) {{
      const down = 0.5 - 0.5*Math.cos(t * 2*Math.PI);
      const elbowFlex = THREE.MathUtils.degToRad(10 + 70*down);
      // Arms: rotate down a bit at shoulders and bend at elbows
      fig.armL.shoulder.rotation.z = THREE.MathUtils.degToRad(15 + 10*down);
      fig.armR.shoulder.rotation.z = -THREE.MathUtils.degToRad(15 + 10*down);
      fig.armL.elbow.rotation.x = -elbowFlex;
      fig.armR.elbow.rotation.x = -elbowFlex;

      // Bar vertical path
      const yLow = 0.82;
      const yHigh = 1.10;
      fig.bar.position.y = yLow + (yHigh - yLow) * (1-down);
      fig.arrow.position.set(fig.bar.position.x, 0.76, 0);
      fig.arrow.setDirection(new THREE.Vector3(0, 1, 0));
      fig.arrow.setLength(0.55);
    }}

    let start = performance.now();
    function loop(now) {{
      const t = ((now - start) / 1600) % 1; // cycle

      if (VP_CFG.pattern === 'bench') {{
        animateBench(figSide, t);
        animateBench(figFront, t);
      }} else {{
        animateStanding(figSide, t);
        animateStanding(figFront, t);
      }}

      side.renderer.render(side.scene, side.camera);
      front.renderer.render(front.scene, front.camera);
      requestAnimationFrame(loop);
    }}
    requestAnimationFrame(loop);
  }}

  boot().catch((e) => {{
    console.error(e);
    const el1 = document.getElementById('vp_canvas_side');
    const el2 = document.getElementById('vp_canvas_front');
    if (el1) el1.innerHTML = '<div style="padding:14px; opacity:.75;">No se pudo cargar Three.js (¿sin internet?).</div>';
    if (el2) el2.innerHTML = '<div style="padding:14px; opacity:.75;">No se pudo cargar Three.js (¿sin internet?).</div>';
  }});
</script>
"""

    components.html(html, height=height + 90, scrolling=False)
