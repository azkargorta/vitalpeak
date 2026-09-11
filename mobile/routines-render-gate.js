(() => {
  'use strict';

  const APP = () => document.querySelector('#app');
  const ROUTINES_BUTTON = () => document.querySelector('.tabbar button[data-route="routines"]');
  const REQUIRED = ['personal-routines','routine-history','custom','add-exercise','predefined-routines','predefined-exercises'];
  const STYLE_ID = 'vp-routines-render-gate-style';
  let timer = null;

  function injectStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #app.vp-routines-preparing{visibility:hidden!important;pointer-events:none!important}
      #app.vp-routines-ready{visibility:visible!important;pointer-events:auto!important}
    `;
    document.head.appendChild(style);
  }

  function isRoutinesRoute(){
    const btn = ROUTINES_BUTTON();
    const app = APP();
    return !!(btn?.classList.contains('active') || /Planes y ejercicios|RUTINAS/.test(app?.textContent || ''));
  }

  function hideWhilePreparing(){
    const app = APP();
    if(!app || !isRoutinesRoute()) return;
    if(!app.classList.contains('vp-routines-ready')) app.classList.add('vp-routines-preparing');
  }

  function cleanDuplicates(app, canonical){
    // Nunca puede quedar más de un acordeón de Rutinas.
    [...app.querySelectorAll('#vp-routines-accordion')].forEach(acc => {
      if(acc !== canonical) acc.remove();
    });

    // Quita cualquier sección generada fuera del acordeón definitivo.
    [...app.querySelectorAll('.vp-routine-section')].forEach(section => {
      if(!canonical.contains(section)) section.remove();
    });

    // Quita restos visibles del layout antiguo que no hayan sido movidos al acordeón.
    [...app.querySelectorAll('.section-head')].forEach(head => {
      if(canonical.contains(head)) return;
      const title = (head.querySelector('h2')?.textContent || head.textContent || '').trim();
      if(['Rutina personalizada','Planes preparados','Catálogo de ejercicios','Tu rutina activa'].includes(title)) {
        const next = head.nextElementSibling;
        head.remove();
        if(next && !canonical.contains(next) && !next.classList.contains('vp-routines-active')) next.remove();
      }
    });
  }

  function ready(){
    const app = APP();
    if(!app || !isRoutinesRoute()) return false;

    const accordions = [...app.querySelectorAll('#vp-routines-accordion')];
    if(!accordions.length) return false;
    const canonical = accordions[0];

    const sections = REQUIRED.map(key => canonical.querySelector(`.vp-routine-section[data-vp-section="${key}"]`));
    if(sections.some(x => !x)) return false;

    // El menú no se muestra hasta que el rediseño haya terminado de aplicar iconos/copys/chevrons.
    const polished = sections.every(section => {
      const summary = section.querySelector(':scope > summary');
      return !!(summary?.querySelector('.vp-section-icon') && summary.querySelector('.vp-section-copy') && summary.querySelector('.vp-section-chevron'));
    });
    if(!polished) return false;

    const coach = app.querySelector('#vp-smart-generator.vp-routines-coach, .vp-routines-coach');
    const active = app.querySelector('.vp-routines-active');
    if(!coach || !active) return false;

    cleanDuplicates(app, canonical);

    // Comprobación final: exactamente seis secciones, todas dentro del acordeón bueno.
    const finalSections = [...app.querySelectorAll('.vp-routine-section')];
    if(finalSections.length !== REQUIRED.length || finalSections.some(section => !canonical.contains(section))) return false;

    app.classList.remove('vp-routines-preparing');
    app.classList.add('vp-routines-ready');
    return true;
  }

  function evaluate(){
    injectStyles();
    const app = APP();
    if(!app) return;

    if(!isRoutinesRoute()){
      app.classList.remove('vp-routines-preparing','vp-routines-ready');
      return;
    }

    hideWhilePreparing();
    ready();
  }

  function schedule(){
    clearTimeout(timer);
    timer = setTimeout(evaluate, 20);
  }

  injectStyles();
  const start = () => {
    const app = APP();
    if(!app) return setTimeout(start, 25);
    new MutationObserver(schedule).observe(app,{childList:true,subtree:true,attributes:true,attributeFilter:['class','open']});
    document.querySelector('.tabbar') && new MutationObserver(schedule).observe(document.querySelector('.tabbar'),{subtree:true,attributes:true,attributeFilter:['class']});
    evaluate();
  };
  start();
})();
