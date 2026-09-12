(() => {
  'use strict';

  const DB='vitalpeak-mobile', STORE='state', STYLE='vp-coach-intelligence-style';
  let timer=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=s=>String(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();

  function styles(){
    if(document.getElementById(STYLE))return;
    const s=document.createElement('style');s.id=STYLE;s.textContent=`
      .vp-coach-intel{margin:10px 0 0;padding:14px;border:1px solid #d8e9e5;border-radius:18px;background:linear-gradient(145deg,#fbfffe,#f2faf8);box-shadow:0 7px 18px rgba(16,46,56,.045)}
      .vp-coach-intel-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:10px}.vp-coach-intel-head h3{margin:2px 0 2px;color:#123a43;font-size:16px}.vp-coach-intel-head p{margin:0;color:#70858a;font-size:11px;line-height:1.4}.vp-coach-intel-badge{flex:none;padding:6px 9px;border-radius:999px;background:#e5f7f2;color:#117965;font-size:9px;font-weight:900;text-transform:uppercase}
      .vp-coach-intel-grid{display:grid;gap:7px}.vp-coach-rec{padding:11px 12px;border:1px solid #e0ebe8;border-radius:13px;background:#fff}.vp-coach-rec-top{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}.vp-coach-rec b{color:#173e46;font-size:12px}.vp-coach-rec p{margin:4px 0 0;color:#71858a;font-size:10.5px;line-height:1.4}.vp-coach-rec span{flex:none;padding:4px 7px;border-radius:999px;background:#eef5f3;color:#60787d;font-size:8px;font-weight:900;text-transform:uppercase}.vp-coach-rec.good span{background:#e1f7f0;color:#117964}.vp-coach-rec.warn span{background:#fff1d6;color:#85631d}.vp-coach-rec.action span{background:#e5f0ff;color:#35678c}
      .vp-coach-intel-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.vp-coach-intel-actions button{min-height:40px;padding:0 12px;border-radius:11px;font-size:10px;font-weight:900}.vp-coach-apply{border:0;background:#16a98e;color:#fff}.vp-coach-open-progress{border:1px solid #d0e2de;background:#fff;color:#254b52}.vp-coach-empty{padding:10px;border-radius:12px;background:#fff;color:#71858a;font-size:11px;line-height:1.45}
      .vp-coach-priority-note{margin:8px 0 0;padding:9px 10px;border-radius:11px;background:#eaf8f4;color:#176f60;font-size:10px;font-weight:800}
      @media(max-width:500px){.vp-coach-intel-head{display:block}.vp-coach-intel-badge{display:inline-block;margin-top:7px}.vp-coach-intel-actions{display:grid}.vp-coach-intel-actions button{width:100%}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((res,rej)=>{const r=indexedDB.open(DB,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
  async function readState(){const db=await openDb();return new Promise((res,rej)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>res(q.result||{});q.onerror=()=>rej(q.error)})}

  function activeRoutine(state){return (state.routines||[]).find(r=>String(r.id)===String(state.activeRoutineId))||(state.routines||[])[0]||null}
  function routineItems(r){if(!r)return[];const days=Array.isArray(r.days)?r.days:[];return days.flatMap(d=>d.items||[]).length?days.flatMap(d=>d.items||[]):(r.exercises||[])}
  function uniqueItems(items){const m=new Map();for(const x of items){const name=x.exercise||x.name;if(name&&!m.has(name))m.set(name,x)}return [...m.values()]}

  function priorityAlias(muscle){
    const n=norm(muscle);
    if(/pectoral|pecho/.test(n))return 'Pecho';
    if(/dorsal|espalda|trapecio/.test(n))return 'Espalda';
    if(/cuadriceps/.test(n))return 'Cuádriceps';
    if(/isquio|femoral/.test(n))return 'Isquios';
    if(/glute/.test(n))return 'Glúteos';
    if(/deltoide lateral/.test(n))return 'Deltoide lateral';
    if(/deltoide posterior/.test(n))return 'Deltoide posterior';
    if(/biceps/.test(n))return 'Bíceps';
    if(/triceps/.test(n))return 'Tríceps';
    if(/gemelo|pantorrilla|soleo/.test(n))return 'Gemelos';
    if(/core|abdom|oblicuo/.test(n))return 'Core';
    return null;
  }

  function buildModel(state){
    const progress=window.VITALPEAK_PROGRESS_ENGINE?.analyze?.(state)||null;
    const volume=window.VitalPeakMuscleVolume?.analyze?.(state,{weeks:6})||null;
    const progression=window.VITALPEAK_PROGRESSION_ENGINE;
    const routine=activeRoutine(state), items=uniqueItems(routineItems(routine));
    const loadRecs=[];
    if(progression){
      for(const item of items){
        const name=item.exercise||item.name;if(!name)continue;
        const rec=progression.recommendation(state,name,{sets:item.sets,reps:item.reps});
        if(rec.status!=='insufficient')loadRecs.push({name,...rec});
      }
    }
    loadRecs.sort((a,b)=>({increase:0,review:1,hold:2}[a.status]??9)-({increase:0,review:1,hold:2}[b.status]??9));
    const muscleAlerts=(volume?.alerts||[]).filter(x=>['low','falling'].includes(x.status));
    const priorities=[...new Set(muscleAlerts.map(x=>priorityAlias(x.name)).filter(Boolean))].slice(0,3);
    const insights=[];
    for(const x of (progress?.exercises||[]).filter(x=>x.status==='plateau').slice(0,2))insights.push({type:'warn',tag:'Revisar',title:x.name,text:x.reason});
    for(const x of loadRecs.filter(x=>x.status==='increase').slice(0,2))insights.push({type:'good',tag:'Progresión',title:x.name,text:`${x.action}. ${x.reason}`});
    for(const x of muscleAlerts.slice(0,2))insights.push({type:'action',tag:'Volumen',title:x.name,text:x.reason});
    if(!insights.length){for(const x of (progress?.exercises||[]).filter(x=>x.status==='progressing').slice(0,2))insights.push({type:'good',tag:'Mejora',title:x.name,text:x.reason})}
    return {progress,volume,loadRecs,priorities,insights:insights.slice(0,4),routine};
  }

  function cardHtml(model){
    const p=model.progress;
    const enough=(p?.usableCount||0)>0 || model.loadRecs.length || model.priorities.length;
    if(!enough)return `<div class="vp-coach-empty">Todavía necesito más entrenamientos registrados para personalizar el Coach. Sigue guardando series y sesiones; cuando haya suficiente historial aparecerán aquí recomendaciones basadas en tus propios datos.</div>`;
    const status=p?.label||'Analizando';
    const summary=p?.summary||'He analizado tu historial reciente para personalizar las recomendaciones.';
    const rows=model.insights.map(x=>`<article class="vp-coach-rec ${x.type}"><div class="vp-coach-rec-top"><b>${esc(x.title)}</b><span>${esc(x.tag)}</span></div><p>${esc(x.text)}</p></article>`).join('');
    const priorityNote=model.priorities.length?`<div class="vp-coach-priority-note">Prioridades sugeridas para un nuevo plan: ${model.priorities.map(esc).join(' · ')}</div>`:'';
    return `<div class="vp-coach-intel-head"><div><h3>Coach basado en tus datos</h3><p>${esc(summary)}</p></div><span class="vp-coach-intel-badge">${esc(status)}</span></div>${rows?`<div class="vp-coach-intel-grid">${rows}</div>`:''}${priorityNote}<div class="vp-coach-intel-actions">${model.priorities.length?'<button type="button" class="vp-coach-apply" data-vp-coach-apply>Aplicar prioridades al plan</button>':''}<button type="button" class="vp-coach-open-progress" data-vp-coach-progress>Ver análisis completo</button></div>`;
  }

  async function enhance(){
    styles();const root=document.querySelector('#vp-smart-generator');if(!root)return;
    let card=root.querySelector('.vp-coach-intel');if(!card){card=document.createElement('section');card.className='vp-coach-intel';const teaser=root.querySelector('.vp-smart-teaser');teaser?.insertAdjacentElement('afterend',card)}
    const state=await readState().catch(()=>null);if(!state)return;const model=buildModel(state);card.__vpModel=model;card.innerHTML=cardHtml(model);
  }
  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,100)}

  document.addEventListener('click',e=>{
    const apply=e.target.closest('[data-vp-coach-apply]');if(apply){e.preventDefault();const card=apply.closest('.vp-coach-intel'),model=card?.__vpModel;if(!model)return;document.querySelector('[data-vp-smart-open]')?.click();setTimeout(()=>{const form=document.querySelector('#vp-smart-form');if(!form)return;form.querySelectorAll('input[name="priority"]').forEach(i=>{i.checked=model.priorities.includes(i.value)});let note=form.querySelector('.vp-coach-applied-note');if(!note){note=document.createElement('div');note.className='vp-coach-priority-note vp-coach-applied-note';form.querySelector('.vp-priority')?.insertAdjacentElement('afterend',note)}if(note)note.textContent=`VitalPeak ha marcado como prioridad: ${model.priorities.join(', ')}. Puedes cambiarlo antes de generar el plan.`;form.scrollIntoView({behavior:'smooth',block:'start'})},120);return}
    if(e.target.closest('[data-vp-coach-progress]')){e.preventDefault();document.querySelector('[data-route="progress"]')?.click()}
  },true);

  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
  schedule();
})();
