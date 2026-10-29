const BASE = 'http://127.0.0.1:18741';
const CABECERAS = {'X-Capri-Puente': chrome.runtime.id};
let ocupado = false, ultimo = null;
function esYouTube(url) {
  try { const u = new URL(url); return u.protocol === 'https:' && ['www.youtube.com', 'youtube.com', 'm.youtube.com', 'www.youtube.cl', 'youtube.cl'].includes(u.hostname); }
  catch { return false; }
}
chrome.runtime.onMessage.addListener((m, sender, responder) => {
  if (sender.id !== chrome.runtime.id || m?.tipo !== 'capri_consultar' || !sender.tab || !esYouTube(sender.url)) return false;
  (async () => {
    if (ocupado) return;
    ocupado = true;
    try {
    const r = await fetch(BASE + '/siguiente', {headers: CABECERAS, signal: AbortSignal.timeout(1200)});
    if (!r.ok) return;
    const {tarea} = await r.json();
    if (!tarea) return;
    let resultado;
    try {
      const tabs = (await chrome.tabs.query({})).filter(t => esYouTube(t.url));
      const estados = await Promise.all(tabs.map(async t => {
        try { return {...t, ...await chrome.tabs.sendMessage(t.id, {tipo: 'capri_estado'})}; }
        catch { return {...t, video: false}; }
      }));
      const videos = estados.filter(t => t.video === true);
      const sonando = videos.filter(t => t.reproduciendo === true);
      const activas = await chrome.tabs.query({active: true, lastFocusedWindow: true});
      const activa = activas.length === 1 ? activas[0].id : null;
      // El foco de otra página nunca impide controlar el vídeo en segundo plano.
      let destino = sonando.length === 1 ? sonando[0] : null;
      if (sonando.length > 1) destino = sonando.find(t => t.id === activa);
      if (!sonando.length) destino = videos.find(t => t.id === ultimo) ||
        videos.find(t => t.id === activa) || (videos.length === 1 ? videos[0] : null);
      let sinDestino = videos.length > 1 ? 'varios_videos' : 'sin_video';
      if (tarea.accion === 'resultado') {
        const busquedas = estados.filter(t => t.resultados === true && new URL(t.url).pathname === '/results');
        destino = busquedas.find(t => t.id === activa) || (busquedas.length === 1 ? busquedas[0] : null);
        sinDestino = busquedas.length > 1 ? 'varios_resultados' : 'sin_resultados';
      }
      if (!destino) resultado = {ok: false, codigo: sinDestino};
      else {
        resultado = await chrome.tabs.sendMessage(destino.id, {tipo: 'capri_ejecutar', tarea});
        if (resultado?.ok) ultimo = destino.id;
      }
    }
    catch { resultado = {ok: false, codigo: 'cambio_no_confirmado'}; }
    await fetch(BASE + '/resultado', {method: 'POST', headers: {...CABECERAS, 'Content-Type': 'application/json'},
      body: JSON.stringify({id: tarea.id, resultado}), signal: AbortSignal.timeout(1200)});
    } finally { ocupado = false; }
  })().then(() => responder({ok: true})).catch(() => responder({ok: false}));
  return true;
});
