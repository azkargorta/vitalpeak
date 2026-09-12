(() => {
  'use strict';

  const STYLE_ID='vp-routines-transition-guard-style';
  const LOADER_ID='vp-routines-loading';
  const RECOVERY_KEY='vitalpeak:routines-clean-recovery';
  const APP=()=>document.getElementById('app');
  let retryTimer=null, rafId=null, recoveryTimer=null, token=0;

  function styles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');
    s.id=STYLE_ID;
    s.textContent=`
      #${LOADER_ID}{position:fixed;inset:0 0 calc(78px + env(safe-area-inset-bottom)) 0;z-index:640;display:grid;place-items:center;padding:24px;background:linear-gradient(180deg,#f5fbf9 0%,#edf6f3 100%);opacity:0;visibility:hidden;pointer-events:none;transition:opacity .12s ease,visibility .12s ease}
      #${LOADER_ID}.show{opacity:1;visibility:visible;pointer-events:auto}
      #${LOADER_ID} .vp-routines-loading-card{display:grid;justify-items:center;gap:12px;width:min(310px,86vw);padding:28px 22px;border:1px solid rgba(22,169,142,.14);border-radius:22px;background:rgba(255,255,255,.94);box-shadow:0 14px 38px rgba(16,46,56,.08);text-align:center}
      #${LOADER_ID} .vp-routines-spinner{width:34px;height:34px;border:3px solid #d9ebe6;border-top-color:#16a98e;border-radius:50%;animation:vp-routines-spin .72s linear infinite}
      #${LOADER_ID} b{font-size:17px;color:#153f49;letter-spacing:-.02em}
      #${LOADER_ID} span{font-size:12px;line-height:1.45;color:#73878c}
      @keyframes vp-routines-spin{to{transform:rotate(360deg)}}
      @media(prefers-reduced-motion:reduce){#${LOADER_ID} .vp-routines-spinner{animation-duration:1.4s}}
    `;
    document.head.appendChild(s);
  }

  function loader(){
    let el=document.getElementById(LOADER_ID);
    if(el) return el;
    el=document.createElement('div');
    el.id=LOADER_ID;
    el.setAttribute('role','status');
    el.setAttribute('aria-live','polite');
    el.innerHTML='<div class="vp-routines-loading-card"><i class="vp-routines-spinner" aria-hidden="true"></i><b>Cargando rutinas…</b><span data-vp-routines-loading-text>Preparando tu rutina activa y tus planes.</span></div>';
    document.body.appendChild(el);
    return el;
  }

  function showLoader(){
    styles();
    const el=loader();
    const text=el.querySelector('[data-vp-routines-loading-text]');
    if(text) text.textContent='Preparando tu rutina activa y tus planes.';
    el.classList.add('show');
  }
  function hideLoader(){ document.getElementById(LOADER_ID)?.classList.remove('show'); }

  function stopWatch(){
    if(rafId){cancelAnimationFrame(rafId);rafId=null;}
    if(retryTimer){clearInterval(retryTimer);retryTimer=null;}
    if(recoveryTimer){clearTimeout(recoveryTimer);recoveryTimer=null;}
  }

  function release(){
    stopWatch();
    hideLoader();
    try{sessionStorage.removeItem(RECOVERY_KEY)}catch{}
  }

  function isActive(){
    return !!document.querySelector('.tabbar [data-route="routines"].active');
  }

  function ready(){
    const app=APP();
    if(!app || !isActive()) return false;
    const accordion=app.querySelector('#vp-routines-accordion');
    const activeCard=app.querySelector('.vp-routines-active');
    const redesigned=app.classList.contains('vp-routines-page');
    const summaries=accordion?[...accordion.querySelectorAll('.vp-routine-section > summary')]:[];
    const polished=summaries.length>=6 && summaries.every(x=>x.dataset.vpPolished==='1' || x.querySelector('.vp-section-title'));
    return !!(redesigned && activeCard && accordion && polished);
  }

  function wakeRoutinesEnhancers(){
    const app=APP();
    if(!app || !isActive() || ready()) return;
    if(!app.querySelector('#vp-routines-accordion') && /Planes preparados|Catálogo de ejercicios|Planes y ejercicios/.test(app.textContent||'')){
      const marker=document.createElement('i');
      marker.hidden=true;
      marker.dataset.vpRoutinesWake='1';
      app.appendChild(marker);
      marker.remove();
    }
  }

  function recoverCleanly(myToken){
    if(myToken!==token || !isActive() || ready()) return;
    let recovered=false;
    try{recovered=sessionStorage.getItem(RECOVERY_KEY)==='1'}catch{}
    if(!recovered){
      try{
        sessionStorage.setItem(RECOVERY_KEY,'1');
        sessionStorage.setItem('vitalpeak:return-to-routines','1');
      }catch{}
      location.reload();
      return;
    }
    const text=document.querySelector(`#${LOADER_ID} [data-vp-routines-loading-text]`);
    if(text) text.textContent='Terminando de preparar tus rutinas…';
  }

  function begin(){
    token+=1;
    const myToken=token;
    stopWatch();
    showLoader();

    wakeRoutinesEnhancers();
    retryTimer=setInterval(()=>{
      if(myToken!==token || !isActive()){release();return;}
      if(ready()){release();return;}
      wakeRoutinesEnhancers();
    },80);

    const check=()=>{
      if(myToken!==token) return;
      if(!isActive()){release();return;}
      if(ready()){release();return;}
      rafId=requestAnimationFrame(check);
    };
    rafId=requestAnimationFrame(check);

    // La primera carga limpia funciona de forma fiable. Si una reentrada queda en un
    // DOM parcialmente transformado, hacemos una única recuperación limpia y volvemos
    // directamente a Rutinas. RECOVERY_KEY impide cualquier bucle de recargas.
    recoveryTimer=setTimeout(()=>recoverCleanly(myToken),1800);
  }

  document.addEventListener('pointerdown',e=>{
    const tab=e.target.closest?.('.tabbar [data-route]');
    if(!tab) return;
    if(tab.dataset.route==='routines') begin();
    else { token+=1; release(); }
  },true);

  document.addEventListener('click',e=>{
    const tab=e.target.closest?.('.tabbar [data-route]');
    if(!tab) return;
    if(tab.dataset.route==='routines' && !ready()) begin();
    else if(tab.dataset.route!=='routines'){ token+=1; release(); }
  },true);

  const tabs=document.querySelector('.tabbar');
  if(tabs){
    new MutationObserver(()=>{
      if(isActive() && !ready()) begin();
      else if(!isActive()) release();
    }).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  }
})();
