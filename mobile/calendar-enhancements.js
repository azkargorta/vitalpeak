(() => {
  const DB_NAME = 'vitalpeak-mobile';
  const STORE = 'state';
  const DAY_COLORS = ['#D32F2F','#1976D2','#388E3C','#F57C00','#7B1FA2','#00838F','#C2185B','#5D4037','#455A64','#C49000'];

  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const colorFor = value => {
    const day = Math.max(0, Number(String(value || '').split('::')[1] || 0));
    return DAY_COLORS[day % DAY_COLORS.length];
  };

  async function readState() {
    return new Promise(resolve => {
      const req = indexedDB.open(DB_NAME, 2);
      req.onerror = () => resolve(null);
      req.onupgradeneeded = () => {
        if (!req.result.objectStoreNames.contains(STORE)) req.result.createObjectStore(STORE);
      };
      req.onsuccess = () => {
        const db = req.result;
        const tx = db.transaction(STORE, 'readonly');
        const get = tx.objectStore(STORE).get('user');
        get.onsuccess = () => resolve(get.result || null);
        get.onerror = () => resolve(null);
      };
    });
  }

  function ensureStyles() {
    if (document.querySelector('#vp-calendar-enhancement-styles')) return;
    const style = document.createElement('style');
    style.id = 'vp-calendar-enhancement-styles';
    style.textContent = `
      .vp-calendar-legend{display:flex;gap:7px;overflow-x:auto;padding:3px 0 12px;scrollbar-width:none}
      .vp-calendar-legend::-webkit-scrollbar{display:none}
      .vp-calendar-legend-item{flex:0 0 auto;display:flex;align-items:center;gap:7px;padding:8px 10px;border:1px solid #d8e7e3;border-radius:999px;background:#fff;color:#284950;font-size:12px;font-weight:800;white-space:nowrap}
      .vp-calendar-legend-dot{width:10px;height:10px;border-radius:50%;flex:0 0 10px}
      .mobile-month{gap:4px!important}
      .mobile-month .month-day{min-height:62px!important;border-radius:12px!important;padding:7px 2px!important;position:relative}
      .mobile-month .month-day b{font-size:14px!important}
      .calendar-dots{gap:4px!important;min-height:12px!important;max-width:100%}
      .calendar-dot{width:9px!important;height:9px!important;box-shadow:0 0 0 1px rgba(255,255,255,.95)}
      .vp-calendar-count{position:absolute;right:4px;bottom:4px;min-width:17px;height:17px;padding:0 4px;border-radius:9px;background:#eef5f3;color:#557076;font-size:10px;line-height:17px;font-weight:900;text-align:center}
      .selected-day-panel{margin-top:14px!important}
      .day-workout-card{border-top:0!important;margin-top:8px;padding:12px!important;border:1px solid #e1ece9!important;border-radius:14px!important;background:#fbfefd}
      .day-workout-color{width:7px!important}
      @media(max-width:390px){.mobile-month{gap:3px!important}.mobile-month .month-day{min-height:58px!important}.calendar-dot{width:8px!important;height:8px!important}}
    `;
    document.head.appendChild(style);
  }

  function routineById(state, id) {
    return (state?.routines || []).find(r => String(r.id) === String(id)) || null;
  }

  function entryLabel(state, value) {
    const [id, dayRaw] = String(value || '').split('::');
    const day = Number(dayRaw || 0);
    const routine = routineById(state, id);
    const dayName = routine?.days?.[day]?.name || `Día ${day + 1}`;
    return routine ? `${routine.name} · ${dayName}` : dayName;
  }

  function legendEntries(state, monthPrefix) {
    const program = routineById(state, state?.plannerProgramId);
    if (program?.days?.length) {
      return program.days.map((day, index) => ({
        value: `${program.id}::${index}`,
        label: day.name || `Día ${index + 1}`,
      }));
    }
    const found = [];
    const seen = new Set();
    for (const [date, raw] of Object.entries(state?.plan || {})) {
      if (!date.startsWith(monthPrefix)) continue;
      const entries = Array.isArray(raw) ? raw : raw ? [raw] : [];
      for (const value of entries) {
        if (seen.has(value)) continue;
        seen.add(value);
        found.push({ value, label: entryLabel(state, value) });
      }
    }
    return found.slice(0, 10);
  }

  async function enhance() {
    const calendar = document.querySelector('.month-calendar.mobile-month');
    if (!calendar) return;
    ensureStyles();
    const state = await readState();
    if (!state || !document.body.contains(calendar)) return;

    const firstDate = calendar.querySelector('[data-date]')?.dataset.date || '';
    const monthPrefix = firstDate.slice(0, 7);

    for (const day of calendar.querySelectorAll('.month-day[data-date]')) {
      const date = day.dataset.date;
      const raw = state.plan?.[date];
      const entries = Array.isArray(raw) ? raw : raw ? [raw] : [];
      const dots = [...day.querySelectorAll('.calendar-dot')];
      dots.forEach((dot, index) => {
        const value = entries[index];
        if (value) dot.style.background = colorFor(value);
      });
      day.querySelector('.vp-calendar-count')?.remove();
      if (entries.length > 1) {
        const count = document.createElement('span');
        count.className = 'vp-calendar-count';
        count.textContent = String(entries.length);
        day.appendChild(count);
      }
      const labels = entries.map(v => entryLabel(state, v));
      day.setAttribute('aria-label', labels.length ? `${date}: ${labels.join(', ')}` : `${date}: día libre`);
    }

    for (const card of document.querySelectorAll('.day-workout-card')) {
      const action = card.querySelector('[data-value]');
      const value = action?.dataset.value;
      const stripe = card.querySelector('.day-workout-color');
      if (stripe && value) stripe.style.setProperty('--workout-color', colorFor(value));
    }

    let legend = document.querySelector('#vp-calendar-legend');
    if (!legend) {
      legend = document.createElement('div');
      legend.id = 'vp-calendar-legend';
      legend.className = 'vp-calendar-legend';
      calendar.parentNode.insertBefore(legend, calendar);
    }
    const entries = legendEntries(state, monthPrefix);
    legend.innerHTML = entries.map(item => `<span class="vp-calendar-legend-item"><i class="vp-calendar-legend-dot" style="background:${colorFor(item.value)}"></i>${esc(item.label)}</span>`).join('');
    legend.hidden = entries.length === 0;
  }

  const observer = new MutationObserver(() => enhance());
  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 50);
    observer.observe(app, { childList: true, subtree: true });
    enhance();
  };
  start();
})();
