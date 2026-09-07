(() => {
  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';

  function openDB() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 2);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function repair() {
    try {
      const db = await openDB();
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      const req = store.get('user');
      const saved = await new Promise((resolve, reject) => {
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
      if (!saved || typeof saved !== 'object') return;

      const fixed = { ...saved };
      fixed.profile = fixed.profile && typeof fixed.profile === 'object' ? fixed.profile : { name: '' };
      fixed.routines = Array.isArray(fixed.routines) ? fixed.routines : [];
      fixed.sessions = Array.isArray(fixed.sessions) ? fixed.sessions : [];
      fixed.weights = Array.isArray(fixed.weights) ? fixed.weights : [];
      fixed.plan = fixed.plan && typeof fixed.plan === 'object' && !Array.isArray(fixed.plan) ? fixed.plan : {};
      fixed.goals = fixed.goals && typeof fixed.goals === 'object' ? fixed.goals : {};
      fixed.goals.exerciseGoals = fixed.goals.exerciseGoals && typeof fixed.goals.exerciseGoals === 'object' ? fixed.goals.exerciseGoals : {};
      fixed.sessions = fixed.sessions.map(s => ({ ...s, sets: Array.isArray(s?.sets) ? s.sets : [] }));
      fixed.routines = fixed.routines.filter(r => r && typeof r === 'object').map(r => ({
        ...r,
        days: Array.isArray(r.days) ? r.days.map((d, i) => ({
          ...d,
          name: d?.name || `Día ${i + 1}`,
          items: Array.isArray(d?.items) ? d.items.filter(Boolean) : []
        })) : []
      }));

      store.put(fixed, 'user');
      await new Promise((resolve, reject) => {
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
      });
    } catch (error) {
      console.error('VitalPeak state repair failed', error);
    }
  }

  window.VITALPEAK_STATE_REPAIR = repair();
})();
