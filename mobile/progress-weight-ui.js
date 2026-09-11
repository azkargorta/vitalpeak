(() => {
  'use strict';

  const DB_NAME='vitalpeak-mobile', STORE='state';
  const STYLE_ID='vp-weight-module-style';
  let rendering=false;

  const num=v=>Number(v||0);
  const fmt=(v,d=1)=>Number(v||0).toLocaleString('es-ES',{minimumFractionDigits:d,maximumFractionDigits:d});
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const today=()=>new Date().toISOString().slice(0,10);
  const dateLabel=v=>{try{return new Intl.DateTimeFormat('es-ES',{day:'numeric',month:'short',year:'numeric'}).format(new Date(`${v}T12:00:00`))}catch{return v}};

  function openDb(){return new Promise((resolve,reject)=>{const r=indexedDB.open(DB_NAME,2);r.onupgradeneeded=()=>{if(!r.result.objectStoreNames.contains(STORE))r.result.createObjectStore(STORE)};r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error)})}
  async function readState(){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),q=tx.objectStore(STORE).get('user');q.onsuccess=()=>resolve(q.result||{});q.onerror=()=>reject(q.error)})}
  async function writeState(state){const db=await openDb();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(state,'user');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)})}

  function injectStyles(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .vpw-current{display:flex;align-items:end;justify-content:space-between;gap:10px;margin:4px 0 10px}.vpw-current strong{font-size:27px;color:#123843}.vpw-current span{font-size:11px;font-weight:800;color:#178d79}
      .vpw-chart{height:128px;margin:4px 0 12px}.vpw-chart svg{width:100%;height:100%;display:block}.vpw-grid{stroke:#e7efed;stroke-width:1}.vpw-line{fill:none;stroke:#12a48a;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}.vpw-dot{fill:#fff;stroke:#12a48a;stroke-width:2}.vpw-label{fill:#819399;font-size:9px}
      .vpw-add{display:flex;align-items:center;justify-content:center;gap:7px;width:100%;min-height:43px;border:0;border-radius:13px;background:#e4f8f3;color:#0a8d76;font-weight:900}.vpw-add svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2}
      .vpw-form{display:none;grid-template-columns:minmax(0,1fr) auto;gap:8px;margin-top:9px}.vpw-form.open{display:grid}.vpw-form input{min-width:0;border:1px solid #c9dfda;border-radius:12px;padding:11px;background:#fff;font-size:16px}.vpw-form button{border:0;border-radius:12px;padding:0 16px;background:#12a98e;color:#fff;font-weight:900}
      .vpw-history{margin-top:14px;padding-top:12px;border-top:1px solid #e7efed}.vpw-history-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.vpw-history-head h3{margin:0;color:#173b43;font-size:14px}.vpw-history-head span{color:#7b8f94;font-size:10px}
      .vpw-list{display:grid;gap:7px}.vpw-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:7px;align-items:center;padding:9px 10px;border:1px solid #e5eeec;border-radius:12px;background:#f9fcfb}.vpw-copy b{display:block;color:#173b43;font-size:13px}.vpw-copy span{display:block;margin-top:2px;color:#7a8e93;font-size:10px}
      .vpw-icon{width:34px;height:34px;display:grid;place-items:center;border:0;border-radius:10px;background:#e8f7f4;color:#0d8f7b}.vpw-icon.delete{background:#fff0f2;color:#b5475a}.vpw-icon svg{width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
      .vpw-edit{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:7px;align-items:center;padding:9px 10px;border:1px solid #bfe4dd;border-radius:12px;background:#f2faf8}.vpw-edit input{min-width:0;width:100%;border:1px solid #c8ded9;border-radius:10px;padding:9px;background:#fff;font-size:16px;font-weight:800}.vpw-edit button{border:0;border-radius:10px;padding:9px 10px;font-weight:850}.vpw-save{background:#14a68d;color:#fff}.vpw-cancel{background:#e8efed;color:#51696f}.vpw-empty{padding:13px 6px;text-align:center;color:#7d9095;font-size:12px}
    `;document.head.appendChild(s);
  }

  function weightCard(){
    return [...document.querySelectorAll('.vp-progress-page .vp-progress-card')].find(card=>card.querySelector('h2')?.textContent.trim()==='Peso corporal')||null;
  }

  function chartSvg(weights){
    if(!weights.length)return '<div class="vpw-empty">Añade tu primer peso para empezar la gráfica.</div>';
    const values=weights.map(w=>num(w.kg)),min=Math.min(...values),max=Math.max(...values),range=Math.max(max-min,1),w=320,h=118,p=18;
    const pts=weights.map((x,i)=>{const px=weights.length===1?w/2:p+i*(w-2*p)/(weights.length-1),py=h-p-((num(x.kg)-min)/range)*(h-2*p);return {x:px,y:py,label:dateLabel(x.date),kg:num(x.kg)}});
    const poly=pts.map(x=>`${x.x},${x.y}`).join(' ');
    return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><line class="vpw-grid" x1="0" y1="${h*.25}" x2="${w}" y2="${h*.25}"/><line class="vpw-grid" x1="0" y1="${h*.5}" x2="${w}" y2="${h*.5}"/><line class="vpw-grid" x1="0" y1="${h*.75}" x2="${w}" y2="${h*.75}"/><polyline class="vpw-line" points="${poly}"/>${pts.map((x,i)=>`<circle class="vpw-dot" cx="${x.x}" cy="${x.y}" r="4"><title>${esc(x.label)} · ${fmt(x.kg)} kg</title></circle>${(i===0||i===pts.length-1)?`<text class="vpw-label" x="${x.x}" y="${Math.max(10,x.y-8)}" text-anchor="${i===0?'start':'end'}">${fmt(x.kg)} kg</text>`:''}`).join('')}</svg>`;
  }

  function updateTopSummary(weights){
    const stat=[...document.querySelectorAll('.vp-progress-page .vp-progress-stat')].find(x=>x.querySelector('small')?.textContent.trim()==='Peso');
    if(!stat)return;
    const b=stat.querySelector('b'),change=stat.querySelector('.vp-progress-change');
    if(!weights.length){if(b)b.textContent='—';if(change){change.className='vp-progress-change neutral';change.textContent='Sin dato'};return}
    const latest=num(weights.at(-1).kg),first=num(weights[0].kg),delta=latest-first;
    if(b)b.textContent=`${fmt(latest)} kg`;
    if(change){change.className=`vp-progress-change ${delta<0?'down':''}`;change.textContent=weights.length<2?'1 registro':`${delta>0?'+':''}${fmt(delta)} kg`}
  }

  async function renderWeight(){
    if(rendering)return;
    const card=weightCard();if(!card)return;
    rendering=true;
    try{
      const state=await readState();
      const weights=(Array.isArray(state.weights)?state.weights:[]).map((x,index)=>({...x,index})).sort((a,b)=>String(a.date||'').localeCompare(String(b.date||''))||a.index-b.index);
      const latest=weights.length?num(weights.at(-1).kg):null,delta=weights.length>1?latest-num(weights[0].kg):null;
      card.innerHTML=`<div class="vp-card-head"><span class="vp-card-icon"><svg viewBox="0 0 24 24"><path d="M7 6a5 5 0 0 1 10 0"/><path d="M5 7h14l2 14H3L5 7Z"/><path d="M12 6v4"/></svg></span><div class="vp-card-head-copy"><h2>Peso corporal</h2><p>Evolución de tus registros</p></div></div><div class="vpw-current"><strong>${latest==null?'—':`${fmt(latest)} kg`}</strong><span>${delta==null?(weights.length?'1 registro':'Sin registros'):`${delta>0?'+':''}${fmt(delta)} kg desde el inicio`}</span></div><div class="vpw-chart">${chartSvg(weights)}</div><button type="button" class="vpw-add" data-vpw-add><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>Registrar peso</button><form class="vpw-form" data-vpw-form><input name="kg" type="number" inputmode="decimal" step="0.1" min="1" required placeholder="Peso en kg"><button type="submit">Guardar</button></form><div class="vpw-history"><div class="vpw-history-head"><h3>Valores registrados</h3><span>${weights.length} registro${weights.length===1?'':'s'}</span></div><div class="vpw-list">${weights.length?[...weights].reverse().map(w=>`<div class="vpw-row" data-vpw-row="${w.index}"><div class="vpw-copy"><b>${fmt(w.kg)} kg</b><span>${esc(dateLabel(w.date||''))}</span></div><button type="button" class="vpw-icon" data-vpw-edit="${w.index}" aria-label="Editar peso"><svg viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16v4Z"/><path d="m13.5 6.5 4 4"/></svg></button><button type="button" class="vpw-icon delete" data-vpw-delete="${w.index}" aria-label="Eliminar peso"><svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg></button></div>`).join(''):'<div class="vpw-empty">Todavía no has introducido ningún peso.</div>'}</div></div>`;
      updateTopSummary(weights);
    }finally{rendering=false}
  }

  function focusInput(input){requestAnimationFrame(()=>{try{input.focus({preventScroll:false})}catch{input.focus()}})}

  document.addEventListener('click',async e=>{
    const add=e.target.closest('[data-vpw-add]');if(add){e.preventDefault();e.stopImmediatePropagation();const form=add.parentElement.querySelector('[data-vpw-form]');form?.classList.toggle('open');if(form?.classList.contains('open'))focusInput(form.querySelector('input'));return}
    const edit=e.target.closest('[data-vpw-edit]');if(edit){e.preventDefault();e.stopImmediatePropagation();const index=Number(edit.dataset.vpwEdit),state=await readState(),current=state.weights?.[index],row=edit.closest('[data-vpw-row]');if(!current||!row)return;row.outerHTML=`<div class="vpw-edit" data-vpw-edit-row="${index}"><input type="number" inputmode="decimal" step="0.1" min="1" value="${num(current.kg)}"><button type="button" class="vpw-save" data-vpw-save="${index}">Guardar</button><button type="button" class="vpw-cancel" data-vpw-cancel>Cancelar</button></div>`;focusInput(document.querySelector(`[data-vpw-edit-row="${index}"] input`));return}
    const cancel=e.target.closest('[data-vpw-cancel]');if(cancel){e.preventDefault();e.stopImmediatePropagation();await renderWeight();return}
    const save=e.target.closest('[data-vpw-save]');if(save){e.preventDefault();e.stopImmediatePropagation();const index=Number(save.dataset.vpwSave),input=save.closest('[data-vpw-edit-row]')?.querySelector('input'),kg=Number(input?.value);if(!Number.isFinite(kg)||kg<=0){focusInput(input);return}const state=await readState();state.weights=Array.isArray(state.weights)?state.weights:[];if(!state.weights[index])return;state.weights[index]={...state.weights[index],kg};await writeState(state);await renderWeight();return}
    const del=e.target.closest('[data-vpw-delete]');if(del){e.preventDefault();e.stopImmediatePropagation();const index=Number(del.dataset.vpwDelete),state=await readState();state.weights=Array.isArray(state.weights)?state.weights:[];const current=state.weights[index];if(!current)return;if(!confirm(`¿Eliminar el registro de ${fmt(current.kg)} kg?`))return;state.weights.splice(index,1);await writeState(state);await renderWeight();return}
  },true);

  document.addEventListener('submit',async e=>{
    const form=e.target.closest('[data-vpw-form]');if(!form)return;
    e.preventDefault();e.stopImmediatePropagation();
    const input=form.querySelector('input[name="kg"]'),kg=Number(input?.value);if(!Number.isFinite(kg)||kg<=0){focusInput(input);return}
    const state=await readState();state.weights=Array.isArray(state.weights)?state.weights:[];state.weights.push({date:today(),kg});await writeState(state);await renderWeight();
  },true);

  const app=document.querySelector('#app');if(app)new MutationObserver(()=>{clearTimeout(window.__vpWeightModuleTimer);window.__vpWeightModuleTimer=setTimeout(renderWeight,50)}).observe(app,{childList:true,subtree:false});
  const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(()=>setTimeout(renderWeight,50)).observe(tabs,{subtree:true,attributes:true,attributeFilter:['class']});
  injectStyles();setTimeout(renderWeight,100);
})();