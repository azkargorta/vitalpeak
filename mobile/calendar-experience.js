(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state', STYLE_ID='vp-calendar-experience-styles';
  let timer=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const today=()=>new Date().toISOString().slice(0,10);

  function injectStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-calendar-week{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:7px;margin:12px 0 16px}
      .vp-calendar-week-day{min-width:0;padding:10px 5px;border:1px solid #dfe9e6;border-radius:14px;background:#fff;text-align:center;color:#294b52;box-shadow:0 4px 12px rgba(16,46,56,.035)}
      .vp-calendar-week-day b{display:block;font-size:15px;line-height:1.1}.vp-calendar-week-day span{display:block;margin-top:4px;font-size:9px;font-weight:850;color:#778b90;text-transform:uppercase}.vp-calendar-week-day i{display:block;width:7px;height:7px;margin:7px auto 0;border-radius:50%;background:#cbd8d5}
      .vp-calendar-week-day.vp-today{border-color:#6db7f0;background:#f3f9ff}.vp-calendar-week-day.vp-completed i{background:#19a987}.vp-calendar-week-day.vp-pending i{background:#e8a928}.vp-calendar-week-day.vp-omitted i{background:#d46a6a}.vp-calendar-week-day.vp-free i{background:#cbd8d5}
      .vp-calendar-legend{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 12px}.vp-calendar-legend span{display:inline-flex;align-items:center;gap:5px;padding:5px 8px;border-radius:99px;background:#f4f7f6;color:#61767b;font-size:9px;font-weight:850}.vp-calendar-legend i{width:7px;height:7px;border-radius:50%}.vp-calendar-legend .done i{background:#19a987}.vp-calendar-legend .pending i{background:#e8a928}.vp-calendar-legend .omitted i{background:#d46a6a}
      .month-day[data-vp-date]{cursor:pointer;transition:transform .12s ease,box-shadow .12s ease}.month-day[data-vp-date]:active{transform:scale(.985)}
      .month-day.vp-calendar-pending{box-shadow:inset 0 0 0 2px rgba(232,169,40,.14)}.month-day.vp-calendar-omitted{box-shadow:inset 0 0 0 2px rgba(212,106,106,.14)}
      .calendar-entry.vp-pending-entry{background:#fff7dc!important;border-color:#eac86b!important;color:#80621a!important}.calendar-entry.vp-omitted-entry{background:#fff0ef!important;border-color:#e1a09c!important;color:#914f4b!important;opacity:.88}
      .vp-day-backdrop{position:fixed;inset:0;z-index:1200;display:flex;align-items:flex-end;justify-content:center;padding:12px;background:rgba(5,22,28,.74);backdrop-filter:blur(8px)}
      .vp-day-sheet{width:min(650px,100%);max-height:90vh;overflow:auto;border-radius:25px 25px 20px 20px;background:#f8fcfb;color:#173a42;box-shadow:0 28px 80px rgba(0,0,0,.3)}
      .vp-day-head{position:sticky;top:0;z-index:2;padding:19px 52px 18px 19px;background:linear-gradient(140deg,#123b46,#17675f 65%,#1b8b78);color:#fff;border-radius:25px 25px 0 0}.vp-day-head .template-meta{color:#91ebda}.vp-day-head h2{margin:5px 0 3px;color:#fff;font-size:24px}.vp-day-head p{margin:0;color:#d8eeea;font-size:12px}.vp-day-close{position:absolute;right:13px;top:13px;width:40px;height:40px;border:0;border-radius:50%;background:rgba(255,255,255,.14);color:#fff;font-size:25px}
      .vp-day-body{display:grid;gap:10px;padding:14px}.vp-day-empty{padding:18px;border:1px dashed #cfded9;border-radius:14px;background:#fff;text-align:center;color:#71858a;font-size:13px}
      .vp-day-training{padding:14px;border:1px solid #dce8e5;border-radius:16px;background:#fff;box-shadow:0 5px 15px rgba(16,46,56,.04)}.vp-day-training-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.vp-day-training h3{margin:3px 0 4px;font-size:15px}.vp-day-training p{margin:0;color:#71858a;font-size:11px}.vp-day-status{flex:none;padding:5px 8px;border-radius:99px;font-size:9px;font-weight:900;text-transform:uppercase}.vp-day-status.done{background:#dcf7ef;color:#117964}.vp-day-status.pending{background:#fff3cb;color:#80621a}.vp-day-status.omitted{background:#ffe6e3;color:#914f4b}
      .vp-day-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:11px}.vp-day-actions button,.vp-day-actions label{min-height:42px;border-radius:11px;font-size:11px;font-weight:850}.vp-day-actions button{border:1px solid #d4e3df;background:#f8fbfa;color:#234b52}.vp-day-actions label{display:flex;align-items:center;gap:6px;padding:5px 8px;border:1px solid #d4e3df;background:#f8fbfa;color:#526b71}.vp-day-actions input{min-width:0;width:100%;border:0;background:transparent;color:#183d44;font:inherit}
      .vp-calendar-session{margin-top:10px;padding-top:10px;border-top:1px solid #edf3f1}.vp-calendar-session-row{display:flex;justify-content:space-between;gap:12px;padding:4px 0;font-size:11px;color:#63797e}.vp-calendar-session-row b{color:#183f47}
      @media(max-width:430px){.vp-calendar-week{gap:4px}.vp-calendar-week-day{padding:9px 2px;border-radius:11px}.vp-calendar-week-day b{font-size:13px}.vp-calendar-week-day span{font-size:8px}.vp-day-actions{grid-template-columns:1fr}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.objectStore(STORE).put(state,'user')})}
  const entries=(state,date)=>{const x=state.plan?.[date];return Array.isArray(x)?x:(x?[x]:[])};
  const completed=(state,date,key)=>(state.sessions||[]).filter(s=>String(s.date)===String(date)&&String(s.routineKey||'')===String(key));
  function statusFor(state,date,key){if(completed(state,date,key).length)return 'done';return date<today()?'omitted':'pending'}
  function routineLabel(state,key){const [id,day]=String(key).split('::'),r=(state.routines||[]).find(x=>String(x.id)===String(id));return {routine:r,name:r?.days?.[Number(day)]?.name||r?.name||'Entrenamiento',routineName:r?.name||'Rutina',day:Number(day||0)}}
  function dateLabel(date,full=false){try{return new Intl.DateTimeFormat('es-ES',full?{weekday:'long',day:'numeric',month:'long',year:'numeric'}:{weekday:'short',day:'numeric'}).format(new Date(`${date}T12:00:00`))}catch{return date}}
  function iso(d){return new Date(d).toISOString().slice(0,10)}
  function monday(date=today()){const d=new Date(`${date}T12:00:00`);d.setDate(d.getDate()-((d.getDay()+6)%7));return d}

  function addWeekStrip(state,cal){
    const old=document.querySelector('.vp-calendar-week-wrap');old?.remove();
    const start=monday(),days=Array.from({length:7},(_,i)=>{const d=new Date(start);d.setDate(start.getDate()+i);return iso(d)});
    const wrap=document.createElement('div');wrap.className='vp-calendar-week-wrap';
    wrap.innerHTML=`<div class="vp-calendar-legend"><span class="done"><i></i>Completado</span><span class="pending"><i></i>Pendiente</span><span class="omitted"><i></i>Omitido</span></div><div class="vp-calendar-week">${days.map(date=>{const es=entries(state,date);const statuses=es.map(k=>statusFor(state,date,k));let cls='vp-free';if(statuses.includes('pending'))cls='vp-pending';if(statuses.length&&statuses.every(x=>x==='done'))cls='vp-completed';if(statuses.length&&statuses.every(x=>x==='omitted'))cls='vp-omitted';return `<button type="button" class="vp-calendar-week-day ${cls} ${date===today()?'vp-today':''}" data-vp-open-day="${date}"><span>${esc(new Intl.DateTimeFormat('es-ES',{weekday:'short'}).format(new Date(`${date}T12:00:00`)).replace('.',''))}</span><b>${Number(date.slice(-2))}</b><i></i></button>`}).join('')}</div>`;
    const controls=document.querySelector('.month-controls');(controls||cal).insertAdjacentElement('beforebegin',wrap);
  }

  function enhanceMonth(state,cal){
    cal.querySelectorAll('.month-day').forEach(day=>{
      const select=day.querySelector('[data-plan-add-date]');if(!select)return;const date=select.dataset.planAddDate;day.dataset.vpDate=date;
      const es=entries(state,date),els=[...day.querySelectorAll('.calendar-entry')];let hasPending=false,hasOmitted=false;
      els.forEach((el,i)=>{el.classList.remove('vp-pending-entry','vp-omitted-entry');const key=es[i];if(!key)return;const st=statusFor(state,date,key);if(st==='pending'){el.classList.add('vp-pending-entry');hasPending=true}if(st==='omitted'){el.classList.add('vp-omitted-entry');hasOmitted=true}});
      day.classList.toggle('vp-calendar-pending',hasPending);day.classList.toggle('vp-calendar-omitted',!hasPending&&hasOmitted);
    });
  }

  function sessionSummary(session){
    if(!session)return '';
    const sets=session.sets||[],names=[...new Set(sets.map(s=>s.exercise).filter(Boolean))],volume=Math.round(sets.reduce((a,s)=>a+Number(s.weight||0)*Number(s.reps||0),0));
    return `<div class="vp-calendar-session"><div class="vp-calendar-session-row"><span>Ejercicios</span><b>${names.length}</b></div><div class="vp-calendar-session-row"><span>Series</span><b>${sets.length}</b></div>${volume?`<div class="vp-calendar-session-row"><span>Volumen aprox.</span><b>${volume.toLocaleString('es-ES')} kg</b></div>`:''}</div>`;
  }

  function openDay(state,date){
    document.querySelector('.vp-day-backdrop')?.remove();
    const es=entries(state,date),rows=es.map((key,index)=>{const info=routineLabel(state,key),st=statusFor(state,date,key),session=completed(state,date,key).at(-1);const statusText=st==='done'?'Completado':st==='omitted'?'Omitido':'Pendiente';return `<article class="vp-day-training"><div class="vp-day-training-top"><div><span class="template-meta">${esc(info.routineName)}</span><h3>${esc(info.name)}</h3><p>${session?`${(session.sets||[]).length} series registradas`:'Entrenamiento planificado'}</p></div><span class="vp-day-status ${st}">${statusText}</span></div>${sessionSummary(session)}<div class="vp-day-actions">${session?`<button type="button" data-vp-calendar-session="${esc(key)}" data-date="${date}">Ver sesión</button>`:''}<label>Mover a<input type="date" value="${date}" data-vp-move-entry="${index}" data-from-date="${date}"></label></div></article>`}).join('');
    const o=document.createElement('div');o.className='vp-day-backdrop';o.innerHTML=`<section class="vp-day-sheet" role="dialog" aria-modal="true"><header class="vp-day-head"><span class="template-meta">PLAN DEL DÍA</span><h2>${esc(dateLabel(date,true))}</h2><p>${es.length?`${es.length} entrenamiento${es.length===1?'':'s'} asignado${es.length===1?'':'s'}`:'Sin entrenamientos asignados'}</p><button class="vp-day-close" type="button" aria-label="Cerrar">×</button></header><div class="vp-day-body">${rows||'<div class="vp-day-empty">Este día está libre. Puedes añadir un entrenamiento desde el selector del calendario.</div>'}</div></section>`;document.body.appendChild(o);const close=()=>o.remove();o.querySelector('.vp-day-close').onclick=close;o.addEventListener('click',e=>{if(e.target===o)close()});
  }

  function showSession(state,date,key){
    const s=completed(state,date,key).at(-1);if(!s)return;const current=document.querySelector('.vp-day-backdrop');current?.remove();
    const names=[...new Set((s.sets||[]).map(x=>x.exercise).filter(Boolean))];const rows=names.map(name=>{const xs=(s.sets||[]).filter(x=>x.exercise===name);return `<article class="vp-day-training"><h3>${esc(name)}</h3>${xs.map((x,i)=>`<div class="vp-calendar-session-row"><span>Serie ${i+1}</span><b>${Number(x.weight||0)} kg × ${Number(x.reps||0)}</b></div>`).join('')}</article>`}).join('');
    const o=document.createElement('div');o.className='vp-day-backdrop';o.innerHTML=`<section class="vp-day-sheet"><header class="vp-day-head"><span class="template-meta">SESIÓN COMPLETADA</span><h2>${esc(s.routineName||'Entrenamiento')}</h2><p>${esc(dateLabel(date,true))}</p><button class="vp-day-close" type="button">×</button></header><div class="vp-day-body">${rows}</div></section>`;document.body.appendChild(o);const close=()=>o.remove();o.querySelector('.vp-day-close').onclick=close;o.addEventListener('click',e=>{if(e.target===o)close()});
  }

  async function moveEntry(state,from,index,to){
    if(!to||to===from)return;state.plan=state.plan||{};const old=entries(state,from),key=old[index];if(!key)return;old.splice(index,1);if(old.length)state.plan[from]=old;else delete state.plan[from];const dest=entries(state,to);if(!dest.includes(key))dest.push(key);state.plan[to]=dest;await writeState(state);sessionStorage.setItem('vitalpeak:return-to-planner','1');location.reload();
  }

  async function enhance(){injectStyles();const cal=document.querySelector('.month-calendar');if(!cal)return;const state=await readState().catch(()=>null);if(!state)return;addWeekStrip(state,cal);enhanceMonth(state,cal)}
  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,90)}

  document.addEventListener('click',e=>{
    const open=e.target.closest('[data-vp-open-day]');if(open){e.preventDefault();readState().then(s=>openDay(s,open.dataset.vpOpenDay)).catch(()=>{});return}
    const day=e.target.closest('.month-day[data-vp-date]');if(day&&!e.target.closest('button,select,input,label')){e.preventDefault();readState().then(s=>openDay(s,day.dataset.vpDate)).catch(()=>{});return}
    const view=e.target.closest('[data-vp-calendar-session]');if(view){e.preventDefault();readState().then(s=>showSession(s,view.dataset.date,view.dataset.vpCalendarSession)).catch(()=>{})}
  },true);
  document.addEventListener('change',e=>{const input=e.target.closest('[data-vp-move-entry]');if(!input)return;readState().then(s=>moveEntry(s,input.dataset.fromDate,Number(input.dataset.vpMoveEntry),input.value)).catch(()=>{})},true);

  if(sessionStorage.getItem('vitalpeak:return-to-planner')==='1'){sessionStorage.removeItem('vitalpeak:return-to-planner');let n=0;const t=setInterval(()=>{const b=document.querySelector('[data-route="planner"]');if(b){clearInterval(t);b.click()}else if(++n>80)clearInterval(t)},50)}
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});schedule();
})();
