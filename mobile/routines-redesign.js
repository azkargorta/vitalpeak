(() => {
  'use strict';

  const STYLE_ID = 'vp-routines-redesign-styles';
  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const items = r => r?.days?.[r.activeDay || 0]?.items || r?.exercises || [];

  const ICONS = {
    folder: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.5h6l2 2h9v9.5a2 2 0 0 1-2 2h-15a2 2 0 0 1-2-2v-9.5a2 2 0 0 1 2-2Z"/></svg>',
    history: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v5l3.5 2"/></svg>',
    clipboard: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="4.5" width="12" height="16" rx="2"/><path d="M9 4.5v-1h6v3H9v-2Zm3 6v6m-3-3h6"/></svg>',
    dumbbellPlus: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6m3-8v10m10-10v10m3-8v6M7 12h10"/><path d="M18.5 3.5v5m-2.5-2.5h5"/></svg>',
    layers: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 8 4-8 4-8-4 8-4Z"/><path d="m4 12 8 4 8-4M4 17l8 4 8-4"/></svg>',
    dumbbell: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9v6m3-8v10m12-10v10m3-8v6M6 12h12"/></svg>',
    spark: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5c.5 4.7 2.8 7 7.5 7.5-4.7.5-7 2.8-7.5 7.5-.5-4.7-2.8-7-7.5-7.5 4.7-.5 7-2.8 7.5-7.5Z"/></svg>',
    chevron: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>'
  };

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .vp-routines-page{padding-bottom:24px}
      .vp-routines-page .vp-routines-hero{position:relative;overflow:hidden;padding:22px 20px 20px;margin:0 0 16px;border:1px solid rgba(60,133,255,.16);border-radius:24px;background:radial-gradient(circle at 88% 18%,rgba(90,177,255,.24),transparent 33%),linear-gradient(135deg,#0b1b25 0%,#0e3541 58%,#102630 100%);box-shadow:0 18px 42px rgba(13,38,49,.17)}
      .vp-routines-page .vp-routines-hero .app-brand{margin-bottom:18px}.vp-routines-page .vp-routines-hero .wordmark,.vp-routines-page .vp-routines-hero .wordmark span{color:#fff}.vp-routines-page .vp-routines-hero .eyebrow{color:#72b9ff;letter-spacing:.14em}.vp-routines-page .vp-routines-hero h1{color:#fff;font-size:clamp(30px,8vw,42px);margin:5px 0 6px;letter-spacing:-.04em}.vp-routines-page .vp-routines-hero p{color:#d5e0e4;max-width:620px;line-height:1.48}

      .vp-routines-coach{position:relative;overflow:hidden;margin:0 0 14px;padding:19px;border-radius:22px;border:1px solid rgba(60,232,207,.28);background:radial-gradient(circle at 86% 18%,rgba(73,224,199,.13),transparent 34%),linear-gradient(135deg,#0d4b4f 0%,#145d5c 55%,#176c68 100%);box-shadow:0 13px 30px rgba(15,73,76,.16);color:#fff!important}
      .vp-routines-coach *{color:inherit}
      .vp-routines-coach .vp-coach-kicker,.vp-routines-coach .template-meta{display:block;margin-bottom:5px;color:#79f0dc!important;font-size:11px;font-weight:900;letter-spacing:.10em;text-transform:uppercase}
      .vp-routines-coach h1,.vp-routines-coach h2,.vp-routines-coach h3,.vp-routines-coach b,.vp-routines-coach strong{color:#fff!important;text-shadow:0 1px 1px rgba(0,0,0,.08)}
      .vp-routines-coach h2,.vp-routines-coach h3{margin:0 0 7px;font-size:22px;line-height:1.12;letter-spacing:-.02em}
      .vp-routines-coach p,.vp-routines-coach .muted,.vp-routines-coach small,.vp-routines-coach span:not(.vp-coach-kicker):not(.template-meta){color:#daf2ee!important;opacity:1!important;line-height:1.45}
      .vp-routines-coach button.primary,.vp-routines-coach [data-vp-smart-open],.vp-routines-coach button{min-height:48px;margin-top:14px;border:0;border-radius:15px;background:linear-gradient(90deg,#40dbc6,#67e7d7)!important;color:#0b3438!important;font-weight:900;box-shadow:none}

      .vp-routines-active{position:relative;display:grid;grid-template-columns:48px 1fr auto;gap:12px;align-items:center;overflow:hidden;padding:15px 16px;margin:0 0 20px;border-radius:20px;border:1px solid rgba(22,169,142,.23);background:linear-gradient(145deg,#f7fffd 0%,#edf9f6 100%);box-shadow:0 9px 24px rgba(16,46,56,.06);cursor:pointer}
      .vp-routines-active:before{content:'';position:absolute;inset:0 auto 0 0;width:4px;background:linear-gradient(#16a98e,#2f80ed)}
      .vp-active-icon{display:grid;place-items:center;width:44px;height:44px;border-radius:14px;background:#e1f8f3;color:#126c63}
      .vp-active-icon svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
      .vp-active-copy{min-width:0}.vp-routines-active-top{display:flex;align-items:center;justify-content:space-between;gap:8px}.vp-routines-active .vp-label{color:#16a98e;font-size:10px;font-weight:900;letter-spacing:.09em;text-transform:uppercase}.vp-routines-active .vp-status{display:inline-flex;align-items:center;gap:5px;padding:5px 9px;border-radius:999px;background:#dcf7f0;color:#117965;font-size:10px;font-weight:850}.vp-routines-active .vp-status:before{content:'';width:7px;height:7px;border-radius:50%;background:#16a98e;box-shadow:0 0 0 4px rgba(22,169,142,.11)}
      .vp-routines-active h2{margin:5px 0 3px;color:#102e38;font-size:19px;line-height:1.2;letter-spacing:-.025em}.vp-routines-active p{margin:0;color:#64787e;font-size:12px;line-height:1.35}.vp-active-chevron{color:#355f68}.vp-active-chevron svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}

      #vp-routines-accordion{display:grid!important;gap:8px!important;margin-top:0!important}
      .vp-group-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin:18px 0 5px;padding:0 2px}
      .vp-group-heading:first-child{margin-top:0}.vp-group-heading b{font-size:18px;color:#113944;letter-spacing:-.025em}.vp-group-heading span{font-size:11px;color:#819298;text-align:right}
      .vp-routines-page .vp-routine-section{margin:0!important;border:1px solid rgba(22,58,67,.09)!important;border-radius:15px!important;background:#fff!important;box-shadow:0 6px 18px rgba(16,46,56,.045)!important;overflow:hidden!important}
      .vp-routines-page .vp-routine-section>summary{list-style:none!important;display:grid!important;grid-template-columns:42px minmax(0,1fr) 26px!important;align-items:center!important;gap:12px!important;min-height:62px!important;padding:10px 13px!important;background:#fff!important;border:0!important;color:#153f49!important;cursor:pointer!important}
      .vp-routines-page .vp-routine-section>summary::-webkit-details-marker{display:none!important}
      .vp-routines-page .vp-routine-section>summary::before,.vp-routines-page .vp-routine-section>summary::after{content:none!important;display:none!important}
      .vp-section-icon{display:grid;place-items:center;width:40px;height:40px;border-radius:13px;background:linear-gradient(145deg,#e2faf5,#f0fdfa);color:#108675;box-shadow:inset 0 0 0 1px rgba(22,169,142,.11)}
      .vp-section-icon svg{width:23px;height:23px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
      .vp-section-copy{display:grid;gap:2px;min-width:0}.vp-section-title{font-size:14px;font-weight:900;line-height:1.2;color:#163a43}.vp-section-subtitle{font-size:11px;font-weight:600;line-height:1.25;color:#7a8e94}
      .vp-section-chevron{display:grid;place-items:center;color:#527078;transition:transform .18s ease}.vp-section-chevron svg{width:21px;height:21px;fill:none;stroke:currentColor;stroke-width:2.1;stroke-linecap:round;stroke-linejoin:round}.vp-routine-section[open] .vp-section-chevron{transform:rotate(90deg)}
      .vp-routines-page .vp-routine-section[open]>summary{background:linear-gradient(90deg,#fbfffe,#f3fbf8)!important;border-bottom:1px solid #e5efec!important}
      .vp-routines-page .vp-routine-section-content{padding:13px!important;background:#fbfefd!important}
      .vp-routines-page .vp-routine-section-content>.section-head{display:none!important}
      .vp-routines-page .vp-routine-section-content>.vp-custom-exercises{margin-top:0!important;padding-top:0!important;border-top:0!important}
      .vp-routines-page .vp-routine-section-content>.vp-custom-exercises>h3,.vp-routines-page .vp-routine-section-content>.vp-custom-exercises>p{display:none!important}
      .vp-routines-page .section-head{margin-top:18px}.vp-routines-page .section-head h2{letter-spacing:-.02em}
      .vp-routines-page .vp-routines-metrics,.vp-routines-page .vp-routines-quick,.vp-routines-page .vp-routine-dashboard{display:none!important}

      @media(max-width:520px){
        .vp-routines-page .vp-routines-hero{padding:19px 17px}.vp-routines-coach{padding:17px}.vp-routines-coach h2,.vp-routines-coach h3{font-size:20px}
        .vp-routines-active{grid-template-columns:44px 1fr auto;padding:14px 14px;gap:10px}.vp-active-icon{width:40px;height:40px}.vp-routines-active h2{font-size:18px}
        .vp-group-heading{margin-top:16px}.vp-group-heading b{font-size:17px}.vp-group-heading span{font-size:10px}
        .vp-routines-page .vp-routine-section>summary{min-height:58px!important;padding:9px 11px!important;grid-template-columns:40px minmax(0,1fr) 24px!important;gap:10px!important}.vp-section-icon{width:38px;height:38px}.vp-section-title{font-size:13px}
      }
    `;
    document.head.appendChild(style);
  }

  function readState() {
    return new Promise(resolve => {
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

  function extractCount(text) {
    const match = String(text || '').match(/(?:·|\()\s*(\d+)\s*\)?\s*$/);
    return match ? Number(match[1]) : null;
  }

  const SECTION_META = {
    'personal-routines': { title: 'Rutinas personales', icon: 'folder', subtitle: count => count == null ? 'Gestiona tus rutinas guardadas' : `${count} rutina${count === 1 ? '' : 's'} guardada${count === 1 ? '' : 's'}` },
    'routine-history': { title: 'Historial de rutinas', icon: 'history', subtitle: count => count == null ? 'Consulta tus rutinas utilizadas' : `${count} rutina${count === 1 ? '' : 's'} registrada${count === 1 ? '' : 's'}` },
    'custom': { title: 'Crea tu propia rutina', icon: 'clipboard', subtitle: () => 'Diseña tu rutina desde cero' },
    'add-exercise': { title: 'Añade tu ejercicio', icon: 'dumbbellPlus', subtitle: () => 'Crea un ejercicio personalizado' },
    'predefined-routines': { title: 'Rutinas predefinidas', icon: 'layers', subtitle: () => 'Rutinas listas para entrenar' },
    'predefined-exercises': { title: 'Ejercicios predefinidos', icon: 'dumbbell', subtitle: () => 'Explora nuestra biblioteca de ejercicios' }
  };

  function enhanceSummary(details) {
    const key = details.dataset.vpSection;
    const meta = SECTION_META[key];
    const summary = details.querySelector(':scope > summary');
    if (!meta || !summary || summary.dataset.vpPolished === '1') return;
    const count = extractCount(summary.textContent);
    summary.dataset.vpPolished = '1';
    summary.innerHTML = `<span class="vp-section-icon">${ICONS[meta.icon]}</span><span class="vp-section-copy"><span class="vp-section-title">${meta.title}</span><span class="vp-section-subtitle">${meta.subtitle(count)}</span></span><span class="vp-section-chevron">${ICONS.chevron}</span>`;
  }

  function addGroupHeading(accordion, beforeNode, title, subtitle, key) {
    if (!beforeNode || accordion.querySelector(`[data-vp-group="${key}"]`)) return;
    const heading = document.createElement('div');
    heading.className = 'vp-group-heading';
    heading.dataset.vpGroup = key;
    heading.innerHTML = `<b>${title}</b><span>${subtitle}</span>`;
    accordion.insertBefore(heading, beforeNode);
  }

  function reorderAccordion(app) {
    const accordion = app.querySelector('#vp-routines-accordion');
    if (!accordion) return;
    accordion.querySelectorAll('.vp-group-heading').forEach(x => x.remove());

    const get = key => accordion.querySelector(`.vp-routine-section[data-vp-section="${key}"]`);
    const order = ['personal-routines','routine-history','custom','add-exercise','predefined-routines','predefined-exercises'];
    order.forEach(key => { const el = get(key); if (el) accordion.appendChild(el); });
    accordion.querySelectorAll('.vp-routine-section').forEach(enhanceSummary);

    addGroupHeading(accordion, get('personal-routines') || get('routine-history'), 'Mis rutinas', 'Gestiona tus rutinas', 'mine');
    addGroupHeading(accordion, get('custom') || get('add-exercise'), 'Crear', 'Personaliza tu entrenamiento', 'create');
    addGroupHeading(accordion, get('predefined-routines') || get('predefined-exercises'), 'Descubrir', 'Explora y encuentra inspiración', 'discover');
  }

  function findCoach(app) {
    const direct = app.querySelector('.vp-routines-coach');
    if (direct) return direct;
    const candidates = [...app.querySelectorAll('.card,section,div')].filter(el => /vitalpeak coach/i.test((el.textContent || '').trim()));
    if (!candidates.length) return null;
    return candidates.sort((a,b) => a.querySelectorAll('*').length - b.querySelectorAll('*').length)[0];
  }

  function polishCoach(app, hero) {
    let coach = findCoach(app);
    if (!coach) {
      coach = document.createElement('section');
      coach.className = 'vp-routines-coach';
      coach.innerHTML = `<span class="vp-coach-kicker">VitalPeak Coach</span><h2>Pídele a VitalPeak tu plan personalizado</h2><p>Elige tu objetivo, nivel, días y tipo de entrenamiento. VitalPeak preparará la rutina por ti.</p>`;
    } else {
      coach.classList.add('vp-routines-coach');
    }
    if (hero && hero.nextElementSibling !== coach) hero.insertAdjacentElement('afterend', coach);
    return coach;
  }

  function buildActiveCard(app, state, coach) {
    const routines = Array.isArray(state.routines) ? state.routines : [];
    const active = routines.find(r => r.id === state.activeRoutineId) || routines[0] || null;
    let box = app.querySelector('.vp-routines-active');
    const heads = [...app.querySelectorAll('.section-head')];
    const activeHead = heads.find(h => /tu rutina activa/i.test(h.textContent || ''));
    const sourceList = activeHead?.nextElementSibling || null;
    const currentButtons = sourceList ? [...sourceList.querySelectorAll('button[data-action="activate-routine"]')] : [];

    if (!box) {
      box = document.createElement('section');
      box.className = 'vp-routines-active';
      if (activeHead) activeHead.replaceWith(box);
      else if (coach) coach.insertAdjacentElement('afterend', box);
    }

    if (active) {
      const sessionName = active.days?.[active.activeDay || 0]?.name || 'Sesión';
      box.innerHTML = `<span class="vp-active-icon">${ICONS.dumbbell}</span><span class="vp-active-copy"><span class="vp-routines-active-top"><span class="vp-label">Rutina activa</span><span class="vp-status">Activa</span></span><h2>${esc(active.name)}</h2><p>${items(active).length} ejercicios · ${esc(sessionName)}</p></span><span class="vp-active-chevron">${ICONS.chevron}</span>`;
      box.onclick = () => currentButtons[0]?.click();
      box.style.cursor = currentButtons.length ? 'pointer' : 'default';
    } else {
      box.innerHTML = `<span class="vp-active-icon">${ICONS.dumbbell}</span><span class="vp-active-copy"><span class="vp-label">Rutina activa</span><h2>Sin rutina seleccionada</h2><p>Elige un plan preparado o crea uno con VitalPeak Coach.</p></span>`;
      box.onclick = null;
      box.style.cursor = 'default';
    }

    if (sourceList && sourceList !== box) sourceList.remove();
    if (coach && coach.nextElementSibling !== box) coach.insertAdjacentElement('afterend', box);
  }

  async function enhanceRoutines() {
    injectStyles();
    const app = document.querySelector('#app');
    if (!app) return;
    const routeBtn = document.querySelector('.tabbar button[data-route="routines"].active');
    const looksLikeRoutines = routeBtn || /Planes y ejercicios|RUTINAS/.test(app.textContent || '');
    if (!looksLikeRoutines) return;

    const state = await readState();
    app.classList.add('vp-routines-page');
    app.querySelectorAll('.vp-routines-metrics,.vp-routines-quick,.vp-routine-dashboard').forEach(el => el.remove());

    const hero = app.querySelector('.hero');
    if (hero) hero.classList.add('vp-routines-hero');
    const coach = polishCoach(app, hero);
    buildActiveCard(app, state, coach);
    reorderAccordion(app);
  }

  const run = () => { enhanceRoutines().catch(() => {}); };
  run();
  setTimeout(run, 120);
  setTimeout(run, 420);
  setTimeout(run, 900);

  const observer = new MutationObserver(() => {
    clearTimeout(window.__vpRoutineEnhanceTimer);
    window.__vpRoutineEnhanceTimer = setTimeout(run, 45);
  });
  const root = document.querySelector('#app');
  if (root) observer.observe(root, { childList: true, subtree: true });
})();
