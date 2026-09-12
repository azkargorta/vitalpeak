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

  function cleanDuplicates(app, accordion){
    if(!accordion) return;

    // Solo debe existir un acordeón canónico.
    [...app.querySelectorAll('#vp-routines-accordion')].forEach(node=>{
      if(node!==accordion) node.remove();
    });

    // Elimina secciones antiguas/sueltas que ya están representadas dentro
    // del acordeón. No toca las secciones canónicas ni la tarjeta activa.
    [...app.querySelectorAll('.vp-routine-section')].forEach(section=>{
      if(!accordion.contains(section)) section.remove();
    });

    // Limpia restos del render base que pueden quedar debajo del rediseño.
    [...app.querySelectorAll('.section-head')].forEach(head=>{
      if(accordion.contains(head)) return;
      const title=(head.querySelector('h2')?.textContent||head.textContent||'').trim();
      if(!['Rutina personalizada','Planes preparados','Catálogo de ejercicios','Tu rutina activa'].includes(title)) return;
      const next=head.nextElementSibling;
      head.remove();
      if(next && !accordion.contains(next) && !next.classList.contains('vp-routines-active') && !next.classList.contains('vp-routines-coach')) next.remove();
    });
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
    if(accordion) cleanDuplicates(app, accordion);

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
