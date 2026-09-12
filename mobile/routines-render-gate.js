(() => {
  'use strict';

  const APP = () => document.querySelector('#app');
  const ROUTINES_BUTTON = () => document.querySelector('.tabbar button[data-route="routines"]');
  const REQUIRED = ['personal-routines','routine-history','custom','add-exercise','predefined-routines','predefined-exercises'];
  const OPEN_STATE_KEY='vitalpeak:routines-open-sections';
  let timer=null;

  function isRoutinesActive(){
    return !!ROUTINES_BUTTON()?.classList.contains('active');
  }

  function hasModernView(app=APP()){
    if(!app) return false;
    const accordion=app.querySelector('#vp-routines-accordion');
    return !!accordion && REQUIRED.every(key=>accordion.querySelector(`.vp-routine-section[data-vp-section="${key}"]`));
  }

  function closeAll(app=APP()){
    try { sessionStorage.removeItem(OPEN_STATE_KEY); } catch {}
    app?.querySelectorAll('#vp-routines-accordion .vp-routine-section[open]').forEach(section=>{ section.open=false; });
  }

  function cleanDuplicates(app){
    const accordions=[...app.querySelectorAll('#vp-routines-accordion')];
    const canonical=accordions[0];
    accordions.slice(1).forEach(node=>node.remove());
    if(!canonical) return;
    [...app.querySelectorAll('.vp-routine-section')].forEach(section=>{
      if(!canonical.contains(section)) section.remove();
    });
  }

  function wakeMount(){
    const app=APP();
    if(!app || !isRoutinesActive() || hasModernView(app)) return;
    const marker=document.createElement('span');
    marker.hidden=true;
    marker.dataset.vpRoutineWake='1';
    app.appendChild(marker);
    marker.remove();
  }

  function evaluate(){
    const app=APP();
    if(!app) return;
    app.classList.remove('vp-routines-preparing');

    if(!isRoutinesActive()){
      app.classList.remove('vp-routines-ready');
      return;
    }

    cleanDuplicates(app);
    const ready=hasModernView(app);
    app.classList.toggle('vp-routines-ready',ready);
    if(ready) return;

    wakeMount();
    document.dispatchEvent(new CustomEvent('vitalpeak:routines-needs-mount'));
  }

  function schedule(delay=20){
    clearTimeout(timer);
    timer=setTimeout(evaluate,delay);
  }

  const start=()=>{
    const app=APP();
    if(!app) return setTimeout(start,30);

    new MutationObserver(()=>schedule()).observe(app,{childList:true,subtree:false});
    const tabbar=document.querySelector('.tabbar');
    if(tabbar) new MutationObserver(()=>schedule(0)).observe(tabbar,{subtree:true,attributes:true,attributeFilter:['class']});

    document.addEventListener('click',e=>{
      const target=e.target.closest('.tabbar [data-route]');
      if(!target) return;
      if(target.dataset.route==='routines'){
        closeAll();
        setTimeout(()=>schedule(0),0);
        setTimeout(()=>schedule(0),80);
        setTimeout(()=>schedule(0),220);
      }
    },true);

    evaluate();
  };
  start();
})();
