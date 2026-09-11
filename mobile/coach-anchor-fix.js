(() => {
  'use strict';

  const STYLE_ID = 'vp-coach-anchor-fix-style';
  let timer = null;

  function addStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const style=document.createElement('style');
    style.id=STYLE_ID;
    style.textContent=`
      #vp-smart-generator.vp-routines-coach{margin:0 0 14px!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:inherit!important;overflow:visible!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-teaser{display:grid!important;grid-template-columns:auto 1fr!important;gap:14px!important;align-items:center!important;margin:0!important;padding:19px!important;border-radius:22px!important;border:1px solid rgba(60,232,207,.28)!important;background:radial-gradient(circle at 86% 18%,rgba(73,224,199,.13),transparent 34%),linear-gradient(135deg,#0d4b4f 0%,#145d5c 55%,#176c68 100%)!important;box-shadow:0 13px 30px rgba(15,73,76,.16)!important;color:#fff!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-teaser .vp-smart-open{grid-column:1/-1!important;width:100%!important;min-height:48px!important;margin-top:10px!important;border:0!important;border-radius:15px!important;background:linear-gradient(90deg,#40dbc6,#67e7d7)!important;color:#0b3438!important;font-weight:900!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-teaser .template-meta{color:#79f0dc!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-teaser h2{color:#fff!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-teaser p{color:#daf2ee!important;opacity:1!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-form-card,#vp-smart-generator.vp-routines-coach .vp-smart-form-card *{color:#163a43}
      #vp-smart-generator.vp-routines-coach .vp-smart-form-card .muted{color:#6b7d82!important}
      @media(max-width:620px){#vp-smart-generator.vp-routines-coach .vp-smart-teaser{padding:17px!important}}
    `;
    document.head.appendChild(style);
  }

  function canonicalTeaser(){
    return `<div class="vp-smart-icon">✦</div><div class="vp-smart-copy"><span class="template-meta">VITALPEAK COACH</span><h2>Pídele a VitalPeak tu plan personalizado</h2><p>Elige tu objetivo, nivel, días y tipo de entrenamiento. VitalPeak preparará la rutina por ti.</p></div><button class="primary vp-smart-open" type="button" data-vp-smart-open>Crear plan</button>`;
  }

  function fix(){
    addStyles();
    const app=document.querySelector('#app');
    const hero=app?.querySelector('.hero');
    const generator=app?.querySelector('#vp-smart-generator');
    if(!app||!hero||!generator) return false;

    let teaser=generator.querySelector(':scope > .vp-smart-teaser');
    if(!teaser){
      teaser=document.createElement('div');
      teaser.className='vp-smart-teaser';
      generator.insertBefore(teaser,generator.firstChild);
    }

    const hasCopy=!!teaser.querySelector('.vp-smart-copy');
    const hasButton=!!teaser.querySelector('[data-vp-smart-open]');
    const hasIcon=!!teaser.querySelector('.vp-smart-icon');
    if(!hasCopy||!hasButton||!hasIcon) teaser.innerHTML=canonicalTeaser();

    document.querySelectorAll('.vp-smart-teaser').forEach(el=>{
      if(el!==teaser && !generator.contains(el)) el.remove();
    });
    document.querySelectorAll('[data-vp-smart-open]').forEach(el=>{
      if(!generator.contains(el)) el.remove();
    });
    document.querySelectorAll('.vp-routines-coach').forEach(el=>{
      if(el!==generator) el.classList.remove('vp-routines-coach');
    });

    generator.classList.add('vp-routines-coach');
    if(hero.nextElementSibling!==generator) hero.insertAdjacentElement('afterend',generator);

    return true;
  }

  function schedule(){
    clearTimeout(timer);
    timer=setTimeout(fix,25);
  }

  const start=()=>{
    const app=document.querySelector('#app');
    if(!app) return setTimeout(start,30);
    new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
    fix();
  };
  start();
})();