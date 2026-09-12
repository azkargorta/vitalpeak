(() => {
  'use strict';

  const RELOAD_KEY = 'vitalpeak:routines-clean-entry';
  let bypassReload = false;

  function routinesButton(){
    return document.querySelector('.tabbar [data-route="routines"]');
  }

  function routinesActive(){
    return !!routinesButton()?.classList.contains('active');
  }

  function requestCleanEntry(){
    try { sessionStorage.setItem(RELOAD_KEY, '1'); } catch {}
    location.reload();
  }

  // Intercepta únicamente entradas a Rutinas desde otra pestaña. El objetivo es
  // que el DOM de Rutinas siempre se monte desde cero, igual que en la primera
  // carga de la app, evitando reutilizar una vista antigua ya transformada.
  document.addEventListener('click', e => {
    const button = e.target.closest('.tabbar [data-route="routines"]');
    if (!button || bypassReload || routinesActive()) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    requestCleanEntry();
  }, true);

  // Después de la recarga, todos los módulos de Rutinas ya están cargados porque
  // este controlador se inserta al final del cargador secuencial. Abrimos la ruta
  // una sola vez y anulamos temporalmente la recarga para no crear un bucle.
  let shouldOpen = false;
  try {
    shouldOpen = sessionStorage.getItem(RELOAD_KEY) === '1';
    if (shouldOpen) sessionStorage.removeItem(RELOAD_KEY);
  } catch {}

  if (shouldOpen) {
    const open = () => {
      const button = routinesButton();
      if (!button) return setTimeout(open, 30);
      bypassReload = true;
      button.click();
      queueMicrotask(() => { bypassReload = false; });
    };
    setTimeout(open, 0);
  }
})();
