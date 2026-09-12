(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile', STORE='state';
  const STYLE_ID='vp-routine-active-ux-styles';

  function injectStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-active-resume{display:inline-flex;align-items:center;gap:6px;margin-top:7px;padding:5px 8px;border-radius:999px;background:#fff3d9;color:#8b6416;font-size:10px;font-weight:900;letter-spacing:.02em}
      .vp-active-resume:before{content:'';width:7px;height:7px;border-radius:50%;background:#e4a72d;box-shadow:0 0 0 3px rgba(228,167,45,.13)}
      .vp-template-train{width:100%;min-height:48px;border:0;border-radius:13px;background:linear-gradient(90deg,#173f49,#176d61)!important;color:#fff!important;font-weight:900!important}
      .vp-template-actions.vp-two-actions{grid-template-columns:1fr 1fr!important}
      @media(max-width:390px){.vp-template-actions.vp-two-actions{grid-template-columns:1fr!important}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),g=tx.objectStore(STORE).get('user');g.onsuccess=()=>resolve(g.result||{});g.onerror=()=>reject(g.error)})}

  async function enhanceActiveCard(){
    const state=await readState().catch(()=>null);if(!state?.activeRoutineId)return;
    const draft=state._draft;
    if(!draft || String(draft.routineId)!==String(state.activeRoutineId) || !(draft.sets||[]).length) return;
    const candidates=[...document.querySelectorAll('[data-action="activate-routine"]')].filter(x=>String(x.dataset.id)===String(state.activeRoutineId));
    candidates.forEach(card=>{
      if(card.querySelector('.vp-active-resume'))return;
      const badge=document.createElement('span');badge.className='vp-active-resume';badge.textContent=`Sesión en curso · ${(draft.sets||[]).length} serie${(draft.sets||[]).length===1?'':'s'}`;
      card.appendChild(badge);
    });
  }

  async function enhanceSavedRoutineModal(){
    const modal=document.querySelector('.vp-template-modal');if(!modal)return;
    const actions=modal.querySelector('.vp-template-actions');if(!actions || actions.querySelector('.vp-template-train'))return;
    const activate=actions.querySelector('.vp-template-activate');
    if(!activate?.disabled)return;
    injectStyles();actions.classList.add('vp-two-actions');
    const train=document.createElement('button');train.type='button';train.className='vp-template-train';train.textContent='Entrenar ahora';
    train.addEventListener('click',()=>{
      document.querySelector('.vp-template-backdrop')?.remove();
      const routeButton=document.querySelector('[data-route="train"]');
      if(routeButton) routeButton.click();
    });
    actions.appendChild(train);
  }

  let queued=false;
  function refresh(){
    if(queued)return;queued=true;
    requestAnimationFrame(()=>{queued=false;enhanceActiveCard();enhanceSavedRoutineModal();});
  }
  injectStyles();
  const app=document.getElementById('app');if(app)new MutationObserver(refresh).observe(app,{childList:true,subtree:true});
  new MutationObserver(refresh).observe(document.body,{childList:true,subtree:true});
  document.addEventListener('click',()=>setTimeout(refresh,40),true);
  setTimeout(refresh,250);
})();