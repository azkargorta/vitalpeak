(() => {
  'use strict';

  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  let busy = false;

  function injectStyles() {
    if (document.querySelector('#vp-routines-polish-styles')) return;
    const style = document.createElement('style');
    style.id = 'vp-routines-polish-styles';
    style.textContent = `
      .vp-personal-routine-row{display:grid;grid-template-columns:minmax(0,1fr) 44px;gap:8px;align-items:stretch}
      .vp-personal-routine-row .vp-personal-routine-card{min-width:0}
      .vp-delete-personal-routine{display:grid;place-items:center;width:44px;min-width:44px;border:1px solid #f1cfd5;border-radius:14px;background:#fff5f6;color:#b33b4e;cursor:pointer}
      .vp-delete-personal-routine:active{transform:scale(.97)}
      .vp-delete-personal-routine svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
      .vp-routines-coach.vp-smart-teaser{margin-top:0!important}
      .vp-routines-coach.vp-smart-teaser .vp-smart-open{width:100%;grid-column:1/-1}
      .vp-routines-coach.vp-smart-teaser .vp-smart-icon{align-self:start}
      @media(max-width:520px){.vp-personal-routine-row{grid-template-columns:minmax(0,1fr) 42px}.vp-delete-personal-routine{width:42px;min-width:42px}}
    `;
    document.head.appendChild(style);
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const r = indexedDB.open(DB_NAME, 2);
      r.onupgradeneeded = () => {
        if (!r.result.objectStoreNames.contains(STORE)) r.result.createObjectStore(STORE);
      };
      r.onsuccess = () => resolve(r.result);
      r.onerror = () => reject(r.error);
    });
  }

  async function readState() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const req = tx.objectStore(STORE).get('user');
      req.onsuccess = () => resolve(req.result || {});
      req.onerror = () => reject(req.error);
    });
  }

  async function writeState(state) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(state, 'user');
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  }

  function moveCoachIntoPlace() {
    const app = document.querySelector('#app');
    const hero = app?.querySelector('.hero');
    const teaser = document.querySelector('#vp-smart-generator .vp-smart-teaser') || document.querySelector('.vp-smart-teaser');
    if (!app || !hero || !teaser) return;

    teaser.classList.add('vp-routines-coach');
    if (hero.nextElementSibling !== teaser) hero.insertAdjacentElement('afterend', teaser);

    const formCard = document.querySelector('.vp-smart-form-card');
    if (formCard && teaser.nextElementSibling !== formCard) teaser.insertAdjacentElement('afterend', formCard);

    const generator = document.querySelector('#vp-smart-generator');
    if (generator && !generator.children.length) generator.remove();
  }

  function fixAddExerciseIcon() {
    const icon = document.querySelector('.vp-routine-section[data-vp-section="add-exercise"] .vp-section-icon');
    if (!icon || icon.dataset.vpFixedIcon === '1') return;
    icon.dataset.vpFixedIcon = '1';
    icon.innerHTML = '<svg viewBox="0 0 30 24" aria-hidden="true"><path d="M3 10v4m3-6v8m10-8v8m3-6v4M6 12h10"/><path d="M24 3v6m-3-3h6"/></svg>';
  }

  function addDeleteButtons() {
    const list = document.querySelector('.vp-routine-section[data-vp-section="personal-routines"] .vp-personal-routines-list');
    if (!list) return;

    [...list.querySelectorAll('.vp-personal-routine-card[data-id]')].forEach(card => {
      if (card.closest('.vp-personal-routine-row')) return;
      const row = document.createElement('div');
      row.className = 'vp-personal-routine-row';
      card.parentNode.insertBefore(row, card);
      row.appendChild(card);

      const del = document.createElement('button');
      del.type = 'button';
      del.className = 'vp-delete-personal-routine';
      del.dataset.vpDeleteRoutine = card.dataset.id;
      del.setAttribute('aria-label', `Eliminar ${card.querySelector('b')?.textContent || 'rutina'}`);
      del.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg>';
      row.appendChild(del);
    });
  }

  async function deletePersonalRoutine(id) {
    if (busy) return;
    busy = true;
    try {
      const state = await readState();
      const routines = Array.isArray(state.routines) ? state.routines : [];
      const target = routines.find(r => String(r.id) === String(id));
      if (!target || target.source !== 'custom-builder') return;

      const ok = window.confirm(`¿Eliminar la rutina “${target.name || 'Rutina sin nombre'}”?\n\nEsta acción no se puede deshacer.`);
      if (!ok) return;

      const remaining = routines.filter(r => String(r.id) !== String(id));
      state.routines = remaining;

      if (String(state.activeRoutineId) === String(id)) {
        state.activeRoutineId = remaining[0]?.id ?? null;
      }

      if (state._draft && String(state._draft.routineId) === String(id)) delete state._draft;

      if (state.plan && typeof state.plan === 'object') {
        for (const [date, raw] of Object.entries(state.plan)) {
          if (Array.isArray(raw)) {
            const filtered = raw.filter(value => String(value).split('::')[0] !== String(id));
            if (filtered.length) state.plan[date] = filtered;
            else delete state.plan[date];
          } else if (String(raw).split('::')[0] === String(id)) {
            delete state.plan[date];
          }
        }
      }

      await writeState(state);
      location.reload();
    } catch (err) {
      console.error(err);
      alert('No se pudo eliminar la rutina. Inténtalo de nuevo.');
    } finally {
      busy = false;
    }
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-vp-delete-routine]');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    deletePersonalRoutine(button.dataset.vpDeleteRoutine);
  }, true);

  function apply() {
    injectStyles();
    moveCoachIntoPlace();
    fixAddExerciseIcon();
    addDeleteButtons();
  }

  apply();
  setTimeout(apply, 120);
  setTimeout(apply, 420);
  setTimeout(apply, 900);

  const root = document.querySelector('#app');
  if (root) {
    const observer = new MutationObserver(() => {
      clearTimeout(window.__vpRoutinesPolishTimer);
      window.__vpRoutinesPolishTimer = setTimeout(apply, 45);
    });
    observer.observe(root, { childList: true, subtree: true });
  }
})();
