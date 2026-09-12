(() => {
  'use strict';

  const STYLE_ID='vp-routines-transition-guard-style';
  const APP=()=>document.getElementById('app');
  let releaseTimer=null, rafId=null, token=0;

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
  }

  function release(){
    stopWatch();
    APP()?.classList.remove('vp-routines-transition');
  }

  function ready(){
    const app=APP();
    if(!app) return false;
    const active=document.querySelector('.tabbar [data-route="routines"].active');
    if(!active) return false;
    const accordion=app.querySelector('#vp-routines-accordion');
    const redesigned=app.classList.contains('vp-routines-page');
    const summaries=accordion?[...accordion.querySelectorAll('.vp-routine-section > summary')]:[];
    const polished=summaries.length>=4 && summaries.every(x=>x.dataset.vpPolished==='1' || x.querySelector('.vp-section-title'));
    return !!(redesigned && accordion && polished);
  }

  function begin(){
    styles();
    token+=1;
    const myToken=token;
    stopWatch();
    const app=APP();
    if(!app) return;
    app.classList.add('vp-routines-transition');

    const check=()=>{
      if(myToken!==token) return;
      const active=document.querySelector('.tabbar [data-route="routines"].active');
      if(!active){release();return;}
      if(ready()){release();return;}
      rafId=requestAnimationFrame(check);
    };
    rafId=requestAnimationFrame(check);

    // Fail-open: aunque falle una capa de Rutinas, nunca puede quedar oculta.
    releaseTimer=setTimeout(()=>{ if(myToken===token) release(); },700);
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
    if(tab.dataset.route==='routines' && !APP()?.classList.contains('vp-routines-page')) begin();
    else if(tab.dataset.route!=='routines'){ token+=1; release(); }
  },true);

  const tabs=document.querySelector('.tabbar');
  if(tabs){
    new MutationObserver(()=>{
      const active=document.querySelector('.tabbar [data-route="routines"].active');
      if(active && !ready()) begin();
      else if(!active) release();
    }).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  }
})();
