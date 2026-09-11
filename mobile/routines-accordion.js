(() => {
  'use strict';
  let running = false;
  const DB_NAME='vitalpeak-mobile', STORE='state';
  const OPEN_STATE_KEY='vitalpeak:routines-open-sections';
  let restoreScrollY = null;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const normalize = value => String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('es')
    .trim();

  function loadOpenSections(){
    try { return new Set(JSON.parse(sessionStorage.getItem(OPEN_STATE_KEY)||'[]')); }
    catch { return new Set(); }
  }
  function saveOpenSections(keys){
    try { sessionStorage.setItem(OPEN_STATE_KEY, JSON.stringify([...keys])); } catch {}
  }
  function captureAccordionState(){
    const accordion=document.querySelector('#vp-routines-accordion');
    if(!accordion) return;
    const open=new Set([...accordion.querySelectorAll('.vp-routine-section[open]')].map(x=>x.dataset.vpSection).filter(Boolean));
    saveOpenSections(open);
    restoreScrollY=window.scrollY;
  }
  function bindDetailsState(details){
    const key=details.dataset.vpSection;
    if(key && loadOpenSections().has(key)) details.open=true;
    details.addEventListener('toggle',()=>{
      if(!key) return;
      const open=loadOpenSections();
      if(details.open) open.add(key); else open.delete(key);
      saveOpenSections(open);
    });
  }

  function ensureStyles() {
    if (document.querySelector('#vp-routines-accordion-styles')) return;
    const style = document.createElement('style');
    style.id = 'vp-routines-accordion-styles';
    style.textContent = `
      .vp-routine-dashboard{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0 18px}.vp-routine-stat{padding:12px 10px;border:1px solid rgba(22,169,142,.16);border-radius:15px;background:linear-gradient(145deg,#f8fffd,#e9f8f4)}.vp-routine-stat b{display:block;font-size:19px;line-height:1;color:#123f45}.vp-routine-stat span{display:block;margin-top:5px;color:#668087;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}
      .vp-active-head{margin-top:8px!important}.vp-active-head h2{font-size:13px!important;text-transform:uppercase;letter-spacing:.09em;color:#5c777d}.vp-active-block{position:relative}.vp-active-block .list-button{position:relative;overflow:hidden;min-height:118px;padding:19px 58px 18px 19px;border:0;border-radius:22px;background:linear-gradient(140deg,#123a45 0%,#17645f 62%,#1a8d7d 100%);color:#fff;box-shadow:0 16px 34px rgba(18,69,70,.22)}.vp-active-block .list-button:before{content:'';position:absolute;width:150px;height:150px;border-radius:50%;right:-72px;top:-78px;background:rgba(174,255,236,.13)}.vp-active-block .list-button:after{content:'›';position:absolute;right:18px;top:50%;transform:translateY(-50%);display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.14);font-size:28px;color:#bdf8e9}.vp-active-block .template-meta{color:#9cebdc}.vp-active-block .list-button b{position:relative;font-size:20px;letter-spacing:-.35px;margin:7px 0}.vp-active-block .list-button .muted{position:relative;color:#d4eeea}
      .vp-routines-accordion{display:grid;gap:11px;margin-top:4px}
      .vp-routine-section{border:1px solid rgba(35,96,96,.1);border-radius:19px;background:rgba(255,255,255,.92);overflow:hidden;box-shadow:0 8px 22px rgba(16,46,56,.055)}
      .vp-routine-section>summary{list-style:none;display:grid;grid-template-columns:42px 1fr 30px;align-items:center;gap:11px;min-height:68px;padding:13px 15px;cursor:pointer;font-size:15px;font-weight:900;color:#163a43;user-select:none}
      .vp-routine-section>summary::-webkit-details-marker{display:none}
      .vp-routine-section>summary::before{content:'•';display:grid;place-items:center;width:42px;height:42px;border-radius:14px;background:linear-gradient(145deg,#daf8f0,#edfdf9);color:#168b78;font-size:20px;box-shadow:inset 0 0 0 1px rgba(22,169,142,.1)}
      .vp-routine-section[data-vp-section="routine-history"]>summary::before{content:'◷'}.vp-routine-section[data-vp-section="personal-routines"]>summary::before{content:'★'}.vp-routine-section[data-vp-section="custom"]>summary::before{content:'＋'}.vp-routine-section[data-vp-section="predefined-routines"]>summary::before{content:'▤'}.vp-routine-section[data-vp-section="predefined-exercises"]>summary::before{content:'●'}.vp-routine-section[data-vp-section="add-exercise"]>summary::before{content:'✦'}
      .vp-routine-section>summary::after{content:'⌄';display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#edf7f4;color:#176d61;font-size:18px;transition:transform .18s ease}
      .vp-routine-section[open]>summary::after{transform:rotate(180deg)}
      .vp-routine-section[open]>summary{border-bottom:1px solid #e2ece9;background:linear-gradient(90deg,#fbfffe,#f1faf7)}
      .vp-routine-section-content{padding:15px 14px 17px;background:#fbfefd}
      .vp-routine-section-content>.section-head{display:none!important}
      .vp-routine-section-content>.vp-custom-exercises{margin-top:0!important;padding-top:0!important;border-top:0!important}
      .vp-routine-section-content>.vp-custom-exercises>h3,
      .vp-routine-section-content>.vp-custom-exercises>p{display:none!important}
      .vp-routine-section-content>.filter-row{margin-top:0}
      .vp-routine-section-content>.exercise-grid{margin-top:0}
      .vp-section-filters{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
      .vp-section-filters.one{grid-template-columns:1fr}
      .vp-section-filters label{display:grid;gap:5px;font-size:11px;font-weight:850;color:#60777d}
      .vp-section-filters input,.vp-section-filters select{width:100%;min-height:44px;border:1px solid #cddfda;border-radius:11px;background:#fbfefd;padding:9px;color:#102e38;font-size:14px}
      .vp-filter-count{grid-column:1/-1;font-size:11px;color:#6b8085;margin-top:-2px}
      .vp-filter-empty{padding:16px;border-radius:12px;background:#f4f8f7;color:#687d82;text-align:center;font-size:13px}
      .vp-personal-routines-list{display:grid;gap:9px}
      .vp-personal-routine-card{width:100%;display:grid;text-align:left;gap:4px;padding:15px;border:1px solid #d8e7e3;border-radius:15px;background:#fff;color:#173b42;box-shadow:0 4px 13px rgba(16,46,56,.045)}
      .vp-personal-routine-card b{font-size:14px}.vp-personal-routine-card span{font-size:11px;color:#687e84}.vp-personal-routine-card .template-meta{color:#168b78;font-weight:850}
      .vp-routine-history{display:grid;gap:8px}.vp-history-card{width:100%;display:grid;grid-template-columns:1fr auto;gap:5px 12px;text-align:left;padding:14px;border:1px solid #d8e7e3;border-radius:14px;background:#fff;color:#173b42}.vp-history-card b{font-size:14px}.vp-history-card span{font-size:11px;color:#687e84}.vp-history-card time{grid-row:1/3;grid-column:2;align-self:center;padding:5px 8px;border-radius:99px;background:#e4f7f2;font-size:10px;font-weight:850;color:#168b78}.vp-history-card[disabled]{cursor:default;opacity:.72}
      .vp-routine-section-content .list-button{padding:15px;border-radius:15px;border-color:#dfeae7;background:#fff;box-shadow:0 4px 13px rgba(16,46,56,.04)}.vp-routine-section-content .list-button+.list-button{margin-top:8px}
      @media(max-width:480px){
        .vp-routine-dashboard{gap:6px}.vp-routine-stat{padding:11px 8px}.vp-routine-stat b{font-size:17px}.vp-routine-section>summary{min-height:62px;padding:11px 13px;font-size:14px}
        .vp-routine-section-content{padding:12px}
        .vp-section-filters{grid-template-columns:1fr}
      }
    `;
    document.head.appendChild(style);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),g=tx.objectStore(STORE).get('user');g.onsuccess=()=>resolve(g.result||{});g.onerror=()=>reject(g.error)})}

  function sectionHead(app, text) {
    return [...app.querySelectorAll('.section-head')].find(x => x.querySelector('h2')?.textContent.trim() === text) || null;
  }

  function collectUntilNextHead(start) {
    const nodes = [];
    let node = start?.nextElementSibling || null;
    while (node && !node.classList?.contains('section-head')) {
      nodes.push(node);
      node = node.nextElementSibling;
    }
    return nodes;
  }

  function makeDetails(title, nodes, key) {
    const details = document.createElement('details');
    details.className = 'vp-routine-section';
    details.dataset.vpSection = key || '';
    details.innerHTML = `<summary>${title}</summary><div class="vp-routine-section-content"></div>`;
    const body = details.querySelector('.vp-routine-section-content');
    nodes.forEach(node => body.appendChild(node));
    bindDetailsState(details);
    return details;
  }

  function templateById(id) {
    return (window.VITALPEAK_CATALOG?.templates || []).find(x => String(x.id) === String(id)) || null;
  }

  function setupRoutineLevelFilter(details) {
    const body = details?.querySelector('.vp-routine-section-content');
    if (!body || body.querySelector('[data-vp-routine-level]')) return;

    const levels = [...new Set((window.VITALPEAK_CATALOG?.templates || []).map(x => String(x.level || '')).filter(Boolean))];
    const preferred = ['principiante','intermedio','avanzado'];
    levels.sort((a,b) => {
      const ia=preferred.indexOf(normalize(a)), ib=preferred.indexOf(normalize(b));
      if(ia>=0||ib>=0) return (ia<0?99:ia)-(ib<0?99:ib);
      return a.localeCompare(b,'es');
    });

    const filters = document.createElement('div');
    filters.className = 'vp-section-filters one';
    filters.innerHTML = `<label>Nivel<select data-vp-routine-level><option value="">Todos los niveles</option>${levels.map(level=>`<option value="${esc(level)}">${esc(level.charAt(0).toUpperCase()+level.slice(1))}</option>`).join('')}</select></label><span class="vp-filter-count" data-vp-routine-count></span>`;

    const existingFilter = body.querySelector('.filter-row');
    if (existingFilter) existingFilter.insertAdjacentElement('afterend', filters);
    else body.insertAdjacentElement('afterbegin', filters);

    const apply = () => {
      const level = filters.querySelector('[data-vp-routine-level]').value;
      const buttons = [...body.querySelectorAll('[data-action="view-template"]')];
      let visible = 0;
      buttons.forEach(button => {
        const template = templateById(button.dataset.template);
        const show = !level || String(template?.level || '') === level;
        button.hidden = !show;
        if (show) visible += 1;
      });
      filters.querySelector('[data-vp-routine-count]').textContent = `${visible} rutina${visible===1?'':'s'} visible${visible===1?'':'s'}`;
      let empty = body.querySelector('.vp-filter-empty[data-kind="routines"]');
      if (!visible) {
        if (!empty) {
          empty = document.createElement('div');
          empty.className = 'vp-filter-empty';
          empty.dataset.kind = 'routines';
          empty.textContent = 'No hay rutinas con este nivel y los días seleccionados.';
          body.appendChild(empty);
        }
      } else empty?.remove();
    };
    filters.querySelector('[data-vp-routine-level]').addEventListener('change', apply);
    apply();
  }

  function exerciseGroup(card) {
    return card.querySelector('span')?.textContent?.trim() || 'Otro';
  }

  function setupExerciseFilters(details) {
    const body = details?.querySelector('.vp-routine-section-content');
    const grid = body?.querySelector('.exercise-grid');
    if (!body || !grid || body.querySelector('[data-vp-exercise-catalog-search]')) return;

    const cards = [...grid.querySelectorAll('.exercise-card')];
    const groups = [...new Set(cards.map(exerciseGroup).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es'));
    const filters = document.createElement('div');
    filters.className = 'vp-section-filters';
    filters.innerHTML = `<label>Grupo muscular<select data-vp-exercise-catalog-group><option value="">Todos los grupos</option>${groups.map(g=>`<option value="${esc(g)}">${esc(g)}</option>`).join('')}</select></label><label>Buscar ejercicio<input type="search" inputmode="search" autocomplete="off" placeholder="Escribe press, remo, curl…" data-vp-exercise-catalog-search></label><span class="vp-filter-count" data-vp-exercise-catalog-count></span>`;
    grid.insertAdjacentElement('beforebegin', filters);

    const apply = () => {
      const group = filters.querySelector('[data-vp-exercise-catalog-group]').value;
      const query = normalize(filters.querySelector('[data-vp-exercise-catalog-search]').value);
      let visible = 0;
      cards.forEach(card => {
        const name = card.dataset.exercise || card.querySelector('b')?.textContent || '';
        const cardGroup = exerciseGroup(card);
        const groupOk = !group || cardGroup === group;
        const textOk = !query || normalize(`${name} ${cardGroup}`).includes(query);
        const show = groupOk && textOk;
        card.hidden = !show;
        if (show) visible += 1;
      });
      filters.querySelector('[data-vp-exercise-catalog-count]').textContent = `${visible} ejercicio${visible===1?'':'s'} visible${visible===1?'':'s'}`;
      let empty = body.querySelector('.vp-filter-empty[data-kind="exercises"]');
      if (!visible) {
        if (!empty) {
          empty = document.createElement('div');
          empty.className = 'vp-filter-empty';
          empty.dataset.kind = 'exercises';
          empty.textContent = 'No hay ejercicios que coincidan con estos filtros.';
          grid.insertAdjacentElement('afterend', empty);
        }
      } else empty?.remove();
    };

    filters.querySelector('[data-vp-exercise-catalog-group]').addEventListener('change', apply);
    filters.querySelector('[data-vp-exercise-catalog-search]').addEventListener('input', apply);
    apply();
  }

  function personalDetails(state) {
    const personal = (state.routines || []).filter(r => r?.source === 'custom-builder');
    const wrapper = document.createElement('div');
    wrapper.className = 'vp-personal-routines-list';
    wrapper.innerHTML = personal.length ? personal.map(r => {
      const days = Array.isArray(r.days) ? r.days : [];
      const exerciseCount = days.reduce((n,d)=>n+(d.items?.length||0),0);
      return `<button type="button" class="vp-personal-routine-card" data-vp-action="view-personal-routine" data-id="${esc(r.id)}"><span class="template-meta">${String(state.activeRoutineId)===String(r.id)?'RUTINA ACTIVA':'RUTINA PERSONAL'}</span><b>${esc(r.name||'Rutina sin nombre')}</b><span>${days.length} día${days.length===1?'':'s'} · ${exerciseCount} ejercicio${exerciseCount===1?'':'s'} · pulsa para ver todos los días</span></button>`;
    }).join('') : `<div class="vp-filter-empty">Todavía no has creado ninguna rutina personal.</div>`;
    return makeDetails(`Rutinas personales${personal.length ? ` · ${personal.length}` : ''}`, [wrapper], 'personal-routines');
  }

  function routineHistoryDetails(state) {
    const routines=Array.isArray(state.routines)?state.routines:[],sessions=(Array.isArray(state.sessions)?state.sessions:[]).slice().reverse().slice(0,12);
    const wrapper=document.createElement('div');wrapper.className='vp-routine-history';
    wrapper.innerHTML=sessions.length?sessions.map(session=>{const routine=routines.find(r=>String(r.id)===String(session.routineId))||routines.find(r=>String(r.name)===String(session.routineName));const date=String(session.date||'');let label=date;try{label=new Intl.DateTimeFormat('es-ES',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${date}T12:00:00`))}catch{}const sets=Array.isArray(session.sets)?session.sets.length:0;return `<button type="button" class="vp-history-card" ${routine?`data-action="activate-routine" data-id="${esc(routine.id)}"`:'disabled'}><b>${esc(session.routineName||routine?.name||'Entrenamiento')}</b><span>${sets} serie${sets===1?'':'s'} registrada${sets===1?'':'s'}${routine?' · pulsa para ver la rutina':' · rutina ya no disponible'}</span><time datetime="${esc(date)}">${esc(label)}</time></button>`}).join(''):`<div class="vp-filter-empty">Cuando completes un entrenamiento aparecerá aquí la rutina utilizada y su fecha.</div>`;
    return makeDetails(`Historial de rutinas${sessions.length?` · ${sessions.length}`:''}`,[wrapper],'routine-history');
  }

  function tidyActiveRoutine(app, state) {
    const activeHead = sectionHead(app, 'Tu rutina activa');
    const activeBlock = activeHead?.nextElementSibling;
    if (!activeBlock) return {activeHead,activeBlock};
    const buttons = [...activeBlock.querySelectorAll('[data-action="activate-routine"]')];
    buttons.forEach(button => {
      if (String(button.dataset.id) !== String(state.activeRoutineId)) button.remove();
    });
    if (!activeBlock.querySelector('[data-action="activate-routine"]')) {
      activeBlock.innerHTML = `<div class="card empty">Aún no has seleccionado una rutina.</div>`;
    }
    activeHead?.classList.add('vp-active-head');activeBlock.classList.add('vp-active-block');
    return {activeHead,activeBlock};
  }

  function dashboard(state) {
    const active=(state.routines||[]).find(r=>String(r.id)===String(state.activeRoutineId));
    const days=active?.days?.length||0,exercises=(active?.days||[]).reduce((n,d)=>n+(d.items?.length||0),0),uses=(state.sessions||[]).filter(s=>String(s.routineId)===String(active?.id)||(!s.routineId&&String(s.routineName)===String(active?.name))).length;
    const el=document.createElement('div');el.className='vp-routine-dashboard';el.innerHTML=`<div class="vp-routine-stat"><b>${days||'—'}</b><span>Días</span></div><div class="vp-routine-stat"><b>${exercises||'—'}</b><span>Ejercicios</span></div><div class="vp-routine-stat"><b>${uses}</b><span>Completadas</span></div>`;return el;
  }

  async function enhance() {
    if (running) return;
    const app = document.querySelector('#app');
    if (!app || !app.textContent.includes('RUTINAS') || app.querySelector('#vp-routines-accordion')) return;

    const customHead = sectionHead(app, 'Rutina personalizada');
    const predefinedHead = sectionHead(app, 'Planes preparados');
    const exercisesHead = sectionHead(app, 'Catálogo de ejercicios');
    const customBuilder = app.querySelector('#vp-custom-routine-builder');
    const customExerciseBlock = app.querySelector('.vp-custom-exercises');

    if (!customHead || !predefinedHead || !exercisesHead || !customBuilder || !customExerciseBlock) return;

    running = true;
    try {
      ensureStyles();
      const state = await readState().catch(()=>({routines:[]}));
      const {activeBlock} = tidyActiveRoutine(app, state);
      if(activeBlock)activeBlock.insertAdjacentElement('afterend',dashboard(state));

      const customCard = customBuilder.closest('.card');
      const predefinedNodes = collectUntilNextHead(predefinedHead);
      const exerciseNodes = collectUntilNextHead(exercisesHead);

      customExerciseBlock.remove();

      const accordion = document.createElement('div');
      accordion.id = 'vp-routines-accordion';
      accordion.className = 'vp-routines-accordion';

      const personal = personalDetails(state);
      const history = routineHistoryDetails(state);
      const customDetails = makeDetails('Crea tu propia rutina', [customCard], 'custom');
      const predefinedDetails = makeDetails('Rutinas predefinidas', predefinedNodes, 'predefined-routines');
      const exerciseDetails = makeDetails('Ejercicios predefinidos', exerciseNodes, 'predefined-exercises');
      const addExerciseDetails = makeDetails('Añade tu ejercicio', [customExerciseBlock], 'add-exercise');

      accordion.appendChild(history);
      accordion.appendChild(personal);
      accordion.appendChild(customDetails);
      accordion.appendChild(predefinedDetails);
      accordion.appendChild(exerciseDetails);
      accordion.appendChild(addExerciseDetails);

      customHead.remove();
      predefinedHead.remove();
      exercisesHead.remove();

      const stats=app.querySelector('.vp-routine-dashboard');
      if (stats) stats.insertAdjacentElement('afterend', accordion);
      else if (activeBlock) activeBlock.insertAdjacentElement('afterend', accordion);
      else app.querySelector('.hero')?.insertAdjacentElement('afterend', accordion);

      setupRoutineLevelFilter(predefinedDetails);
      setupExerciseFilters(exerciseDetails);

      if(restoreScrollY!==null){
        const y=restoreScrollY; restoreScrollY=null;
        requestAnimationFrame(()=>window.scrollTo({top:y,left:0,behavior:'auto'}));
      }
    } finally {
      running = false;
    }
  }

  document.addEventListener('change',e=>{
    if(e.target.closest('#vp-routines-accordion')) captureAccordionState();
  },true);
  document.addEventListener('input',e=>{
    if(e.target.closest('#vp-routines-accordion')) captureAccordionState();
  },true);

  let timer = null;
  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 60);
    new MutationObserver(() => {
      clearTimeout(timer);
      timer = setTimeout(enhance, 60);
    }).observe(app, { childList: true, subtree: true });
    enhance();
  };
  start();
})();
