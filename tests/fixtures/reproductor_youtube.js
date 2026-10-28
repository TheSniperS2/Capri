if (typeof CustomEvent === 'undefined') globalThis.CustomEvent = class extends Event {
  constructor(tipo, opciones) { super(tipo); this.detail = opciones.detail; }
};
function crear({volumen = .4, silenciado = false} = {}) {
  const video = {readyState: 4, volume: volumen, muted: silenciado, paused: false,
    pause() { this.paused = true; }, async play() { this.paused = false; }};
  let nivel = volumen * 100, mute = silenciado;
  const player = {
    setVolume(v) { nivel = v; video.volume = v / 100; }, getVolume() { return nivel; },
    mute() { mute = true; video.muted = true; }, unMute() { mute = false; video.muted = false; }, isMuted() { return mute; }
  };
  const boton = {getAttribute: () => mute || nivel === 0 ? 'Activar sonido (m)' : 'Silenciar (m)'};
  const slider = {getAttribute: n => n === 'aria-valuemin' ? '0' : n === 'aria-valuemax' ? '100' : String(nivel)};
  const doc = new EventTarget();
  doc.getElementById = id => id === 'movie_player' ? player : null;
  doc.querySelector = s => s.includes('video.html5-main-video') ? video : s === '.ytp-mute-button' ? boton : s === '.ytp-volume-slider[role="slider"]' ? slider : null;
  const pagina = require('../../integraciones/opera-capri/page.js');
  const desconectar = pagina.conectar(doc, () => 'https://www.youtube.com/watch?v=prueba');
  return {video, doc, player, boton, slider, desconectar, pagina};
}
module.exports = {crear};
