(() => {
  'use strict';

  const APP=()=>document.querySelector('#app');
  const ROUTINES=()=>document.querySelector('.tabbar button[data-route="routines"]');
  let mounting=false;
  let timer=null;
  let wasActive=false;

  function active(){ return !!ROUTINES()?.classList.contains('active'); }

  function ensureStyles(){
    if(document.querySelector('#vp-routines-fallback-styles')) return;
    const style=document.createElement('style');
    style.id='vp-routines-fallback-styles';
    style.textContent=`
      #vp-routines-accordion{display:grid;gap:11px;margin:12px 0 24px}
      #vp-routines-accordion .vp-routine-section{border:1px solid rgba(35,96,96,.12);border-radius:19px;background:rgba(255,255,255,.94);overflow:hidden;box-shadow:0 8px 22px rgba(16,46,56,.055)}
      #vp-routines-accordion .vp-routine-section>summary{list-style:none;display:grid;grid-template-columns:42px 1fr 30px;align-items:center;gap:11px;min-height:66px;padding:12px 14px;cursor:pointer;font-size:15px;font-weight:900;color:#163a43;user-select:none}
      #vp-routines-accordion .vp-routine-section>summary::-webkit-details-marker{display:none}
      #vp-routines-accordion .vp-routine-section>summary::before{content:'•';display:grid;place-items:center;width:42px;height:42px;border-radius:14px;background:linear-gradient(145deg,#daf8f0,#edfdf9);color:#168b78;font-size:20px}
      #vp-routines-accordion .vp-routine-section[data-vp-section="routine-history"]>summary::before{content:'◷'}
      #vp-routines-accordion .vp-routine-section[data-vp-section="personal-routines"]>summary::before{content:'★'}
      #vp-routines-accordion .vp-routine-section[data-vp-section="custom"]>summary::before{content:'＋'}
      #vp-routines-accordion .vp-routine-section[data-vp-section="add-exercise"]>summary::before{content:'+'}
      #vp-routines-accordion .vp-routine-section[data-vp-section="predefined-routines"]>summary::before{content:'▤'}
      #vp-routines-accordion .vp-routine-section[data-vp-section="predefined-exercises"]>summary::before{content:'●'}
      #vp-routines-accordion .vp-routine-section>summary::after{content:'⌄';display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#edf7f4;color:#176d61;font-size:18px;transition:transform .18s ease}
      #vp-routines-accordion .vp-routine-section[open]>summary::after{transform:rotate(180deg)}
      #vp-routines-accordion .vp-routine-section[open]>summary{border-bottom:1px solid #e2ece9;background:linear-gradient(90deg,#fbfffe,#f1faf7)}
      #vp-routines-accordion .vp-routine-section-content{padding:14px;background:#fbfefd}
      #vp-routines-accordion .vp-routine-section-content>.section-head{display:none!important}
      #vp-routines-accordion .vp-routine-section-content>.filter-row{margin-top:0}
      #vp-routines-accordion .vp-routine-section-content>.exercise-grid{margin-top:0}
      #vp-routines-accordion .vp-fallback-empty{padding:13px;border-radius:12px;background:#f3f8f6;color:#6b8085;font-size:13px}
    `;
    document.head.appendChild(style);
  }

  function head(app,title){
    return [...app.querySelectorAll(':scope > .section-head')].find(node=>(node.querySelector('h2')?.textContent||'').trim()===title)||null;
  }

  function nodesUntilHead(start){
    const nodes=[];
    let node=start?.nextElementSibling||null;
    while(node && !node.classList?.contains('section-head')){
      nodes.push(node);
      node=node.nextElementSibling;
    }
    return nodes;
  }

  function details(title,key,nodes=[]){
    const el=document.createElement('details');
    el.className='vp-routine-section';
    el.dataset.vpSection=key;
    const summary=document.createElement('summary');
    summary.textContent=title;
    const body=document.createElement('div');
    body.className='vp-routine-section-content';
    nodes.filter(Boolean).forEach(node=>body.appendChild(node));
    el.append(summary,body);
    el.open=false;
    return el;
  }

  function readState(){
    return new Promise(resolve=>{
      try{
        const req=indexedDB.open('vitalpeak-mobile',2);
        req.onerror=()=>resolve({});
        req.onupgradeneeded=()=>{ if(!req.result.objectStoreNames.contains('state')) req.result.createObjectStore('state'); };
        req.onsuccess=()=>{
          try{
            const tx=req.result.transaction('state','readonly');
            const get=tx.objectStore('state').get('user');
            get.onsuccess=()=>resolve(get.result||{});
            get.onerror=()=>resolve({});
          }catch{ resolve({}); }
        };
      }catch{ resolve({}); }
    });
  }

  async function fillHistory(body){
    const state=await readState();
    if(!body.isConnected) return;
    const sessions=[...(state.sessions||[])].slice().reverse().slice(0,12);
    body.replaceChildren();
    if(!sessions.length){
      const empty=document.createElement('div');
      empty.className='vp-fallback-empty';
      empty.textContent='Todavía no hay rutinas completadas.';
      body.appendChild(empty);
      return;
    }
    sessions.forEach(session=>{
      const card=document.createElement('div');
      card.className='card';
      card.style.marginBottom='8px';
      const name=session.routineName||'Entrenamiento';
      const sets=Array.isArray(session.sets)?session.sets.length:0;
      card.innerHTML=`<b>${String(name).replace(/[&<>"']/g,'')}</b><p class="muted small">${session.date||''} · ${sets} series</p>`;
      body.appendChild(card);
    });
  }

  function moveSavedRoutines(app,body){
    const activeHead=head(app,'Tu rutina activa');
    const current=activeHead?.nextElementSibling;
    if(!current) return;
    [...current.querySelectorAll('[data-action="activate-routine"]')].forEach(button=>{
      const meta=(button.querySelector('.template-meta')?.textContent||'').trim();
      if(/PLAN GUARDADO/i.test(meta)) body.appendChild(button);
    });
    if(!body.children.length){
      const empty=document.createElement('div');
      empty.className='vp-fallback-empty';
      empty.textContent='No tienes otras rutinas personales guardadas.';
      body.appendChild(empty);
    }
  }

  function attachLateCustomExercises(app,accordion){
    const addBody=accordion.querySelector('[data-vp-section="add-exercise"] .vp-routine-section-content');
    if(!addBody) return;
    const custom=app.querySelector(':scope > .vp-custom-exercises');
    if(custom){
      addBody.replaceChildren(custom);
      return;
    }
    if(!addBody.children.length){
      const empty=document.createElement('div');
      empty.className='vp-fallback-empty';
      empty.textContent='El editor para añadir ejercicios se está preparando.';
      addBody.appendChild(empty);
    }
  }

  function mount(){
    if(mounting || !active()) return;
    const app=APP();
    if(!app) return;
    const existing=app.querySelector('#vp-routines-accordion');
    if(existing){
      existing.querySelectorAll('.vp-routine-section[open]').forEach(x=>x.open=false);
      return;
    }

    const prepared=head(app,'Planes preparados');
    const exercises=head(app,'Catálogo de ejercicios');
    const custom=head(app,'Rutina personalizada');
    if(!prepared || !exercises || !custom) return;

    mounting=true;
    try{
      ensureStyles();
      const preparedNodes=nodesUntilHead(prepared);
      const exerciseNodes=nodesUntilHead(exercises);
      const customNodes=nodesUntilHead(custom);

      const accordion=document.createElement('div');
      accordion.id='vp-routines-accordion';
      accordion.className='vp-routines-accordion';

      const history=details('Historial de rutinas','routine-history');
      const personal=details('Rutinas personales','personal-routines');
      const own=details('Crea tu propia rutina','custom',customNodes);
      const add=details('Añade tu ejercicio','add-exercise');
      const predefined=details('Rutinas predefinidas','predefined-routines',preparedNodes);
      const exerciseCatalog=details('Ejercicios predefinidos','predefined-exercises',exerciseNodes);

      moveSavedRoutines(app,personal.querySelector('.vp-routine-section-content'));
      accordion.append(history,personal,own,add,predefined,exerciseCatalog);
      prepared.before(accordion);
      prepared.remove();
      exercises.remove();
      custom.remove();
      attachLateCustomExercises(app,accordion);
      fillHistory(history.querySelector('.vp-routine-section-content'));

      accordion.querySelectorAll('.vp-routine-section').forEach(section=>{ section.open=false; });
      app.classList.add('vp-routines-ready');
      document.dispatchEvent(new CustomEvent('vitalpeak:routines-fallback-mounted'));
    }finally{
      mounting=false;
    }
  }

  function schedule(delay=35){
    clearTimeout(timer);
    timer=setTimeout(()=>{
      if(!active()) return;
      mount();
      const app=APP();
      const accordion=app?.querySelector('#vp-routines-accordion');
      if(accordion) attachLateCustomExercises(app,accordion);
    },delay);
  }

  function onEntry(){
    try{ sessionStorage.removeItem('vitalpeak:routines-open-sections'); }catch{}
    setTimeout(()=>schedule(0),0);
    setTimeout(()=>schedule(0),80);
    setTimeout(()=>schedule(0),220);
    setTimeout(()=>schedule(0),500);
  }

  const start=()=>{
    const app=APP();
    if(!app) return setTimeout(start,30);
    wasActive=active();
    if(wasActive) onEntry();

    new MutationObserver(()=>{
      const now=active();
      if(now && !wasActive) onEntry();
      wasActive=now;
      if(now) schedule();
    }).observe(app,{childList:true,subtree:false});

    const tabbar=document.querySelector('.tabbar');
    if(tabbar) new MutationObserver(()=>{
      const now=active();
      if(now && !wasActive) onEntry();
      wasActive=now;
      if(now) schedule(0);
    }).observe(tabbar,{subtree:true,attributes:true,attributeFilter:['class']});

    document.addEventListener('vitalpeak:routines-needs-mount',()=>schedule(0));
    document.addEventListener('vitalpeak:routines-fallback-mounted',()=>{
      APP()?.querySelectorAll('#vp-routines-accordion .vp-routine-section').forEach(x=>x.open=false);
    });
  };
  start();
})();
