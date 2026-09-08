(() => {
  'use strict';
  const DB_NAME='vitalpeak-mobile',STORE='state';
  const openDB=()=>new Promise((ok,no)=>{const r=indexedDB.open(DB_NAME,2);r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error)});
  async function readState(){const db=await openDB();return new Promise((ok,no)=>{const tx=db.transaction(STORE,'readonly'),r=tx.objectStore(STORE).get('user');r.onsuccess=()=>ok(r.result||{});r.onerror=()=>no(r.error)})}
  const cardioInfo=name=>(window.VITALPEAK_CATALOG?.exercises||[]).find(e=>e.name===name)||null;
  const cardio=name=>{const x=cardioInfo(name);return !!(x?.cardio||x?.group==='Cardio')};
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function text(s){const a=[];if(s.durationMin!=null)a.push(`${s.durationMin} min`);if(s.distanceKm!=null)a.push(`${s.distanceKm} km`);if(s.speedKmh!=null)a.push(`${Number(s.speedKmh).toFixed(1)} km/h`);if(s.paceMinKm)a.push(`${s.paceMinKm} min/km`);if(s.resistance!=null)a.push(`res. ${s.resistance}`);if(s.inclinePercent!=null)a.push(`${s.inclinePercent}% incl.`);a.push(`❤️ ${s.heartRate??'SD'}`);return a.join(' · ')}
  async function rowsFor(name){const state=await readState(),rows=[];for(const session of state.sessions||[])for(const s of session.sets||[])if(s.exercise===name&&s.cardio)rows.push({...s,date:session.date});return rows.sort((a,b)=>String(b.at||b.date).localeCompare(String(a.at||a.date)))}
  function polishTrain(){const form=document.querySelector('#set-form');if(!form||!cardio(form.closest('.card')?.querySelector('.row h2')?.textContent?.trim()))return;const timer=document.querySelector('#rest-timer');if(timer&&!timer.dataset.vpCardioText){timer.dataset.vpCardioText='1';timer.textContent=document.querySelector('.set-list .vp-cardio-card')?'Cardio registrado':'Registra tu sesión de cardio'}const modal=document.querySelector('.decision-card');if(modal&&!modal.dataset.vpCardio){modal.dataset.vpCardio='1';const meta=modal.querySelector('.template-meta'),h=modal.querySelector('h2'),p=modal.querySelector('p'),buttons=modal.querySelectorAll('button');if(meta)meta.textContent='CARDIO REGISTRADO';if(h)h.textContent='Sesión de cardio completada';if(p)p.innerHTML='Has guardado los datos de este ejercicio cardiovascular. ¿Quieres añadir otro registro o continuar?';if(buttons[0])buttons[0].textContent='Añadir otro registro'}}
  async function polishProgress(){const select=document.querySelector('#progress-exercise');if(!select||!cardio(select.value))return;const card=select.closest('.card.stack');if(!card||card.dataset.vpCardioProgress===select.value)return;card.dataset.vpCardioProgress=select.value;card.querySelectorAll('.exercise-metrics,.exercise-chart,.history-table').forEach(e=>e.style.display='none');card.querySelectorAll('.vp-cardio-progress-inline').forEach(e=>e.remove());const rows=await rowsFor(select.value),totalMin=rows.reduce((n,x)=>n+Number(x.durationMin||0),0),totalKm=rows.reduce((n,x)=>n+Number(x.distanceKm||0),0),bestSpeed=Math.max(0,...rows.map(x=>Number(x.speedKmh||0))),avgHr=rows.filter(x=>x.heartRate).length?Math.round(rows.filter(x=>x.heartRate).reduce((n,x)=>n+Number(x.heartRate),0)/rows.filter(x=>x.heartRate).length):null;const html=`<div class="vp-cardio-progress-inline"><div class="metric-grid exercise-metrics" style="display:grid"><div class="metric"><b>${totalMin}</b><span>minutos</span></div><div class="metric"><b>${totalKm.toFixed(1)} km</b><span>distancia</span></div><div class="metric"><b>${avgHr??'—'}</b><span>PPM media</span></div></div>${rows.length?`<div class="vp-cardio-history">${rows.slice(0,15).map(x=>`<div><b>${esc(x.date)}</b><span class="muted small">${esc(text(x))}</span>${x.notes?`<div class="muted small">${esc(x.notes)}</div>`:''}</div>`).join('')}</div>`:`<p class="muted">Todavía no has registrado cardio de ${esc(select.value)}.</p>`}${bestSpeed?`<p class="muted small">Mejor velocidad registrada: <b>${bestSpeed.toFixed(1)} km/h</b></p>`:''}</div>`;select.closest('.field').insertAdjacentHTML('afterend',html)}
  function polishExercise(){
    const title=document.querySelector('.hero h1')?.textContent?.trim();
    if(!title||!cardio(title))return;
    const card=document.querySelector('#app .card.stack'),info=cardioInfo(title),path=info?.animation?.path;
    if(!card)return;
    if(path){
      let media=card.querySelector('.movement-placeholder');
      if(!media){
        media=document.createElement('div');
        media.className='movement-placeholder vp-cardio-image';
        media.innerHTML='<img alt=""><b></b><span></span>';
        card.insertAdjacentElement('afterbegin',media);
      }
      media.classList.add('vp-cardio-image');
      const img=media.querySelector('img'),label=media.querySelector('b'),note=media.querySelector('span');
      if(img){img.src='./'+encodeURI(String(path).replace(/^\.\//,''));img.alt=`Imagen de ${title}`;img.loading='eager';img.style.width='100%';img.style.height='auto';img.style.maxHeight='340px';img.style.objectFit='contain'}
      if(label)label.textContent='Imagen del ejercicio';
      if(note)note.textContent='Referencia visual del ejercicio de cardio.';
    }
    card.querySelectorAll('.exercise-metrics,.exercise-chart,.history-list').forEach(e=>e.style.display='none');
    card.dataset.vpCardioDetail='1';
  }
  let t;const run=()=>{clearTimeout(t);t=setTimeout(()=>{polishTrain();polishProgress().catch(()=>{});polishExercise()},70)};const start=()=>{const app=document.querySelector('#app');if(!app)return setTimeout(start,50);new MutationObserver(run).observe(app,{childList:true,subtree:true});document.addEventListener('change',e=>{if(e.target.id==='progress-exercise'){const c=e.target.closest('.card.stack');if(c)delete c.dataset.vpCardioProgress;run()}});run()};start();
})();