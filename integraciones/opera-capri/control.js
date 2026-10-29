/* El código de las páginas nunca se convierte en comandos. */
(() => {
  const sitios = new Set(['www.youtube.com', 'youtube.com', 'm.youtube.com', 'www.youtube.cl', 'youtube.cl']);
  function esYouTube(url) {
    try { const u = new URL(url); return u.protocol === 'https:' && sitios.has(u.hostname); }
    catch { return false; }
  }
  const fallo = codigo => ({ok: false, codigo});
  function volumenPagina(doc, datos) {
    return new Promise(resolve => {
      const id = globalThis.crypto.randomUUID();
      let timer;
      const terminar = resultado => { clearTimeout(timer); doc.removeEventListener('capri:volumen:resultado', recibir); resolve(resultado); };
      const recibir = evento => {
        try {
          const respuesta = JSON.parse(evento.detail);
          if (respuesta.id === id) terminar(respuesta.resultado);
        } catch { /* Ignore unrelated events. */ }
      };
      doc.addEventListener('capri:volumen:resultado', recibir);
      timer = setTimeout(() => terminar({ok: false, codigo: 'sin_control'}), 1600);
      doc.dispatchEvent(new CustomEvent('capri:volumen:peticion', {detail: JSON.stringify({id, datos})}));
    });
  }
  async function ejecutar(doc, url, tarea) {
    if (!esYouTube(url)) return fallo('pagina_invalida');
    const {accion, datos = {}} = tarea;
    if (accion === 'resultado') {
      if (!Number.isInteger(datos.indice) || datos.indice < 1 || datos.indice > 10) return fallo('operacion_invalida');
      if (new URL(url).pathname !== '/results') return fallo('sin_resultados');
      const raiz = doc.querySelector('ytd-search') || doc.querySelector('ytm-search');
      if (!raiz) return fallo('sin_resultados');
      const vistos = new Set(), enlaces = [];
      const tarjetas = raiz.querySelectorAll('ytd-video-renderer, yt-lockup-view-model, ytd-rich-item-renderer, ytm-compact-video-renderer');
      for (const tarjeta of tarjetas) {
        // Los anuncios y estantes de Shorts no cuentan como vídeos ordinarios.
        if (tarjeta.closest('ytd-ad-slot-renderer, ytd-promoted-video-renderer, ytd-in-feed-ad-layout-renderer, ytd-reel-shelf-renderer, ytd-rich-shelf-renderer')) continue;
        for (const enlace of tarjeta.querySelectorAll('a[href]')) {
          let destino;
          try { destino = new URL(enlace.href, url); } catch { continue; }
          const id = destino.searchParams.get('v');
          if (!esYouTube(destino.href) || destino.pathname !== '/watch' || !id || !/^[\w-]+$/.test(id) || vistos.has(id)) continue;
          vistos.add(id);enlaces.push(enlace);break;
        }
      }
      const elegido = enlaces[datos.indice - 1];
      if (!elegido) return fallo('resultado_no_disponible');
      // Confirmamos la solicitud antes de que la navegación cierre el documento.
      setTimeout(() => elegido.click(), 50);
      return {ok: true, estado: 'Solicitado'};
    }
    if (['siguiente', 'anterior'].includes(accion)) {
      const selector = {siguiente: '.ytp-next-button', anterior: '.ytp-prev-button'}[accion];
      const boton = doc.querySelector(selector);
      if (!boton || boton.getAttribute('aria-disabled') === 'true' || boton.disabled) return fallo('sin_control');
      if (boton.href && !esYouTube(boton.href)) return fallo('sin_control');
      // Responder antes de una navegación que pudiera destruir este documento.
      setTimeout(() => boton.click(), 50);
      return {ok: true, estado: 'Solicitado'};
    }
    const video = doc.querySelector('#movie_player video.html5-main-video') || doc.querySelector('video.html5-main-video');
    if (!video || video.readyState === 0) return fallo('sin_video');
    if (accion === 'pausa') { video.pause(); return {ok: video.paused, estado: video.paused ? 'Paused' : 'Playing'}; }
    if (accion === 'reanudar') {
      try { await video.play(); return {ok: !video.paused, estado: video.paused ? 'Paused' : 'Playing'}; }
      catch { return fallo('reproduccion_bloqueada'); }
    }
    if (accion === 'estado') return {ok: true, estado: video.paused ? 'Paused' : 'Playing'};
    if (accion !== 'volumen') return fallo('operacion_invalida');
    return volumenPagina(doc, datos);
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {ejecutar, esYouTube};
  else globalThis.CapriVideo = {ejecutar, esYouTube};
})();
