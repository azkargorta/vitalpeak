(() => {
  'use strict';

  const STYLE_ID = 'vp-routines-entry-controller-style';
  const LOADER_ID = 'vp-routines-entry-loader';
  let timer = null;
  let startedAt = 0;
  let attempt = 0;

  function isActive(){
    return !!document.querySelector('.tabbar [data-route="routines"].active');
  }

  function app(){ return document.getElementById('app'); }

  function ready(){
    const root = app();
    if(!root || !isActive()) return false;
    const accordion = root.querySelector('#vp-routines-accordion');
    const sections = accordion ? accordion.querySelectorAll('.vp-routine-section[data-vp-section]') : [];
    return root.classList.contains('vp-routines-page') &&
      !!root.querySelector('.vp-routines-active') &&
      !!accordion &&
      sections.length >= 6;
  }

  function ensureStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #${LOADER_ID}{position:fixed;inset:0 0 calc(78px + env(safe-area-inset-bottom)) 0;z-index:620;display:none;place-items:center;padding:24px;background:linear-gradient(180deg,#f5fbf9,#edf6f3)}
      #${LOADER_ID}.show{display:grid}
      #${LOADER_ID}>div{display:grid;justify-items:center;gap:11px;width:min(300px,86vw);padding:24px 20px;border:1px solid rgba(22,169,142,.14);border-radius:22px;background:#fff;box-shadow:0 12px 34px rgba(16,46,56,.08);text-align:center}
      #${LOADER_ID} i{width:32px;height:32px;border:3px solid #d9ebe6;border-top-color:#16a98e;border-radius:50%;animation:vp-entry-spin .75s linear infinite}
      #${LOADER_ID} b{font-size:17px;color:#153f49}#${LOADER_ID} span{font-size:12px;color:#73878c}
      @keyframes vp-entry-spin{to{transform:rotate(360deg)}}
    `;
    document.head.appendChild(style);
  }

  function loader(){
    ensureStyles();
    let el=document.getElementById(LOADER_ID);
    if(el) return el;
    el=document.createElement('div');
    el.id=LOADER_ID;
    el.setAttribute('role','status');
    el.innerHTML='<div><i aria-hidden="true"></i><b>Cargando rutinas…</b><span data-vp-entry-text>Preparando la vista actual.</span></div>';
    document.body.appendChild(el);
    return el;
  }

  function show(){ loader().classList.add('show'); }
  function hide(){ document.getElementById(LOADER_ID)?.classList.remove('show'); }

  function wakeMountObservers(){
    const root=app();
    if(!root) return;
    const marker=document.createElement('span');
    marker.hidden=true;
    marker.dataset.vpRoutineWake='1';
    root.appendChild(marker);
    marker.remove();
  }

  function stop(){
    clearTimeout(timer); timer=null; startedAt=0; attempt=0; hide();
  }

  function tick(){
    clearTimeout(timer);
    if(!isActive()){ stop(); return; }
    if(ready()){ stop(); return; }

    show();
    attempt += 1;
    wakeMountObservers();

    const elapsed = Date.now() - startedAt;
    const text=document.querySelector(`#${LOADER_ID} [data-vp-entry-text]`);
    if(text && elapsed > 1800) text.textContent='Terminando de montar tus rutinas…';

    // Las primeras pasadas son rápidas para respetar el orden de montaje
    // routine-enhancements -> accordion -> redesign. Después bajamos frecuencia.
    timer=setTimeout(tick, elapsed < 2200 ? 80 : 220);
  }

  function begin(){
    if(!isActive()) return;
    if(ready()){ hide(); return; }
    startedAt=Date.now(); attempt=0; show();
    clearTimeout(timer); timer=setTimeout(tick, 0);
  }

  // El router principal ya ha renderizado cuando llega este listener (se registra después).
  document.addEventListener('click',e=>{
    if(e.target.closest('.tabbar [data-route="routines"]')) setTimeout(begin,0);
    else if(e.target.closest('.tabbar [data-route]')) stop();
  });

  const tabs=document.querySelector('.tabbar');
  if(tabs){
    new MutationObserver(()=>{
      if(isActive()) begin(); else stop();
    }).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  }

  if(isActive()) begin();
})();
