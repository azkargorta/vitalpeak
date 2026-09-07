(() => {
  const CUSTOM_EXERCISES_KEY = "vitalpeak-custom-exercises";
  const DB_NAME = "vitalpeak-mobile";
  const STORE = "state";

  let draft = newDraft();

  function newDraft() {
    return {
      id: null,
      name: "",
      dayCount: 3,
      days: Array.from({ length: 3 }, (_, i) => ({ name: `Día ${i + 1}`, items: [] })),
    };
  }

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function normalizeText(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("es")
      .trim();
  }

  function allExercises() {
    const list = window.VITALPEAK_CATALOG?.exercises || [];
    return [...list].sort((a, b) => String(a.name).localeCompare(String(b.name), "es"));
  }

  function filteredExercises(query = "") {
    const q = normalizeText(query);
    if (!q) return allExercises();
    return allExercises().filter(x => normalizeText(`${x.name} ${x.group || ""}`).includes(q));
  }

  function exerciseOptions(selected = "", query = "") {
    const list = filteredExercises(query);
    return `<option value="">${list.length ? "Selecciona un ejercicio…" : "No hay resultados"}</option>${list.map(x =>
      `<option value="${esc(x.name)}" ${x.name === selected ? "selected" : ""}>${esc(x.name)} · ${esc(x.group || "Otro")}</option>`
    ).join("")}`;
  }

  function normalizeItem(raw = {}) {
    const sets = Math.max(1, Math.min(15, Number(raw.sets || 3)));
    const baseReps = Math.max(1, Number(raw.reps || raw.repsBySet?.[0] || 10));
    const hasPerSet = Array.isArray(raw.repsBySet) && raw.repsBySet.length > 0;
    const repsBySet = Array.from({ length: sets }, (_, i) => Math.max(1, Number(raw.repsBySet?.[i] ?? baseReps)));
    const allEqual = repsBySet.every(x => x === repsBySet[0]);
    return {
      ...raw,
      sets,
      reps: baseReps,
      repsBySet,
      sameReps: raw.sameReps !== undefined ? Boolean(raw.sameReps) : (!hasPerSet || allEqual),
      rest_sec: Math.max(0, Number(raw.rest_sec ?? 90)),
      weight: Number(raw.weight || 0),
    };
  }

  function normalizeDays(count) {
    const next = [];
    for (let i = 0; i < count; i += 1) {
      next.push(draft.days[i] || { name: `Día ${i + 1}`, items: [] });
    }
    draft.dayCount = count;
    draft.days = next;
  }

  function syncReps(item) {
    item.sets = Math.max(1, Math.min(15, Number(item.sets || 1)));
    item.reps = Math.max(1, Number(item.reps || 10));
    const current = Array.isArray(item.repsBySet) ? item.repsBySet : [];
    item.repsBySet = Array.from({ length: item.sets }, (_, i) => Math.max(1, Number(current[i] ?? item.reps)));
    if (item.sameReps !== false) item.repsBySet = Array(item.sets).fill(item.reps);
  }

  function styles() {
    if (document.querySelector("#vp-routine-enhancement-styles")) return;
    const style = document.createElement("style");
    style.id = "vp-routine-enhancement-styles";
    style.textContent = `
      .vp-builder-intro{margin:0 0 14px;color:#658087;font-size:13px}
      .vp-builder-top{display:grid;grid-template-columns:1fr 112px;gap:10px;margin-bottom:14px}
      .vp-day-builder{padding:14px 0;border-top:1px solid #d8e7e3}
      .vp-day-builder:first-of-type{border-top:0}
      .vp-day-head{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end;margin-bottom:10px}
      .vp-day-head input,.vp-day-add select,.vp-day-add input,.vp-custom-exercise-form input,.vp-custom-exercise-form select{width:100%;min-height:44px;border:1px solid #cddfda;border-radius:11px;background:#fbfefd;padding:9px;color:#102e38;font-size:14px}
      .vp-day-add{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;margin:10px 0}
      .vp-exercise-search-wrap{display:grid;gap:6px;min-width:0}
      .vp-exercise-search{background:#fff!important}
      .vp-exercise-result-count{font-size:11px;color:#6a7f84;padding-left:2px}
      .vp-day-add button{min-height:44px;padding:8px 12px;border-radius:11px;background:#e8f6f2;color:#176d61;font-weight:800;align-self:end}
      .vp-builder-exercises{display:grid;gap:8px}
      .vp-builder-exercise{padding:10px;border:1px solid #d8e7e3;border-radius:12px;background:#fff}
      .vp-builder-exercise-name{display:flex;justify-content:space-between;gap:8px;align-items:start;margin-bottom:8px}
      .vp-builder-exercise-name b{font-size:13px;line-height:1.25}
      .vp-builder-exercise-name button{background:#fdecef;color:#b43b4c;border-radius:9px;padding:5px 8px;font-size:11px;font-weight:800}
      .vp-builder-values{display:grid;grid-template-columns:1fr 1fr;gap:7px;align-items:end}
      .vp-builder-values label{display:grid;gap:3px;font-size:10px;font-weight:800;color:#658087}
      .vp-builder-values input{width:100%;min-height:38px;border:1px solid #cddfda;border-radius:9px;background:#fbfefd;padding:7px;color:#102e38;font-size:13px}
      .vp-same-reps{grid-column:1/-1;display:flex!important;grid-template-columns:none!important;align-items:center;gap:8px!important;min-height:34px;font-size:12px!important;color:#244a52!important;cursor:pointer}
      .vp-same-reps input{width:18px!important;min-height:18px!important;height:18px;margin:0;accent-color:#20b59d}
      .vp-reps-by-set{grid-column:1/-1;display:grid;grid-template-columns:repeat(auto-fit,minmax(82px,1fr));gap:7px;padding:9px;border-radius:10px;background:#f3f8f6}
      .vp-reps-by-set label{font-size:10px!important}
      .vp-editing-banner{display:flex;justify-content:space-between;gap:10px;align-items:center;margin:0 0 12px;padding:10px 12px;border-radius:11px;background:#e8f6f2;color:#176d61;font-size:12px;font-weight:800}
      .vp-editing-banner button{border:0;background:#fff;border-radius:9px;padding:6px 9px;color:#176d61;font-weight:850}
      .vp-empty-day{padding:12px;border-radius:11px;background:#f3f8f6;color:#658087;font-size:12px;text-align:center}
      .vp-save-routine{margin-top:14px}
      .vp-custom-exercises{margin-top:24px;padding-top:18px;border-top:1px solid #d8e7e3}
      .vp-custom-exercises h3{margin:0 0 5px}
      .vp-custom-exercises p{margin:0 0 12px;color:#658087;font-size:13px}
      .vp-custom-exercise-form{display:grid;grid-template-columns:1fr 140px;gap:8px}
      .vp-custom-exercise-form button{grid-column:1/-1}
      .vp-my-exercises{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
      .vp-my-exercise{padding:6px 9px;border-radius:99px;background:#edf8f5;color:#176d61;font-size:11px;font-weight:750}
      .vp-personal-backdrop{position:fixed;inset:0;z-index:760;background:rgba(8,29,34,.72);backdrop-filter:blur(7px);display:flex;align-items:stretch;justify-content:center;padding:max(10px,env(safe-area-inset-top)) 10px max(10px,env(safe-area-inset-bottom))}
      .vp-personal-modal{width:min(720px,100%);background:#f4f9f7;border-radius:22px;overflow:auto;color:#14343b;box-shadow:0 24px 70px rgba(0,0,0,.28)}
      .vp-personal-head{position:sticky;top:0;z-index:2;background:rgba(244,249,247,.97);padding:18px;border-bottom:1px solid #dbe8e4;display:flex;justify-content:space-between;gap:12px}.vp-personal-head h2{margin:4px 0 3px;font-size:24px}.vp-personal-head p{margin:0;color:#63797f;font-size:13px}
      .vp-personal-close{width:42px;height:42px;border:0;border-radius:50%;background:#fff;color:#14343b;font-size:27px;box-shadow:0 4px 13px rgba(0,0,0,.1)}
      .vp-personal-body{padding:16px 16px 110px;display:grid;gap:12px}.vp-personal-day{padding:13px;border:1px solid #dce8e5;border-radius:14px;background:#fff}.vp-personal-day h3{margin:0 0 9px}.vp-personal-exercises{display:grid;gap:7px}.vp-personal-exercise{padding:9px 10px;border-radius:10px;background:#f4f8f7}.vp-personal-exercise b{display:block;font-size:13px}.vp-personal-exercise span{display:block;margin-top:3px;color:#687e84;font-size:12px}
      .vp-personal-actions{position:sticky;bottom:0;background:rgba(244,249,247,.97);border-top:1px solid #dbe8e4;padding:12px 16px calc(12px + env(safe-area-inset-bottom));display:grid;grid-template-columns:1fr 1fr;gap:8px}.vp-personal-actions button{min-height:48px;border-radius:13px;font-weight:900}
      @media(max-width:480px){.vp-builder-top,.vp-custom-exercise-form{grid-template-columns:1fr}.vp-builder-values{grid-template-columns:1fr 1fr}.vp-day-add{grid-template-columns:1fr}.vp-day-add button{width:100%}.vp-personal-actions{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function customExercises() {
    try { return JSON.parse(localStorage.getItem(CUSTOM_EXERCISES_KEY) || "[]"); }
    catch { return []; }
  }

  function openDB() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 2);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function readState() {
    const db = await openDB();
    const tx = db.transaction(STORE, "readonly");
    const req = tx.objectStore(STORE).get("user");
    return new Promise((resolve, reject) => {
      req.onsuccess = () => resolve(req.result || {});
      req.onerror = () => reject(req.error);
    });
  }

  async function writeState(state) {
    const db = await openDB();
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put(state, "user");
    return new Promise((resolve, reject) => {
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  }

  function renderBuilder() {
    styles();
    const old = document.querySelector("#routine-form");
    if (!old) return;
    const card = old.closest(".card");
    if (!card) return;
    if (card.dataset.vpEnhanced !== "1") card.dataset.vpEnhanced = "1";

    card.innerHTML = `
      <div id="vp-custom-routine-builder">
        ${draft.id ? `<div class="vp-editing-banner"><span>Editando: ${esc(draft.name || "Rutina personal")}</span><button type="button" data-vp-action="cancel-edit">Cancelar edición</button></div>` : ""}
        <p class="vp-builder-intro">Crea una rutina completa de varios días. Después podrás asignar cada día de esta rutina desde el calendario.</p>
        <div class="vp-builder-top">
          <label class="field">Nombre de la rutina<input id="vp-routine-name" maxlength="50" placeholder="Ej. Fuerza 4 días" value="${esc(draft.name)}"></label>
          <label class="field">Número de días<select id="vp-routine-days">${[1,2,3,4,5,6,7].map(n => `<option value="${n}" ${n === draft.dayCount ? "selected" : ""}>${n}</option>`).join("")}</select></label>
        </div>
        <div id="vp-routine-days-container"></div>
        <button class="primary wide vp-save-routine" type="button" data-vp-action="save-routine">${draft.id ? "Guardar cambios" : "Guardar rutina"}</button>
        <div class="vp-custom-exercises">
          <h3>Mis ejercicios</h3>
          <p>Añade ejercicios propios. Después aparecerán en las listas de ejercicios de VitalPeak y podrás usarlos en tus rutinas.</p>
          <form id="vp-custom-exercise-form" class="vp-custom-exercise-form">
            <input name="name" required maxlength="70" placeholder="Nombre del ejercicio">
            <select name="group">
              ${["Pecho","Espalda","Hombro","Pierna","Brazo","Core","Cardio","Movilidad","Otro"].map(g => `<option value="${g}">${g}</option>`).join("")}
            </select>
            <button class="secondary wide" type="submit">Añadir ejercicio propio</button>
          </form>
          <div class="vp-my-exercises">${customExercises().map(x => `<span class="vp-my-exercise">${esc(x.name)}</span>`).join("")}</div>
        </div>
      </div>`;
    renderDays();
  }

  function repsControls(item, dayIndex, itemIndex) {
    syncReps(item);
    const key = `${dayIndex}:${itemIndex}`;
    return `
      <label class="vp-same-reps"><input type="checkbox" data-vp-same-reps="${key}" ${item.sameReps !== false ? "checked" : ""}> Mismas repeticiones en todas las series</label>
      ${item.sameReps !== false
        ? `<label>Repeticiones<input type="number" min="1" max="100" value="${Number(item.reps || 10)}" data-vp-item-field="${key}:reps"></label>`
        : `<div class="vp-reps-by-set">${item.repsBySet.map((value, setIndex) => `<label>Serie ${setIndex + 1}<input type="number" min="1" max="100" value="${Number(value || 1)}" data-vp-set-reps="${key}:${setIndex}"></label>`).join("")}</div>`}`;
  }

  function renderDays() {
    const container = document.querySelector("#vp-routine-days-container");
    if (!container) return;
    container.innerHTML = draft.days.map((day, dayIndex) => `
      <section class="vp-day-builder">
        <div class="vp-day-head">
          <label class="field">Nombre del día ${dayIndex + 1}<input data-vp-day-name="${dayIndex}" maxlength="40" value="${esc(day.name)}" placeholder="Ej. Pecho + tríceps"></label>
          <span class="pill">${day.items.length} ejercicios</span>
        </div>
        <div class="vp-builder-exercises">
          ${day.items.length ? day.items.map((item, itemIndex) => `
            <div class="vp-builder-exercise">
              <div class="vp-builder-exercise-name"><b>${esc(item.exercise)}</b><button type="button" data-vp-remove="${dayIndex}:${itemIndex}">Quitar</button></div>
              <div class="vp-builder-values">
                <label>Series<input type="number" min="1" max="15" value="${Number(item.sets || 3)}" data-vp-item-field="${dayIndex}:${itemIndex}:sets"></label>
                <label>Descanso (s)<input type="number" min="0" max="600" step="5" value="${Number(item.rest_sec || 90)}" data-vp-item-field="${dayIndex}:${itemIndex}:rest_sec"></label>
                ${repsControls(item, dayIndex, itemIndex)}
              </div>
            </div>`).join("") : `<div class="vp-empty-day">Añade al menos un ejercicio a este día.</div>`}
        </div>
        <div class="vp-day-add">
          <div class="vp-exercise-search-wrap">
            <input class="vp-exercise-search" type="search" inputmode="search" autocomplete="off" placeholder="Buscar ejercicio…" data-vp-exercise-search="${dayIndex}">
            <select data-vp-exercise-select="${dayIndex}">${exerciseOptions()}</select>
            <span class="vp-exercise-result-count" data-vp-exercise-count="${dayIndex}">${allExercises().length} ejercicios disponibles</span>
          </div>
          <button type="button" data-vp-action="add-exercise" data-day="${dayIndex}">+ Añadir</button>
        </div>
      </section>`).join("");
  }

  async function saveRoutine() {
    draft.name = document.querySelector("#vp-routine-name")?.value.trim() || "";
    draft.days.forEach((day, i) => {
      const input = document.querySelector(`[data-vp-day-name="${i}"]`);
      if (input) day.name = input.value.trim() || `Día ${i + 1}`;
    });
    if (!draft.name) return alert("Pon un nombre a la rutina.");
    const empty = draft.days.findIndex(d => !d.items.length);
    if (empty >= 0) return alert(`Añade al menos un ejercicio al día ${empty + 1}.`);

    const state = await readState();
    state.routines = Array.isArray(state.routines) ? state.routines : [];
    const id = draft.id || `custom-${Date.now()}`;
    const routine = {
      id,
      name: draft.name,
      days: draft.days.map((d, i) => ({
        name: d.name || `Día ${i + 1}`,
        focus: d.name || `Día ${i + 1}`,
        items: d.items.map(raw => {
          const x = normalizeItem(raw);
          syncReps(x);
          const saved = { ...x, weight: Number(x.weight || 0) };
          if (x.sameReps !== false) {
            saved.reps = x.reps;
            delete saved.repsBySet;
          } else {
            saved.reps = x.repsBySet[0] || x.reps;
            saved.repsBySet = [...x.repsBySet];
          }
          delete saved.sameReps;
          return saved;
        }),
      })),
      activeDay: 0,
      source: "custom-builder",
    };
    const existing = state.routines.findIndex(r => String(r.id) === String(id));
    if (existing >= 0) state.routines.splice(existing, 1, routine);
    else state.routines.unshift(routine);
    if (!state.activeRoutineId || String(state.activeRoutineId) === String(id) || !draft.id) state.activeRoutineId = id;
    await writeState(state);
    location.reload();
  }

  function saveCustomExercise(form) {
    const data = new FormData(form);
    const name = String(data.get("name") || "").trim();
    const group = String(data.get("group") || "Otro");
    if (!name) return;
    const all = customExercises();
    const duplicate = allExercises().some(x => x.name.toLocaleLowerCase("es") === name.toLocaleLowerCase("es"));
    if (duplicate) return alert("Ya existe un ejercicio con ese nombre.");
    all.push({
      name,
      group,
      cues: ["Realiza el movimiento con control y una postura estable.", "Ajusta el rango a tu técnica y detente si aparece dolor agudo."],
      animation: {},
      custom: true,
    });
    localStorage.setItem(CUSTOM_EXERCISES_KEY, JSON.stringify(all));
    location.reload();
  }

  function repsSummary(item) {
    const x = normalizeItem(item);
    if (Array.isArray(item.repsBySet) && item.repsBySet.length) return `${x.sets} series · reps ${x.repsBySet.join(" / ")}`;
    return `${x.sets} series × ${x.reps} reps`;
  }

  async function openPersonalRoutine(id) {
    styles();
    const state = await readState();
    const routine = (state.routines || []).find(r => String(r.id) === String(id));
    if (!routine) return;
    document.querySelector('.vp-personal-backdrop')?.remove();
    const overlay = document.createElement('div');
    overlay.className = 'vp-personal-backdrop';
    const days = Array.isArray(routine.days) ? routine.days : [];
    overlay.innerHTML = `<div class="vp-personal-modal">
      <div class="vp-personal-head"><div><span class="template-meta">RUTINA PERSONAL</span><h2>${esc(routine.name)}</h2><p>${days.length} día${days.length === 1 ? "" : "s"} · ${days.reduce((n,d)=>n+(d.items?.length||0),0)} ejercicios</p></div><button class="vp-personal-close" type="button" aria-label="Cerrar">×</button></div>
      <div class="vp-personal-body">${days.map((day, dayIndex) => `<section class="vp-personal-day"><h3>${esc(day.name || `Día ${dayIndex + 1}`)}</h3><div class="vp-personal-exercises">${(day.items || []).map((item, i) => `<div class="vp-personal-exercise"><b>${i + 1}. ${esc(item.exercise || item.name || "Ejercicio")}</b><span>${esc(repsSummary(item))} · descanso ${Number(item.rest_sec ?? 90)}s</span></div>`).join("") || `<span class="muted small">Sin ejercicios.</span>`}</div></section>`).join("")}</div>
      <div class="vp-personal-actions"><button type="button" class="secondary" data-vp-action="edit-personal-routine" data-id="${esc(routine.id)}">Editar rutina</button><button type="button" class="primary" data-vp-action="activate-personal-routine" data-id="${esc(routine.id)}">${String(state.activeRoutineId) === String(routine.id) ? "Rutina activa" : "Activar rutina"}</button></div>
    </div>`;
    document.body.appendChild(overlay);
    overlay.querySelector('.vp-personal-close').onclick = () => overlay.remove();
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  }

  async function editPersonalRoutine(id) {
    const state = await readState();
    const routine = (state.routines || []).find(r => String(r.id) === String(id));
    if (!routine) return;
    draft = {
      id: routine.id,
      name: routine.name || "",
      dayCount: Math.max(1, routine.days?.length || 1),
      days: (routine.days || []).map((day, i) => ({
        name: day.name || `Día ${i + 1}`,
        items: (day.items || []).map(normalizeItem),
      })),
    };
    if (!draft.days.length) draft.days = [{ name: "Día 1", items: [] }];
    draft.dayCount = draft.days.length;
    document.querySelector('.vp-personal-backdrop')?.remove();
    const createSection = document.querySelector('[data-vp-section="custom"]');
    if (createSection) createSection.open = true;
    const card = document.querySelector('#vp-custom-routine-builder')?.closest('.card');
    if (card) {
      card.dataset.vpEnhanced = "0";
      const builder = card.querySelector('#vp-custom-routine-builder');
      if (builder) builder.replaceWith(Object.assign(document.createElement('form'), { id: 'routine-form' }));
    }
    renderBuilder();
    setTimeout(() => document.querySelector('#vp-custom-routine-builder')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
  }

  async function activatePersonalRoutine(id) {
    const state = await readState();
    if (!(state.routines || []).some(r => String(r.id) === String(id))) return;
    state.activeRoutineId = id;
    await writeState(state);
    location.reload();
  }

  document.addEventListener("change", e => {
    if (e.target.id === "vp-routine-days") {
      normalizeDays(Math.max(1, Math.min(7, Number(e.target.value) || 1)));
      renderDays();
      return;
    }
    if (e.target.matches("[data-vp-day-name]")) {
      const i = Number(e.target.dataset.vpDayName);
      if (draft.days[i]) draft.days[i].name = e.target.value;
      return;
    }
    if (e.target.matches("[data-vp-same-reps]")) {
      const [dayIndex, itemIndex] = e.target.dataset.vpSameReps.split(":").map(Number);
      const item = draft.days[dayIndex]?.items[itemIndex];
      if (item) {
        item.sameReps = e.target.checked;
        syncReps(item);
        if (!item.sameReps) item.repsBySet = Array.from({ length: item.sets }, () => item.reps);
        renderDays();
      }
      return;
    }
    if (e.target.matches("[data-vp-item-field]")) {
      const [dayIndex, itemIndex, field] = e.target.dataset.vpItemField.split(":");
      const item = draft.days[Number(dayIndex)]?.items[Number(itemIndex)];
      if (item) {
        item[field] = Number(e.target.value) || (field === "rest_sec" ? 0 : 1);
        if (field === "sets") { syncReps(item); renderDays(); }
        if (field === "reps") syncReps(item);
      }
      return;
    }
    if (e.target.matches("[data-vp-set-reps]")) {
      const [dayIndex, itemIndex, setIndex] = e.target.dataset.vpSetReps.split(":").map(Number);
      const item = draft.days[dayIndex]?.items[itemIndex];
      if (item) {
        syncReps(item);
        item.repsBySet[setIndex] = Math.max(1, Number(e.target.value) || 1);
        item.reps = item.repsBySet[0] || item.reps;
      }
    }
  });

  document.addEventListener("input", e => {
    if (e.target.id === "vp-routine-name") draft.name = e.target.value;
    if (e.target.matches("[data-vp-day-name]")) {
      const i = Number(e.target.dataset.vpDayName);
      if (draft.days[i]) draft.days[i].name = e.target.value;
      return;
    }
    if (e.target.matches("[data-vp-exercise-search]")) {
      const dayIndex = Number(e.target.dataset.vpExerciseSearch);
      const select = document.querySelector(`[data-vp-exercise-select="${dayIndex}"]`);
      const count = document.querySelector(`[data-vp-exercise-count="${dayIndex}"]`);
      const matches = filteredExercises(e.target.value);
      if (select) {
        const previous = select.value;
        select.innerHTML = exerciseOptions(previous, e.target.value);
        if (matches.length === 1) select.value = matches[0].name;
      }
      if (count) count.textContent = `${matches.length} resultado${matches.length === 1 ? "" : "s"}`;
    }
  });

  document.addEventListener("click", e => {
    const view = e.target.closest('[data-vp-action="view-personal-routine"]');
    if (view) { e.preventDefault(); e.stopImmediatePropagation(); openPersonalRoutine(view.dataset.id).catch(() => {}); return; }
    const edit = e.target.closest('[data-vp-action="edit-personal-routine"]');
    if (edit) { e.preventDefault(); e.stopImmediatePropagation(); editPersonalRoutine(edit.dataset.id).catch(() => {}); return; }
    const activate = e.target.closest('[data-vp-action="activate-personal-routine"]');
    if (activate) { e.preventDefault(); e.stopImmediatePropagation(); activatePersonalRoutine(activate.dataset.id).catch(() => {}); return; }
    if (e.target.closest('[data-vp-action="cancel-edit"]')) {
      draft = newDraft();
      const card = document.querySelector('#vp-custom-routine-builder')?.closest('.card');
      if (card) {
        const builder = card.querySelector('#vp-custom-routine-builder');
        if (builder) builder.replaceWith(Object.assign(document.createElement('form'), { id: 'routine-form' }));
      }
      renderBuilder();
      return;
    }
    const add = e.target.closest('[data-vp-action="add-exercise"]');
    if (add) {
      const dayIndex = Number(add.dataset.day);
      const select = document.querySelector(`[data-vp-exercise-select="${dayIndex}"]`);
      const name = select?.value;
      if (!name) return alert("Busca o selecciona un ejercicio antes de añadirlo.");
      draft.days[dayIndex].items.push(normalizeItem({ exercise: name, sets: 3, reps: 10, rest_sec: 90, weight: 0, sameReps: true }));
      renderDays();
      return;
    }
    const remove = e.target.closest("[data-vp-remove]");
    if (remove) {
      const [dayIndex, itemIndex] = remove.dataset.vpRemove.split(":").map(Number);
      draft.days[dayIndex]?.items.splice(itemIndex, 1);
      renderDays();
      return;
    }
    if (e.target.closest('[data-vp-action="save-routine"]')) saveRoutine().catch(() => alert("No se ha podido guardar la rutina."));
  }, true);

  document.addEventListener("submit", e => {
    if (e.target.id !== "vp-custom-exercise-form") return;
    e.preventDefault();
    e.stopImmediatePropagation();
    saveCustomExercise(e.target);
  }, true);

  const observer = new MutationObserver(renderBuilder);
  const start = () => {
    const app = document.querySelector("#app");
    if (!app) return setTimeout(start, 50);
    observer.observe(app, { childList: true, subtree: true });
    renderBuilder();
  };
  start();
})();