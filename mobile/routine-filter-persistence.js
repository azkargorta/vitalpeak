(() => {
  'use strict';

  const STORAGE_KEY = 'vitalpeak:routine-filter-state-v1';
  let restoring = false;

  const readState = () => {
    try { return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '{}'); }
    catch { return {}; }
  };

  const writeState = state => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
  };

  function controlKey(el) {
    if (!el) return '';
    if (el.matches('[data-vp-routine-level]')) return 'routine-level';
    if (el.matches('[data-vp-exercise-catalog-group]')) return 'exercise-group';
    if (el.matches('[data-vp-exercise-catalog-search]')) return 'exercise-search';

    const row = el.closest('.filter-row');
    if (!row) return '';
    const controls = [...row.querySelectorAll('select,input')];
    const index = controls.indexOf(el);
    return `native-${el.tagName.toLowerCase()}-${el.name || el.id || index}`;
  }

  function saveControl(el) {
    if (restoring) return;
    const key = controlKey(el);
    if (!key) return;
    const state = readState();
    state[key] = el.type === 'checkbox' ? Boolean(el.checked) : el.value;
    writeState(state);
  }

  function restoreFilters() {
    const app = document.querySelector('#app');
    if (!app) return;
    const state = readState();
    const controls = app.querySelectorAll(
      '[data-vp-routine-level], [data-vp-exercise-catalog-group], [data-vp-exercise-catalog-search], .filter-row select, .filter-row input'
    );

    controls.forEach(el => {
      const key = controlKey(el);
      if (!key || !(key in state) || el.dataset.vpFilterRestored === '1') return;
      el.dataset.vpFilterRestored = '1';
      restoring = true;
      if (el.type === 'checkbox') el.checked = Boolean(state[key]);
      else el.value = state[key] ?? '';
      const type = el.matches('input[type="search"],input[type="text"]') ? 'input' : 'change';
      el.dispatchEvent(new Event(type, { bubbles: true }));
      restoring = false;
    });
  }

  document.addEventListener('input', event => {
    if (event.target.matches('[data-vp-exercise-catalog-search], .filter-row input')) saveControl(event.target);
  }, true);

  document.addEventListener('change', event => {
    if (event.target.matches('[data-vp-routine-level], [data-vp-exercise-catalog-group], .filter-row select, .filter-row input')) saveControl(event.target);
  }, true);

  let timer = null;
  const observer = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(restoreFilters, 35);
  });

  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 50);
    observer.observe(app, { childList: true, subtree: true });
    restoreFilters();
  };

  start();
})();
