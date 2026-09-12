(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile', STORE='state';
  const STYLE_ID='vp-training-session-ui-styles';
  const FLAG='vitalpeak:return-to-train';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-session-overview{margin:0 0 14px;padding:16px;border:1px solid rgba(22,169,142,.18);border-radius:20px;background:linear-gradient(145deg,#f8fffd,#eef8f5);box-shadow:0 8px 22px rgba(16,46,56,.055)}
      .vp-session-overview-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}.vp-session-overview-head b{display:block;color:#143c45;font-size:15px}.vp-session-overview-head span{display:block;margin-top:3px;color:#73878c;font-size:11px}.vp-session-percent{flex:0 0 auto;display:grid;place-items:center;min-width:48px;height:34px;padding:0 10px;border-radius:999px;background:#dff7f1;color:#147b6d;font-size:12px;font-weight:900}
      .vp-session-bar{height:8px;overflow:hidden;border-radius:999px;background:#dfeae7}.vp-session-bar>i{display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,#18a68d,#4fd3c1);transition:width .25s ease}
      .vp-session-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:11px}.vp-session-stat{padding:9px 8px;border-radius:12px;background:rgba(255,255,255,.78);text-align:center}.vp-session-stat b{display:block;color:#153d45;font-size:15px}.vp-session-stat span{display:block;margin-top:2px;color:#7b8c91;font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}
      .vp-session-exercises{display:grid;gap:7px;margin:0 0 14px}.vp-session-exercise{width:100%;display:grid;grid-template-columns:30px minmax(0,1fr) auto;gap:10px;align-items:center;padding:10px 11px;border:1px solid #dce8e5;border-radius:14px;background:#fff;text-align:left;color:#173b42}.vp-session-exercise-index{display:grid;place-items:center;width:30px;height:30px;border-radius:10px;background:#edf4f2;color:#68807f;font-size:11px;font-weight:900}.vp-session-exercise-copy{min-width:0}.vp-session-exercise-copy b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}.vp-session-exercise-copy span{display:block;margin-top:2px;color:#7a8d91;font-size:10px}.vp-session-exercise-state{padding:5px 8px;border-radius:999px;background:#f1f5f4;color:#758886;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.03em}
      .vp-session-exercise.is-current{border-color:#4fcab8;background:linear-gradient(145deg,#f6fffc,#eaf9f5);box-shadow:0 6px 16px rgba(22,169,142,.08)}.vp-session-exercise.is-current .vp-session-exercise-index{background:#d9f7f0;color:#11806f}.vp-session-exercise.is-current .vp-session-exercise-state{background:#dff7f1;color:#117966}
      .vp-session-exercise.is-done{border-color:#d1e9e3}.vp-session-exercise.is-done .vp-session-exercise-index{background:#dff7f1;color:#117966}.vp-session-exercise.is-done .vp-session-exercise-state{background:#e4f7f2;color:#117966}
      #set-form+.set-list{margin-top:10px}.session-nav [data-action="next-exercise"]{font-weight:900}.session-nav [data-action="next-exercise"]:not([disabled]){border-color:#63cdbd}
      @media(max-width:420px){.vp-session-overview{padding:14px}.vp-session-stats{gap:5px}.vp-session-stat{padding:8px 5px}.vp-session-exercise{grid-template-columns:28px minmax(0,1fr) auto;padding:9px}.vp-session-exercise-state{padding:4px 6px;font-size:8px}}
    `;document.head.appendChild(s);
  }
  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(st){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.objectStore(STORE).put(st,'user')})}
  const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
  function planEntries(st,iso=today()){const raw=st.plan?.[iso];return Array.isArray(raw)?raw:(raw?[raw]:[])}
  function routineById(st,id){return (st.routines||[]).find(r=>String(r.id)===String(id))||null}
  function selectedRoutine(st){
    const planned=planEntries(st).map(raw=>{const [id,day]=String(raw).split('::'),r=routineById(st,id);return r?{...r,activeDay:Number(day||0)}:null}).filter(Boolean);
    if(planned.length){const i=Math.min(Number(st.todaySessionIndex||0),planned.length-1);return planned[i]}
    return routineById(st,st.activeRoutineId)||(st.routines||[])[0]||null;
  }
  function routineItems(r){return r?.days?.[Number(r.activeDay||0)]?.items||r?.exercises||[]}
  function setCountFor(draft,name){return (draft?.sets||[]).filter(s=>String(s.exercise)===String(name)).length}

  async function enhance(){
    const form=document.querySelector('#set-form');
    if(!form)return;
    injectStyles();
    const card=form.closest('.card');
    if(!card||card.dataset.vpSessionEnhanced==='1')return;
    const st=await readState().catch(()=>null);if(!st)return;
    const r=selectedRoutine(st), draft=st._draft;if(!r||!draft)return;
    const list=routineItems(r);if(!list.length)return;
    const index=Math.min(Number(draft.exerciseIndex||0),list.length-1);
    const done=list.filter(x=>setCountFor(draft,x.exercise||x.name)>=Number(x.sets||1)).length;
    const totalSets=(draft.sets||[]).length;
    const targetSets=list.reduce((sum,x)=>sum+Number(x.sets||1),0);
    const percent=Math.min(100,Math.round((done/list.length)*100));
    const overview=document.createElement('section');overview.className='vp-session-overview';overview.innerHTML=`<div class="vp-session-overview-head"><div><b>Progreso de la sesión</b><span>${esc(r.days?.[Number(r.activeDay||0)]?.name||r.name||'Entrenamiento')}</span></div><strong class="vp-session-percent">${percent}%</strong></div><div class="vp-session-bar"><i style="width:${percent}%"></i></div><div class="vp-session-stats"><div class="vp-session-stat"><b>${done}/${list.length}</b><span>ejercicios</span></div><div class="vp-session-stat"><b>${totalSets}</b><span>series hechas</span></div><div class="vp-session-stat"><b>${Math.max(0,targetSets-totalSets)}</b><span>series objetivo</span></div></div>`;
    const exercises=document.createElement('section');exercises.className='vp-session-exercises';
    exercises.innerHTML=list.map((x,i)=>{const name=x.exercise||x.name||`Ejercicio ${i+1}`,sets=setCountFor(draft,name),target=Number(x.sets||1),doneOne=sets>=target,current=i===index;return `<button type="button" class="vp-session-exercise ${current?'is-current':''} ${doneOne?'is-done':''}" data-vp-jump-exercise="${i}"><span class="vp-session-exercise-index">${doneOne?'✓':i+1}</span><span class="vp-session-exercise-copy"><b>${esc(name)}</b><span>${sets}/${target} series · ${esc(x.reps||'—')} reps</span></span><span class="vp-session-exercise-state">${current?'Ahora':doneOne?'Hecho':'Pendiente'}</span></button>`}).join('');
    card.dataset.vpSessionEnhanced='1';card.parentElement?.insertBefore(exercises,card);card.parentElement?.insertBefore(overview,exercises);
  }

  document.addEventListener('click',async e=>{
    const b=e.target.closest('[data-vp-jump-exercise]');if(!b)return;
    e.preventDefault();e.stopImmediatePropagation();
    const st=await readState().catch(()=>null);if(!st?._draft)return;
    st._draft.exerciseIndex=Number(b.dataset.vpJumpExercise)||0;st._draft.pendingChoice=false;st._draft.restEndsAt=null;
    await writeState(st);sessionStorage.setItem(FLAG,'1');location.reload();
  },true);

  if(sessionStorage.getItem(FLAG)==='1'){
    sessionStorage.removeItem(FLAG);let tries=0;const t=setInterval(()=>{const b=document.querySelector('[data-route="train"]');if(b){clearInterval(t);b.click()}else if(++tries>100)clearInterval(t)},50);
  }
  const app=document.getElementById('app');if(app)new MutationObserver(()=>setTimeout(enhance,25)).observe(app,{childList:true,subtree:true});
  setTimeout(enhance,300);
})();
