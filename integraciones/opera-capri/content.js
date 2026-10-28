(() => {
  let ocupado = false;
  chrome.runtime.onMessage.addListener((m, sender, responder) => {
    if (sender.id !== chrome.runtime.id || m?.tipo !== 'capri_ejecutar') return false;
    CapriVideo.ejecutar(document, location.href, m.tarea).then(responder).catch(() => responder({ok: false, codigo: 'cambio_no_confirmado'}));
    return true;
  });
  async function consultar() {
    if (ocupado) return;
    ocupado = true;
    try { await chrome.runtime.sendMessage({tipo: 'capri_consultar'}); }
    catch { /* Capri puede estar cerrado o la extensión recién recargada. */ }
    finally { ocupado = false; }
  }
  setInterval(consultar, 700);
  consultar();
})();
