// Offline support. Bump VERSION whenever app files change so phones pick up the new version.
const VERSION = 'tm-2026-10-24-1';
const SHELL = ['./', 'index.html', 'config.js', 'manifest.webmanifest', 'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png',
  'fonts/fredoka.woff2', 'fonts/nunito.woff2', 'fonts/noto-serif-sc-500.woff2', 'fonts/noto-serif-sc-700.woff2',
  'content/lessons.json', 'content/items.json', 'content/audio.json', 'content/profile.json'];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const cache = await caches.open(VERSION);
    await cache.addAll(SHELL);
    try {
      const audio = await (await fetch('content/audio.json', {cache: 'no-cache'})).json();
      await cache.addAll([...new Set(Object.values(audio))]);
    } catch(err) { /* audio is cached as it plays instead */ }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for(const k of await caches.keys()) if(k !== VERSION) await caches.delete(k);
    await self.clients.claim();
  })());
});

// Safari asks for audio in byte ranges; answer them from the cached file.
async function ranged(req, res) {
  const range = req.headers.get('range');
  if(!range || !res || res.status !== 200) return res;
  const buf = await res.arrayBuffer();
  const m = /bytes=(\d*)-(\d*)/.exec(range) || [];
  const start = m[1] ? +m[1] : 0, end = m[2] ? Math.min(+m[2], buf.byteLength - 1) : buf.byteLength - 1;
  return new Response(buf.slice(start, end + 1), {status: 206, headers: {
    'Content-Type': res.headers.get('Content-Type') || 'audio/mp4', 'Content-Range': `bytes ${start}-${end}/${buf.byteLength}`,
    'Content-Length': String(end - start + 1), 'Accept-Ranges': 'bytes'}});
}

self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if(req.method !== 'GET' || url.origin !== location.origin) return;
  const fresh = req.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('index.html') || url.pathname.includes('/content/');
  if(fresh) {
    // Lessons and the page: network first so new lessons show up, cache when offline.
    e.respondWith(fetch(req).then(res => {
      if(res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(url.pathname.endsWith('/') || req.mode === 'navigate' ? './' : req, copy)); }
      return res;
    }).catch(async () => (await caches.match(req, {ignoreSearch: true})) || caches.match('./')));
    return;
  }
  e.respondWith((async () => {
    const plain = new Request(url.href.split('#')[0]);
    let res = await caches.match(plain, {ignoreSearch: true});
    if(!res) {
      res = await fetch(plain);
      if(res.ok) { const copy = res.clone(); (await caches.open(VERSION)).put(plain, copy); }
    }
    return url.pathname.includes('/audio/') ? ranged(req, res) : res;
  })());
});
