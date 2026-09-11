(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile', STORE='state';
  const OPEN_KEY='vitalpeak:progress-weight-open';

  function openDb(){
    return new Promise((resolve,reject)=>{
      const r=indexedDB.open(DB_NAME,2);
      r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};
      r.onsuccess=()=>resolve(r.result);
      r.onerror=()=>reject(r.error);
    });
  }
  async function readState(){
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readonly');
      const q=tx.objectStore(STORE).get('user');
      q.onsuccess=()=>resolve(q.result||{});
      q.onerror=()=>reject(q.error);
    });
  }
  async function writeState(state){
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readwrite');
      tx.objectStore(STORE).put(state,'user');
      tx.oncomplete=resolve;
      tx.onerror=()=>reject(tx.error);
    });
  }
  function today(){return new Date().toISOString().slice(0,10)}
  function restoreOpenState(){
    const form=document.querySelector('.vp-progress-page .vp-weight-form');
    if(form && sessionStorage.getItem(OPEN_KEY)==='1') form.classList.add('open');
  }
  function refreshProgress(){
    sessionStorage.removeItem(OPEN_KEY);
    const btn=document.querySelector('.tabbar button[data-route="progress"]');
    if(btn) btn.click();
  }
  function focusInput(form){
    const input=form?.querySelector('input[name="kg"]');
    if(!input) return;
    input.removeAttribute('readonly');
    input.focus({preventScroll:true});
    try{input.setSelectionRange(input.value.length,input.value.length)}catch{}
  }

  document.addEventListener('click',e=>{
    const button=e.target.closest('.vp-progress-page [data-vp-toggle-weight]');
    if(!button) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const form=document.querySelector('.vp-progress-page .vp-weight-form');
    if(!form) return;
    const opening=!form.classList.contains('open');
    form.classList.toggle('open',opening);
    if(opening){
      sessionStorage.setItem(OPEN_KEY,'1');
      focusInput(form);
    }else sessionStorage.removeItem(OPEN_KEY);
  },true);

  document.addEventListener('touchend',e=>{
    const button=e.target.closest('.vp-progress-page [data-vp-toggle-weight]');
    if(!button) return;
    const form=document.querySelector('.vp-progress-page .vp-weight-form');
    if(!form) return;
    form.classList.add('open');
    sessionStorage.setItem(OPEN_KEY,'1');
    focusInput(form);
  },{capture:true,passive:true});

  document.addEventListener('submit',async e=>{
    const form=e.target.closest('.vp-progress-page .vp-weight-form');
    if(!form) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const input=form.querySelector('input[name="kg"]');
    const kg=Number(input?.value);
    if(!Number.isFinite(kg)||kg<=0){focusInput(form);return;}
    try{
      const state=await readState();
      state.weights=Array.isArray(state.weights)?state.weights:[];
      state.weights.push({date:today(),kg});
      await writeState(state);
      refreshProgress();
    }catch(err){
      console.error('No se pudo guardar el peso',err);
      alert('No se pudo guardar el peso. Inténtalo de nuevo.');
    }
  },true);

  const root=document.querySelector('#app');
  if(root) new MutationObserver(restoreOpenState).observe(root,{childList:true,subtree:false});
  restoreOpenState();
})();