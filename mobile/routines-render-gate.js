(() => {
  'use strict';

  const APP = () => document.querySelector('#app');
  const ROUTINES_BUTTON = () => document.querySelector('.tabbar button[data-route="routines"]');
  const REQUIRED = ['personal-routines','routine-history','custom','add-exercise','predefined-routines','predefined-exercises'];
  let timer = null;

  function isRoutinesRoute(){
    const btn = ROUTINES_BUTTON();
    const app = APP();
    return !!(btn?.classList.contains('active') || /Planes y ejercicios|RUTINAS/.test(app?.textContent || ''));
  }

  function evaluate(){
    const app = APP();
    if(!app) return;

    // Fail-open: nunca ocultamos #app. Si las capas avanzadas tardan o fallan,
    // el render base de Rutinas debe seguir siendo visible y navegable.
    app.classList.remove('vp-routines-preparing');

    if(!isRoutinesRoute()){
      app.classList.remove('vp-routines-ready');
      return;
    }

    const accordion = app.querySelector('#vp-routines-accordion');
    const sections = accordion
      ? REQUIRED.map(key => accordion.querySelector(`.vp-routine-section[data-vp-section="${key}"]`))
      : [];
    const coach = app.querySelector('#vp-smart-generator.vp-routines-coach, .vp-routines-coach');
    const active = app.querySelector('.vp-routines-active');
    const complete = !!accordion && sections.length === REQUIRED.length && sections.every(Boolean) && !!coach && !!active;
    app.classList.toggle('vp-routines-ready', complete);
  }

  function schedule(delay=35){
    clearTimeout(timer);
    timer = setTimeout(evaluate, delay);
  }

  const start = () => {
    const app = APP();
    if(!app) return setTimeout(start, 30);

    // Solo cambios de página, no cada modificación interna del acordeón.
    new MutationObserver(() => schedule()).observe(app,{childList:true,subtree:false});
    const tabbar=document.querySelector('.tabbar');
    if(tabbar) new MutationObserver(() => schedule()).observe(tabbar,{subtree:true,attributes:true,attributeFilter:['class']});

    document.addEventListener('click',e=>{
      if(e.target.closest('.tabbar [data-route]')) schedule(0);
    },true);

    evaluate();
  };
  start();
})();
