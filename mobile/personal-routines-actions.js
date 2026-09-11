(() => {
  'use strict';

  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  const STYLE_ID = 'vp-personal-routines-actions-style';
  let deleting = false;

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .vp-personal-routine-row{display:grid;grid-template-columns:minmax(0,1fr) 46px;gap:9px;align-items:stretch}
      .vp-personal-routine-row>.vp-personal-routine-card{min-width:0;width:100%}
      .vp-delete-personal-routine{display:grid;place-items:center;width:46px;min-width:46px;border:1px solid #f0cfd5;border-radius:14px;background:#fff7f8;color:#b3384b;cursor:pointer;box-shadow:0 4px 12px rgba(100,25,38,.04)}
      .vp-delete-personal-routine:active{transform:scale(.97)}
      .vp-delete-personal-routine svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
      .vp-routine-section[data-vp-section="add-exercise"] .vp-section-icon svg{width:22px!important;height:22px!important}
      @media(max-width:520px){.vp-personal-routine-row{grid-template-columns:minmax(0,1fr) 43px}.vp-delete-personal-routine{width:43px;min-width:43px}}
    `;
    document.head.appendChild(style);
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 2);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(STORE)) request.result.createObjectStore(STORE);
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async function readState() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readonly');
      const request = tx.objectStore(STORE).get('user');
      request.onsuccess = () => resolve(request.result || {});
      request.onerror = () => reject(request.error);
    });
  }

  async function writeState(state) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(state, 'user');
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  function setPlusIcon() {
    const icon = document.querySelector('.vp-routine-section[data-vp-section="add-exercise"] .vp-section-icon');
    if (!icon || icon.dataset.vpPurePlus === '1') return;
    icon.dataset.vpPurePlus = '1';
    icon.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
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

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'vp-delete-personal-routine';
      button.dataset.vpDeleteRoutine = card.dataset.id || '';
      button.setAttribute('aria-label', `Eliminar ${card.querySelector('b')?.textContent?.trim() || 'rutina personal'}`);
      button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg>';
      row.appendChild(button);
    });
  }

  async function deleteRoutine(id) {
    if (deleting || !id) return;
    deleting = true;
    try {
      const state = await readState();
      const routines = Array.isArray(state.routines) ? state.routines : [];
      const routine = routines.find(r => String(r.id) === String(id));
      if (!routine || routine.source !== 'custom-builder') {
        alert('Esta rutina no se puede eliminar desde Rutinas personales.');
        return;
      }

      const confirmed = window.confirm(`¿Eliminar la rutina “${routine.name || 'Rutina sin nombre'}”?\n\nEsta acción no se puede deshacer.`);
      if (!confirmed) return;

      const remaining = routines.filter(r => String(r.id) !== String(id));
      state.routines = remaining;

      if (String(state.activeRoutineId) === String(id)) {
        state.activeRoutineId = remaining[0]?.id ?? null;
      }

      if (state._draft && String(state._draft.routineId) === String(id)) {
        delete state._draft;
      }

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
    } catch (error) {
      console.error(error);
      alert('No se pudo eliminar la rutina. Inténtalo de nuevo.');
    } finally {
      deleting = false;
    }
  }

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-vp-delete-routine]');
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();
    deleteRoutine(button.dataset.vpDeleteRoutine);
  }, true);

  function apply() {
    injectStyles();
    setPlusIcon();
    addDeleteButtons();
  }

  apply();
  setTimeout(apply, 150);
  setTimeout(apply, 500);
  setTimeout(apply, 1000);

  const app = document.querySelector('#app');
  if (app) {
    const observer = new MutationObserver(() => {
      clearTimeout(window.__vpPersonalRoutineActionsTimer);
      window.__vpPersonalRoutineActionsTimer = setTimeout(apply, 70);
    });
    observer.observe(app, { childList: true, subtree: true });
  }
})();
