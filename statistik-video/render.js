// Rendert das Video Bild für Bild: node render.js land|port [ausgabe.mp4]
// Danach Ton dazumischen (siehe build.sh).
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const fmt = process.argv[2] === 'port' ? 'port' : 'land';
const out = process.argv[3] || `video_${fmt}.mp4`;
const [W, H] = fmt === 'port' ? [1080, 1920] : [1920, 1080];
const FPS = 30, WORKERS = 4;
const tmp = path.join(__dirname, `.seg_${fmt}`);
fs.mkdirSync(tmp, { recursive: true });

async function worker(idx, from, to) {
  const seg = path.join(tmp, `seg_${idx}.mp4`);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-vf', 'noise=alls=3:allf=t,format=yuv420p', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  await page.goto('file://' + path.join(__dirname, 'index.html') + `?render=1&fmt=${fmt}`);
  await page.waitForFunction('window.READY');
  for (let f = from; f < to; f++) {
    await page.evaluate(t => { seek(t); return new Promise(r => requestAnimationFrame(() => r())); }, f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 97 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (idx === 0 && (f - from) % 150 === 0) console.log(`${fmt}: ${Math.round((f - from) / (to - from) * 100)} %`);
  }
  ff.stdin.end();
  await browser.close();
  await done;
  return seg;
}

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + path.join(__dirname, 'index.html') + '?render=1');
  await p.waitForFunction('window.READY');
  const total = Math.round((await p.evaluate('TOTAL')) * FPS);
  await b.close();
  const per = Math.ceil(total / WORKERS);
  const segs = await Promise.all([...Array(WORKERS)].map((_, i) => worker(i, i * per, Math.min(total, (i + 1) * per))));
  const list = path.join(tmp, 'list.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out]);
  fs.rmSync(tmp, { recursive: true });
  console.log('fertig:', out, total, 'Bilder');
})();
