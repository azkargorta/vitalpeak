(() => {
  const STYLE_ID = 'vp-routines-redesign-styles';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .vp-routines-page .vp-routines-hero{position:relative;overflow:hidden;padding:22px 20px 20px;margin:0 0 14px;border:1px solid rgba(60,133,255,.22);border-radius:24px;background:radial-gradient(circle at 88% 20%,rgba(57,134,255,.30),transparent 36%),linear-gradient(135deg,#0c1a24 0%,#102934 58%,#10222d 100%);box-shadow:0 18px 42px rgba(13,38,49,.18)}
      .vp-routines-page .vp-routines-hero .app-brand{margin-bottom:18px}.vp-routines-page .vp-routines-hero .wordmark,.vp-routines-page .vp-routines-hero .wordmark span{color:#fff}.vp-routines-page .vp-routines-hero .eyebrow{color:#70b5ff;letter-spacing:.13em}.vp-routines-page .vp-routines-hero h1{color:#fff;font-size:clamp(30px,8vw,42px);margin:5px 0 6px;letter-spacing:-.04em}.vp-routines-page .vp-routines-hero p{color:#c0d0d8;max-width:620px}
      .vp-routines-coach{margin:0 0 18px;padding:18px;border-radius:20px;border:1px solid rgba(47,128,237,.18);background:linear-gradient(145deg,#f6faff,#edf4ff);box-shadow:0 10px 26px rgba(16,46,56,.06)}
      .vp-routines-coach .vp-coach-kicker{display:block;margin-bottom:5px;color:#2f80ed;font-size:11px;font-weight:900;letter-spacing:.10em;text-transform:uppercase}.vp-routines-coach h2{margin:0 0 6px;color:#102e38;font-size:22px}.vp-routines-coach p{margin:0;color:#667980;font-size:13px}
      .vp-routines-active{position:relative;overflow:hidden;padding:18px;margin:0 0 18px;border-radius:20px;border:1px solid rgba(22,169,142,.22);background:linear-gradient(145deg,#f6fffc 0%,#edf8f5 100%);box-shadow:0 10px 26px rgba(16,46,56,.07)}.vp-routines-active:before{content:'';position:absolute;inset:0 auto 0 0;width:5px;background:linear-gradient(#16a98e,#2f80ed)}.vp-routines-active-top{display:flex;align-items:center;justify-content:space-between;gap:10px}.vp-routines-active .vp-label{color:#16a98e;font-size:11px;font-weight:900;letter-spacing:.09em;text-transform:uppercase}.vp-routines-active .vp-status{display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border-radius:999px;background:#dff7f0;color:#117965;font-size:11px;font-weight:800}.vp-routines-active .vp-status:before{content:'';width:7px;height:7px;border-radius:50%;background:#16a98e;box-shadow:0 0 0 4px rgba(22,169,142,.10)}.vp-routines-active h2{margin:8px 0 4px;color:#102e38;font-size:22px;letter-spacing:-.025em}.vp-routines-active p{margin:0;color:#63777d;font-size:13px}
      .vp-routines-page details{border:1px solid rgba(22,58,67,.10);border-radius:16px;background:#fff;box-shadow:0 7px 20px rgba(16,46,56,.04);overflow:hidden}.vp-routines-page details+details{margin-top:10px}.vp-routines-page details>summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:52px;padding:13px 15px;color:#163a43;font-weight:850;cursor:pointer}.vp-routines-page details>summary::-webkit-details-marker{display:none}.vp-routines-page details>summary:after{content:'';width:10px;height:10px;flex:0 0 10px;border-right:2px solid #2f80ed;border-bottom:2px solid #2f80ed;transform:rotate(45deg) translateY(-2px);transition:transform .2s ease}.vp-routines-page details[open]>summary:after{transform:rotate(225deg) translate(-2px,-2px)}.vp-routines-page details>div{padding:0 14px 14px}.vp-routines-page .section-head{margin-top:20px}.vp-routines-page .section-head h2{letter-spacing:-.02em}
      @media(max-width:520px){.vp-routines-page .vp-routines-hero{padding:19px 17px}.vp-routines-active,.vp-routines-coach{padding:16px}}
    `;
    document.head.appendChild(style);
  }

  function readState() {
    return new Promise((resolve) => {
      try {
        const r = indexedDB.open('vitalpeak-mobile', 2);
        r.onupgradeneeded = () => { if (!r.result.objectStoreNames.contains('state')) r.result.createObjectStore('state'); };
        r.onerror = () => resolve({});
        r.onsuccess = () => {
          try {
            const tx = r.result.transaction('state', 'readonly');
            const q = tx.objectStore('state').get('user');
            q.onsuccess = () => resolve(q.result || {});
            q.onerror = () => resolve({});
          } catch { resolve({}); }
        };
      } catch { resolve({}); }
    });
  }

  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const items = r => r?.days?.[r.activeDay || 0]?.items || r?.exercises || [];

  async function enhanceRoutines() {
    injectStyles();
    const app = document.querySelector('#app');
    if (!app) return;
    const routeBtn = document.querySelector('.tabbar button[data-route="routines"].active');
    const looksLikeRoutines = routeBtn || /Planes y ejercicios|RUTINAS/.test(app.textContent || '');
    if (!looksLikeRoutines) return;

    const state = await readState();
    const routines = Array.isArray(state.routines) ? state.routines : [];
    const active = routines.find(r => r.id === state.activeRoutineId) || routines[0] || null;
    app.classList.add('vp-routines-page');

    const hero = app.querySelector('.hero');
    if (hero) hero.classList.add('vp-routines-hero');

    const coachExisting = [...app.querySelectorAll('*')].find(el => /vitalpeak coach/i.test((el.textContent || '').trim()) && el.children.length < 8);
    let coach;
    if (coachExisting) {
      coach = coachExisting.closest('.card,section,div') || coachExisting;
      coach.classList.add('vp-routines-coach');
    } else {
      coach = document.createElement('section');
      coach.className = 'vp-routines-coach';
      coach.innerHTML = '<span class="vp-coach-kicker">VitalPeak Coach</span><h2>Tu plan personalizado</h2><p>Genera o ajusta tu entrenamiento según objetivo, días disponibles, nivel y tipo de rutina.</p>';
    }
    if (hero && coach && hero.nextSibling !== coach) hero.insertAdjacentElement('afterend', coach);

    const sectionHeads = [...app.querySelectorAll('.section-head')];
    for (const head of sectionHeads) {
      const text = (head.textContent || '').trim().toLowerCase();
      if (text.includes('tu rutina activa')) {
        const next = head.nextElementSibling;
        const currentButtons = next ? [...next.querySelectorAll('button[data-action="activate-routine"]')] : [];
        const box = document.createElement('section');
        box.className = 'vp-routines-active';
        if (active) {
          const sessionName = active.days?.[active.activeDay || 0]?.name || 'Sesión';
          box.innerHTML = `<div class="vp-routines-active-top"><span class="vp-label">Rutina activa</span><span class="vp-status">Activa</span></div><h2>${esc(active.name)}</h2><p>${items(active).length} ejercicios · ${esc(sessionName)}</p>`;
          box.addEventListener('click', () => currentButtons[0]?.click());
          box.style.cursor = currentButtons.length ? 'pointer' : 'default';
        } else {
          box.innerHTML = '<div class="vp-routines-active-top"><span class="vp-label">Rutina activa</span></div><h2>Sin rutina seleccionada</h2><p>Elige un plan preparado o crea uno con VitalPeak Coach.</p>';
        }
        head.replaceWith(box);
        if (next) next.remove();
      }
      if (text.includes('planes preparados')) head.scrollMarginTop = '90px';
    }

    // Quitar los dos menús de resumen/accesos añadidos en el rediseño anterior.
    app.querySelectorAll('.vp-routines-metrics,.vp-routines-quick').forEach(el => el.remove());

    // Mejorar visualmente desplegables nativos/inyectados sin cambiar funcionalidad.
    app.querySelectorAll('details').forEach(d => d.classList.add('vp-clean-details'));
  }

  // Reintentos cortos: la app se monta de forma asíncrona y en algunos arranques el primer render tarda.
  const run = () => { enhanceRoutines().catch(() => {}); };
  run();
  setTimeout(run, 120);
  setTimeout(run, 420);
  setTimeout(run, 900);

  const observer = new MutationObserver(() => {
    clearTimeout(window.__vpRoutineEnhanceTimer);
    window.__vpRoutineEnhanceTimer = setTimeout(run, 35);
  });
  const root = document.querySelector('#app');
  if (root) observer.observe(root, { childList: true, subtree: true });
})();
