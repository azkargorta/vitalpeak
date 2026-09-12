(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state', STYLE_ID='vp-rir-progression-styles';
  let timer=null, pendingRir=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-load-recommendation{margin:10px 0 12px;padding:12px 13px;border:1px solid #dce9e6;border-radius:15px;background:linear-gradient(145deg,#fbfffe,#f2f8f6)}
      .vp-load-rec-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.vp-load-rec-copy{min-width:0}.vp-load-rec-copy span{display:block;color:#74888d;font-size:9px;font-weight:900;letter-spacing:.06em;text-transform:uppercase}.vp-load-rec-copy b{display:block;margin-top:4px;color:#143d45;font-size:14px}.vp-load-rec-copy p{margin:5px 0 0;color:#70858a;font-size:10px;line-height:1.4}
      .vp-load-rec-chip{flex:none;padding:5px 8px;border-radius:999px;font-size:9px;font-weight:900;text-transform:uppercase}.vp-load-rec-chip.increase{background:#dcf7ef;color:#117964}.vp-load-rec-chip.hold{background:#eef4f4;color:#526d73}.vp-load-rec-chip.review{background:#fff0d3;color:#87631a}.vp-load-rec-chip.insufficient{background:#f0f3f4;color:#738388}
      .vp-rir-block{margin:10px 0 2px;padding:11px 12px;border:1px solid #dce9e6;border-radius:14px;background:#fff}.vp-rir-head{display:flex;justify-content:space-between;gap:10px;align-items:center}.vp-rir-head b{font-size:12px;color:#153d45}.vp-rir-head span{font-size:9px;color:#809197}.vp-rir-options{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:8px}.vp-rir-option{min-height:36px;border:1px solid #d7e5e1;border-radius:10px;background:#f7fbfa;color:#476268;font-size:10px;font-weight:900}.vp-rir-option.is-selected{border-color:#56cbb8;background:#dcf7ef;color:#117964;box-shadow:0 0 0 1px rgba(22,169,142,.08)}.vp-rir-help{margin:7px 0 0;color:#7a8d91;font-size:9px;line-height:1.35}
      @media(max-width:420px){.vp-rir-options{grid-template-columns:repeat(5,1fr);gap:4px}.vp-rir-option{font-size:9px;padding:0 3px}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.objectStore(STORE).put(state,'user')})}

  function routineForDraft(state){
    const d=state._draft;if(!d)return null;
    const id=d.routineId||String(d.routineKey||'').split('::')[0];
    return (state.routines||[]).find(r=>String(r.id)===String(id))||null;
  }
  function currentTarget(state){
    const d=state._draft,r=routineForDraft(state);if(!d||!r)return null;
    const day=Number(String(d.routineKey||'').split('::')[1]||r.activeDay||0);
    const list=r.days?.[day]?.items||r.exercises||[];
    return list[Math.min(Number(d.exerciseIndex||0),Math.max(0,list.length-1))]||null;
  }
  function currentExerciseName(){
    const form=document.getElementById('set-form');if(!form)return '';
    return form.closest('.card')?.querySelector('.row.between h2')?.textContent?.trim()||form.closest('.card')?.querySelector('h2')?.textContent?.trim()||'';
  }

  function recommendationHtml(rec){
    const rir=rec.rir==null?'':` · RIR medio reciente ${Number(rec.rir).toLocaleString('es-ES',{maximumFractionDigits:1})}`;
    return `<section class="vp-load-recommendation"><div class="vp-load-rec-top"><div class="vp-load-rec-copy"><span>Próxima progresión</span><b>${esc(rec.action)}</b><p>${esc(rec.reason)}${esc(rir)}</p></div><span class="vp-load-rec-chip ${esc(rec.status)}">${esc(rec.label)}</span></div></section>`;
  }

  async function enhance(){
    injectStyles();
    const form=document.getElementById('set-form');if(!form||form.dataset.vpRirReady==='1')return;
    const engine=window.VITALPEAK_PROGRESSION_ENGINE;if(!engine)return;
    const state=await readState().catch(()=>null);if(!state?._draft)return;
    const target=currentTarget(state), name=currentExerciseName()||target?.exercise||target?.name;if(!name)return;
    const rec=engine.recommendation(state,name,{sets:target?.sets,reps:target?.reps});
    const recWrap=document.createElement('div');recWrap.innerHTML=recommendationHtml(rec);const recEl=recWrap.firstElementChild;
    const context=form.previousElementSibling?.classList?.contains('vp-exercise-context')?form.previousElementSibling:null;
    (context||form).insertAdjacentElement('beforebegin',recEl);

    const rir=document.createElement('div');rir.className='vp-rir-block';rir.innerHTML=`<div class="vp-rir-head"><b>RIR de esta serie <span style="font-weight:700;color:#8a999d">(opcional)</span></b><span>Repeticiones que te quedaban</span></div><div class="vp-rir-options"><button type="button" class="vp-rir-option" data-vp-rir="0">0</button><button type="button" class="vp-rir-option" data-vp-rir="1">1</button><button type="button" class="vp-rir-option" data-vp-rir="2">2</button><button type="button" class="vp-rir-option" data-vp-rir="3">3+</button><button type="button" class="vp-rir-option is-selected" data-vp-rir="">Omitir</button></div><p class="vp-rir-help">0 = no podrías haber hecho otra repetición; 2 = crees que te quedaban unas dos. No es obligatorio y solo se usa para afinar recomendaciones.</p>`;
    const submit=form.querySelector('button[type="submit"],button:not([type])');
    if(submit)submit.insertAdjacentElement('beforebegin',rir);else form.appendChild(rir);
    form.dataset.vpRirReady='1';
  }

  async function persistRir(){
    const p=pendingRir;pendingRir=null;if(!p||p.rir==null)return;
    const state=await readState().catch(()=>null);if(!state?._draft)return;
    const sets=state._draft.sets||[];
    for(let i=sets.length-1;i>=0;i--){
      const s=sets[i];
      if(String(s.exercise)!==String(p.exercise))continue;
      if(s.rir!=null)continue;
      s.rir=p.rir;
      await writeState(state).catch(()=>{});
      return;
    }
  }

  document.addEventListener('click',e=>{
    const b=e.target.closest('[data-vp-rir]');if(!b)return;
    e.preventDefault();const block=b.closest('.vp-rir-block');block?.querySelectorAll('[data-vp-rir]').forEach(x=>x.classList.toggle('is-selected',x===b));
  },true);

  document.addEventListener('submit',e=>{
    if(e.target?.id!=='set-form')return;
    const selected=e.target.querySelector('.vp-rir-option.is-selected');
    const raw=selected?.dataset.vpRir;
    pendingRir={exercise:currentExerciseName(),rir:raw===''||raw==null?null:Number(raw)};
    if(pendingRir.rir!=null)setTimeout(persistRir,220);
  },true);

  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,80)}
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
  schedule();
})();
