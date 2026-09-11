(() => {
  'use strict';
  if (!('serviceWorker' in navigator)) return;
  window.addEventListener('load', async () => {
    try {
      const reg = await navigator.serviceWorker.register('./sw.js?v=74', {
        scope: './',
        updateViaCache: 'none'
      });
      await reg.update().catch(() => {});
      if (reg.waiting) reg.waiting.postMessage?.({ type: 'SKIP_WAITING' });
    } catch (err) {
      console.warn('VitalPeak SW refresh error', err);
    }
  });
})();
