(() => {
  const STYLE_ID = 'vp-routines-redesign-styles';

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .vp-routines-page .vp-routines-hero {
        position: relative;
        overflow: hidden;
        padding: 22px 20px 20px;
        margin: 0 0 14px;
        border: 1px solid rgba(60, 133, 255, .22);
        border-radius: 24px;
        background:
          radial-gradient(circle at 88% 20%, rgba(57, 134, 255, .30), transparent 36%),
          linear-gradient(135deg, #0c1a24 0%, #102934 58%, #10222d 100%);
        box-shadow: 0 18px 42px rgba(13, 38, 49, .18);
      }
      .vp-routines-page .vp-routines-hero .app-brand { margin-bottom: 18px; }
      .vp-routines-page .vp-routines-hero .wordmark,
      .vp-routines-page .vp-routines-hero .wordmark span { color: #fff; }
      .vp-routines-page .vp-routines-hero .eyebrow { color: #70b5ff; letter-spacing: .13em; }
      .vp-routines-page .vp-routines-hero h1 { color: #fff; font-size: clamp(30px, 8vw, 42px); margin: 5px 0 6px; letter-spacing: -.04em; }
      .vp-routines-page .vp-routines-hero p { color: #c0d0d8; max-width: 620px; }
      .vp-routines-page .vp-routines-hero::after {
        content: '';
        position: absolute;
        width: 210px;
        height: 210px;
        right: -88px;
        bottom: -124px;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,.09);
        pointer-events: none;
      }
      .vp-routines-dashboard { display: grid; gap: 12px; margin: 0 0 20px; }
      .vp-routines-active {
        position: relative;
        overflow: hidden;
        padding: 18px;
        border-radius: 20px;
        border: 1px solid rgba(22,169,142,.22);
        background: linear-gradient(145deg, #f6fffc 0%, #edf8f5 100%);
        box-shadow: 0 10px 26px rgba(16,46,56,.07);
      }
      .vp-routines-active::before {
        content: '';
        position: absolute;
        inset: 0 auto 0 0;
        width: 5px;
        background: linear-gradient(#16a98e, #2f80ed);
      }
      .vp-routines-active-top { display:flex; align-items:center; justify-content:space-between; gap:10px; }
      .vp-routines-active .vp-label { color:#16a98e; font-size:11px; font-weight:900; letter-spacing:.09em; text-transform:uppercase; }
      .vp-routines-active .vp-status {
        display:inline-flex; align-items:center; gap:6px; padding:5px 9px; border-radius:999px;
        background:#dff7f0; color:#117965; font-size:11px; font-weight:800;
      }
      .vp-routines-active .vp-status::before { content:''; width:7px; height:7px; border-radius:50%; background:#16a98e; box-shadow:0 0 0 4px rgba(22,169,142,.10); }
      .vp-routines-active h2 { margin:8px 0 4px; color:#102e38; font-size:22px; letter-spacing:-.025em; }
      .vp-routines-active p { margin:0; color:#63777d; font-size:13px; }
      .vp-routines-metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:9px; }
      .vp-routines-metric {
        min-width:0; padding:13px 12px; border-radius:16px; border:1px solid rgba(22,58,67,.10);
        background:#fff; box-shadow:0 7px 20px rgba(16,46,56,.05);
      }
      .vp-routines-metric b { display:block; color:#102e38; font-size:20px; line-height:1; }
      .vp-routines-metric span { display:block; margin-top:6px; color:#6d7e83; font-size:10px; font-weight:800; line-height:1.2; text-transform:uppercase; letter-spacing:.035em; }
      .vp-routines-quick { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }
      .vp-routines-quick button {
        min-height:62px; padding:10px 8px; border:1px solid rgba(22,58,67,.11); border-radius:15px;
        background:#fff; color:#163a43; font:inherit; font-size:12px; font-weight:850; line-height:1.15;
        box-shadow:0 6px 18px rgba(16,46,56,.045); cursor:pointer;
      }
      .vp-routines-quick button:first-child { background:#163a43; color:#fff; border-color:#163a43; }
      .vp-routines-quick button:active { transform:translateY(1px); }
      .vp-routines-page .section-head { margin-top:24px; margin-bottom:10px; align-items:center; }
      .vp-routines-page .section-head h2 { letter-spacing:-.02em; }
      .vp-routines-page .vp-routines-saved-list {
        display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px;
      }
      .vp-routines-page .vp-routines-saved-list .list-button {
        min-height:112px; margin:0; padding:15px; border-radius:18px; align-items:flex-start;
        border:1px solid rgba(22,58,67,.11); background:linear-gradient(180deg,#fff,#f9fcfb);
        box-shadow:0 7px 20px rgba(16,46,56,.045);
      }
      .vp-routines-page .vp-routines-saved-list .list-button.vp-is-active {
        border-color:rgba(22,169,142,.45); background:linear-gradient(145deg,#f3fffb,#fff);
        box-shadow:0 10px 24px rgba(22,169,142,.09);
      }
      .vp-routines-page .vp-routines-saved-list .list-button b { font-size:15px; line-height:1.2; margin-top:4px; }
      .vp-routines-page #vp-routines-plans + .filter-row {
        padding:12px; border-radius:16px; background:#f2f8f6; border:1px solid #dfebe7; margin-bottom:10px;
      }
      .vp-routines-page .exercise-grid { gap:10px; }
      .vp-routines-page .exercise-card { border-radius:16px; box-shadow:0 6px 18px rgba(16,46,56,.045); }
      .vp-routines-page .vp-routines-create-card { border-radius:20px; border:1px solid rgba(22,58,67,.11); box-shadow:0 10px 26px rgba(16,46,56,.06); }
      .vp-routines-page .vp-routines-section-note { margin:-3px 0 10px; color:#6c7f85; font-size:12px; }
      @media (min-width: 760px) {
        .vp-routines-dashboard { grid-template-columns:1.2fr .8fr; align-items:stretch; }
        .vp-routines-active { grid-row:span 2; display:flex; flex-direction:column; justify-content:center; min-height:172px; }
        .vp-routines-quick { align-self:end; }
        .vp-routines-page .vp-routines-saved-list { grid-template-columns:repeat(3,minmax(0,1fr)); }
      }
      @media (max-width: 520px) {
        .vp-routines-page .vp-routines-hero { border-radius:20px; padding:18px 16px; }
        .vp-routines-metrics { grid-template-columns:repeat(3,1fr); gap:7px; }
        .vp-routines-metric { padding:11px 9px; }
        .vp-routines-metric b { font-size:18px; }
        .vp-routines-metric span { font-size:9px; }
        .vp-routines-quick { grid-template-columns:repeat(2,1fr); }
        .vp-routines-page .vp-routines-saved-list { grid-template-columns:1fr; }
      }
    `;
    document.head.appendChild(style);
  }

  function getSectionHead(app, title) {
    return [...app.querySelectorAll('.section-head')].find(head =>
      head.querySelector('h2')?.textContent.trim().toLowerCase() === title.toLowerCase()
    ) || null;
  }

  function scrollToId(id) {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function enhanceRoutines() {
    const app = document.querySelector('#app');
    const hero = app?.querySelector('.hero');
    const eyebrow = hero?.querySelector('.eyebrow');
    if (!app || !hero || eyebrow?.textContent.trim().toUpperCase() !== 'RUTINAS') return;
    if (app.querySelector('.vp-routines-dashboard')) return;

    injectStyles();
    app.classList.add('vp-routines-page');
    hero.classList.add('vp-routines-hero');
    const h1 = hero.querySelector('h1');
    const intro = hero.querySelector('p');
    if (h1) h1.textContent = 'Mis rutinas';
    if (intro) intro.textContent = 'Organiza tus planes, elige qué entrenar y ten siempre a mano tu siguiente sesión.';

    const savedHead = getSectionHead(app, 'Tu rutina activa');
    const plansHead = getSectionHead(app, 'Planes preparados');
    const exercisesHead = getSectionHead(app, 'Catálogo de ejercicios');
    const createHead = getSectionHead(app, 'Rutina personalizada');
    const savedList = savedHead?.nextElementSibling;
    const planFilter = plansHead?.nextElementSibling;
    const planList = planFilter?.nextElementSibling;
    const exerciseGrid = exercisesHead?.nextElementSibling;
    const createCard = createHead?.nextElementSibling;

    if (savedHead) {
      savedHead.id = 'vp-routines-saved';
      const title = savedHead.querySelector('h2');
      if (title) title.textContent = 'Tus rutinas';
    }
    if (plansHead) plansHead.id = 'vp-routines-plans';
    if (exercisesHead) exercisesHead.id = 'vp-routines-exercises';
    if (createHead) createHead.id = 'vp-routines-create';
    savedList?.classList.add('vp-routines-saved-list');
    createCard?.classList.add('vp-routines-create-card');

    const savedButtons = [...(savedList?.querySelectorAll('.list-button') || [])];
    savedButtons.forEach(btn => {
      const meta = btn.querySelector('.template-meta')?.textContent.toUpperCase() || '';
      btn.classList.toggle('vp-is-active', meta.includes('PLAN ACTIVO'));
    });
    const activeButton = savedButtons.find(btn => btn.classList.contains('vp-is-active')) || savedButtons[0];
    const activeName = activeButton?.querySelector('b')?.textContent.trim() || 'Aún no has elegido una rutina';
    const activeMeta = activeButton?.querySelector('.muted')?.textContent.trim() || 'Elige un plan preparado o crea el tuyo.';
    const totalPlans = Number(plansHead?.querySelector('.pill')?.textContent || 0) || planList?.querySelectorAll('.list-button').length || 0;
    const totalExercises = Number(exercisesHead?.querySelector('.pill')?.textContent || 0) || exerciseGrid?.querySelectorAll('.exercise-card').length || 0;

    const dashboard = document.createElement('section');
    dashboard.className = 'vp-routines-dashboard';
    dashboard.innerHTML = `
      <div class="vp-routines-active">
        <div class="vp-routines-active-top">
          <span class="vp-label">Rutina activa</span>
          <span class="vp-status">Lista para entrenar</span>
        </div>
        <h2>${activeName.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}</h2>
        <p>${activeMeta.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}</p>
      </div>
      <div class="vp-routines-metrics">
        <div class="vp-routines-metric"><b>${savedButtons.length}</b><span>Guardadas</span></div>
        <div class="vp-routines-metric"><b>${totalPlans}</b><span>Planes</span></div>
        <div class="vp-routines-metric"><b>${totalExercises}</b><span>Ejercicios</span></div>
      </div>
      <div class="vp-routines-quick">
        <button type="button" data-vp-scroll="vp-routines-plans">Elegir plan</button>
        <button type="button" data-vp-scroll="vp-routines-create">Crear rutina</button>
        <button type="button" data-vp-scroll="vp-routines-exercises">Ver ejercicios</button>
        <button type="button" data-route="progress">Historial</button>
      </div>
    `;

    if (savedHead) app.insertBefore(dashboard, savedHead);
    else hero.insertAdjacentElement('afterend', dashboard);

    if (plansHead && !plansHead.nextElementSibling?.classList.contains('vp-routines-section-note')) {
      const note = document.createElement('p');
      note.className = 'vp-routines-section-note';
      note.textContent = 'Filtra por días, abre un plan y personalízalo antes de guardarlo.';
      plansHead.insertAdjacentElement('afterend', note);
    }
    if (exercisesHead && !exercisesHead.nextElementSibling?.classList.contains('vp-routines-section-note')) {
      const note = document.createElement('p');
      note.className = 'vp-routines-section-note';
      note.textContent = 'Consulta técnica y movimiento de cada ejercicio.';
      exercisesHead.insertAdjacentElement('afterend', note);
    }
    if (createHead && !createHead.nextElementSibling?.classList.contains('vp-routines-section-note')) {
      const note = document.createElement('p');
      note.className = 'vp-routines-section-note';
      note.textContent = 'Crea una rutina rápida con tus ejercicios favoritos.';
      createHead.insertAdjacentElement('afterend', note);
    }
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-vp-scroll]');
    if (!button) return;
    event.preventDefault();
    scrollToId(button.dataset.vpScroll);
  });

  injectStyles();
  const observer = new MutationObserver(() => requestAnimationFrame(enhanceRoutines));
  observer.observe(document.body, { childList: true, subtree: true });
  enhanceRoutines();
})();
