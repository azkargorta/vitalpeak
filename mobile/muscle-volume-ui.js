(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile',STORE='state',STYLE_ID='vp-muscle-volume-styles';
  let timer=null,rendering=false;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(v,d=1)=>Number(v||0).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-muscle-card{margin:0 0 13px;padding:16px;border:1px solid #dfece8;border-radius:20px;background:#fff;box-shadow:0 8px 22px rgba(16,46,56,.05)}
      .vp-muscle-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}.vp-muscle-head h2{margin:0;color:#123843;font-size:18px}.vp-muscle-head p{margin:3px 0 0;color:#71868b;font-size:11px;line-height:1.45}.vp-muscle-note{padding:7px 9px;border-radius:10px;background:#f3f8f7;color:#6d8287;font-size:9px;line-height:1.35}
      .vp-muscle-list{display:grid;gap:8px;margin-top:12px}.vp-muscle-row{padding:12px;border:1px solid #e1ece9;border-radius:14px;background:#fbfefd}.vp-muscle-row-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.vp-muscle-row h3{margin:0;color:#153d46;font-size:13px}.vp-muscle-row p{margin:4px 0 0;color:#70858a;font-size:10px;line-height:1.35}.vp-muscle-chip{flex:none;padding:5px 7px;border-radius:999px;font-size:9px;font-weight:900}.vp-muscle-chip.stable,.vp-muscle-chip.insufficient{background:#eef3f4;color:#64787d}.vp-muscle-chip.rising{background:#e0f7ef;color:#117964}.vp-muscle-chip.falling,.vp-muscle-chip.low{background:#fff0d3;color:#87631a}.vp-muscle-chip.high{background:#ffe8e4;color:#9b5047}
      .vp-muscle-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:9px}.vp-muscle-metric{padding:8px;border-radius:10px;background:#f4faf8}.vp-muscle-metric span{display:block;color:#778b90;font-size:8px;font-weight:800;text-transform:uppercase}.vp-muscle-metric b{display:block;margin-top:3px;color:#183f47;font-size:13px}.vp-muscle-bar{height:7px;margin-top:9px;border-radius:99px;background:#edf3f1;overflow:hidden}.vp-muscle-bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#66d2bf,#149d85)}
      .vp-muscle-week-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin-top:12px}.vp-muscle-week{padding:9px;border-radius:12px;background:#f6faf9;border:1px solid #e6efec;text-align:center}.vp-muscle-week span{display:block;color:#7a8d91;font-size:8px;text-transform:uppercase;font-weight:800}.vp-muscle-week b{display:block;margin-top:3px;color:#173e46;font-size:14px}
      @media(max-width:620px){.vp-muscle-metrics{grid-template-columns:1fr 1fr 1fr}.vp-muscle-head{display:block}.vp-muscle-note{margin-top:8px}.vp-muscle-week-grid{grid-template-columns:1fr 1fr}}
    `;document.head.appendChild(s)
  }
  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  function stateKey(state){const sessions=state.sessions||[],last=sessions.at(-1),sets=last?.sets||[];return `${sessions.length}|${last?.date||''}|${sets.length}|${sets.at(-1)?.at||''}`}
  function rowHtml(x,max){const width=max?Math.min(100,Math.max(4,x.direct/max*100)):4;const change=x.changePct==null?'—':`${x.changePct>0?'+':''}${fmt(x.changePct,0)} %`;return `<article class="vp-muscle-row"><div class="vp-muscle-row-top"><div><h3>${esc(x.name)}</h3><p>${esc(x.reason)}</p></div><span class="vp-muscle-chip ${esc(x.status)}">${esc(x.label)}</span></div><div class="vp-muscle-metrics"><div class="vp-muscle-metric"><span>Series directas</span><b>${fmt(x.direct,0)}</b></div><div class="vp-muscle-metric"><span>Series implicadas</span><b>${fmt(x.involved,1)}</b></div><div class="vp-muscle-metric"><span>Vs. media</span><b>${esc(change)}</b></div></div><div class="vp-muscle-bar"><i style="width:${width}%"></i></div></article>`}
  async function enhance(){
    if(rendering)return;
    injectStyles();const page=document.querySelector('.vp-progress-page');if(!page||!document.querySelector('.tabbar button[data-route="progress"].active'))return;
    const engine=window.VitalPeakMuscleVolume;if(!engine)return;
    rendering=true;
    try{
      const state=await readState().catch(()=>null);if(!state)return;
      const key=stateKey(state),existing=page.querySelector('.vp-muscle-card');
      if(existing?.dataset.vpStateKey===key)return;
      const a=engine.analyze(state,{weeks:6});const recentWeeks=a.weeks.slice(-4);const max=Math.max(1,...a.muscles.map(x=>x.direct));const visible=a.muscles.filter(x=>x.direct>0||x.baseline>0).slice(0,10);
      const card=existing||document.createElement('section');card.className='vp-muscle-card';card.dataset.vpStateKey=key;card.innerHTML=`<div class="vp-muscle-head"><div><h2>Volumen por grupo muscular</h2><p>Compara tus series semanales con tu propia media reciente.</p></div><div class="vp-muscle-note">Principal = 1 serie directa · secundario = 0,5 serie implicada. Es una estimación de carga de trabajo, no de recuperación.</div></div><div class="vp-muscle-week-grid">${recentWeeks.map(w=>`<div class="vp-muscle-week"><span>Semana ${esc(w.start.slice(5))}</span><b>${Object.values(w.muscles||{}).reduce((n,m)=>n+Number(m.direct||0),0)} series</b></div>`).join('')}</div>${visible.length?`<div class="vp-muscle-list">${visible.map(x=>rowHtml(x,max)).join('')}</div>`:`<div class="vp-empty-small">Aún no hay suficientes entrenamientos registrados para calcular volumen muscular.</div>`}`;
      if(!existing){const intel=page.querySelector('.vp-intel-card');if(intel)intel.insertAdjacentElement('afterend',card);else{const summary=page.querySelector('.vp-progress-summary');if(summary)summary.insertAdjacentElement('beforebegin',card);else page.prepend(card)}}
    } finally {rendering=false}
  }
  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,140)}
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(schedule).observe(tabs,{attributes:true,subtree:true,attributeFilter:['class']});schedule();
})();