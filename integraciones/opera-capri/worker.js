const BASE = 'http://127.0.0.1:18741';
const CABECERAS = {'X-Capri-Puente': chrome.runtime.id};
function esYouTube(url) {
  try { const u = new URL(url); return u.protocol === 'https:' && ['www.youtube.com', 'youtube.com', 'm.youtube.com', 'www.youtube.cl', 'youtube.cl'].includes(u.hostname); }
  catch { return false; }
}
chrome.runtime.onMessage.addListener((m, sender, responder) => {
  if (sender.id !== chrome.runtime.id || m?.tipo !== 'capri_consultar' || !sender.tab || !esYouTube(sender.url)) return false;
  (async () => {
    const tabs = await chrome.tabs.query({active: true, lastFocusedWindow: true});
    if (tabs.length !== 1 || tabs[0].id !== sender.tab.id || !esYouTube(tabs[0].url)) return;
    const r = await fetch(BASE + '/siguiente', {headers: CABECERAS, signal: AbortSignal.timeout(1200)});
    if (!r.ok) return;
    const {tarea} = await r.json();
    if (!tarea) return;
    let resultado;
    try { resultado = await chrome.tabs.sendMessage(sender.tab.id, {tipo: 'capri_ejecutar', tarea}); }
    catch { resultado = {ok: false, codigo: 'cambio_no_confirmado'}; }
    await fetch(BASE + '/resultado', {method: 'POST', headers: {...CABECERAS, 'Content-Type': 'application/json'},
      body: JSON.stringify({id: tarea.id, resultado}), signal: AbortSignal.timeout(1200)});
  })().then(() => responder({ok: true})).catch(() => responder({ok: false}));
  return true;
});
