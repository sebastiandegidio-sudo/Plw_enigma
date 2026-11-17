// Kontrollbilder: OUT=ordner node shot.js land|port [t1 t2 ...]   (ohne Zeiten: je ein Bild kurz vor Ende jeder Szene)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  let [fmt, ...ts] = process.argv.slice(2);
  const [w, h] = fmt === 'port' ? [1080, 1920] : [1920, 1080];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: w, height: h } });
  p.on('pageerror', e => console.log('FEHLER', e.message));
  await p.goto('file://' + path.join(__dirname, 'index.html') + `?render=1&fmt=${fmt}`);
  await p.waitForFunction('window.READY');
  if (!ts.length) ts = await p.evaluate(() => ST.map((s, i) => +(s + LEN[i] * 2.4 - 1.3).toFixed(1)));
  let n = 0;
  for (const t of ts) {
    await p.evaluate(t => { seek(t); return new Promise(r => requestAnimationFrame(() => r())); }, +t);
    await p.screenshot({ path: `${process.env.OUT || '.'}/${fmt}_${String(n++).padStart(2, '0')}.jpg`, quality: 82, type: 'jpeg' });
  }
  // kleinste Schrift je Szene (nur Text mit Ziffern), zur Kontrolle der Lesbarkeit
  if (fmt !== 'port') console.log(JSON.stringify(await p.evaluate(() => [...document.querySelectorAll('.scene')].map(s => { s.classList.add('on'); let m = 999, tx = '';
    const w = document.createTreeWalker(s, NodeFilter.SHOW_TEXT); let nd; while (nd = w.nextNode()) { if (/\d/.test(nd.textContent)) { const f = parseFloat(getComputedStyle(nd.parentElement).fontSize); if (f < m) { m = f; tx = nd.textContent.trim().slice(0, 24); } } } return [s.className.split(' ')[1], m, tx]; }))));
  await b.close();
})();
