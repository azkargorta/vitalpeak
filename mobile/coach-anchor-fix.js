(() => {
  'use strict';

  const STYLE_ID = 'vp-coach-anchor-fix-style';

  function addStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const style=document.createElement('style');
    style.id=STYLE_ID;
    style.textContent=`
      #vp-smart-generator.vp-routines-coach{margin:0 0 14px!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;color:inherit!important;overflow:visible!important}
      #vp-smart-generator.vp-routines-coach .vp-smart-teaser{margin:0!important;padding:19px!important;border-radius:22px!important;border:1px solid rgba(60,232,207,.28)!important;background:radial-gradient(circle at 86% 18%,rgba(73,224,199,.13),transparent 34%),linear-gradient(135deg,#0d4b4f 0%,#145d5c 55%,#176c68 100%)!important;box-shadow:0 13px 30px rgba(15,73,76,.16)!important;color:#fff!important}
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

  function fix(){
    addStyles();
    const app=document.querySelector('#app');
    const hero=app?.querySelector('.hero');
    const generator=document.querySelector('#vp-smart-generator');
    const teaser=document.querySelector('.vp-smart-teaser');
    if(!app||!hero||!generator||!teaser) return false;

    // Mantener toda la funcionalidad de Coach dentro de un único componente.
    if(teaser.parentElement!==generator){
      generator.insertBefore(teaser,generator.firstChild);
    }

    // El rediseño usa .vp-routines-coach como ancla. La clase debe vivir en
    // el contenedor, nunca en la tarjeta interior, para que no se separe el botón.
    document.querySelectorAll('.vp-routines-coach').forEach(el=>{
      if(el!==generator) el.classList.remove('vp-routines-coach');
    });
    generator.classList.add('vp-routines-coach');

    if(hero.nextElementSibling!==generator){
      hero.insertAdjacentElement('afterend',generator);
    }

    // Si algún render anterior dejó una copia sintética de Coach, eliminarla.
    [...app.querySelectorAll('.vp-routines-coach')].forEach(el=>{
      if(el!==generator) el.remove();
    });
    return true;
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries+=1;
    fix();
    if(tries>=20) clearInterval(timer);
  },100);
  fix();
})();
