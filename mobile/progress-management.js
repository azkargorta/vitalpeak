(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state';
  const RECORDS_KEY='vitalpeak:progress-records-expanded';
  const STYLE_ID='vp-progress-records-style';
  let enhancing=false;
  let lastTouch=0;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=v=>Number(v||0);
  const fmt=(v,d=1)=>Number(v||0).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`.vp-record-toggle-fixed{margin-top:7px!important}`;document.head.appendChild(s);
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

  async function enhance(){
    if(enhancing||!document.querySelector('.tabbar button[data-route="progress"].active')||!document.querySelector('.vp-progress-page'))return;
    enhancing=true;try{injectStyles();await enhanceRecords()}finally{enhancing=false}
  }
  async function toggleRecords(e){
    const button=e.target.closest('.vp-progress-page [data-vp-toggle-records]');if(!button)return false;
    e.preventDefault();e.stopImmediatePropagation();
    const expanded=sessionStorage.getItem(RECORDS_KEY)==='1';sessionStorage.setItem(RECORDS_KEY,expanded?'0':'1');await enhanceRecords();return true;
  }
  document.addEventListener('touchend',e=>{if(!e.target.closest('.vp-progress-page [data-vp-toggle-records]'))return;lastTouch=Date.now();toggleRecords(e)}, {capture:true,passive:false});
  document.addEventListener('click',e=>{if(Date.now()-lastTouch<500&&e.target.closest('.vp-progress-page [data-vp-toggle-records]')){e.preventDefault();e.stopImmediatePropagation();return}toggleRecords(e)},true);

  const app=document.querySelector('#app');if(app)new MutationObserver(()=>{clearTimeout(window.__vpProgressManagementTimer);window.__vpProgressManagementTimer=setTimeout(enhance,40)}).observe(app,{childList:true,subtree:false});
  const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(()=>setTimeout(enhance,30)).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  injectStyles();setTimeout(enhance,80);
})();