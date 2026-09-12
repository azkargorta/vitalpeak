(() => {
  'use strict';

  const APP = () => document.querySelector('#app');
  const ROUTINES_BUTTON = () => document.querySelector('.tabbar button[data-route="routines"]');
  const REQUIRED = ['personal-routines','routine-history','custom','add-exercise','predefined-routines','predefined-exercises'];
  let timer = null;
  let cachedView = null;
  let cachedScrollY = 0;
  let restorePending = false;
  let restoring = false;

  function isRoutinesActive(){
    return !!ROUTINES_BUTTON()?.classList.contains('active');
  }

  function isRoutinesRoute(){
    const app = APP();
    return !!(isRoutinesActive() || /Planes y ejercicios|RUTINAS/.test(app?.textContent || ''));
  }

  function hasModernView(app=APP()){
    if(!app) return false;
    const accordion = app.querySelector('#vp-routines-accordion');
    if(!accordion) return false;
    return REQUIRED.every(key => accordion.querySelector(`.vp-routine-section[data-vp-section="${key}"]`));
  }

  function cleanDuplicates(app, accordion){
    if(!accordion) return;

    [...app.querySelectorAll('#vp-routines-accordion')].forEach(node=>{
      if(node!==accordion) node.remove();
    });

    [...app.querySelectorAll('.vp-routine-section')].forEach(section=>{
      if(!accordion.contains(section)) section.remove();
    });

    [...app.querySelectorAll('.section-head')].forEach(head=>{
      if(accordion.contains(head)) return;
      const title=(head.querySelector('h2')?.textContent||head.textContent||'').trim();
      if(!['Rutina personalizada','Planes preparados','Catálogo de ejercicios','Tu rutina activa'].includes(title)) return;
      const next=head.nextElementSibling;
      head.remove();
      if(next && !accordion.contains(next) && !next.classList.contains('vp-routines-active') && !next.classList.contains('vp-routines-coach')) next.remove();
    });
  }

  function captureModernView(){
    const app = APP();
    if(!app || !isRoutinesActive() || !hasModernView(app)) return false;

    const fragment = document.createDocumentFragment();
    while(app.firstChild) fragment.appendChild(app.firstChild);
    cachedView = fragment;
    cachedScrollY = window.scrollY;
    app.classList.remove('vp-routines-ready');
    return true;
  }

  function restoreModernView(){
    const app = APP();
    if(!app || !restorePending || !cachedView || !isRoutinesActive()) return false;

    restoring = true;
    restorePending = false;
    app.replaceChildren(cachedView);
    cachedView = null;
    restoring = false;

    const accordion = app.querySelector('#vp-routines-accordion');
    if(accordion) cleanDuplicates(app, accordion);
    app.classList.add('vp-routines-ready');
    requestAnimationFrame(()=>window.scrollTo({top:cachedScrollY,left:0,behavior:'auto'}));
    return true;
  }

  function wakeMountObservers(){
    const app = APP();
    if(!app || !isRoutinesActive() || hasModernView(app)) return;
    const marker=document.createElement('span');
    marker.hidden=true;
    marker.dataset.vpRoutineWake='1';
    app.appendChild(marker);
    marker.remove();
  }

  function evaluate(){
    const app = APP();
    if(!app) return;

    app.classList.remove('vp-routines-preparing');

    if(!isRoutinesRoute()){
      app.classList.remove('vp-routines-ready');
      return;
    }

    if(restoreModernView()) return;

    const accordion = app.querySelector('#vp-routines-accordion');
    if(accordion) cleanDuplicates(app, accordion);

    const complete = hasModernView(app);
    app.classList.toggle('vp-routines-ready', complete);

    if(!complete && isRoutinesActive()) wakeMountObservers();
  }

  function schedule(delay=20){
    clearTimeout(timer);
    timer = setTimeout(evaluate, delay);
  }

  const start = () => {
    const app = APP();
    if(!app) return setTimeout(start, 30);

    new MutationObserver(() => {
      if(restoring) return;
      if(restorePending && cachedView && isRoutinesActive()) {
        restoreModernView();
        return;
      }
      schedule();
    }).observe(app,{childList:true,subtree:false});

    const tabbar=document.querySelector('.tabbar');
    if(tabbar) new MutationObserver(() => schedule(0)).observe(tabbar,{subtree:true,attributes:true,attributeFilter:['class']});

    document.addEventListener('click',e=>{
      const target=e.target.closest('.tabbar [data-route]');
      if(!target) return;
      const nextRoute=target.dataset.route;

      if(isRoutinesActive() && nextRoute!=='routines') {
        captureModernView();
        return;
      }

      if(!isRoutinesActive() && nextRoute==='routines' && cachedView) {
        restorePending=true;
      }
    },true);

    evaluate();
  };
  start();
})();
