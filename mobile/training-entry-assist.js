(() => {
  'use strict';

  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  const STYLE_ID = 'vp-training-entry-assist-styles';
  let lastDraftSnapshot = null;
  let lastCompletionKey = sessionStorage.getItem('vitalpeak:last-summary-key') || '';
  let enhanceTimer = null;

  const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function injectStyles(){
    if(document.getElementById(STYLE_ID)) return;
    const s=document.createElement('style');
    s.id=STYLE_ID;
    s.textContent=`
      .vp-exercise-context{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0 4px}
      .vp-exercise-context-card{padding:11px 12px;border:1px solid #dce9e6;border-radius:13px;background:linear-gradient(145deg,#fbfffe,#f2f8f6)}
      .vp-exercise-context-card span{display:block;color:#74878c;font-size:10px;font-weight:850;letter-spacing:.06em;text-transform:uppercase}
      .vp-exercise-context-card b{display:block;margin-top:4px;color:#163c45;font-size:14px;line-height:1.25}
      .vp-prefill-note{margin:5px 0 0;color:#72868a;font-size:10px;line-height:1.35}
      .vp-summary-backdrop{position:fixed;inset:0;z-index:1000;display:flex;align-items:flex-end;justify-content:center;background:rgba(5,22,28,.72);backdrop-filter:blur(8px);padding:14px}
      .vp-summary-card{width:min(620px,100%);max-height:88vh;overflow:auto;border-radius:25px 25px 20px 20px;background:#f8fcfb;color:#173a42;box-shadow:0 28px 80px rgba(0,0,0,.3)}
      .vp-summary-hero{padding:22px 20px;background:linear-gradient(140deg,#123b46,#17675f 65%,#1b8b78);color:#fff;border-radius:25px 25px 0 0}
      .vp-summary-hero .template-meta{color:#91ebda}.vp-summary-hero h2{margin:5px 0 4px;color:#fff;font-size:26px}.vp-summary-hero p{margin:0;color:#d8eeea;font-size:13px}
      .vp-summary-body{padding:16px}.vp-summary-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px}
      .vp-summary-stat{padding:12px 8px;border:1px solid #dce9e6;border-radius:14px;background:#fff;text-align:center}.vp-summary-stat b{display:block;font-size:19px;color:#153e46}.vp-summary-stat span{display:block;margin-top:4px;font-size:10px;color:#71858a;text-transform:uppercase;font-weight:800}
      .vp-summary-prs{display:grid;gap:7px;margin:12px 0}.vp-summary-pr{padding:11px 12px;border-radius:12px;background:#e8f8f3;color:#176d60;font-size:12px;font-weight:800}
      .vp-summary-exercises{display:grid;gap:7px;margin-top:10px}.vp-summary-exercise{display:flex;justify-content:space-between;gap:12px;padding:10px 11px;border-radius:12px;background:#fff;border:1px solid #e0ebe8;font-size:12px}.vp-summary-exercise b{font-size:12px}.vp-summary-exercise span{color:#708489;white-space:nowrap}
      .vp-summary-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 16px 16px}.vp-summary-actions button{min-height:48px;border-radius:14px;font-weight:900}.vp-summary-close{border:1px solid #cfe0dc;background:#fff;color:#21464d}.vp-summary-progress{border:0;background:#4fd3c1;color:#12383a}
      @media(max-width:420px){.vp-exercise-context{grid-template-columns:1fr}.vp-summary-stats{grid-template-columns:repeat(3,1fr)}.vp-summary-actions{grid-template-columns:1fr}}
    `;
    document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}

  function currentExerciseName(){
    const form=document.getElementById('set-form');
    if(!form) return '';
    const card=form.closest('.card');
    return card?.querySelector('.row.between h2')?.textContent?.trim() || card?.querySelector('h2')?.textContent?.trim() || '';
  }

  function historicalSets(state,name){
    const rows=[];
    for(const session of state.sessions||[]) for(const set of session.sets||[]) if(String(set.exercise)===String(name)) rows.push({...set,date:session.date});
    rows.sort((a,b)=>String(b.at||b.date||'').localeCompare(String(a.at||a.date||'')));
    return rows;
  }

  function currentDraftSets(state,name){
    return (state._draft?.sets||[]).filter(s=>String(s.exercise)===String(name));
  }

  function formatSet(set){
    if(!set) return 'Sin registros';
    return `${Number(set.weight||0)} kg × ${Number(set.reps||0)}`;
  }

  async function enhanceForm(){
    injectStyles();
    const form=document.getElementById('set-form');
    if(!form || form.dataset.vpAssist==='1') return;
    const name=currentExerciseName();
    if(!name) return;
    const state=await readState().catch(()=>null); if(!state) return;
    if(state._draft) lastDraftSnapshot=JSON.parse(JSON.stringify(state._draft));
    const history=historicalSets(state,name), draftSets=currentDraftSets(state,name);
    const latest=draftSets.at(-1)||history[0]||null;
    const best=[...history,...draftSets].sort((a,b)=>Number(b.weight||0)-Number(a.weight||0)||Number(b.reps||0)-Number(a.reps||0))[0]||null;
    const weight=form.elements.weight, reps=form.elements.reps;
    if(latest){
      if(weight && !String(weight.value||'').trim()) weight.value=Number(latest.weight||0);
      if(reps && !String(reps.value||'').trim()) reps.value=Number(latest.reps||0);
    }
    const context=document.createElement('div');
    context.className='vp-exercise-context';
    context.innerHTML=`<div class="vp-exercise-context-card"><span>Última referencia</span><b>${esc(formatSet(latest))}</b></div><div class="vp-exercise-context-card"><span>Mejor marca</span><b>${esc(formatSet(best))}</b></div>`;
    form.insertAdjacentElement('beforebegin',context);
    if(latest){const note=document.createElement('p');note.className='vp-prefill-note';note.textContent='He rellenado peso y repeticiones con tu última referencia. Puedes cambiarlos antes de guardar.';form.insertAdjacentElement('afterend',note)}
    form.dataset.vpAssist='1';
  }

  function sessionKey(session){
    const last=(session?.sets||[]).at(-1);
    return `${session?.date||''}|${session?.routineId||session?.routineName||''}|${last?.at||''}|${(session?.sets||[]).length}`;
  }

  function previousBestByExercise(state,currentSession){
    const map=new Map();
    for(const session of state.sessions||[]){
      if(session===currentSession) continue;
      for(const set of session.sets||[]){
        const key=String(set.exercise||''); if(!key) continue;
        const prev=map.get(key)||{weight:-Infinity,reps:-Infinity};
        const w=Number(set.weight||0), r=Number(set.reps||0);
        if(w>prev.weight || (w===prev.weight && r>prev.reps)) map.set(key,{weight:w,reps:r});
      }
    }
    return map;
  }

  function computePrs(state,session){
    const before=previousBestByExercise(state,session), prs=[];
    const grouped=new Map();
    for(const set of session.sets||[]){
      const key=String(set.exercise||''); if(!key) continue;
      const cur=grouped.get(key)||{weight:-Infinity,reps:-Infinity};
      const w=Number(set.weight||0), r=Number(set.reps||0);
      if(w>cur.weight || (w===cur.weight && r>cur.reps)) grouped.set(key,{weight:w,reps:r});
    }
    for(const [name,best] of grouped){
      const old=before.get(name);
      if(!old || best.weight>old.weight || (best.weight===old.weight && best.reps>old.reps)) prs.push({name,...best,first:!old});
    }
    return prs;
  }

  function durationLabel(session){
    const times=(session.sets||[]).map(s=>Date.parse(s.at)).filter(Number.isFinite).sort((a,b)=>a-b);
    if(times.length<2) return '—';
    const min=Math.max(1,Math.round((times.at(-1)-times[0])/60000));
    return `${min} min`;
  }

  function showSummary(state,session){
    if(document.querySelector('.vp-summary-backdrop')) return;
    injectStyles();
    const sets=session.sets||[], names=[...new Set(sets.map(s=>s.exercise).filter(Boolean))], prs=computePrs(state,session);
    const volume=sets.reduce((sum,s)=>sum+(Number(s.weight||0)*Number(s.reps||0)),0);
    const exerciseRows=names.map(name=>{const xs=sets.filter(s=>s.exercise===name),best=[...xs].sort((a,b)=>Number(b.weight||0)-Number(a.weight||0)||Number(b.reps||0)-Number(a.reps||0))[0];return `<div class="vp-summary-exercise"><b>${esc(name)}</b><span>${xs.length} series · ${esc(formatSet(best))}</span></div>`}).join('');
    const o=document.createElement('div');o.className='vp-summary-backdrop';o.innerHTML=`<div class="vp-summary-card" role="dialog" aria-modal="true" aria-label="Resumen del entrenamiento"><div class="vp-summary-hero"><span class="template-meta">ENTRENAMIENTO COMPLETADO</span><h2>${esc(session.routineName||'Sesión terminada')}</h2><p>Buen trabajo. Tu sesión ya está guardada en el historial.</p></div><div class="vp-summary-body"><div class="vp-summary-stats"><div class="vp-summary-stat"><b>${sets.length}</b><span>Series</span></div><div class="vp-summary-stat"><b>${names.length}</b><span>Ejercicios</span></div><div class="vp-summary-stat"><b>${esc(durationLabel(session))}</b><span>Duración</span></div></div>${prs.length?`<span class="template-meta">NUEVAS MARCAS</span><div class="vp-summary-prs">${prs.map(p=>`<div class="vp-summary-pr">🏆 ${esc(p.name)} · ${p.weight} kg × ${p.reps}${p.first?' · primera referencia':''}</div>`).join('')}</div>`:''}<span class="template-meta">RESUMEN</span><div class="vp-summary-exercises">${exerciseRows}</div>${volume>0?`<p class="muted small" style="margin:12px 2px 0">Volumen registrado aproximado: ${Math.round(volume).toLocaleString('es-ES')} kg</p>`:''}</div><div class="vp-summary-actions"><button type="button" class="vp-summary-close">Cerrar</button><button type="button" class="vp-summary-progress">Ver progreso</button></div></div>`;document.body.appendChild(o);
    const close=()=>o.remove();o.querySelector('.vp-summary-close').onclick=close;o.addEventListener('click',e=>{if(e.target===o)close()});o.querySelector('.vp-summary-progress').onclick=()=>{close();document.querySelector('[data-route="progress"]')?.click()};
  }

  async function detectCompletion(){
    const state=await readState().catch(()=>null); if(!state) return;
    if(state._draft){lastDraftSnapshot=JSON.parse(JSON.stringify(state._draft));return}
    if(!lastDraftSnapshot?.sets?.length) return;
    const sessions=state.sessions||[], latest=sessions.at(-1); if(!latest?.sets?.length) return;
    const key=sessionKey(latest); if(!key || key===lastCompletionKey) return;
    const draftLast=lastDraftSnapshot.sets.at(-1)?.at;
    const latestLast=latest.sets.at(-1)?.at;
    if(draftLast && latestLast && String(draftLast)!==String(latestLast)) return;
    lastCompletionKey=key;sessionStorage.setItem('vitalpeak:last-summary-key',key);lastDraftSnapshot=null;showSummary(state,latest);
  }

  function scheduleEnhance(){clearTimeout(enhanceTimer);enhanceTimer=setTimeout(()=>{enhanceForm();detectCompletion()},70)}
  const app=document.getElementById('app');if(app)new MutationObserver(scheduleEnhance).observe(app,{childList:true,subtree:true});
  document.addEventListener('submit',e=>{if(e.target?.id==='set-form')setTimeout(scheduleEnhance,180)},true);
  scheduleEnhance();
})();
