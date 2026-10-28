(() => {
  let ocupado = false;
  chrome.runtime.onMessage.addListener((m, sender, responder) => {
    if (sender.id !== chrome.runtime.id) return false;
    if (m?.tipo === 'capri_estado') {
      const v = document.querySelector('#movie_player video.html5-main-video');
      responder({video: !!v && v.readyState > 0, reproduciendo: !!v && !v.paused && !v.ended});
      return false;
    }
    if (m?.tipo !== 'capri_ejecutar') return false;
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
