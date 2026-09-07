(() => {
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  async function importPatchedApp() {
    const response = await fetch('./app.js?v=24-recovery', { cache: 'no-store' });
    if (!response.ok) throw new Error(`No se pudo cargar app.js (${response.status})`);
    let source = await response.text();

    // El archivo base referencia renderTemplate, pero esa función se perdió en una modificación anterior.
    // Para recuperar el arranque sin tocar los datos del usuario, hacemos que esa ruta vuelva a Rutinas
    // hasta restaurar la vista de detalle de plantilla de forma definitiva.
    source = source.replace(
      'template:renderTemplate',
      'template:(typeof renderTemplate==="function"?renderTemplate:renderRoutines)'
    );

    const blob = new Blob([source], { type: 'text/javascript' });
    const url = URL.createObjectURL(blob);
    try {
      await import(url);
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async function recoverIfNeeded() {
    await wait(1200);
    const app = document.querySelector('#app');
    if (!app || app.children.length || app.textContent.trim()) return;

    try {
      if (window.VITALPEAK_STATE_REPAIR) await window.VITALPEAK_STATE_REPAIR;
      await importPatchedApp();
    } catch (error) {
      console.error('VitalPeak recovery failed', error);
      const message = String(error?.message || error || 'Error desconocido');
      app.innerHTML = `
        <section style="padding:24px;margin:24px;background:#fff;border-radius:20px;color:#163a43;box-shadow:0 8px 24px rgba(0,0,0,.08)">
          <h2 style="margin:0 0 8px">No se ha podido iniciar VitalPeak</h2>
          <p style="margin:0 0 14px;color:#60757a">No se han borrado tus datos. Cierra la app por completo y vuelve a abrirla después de que termine la actualización.</p>
          <p style="margin:0 0 14px;padding:10px;border-radius:10px;background:#f4f7f6;color:#52666b;font-size:12px;word-break:break-word"><b>Error:</b> ${escapeHtml(message)}</p>
          <button type="button" onclick="location.reload()" style="border:0;border-radius:14px;padding:12px 18px;background:#4fd6c1;color:#12343b;font-weight:800">Reintentar</button>
        </section>`;
    }
  }

  recoverIfNeeded();
})();
