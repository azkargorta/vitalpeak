(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state', STYLE_ID='vp-training-completion-history-styles';
  let timer=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function injectStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-completed-badge{display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border-radius:999px;background:#dcf7ef;color:#117964;font-size:10px;font-weight:900;letter-spacing:.04em;text-transform:uppercase}
      .vp-completed-badge:before{content:'✓';display:grid;place-items:center;width:17px;height:17px;border-radius:50%;background:#19a987;color:#fff;font-size:11px}
      .calendar-entry.vp-completed{background:#def8ef!important;border-color:#6fd2b9!important;color:#116b5c!important;padding-right:8px!important}
      .calendar-entry.vp-completed:before{content:'✓';font-weight:900;margin-right:4px;color:#149477}
      .month-day.vp-has-completed{box-shadow:inset 0 0 0 2px rgba(25,169,135,.16)}
      .vp-today-completed{margin:10px 0 0;padding:12px 13px;border:1px solid #cdebe2;border-radius:14px;background:linear-gradient(145deg,#f3fffb,#e7f8f2);color:#174c46}
      .vp-today-completed b{display:block;margin-top:5px;font-size:14px}.vp-today-completed span{font-size:11px;color:#5f7e78}
      .vp-history-card[data-vp-session-index]{cursor:pointer!important;opacity:1!important}
      .vp-history-card[data-vp-session-index]:after{content:'Ver detalle';grid-column:1;display:block;margin-top:3px;color:#168b78;font-size:10px;font-weight:900}
      .vp-session-detail-backdrop{position:fixed;inset:0;z-index:1100;display:flex;align-items:flex-end;justify-content:center;background:rgba(5,22,28,.74);backdrop-filter:blur(8px);padding:12px}
      .vp-session-detail{width:min(680px,100%);max-height:90vh;overflow:auto;border-radius:25px 25px 20px 20px;background:#f8fcfb;color:#173b42;box-shadow:0 28px 80px rgba(0,0,0,.3)}
      .vp-session-detail-head{position:sticky;top:0;z-index:2;padding:20px;background:linear-gradient(140deg,#123b46,#17675f 65%,#1b8b78);color:#fff;border-radius:25px 25px 0 0}
      .vp-session-detail-head .template-meta{color:#91ebda}.vp-session-detail-head h2{margin:5px 40px 4px 0;color:#fff;font-size:24px}.vp-session-detail-head p{margin:0;color:#d8eeea;font-size:12px}.vp-session-detail-close{position:absolute;right:14px;top:14px;width:40px;height:40px;border:0;border-radius:50%;background:rgba(255,255,255,.14);color:#fff;font-size:25px}
      .vp-session-detail-body{padding:15px}.vp-session-detail-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px}.vp-session-detail-stat{padding:11px 8px;border:1px solid #dce9e6;border-radius:13px;background:#fff;text-align:center}.vp-session-detail-stat b{display:block;font-size:18px}.vp-session-detail-stat span{display:block;margin-top:3px;color:#74878c;font-size:9px;font-weight:850;text-transform:uppercase}
      .vp-session-exercise{margin:9px 0;padding:13px;border:1px solid #dce9e6;border-radius:14px;background:#fff}.vp-session-exercise h3{margin:0 0 9px;font-size:14px}.vp-session-set{display:grid;grid-template-columns:auto 1fr auto;gap:8px;align-items:center;padding:7px 0;border-top:1px solid #edf3f1;font-size:12px}.vp-session-set:first-of-type{border-top:0}.vp-session-set i{font-style:normal;color:#7b8f93}.vp-session-set strong{font-size:12px}.vp-session-set small{color:#75898d;text-align:right}.vp-session-note{grid-column:2/4;color:#71858a;font-size:10px}
      @media(max-width:420px){.vp-session-detail-stats{grid-template-columns:repeat(3,1fr)}.vp-session-detail{max-height:92vh}.vp-session-set{grid-template-columns:auto 1fr}}
    `;document.head.appendChild(s);
  }
  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  const today=()=>new Date().toISOString().slice(0,10);
  function duration(session){const ts=(session.sets||[]).map(s=>Date.parse(s.at)).filter(Number.isFinite).sort((a,b)=>a-b);if(ts.length<2)return '—';return `${Math.max(1,Math.round((ts.at(-1)-ts[0])/60000))} min`}
  function volume(session){return Math.round((session.sets||[]).reduce((a,s)=>a+Number(s.weight||0)*Number(s.reps||0),0))}
  function completedFor(state,date,key){return (state.sessions||[]).filter(s=>String(s.date)===String(date) && (!key || String(s.routineKey||'')===String(key)))}

  function enhanceCalendar(state){
    const cal=document.querySelector('.month-calendar');if(!cal)return;
    cal.querySelectorAll('.month-day').forEach(day=>{
      const select=day.querySelector('[data-plan-add-date]');if(!select)return;const date=select.dataset.planAddDate;const planned=Array.isArray(state.plan?.[date])?state.plan[date]:(state.plan?.[date]?[state.plan[date]]:[]);const entries=[...day.querySelectorAll('.calendar-entry')];
      let any=false;entries.forEach((el,i)=>{const key=planned[i];const done=key?completedFor(state,date,key).length>0:false;el.classList.toggle('vp-completed',done);if(done){any=true;el.title='Entrenamiento completado'}});day.classList.toggle('vp-has-completed',any);
    });
  }

  function enhanceToday(state){
    const app=document.getElementById('app');if(!app || document.querySelector('.month-calendar') || document.getElementById('set-form'))return;
    app.querySelectorAll('.vp-today-completed').forEach(x=>x.remove());
    const done=(state.sessions||[]).filter(s=>String(s.date)===today());if(!done.length)return;
    const head=[...app.querySelectorAll('.section-head h2')].find(h=>h.textContent.trim()==='Entrenamiento de hoy')?.closest('.section-head');const card=head?.nextElementSibling;if(!card)return;
    const box=document.createElement('div');box.className='vp-today-completed';box.innerHTML=`<span class="vp-completed-badge">Completado hoy</span><b>${done.length} entrenamiento${done.length===1?'':'s'} terminado${done.length===1?'':'s'}</b><span>${done.reduce((n,s)=>n+(s.sets||[]).length,0)} series registradas en total</span>`;card.appendChild(box);
    const start=card.querySelector('[data-route="train"]');if(start && done.some(s=>String(s.routineKey||'')===String((state.plan?.[today()]||[])[Number(state.todaySessionIndex||0)]||''))){start.textContent='Entrenamiento completado';start.classList.remove('primary');start.classList.add('secondary')}
  }

  function enhanceHistory(state){
    const wrap=document.querySelector('.vp-routine-history');if(!wrap)return;
    const recent=(state.sessions||[]).slice().reverse().slice(0,12), cards=[...wrap.querySelectorAll('.vp-history-card')];
    cards.forEach((card,i)=>{const session=recent[i];if(!session)return;card.dataset.vpSessionIndex=String((state.sessions||[]).indexOf(session));card.removeAttribute('data-action');card.removeAttribute('data-id');card.removeAttribute('disabled');const info=card.querySelector('span');if(info)info.textContent=`${(session.sets||[]).length} serie${(session.sets||[]).length===1?'':'s'} · pulsa para ver el entrenamiento realizado`});
  }

  function showSession(state,index){
    const s=(state.sessions||[])[Number(index)];if(!s)return;document.querySelector('.vp-session-detail-backdrop')?.remove();injectStyles();
    const names=[...new Set((s.sets||[]).map(x=>x.exercise).filter(Boolean))];const rows=names.map(name=>{const sets=(s.sets||[]).filter(x=>x.exercise===name);return `<section class="vp-session-exercise"><h3>${esc(name)}</h3>${sets.map((x,i)=>`<div class="vp-session-set"><i>Serie ${i+1}</i><strong>${Number(x.weight||0)} kg × ${Number(x.reps||0)}</strong><small>${x.at?new Intl.DateTimeFormat('es-ES',{hour:'2-digit',minute:'2-digit'}).format(new Date(x.at)):''}</small>${x.notes?`<div class="vp-session-note">${esc(x.notes)}</div>`:''}</div>`).join('')}</section>`}).join('');
    let date=s.date||'';try{date=new Intl.DateTimeFormat('es-ES',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date(`${s.date}T12:00:00`))}catch{}
    const o=document.createElement('div');o.className='vp-session-detail-backdrop';o.innerHTML=`<article class="vp-session-detail" role="dialog" aria-modal="true"><header class="vp-session-detail-head"><span class="template-meta">SESIÓN REALIZADA</span><h2>${esc(s.routineName||'Entrenamiento')}</h2><p>${esc(date)}</p><button class="vp-session-detail-close" aria-label="Cerrar">×</button></header><div class="vp-session-detail-body"><div class="vp-session-detail-stats"><div class="vp-session-detail-stat"><b>${(s.sets||[]).length}</b><span>Series</span></div><div class="vp-session-detail-stat"><b>${names.length}</b><span>Ejercicios</span></div><div class="vp-session-detail-stat"><b>${esc(duration(s))}</b><span>Duración</span></div></div>${rows}${volume(s)>0?`<p class="muted small">Volumen total aproximado: ${volume(s).toLocaleString('es-ES')} kg</p>`:''}</div></article>`;document.body.appendChild(o);const close=()=>o.remove();o.querySelector('.vp-session-detail-close').onclick=close;o.addEventListener('click',e=>{if(e.target===o)close()});
  }

  async function enhance(){injectStyles();const state=await readState().catch(()=>null);if(!state)return;enhanceCalendar(state);enhanceToday(state);enhanceHistory(state)}
  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,80)}
  document.addEventListener('click',e=>{const card=e.target.closest('.vp-history-card[data-vp-session-index]');if(card){e.preventDefault();e.stopPropagation();readState().then(state=>showSession(state,card.dataset.vpSessionIndex)).catch(()=>{})}},true);
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
  document.addEventListener('submit',e=>{if(e.target?.id==='set-form')setTimeout(schedule,220)},true);
  schedule();
})();
