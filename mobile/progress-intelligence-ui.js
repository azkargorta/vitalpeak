(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state', STYLE_ID='vp-progress-intelligence-styles';
  let timer=null, rendering=false;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
  const fmt=(v,d=1)=>Number(v||0).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-intel-card{margin:0 0 13px;padding:16px;border:1px solid #dfece8;border-radius:20px;background:linear-gradient(145deg,#fbfffe,#f3faf8);box-shadow:0 8px 22px rgba(16,46,56,.05)}
      .vp-intel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}.vp-intel-head h2{margin:0;color:#123843;font-size:18px}.vp-intel-head p{margin:3px 0 0;color:#71868b;font-size:11px;line-height:1.4}
      .vp-intel-status{flex:none;padding:7px 10px;border-radius:999px;font-size:10px;font-weight:900;text-transform:uppercase}.vp-intel-status.progressing{background:#dcf7ef;color:#117964}.vp-intel-status.stable{background:#edf4f5;color:#526d73}.vp-intel-status.plateau{background:#fff0d3;color:#87631a}.vp-intel-status.insufficient{background:#f0f3f4;color:#738388}
      .vp-intel-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:12px}.vp-intel-metric{padding:11px;border-radius:14px;background:#fff;border:1px solid #e1ece9}.vp-intel-metric span{display:block;color:#74888d;font-size:9px;font-weight:800;text-transform:uppercase}.vp-intel-metric b{display:block;margin-top:4px;color:#153d46;font-size:17px}
      .vp-intel-insights{display:grid;gap:8px}.vp-intel-insight{padding:12px;border-radius:14px;background:#fff;border:1px solid #e1ece9}.vp-intel-insight-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.vp-intel-insight h3{margin:0;color:#163d45;font-size:13px}.vp-intel-insight p{margin:5px 0 0;color:#6e8489;font-size:11px;line-height:1.4}.vp-intel-chip{flex:none;padding:5px 7px;border-radius:999px;font-size:9px;font-weight:900}.vp-intel-chip.progressing{background:#e1f7f0;color:#117964}.vp-intel-chip.stable{background:#eef3f4;color:#64787d}.vp-intel-chip.plateau{background:#fff0d3;color:#87631a}
      .vp-intel-detail{display:flex;gap:10px;flex-wrap:wrap;margin-top:7px;color:#6f858a;font-size:10px}.vp-intel-detail b{color:#193f47}
      @media(max-width:620px){.vp-intel-metrics{grid-template-columns:1fr 1fr}.vp-intel-metric:last-child{grid-column:1/-1}.vp-intel-head{align-items:flex-start}.vp-intel-status{font-size:9px}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  function stateKey(state){const sessions=state.sessions||[],last=sessions.at(-1),sets=last?.sets||[];return `${sessions.length}|${last?.date||''}|${sets.length}|${sets.at(-1)?.at||''}|${Object.keys(state.plan||{}).length}`}

  function insightHtml(x){
    const delta=x.deltaPct==null?'Sin comparativa':`${x.deltaPct>0?'+':''}${fmt(x.deltaPct,1)} %`;
    const e1=x.recentE1rm?`${fmt(x.recentE1rm,1)} kg e1RM`:'e1RM insuficiente';
    return `<article class="vp-intel-insight"><div class="vp-intel-insight-top"><div><h3>${esc(x.name)}</h3><p>${esc(x.reason)}</p></div><span class="vp-intel-chip ${esc(x.status)}">${esc(x.label)}</span></div><div class="vp-intel-detail"><span><b>${esc(delta)}</b> vs bloque anterior</span><span><b>${esc(e1)}</b> reciente</span><span>${x.exposures} sesiones</span></div></article>`;
  }

  async function enhance(){
    if(rendering)return;
    injectStyles();
    const page=document.querySelector('.vp-progress-page');
    if(!page||!document.querySelector('.tabbar button[data-route="progress"].active'))return;
    const engine=window.VITALPEAK_PROGRESS_ENGINE;if(!engine)return;
    rendering=true;
    try{
      const state=await readState().catch(()=>null);if(!state)return;
      const key=stateKey(state),existing=page.querySelector('.vp-intel-card');
      if(existing?.dataset.vpStateKey===key)return;
      const a=engine.analyze(state);
      const card=existing||document.createElement('section');card.className='vp-intel-card';card.dataset.vpStateKey=key;
      const adherence=a.adherence.pct==null?'—':`${a.adherence.pct} %`;
      const progressCount=a.exercises.filter(x=>x.status==='progressing').length;
      const plateauCount=a.exercises.filter(x=>x.status==='plateau').length;
      card.innerHTML=`<div class="vp-intel-head"><div><h2>Estado de progreso</h2><p>${esc(a.summary)}</p></div><span class="vp-intel-status ${esc(a.status)}">${esc(a.label)}</span></div><div class="vp-intel-metrics"><div class="vp-intel-metric"><span>Ejercicios mejorando</span><b>${progressCount}</b></div><div class="vp-intel-metric"><span>Posibles estancamientos</span><b>${plateauCount}</b></div><div class="vp-intel-metric"><span>Adherencia 28 días</span><b>${esc(adherence)}</b></div></div>${a.insights.length?`<div class="vp-intel-insights">${a.insights.map(insightHtml).join('')}</div>`:`<div class="vp-intel-insight"><h3>Aún estamos aprendiendo de tus entrenamientos</h3><p>Necesitamos al menos 4 sesiones por ejercicio para detectar tendencias y 6 para señalar un posible estancamiento con prudencia.</p></div>`}`;
      if(!existing){const summary=page.querySelector('.vp-progress-summary');if(summary)summary.insertAdjacentElement('beforebegin',card);else page.prepend(card)}
    } finally {rendering=false}
  }

  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,120)}
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
  const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(schedule).observe(tabs,{attributes:true,subtree:true,attributeFilter:['class']});
  schedule();
})();