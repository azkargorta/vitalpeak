(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state', STYLE_ID='vp-calendar-recurrence-styles';
  let timer=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
  const today=()=>new Date().toISOString().slice(0,10);
  const monthKey=()=>document.querySelector('[data-plan-add-date]')?.dataset.planAddDate?.slice(0,7)||today().slice(0,7);

  function styles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vp-recurrence-panel{margin:12px 0 16px;padding:15px;border:1px solid #d9e8e4;border-radius:18px;background:linear-gradient(145deg,#fbfffe,#f1f9f6);box-shadow:0 8px 22px rgba(16,46,56,.05)}
      .vp-recurrence-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.vp-recurrence-head h3{margin:3px 0 4px;font-size:16px;color:#173e46}.vp-recurrence-head p{margin:0;color:#6c8186;font-size:11px;line-height:1.4}.vp-recurrence-badge{flex:none;padding:5px 8px;border-radius:99px;background:#e2f7f1;color:#177765;font-size:9px;font-weight:900;text-transform:uppercase}
      .vp-recurrence-presets{display:flex;gap:6px;overflow:auto;padding:12px 0 5px}.vp-recurrence-presets button{flex:none;min-height:36px;padding:7px 10px;border:1px solid #d1e2dd;border-radius:11px;background:#fff;color:#244a51;font-size:10px;font-weight:850}.vp-recurrence-presets button.active{background:#dff6f0;border-color:#6fcab8;color:#146f60}
      .vp-recurrence-map{display:grid;gap:7px;margin-top:9px}.vp-recurrence-row{display:grid;grid-template-columns:1fr minmax(135px,.8fr);gap:8px;align-items:center;padding:9px 10px;border-radius:12px;background:#fff;border:1px solid #e0ebe8}.vp-recurrence-row span{font-size:11px;font-weight:850;color:#294b52}.vp-recurrence-row select{min-height:38px;border:1px solid #d3e1dd;border-radius:9px;background:#fbfefd;padding:7px;color:#163d44;font-size:12px}
      .vp-recurrence-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:11px}.vp-recurrence-actions button{min-height:44px;border-radius:12px;font-weight:900}.vp-recurrence-save{border:0;background:#4fd3c1;color:#12383a}.vp-recurrence-remove{border:1px solid #e2b4af;background:#fff5f4;color:#914f4b}.vp-recurrence-help{margin:9px 1px 0;color:#74878c;font-size:10px;line-height:1.4}
      .vp-plan-legend{display:flex;gap:7px;overflow:auto;margin:4px 0 12px;padding-bottom:3px}.vp-plan-legend span{flex:none;display:inline-flex;align-items:center;gap:6px;padding:6px 9px;border:1px solid #dfe9e6;border-radius:99px;background:#fff;color:#536d72;font-size:10px;font-weight:800}.vp-plan-legend i{width:9px;height:9px;border-radius:50%;background:hsl(var(--vp-plan-hue) 52% 52%)}
      .calendar-entry[data-vp-plan]{position:relative;border-left:4px solid hsl(var(--vp-plan-hue) 52% 52%)!important;background:linear-gradient(90deg,hsl(var(--vp-plan-hue) 58% 96%),#fff)!important;color:#25494f!important}.calendar-entry[data-vp-plan].vp-completed{background:linear-gradient(90deg,#dff8ef,#f7fffc)!important}.calendar-entry[data-vp-plan].vp-omitted-entry{background:linear-gradient(90deg,#ffe7e4,#fff8f7)!important}
      .vp-recurrence-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:10px 0 0}.vp-recurrence-stat{padding:10px 8px;border-radius:12px;background:#fff;border:1px solid #e0ebe8;text-align:center}.vp-recurrence-stat b{display:block;font-size:16px;color:#173f47}.vp-recurrence-stat span{display:block;margin-top:3px;font-size:9px;color:#74878c;text-transform:uppercase;font-weight:850}
      @media(max-width:430px){.vp-recurrence-row{grid-template-columns:1fr}.vp-recurrence-actions{grid-template-columns:1fr}.vp-recurrence-summary{grid-template-columns:repeat(3,1fr)}}
    `;document.head.appendChild(s);
  }

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);tx.objectStore(STORE).put(state,'user')})}
  const entries=(state,date)=>{const x=state.plan?.[date];return Array.isArray(x)?[...x]:(x?[x]:[])};
  const iso=d=>new Date(d).toISOString().slice(0,10);
  function routine(state,id){return (state.routines||[]).find(r=>String(r.id)===String(id))||null}
  function hue(id){let h=0;for(const ch of String(id||''))h=(h*31+ch.charCodeAt(0))%360;return h}
  function firstOfMonth(key){return new Date(`${key}-01T12:00:00`)}
  function datesForWeekday(key,weekday){const d=firstOfMonth(key),month=d.getMonth(),out=[];while(d.getMonth()===month){const wd=(d.getDay()+6)%7;if(wd===Number(weekday))out.push(iso(d));d.setDate(d.getDate()+1)}return out}
  function recurrenceStore(state){state.calendarRecurrences=state.calendarRecurrences||{};return state.calendarRecurrences}
  function recKey(month,id){return `${month}::${id}`}

  function defaultMapping(program,state){return (program.days||[]).map((_,i)=>Number(state.programWeekdays?.[`${program.id}::${i}`]??i%7))}
  function presets(count){
    const standard={1:[0],2:[0,3],3:[0,2,4],4:[0,1,3,4],5:[0,1,2,3,4],6:[0,1,2,3,4,5],7:[0,1,2,3,4,5,6]};
    const list=[{id:'balanced',label:'Equilibrado',days:standard[count]||standard[7].slice(0,count)}];
    if(count===2)list.push({id:'tu-sa',label:'Mar · Sáb',days:[1,5]});
    if(count===3)list.push({id:'tthsa',label:'Mar · Jue · Sáb',days:[1,3,5]});
    if(count<=5)list.push({id:'weekdays',label:'Seguidos',days:Array.from({length:count},(_,i)=>i)});
    return list;
  }

  function existingRecord(state,month,id){return recurrenceStore(state)[recKey(month,id)]||null}
  function mappingFromUi(panel){return [...panel.querySelectorAll('[data-vp-recur-day]')].map(x=>Number(x.value))}

  function removeManaged(state,record){
    for(const item of record?.managed||[]){
      const xs=entries(state,item.date);const idx=xs.indexOf(item.key);if(idx>=0)xs.splice(idx,1);if(xs.length)state.plan[item.date]=xs;else delete state.plan[item.date];
    }
  }

  function applyRecurrence(state,month,program,mapping){
    state.plan=state.plan||{};const store=recurrenceStore(state),key=recKey(month,program.id),old=store[key];if(old)removeManaged(state,old);
    const managed=[];
    (program.days||[]).forEach((day,i)=>{
      const planKey=`${program.id}::${i}`;for(const date of datesForWeekday(month,mapping[i])){const xs=entries(state,date);if(!xs.includes(planKey))xs.push(planKey);state.plan[date]=xs;managed.push({date,key:planKey})}
    });
    store[key]={programId:program.id,month,mapping:[...mapping],managed,updatedAt:new Date().toISOString()};
    state.programWeekdays={...(state.programWeekdays||{})};mapping.forEach((wd,i)=>state.programWeekdays[`${program.id}::${i}`]=wd);
    return managed.length;
  }

  function addPanel(state,cal){
    const programId=document.querySelector('#planner-program')?.value||state.plannerProgramId;if(!programId)return;
    const program=routine(state,programId);if(!program?.days?.length)return;
    document.querySelector('.vp-recurrence-panel')?.remove();const month=monthKey(),record=existingRecord(state,month,program.id),mapping=record?.mapping||defaultMapping(program,state),week=['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
    const panel=document.createElement('section');panel.className='vp-recurrence-panel';panel.dataset.program=program.id;panel.dataset.month=month;
    const ps=presets(program.days.length);
    panel.innerHTML=`<div class="vp-recurrence-head"><div><span class="template-meta">RECURRENCIA MENSUAL</span><h3>${esc(program.name)}</h3><p>Configura una vez los días de la semana y VitalPeak mantiene este patrón durante el mes.</p></div><span class="vp-recurrence-badge">${record?'Activa':'Nueva'}</span></div><div class="vp-recurrence-presets">${ps.map(p=>`<button type="button" data-vp-preset="${p.id}" data-days="${p.days.join(',')}">${esc(p.label)}</button>`).join('')}</div><div class="vp-recurrence-map">${program.days.map((d,i)=>`<label class="vp-recurrence-row"><span>Día ${i+1} · ${esc(d.name||`Sesión ${i+1}`)}</span><select data-vp-recur-day="${i}">${week.map((n,wd)=>`<option value="${wd}" ${Number(mapping[i])===wd?'selected':''}>${n}</option>`).join('')}</select></label>`).join('')}</div><div class="vp-recurrence-actions"><button type="button" class="vp-recurrence-save">${record?'Actualizar recurrencia':'Crear recurrencia'}</button>${record?'<button type="button" class="vp-recurrence-remove">Eliminar recurrencia</button>':''}</div><div class="vp-recurrence-summary"><div class="vp-recurrence-stat"><b>${program.days.length}</b><span>Sesiones</span></div><div class="vp-recurrence-stat"><b>${new Set(mapping).size}</b><span>Días usados</span></div><div class="vp-recurrence-stat"><b>${record?.managed?.length||'—'}</b><span>Entrenos mes</span></div></div><p class="vp-recurrence-help">Al actualizar, solo se recolocan los entrenamientos creados por esta recurrencia. Los que hayas añadido manualmente permanecen intactos.</p>`;
    const setup=document.querySelector('.planner-setup');if(setup){setup.hidden=true;setup.insertAdjacentElement('afterend',panel)}else cal.insertAdjacentElement('beforebegin',panel);
    panel.querySelectorAll('[data-vp-preset]').forEach(b=>b.onclick=()=>{const days=b.dataset.days.split(',').map(Number);panel.querySelectorAll('[data-vp-recur-day]').forEach((sel,i)=>{if(days[i]!=null)sel.value=String(days[i])});panel.querySelectorAll('[data-vp-preset]').forEach(x=>x.classList.toggle('active',x===b))});
    panel.querySelector('.vp-recurrence-save').onclick=async()=>{const fresh=await readState(),p=routine(fresh,program.id);if(!p)return;const count=applyRecurrence(fresh,month,p,mappingFromUi(panel));await writeState(fresh);sessionStorage.setItem('vitalpeak:return-to-planner','1');sessionStorage.setItem('vitalpeak:calendar-toast',`Recurrencia actualizada · ${count} entrenamientos`);location.reload()};
    panel.querySelector('.vp-recurrence-remove')?.addEventListener('click',async()=>{const fresh=await readState(),rec=existingRecord(fresh,month,program.id);if(!rec)return;removeManaged(fresh,rec);delete recurrenceStore(fresh)[recKey(month,program.id)];await writeState(fresh);sessionStorage.setItem('vitalpeak:return-to-planner','1');sessionStorage.setItem('vitalpeak:calendar-toast','Recurrencia eliminada');location.reload()});
  }

  function paintPlans(state,cal){
    const seen=new Map();cal.querySelectorAll('.month-day').forEach(day=>{const date=day.querySelector('[data-plan-add-date]')?.dataset.planAddDate;if(!date)return;const keys=entries(state,date),els=[...day.querySelectorAll('.calendar-entry')];els.forEach((el,i)=>{const key=keys[i];if(!key)return;const id=String(key).split('::')[0],r=routine(state,id);el.dataset.vpPlan=id;el.style.setProperty('--vp-plan-hue',String(hue(id)));seen.set(id,r?.name||'Rutina')})});
    document.querySelector('.vp-plan-legend')?.remove();if(seen.size<2)return;const legend=document.createElement('div');legend.className='vp-plan-legend';legend.innerHTML=[...seen].map(([id,name])=>`<span style="--vp-plan-hue:${hue(id)}"><i></i>${esc(name)}</span>`).join('');cal.insertAdjacentElement('beforebegin',legend);
  }

  async function enhance(){styles();const cal=document.querySelector('.month-calendar');if(!cal)return;const state=await readState().catch(()=>null);if(!state)return;paintPlans(state,cal);addPanel(state,cal);const msg=sessionStorage.getItem('vitalpeak:calendar-toast');if(msg){sessionStorage.removeItem('vitalpeak:calendar-toast');const toast=document.querySelector('#toast');if(toast){toast.textContent=msg;toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),2600)}}}
  function schedule(){clearTimeout(timer);timer=setTimeout(enhance,100)}
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});document.addEventListener('change',e=>{if(e.target?.id==='planner-program')setTimeout(schedule,80)},true);schedule();
})();
