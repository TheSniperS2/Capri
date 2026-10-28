/* Contexto de la página: volumen y silencio deben actualizar el modelo de YouTube. */
(() => {
  const PETICION = 'capri:volumen:peticion';
  const RESPUESTA = 'capri:volumen:resultado';
  const fallo = codigo => ({ok: false, codigo});
  async function aplicar(doc, url, datos) {
    let u;
    try { u = new URL(url); } catch { return fallo('pagina_invalida'); }
    if (u.protocol !== 'https:' || !['www.youtube.com', 'youtube.com', 'm.youtube.com', 'www.youtube.cl', 'youtube.cl'].includes(u.hostname)) return fallo('pagina_invalida');
    const p = doc.getElementById('movie_player');
    const video = doc.querySelector('#movie_player video.html5-main-video');
    if (!video || video.readyState === 0) return fallo('sin_video');
    if (!p || !['setVolume', 'getVolume', 'mute', 'unMute', 'isMuted'].every(k => typeof p[k] === 'function')) return fallo('sin_control');
    const anterior = Number(p.getVolume());
    if (!Number.isFinite(anterior) || anterior < 0 || anterior > 100) return fallo('cambio_no_confirmado');
    let destino = anterior, silenciado = Boolean(p.isMuted());
    const op = datos?.operacion;
    const m = typeof op === 'string' && /^(subir|bajar|fijar):(\d{1,3})$/.exec(op);
    if (m) {
      const n = Number(m[2]);
      if (n > 100) return fallo('operacion_invalida');
      destino = m[1] === 'fijar' ? n : Math.max(0, Math.min(100, anterior + (m[1] === 'subir' ? n : -n)));
      p.setVolume(destino);
      // Un nivel positivo pide sonido; cero pide silencio.
      if (destino > 0) { p.unMute(); silenciado = false; }
      else { p.mute(); silenciado = true; }
    } else if (op === 'silenciar') {
      p.mute(); silenciado = true;
    } else if (op === 'activar') {
      if (typeof datos.restaurar !== 'number' || !Number.isFinite(datos.restaurar) || datos.restaurar < 0 || datos.restaurar > 100) return fallo('operacion_invalida');
      if (anterior === 0) { destino = datos.restaurar; p.setVolume(destino); }
      p.unMute(); silenciado = false;
    } else if (op !== 'consultar') return fallo('operacion_invalida');
    // Reconciliar una desincronización que pudiera venir de la versión anterior.
    if (op !== 'consultar' && Boolean(p.isMuted()) === silenciado && Boolean(video.muted) !== silenciado) video.muted = silenciado;
    function coherente(nivel, mute) {
      if (!Number.isFinite(nivel) || Math.abs(nivel - destino) > 1 || mute !== silenciado || Boolean(video.muted) !== mute) return false;
      const boton = doc.querySelector('.ytp-mute-button');
      const etiqueta = String(boton?.getAttribute('aria-label') || boton?.getAttribute('title') || '').toLowerCase();
      const indicaSilencio = /^(unmute|activar (?:el )?(?:sonido|audio)|quitar (?:el )?silencio|desactivar (?:el )?silencio)\b/.test(etiqueta);
      const indicaSonido = /^(mute|silenciar|desactivar (?:el )?sonido)\b/.test(etiqueta);
      const silencioEfectivo = mute || nivel === 0;
      if ((!silencioEfectivo && indicaSilencio) || (silencioEfectivo && indicaSonido)) return false;
      const slider = doc.querySelector('.ytp-volume-slider[role="slider"]');
      const valor = slider?.getAttribute('aria-valuenow');
      const min = Number(slider?.getAttribute('aria-valuemin') ?? 0), max = Number(slider?.getAttribute('aria-valuemax') ?? 100);
      if (!mute && valor != null && Number.isFinite(Number(valor)) && max > min && Math.abs(100 * (Number(valor) - min) / (max - min) - destino) > 1) return false;
      return true;
    }
    const vence = Date.now() + 650;
    do {
      const volumen = Number(p.getVolume()), mute = Boolean(p.isMuted());
      if (coherente(volumen, mute)) return {ok: true, volumen, anterior, silenciado: mute};
      if (Date.now() >= vence) break;
      await new Promise(resolve => setTimeout(resolve, 50));
    } while (true);
    return fallo('cambio_no_confirmado');
  }
  function conectar(doc, obtenerUrl) {
    const recibir = async evento => {
      try {
        if (typeof evento.detail !== 'string' || evento.detail.length > 1024) return;
        const {id, datos} = JSON.parse(evento.detail);
        if (typeof id !== 'string' || !/^[a-f0-9-]{20,64}$/.test(id)) return;
        let resultado;
        try { resultado = await aplicar(doc, obtenerUrl(), datos); }
        catch { resultado = fallo('cambio_no_confirmado'); }
        doc.dispatchEvent(new CustomEvent(RESPUESTA, {detail: JSON.stringify({id, resultado})}));
      } catch { /* Mensajes ajenos o incompletos no son órdenes. */ }
    };
    doc.addEventListener(PETICION, recibir);
    return () => doc.removeEventListener(PETICION, recibir);
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {aplicar, conectar};
  else conectar(document, () => location.href);
})();
