(() => {
  'use strict';
  let running = false;

  function ensureStyles() {
    if (document.querySelector('#vp-routines-accordion-styles')) return;
    const style = document.createElement('style');
    style.id = 'vp-routines-accordion-styles';
    style.textContent = `
      .vp-routines-accordion{display:grid;gap:10px;margin-top:16px}
      .vp-routine-section{border:1px solid #d8e7e3;border-radius:16px;background:#fff;overflow:hidden;box-shadow:0 5px 16px rgba(16,46,56,.04)}
      .vp-routine-section>summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:58px;padding:15px 16px;cursor:pointer;font-size:16px;font-weight:900;color:#163a43;user-select:none}
      .vp-routine-section>summary::-webkit-details-marker{display:none}
      .vp-routine-section>summary::after{content:'⌄';display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:#edf7f4;color:#176d61;font-size:18px;transition:transform .18s ease}
      .vp-routine-section[open]>summary::after{transform:rotate(180deg)}
      .vp-routine-section[open]>summary{border-bottom:1px solid #e2ece9}
      .vp-routine-section-content{padding:14px 14px 16px}
      .vp-routine-section-content>.section-head{display:none!important}
      .vp-routine-section-content>.vp-custom-exercises{margin-top:0!important;padding-top:0!important;border-top:0!important}
      .vp-routine-section-content>.vp-custom-exercises>h3,
      .vp-routine-section-content>.vp-custom-exercises>p{display:none!important}
      .vp-routine-section-content>.filter-row{margin-top:0}
      .vp-routine-section-content>.exercise-grid{margin-top:0}
      @media(max-width:480px){
        .vp-routine-section>summary{min-height:56px;padding:14px;font-size:15px}
        .vp-routine-section-content{padding:12px}
      }
    `;
    document.head.appendChild(style);
  }

  function sectionHead(app, text) {
    return [...app.querySelectorAll('.section-head')].find(x => x.querySelector('h2')?.textContent.trim() === text) || null;
  }

  function collectUntilNextHead(start) {
    const nodes = [];
    let node = start?.nextElementSibling || null;
    while (node && !node.classList?.contains('section-head')) {
      nodes.push(node);
      node = node.nextElementSibling;
    }
    return nodes;
  }

  function makeDetails(title, nodes) {
    const details = document.createElement('details');
    details.className = 'vp-routine-section';
    details.innerHTML = `<summary>${title}</summary><div class="vp-routine-section-content"></div>`;
    const body = details.querySelector('.vp-routine-section-content');
    nodes.forEach(node => body.appendChild(node));
    return details;
  }

  function enhance() {
    if (running) return;
    const app = document.querySelector('#app');
    if (!app || !app.textContent.includes('RUTINAS') || app.querySelector('#vp-routines-accordion')) return;

    const customHead = sectionHead(app, 'Rutina personalizada');
    const predefinedHead = sectionHead(app, 'Planes preparados');
    const exercisesHead = sectionHead(app, 'Catálogo de ejercicios');
    const customBuilder = app.querySelector('#vp-custom-routine-builder');
    const customExerciseBlock = app.querySelector('.vp-custom-exercises');

    if (!customHead || !predefinedHead || !exercisesHead || !customBuilder || !customExerciseBlock) return;

    running = true;
    try {
      ensureStyles();

      const customCard = customBuilder.closest('.card');
      const predefinedNodes = collectUntilNextHead(predefinedHead);
      const exerciseNodes = collectUntilNextHead(exercisesHead);

      // Extraemos "Mis ejercicios" del constructor para convertirlo en un apartado independiente.
      customExerciseBlock.remove();

      const accordion = document.createElement('div');
      accordion.id = 'vp-routines-accordion';
      accordion.className = 'vp-routines-accordion';

      accordion.appendChild(makeDetails('Crea tu propia rutina', [customCard]));
      accordion.appendChild(makeDetails('Rutinas predefinidas', predefinedNodes));
      accordion.appendChild(makeDetails('Ejercicios predefinidos', exerciseNodes));
      accordion.appendChild(makeDetails('Añade tu ejercicio', [customExerciseBlock]));

      // Los títulos originales ya no son necesarios una vez agrupado el contenido.
      customHead.remove();
      predefinedHead.remove();
      exercisesHead.remove();

      const activeHead = sectionHead(app, 'Tu rutina activa');
      const activeBlock = activeHead?.nextElementSibling;
      if (activeBlock) activeBlock.insertAdjacentElement('afterend', accordion);
      else {
        const hero = app.querySelector('.hero');
        hero?.insertAdjacentElement('afterend', accordion);
      }
    } finally {
      running = false;
    }
  }

  let timer = null;
  const start = () => {
    const app = document.querySelector('#app');
    if (!app) return setTimeout(start, 60);
    new MutationObserver(() => {
      clearTimeout(timer);
      timer = setTimeout(enhance, 60);
    }).observe(app, { childList: true, subtree: true });
    enhance();
  };
  start();
})();
