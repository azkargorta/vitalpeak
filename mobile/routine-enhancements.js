(() => {
  const CUSTOM_EXERCISES_KEY = "vitalpeak-custom-exercises";
  const DB_NAME = "vitalpeak-mobile";
  const STORE = "state";

  let draft = {
    name: "",
    dayCount: 3,
    days: Array.from({ length: 3 }, (_, i) => ({ name: `Día ${i + 1}`, items: [] })),
  };

  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function allExercises() {
    const list = window.VITALPEAK_CATALOG?.exercises || [];
    return [...list].sort((a, b) => String(a.name).localeCompare(String(b.name), "es"));
  }

  function exerciseOptions(selected = "") {
    return `<option value="">Selecciona un ejercicio…</option>${allExercises().map(x =>
      `<option value="${esc(x.name)}" ${x.name === selected ? "selected" : ""}>${esc(x.name)} · ${esc(x.group || "Otro")}</option>`
    ).join("")}`;
  }

  function normalizeDays(count) {
    const next = [];
    for (let i = 0; i < count; i += 1) {
      next.push(draft.days[i] || { name: `Día ${i + 1}`, items: [] });
    }
    draft.dayCount = count;
    draft.days = next;
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
      .vp-day-head input,.vp-day-add select,.vp-custom-exercise-form input,.vp-custom-exercise-form select{width:100%;min-height:44px;border:1px solid #cddfda;border-radius:11px;background:#fbfefd;padding:9px;color:#102e38;font-size:14px}
      .vp-day-add{display:grid;grid-template-columns:1fr auto;gap:8px;margin:10px 0}
      .vp-day-add button{min-height:44px;padding:8px 12px;border-radius:11px;background:#e8f6f2;color:#176d61;font-weight:800}
      .vp-builder-exercises{display:grid;gap:8px}
      .vp-builder-exercise{padding:10px;border:1px solid #d8e7e3;border-radius:12px;background:#fff}
      .vp-builder-exercise-name{display:flex;justify-content:space-between;gap:8px;align-items:start;margin-bottom:8px}
      .vp-builder-exercise-name b{font-size:13px;line-height:1.25}
      .vp-builder-exercise-name button{background:#fdecef;color:#b43b4c;border-radius:9px;padding:5px 8px;font-size:11px;font-weight:800}
      .vp-builder-values{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px}
      .vp-builder-values label{display:grid;gap:3px;font-size:10px;font-weight:800;color:#658087}
      .vp-builder-values input{width:100%;min-height:38px;border:1px solid #cddfda;border-radius:9px;background:#fbfefd;padding:7px;color:#102e38;font-size:13px}
      .vp-empty-day{padding:12px;border-radius:11px;background:#f3f8f6;color:#658087;font-size:12px;text-align:center}
      .vp-save-routine{margin-top:14px}
      .vp-custom-exercises{margin-top:24px;padding-top:18px;border-top:1px solid #d8e7e3}
      .vp-custom-exercises h3{margin:0 0 5px}
      .vp-custom-exercises p{margin:0 0 12px;color:#658087;font-size:13px}
      .vp-custom-exercise-form{display:grid;grid-template-columns:1fr 140px;gap:8px}
      .vp-custom-exercise-form button{grid-column:1/-1}
      .vp-my-exercises{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
      .vp-my-exercise{padding:6px 9px;border-radius:99px;background:#edf8f5;color:#176d61;font-size:11px;font-weight:750}
      @media(max-width:480px){.vp-builder-top,.vp-custom-exercise-form{grid-template-columns:1fr}.vp-builder-values{grid-template-columns:repeat(3,minmax(0,1fr))}}
    `;
    document.head.appendChild(style);
  }

  function customExercises() {
    try { return JSON.parse(localStorage.getItem(CUSTOM_EXERCISES_KEY) || "[]"); }
    catch { return []; }
  }

  function renderBuilder() {
    styles();
    const old = document.querySelector("#routine-form");
    if (!old) return;
    const card = old.closest(".card");
    if (!card || card.dataset.vpEnhanced === "1") return;
    card.dataset.vpEnhanced = "1";

    card.innerHTML = `
      <div id="vp-custom-routine-builder">
        <p class="vp-builder-intro">Crea una rutina completa de varios días. Después podrás asignar cada día de esta rutina desde el calendario.</p>
        <div class="vp-builder-top">
          <label class="field">Nombre de la rutina<input id="vp-routine-name" maxlength="50" placeholder="Ej. Fuerza 4 días" value="${esc(draft.name)}"></label>
          <label class="field">Número de días<select id="vp-routine-days">${[1,2,3,4,5,6,7].map(n => `<option value="${n}" ${n === draft.dayCount ? "selected" : ""}>${n}</option>`).join("")}</select></label>
        </div>
        <div id="vp-routine-days-container"></div>
        <button class="primary wide vp-save-routine" type="button" data-vp-action="save-routine">Guardar rutina</button>
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
                <label>Reps<input type="number" min="1" max="100" value="${Number(item.reps || 10)}" data-vp-item-field="${dayIndex}:${itemIndex}:reps"></label>
                <label>Descanso<input type="number" min="0" max="600" step="5" value="${Number(item.rest_sec || 90)}" data-vp-item-field="${dayIndex}:${itemIndex}:rest_sec"></label>
              </div>
            </div>`).join("") : `<div class="vp-empty-day">Añade al menos un ejercicio a este día.</div>`}
        </div>
        <div class="vp-day-add">
          <select data-vp-exercise-select="${dayIndex}">${exerciseOptions()}</select>
          <button type="button" data-vp-action="add-exercise" data-day="${dayIndex}">+ Añadir</button>
        </div>
      </section>`).join("");
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

  async function saveRoutine() {
    draft.name = document.querySelector("#vp-routine-name")?.value.trim() || "";
    draft.days.forEach((day, i) => {
      const input = document.querySelector(`[data-vp-day-name="${i}"]`);
      if (input) day.name = input.value.trim() || `Día ${i + 1}`;
    });
    if (!draft.name) return alert("Pon un nombre a la rutina.");
    const empty = draft.days.findIndex(d => !d.items.length);
    if (empty >= 0) return alert(`Añade al menos un ejercicio al día ${empty + 1}.`);

    const db = await openDB();
    const tx = db.transaction(STORE, "readwrite");
    const store = tx.objectStore(STORE);
    const getReq = store.get("user");
    const state = await new Promise((resolve, reject) => {
      getReq.onsuccess = () => resolve(getReq.result || {});
      getReq.onerror = () => reject(getReq.error);
    });
    const id = `custom-${Date.now()}`;
    const routine = {
      id,
      name: draft.name,
      days: draft.days.map((d, i) => ({
        name: d.name || `Día ${i + 1}`,
        focus: d.name || `Día ${i + 1}`,
        items: d.items.map(x => ({ ...x, weight: Number(x.weight || 0) })),
      })),
      activeDay: 0,
      source: "custom-builder",
    };
    state.routines = Array.isArray(state.routines) ? state.routines : [];
    state.routines.unshift(routine);
    state.activeRoutineId = id;
    store.put(state, "user");
    await new Promise((resolve, reject) => {
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
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
    if (e.target.matches("[data-vp-item-field]")) {
      const [dayIndex, itemIndex, field] = e.target.dataset.vpItemField.split(":");
      const item = draft.days[Number(dayIndex)]?.items[Number(itemIndex)];
      if (item) item[field] = Number(e.target.value) || (field === "rest_sec" ? 0 : 1);
    }
  });

  document.addEventListener("input", e => {
    if (e.target.id === "vp-routine-name") draft.name = e.target.value;
    if (e.target.matches("[data-vp-day-name]")) {
      const i = Number(e.target.dataset.vpDayName);
      if (draft.days[i]) draft.days[i].name = e.target.value;
    }
  });

  document.addEventListener("click", e => {
    const add = e.target.closest('[data-vp-action="add-exercise"]');
    if (add) {
      const dayIndex = Number(add.dataset.day);
      const select = document.querySelector(`[data-vp-exercise-select="${dayIndex}"]`);
      const name = select?.value;
      if (!name) return;
      draft.days[dayIndex].items.push({ exercise: name, sets: 3, reps: 10, rest_sec: 90, weight: 0 });
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
  });

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
