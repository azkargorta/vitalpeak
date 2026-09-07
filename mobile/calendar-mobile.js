(() => {
  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  const COLORS = ['#D32F2F','#1976D2','#388E3C','#F57C00','#7B1FA2','#00838F','#C2185B','#5D4037','#455A64','#C49000'];
  let selectedDate = sessionStorage.getItem('vp-calendar-reopen-date') || null;
  let running = false;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const colorFor = value => COLORS[Math.max(0, Number(String(value || '').split('::')[1] || 0)) % COLORS.length];
  const clone = value => JSON.parse(JSON.stringify(value));
  const catalogExercises = () => Array.isArray(window.VITALPEAK_CATALOG?.exercises) ? window.VITALPEAK_CATALOG.exercises : [];

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
      .vp-day-button strong{font-size:14px;line-height:1.1}.vp-day-button.today{box-shadow:inset 0 0 0 2px #16a98e;border-radius:11px}.vp-day-button.selected{background:#e7f7f3}
      .vp-day-dots{display:flex;gap:4px;flex-wrap:wrap;justify-content:center;min-height:10px}.vp-day-dot{width:9px;height:9px;border-radius:50%;display:block;box-shadow:0 0 0 1px rgba(255,255,255,.95)}
      .vp-day-count{font-size:9px;font-weight:900;color:#60757a;line-height:1}.vp-selected-day{margin-top:16px;padding:16px;border:1px solid #d8e7e3;border-radius:18px;background:#fff;scroll-margin-top:16px}
      .vp-selected-day h2{margin:3px 0 4px;font-size:20px}.vp-selected-day .muted{margin:0 0 10px}.vp-day-workout{display:grid;grid-template-columns:7px minmax(0,1fr);gap:10px;padding:12px 0;border-top:1px solid #e2ece9}
      .vp-day-workout:first-of-type{border-top:0}.vp-workout-stripe{border-radius:99px}.vp-day-workout b{display:block;font-size:15px;line-height:1.25}.vp-day-workout small{display:block;margin-top:3px;color:#687e84}
      .vp-day-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:9px}.vp-day-actions button{min-height:38px;padding:7px 11px;border-radius:10px;font-size:12px;font-weight:800}
      .vp-day-add{display:grid;gap:6px;margin-top:12px;padding-top:12px;border-top:1px solid #e2ece9}.vp-day-add select{width:100%;min-height:46px;border:1px solid #cddfda;border-radius:12px;background:#fbfefd;padding:9px;color:#102e38;font-size:14px}
      .vp-editor-backdrop{position:fixed;inset:0;z-index:500;background:rgba(9,30,35,.72);backdrop-filter:blur(6px);padding:max(10px,env(safe-area-inset-top)) 10px max(10px,env(safe-area-inset-bottom));display:flex;align-items:stretch;justify-content:center}
      .vp-editor{width:min(720px,100%);background:#f4f9f7;border-radius:22px;overflow:auto;box-shadow:0 22px 70px rgba(0,0,0,.28);color:#14333b}
      .vp-editor-head{position:sticky;top:0;z-index:3;background:rgba(244,249,247,.96);backdrop-filter:blur(10px);padding:18px 18px 12px;border-bottom:1px solid #dbe8e4;display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
      .vp-editor-head h2{margin:3px 0 2px;font-size:23px}.vp-editor-head p{margin:0;color:#63797f;font-size:13px}.vp-editor-close{width:42px;height:42px;border:0;border-radius:50%;background:#fff;color:#14333b;font-size:27px;line-height:1;box-shadow:0 4px 13px rgba(0,0,0,.1)}
      .vp-editor-body{padding:14px 16px 110px}.vp-editor-note{padding:11px 12px;border-radius:13px;background:#e8f6f2;color:#355e5a;font-size:13px;margin-bottom:12px}
      .vp-edit-row{background:#fff;border:1px solid #dce8e5;border-radius:16px;padding:13px;margin-bottom:10px}.vp-edit-title{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:9px}.vp-edit-title b{font-size:14px}.vp-remove{border:0;background:#fdebed;color:#b43849;border-radius:10px;padding:7px 9px;font-weight:800;font-size:12px}
      .vp-edit-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}.vp-edit-grid label{display:grid;gap:4px;font-size:11px;font-weight:800;color:#667b80}.vp-edit-grid label:first-child{grid-column:1/-1}
      .vp-edit-grid select,.vp-edit-grid input{width:100%;min-height:42px;border:1px solid #cddfda;border-radius:11px;background:#fbfefd;padding:8px;color:#15343c;font-size:14px}
      .vp-alt-button{margin-top:9px;width:100%;min-height:38px;border:1px solid #acd8cf;background:#edf8f5;color:#176c60;border-radius:10px;font-weight:800}
      .vp-alternatives{display:grid;gap:6px;margin-top:8px}.vp-alternative{border:1px solid #d7e7e2;background:#fff;border-radius:11px;padding:9px;text-align:left;color:#163a43}.vp-alternative b{display:block;font-size:13px}.vp-alternative span{font-size:11px;color:#6b8085}
      .vp-add-card{margin-top:14px;padding:13px;border-radius:15px;background:#eaf6f3}.vp-add-card b{display:block;margin-bottom:8px}.vp-add-card select{width:100%;min-height:44px;border:1px solid #cddfda;border-radius:11px;background:#fff;padding:8px;color:#15343c}
      .vp-editor-save{position:sticky;bottom:0;z-index:4;background:rgba(244,249,247,.97);backdrop-filter:blur(10px);border-top:1px solid #dbe8e4;padding:12px 16px calc(12px + env(safe-area-inset-bottom));display:grid;grid-template-columns:1fr 1fr;gap:8px}
      .vp-editor-save button{min-height:48px;border-radius:13px;font-weight:900;font-size:14px}.vp-save-day{border:1px solid #16a98e;background:#fff;color:#157f70}.vp-save-routine{border:0;background:#4fd3c1;color:#12383a}
      @media(max-width:390px){.vp-calendar-ready .month-calendar{gap:3px!important}.vp-day-button{min-height:58px}.vp-day-dot{width:8px;height:8px}.vp-edit-grid{grid-template-columns:1fr 1fr}.vp-edit-grid label:first-child{grid-column:1/-1}.vp-editor-save{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 2);
      req.onerror = () => reject(req.error);
      req.onupgradeneeded = () => { if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE); };
      req.onsuccess = () => resolve(req.result);
    });
  }

  async function readState() {
    try {
      const db = await openDb();
      return await new Promise(resolve => {
        const tx = db.transaction(STORE, 'readonly');
        const get = tx.objectStore(STORE).get('user');
        get.onsuccess = () => resolve(get.result || null);
        get.onerror = () => resolve(null);
      });
    } catch { return null; }
  }

  async function writeState(state) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.objectStore(STORE).put(state, 'user');
    });
  }

  function routineById(state, id) { return (state?.routines || []).find(r => String(r.id) === String(id)) || null; }
  function entriesFor(state, date) { const raw = state?.plan?.[date]; return Array.isArray(raw) ? raw : raw ? [raw] : []; }
  function workoutInfo(state, value) {
    const [id, dayRaw] = String(value || '').split('::');
    const day = Number(dayRaw || 0), routine = routineById(state, id), routineDay = routine?.days?.[day];
    return { routine, day, name: routineDay?.name || routine?.name || `Día ${day + 1}`, count: routineDay?.items?.length || routine?.exercises?.length || 0 };
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

  function alternativesFor(name) {
    const all = catalogExercises(), current = all.find(x => x.name === name), group = current?.group;
    const preferred = all.filter(x => x.name !== name && group && x.group === group);
    const fallback = all.filter(x => x.name !== name && !preferred.some(p => p.name === x.name));
    return [...preferred, ...fallback].slice(0, 3);
  }

  function exerciseOptions(selected) {
    return catalogExercises().map(x => `<option value="${esc(x.name)}" ${x.name === selected ? 'selected' : ''}>${esc(x.name)} · ${esc(x.group || 'Otro')}</option>`).join('');
  }

  function renderEditorRows(container, draft) {
    container.innerHTML = draft.map((item, index) => `
      <div class="vp-edit-row" data-edit-index="${index}">
        <div class="vp-edit-title"><b>Ejercicio ${index + 1}</b><button type="button" class="vp-remove" data-remove-index="${index}">Quitar</button></div>
        <div class="vp-edit-grid">
          <label>Ejercicio<select data-field="exercise" data-index="${index}">${exerciseOptions(item.exercise)}</select></label>
          <label>Series<input type="number" min="1" max="20" value="${Number(item.sets || 3)}" data-field="sets" data-index="${index}"></label>
          <label>Repeticiones<input type="number" min="1" max="100" value="${Number(item.reps || 10)}" data-field="reps" data-index="${index}"></label>
          <label>Descanso (s)<input type="number" min="0" max="900" step="5" value="${Number(item.rest_sec || 90)}" data-field="rest_sec" data-index="${index}"></label>
        </div>
        <button type="button" class="vp-alt-button" data-alt-index="${index}">Mostrar 3 alternativas</button>
        <div class="vp-alternatives" data-alt-list="${index}" hidden></div>
      </div>`).join('');
  }

  async function openWorkoutEditor(date, value) {
    const state = await readState();
    if (!state) return;
    const info = workoutInfo(state, value);
    if (!info.routine) return;
    const sourceItems = info.routine.days?.[info.day]?.items || info.routine.exercises || [];
    const draft = clone(sourceItems);
    if (!draft.length) draft.push({ exercise: catalogExercises()[0]?.name || 'Ejercicio', sets: 3, reps: 10, rest_sec: 90, weight: 0 });

    const overlay = document.createElement('div');
    overlay.className = 'vp-editor-backdrop';
    const formatted = new Intl.DateTimeFormat('es-ES', { weekday:'long', day:'numeric', month:'long' }).format(new Date(`${date}T12:00:00`));
    overlay.innerHTML = `<div class="vp-editor"><div class="vp-editor-head"><div><span class="template-meta">ENTRENAMIENTO DEL DÍA</span><h2>${esc(info.name)}</h2><p>${esc(formatted)} · ${esc(info.routine.name || '')}</p></div><button type="button" class="vp-editor-close" aria-label="Cerrar">×</button></div><div class="vp-editor-body"><div class="vp-editor-note">Puedes cambiar ejercicios, series, repeticiones y descanso. En cada ejercicio puedes pedir 3 alternativas.</div><div data-editor-rows></div><div class="vp-add-card"><b>Añadir ejercicio</b><select data-add-exercise><option value="">Selecciona un ejercicio…</option>${catalogExercises().map(x => `<option value="${esc(x.name)}">${esc(x.name)} · ${esc(x.group || 'Otro')}</option>`).join('')}</select></div></div><div class="vp-editor-save"><button type="button" class="vp-save-day">Guardar solo este día</button><button type="button" class="vp-save-routine">Guardar rutina completa</button></div></div>`;
    document.body.appendChild(overlay);
    const rows = overlay.querySelector('[data-editor-rows]');
    const redraw = () => renderEditorRows(rows, draft);
    redraw();

    overlay.querySelector('.vp-editor-close').addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
    rows.addEventListener('change', e => {
      const index = Number(e.target.dataset.index), field = e.target.dataset.field;
      if (!Number.isInteger(index) || !field || !draft[index]) return;
      draft[index][field] = field === 'exercise' ? e.target.value : Number(e.target.value);
    });
    rows.addEventListener('click', e => {
      const remove = e.target.closest('[data-remove-index]');
      if (remove) {
        if (draft.length <= 1) return;
        draft.splice(Number(remove.dataset.removeIndex), 1); redraw(); return;
      }
      const alt = e.target.closest('[data-alt-index]');
      if (alt) {
        const index = Number(alt.dataset.altIndex), box = rows.querySelector(`[data-alt-list="${index}"]`), options = alternativesFor(draft[index]?.exercise);
        box.hidden = !box.hidden;
        if (!box.hidden) box.innerHTML = options.map(x => `<button type="button" class="vp-alternative" data-use-alt="${index}" data-alt-name="${esc(x.name)}"><b>${esc(x.name)}</b><span>${esc(x.group || '')}</span></button>`).join('') || '<span class="muted small">No hay alternativas disponibles.</span>';
        return;
      }
      const use = e.target.closest('[data-use-alt]');
      if (use) { const index = Number(use.dataset.useAlt); if (draft[index]) { draft[index].exercise = use.dataset.altName; redraw(); } }
    });
    overlay.querySelector('[data-add-exercise]').addEventListener('change', e => {
      if (!e.target.value) return;
      draft.push({ exercise: e.target.value, sets: 3, reps: 10, rest_sec: 90, weight: 0 }); e.target.value = ''; redraw();
      requestAnimationFrame(() => rows.lastElementChild?.scrollIntoView({ behavior:'smooth', block:'center' }));
    });

    const finish = async mode => {
      if (!draft.length) return;
      const fresh = await readState();
      if (!fresh) return;
      const [routineId, dayRaw] = String(value).split('::'), day = Number(dayRaw || 0), routine = routineById(fresh, routineId);
      if (!routine) return;
      if (mode === 'routine') {
        if (routine.days?.[day]) routine.days[day].items = clone(draft); else routine.exercises = clone(draft);
      } else {
        const oneId = `single-${date}-${Date.now()}`;
        const oneRoutine = { id: oneId, name: `${routine.name} · ${routine.days?.[day]?.name || 'Entrenamiento'} · ${date}`, days:[{ name:routine.days?.[day]?.name || 'Entrenamiento', focus:'Ajuste puntual', items:clone(draft) }], activeDay:0, source:'single-day' };
        fresh.routines = fresh.routines || [];
        fresh.routines.unshift(oneRoutine);
        const current = fresh.plan?.[date];
        if (Array.isArray(current)) fresh.plan[date] = current.map(x => String(x) === String(value) ? `${oneId}::0` : x);
        else fresh.plan[date] = `${oneId}::0`;
      }
      await writeState(fresh);
      sessionStorage.setItem('vp-calendar-open-after-reload', '1');
      sessionStorage.setItem('vp-calendar-reopen-date', date);
      location.reload();
    };
    overlay.querySelector('.vp-save-day').addEventListener('click', () => finish('day'));
    overlay.querySelector('.vp-save-routine').addEventListener('click', () => finish('routine'));
  }

  function renderDetail(state, date, panel) {
    const entries = entriesFor(state, date);
    const sourceSelect = document.querySelector(`.month-day select[data-plan-add-date="${CSS.escape(date)}"]`);
    const addOptions = sourceSelect ? sourceSelect.innerHTML : '<option value="">Añadir entrenamiento…</option>';
    const formatted = new Intl.DateTimeFormat('es-ES', { weekday:'long', day:'numeric', month:'long' }).format(new Date(`${date}T12:00:00`));
    panel.innerHTML = `<span class="template-meta">DÍA SELECCIONADO</span><h2>${esc(formatted.charAt(0).toUpperCase() + formatted.slice(1))}</h2><p class="muted">${entries.length ? `${entries.length} entrenamiento${entries.length > 1 ? 's' : ''} asignado${entries.length > 1 ? 's' : ''}` : 'Día libre · sin entrenamientos asignados'}</p><div class="vp-day-workouts">${entries.map(value => { const info = workoutInfo(state, value); return `<div class="vp-day-workout"><span class="vp-workout-stripe" style="background:${colorFor(value)}"></span><div><b>${esc(info.name)}</b><small>${esc(info.routine?.name || '')}${info.count ? ` · ${info.count} ejercicios` : ''}</small><div class="vp-day-actions"><button class="secondary" type="button" data-vp-view="${esc(value)}">Ver / editar</button><button class="danger" type="button" data-vp-remove="${esc(value)}">Quitar</button></div></div></div>`; }).join('')}</div><label class="vp-day-add"><span class="muted small">Añadir entrenamiento a este día</span><select data-vp-add>${addOptions}</select></label>`;
    panel.querySelector('[data-vp-add]')?.addEventListener('change', e => { if (e.target.value) triggerOriginalAdd(date, e.target.value); });
    panel.querySelectorAll('[data-vp-remove]').forEach(btn => btn.addEventListener('click', () => triggerOriginalAction(date, btn.dataset.vpRemove, 'remove-plan-entry')));
    panel.querySelectorAll('[data-vp-view]').forEach(btn => btn.addEventListener('click', () => openWorkoutEditor(date, btn.dataset.vpView)));
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
      if (!panel) { panel = document.createElement('section'); panel.id = 'vp-selected-day'; panel.className = 'vp-selected-day'; calendar.insertAdjacentElement('afterend', panel); }
      const cells = [...calendar.querySelectorAll('.month-day')].filter(cell => !cell.classList.contains('blank'));
      let firstDate = null;
      for (const cell of cells) {
        const originalSelect = cell.querySelector('select[data-plan-add-date]'), date = originalSelect?.dataset.planAddDate;
        if (!date) continue;
        firstDate ||= date;
        const dayNumber = cell.querySelector(':scope > b')?.textContent?.trim() || String(Number(date.slice(-2))), entries = entriesFor(state, date), button = document.createElement('button');
        button.type = 'button'; button.className = 'vp-day-button'; if (cell.classList.contains('today')) button.classList.add('today'); if (date === selectedDate) button.classList.add('selected'); button.dataset.vpDate = date;
        button.innerHTML = `<strong>${esc(dayNumber)}</strong><span class="vp-day-dots">${entries.slice(0,5).map(value => `<i class="vp-day-dot" style="background:${colorFor(value)}"></i>`).join('')}</span>${entries.length > 1 ? `<span class="vp-day-count">${entries.length} entrenos</span>` : ''}`;
        button.addEventListener('click', async () => { selectedDate = date; sessionStorage.setItem('vp-calendar-reopen-date', date); const fresh = await readState(); document.querySelectorAll('.vp-day-button.selected').forEach(x => x.classList.remove('selected')); button.classList.add('selected'); renderDetail(fresh, date, panel); requestAnimationFrame(() => panel.scrollIntoView({ behavior:'smooth', block:'start' })); });
        cell.appendChild(button);
      }
      const initial = selectedDate && cells.some(c => c.querySelector(`select[data-plan-add-date="${CSS.escape(selectedDate)}"]`)) ? selectedDate : (cells.find(c => c.classList.contains('today'))?.querySelector('select[data-plan-add-date]')?.dataset.planAddDate || firstDate);
      if (initial) { selectedDate = initial; calendar.querySelector(`.vp-day-button[data-vp-date="${CSS.escape(initial)}"]`)?.classList.add('selected'); renderDetail(state, initial, panel); if (sessionStorage.getItem('vp-calendar-scroll-after-reload') === '1') { sessionStorage.removeItem('vp-calendar-scroll-after-reload'); requestAnimationFrame(() => panel.scrollIntoView({ behavior:'smooth', block:'start' })); } }
    } finally { running = false; }
  }

  let timer = null;
  const observer = new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(enhance, 40); });
  const openPlannerAfterReload = () => {
    if (sessionStorage.getItem('vp-calendar-open-after-reload') !== '1') return;
    let tries = 0;
    const attempt = () => {
      const app = document.querySelector('#app'), button = document.querySelector('[data-route="planner"]');
      if (app?.textContent?.trim() && button) { sessionStorage.removeItem('vp-calendar-open-after-reload'); sessionStorage.setItem('vp-calendar-scroll-after-reload','1'); button.click(); }
      else if (tries++ < 80) setTimeout(attempt, 50);
    };
    attempt();
  };
  const start = () => { const app = document.querySelector('#app'); if (!app) return setTimeout(start, 50); observer.observe(app, { childList:true }); enhance(); openPlannerAfterReload(); };
  start();
})();
