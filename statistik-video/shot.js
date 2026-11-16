// Einzelbilder zur Kontrolle: OUT=ordner node shot.js land|port t1 t2 ...
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [fmt, ...ts] = process.argv.slice(2);
  const [w, h] = fmt === 'port' ? [1080, 1920] : [1920, 1080];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: w, height: h } });
  p.on('pageerror', e => console.log('FEHLER', e.message));
  await p.goto('file://' + path.join(__dirname, 'index.html') + `?render=1&fmt=${fmt}`);
  await p.waitForFunction('window.READY');
  for (const t of ts) {
    await p.evaluate(t => { seek(t); return new Promise(r => requestAnimationFrame(() => r())); }, +t);
    await p.screenshot({ path: `${process.env.OUT || '.'}/${fmt}_${String(Math.round(t * 10)).padStart(5, '0')}.jpg`, quality: 80, type: 'jpeg' });
  }
  await b.close();
})();
