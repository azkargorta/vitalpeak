(() => {
  'use strict';

  if (!window.__VITALPEAK_CARDIO_LOADER__) {
    window.__VITALPEAK_CARDIO_LOADER__ = true;
    const script = document.createElement('script');
    script.src = './cardio-catalog.js?v=2';
    script.onload = () => {
      window.dispatchEvent(new Event('vitalpeak:catalog-updated'));
      const training = document.createElement('script');
      training.src = './cardio-training.js?v=1';
      document.head.appendChild(training);
    };
    document.head.appendChild(script);
  }

  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  let editingSetIndex = null;
  let busy = false;

  function isCurrentCardio(){const name=currentExerciseName(),x=(window.VITALPEAK_CATALOG?.exercises||[]).find(e=>e.name===name);return !!(x?.cardio||x?.group==='Cardio')}

  function ensureStyles() {
    if (document.querySelector('#vp-set-editor-styles')) return;
    const style = document.createElement('style');
    style.id = 'vp-set-editor-styles';
    style.textContent = `
      .set-list .set{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
      .vp-set-text{min-width:0;flex:1 1 150px}
      .vp-set-actions{display:flex;gap:6px;flex:0 0 auto}
      .vp-set-action{min-height:32px;border:0;border-radius:9px;padding:6px 9px;font-size:11px;font-weight:850;cursor:pointer}
      .vp-set-edit{background:#e8f6f2;color:#176d61}
      .vp-set-delete{background:#fdecef;color:#b43b4c}
      .vp-editing-banner{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:12px;background:#fff5dc;color:#725313;font-size:12px;font-weight:750}
      .vp-editing-banner button{border:0;border-radius:9px;background:#fff;color:#725313;padding:6px 9px;font-weight:800}
      #set-form.vp-editing-set>button[type="submit"]{background:#176d61}
      @media(max-width:380px){.vp-set-actions{width:100%}.vp-set-action{flex:1}}
    `;
    document.head.appendChild(style);
  }

  function openDB() { return new Promise((resolve, reject) => { const req=indexedDB.open(DB_NAME,2); req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains(STORE))req.result.createObjectStore(STORE)}; req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error); }); }
  async function readState(){const db=await openDB();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readonly'),req=tx.objectStore(STORE).get('user');req.onsuccess=()=>resolve(req.result||{});req.onerror=()=>reject(req.error)})}
  async function writeState(state){const db=await openDB();return new Promise((resolve,reject)=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(state,'user');tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error)})}
  function currentExerciseName(){const form=document.querySelector('#set-form'),card=form?.closest('.card');return card?.querySelector('.row h2')?.textContent?.trim()||''}
  function indicesForExercise(state,exerciseName){const sets=state?._draft?.sets||[],indices=[];sets.forEach((set,index)=>{if(set.exercise===exerciseName)indices.push(index)});return indices}
  function toast(message){const el=document.querySelector('#toast');if(!el)return;el.textContent=message;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2400)}

  async function decorateSets(){
    ensureStyles();
    const form=document.querySelector('#set-form'),list=document.querySelector('.set-list');
    if(!form||!list||busy||isCurrentCardio())return;
    const exerciseName=currentExerciseName();if(!exerciseName)return;
    const state=await readState().catch(()=>null);if(!state?._draft)return;
    const indices=indicesForExercise(state,exerciseName),rows=[...list.querySelectorAll('.set')];
    rows.forEach((row,visibleIndex)=>{const actualIndex=indices[visibleIndex];if(actualIndex===undefined)return;row.dataset.vpSetIndex=String(actualIndex);if(row.querySelector('.vp-set-actions'))return;const original=row.textContent.trim();row.textContent='';const text=document.createElement('span');text.className='vp-set-text';text.textContent=original;const actions=document.createElement('span');actions.className='vp-set-actions';actions.innerHTML=`<button type="button" class="vp-set-action vp-set-edit" data-vp-edit-set="${actualIndex}">Editar</button><button type="button" class="vp-set-action vp-set-delete" data-vp-delete-set="${actualIndex}">Eliminar</button>`;row.append(text,actions)});
  }

  async function startEdit(index){if(isCurrentCardio())return;const state=await readState(),set=state?._draft?.sets?.[index],form=document.querySelector('#set-form');if(!set||!form)return;editingSetIndex=index;form.classList.add('vp-editing-set');if(form.elements.weight)form.elements.weight.value=set.weight??'';if(form.elements.reps)form.elements.reps.value=set.reps??'';if(form.elements.heartRate)form.elements.heartRate.value=set.heartRate??'';if(form.elements.notes)form.elements.notes.value=set.notes??'';const submit=form.querySelector('button[type="submit"], button:not([type])');if(submit)submit.textContent='Guardar cambios de la serie';let banner=form.querySelector('.vp-editing-banner');if(!banner){banner=document.createElement('div');banner.className='vp-editing-banner';form.prepend(banner)}const exerciseName=currentExerciseName(),ordinal=indicesForExercise(state,exerciseName).indexOf(index)+1;banner.innerHTML=`<span>Editando serie ${ordinal>0?ordinal:''}</span><button type="button" data-vp-cancel-edit>Cancelar</button>`;form.scrollIntoView({behavior:'smooth',block:'center'})}
  function cancelEdit(){editingSetIndex=null;const form=document.querySelector('#set-form');if(!form)return;form.classList.remove('vp-editing-set');form.querySelector('.vp-editing-banner')?.remove();const submit=form.querySelector('button[type="submit"], button:not([type])'),count=document.querySelectorAll('.set-list .set').length;if(submit)submit.textContent=`Guardar serie ${count+1}`}
  async function deleteSet(index){if(isCurrentCardio())return;const state=await readState(),draft=state?._draft,set=draft?.sets?.[index];if(!draft||!set)return;if(!window.confirm('¿Eliminar esta serie guardada? Esta acción no se puede deshacer.'))return;draft.sets.splice(index,1);const remaining=draft.sets.filter(x=>x.exercise===set.exercise).length,form=document.querySelector('#set-form'),targetText=form?.closest('.card')?.querySelector('.muted')?.textContent||'',target=Number(targetText.match(/Objetivo:\s*(\d+)/i)?.[1]||0);if(!target||remaining<target)draft.pendingChoice=false;draft.restEndsAt=null;await writeState(state);location.reload()}

  document.addEventListener('click',async event=>{if(isCurrentCardio())return;const edit=event.target.closest('[data-vp-edit-set]');if(edit){event.preventDefault();event.stopImmediatePropagation();await startEdit(Number(edit.dataset.vpEditSet)).catch(()=>toast('No se ha podido abrir la serie para editar.'));return}const del=event.target.closest('[data-vp-delete-set]');if(del){event.preventDefault();event.stopImmediatePropagation();await deleteSet(Number(del.dataset.vpDeleteSet)).catch(()=>toast('No se ha podido eliminar la serie.'));return}if(event.target.closest('[data-vp-cancel-edit]')){event.preventDefault();event.stopImmediatePropagation();cancelEdit()}},true);
  document.addEventListener('submit',async event=>{if(event.target.id!=='set-form'||editingSetIndex===null||isCurrentCardio())return;event.preventDefault();event.stopImmediatePropagation();if(busy)return;busy=true;try{const form=event.target,data=new FormData(form),state=await readState(),draft=state?._draft,set=draft?.sets?.[editingSetIndex];if(!draft||!set)throw new Error('Serie no encontrada');set.weight=Number(data.get('weight'));set.reps=Number(data.get('reps'));set.heartRate=String(data.get('heartRate')||'').trim()?Number(data.get('heartRate')):null;set.notes=String(data.get('notes')||'');set.editedAt=new Date().toISOString();const remaining=draft.sets.filter(x=>x.exercise===set.exercise).length,targetText=form.closest('.card')?.querySelector('.muted')?.textContent||'',target=Number(targetText.match(/Objetivo:\s*(\d+)/i)?.[1]||0);draft.pendingChoice=Boolean(target&&remaining>=target);await writeState(state);editingSetIndex=null;location.reload()}catch{busy=false;toast('No se han podido guardar los cambios de la serie.')}},true);

  let timer=null;const observer=new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(()=>decorateSets().catch(()=>{}),40)});const start=()=>{const app=document.querySelector('#app');if(!app)return setTimeout(start,50);observer.observe(app,{childList:true,subtree:true});decorateSets().catch(()=>{})};start();
})();