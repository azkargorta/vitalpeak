(() => {
  'use strict';

  let timer=null;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('es').trim();
  const ADD_ICON='<svg viewBox="0 0 32 24" aria-hidden="true"><path d="M3 10v4m3-6v8m3-2h10m3-6v8m3-6v4"/><path d="M26 2.5v7m-3.5-3.5h7"/></svg>';

  function fixAddExerciseIcon(){
    const section=document.querySelector('.vp-routine-section[data-vp-section="add-exercise"]');
    const icon=section?.querySelector(':scope > summary .vp-section-icon');
    if(!icon)return;
    if(icon.innerHTML!==ADD_ICON)icon.innerHTML=ADD_ICON;
    icon.dataset.vpCorrectIcon='2';
  }

  function cardHtml(x){
    const image=x.animation?.path?`<img src="./${encodeURI(x.animation.path)}" alt="Movimiento de ${esc(x.name)}" loading="lazy" style="width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:12px;margin-bottom:8px">`:'';
    return `<button class="exercise-card" data-action="exercise-detail" data-exercise="${esc(x.name)}">${image}<span>${esc(x.group||'Otro')}</span><b>${esc(x.name)}</b>${x.animation?.path?'<small>Movimiento guiado</small>':''}</button>`;
  }

  function addFilters(body,grid){
    if(body.querySelector('[data-vp-repair-exercise-search]'))return;
    const cards=[...grid.querySelectorAll('.exercise-card')];if(!cards.length)return;
    const groups=[...new Set(cards.map(c=>c.querySelector('span')?.textContent?.trim()||'Otro'))].sort((a,b)=>a.localeCompare(b,'es'));
    const f=document.createElement('div');f.className='vp-section-filters';f.dataset.vpRepairFilters='2';
    f.innerHTML=`<label>Grupo muscular<select data-vp-repair-exercise-group><option value="">Todos los grupos</option>${groups.map(g=>`<option value="${esc(g)}">${esc(g)}</option>`).join('')}</select></label><label>Buscar ejercicio<input type="search" autocomplete="off" placeholder="Escribe press, remo, curl…" data-vp-repair-exercise-search></label><span class="vp-filter-count" data-vp-repair-exercise-count></span>`;
    grid.insertAdjacentElement('beforebegin',f);
    const apply=()=>{const group=f.querySelector('[data-vp-repair-exercise-group]').value,q=norm(f.querySelector('[data-vp-repair-exercise-search]').value);let n=0;cards.forEach(c=>{const cg=c.querySelector('span')?.textContent?.trim()||'Otro',name=c.dataset.exercise||c.querySelector('b')?.textContent||'',show=(!group||cg===group)&&(!q||norm(`${name} ${cg}`).includes(q));c.hidden=!show;if(show)n++});f.querySelector('[data-vp-repair-exercise-count]').textContent=`${n} ejercicio${n===1?'':'s'} visible${n===1?'':'s'}`};
    f.addEventListener('input',apply);f.addEventListener('change',apply);apply();
  }

  function ensureCatalog(section){
    const body=section?.querySelector('.vp-routine-section-content');
    if(!section||!body)return false;
    let grid=body.querySelector('.exercise-grid');
    const catalog=window.VITALPEAK_CATALOG?.exercises||[];
    if(!catalog.length)return false;
    if(!grid){grid=document.createElement('div');grid.className='exercise-grid';body.appendChild(grid)}
    if(!grid.querySelector('.exercise-card')){
      grid.innerHTML=catalog.map(cardHtml).join('');
      body.querySelectorAll('.vp-filter-empty').forEach(x=>x.remove());
    }
    addFilters(body,grid);
    return true;
  }

  function bindExerciseSection(){
    const section=document.querySelector('.vp-routine-section[data-vp-section="predefined-exercises"]');
    const summary=section?.querySelector(':scope > summary');
    if(!section||!summary)return;
    ensureCatalog(section);
    if(summary.dataset.vpCatalogToggle==='2')return;
    summary.dataset.vpCatalogToggle='2';
    summary.addEventListener('click',e=>{
      e.preventDefault();
      e.stopImmediatePropagation();
      ensureCatalog(section);
      section.open=!section.open;
      try{
        const raw=JSON.parse(sessionStorage.getItem('vitalpeak:routines-open-sections')||'[]');
        const set=new Set(Array.isArray(raw)?raw:[]);
        if(section.open)set.add('predefined-exercises');else set.delete('predefined-exercises');
        sessionStorage.setItem('vitalpeak:routines-open-sections',JSON.stringify([...set]));
      }catch{}
    },true);
  }

  function repair(){
    if(!document.querySelector('.tabbar button[data-route="routines"].active'))return;
    fixAddExerciseIcon();
    bindExerciseSection();
  }
  function schedule(){clearTimeout(timer);timer=setTimeout(repair,45)}
  const app=document.getElementById('app');if(app)new MutationObserver(schedule).observe(app,{childList:true,subtree:true});
  const tabs=document.querySelector('.tabbar');if(tabs)new MutationObserver(schedule).observe(tabs,{attributes:true,subtree:true,attributeFilter:['class']});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule()});
  schedule();
})();