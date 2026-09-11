(() => {
  'use strict';

  function fixLogo(){
    const active=document.querySelector('.tabbar button[data-route="progress"].active');
    if(!active) return;
    const img=document.querySelector('.vp-progress-hero .app-brand img');
    if(!img) return;
    const target='./apple-touch-icon.png';
    if(img.getAttribute('src')!==target) img.setAttribute('src',target);
    img.setAttribute('alt','VitalPeak');
  }

  let timer=null;
  const schedule=()=>{
    clearTimeout(timer);
    timer=setTimeout(fixLogo,20);
  };

  const start=()=>{
    const app=document.querySelector('#app');
    if(!app) return setTimeout(start,30);
    new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
    const tabbar=document.querySelector('.tabbar');
    if(tabbar) new MutationObserver(schedule).observe(tabbar,{subtree:true,attributes:true,attributeFilter:['class']});
    fixLogo();
  };
  start();
})();
