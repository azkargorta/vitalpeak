(() => {
  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  const COLORS = ['#D32F2F','#1976D2','#388E3C','#F57C00','#7B1FA2','#00838F','#C2185B','#5D4037','#455A64','#C49000'];
  let selectedDate = null;
  let running = false;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const colorFor = value => COLORS[Math.max(0, Number(String(value || '').split('::')[1] || 0)) % COLORS.length];

  function ensureStyles() {
    if (document.querySelector('#vp-calendar-mobile-styles')) return;
    const style = document.createElement('style');
    style.id = 'vp-calendar-mobile-styles';
    style.textContent = `
      .vp-calendar-ready .month-calendar{gap:4px!important}
      .vp-calendar-ready .month-day{min-height:64px!important;position:relative!important;padding:0!important;overflow:hidden!important;border-radius:12px!important;background:#fff!important}
      .vp-calendar-ready .month-day.blank{visibility:hidden!important}
      .vp-calendar-ready .month-day>.calendar-entries,.vp-calendar-ready .month-day>select,.vp-calendar-ready .month-day>b{display:none!important}
      .vp-day-button{appearance:none;width:100%;height:100%;min-height:62px;border:0;background:transparent;color:#102e38;padding:7px 4px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:8px;cursor:pointer}
      .vp-day-button strong{font-size:14px;line-height:1.1}
      .vp-day-button.today{box-shadow:inset 0 0 0 2px #16a98e;border-radius:11px}
      .vp-day-button.selected{background:#e7f7f3}
      .vp-day-dots{display:flex;gap:4px;flex-wrap:wrap;justify-content:center;min-height:10px}
      .vp-day-dot{width:9px;height:9px;border-radius:50%;display:block;box-shadow:0 0 0 1px rgba(255,255,255,.95)}
      .vp-day-count{font-size:9px;font-weight:900;color:#60757a;line-height:1}
      .vp-selected-day{margin-top:16px;padding:16px;border:1px solid #d8e7e3;border-radius:18px;background:#fff;scroll-margin-top:16px}
      .vp-selected-day h2{margin:3px 0 4px;font-size:20px}
      .vp-selected-day .muted{margin:0 0 10px}
      .vp-day-workout{display:grid;grid-template-columns:7px minmax(0,1fr);gap:10px;padding:12px 0;border-top:1px solid #e2ece9}
      .vp-day-workout:first-of-type{border-top:0}
      .vp-workout-stripe{border-radius:99px}
      .vp-day-workout b{display:block;font-size:15px;line-height:1.25}
      .vp-day-workout small{display:block;margin-top:3px;color:#687e84}
      .vp-day-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:9px}
      .vp-day-actions button{min-height:38px;padding:7px 11px;border-radius:10px;font-size:12px;font-weight:800}
      .vp-day-add{display:grid;gap:6px;margin-top:12px;padding-top:12px;border-top:1px solid #e2ece9}
      .vp-day-add select{width:100%;min-height:46px;border:1px solid #cddfda;border-radius:12px;background:#fbfefd;padding:9px;color:#102e38;font-size:14px}
      @media(max-width:390px){.vp-calendar-ready .month-calendar{gap:3px!important}.vp-day-button{min-height:58px}.vp-day-dot{width:8px;height:8px}}
    `;
    document.head.appendChild(style);
  }

  function readState() {
    return new Promise(resolve => {
      const req = indexedDB.open(DB_NAME, 2);
      req.onerror = () => resolve(null);
      req.onupgradeneeded = () => { if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE); };
      req.onsuccess = () => {
        const tx = req.result.transaction(STORE, 'readonly');
        const get = tx.objectStore(STORE).get('user');
        get.onsuccess = () => resolve(get.result || null);
        get.onerror = () => resolve(null);
      };
    });
  }

  function routineById(state, id) {
    return (state?.routines || []).find(r => String(r.id) === String(id)) || null;
  }

  function entriesFor(state, date) {
    const raw = state?.plan?.[date];
    return Array.isArray(raw) ? raw : raw ? [raw] : [];
  }

  function workoutInfo(state, value) {
    const [id, dayRaw] = String(value || '').split('::');
    const day = Number(dayRaw || 0);
    const routine = routineById(state, id);
    const routineDay = routine?.days?.[day];
    return {
      routine,
      day,
      name: routineDay?.name || routine?.name || `Día ${day + 1}`,
      count: routineDay?.items?.length || routine?.exercises?.length || 0,
    };
  }

  function triggerOriginalAdd(date, value) {
    const select = document.querySelector(`.month-day select[data-plan-add-date="${CSS.escape(date)}"]`);
    if (!select || !value) return;
    select.value = value;
    select.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function triggerOriginalAction(date, value, action) {
    const node = document.querySelector(`[data-action="${action}"][data-date="${CSS.escape(date)}"][data-value="${CSS.escape(value)}"]`);
    node?.click();
  }

  function renderDetail(state, date, panel) {
    const entries = entriesFor(state, date);
    const sourceSelect = document.querySelector(`.month-day select[data-plan-add-date="${CSS.escape(date)}"]`);
    const addOptions = sourceSelect ? sourceSelect.innerHTML : '<option value="">Añadir entrenamiento…</option>';
    const formatted = new Intl.DateTimeFormat('es-ES', { weekday:'long', day:'numeric', month:'long' }).format(new Date(`${date}T12:00:00`));
    panel.innerHTML = `
      <span class="template-meta">DÍA SELECCIONADO</span>
      <h2>${esc(formatted.charAt(0).toUpperCase() + formatted.slice(1))}</h2>
      <p class="muted">${entries.length ? `${entries.length} entrenamiento${entries.length > 1 ? 's' : ''} asignado${entries.length > 1 ? 's' : ''}` : 'Día libre · sin entrenamientos asignados'}</p>
      <div class="vp-day-workouts">
        ${entries.map(value => {
          const info = workoutInfo(state, value);
          return `<div class="vp-day-workout"><span class="vp-workout-stripe" style="background:${colorFor(value)}"></span><div><b>${esc(info.name)}</b><small>${esc(info.routine?.name || '')}${info.count ? ` · ${info.count} ejercicios` : ''}</small><div class="vp-day-actions"><button class="secondary" type="button" data-vp-view="${esc(value)}">Ver / editar</button><button class="danger" type="button" data-vp-remove="${esc(value)}">Quitar</button></div></div></div>`;
        }).join('')}
      </div>
      <label class="vp-day-add"><span class="muted small">Añadir entrenamiento a este día</span><select data-vp-add>${addOptions}</select></label>`;

    panel.querySelector('[data-vp-add]')?.addEventListener('change', e => {
      if (e.target.value) triggerOriginalAdd(date, e.target.value);
    });
    panel.querySelectorAll('[data-vp-remove]').forEach(btn => btn.addEventListener('click', () => triggerOriginalAction(date, btn.dataset.vpRemove, 'remove-plan-entry')));
    panel.querySelectorAll('[data-vp-view]').forEach(btn => btn.addEventListener('click', () => triggerOriginalAction(date, btn.dataset.vpView, 'view-planned-workout')));
  }

  async function enhance() {
    if (running) return;
    const calendar = document.querySelector('.month-calendar');
    if (!calendar || calendar.dataset.vpMobile === '1') return;
    running = true;
    try {
      ensureStyles();
      const state = await readState();
      if (!state || !document.body.contains(calendar)) return;
      calendar.dataset.vpMobile = '1';
      calendar.closest('main')?.classList.add('vp-calendar-ready');

      let panel = document.querySelector('#vp-selected-day');
      if (!panel) {
        panel = document.createElement('section');
        panel.id = 'vp-selected-day';
        panel.className = 'vp-selected-day';
        calendar.insertAdjacentElement('afterend', panel);
      }

      const cells = [...calendar.querySelectorAll('.month-day')].filter(cell => !cell.classList.contains('blank'));
      let firstDate = null;
      for (const cell of cells) {
        const originalSelect = cell.querySelector('select[data-plan-add-date]');
        const date = originalSelect?.dataset.planAddDate;
        if (!date) continue;
        firstDate ||= date;
        const dayNumber = cell.querySelector(':scope > b')?.textContent?.trim() || String(Number(date.slice(-2)));
        const entries = entriesFor(state, date);
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'vp-day-button';
        if (cell.classList.contains('today')) button.classList.add('today');
        if (date === selectedDate) button.classList.add('selected');
        button.dataset.vpDate = date;
        button.innerHTML = `<strong>${esc(dayNumber)}</strong><span class="vp-day-dots">${entries.slice(0,5).map(value => `<i class="vp-day-dot" style="background:${colorFor(value)}"></i>`).join('')}</span>${entries.length > 1 ? `<span class="vp-day-count">${entries.length} entrenos</span>` : ''}`;
        button.addEventListener('click', async () => {
          selectedDate = date;
          const fresh = await readState();
          document.querySelectorAll('.vp-day-button.selected').forEach(x => x.classList.remove('selected'));
          button.classList.add('selected');
          renderDetail(fresh, date, panel);
          requestAnimationFrame(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }));
        });
        cell.appendChild(button);
      }

      const initial = selectedDate && cells.some(c => c.querySelector(`select[data-plan-add-date="${CSS.escape(selectedDate)}"]`))
        ? selectedDate
        : (cells.find(c => c.classList.contains('today'))?.querySelector('select[data-plan-add-date]')?.dataset.planAddDate || firstDate);
      if (initial) {
        selectedDate = initial;
        calendar.querySelector(`.vp-day-button[data-vp-date="${CSS.escape(initial)}"]`)?.classList.add('selected');
        renderDetail(state, initial, panel);
      }
    } finally {
      running = false;
    }
  }

  let timer = null;
  const observer = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(enhance, 40);
  });
  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 50);
    observer.observe(app, { childList: true });
    enhance();
  };
  start();
})();
