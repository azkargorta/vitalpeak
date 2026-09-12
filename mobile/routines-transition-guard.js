(() => {
  'use strict';

  const STYLE_ID='vp-routines-transition-guard-style';
  const LOADER_ID='vp-routines-loading';
  const CLEAN_ENTRY_KEY='vitalpeak:routines-clean-entry';
  const RETURN_KEY='vitalpeak:return-to-routines';
  let loading=false, rafId=null, slowTimer=null;

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

  function hideLoader(){
    document.getElementById(LOADER_ID)?.classList.remove('show');
    if(rafId){ cancelAnimationFrame(rafId); rafId=null; }
    if(slowTimer){ clearTimeout(slowTimer); slowTimer=null; }
    loading=false;
  }

  function isActive(){
    return !!document.querySelector('.tabbar [data-route="routines"].active');
  }

  function ready(){
    const app=document.getElementById('app');
    if(!app || !isActive()) return false;
    const accordion=app.querySelector('#vp-routines-accordion');
    const activeCard=app.querySelector('.vp-routines-active');
    const redesigned=app.classList.contains('vp-routines-page');
    const summaries=accordion?[...accordion.querySelectorAll('.vp-routine-section > summary')]:[];
    const polished=summaries.length>=6 && summaries.every(x=>x.dataset.vpPolished==='1' || x.querySelector('.vp-section-title'));
    return !!(redesigned && activeCard && accordion && polished);
  }

  function watchUntilReady(){
    if(loading) return;
    loading=true;
    showLoader();

    const check=()=>{
      if(!isActive()) { hideLoader(); return; }
      if(ready()) {
        try{sessionStorage.removeItem(CLEAN_ENTRY_KEY)}catch{}
        hideLoader();
        return;
      }
      rafId=requestAnimationFrame(check);
    };
    rafId=requestAnimationFrame(check);

    slowTimer=setTimeout(()=>{
      if(!loading || ready()) return;
      const text=document.querySelector(`#${LOADER_ID} [data-vp-routines-loading-text]`);
      if(text) text.textContent='Terminando de preparar tus rutinas…';
    },2200);
  }

  function requestCleanEntry(event){
    if(isActive()) return false;
    let clean=false;
    try{ clean=sessionStorage.getItem(CLEAN_ENTRY_KEY)==='1'; }catch{}

    // Tras la recarga limpia, routine-navigation-fix hace un click programático en
    // Rutinas. Ese click debe continuar al router, no provocar otra recarga.
    if(clean){
      watchUntilReady();
      return false;
    }

    event?.preventDefault?.();
    event?.stopImmediatePropagation?.();
    showLoader();
    try{
      sessionStorage.setItem(CLEAN_ENTRY_KEY,'1');
      sessionStorage.setItem(RETURN_KEY,'1');
    }catch{}
    location.reload();
    return true;
  }

  // El pointerdown se ejecuta antes que el router y evita que llegue a pintarse la
  // vista antigua durante la navegación.
  document.addEventListener('pointerdown',e=>{
    const tab=e.target.closest?.('.tabbar [data-route="routines"]');
    if(!tab) return;
    requestCleanEntry(e);
  },true);

  document.addEventListener('click',e=>{
    const tab=e.target.closest?.('.tabbar [data-route]');
    if(!tab) return;
    if(tab.dataset.route==='routines') requestCleanEntry(e);
    else if(loading) hideLoader();
  },true);

  // Si llegamos de una recarga limpia y el router activa Rutinas, esperamos hasta
  // que la interfaz nueva esté completa antes de retirar el cargador.
  const tabs=document.querySelector('.tabbar');
  if(tabs){
    new MutationObserver(()=>{
      if(isActive()){
        let clean=false;
        try{clean=sessionStorage.getItem(CLEAN_ENTRY_KEY)==='1'}catch{}
        if(clean) watchUntilReady();
      }else if(loading){
        hideLoader();
      }
    }).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  }
})();
