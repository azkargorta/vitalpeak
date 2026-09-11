(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile', STORE='state';
  const SENT_KEY='vitalpeak:training-notification-last-sent';
  const STATUS_ID='vp-notify-today-status';
  const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  function hasWorkout(state,date=today()){const raw=state.plan?.[date];return Array.isArray(raw)?raw.length>0:!!raw}
  async function renderTodayStatus(){
    const card=document.getElementById('vp-training-notifications');
    if(!card)return;
    let el=document.getElementById(STATUS_ID);
    if(!el){el=document.createElement('p');el.id=STATUS_ID;el.style.margin='8px 0 0';el.style.padding='9px 11px';el.style.borderRadius='12px';el.style.fontSize='11px';el.style.lineHeight='1.4';card.appendChild(el)}
    const state=await readState().catch(()=>null),yes=!!state&&hasWorkout(state);
    el.textContent=yes?'Hoy: entrenamiento detectado en tu calendario.':'Hoy: no hay entrenamiento detectado en tu calendario; no se enviará aviso programado.';
    el.style.background=yes?'#eef8f5':'#fff7e8';
    el.style.color=yes?'#567178':'#8b6416';
  }
  document.addEventListener('change',e=>{
    if(e.target.closest('[data-vp-notify-time]')){
      localStorage.removeItem(SENT_KEY);
      setTimeout(renderTodayStatus,50);
    }
    if(e.target.closest('[data-vp-notify-toggle]'))setTimeout(renderTodayStatus,50);
  },true);
  const app=document.getElementById('app');if(app)new MutationObserver(()=>setTimeout(renderTodayStatus,60)).observe(app,{childList:true,subtree:true});
  setTimeout(renderTodayStatus,500);
})();