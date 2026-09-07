(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile', STORE='state';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const catalog=()=>window.VITALPEAK_CATALOG||{templates:[],exercises:[]};
  function styles(){
    if(document.querySelector('#vp-routine-nav-styles'))return;
    const s=document.createElement('style');s.id='vp-routine-nav-styles';s.textContent=`
      .vp-template-backdrop{position:fixed;inset:0;z-index:700;background:rgba(8,29,34,.72);backdrop-filter:blur(7px);display:flex;align-items:stretch;justify-content:center;padding:max(10px,env(safe-area-inset-top)) 10px max(10px,env(safe-area-inset-bottom))}
      .vp-template-modal{width:min(720px,100%);background:#f4f9f7;border-radius:22px;overflow:auto;color:#14343b;box-shadow:0 24px 70px rgba(0,0,0,.28)}
      .vp-template-head{position:sticky;top:0;z-index:2;background:rgba(244,249,247,.97);backdrop-filter:blur(10px);padding:18px;border-bottom:1px solid #dbe8e4;display:flex;justify-content:space-between;gap:12px}
      .vp-template-head h2{margin:4px 0 3px;font-size:24px}.vp-template-head p{margin:0;color:#63797f;font-size:13px}.vp-template-close{width:42px;height:42px;border:0;border-radius:50%;background:#fff;color:#14343b;font-size:27px;box-shadow:0 4px 13px rgba(0,0,0,.1)}
      .vp-template-body{padding:16px 16px 110px}.vp-template-days{display:flex;gap:7px;overflow:auto;padding-bottom:10px}.vp-template-days button{white-space:nowrap;min-height:40px;border:1px solid #cfe1dd;border-radius:12px;background:#fff;padding:8px 11px;color:#173b42;font-weight:800}.vp-template-days button.selected{background:#dff5ef;border-color:#6ecfbe}
      .vp-template-exercises{display:grid;gap:9px;margin-top:10px}.vp-template-exercise{padding:12px;border:1px solid #dce8e5;border-radius:14px;background:#fff}.vp-template-exercise b{display:block;font-size:14px}.vp-template-exercise span{display:block;margin-top:3px;color:#687e84;font-size:12px}
      .vp-template-actions{position:sticky;bottom:0;background:rgba(244,249,247,.97);backdrop-filter:blur(10px);border-top:1px solid #dbe8e4;padding:12px 16px calc(12px + env(safe-area-inset-bottom));display:grid;grid-template-columns:1fr 1fr;gap:8px}.vp-template-actions button{min-height:48px;border-radius:13px;font-weight:900}.vp-template-save{border:1px solid #16a98e;background:#fff;color:#157f70}.vp-template-activate{border:0;background:#4fd3c1;color:#12383a}
      @media(max-width:390px){.vp-template-actions{grid-template-columns:1fr}}
    `;document.head.appendChild(s);
  }
  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),g=tx.objectStore(STORE).get('user');g.onsuccess=()=>resolve(g.result||{});g.onerror=()=>reject(g.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.objectStore(STORE).put(state,'user')})}
  function clone(v){return JSON.parse(JSON.stringify(v))}
  async function saveTemplate(template,activate=true){
    const state=await readState();state.routines=Array.isArray(state.routines)?state.routines:[];const copy=clone(template);copy.source='template';copy.activeDay=Number(copy.activeDay||0);const i=state.routines.findIndex(r=>String(r.id)===String(copy.id));if(i>=0)state.routines.splice(i,1,copy);else state.routines.unshift(copy);if(activate)state.activeRoutineId=copy.id;await writeState(state);location.reload();
  }
  async function activateRoutine(id){const state=await readState();if(!(state.routines||[]).some(r=>String(r.id)===String(id)))return;state.activeRoutineId=id;await writeState(state);location.reload()}
  function openTemplate(id){
    const t=catalog().templates.find(x=>String(x.id)===String(id));if(!t)return;
    styles();let day=0;const o=document.createElement('div');o.className='vp-template-backdrop';o.innerHTML=`<div class="vp-template-modal"><div class="vp-template-head"><div><span class="template-meta">RUTINA PREPARADA</span><h2>${esc(t.name)}</h2><p>${esc(t.description||'')} · ${Number(t.days_per_week||t.days?.length||1)} días</p></div><button class="vp-template-close" type="button" aria-label="Cerrar">×</button></div><div class="vp-template-body"><div class="vp-template-days"></div><div class="vp-template-exercises"></div></div><div class="vp-template-actions"><button type="button" class="vp-template-save">Guardar rutina</button><button type="button" class="vp-template-activate">Guardar y activar</button></div></div>`;document.body.appendChild(o);
    const days=o.querySelector('.vp-template-days'), exercises=o.querySelector('.vp-template-exercises');
    const render=()=>{const ds=Array.isArray(t.days)?t.days:[];days.innerHTML=ds.map((d,i)=>`<button type="button" data-day="${i}" class="${i===day?'selected':''}">${esc(d.name||`Día ${i+1}`)}</button>`).join('');const list=ds[day]?.items||t.exercises||[];exercises.innerHTML=list.length?list.map((x,i)=>`<div class="vp-template-exercise"><b>${i+1}. ${esc(x.exercise||x.name||'Ejercicio')}</b><span>${Number(x.sets||3)} series × ${Number(x.reps||10)} reps · descanso ${Number(x.rest_sec||90)}s</span></div>`).join(''):`<div class="card empty">Este día no tiene ejercicios.</div>`};render();
    days.addEventListener('click',e=>{const b=e.target.closest('[data-day]');if(!b)return;day=Number(b.dataset.day)||0;render()});o.querySelector('.vp-template-close').onclick=()=>o.remove();o.addEventListener('click',e=>{if(e.target===o)o.remove()});o.querySelector('.vp-template-save').onclick=()=>saveTemplate({...t,activeDay:day},false);o.querySelector('.vp-template-activate').onclick=()=>saveTemplate({...t,activeDay:day},true);
  }
  document.addEventListener('click',e=>{
    const view=e.target.closest('[data-action="view-template"]');if(view){e.preventDefault();e.stopImmediatePropagation();openTemplate(view.dataset.template);return}
    const activate=e.target.closest('[data-action="activate-routine"]');if(activate){e.preventDefault();e.stopImmediatePropagation();activateRoutine(activate.dataset.id).catch(()=>{});}
  },true);
})();
