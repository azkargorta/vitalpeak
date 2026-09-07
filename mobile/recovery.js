(() => {
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

  async function recoverIfNeeded() {
    await wait(1200);
    const app = document.querySelector('#app');
    if (!app || app.children.length || app.textContent.trim()) return;

    try {
      await import('./app.js?v=22-recovery');
    } catch (error) {
      console.error('VitalPeak recovery failed', error);
      app.innerHTML = `
        <section style="padding:24px;margin:24px;background:#fff;border-radius:20px;color:#163a43;box-shadow:0 8px 24px rgba(0,0,0,.08)">
          <h2 style="margin:0 0 8px">No se ha podido iniciar VitalPeak</h2>
          <p style="margin:0 0 14px;color:#60757a">Cierra la app por completo y vuelve a abrirla. Tus datos guardados no se han borrado.</p>
          <button type="button" onclick="location.reload()" style="border:0;border-radius:14px;padding:12px 18px;background:#4fd6c1;color:#12343b;font-weight:800">Reintentar</button>
        </section>`;
    }
  }

  recoverIfNeeded();
})();
