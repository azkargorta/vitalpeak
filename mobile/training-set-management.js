(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state', STYLE_ID='vp-training-set-management-styles';
  let busy=false, timer=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function styles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-set-tools{display:grid;gap:8px;margin-top:10px}
      .vp-set-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;padding:10px 11px;border:1px solid #dce9e6;border-radius:13px;background:#fbfefd}
      .vp-set-main{min-width:0}.vp-set-main b{display:block;color:#173d45;font-size:13px}.vp-set-main small{display:block;margin-top:3px;color:#72868b;font-size:10px}
      .vp-set-compare{display:inline-flex;align-items:center;gap:4px;margin-top:5px;padding:4px 7px;border-radius:999px;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.04em}
      .vp-set-compare.up{background:#e4f7f0;color:#13715f}.vp-set-compare.same{background:#eef3f2;color:#60777c}.vp-set-compare.down{background:#fff0ec;color:#a24f3e}.vp-set-compare.new{background:#edf4ff;color:#37689c}
      .vp-set-actions{display:flex;gap:5px}.vp-set-actions button{min-width:34px;min-height:34px;border:1px solid #d6e4e0;border-radius:10px;background:#fff;color:#31565d;font-size:11px;font-weight:850;padding:6px 8px}.vp-set-actions .danger{color:#a34b42}
      .vp-copy-set{margin-top:8px;min-height:42px;border:1px dashed #a9cfc6;border-radius:12px;background:#f5fbf9;color:#176b60;font-weight:850;width:100%}
      .vp-edit-backdrop{position:fixed;inset:0;z-index:1200;display:grid;place-items:end center;background:rgba(5,22,28,.7);backdrop-filter:blur(7px);padding:14px}
      .vp-edit-card{width:min(520px,100%);border-radius:22px;background:#f8fcfb;padding:17px;box-shadow:0 28px 80px rgba(0,0,0,.3)}.vp-edit-card h3{margin:4px 0 14px;color:#173c45}.vp-edit-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}.vp-edit-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:13px}.vp-edit-actions button{min-height:46px;border-radius:13px;font-weight:900}.vp-edit-cancel{border:1px solid #d2e0dd;background:#fff;color:#385a61}.vp-edit-save{border:0;background:#4fd3c1;color:#12383a}
      .vp-previous-session{margin:10px 0 0;padding:10px 12px;border-radius:12px;background:#f3f8f7;color:#5d7378;font-size:11px;line-height:1.4}
      @media(max-width:390px){.vp-set-row{grid-template-columns:1fr}.vp-set-actions{justify-content:flex-end}.vp-edit-grid{grid-template-columns:1fr}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.objectStore(STORE).put(state,'user')})}

  function currentExercise(){const form=document.getElementById('set-form');const card=form?.closest('.card');return card?.querySelector('.row.between h2')?.textContent?.trim()||card?.querySelector('h2')?.textContent?.trim()||''}
  function refreshTrain(){const b=document.querySelector('[data-route="train"]');if(b){b.click();return}location.reload()}
  function prevSessionSets(state,name){
    const sessions=[...(state.sessions||[])].reverse();
    for(const session of sessions){const xs=(session.sets||[]).filter(s=>String(s.exercise)===String(name));if(xs.length)return xs}
    return [];
  }
  function compare(cur,prev){
    if(!prev)return {kind:'new',label:'Sin referencia'};
    const cw=Number(cur.weight||0),pw=Number(prev.weight||0),cr=Number(cur.reps||0),pr=Number(prev.reps||0);
    if(cw>pw||(cw===pw&&cr>pr))return {kind:'up',label:'Mejora'};
    if(cw===pw&&cr===pr)return {kind:'same',label:'Igual'};
    return {kind:'down',label:'Por debajo'};
  }
  function fmt(s){return `${Number(s.weight||0)} kg × ${Number(s.reps||0)}`}

  async function enhance(){
    if(busy)return;styles();
    const list=document.querySelector('.set-list'),form=document.getElementById('set-form');if(!list||!form||list.dataset.vpManaged==='1')return;
    const name=currentExercise();if(!name)return;const state=await readState().catch(()=>null);if(!state?._draft)return;
    const all=state._draft.sets||[], indices=[];all.forEach((s,i)=>{if(String(s.exercise)===String(name))indices.push(i)});const curSets=indices.map(i=>all[i]);
    if(!curSets.length)return;
    const prev=prevSessionSets(state,name);
    list.innerHTML='';list.dataset.vpManaged='1';const wrap=document.createElement('div');wrap.className='vp-set-tools';
    wrap.innerHTML=curSets.map((s,local)=>{const cmp=compare(s,prev[local]);return `<div class="vp-set-row"><div class="vp-set-main"><b>Serie ${local+1}: ${esc(fmt(s))}</b><small>${prev[local]?`Anterior: ${esc(fmt(prev[local]))}`:'Primera referencia comparable'}</small><span class="vp-set-compare ${cmp.kind}">${cmp.kind==='up'?'↑':cmp.kind==='down'?'↓':cmp.kind==='same'?'=':'•'} ${cmp.label}</span></div><div class="vp-set-actions"><button type="button" data-vp-edit-set="${indices[local]}">Editar</button><button type="button" class="danger" data-vp-delete-set="${indices[local]}">Borrar</button></div></div>`}).join('');
    list.appendChild(wrap);
    const copy=document.createElement('button');copy.type='button';copy.className='vp-copy-set';copy.dataset.vpCopySet='1';copy.textContent='Copiar última serie';list.appendChild(copy);
    if(prev.length){const p=document.createElement('div');p.className='vp-previous-session';p.textContent=`Sesión anterior: ${prev.length} serie${prev.length===1?'':'s'} · mejor referencia ${fmt([...prev].sort((a,b)=>Number(b.weight||0)-Number(a.weight||0)||Number(b.reps||0)-Number(a.reps||0))[0])}`;list.appendChild(p)}
  }

  async function editSet(index){
    const state=await readState();const set=state._draft?.sets?.[index];if(!set)return;
    document.querySelector('.vp-edit-backdrop')?.remove();const o=document.createElement('div');o.className='vp-edit-backdrop';o.innerHTML=`<form class="vp-edit-card" data-vp-edit-form><span class="template-meta">EDITAR SERIE</span><h3>${esc(set.exercise||'Serie')}</h3><div class="vp-edit-grid"><label class="field">Peso (kg)<input name="weight" type="number" inputmode="decimal" step="0.5" min="0" required value="${esc(set.weight)}"></label><label class="field">Repeticiones<input name="reps" type="number" inputmode="numeric" min="1" required value="${esc(set.reps)}"></label></div><label class="field" style="margin-top:9px">Notas<input name="notes" maxlength="100" value="${esc(set.notes||'')}"></label><div class="vp-edit-actions"><button type="button" class="vp-edit-cancel">Cancelar</button><button class="vp-edit-save">Guardar cambios</button></div></form>`;document.body.appendChild(o);
    o.querySelector('.vp-edit-cancel').onclick=()=>o.remove();o.addEventListener('click',e=>{if(e.target===o)o.remove()});o.querySelector('form').onsubmit=async e=>{e.preventDefault();const d=new FormData(e.currentTarget),fresh=await readState();const target=fresh._draft?.sets?.[index];if(!target)return o.remove();target.weight=Number(d.get('weight'));target.reps=Number(d.get('reps'));target.notes=String(d.get('notes')||'');await writeState(fresh);o.remove();refreshTrain()}
  }

  async function deleteSet(index){
    const state=await readState();if(!state._draft?.sets?.[index])return;
    if(!confirm('¿Borrar esta serie?'))return;
    state._draft.sets.splice(index,1);state._draft.pendingChoice=false;await writeState(state);refreshTrain();
  }

  async function copyLast(){
    const state=await readState(),name=currentExercise(),xs=(state._draft?.sets||[]).filter(s=>String(s.exercise)===String(name)),last=xs.at(-1);if(!last)return;
    const form=document.getElementById('set-form');if(!form)return;form.elements.weight.value=Number(last.weight||0);form.elements.reps.value=Number(last.reps||0);if(form.elements.notes)form.elements.notes.value='';form.elements.weight.focus();
  }

  document.addEventListener('click',e=>{const edit=e.target.closest('[data-vp-edit-set]');if(edit){e.preventDefault();editSet(Number(edit.dataset.vpEditSet));return}const del=e.target.closest('[data-vp-delete-set]');if(del){e.preventDefault();deleteSet(Number(del.dataset.vpDeleteSet));return}if(e.target.closest('[data-vp-copy-set]')){e.preventDefault();copyLast()}},true);
  const app=document.getElementById('app');if(app)new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(enhance,80)}).observe(app,{childList:true,subtree:true});
  setTimeout(enhance,120);
})();
