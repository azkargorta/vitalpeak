(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state';
  const ROOT_ID='vp-share-progress-section';
  const MODAL_ID='vp-share-progress-modal';
  const STYLE_ID='vp-share-progress-style';
  const num=v=>Number(v||0);
  const today=()=>new Date().toISOString().slice(0,10);
  const htmlEsc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-share-card{margin-top:14px}.vp-share-card h3{margin:0 0 4px;color:#163b44}.vp-share-card p{margin:0 0 12px;color:#72888e;font-size:13px;line-height:1.45}
      .vp-share-progress-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;min-height:46px;border:0;border-radius:14px;background:linear-gradient(90deg,#0fa78c,#19b99e);color:#fff;font-weight:900;font-size:14px}.vp-share-progress-btn svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
      .vp-share-backdrop{position:fixed;inset:0;z-index:9999;background:rgba(7,31,38,.52);display:flex;align-items:flex-end;justify-content:center;padding:18px}.vp-share-dialog{width:min(760px,100%);max-height:88vh;overflow:auto;background:#f6fbfa;border-radius:24px 24px 18px 18px;padding:18px;box-shadow:0 24px 70px rgba(5,33,40,.3);box-sizing:border-box}
      .vp-share-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px}.vp-share-head h2{margin:0;color:#123943;font-size:22px}.vp-share-head p{margin:4px 0 0;color:#73888d;font-size:12px}.vp-share-close{width:38px;height:38px;flex:0 0 38px;border:0;border-radius:50%;background:#e8f2ef;color:#23464e;font-size:24px}
      .vp-share-range{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px;margin-bottom:16px}.vp-share-range label{min-width:0;font-size:11px;font-weight:800;color:#62797f}.vp-share-range input{display:block;box-sizing:border-box;min-width:0;width:100%;max-width:100%;margin-top:5px;border:1px solid #cfe2de;border-radius:12px;padding:9px 7px;background:#fff;color:#173b43;font-size:12px;font-weight:800;text-align:center}
      .vp-share-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:4px}.vp-share-summary div{min-width:0;padding:12px 10px;border-radius:13px;background:#fff;border:1px solid #e1ece9}.vp-share-summary b{display:block;color:#143b44;font-size:20px}.vp-share-summary span{display:block;margin-top:5px;color:#778c91;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .vp-share-note{margin:10px 2px 0;color:#7a8d92;font-size:11px;line-height:1.4}.vp-share-actions{display:grid;grid-template-columns:1fr;gap:8px;margin-top:14px}.vp-share-actions button{min-height:46px;border:0;border-radius:14px;font-weight:900}.vp-share-native{background:linear-gradient(90deg,#0fa78c,#19b99e);color:#fff}
      @media(max-width:620px){.vp-share-backdrop{padding:0;align-items:flex-end}.vp-share-dialog{border-radius:24px 24px 0 0;max-height:90vh;padding:18px 16px}.vp-share-range{gap:14px}.vp-share-range input{font-size:11px;padding:9px 4px}.vp-share-summary div{padding:11px 8px}.vp-share-summary b{font-size:19px}.vp-share-summary span{font-size:9px}}
    `;document.head.appendChild(s);
  }

  function isAccount(){return !!document.querySelector('.tabbar [data-route="account"].active') || /CUENTA/.test(document.querySelector('#app')?.textContent||'')}
  function earliestDate(state){const dates=[];(state.sessions||[]).forEach(s=>s.date&&dates.push(s.date));(state.weights||[]).forEach(w=>w.date&&dates.push(w.date));return dates.sort()[0]||today()}
  function inRange(date,from,to){return date && date>=from && date<=to}

  function buildData(state,from,to){
    const sessions=(state.sessions||[]).filter(s=>inRange(s.date,from,to)).slice().sort((a,b)=>String(a.date).localeCompare(String(b.date)));
    const setRows=[];
    sessions.forEach(s=>{const perExercise={};(s.sets||[]).forEach(set=>{const name=set.exercise||'Ejercicio';perExercise[name]=(perExercise[name]||0)+1;setRows.push({date:s.date,routine:s.routineName||'Entrenamiento',exercise:name,set:perExercise[name],weight:num(set.weight),reps:num(set.reps),notes:set.notes||''})})});
    const weights=(state.weights||[]).filter(w=>inRange(w.date,from,to)).slice().sort((a,b)=>String(a.date).localeCompare(String(b.date)));
    const byExercise=new Map();setRows.forEach(r=>{if(!byExercise.has(r.exercise))byExercise.set(r.exercise,[]);byExercise.get(r.exercise).push(r)});
    const progress=[...byExercise.entries()].map(([exercise,rows])=>{const dates=[...new Set(rows.map(r=>r.date))],firstDate=dates[0],lastDate=dates.at(-1),firstBest=Math.max(...rows.filter(r=>r.date===firstDate).map(r=>r.weight),0),lastBest=Math.max(...rows.filter(r=>r.date===lastDate).map(r=>r.weight),0);return {exercise,firstBest,lastBest,change:lastBest-firstBest,sessions:dates.length,sets:rows.length}}).sort((a,b)=>a.exercise.localeCompare(b.exercise,'es'));
    return {sessions,setRows,weights,progress};
  }

  function renderPreview(state,from,to){const data=buildData(state,from,to),root=document.querySelector('#vp-share-preview');if(!root)return;root.innerHTML=`<div class="vp-share-summary"><div><b>${data.sessions.length}</b><span>entrenamientos</span></div><div><b>${data.setRows.length}</b><span>series</span></div><div><b>${data.progress.length}</b><span>ejercicios</span></div></div><p class="vp-share-note">El archivo compartido incluirá tres tablas separadas: Entrenamiento, Progreso por ejercicio y Peso corporal.</p>`;return data}

  function makeHtmlReport(data,from,to){
    const trainingRows=data.setRows.length?data.setRows.map(r=>`<tr><td>${htmlEsc(r.date)}</td><td>${htmlEsc(r.routine)}</td><td>${htmlEsc(r.exercise)}</td><td>${r.set}</td><td>${r.weight}</td><td>${r.reps}</td><td>${htmlEsc(r.notes||'')}</td></tr>`).join(''):'<tr><td colspan="7" class="empty">Sin datos en este periodo.</td></tr>';
    const progressRows=data.progress.length?data.progress.map(r=>`<tr><td>${htmlEsc(r.exercise)}</td><td>${r.sessions}</td><td>${r.sets}</td><td>${r.firstBest}</td><td>${r.lastBest}</td><td>${r.change>0?'+':''}${r.change}</td></tr>`).join(''):'<tr><td colspan="6" class="empty">Sin datos en este periodo.</td></tr>';
    const firstWeight=data.weights[0]?.kg;
    const weightRows=data.weights.length?data.weights.map((w,i)=>`<tr><td>${htmlEsc(w.date)}</td><td>${w.kg}</td><td>${i===0?'0':`${num(w.kg)-num(firstWeight)>0?'+':''}${(num(w.kg)-num(firstWeight)).toFixed(1)}`}</td></tr>`).join(''):'<tr><td colspan="3" class="empty">Sin datos en este periodo.</td></tr>';
    return `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VitalPeak - Progreso</title><style>
      *{box-sizing:border-box}body{margin:0;padding:24px;background:#f4f9f8;color:#173b43;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}main{max-width:1200px;margin:0 auto}.report-head{margin-bottom:28px;padding:22px 24px;border-radius:20px;background:linear-gradient(135deg,#0c2330,#0d4d54);color:#fff}.report-head h1{margin:0 0 6px;font-size:28px}.report-head p{margin:0;color:#d4e8e6}.section{margin:0 0 34px}.section h2{margin:0 0 12px;color:#123943;font-size:22px}.table-wrap{overflow:auto;border:1px solid #dceae7;border-radius:16px;background:#fff;box-shadow:0 8px 24px rgba(18,57,67,.06)}table{width:100%;border-collapse:collapse;min-width:720px}th{padding:12px 14px;background:#e7f7f3;color:#143b44;text-align:left;font-size:13px;border-bottom:1px solid #cfe4df;white-space:nowrap}td{padding:11px 14px;border-bottom:1px solid #edf2f1;font-size:13px;vertical-align:top}tbody tr:last-child td{border-bottom:0}.empty{text-align:center;color:#7b8f94;padding:20px}@media(max-width:700px){body{padding:14px}.report-head{padding:18px}.report-head h1{font-size:24px}.section h2{font-size:19px}}
    </style></head><body><main><header class="report-head"><h1>Informe de progreso VitalPeak</h1><p>Periodo: ${htmlEsc(from)} a ${htmlEsc(to)}</p></header>
      <section class="section"><h2>Entrenamiento</h2><div class="table-wrap"><table><thead><tr><th>Fecha</th><th>Rutina</th><th>Ejercicio</th><th>Serie</th><th>Peso kg</th><th>Repeticiones</th><th>Notas</th></tr></thead><tbody>${trainingRows}</tbody></table></div></section>
      <section class="section"><h2>Progreso por ejercicio</h2><div class="table-wrap"><table><thead><tr><th>Ejercicio</th><th>Sesiones</th><th>Series</th><th>Mejor inicial kg</th><th>Mejor final kg</th><th>Cambio kg</th></tr></thead><tbody>${progressRows}</tbody></table></div></section>
      <section class="section"><h2>Peso corporal</h2><div class="table-wrap"><table><thead><tr><th>Fecha</th><th>Peso kg</th><th>Cambio desde inicio kg</th></tr></thead><tbody>${weightRows}</tbody></table></div></section>
    </main></body></html>`;
  }

  async function shareCurrent(){
    const modal=document.getElementById(MODAL_ID);if(!modal)return;
    const from=modal.querySelector('[name="from"]').value,to=modal.querySelector('[name="to"]').value;
    const state=await readState(),data=buildData(state,from,to),html=makeHtmlReport(data,from,to);
    const file=new File([html],`vitalpeak-progreso-${from}-a-${to}.html`,{type:'text/html;charset=utf-8'});
    const text=`Mi progreso en VitalPeak del ${from} al ${to}: ${data.sessions.length} entrenamientos, ${data.setRows.length} series y ${data.progress.length} ejercicios.`;
    try{if(navigator.share&&navigator.canShare?.({files:[file]})){await navigator.share({title:'Mi progreso VitalPeak',text,files:[file]});return}if(navigator.share){await navigator.share({title:'Mi progreso VitalPeak',text});return}}catch(err){if(err?.name==='AbortError')return}
    const url=URL.createObjectURL(file),a=document.createElement('a');a.href=url;a.download=file.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }

  async function openModal(){document.getElementById(MODAL_ID)?.remove();const state=await readState(),from=earliestDate(state),to=today(),modal=document.createElement('div');modal.id=MODAL_ID;modal.className='vp-share-backdrop';modal.innerHTML=`<div class="vp-share-dialog" role="dialog" aria-modal="true" aria-label="Compartir progreso"><div class="vp-share-head"><div><h2>Compartir progreso</h2><p>Elige el periodo que quieres compartir.</p></div><button class="vp-share-close" data-vp-share-close>×</button></div><div class="vp-share-range"><label>Desde<input type="date" name="from" value="${from}" max="${to}"></label><label>Hasta<input type="date" name="to" value="${to}" min="${from}" max="${to}"></label></div><div id="vp-share-preview"></div><div class="vp-share-actions"><button class="vp-share-native" data-vp-share-now>Compartir progreso</button></div></div>`;document.body.appendChild(modal);renderPreview(state,from,to)}
  function mount(){injectStyles();if(!isAccount())return;const app=document.querySelector('#app');if(!app||document.getElementById(ROOT_ID))return;const section=document.createElement('section');section.id=ROOT_ID;section.className='vp-share-card card stack';section.innerHTML=`<h3>Compartir progreso</h3><p>Genera un informe por fechas con tus ejercicios, series, pesos, repeticiones y evolución de peso corporal.</p><button type="button" class="vp-share-progress-btn" data-vp-open-share><svg viewBox="0 0 24 24"><path d="M12 16V4m0 0-4 4m4-4 4 4M5 13v6h14v-6"/></svg>Compartir progreso</button>`;const firstCard=app.querySelector('.card');if(firstCard)firstCard.insertAdjacentElement('afterend',section);else app.appendChild(section)}

  document.addEventListener('click',e=>{if(e.target.closest('[data-vp-open-share]')){e.preventDefault();openModal();return}if(e.target.closest('[data-vp-share-close]')||e.target.id===MODAL_ID){document.getElementById(MODAL_ID)?.remove();return}if(e.target.closest('[data-vp-share-now]')){e.preventDefault();shareCurrent();return}},true);
  document.addEventListener('change',async e=>{if(!e.target.closest(`#${MODAL_ID} .vp-share-range`))return;const modal=document.getElementById(MODAL_ID),from=modal.querySelector('[name="from"]'),to=modal.querySelector('[name="to"]');if(from.value>to.value)to.value=from.value;to.min=from.value;from.max=to.value;renderPreview(await readState(),from.value,to.value)},true);
  const app=document.querySelector('#app');if(app)new MutationObserver(()=>setTimeout(mount,20)).observe(app,{childList:true,subtree:false});const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(()=>setTimeout(mount,20)).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});injectStyles();setTimeout(mount,50);
})();