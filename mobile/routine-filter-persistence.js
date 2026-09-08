(() => {
  'use strict';

  const STORAGE_KEY = 'vitalpeak:routine-filter-state-v2';
  let restoring = false;
  let timer = null;

  const readState = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch { return {}; }
  };

  const writeState = state => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch {}
  };

  function controlKey(el) {
    if (!el) return '';
    if (el.id === 'template-days') return 'template-days';
    if (el.matches('[data-vp-routine-level]')) return 'routine-level';
    if (el.matches('[data-vp-exercise-catalog-group]')) return 'exercise-group';
    if (el.matches('[data-vp-exercise-catalog-search]')) return 'exercise-search';
    return '';
  }

  function saveControl(el) {
    if (restoring) return;
    const key = controlKey(el);
    if (!key) return;
    const state = readState();
    state[key] = el.value;
    writeState(state);
  }

  function snapshot() {
    if (restoring) return;
    const state = readState();
    document.querySelectorAll('#template-days,[data-vp-routine-level],[data-vp-exercise-catalog-group],[data-vp-exercise-catalog-search]').forEach(el => {
      const key = controlKey(el);
      if (key) state[key] = el.value;
    });
    writeState(state);
  }

  function restoreFilters() {
    const app = document.querySelector('#app');
    if (!app || !app.textContent.includes('RUTINAS')) return;
    const state = readState();
    const controls = app.querySelectorAll('#template-days,[data-vp-routine-level],[data-vp-exercise-catalog-group],[data-vp-exercise-catalog-search]');

    restoring = true;
    controls.forEach(el => {
      const key = controlKey(el);
      if (!key || !(key in state)) return;
      const wanted = String(state[key] ?? '');
      if (String(el.value) === wanted) return;
      el.value = wanted;
      const eventType = el.matches('input[type="search"],input[type="text"]') ? 'input' : 'change';
      el.dispatchEvent(new Event(eventType, { bubbles: true }));
    });
    restoring = false;
  }

  function scheduleRestore(delay=40) {
    clearTimeout(timer);
    timer = setTimeout(restoreFilters, delay);
  }

  document.addEventListener('input', event => {
    if (controlKey(event.target)) saveControl(event.target);
  }, true);

  document.addEventListener('change', event => {
    if (controlKey(event.target)) saveControl(event.target);
  }, true);

  document.addEventListener('click', event => {
    if (event.target.closest('[data-action="view-template"],[data-action="exercise-detail"],[data-vp-action="view-personal-routine"]')) snapshot();
    if (event.target.closest('[data-route="routines"],.exercise-close')) scheduleRestore(80);
  }, true);

  window.addEventListener('pagehide', snapshot);

  const observer = new MutationObserver(() => scheduleRestore(45));
  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 50);
    observer.observe(app, { childList: true, subtree: true });
    scheduleRestore(0);
  };

  start();
})();
