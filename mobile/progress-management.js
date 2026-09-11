(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state';
  const RECORDS_KEY='vitalpeak:progress-records-expanded';
  const RETURN_KEY='vitalpeak:return-progress';
  const STYLE_ID='vp-progress-management-style';
  let enhancing=false;
  let lastTouch=0;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=v=>Number(v||0);
  const fmt=(v,d=1)=>Number(v||0).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});
  const dateLabel=v=>{try{return new Intl.DateTimeFormat('es-ES',{day:'2-digit',month:'short',year:'numeric'}).format(new Date(`${v}T12:00:00`))}catch{return v}};

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(state,'user');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)})}

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-weight-history{margin-top:14px;padding-top:12px;border-top:1px solid #e7efed}
      .vp-weight-history-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:7px}
      .vp-weight-history-head h3{margin:0;color:#173b43;font-size:14px}.vp-weight-history-head span{color:#7b8f94;font-size:10px}
      .vp-weight-history-list{display:grid;gap:7px}
      .vp-weight-history-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;padding:9px 10px;border:1px solid #e5eeec;border-radius:12px;background:#f9fcfb}
      .vp-weight-history-copy b{display:block;color:#173b43;font-size:13px}.vp-weight-history-copy span{display:block;margin-top:2px;color:#7a8e93;font-size:10px}
      .vp-weight-action{width:34px;height:34px;display:grid;place-items:center;border:0;border-radius:10px;background:#e8f7f4;color:#0d8f7b}
      .vp-weight-action.delete{background:#fff0f2;color:#b5475a}.vp-weight-action svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
      .vp-weight-edit-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:7px;align-items:center;padding:9px 10px;border:1px solid #bfe4dd;border-radius:12px;background:#f2faf8}
      .vp-weight-edit-row input{min-width:0;width:100%;border:1px solid #c8ded9;border-radius:10px;padding:9px;background:#fff;color:#173b43;font-weight:800}
      .vp-weight-edit-row button{border:0;border-radius:10px;padding:9px 11px;font-weight:850}.vp-weight-save{background:#14a68d;color:#fff}.vp-weight-cancel{background:#e8efed;color:#51696f}
      .vp-record-toggle-fixed{margin-top:7px!important}
    `;document.head.appendChild(s);
  }

  function exerciseRows(state,name){const rows=[];for(const s of state.sessions||[])for(const set of s.sets||[])if(set.exercise===name)rows.push({...set,date:s.date});return rows}
  function allExerciseNames(state){const names=new Set();for(const s of state.sessions||[])for(const set of s.sets||[])if(set.exercise)names.add(set.exercise);return [...names]}
  function records(state){return allExerciseNames(state).map(name=>({name,best:Math.max(0,...exerciseRows(state,name).map(x=>num(x.weight)))})).filter(x=>x.best>0).sort((a,b)=>b.best-a.best)}
  const chev='<svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>';

  async function enhanceRecords(){
    const page=document.querySelector('.vp-progress-page'),list=page?.querySelector('[data-vp-record-list]');
    if(!page||!list)return;
    const state=await readState().catch(()=>({sessions:[]})),all=records(state),expanded=sessionStorage.getItem(RECORDS_KEY)==='1',shown=expanded?all:all.slice(0,3);
    list.innerHTML=shown.length?shown.map(r=>`<button class="vp-record-row" data-action="exercise-detail" data-exercise="${esc(r.name)}"><b>${esc(r.name)}</b><span>${fmt(r.best)} kg</span>${chev}</button>`).join(''):'<div class="vp-empty-small">Aún no hay récords registrados.</div>';
    let toggle=page.querySelector('[data-vp-toggle-records]');
    if(all.length>3){if(!toggle){toggle=document.createElement('button');toggle.type='button';toggle.className='vp-link vp-record-toggle-fixed';toggle.dataset.vpToggleRecords='';list.insertAdjacentElement('afterend',toggle)}toggle.innerHTML=`${expanded?'Ver menos':'Ver más'} ${chev}`}else toggle?.remove();
  }

  async function enhanceWeights(){
    const page=document.querySelector('.vp-progress-page'),form=page?.querySelector('.vp-weight-form');
    if(!page||!form)return;
    let box=page.querySelector('.vp-weight-history');if(!box){box=document.createElement('div');box.className='vp-weight-history';form.insertAdjacentElement('afterend',box)}
    const state=await readState().catch(()=>({weights:[]}));
    const weights=(Array.isArray(state.weights)?state.weights:[]).map((w,index)=>({...w,index})).sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))||b.index-a.index);
    box.innerHTML=`<div class="vp-weight-history-head"><h3>Histórico de peso</h3><span>${weights.length} registro${weights.length===1?'':'s'}</span></div><div class="vp-weight-history-list">${weights.length?weights.map(w=>`<div class="vp-weight-history-row" data-vp-weight-row="${w.index}"><div class="vp-weight-history-copy"><b>${fmt(w.kg)} kg</b><span>${esc(dateLabel(w.date||''))}</span></div><button type="button" class="vp-weight-action" data-vp-edit-weight="${w.index}" aria-label="Editar peso"><svg viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16v4Z"/><path d="m13.5 6.5 4 4"/></svg></button><button type="button" class="vp-weight-action delete" data-vp-delete-weight="${w.index}" aria-label="Eliminar peso"><svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg></button></div>`).join(''):'<div class="vp-empty-small">Todavía no has registrado ningún peso.</div>'}</div>`;
  }

  async function enhance(){
    if(enhancing||!document.querySelector('.tabbar button[data-route="progress"].active')||!document.querySelector('.vp-progress-page'))return;
    enhancing=true;try{injectStyles();await Promise.all([enhanceRecords(),enhanceWeights()])}finally{enhancing=false}
  }

  function reloadToProgress(){sessionStorage.setItem(RETURN_KEY,'1');location.reload()}
  function restoreProgressAfterReload(){
    if(sessionStorage.getItem(RETURN_KEY)!=='1')return;
    const tryOpen=()=>{const btn=document.querySelector('.tabbar button[data-route="progress"]');if(!btn)return setTimeout(tryOpen,40);sessionStorage.removeItem(RETURN_KEY);btn.click()};tryOpen();
  }

  async function toggleRecords(e){
    const button=e.target.closest('.vp-progress-page [data-vp-toggle-records]');if(!button)return false;
    e.preventDefault();e.stopImmediatePropagation();
    const expanded=sessionStorage.getItem(RECORDS_KEY)==='1';sessionStorage.setItem(RECORDS_KEY,expanded?'0':'1');await enhanceRecords();return true;
  }
  document.addEventListener('touchend',e=>{if(!e.target.closest('.vp-progress-page [data-vp-toggle-records]'))return;lastTouch=Date.now();toggleRecords(e)}, {capture:true,passive:false});
  document.addEventListener('click',e=>{if(Date.now()-lastTouch<500&&e.target.closest('.vp-progress-page [data-vp-toggle-records]')){e.preventDefault();e.stopImmediatePropagation();return}toggleRecords(e)},true);

  document.addEventListener('click',async e=>{
    const edit=e.target.closest('[data-vp-edit-weight]');
    if(edit){e.preventDefault();e.stopImmediatePropagation();const index=Number(edit.dataset.vpEditWeight),row=edit.closest('[data-vp-weight-row]'),state=await readState(),current=state.weights?.[index];if(!row||!current)return;row.outerHTML=`<div class="vp-weight-edit-row" data-vp-weight-edit-row="${index}"><input type="number" inputmode="decimal" step="0.1" min="1" value="${num(current.kg)}" aria-label="Peso en kg"><button type="button" class="vp-weight-save" data-vp-save-weight="${index}">Guardar</button><button type="button" class="vp-weight-cancel" data-vp-cancel-weight>Cancelar</button></div>`;document.querySelector(`[data-vp-weight-edit-row="${index}"] input`)?.focus();return}
    const cancel=e.target.closest('[data-vp-cancel-weight]');if(cancel){e.preventDefault();e.stopImmediatePropagation();await enhanceWeights();return}
    const save=e.target.closest('[data-vp-save-weight]');
    if(save){e.preventDefault();e.stopImmediatePropagation();const index=Number(save.dataset.vpSaveWeight),row=save.closest('[data-vp-weight-edit-row]'),kg=Number(row?.querySelector('input')?.value);if(!Number.isFinite(kg)||kg<=0){row?.querySelector('input')?.focus();return}const state=await readState();if(!Array.isArray(state.weights)||!state.weights[index])return;state.weights[index]={...state.weights[index],kg};await writeState(state);reloadToProgress();return}
    const del=e.target.closest('[data-vp-delete-weight]');
    if(del){e.preventDefault();e.stopImmediatePropagation();const index=Number(del.dataset.vpDeleteWeight),state=await readState();if(!Array.isArray(state.weights)||!state.weights[index])return;const w=state.weights[index];if(!confirm(`¿Eliminar el registro de ${fmt(w.kg)} kg?`))return;state.weights.splice(index,1);await writeState(state);reloadToProgress();return}
  },true);

  const app=document.querySelector('#app');if(app)new MutationObserver(()=>{clearTimeout(window.__vpProgressManagementTimer);window.__vpProgressManagementTimer=setTimeout(enhance,40)}).observe(app,{childList:true,subtree:false});
  const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(()=>setTimeout(enhance,30)).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  injectStyles();restoreProgressAfterReload();setTimeout(enhance,80);
})();