(() => {
  'use strict';

  const STYLE_ID='vp-routines-transition-guard-style';
  const APP=()=>document.getElementById('app');
  let releaseTimer=null, retryTimer=null, rafId=null, token=0;

  function styles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');
    s.id=STYLE_ID;
    s.textContent=`
      #app.vp-routines-transition{visibility:hidden!important;pointer-events:none!important}
    `;
    document.head.appendChild(s);
  }

  function stopWatch(){
    if(rafId){cancelAnimationFrame(rafId);rafId=null;}
    if(releaseTimer){clearTimeout(releaseTimer);releaseTimer=null;}
    if(retryTimer){clearInterval(retryTimer);retryTimer=null;}
  }

  function release(){
    stopWatch();
    APP()?.classList.remove('vp-routines-transition');
  }

  function isActive(){
    return !!document.querySelector('.tabbar [data-route="routines"].active');
  }

  function ready(){
    const app=APP();
    if(!app || !isActive()) return false;
    const accordion=app.querySelector('#vp-routines-accordion');
    const redesigned=app.classList.contains('vp-routines-page');
    const summaries=accordion?[...accordion.querySelectorAll('.vp-routine-section > summary')]:[];
    const polished=summaries.length>=4 && summaries.every(x=>x.dataset.vpPolished==='1' || x.querySelector('.vp-section-title'));
    return !!(redesigned && accordion && polished);
  }

  function wakeRoutinesEnhancers(){
    const app=APP();
    if(!app || !isActive() || ready()) return;

    // Si seguimos viendo el render base antiguo, provocamos un único cambio de hijo
    // para despertar los observers de accordion/redesign sin tocar el contenido real.
    if(!app.querySelector('#vp-routines-accordion') && /Planes preparados|Catálogo de ejercicios/.test(app.textContent||'')){
      const marker=document.createElement('i');
      marker.hidden=true;
      marker.dataset.vpRoutinesWake='1';
      app.appendChild(marker);
      marker.remove();
    }
  }

  function begin(){
    styles();
    token+=1;
    const myToken=token;
    stopWatch();
    const app=APP();
    if(!app) return;
    app.classList.add('vp-routines-transition');

    wakeRoutinesEnhancers();
    retryTimer=setInterval(()=>{
      if(myToken!==token || !isActive()){release();return;}
      if(ready()){release();return;}
      wakeRoutinesEnhancers();
    },90);

    const check=()=>{
      if(myToken!==token) return;
      if(!isActive()){release();return;}
      if(ready()){release();return;}
      rafId=requestAnimationFrame(check);
    };
    rafId=requestAnimationFrame(check);

    // Tiempo suficiente para que carguen las capas auxiliares, pero nunca puede
    // bloquear indefinidamente la pantalla si hay un fallo real.
    releaseTimer=setTimeout(()=>{ if(myToken===token) release(); },2200);
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
