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
      .vp-routines-accordion{display:grid;gap:10px;margin-top:16px}
      .vp-routine-section{border:1px solid #d8e7e3;border-radius:16px;background:#fff;overflow:hidden;box-shadow:0 5px 16px rgba(16,46,56,.04)}
      .vp-routine-section>summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:58px;padding:15px 16px;cursor:pointer;font-size:16px;font-weight:900;color:#163a43;user-select:none}
      .vp-routine-section>summary::-webkit-details-marker{display:none}
      .vp-routine-section>summary::after{content:'⌄';display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#edf7f4;color:#176d61;font-size:18px;transition:transform .18s ease}
      .vp-routine-section[open]>summary::after{transform:rotate(180deg)}
      .vp-routine-section[open]>summary{border-bottom:1px solid #e2ece9}
      .vp-routine-section-content{padding:14px 14px 16px}
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
      .vp-personal-routine-card{width:100%;display:grid;text-align:left;gap:4px;padding:13px 14px;border:1px solid #d8e7e3;border-radius:13px;background:#fbfefd;color:#173b42}
      .vp-personal-routine-card b{font-size:14px}.vp-personal-routine-card span{font-size:11px;color:#687e84}.vp-personal-routine-card .template-meta{color:#168b78;font-weight:850}
      @media(max-width:480px){
        .vp-routine-section>summary{min-height:56px;padding:14px;font-size:15px}
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
    return {activeHead,activeBlock};
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

      const customCard = customBuilder.closest('.card');
      const predefinedNodes = collectUntilNextHead(predefinedHead);
      const exerciseNodes = collectUntilNextHead(exercisesHead);

      customExerciseBlock.remove();

      const accordion = document.createElement('div');
      accordion.id = 'vp-routines-accordion';
      accordion.className = 'vp-routines-accordion';

      const personal = personalDetails(state);
      const customDetails = makeDetails('Crea tu propia rutina', [customCard], 'custom');
      const predefinedDetails = makeDetails('Rutinas predefinidas', predefinedNodes, 'predefined-routines');
      const exerciseDetails = makeDetails('Ejercicios predefinidos', exerciseNodes, 'predefined-exercises');
      const addExerciseDetails = makeDetails('Añade tu ejercicio', [customExerciseBlock], 'add-exercise');

      accordion.appendChild(personal);
      accordion.appendChild(customDetails);
      accordion.appendChild(predefinedDetails);
      accordion.appendChild(exerciseDetails);
      accordion.appendChild(addExerciseDetails);

      customHead.remove();
      predefinedHead.remove();
      exercisesHead.remove();

      if (activeBlock) activeBlock.insertAdjacentElement('afterend', accordion);
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
