(() => {
  'use strict';

  const normalize = value => String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase('es')
    .trim();

  const allExercises = () => Array.isArray(window.VITALPEAK_CATALOG?.exercises)
    ? [...window.VITALPEAK_CATALOG.exercises].sort((a,b)=>String(a.name).localeCompare(String(b.name),'es'))
    : [];

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function groups() {
    return [...new Set(allExercises().map(x => String(x.group || 'Otro')).filter(Boolean))]
      .sort((a,b)=>a.localeCompare(b,'es'));
  }

  function matchesFor(search, group) {
    const q = normalize(search);
    return allExercises().filter(x => {
      const groupOk = !group || String(x.group || 'Otro') === group;
      const textOk = !q || normalize(`${x.name} ${x.group || ''}`).includes(q);
      return groupOk && textOk;
    });
  }

  function apply(dayIndex) {
    const search = document.querySelector(`[data-vp-exercise-search="${dayIndex}"]`);
    const group = document.querySelector(`[data-vp-exercise-group="${dayIndex}"]`);
    const select = document.querySelector(`[data-vp-exercise-select="${dayIndex}"]`);
    const count = document.querySelector(`[data-vp-exercise-count="${dayIndex}"]`);
    if (!search || !group || !select) return;

    const previous = select.value;
    const list = matchesFor(search.value, group.value);
    select.innerHTML = `<option value="">${list.length ? 'Selecciona un ejercicio…' : 'No hay resultados'}</option>${list.map(x => `<option value="${esc(x.name)}">${esc(x.name)} · ${esc(x.group || 'Otro')}</option>`).join('')}`;
    if (list.some(x => x.name === previous)) select.value = previous;
    else if (list.length === 1) select.value = list[0].name;
    if (count) count.textContent = `${list.length} resultado${list.length === 1 ? '' : 's'}`;
  }

  function enhance() {
    document.querySelectorAll('.vp-exercise-search-wrap').forEach(wrap => {
      if (wrap.dataset.vpMuscleFilter === '1') return;
      const search = wrap.querySelector('[data-vp-exercise-search]');
      if (!search) return;
      const dayIndex = search.dataset.vpExerciseSearch;
      const select = document.createElement('select');
      select.className = 'vp-exercise-group-filter';
      select.dataset.vpExerciseGroup = dayIndex;
      select.innerHTML = `<option value="">Todos los grupos musculares</option>${groups().map(g => `<option value="${esc(g)}">${esc(g)}</option>`).join('')}`;
      search.insertAdjacentElement('afterend', select);
      wrap.dataset.vpMuscleFilter = '1';
      select.addEventListener('change', () => apply(dayIndex));
      search.addEventListener('input', () => setTimeout(() => apply(dayIndex), 0));
      apply(dayIndex);
    });
  }

  if (!document.querySelector('#vp-muscle-filter-style')) {
    const style = document.createElement('style');
    style.id = 'vp-muscle-filter-style';
    style.textContent = `.vp-exercise-group-filter{width:100%;min-height:44px;border:1px solid #cddfda;border-radius:11px;background:#fff;padding:9px;color:#102e38;font-size:14px}`;
    document.head.appendChild(style);
  }

  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 60);
    new MutationObserver(enhance).observe(app, {childList:true, subtree:true});
    enhance();
  };
  start();
})();