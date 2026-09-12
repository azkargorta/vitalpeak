(() => {
  'use strict';

  const APP=()=>document.querySelector('#app');
  const ROUTINES=()=>document.querySelector('.tabbar button[data-route="routines"]');
  let timer=null;

  function active(){return !!ROUTINES()?.classList.contains('active');}
  function templateById(id){
    return (window.VITALPEAK_CATALOG?.templates||[]).find(t=>String(t.id)===String(id))||null;
  }

  function setup(){
    if(!active()) return;
    const section=APP()?.querySelector('#vp-routines-accordion .vp-routine-section[data-vp-section="predefined-routines"]');
    const body=section?.querySelector('.vp-routine-section-content');
    if(!body) return;

    let daySelect=body.querySelector('[data-vp-routine-days]');
    const levelSelect=body.querySelector('[data-vp-routine-level]');
    const buttons=[...body.querySelectorAll('[data-action="view-template"]')];
    if(!buttons.length) return;

    if(!daySelect){
      const days=[...new Set((window.VITALPEAK_CATALOG?.templates||[])
        .map(t=>Number(t.days_per_week||t.days?.length||0))
        .filter(n=>Number.isFinite(n)&&n>0))].sort((a,b)=>a-b);

      let filters=body.querySelector('.vp-section-filters');
      if(!filters){
        filters=document.createElement('div');
        filters.className='vp-section-filters';
        body.insertAdjacentElement('afterbegin',filters);
      } else {
        filters.classList.remove('one');
      }

      const label=document.createElement('label');
      label.innerHTML=`Días por semana<select data-vp-routine-days><option value="">Todos los días</option>${days.map(n=>`<option value="${n}">${n} día${n===1?'':'s'}</option>`).join('')}</select>`;
      const count=filters.querySelector('[data-vp-routine-count]');
      if(count) filters.insertBefore(label,count);
      else filters.appendChild(label);
      daySelect=label.querySelector('[data-vp-routine-days]');
    }

    const count=body.querySelector('[data-vp-routine-count]');
    const apply=()=>{
      const dayValue=Number(daySelect?.value||0);
      const levelValue=levelSelect?.value||'';
      let visible=0;
      buttons.forEach(button=>{
        const template=templateById(button.dataset.template);
        const templateDays=Number(template?.days_per_week||template?.days?.length||0);
        const daysOk=!dayValue||templateDays===dayValue;
        const levelOk=!levelValue||String(template?.level||'')===levelValue;
        const show=daysOk&&levelOk;
        button.hidden=!show;
        if(show) visible+=1;
      });
      if(count) count.textContent=`${visible} rutina${visible===1?'':'s'} visible${visible===1?'':'s'}`;

      let empty=body.querySelector('.vp-filter-empty[data-kind="routines-days"]');
      if(!visible){
        if(!empty){
          empty=document.createElement('div');
          empty.className='vp-filter-empty';
          empty.dataset.kind='routines-days';
          empty.textContent='No hay rutinas con ese número de días y nivel.';
          body.appendChild(empty);
        }
      }else empty?.remove();
    };

    if(!daySelect.dataset.vpBound){
      daySelect.dataset.vpBound='1';
      daySelect.addEventListener('change',apply);
    }
    if(levelSelect && !levelSelect.dataset.vpDaysBound){
      levelSelect.dataset.vpDaysBound='1';
      levelSelect.addEventListener('change',()=>setTimeout(apply,0));
    }
    apply();
  }

  function schedule(delay=30){
    clearTimeout(timer);
    timer=setTimeout(setup,delay);
  }

  const start=()=>{
    const app=APP();
    if(!app) return setTimeout(start,30);
    new MutationObserver(()=>{if(active()) schedule();}).observe(app,{childList:true,subtree:false});
    const tabbar=document.querySelector('.tabbar');
    if(tabbar) new MutationObserver(()=>{if(active()) schedule(0);}).observe(tabbar,{subtree:true,attributes:true,attributeFilter:['class']});
    document.addEventListener('toggle',e=>{
      if(e.target?.matches?.('.vp-routine-section[data-vp-section="predefined-routines"]')) schedule(0);
    },true);
    setup();
  };
  start();
})();
