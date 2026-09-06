const DB_NAME = "vitalpeak-mobile";
const STORE = "state";
const defaultState = { profile: { name: "" }, routines: [], sessions: [], weights: [] };
let state = structuredClone(defaultState);
let route = "today";
let deferredPrompt;

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
async function loadState() {
  const db = await openDB();
  const tx = db.transaction(STORE, "readonly");
  const request = tx.objectStore(STORE).get("user");
  const saved = await new Promise((resolve, reject) => { request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error); });
  state = { ...structuredClone(defaultState), ...(saved || {}) };
}
async function saveState() {
  const db = await openDB();
  const tx = db.transaction(STORE, "readwrite");
  tx.objectStore(STORE).put(state, "user");
  await new Promise((resolve, reject) => { tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); });
}
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));
const dateLabel = value => new Intl.DateTimeFormat("es-ES", { weekday:"long", day:"numeric", month:"long" }).format(new Date(`${value}T12:00:00`));
const today = () => new Date().toISOString().slice(0, 10);
function toast(message) { const el = document.querySelector("#toast"); el.textContent = message; el.classList.add("show"); setTimeout(() => el.classList.remove("show"), 2600); }
function hero(kicker, title, text) { return `<header class="hero"><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${text}</p></header>`; }
function sessionsThisWeek() { const start = new Date(); start.setHours(0,0,0,0); start.setDate(start.getDate() - ((start.getDay() + 6) % 7)); return state.sessions.filter(s => new Date(`${s.date}T12:00:00`) >= start); }
function renderToday() {
  const week = sessionsThisWeek();
  const latest = [...state.sessions].sort((a,b) => b.date.localeCompare(a.date))[0];
  return `${hero("TU ESPACIO DE ENTRENAMIENTO", `Hola${state.profile.name ? `, ${esc(state.profile.name)}` : ""}`, "Sigue avanzando, aunque no tengas cobertura.")}
    ${deferredPrompt ? `<div class="install">Instala VitalPeak en tu móvil para abrirlo como una app. <button class="secondary" data-action="install">Instalar</button></div>` : ""}
    <section class="metric-grid"><div class="metric"><b>${week.length}</b><span>sesiones esta semana</span></div><div class="metric"><b>${state.sessions.length}</b><span>sesiones guardadas</span></div><div class="metric"><b>${state.weights.length ? `${state.weights.at(-1).kg} kg` : "—"}</b><span>último peso</span></div></section>
    <section class="section-head"><h2>Entrenamiento de hoy</h2><span class="pill">${dateLabel(today())}</span></section>
    <div class="card">${state.routines.length ? `<h3>${esc(state.routines[0].name)}</h3><p class="muted">${state.routines[0].exercises.length} ejercicios preparados.</p><button class="primary wide" data-route="train">Empezar entrenamiento</button>` : `<div class="empty"><b>Aún no tienes rutina.</b><br>Crea una y podrás registrar cada serie incluso sin internet.<br><br><button class="primary" data-route="routines">Crear rutina</button></div>`}</div>
    <section class="section-head"><h2>Última sesión</h2></section>
    <div class="card">${latest ? `<h3>${esc(latest.routineName || "Entrenamiento libre")}</h3><p class="muted">${dateLabel(latest.date)} · ${latest.sets.length} series registradas</p><button class="secondary wide" data-route="progress">Ver progreso</button>` : `<p class="muted">Todavía no hay entrenamientos registrados.</p>`}</div>`;
}
function renderTrain() {
  const routine = state.routines[0];
  if (!routine) return `${hero("ENTRENAR", "Registra tu sesión", "Primero crea una rutina con los ejercicios que haces.")}<div class="card empty"><button class="primary" data-route="routines">Crear rutina</button></div>`;
  const exercise = routine.exercises[0] || { name:"Ejercicio", targetSets:3, targetReps:"8–12" };
  return `${hero("ENTRENAR", esc(routine.name), "Cada serie se guarda al instante en tu teléfono.")}
    <div class="card"><div class="row between"><div><h2>${esc(exercise.name)}</h2><p class="muted">Objetivo: ${exercise.targetSets} × ${esc(exercise.targetReps)}</p></div><span class="pill">1 / ${routine.exercises.length}</span></div>
      <form id="set-form" class="stack"><div class="form-grid"><label class="field">Peso (kg)<input name="weight" inputmode="decimal" type="number" step="0.5" min="0" required placeholder="0" /></label><label class="field">Repeticiones<input name="reps" inputmode="numeric" type="number" min="1" required placeholder="10" /></label></div><label class="field">Notas opcionales<input name="notes" maxlength="100" placeholder="Cómo te has sentido" /></label><button class="primary wide">Guardar serie</button></form>
      <div id="current-sets" class="set-list"></div></div>
    <section class="section-head"><h2>Finalizar</h2></section><button class="secondary wide" data-action="finish-session">Terminar y guardar sesión</button>`;
}
function renderRoutines() {
  const items = state.routines.map((r,i) => `<button class="list-button" data-action="delete-routine" data-index="${i}"><b>${esc(r.name)}</b><br><span class="muted small">${r.exercises.length} ejercicios · tocar para eliminar</span></button>`).join("");
  return `${hero("RUTINAS", "Tu plan", "Sencillo, editable y disponible siempre.")}<div class="stack">${items || `<div class="card empty">Crea tu primera rutina para empezar.</div>`}</div>
    <section class="section-head"><h2>Nueva rutina</h2></section><div class="card"><form id="routine-form" class="stack"><label class="field">Nombre de la rutina<input name="name" required maxlength="40" placeholder="Ej. Torso + brazos" /></label><label class="field">Ejercicios (uno por línea)<textarea name="exercises" required rows="6" placeholder="Press banca\nRemo con mancuerna\nElevaciones laterales"></textarea></label><button class="primary wide">Guardar rutina</button></form></div>`;
}
function renderProgress() {
  const last = state.sessions.slice(-8);
  const max = Math.max(...last.map(s => s.sets.reduce((sum,set) => sum + Number(set.weight || 0) * Number(set.reps || 0), 0)), 1);
  const weightText = state.weights.length ? `${state.weights.at(-1).kg} kg` : "Sin dato";
  return `${hero("PROGRESO", "Tu constancia cuenta", "Los datos de esta pantalla permanecen en tu teléfono.")}<div class="metric-grid"><div class="metric"><b>${state.sessions.length}</b><span>entrenamientos</span></div><div class="metric"><b>${weightText}</b><span>peso actual</span></div><div class="metric"><b>${sessionsThisWeek().length}</b><span>esta semana</span></div></div>
    <section class="section-head"><h2>Volumen reciente</h2></section><div class="card"><div class="chart">${last.length ? last.map(s => `<div class="bar" title="${esc(s.date)}" style="height:${Math.max(10, s.sets.reduce((sum,set) => sum + Number(set.weight || 0) * Number(set.reps || 0),0) / max * 100)}%"></div>`).join("") : `<p class="muted">Registra una sesión para ver tu evolución.</p>`}</div><p class="muted small">Cada barra representa el volumen de una sesión.</p></div>
    <section class="section-head"><h2>Registrar peso</h2></section><div class="card"><form id="weight-form" class="row"><label class="field" style="flex:1">Peso (kg)<input name="kg" inputmode="decimal" type="number" step="0.1" min="1" required placeholder="Ej. 78,5" /></label><button class="primary">Guardar</button></form></div>`;
}
function renderAccount() {
  return `${hero("CUENTA", "Tus datos", "VitalPeak móvil guarda la información en este dispositivo.")}<div class="card stack"><label class="field">Cómo quieres que te llamemos<input id="profile-name" maxlength="30" value="${esc(state.profile.name)}" placeholder="Tu nombre" /></label><button class="primary wide" data-action="save-name">Guardar nombre</button></div>
    <section class="section-head"><h2>Copia de seguridad</h2></section><div class="card stack"><p class="muted">Descarga un archivo con tus rutinas, sesiones y peso. Impórtalo en otro móvil si lo necesitas.</p><button class="secondary wide" data-action="export">Exportar mis datos</button><label class="secondary wide" style="text-align:center">Importar copia<input id="import-file" type="file" accept="application/json" hidden /></label></div>
    <section class="section-head"><h2>Estado sin conexión</h2></section><div class="card"><b>${navigator.onLine ? "Con conexión" : "Sin conexión"}</b><p class="muted">La app y los registros locales siguen funcionando sin internet.</p></div>`;
}
function render() {
  document.querySelector("#app").innerHTML = ({today:renderToday,train:renderTrain,routines:renderRoutines,progress:renderProgress,account:renderAccount}[route])();
  document.querySelectorAll("[data-route]").forEach(el => el.classList.toggle("active", el.dataset.route === route));
  if (route === "train") updateCurrentSets();
}
function currentDraft() { return state._draft || (state._draft = { date:today(), routineName:state.routines[0]?.name || "Entrenamiento libre", sets:[] }); }
function updateCurrentSets() { const el = document.querySelector("#current-sets"); if (el) el.innerHTML = currentDraft().sets.length ? currentDraft().sets.map((s,i) => `<span class="set">Serie ${i+1}: ${s.weight} kg × ${s.reps}</span>`).join("") : `<span class="muted small">Aún no has guardado ninguna serie.</span>`; }
async function handleAction(action, source) {
  if (action === "install" && deferredPrompt) { deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = undefined; render(); }
  if (action === "save-name") { state.profile.name = document.querySelector("#profile-name").value.trim(); await saveState(); toast("Nombre guardado"); render(); }
  if (action === "delete-routine") { state.routines.splice(Number(source.dataset.index), 1); await saveState(); toast("Rutina eliminada"); render(); }
  if (action === "finish-session") { const draft = state._draft; if (!draft?.sets.length) return toast("Guarda al menos una serie antes de terminar"); state.sessions.push(draft); delete state._draft; await saveState(); route="today"; toast("Sesión guardada"); render(); }
  if (action === "export") { const blob = new Blob([JSON.stringify(state, null, 2)], {type:"application/json"}); const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download=`vitalpeak-${today()}.json`; a.click(); URL.revokeObjectURL(a.href); }
}
document.addEventListener("click", async event => { const routeButton = event.target.closest("[data-route]"); if (routeButton) { route = routeButton.dataset.route; render(); return; } const action = event.target.closest("[data-action]"); if (action) await handleAction(action.dataset.action, action); });
document.addEventListener("submit", async event => { event.preventDefault(); const form=event.target; const data=new FormData(form); if (form.id === "set-form") { const exercise=state.routines[0].exercises[0]; currentDraft().sets.push({exercise:exercise.name,weight:Number(data.get("weight")),reps:Number(data.get("reps")),notes:data.get("notes")||""}); form.reset(); updateCurrentSets(); toast("Serie guardada sin conexión"); } if (form.id === "routine-form") { const exercises=String(data.get("exercises")).split("\n").map(name=>name.trim()).filter(Boolean).map(name=>({name,targetSets:3,targetReps:"8–12"})); state.routines.push({name:String(data.get("name")).trim(),exercises}); await saveState(); toast("Rutina creada"); render(); } if (form.id === "weight-form") { state.weights.push({date:today(),kg:Number(data.get("kg"))}); await saveState(); toast("Peso guardado"); render(); } });
document.addEventListener("change", async event => { if (event.target.id !== "import-file") return; const file=event.target.files[0]; if (!file) return; try { const imported=JSON.parse(await file.text()); if (!imported || !Array.isArray(imported.sessions) || !Array.isArray(imported.routines)) throw new Error(); state={...structuredClone(defaultState),...imported}; delete state._draft; await saveState(); toast("Copia importada correctamente"); render(); } catch { toast("Ese archivo no es una copia válida de VitalPeak"); } });
window.addEventListener("beforeinstallprompt", event => { event.preventDefault(); deferredPrompt=event; render(); });
window.addEventListener("online", render); window.addEventListener("offline", render);
if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js"));
await loadState(); render();
