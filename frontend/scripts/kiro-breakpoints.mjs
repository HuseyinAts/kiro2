// KIRO2 — ekran breakpoint denetimi (BREAKPOINT_SPEC §4 QA matrisi).
// storybook-static ekran story'lerini 7 genişlikte ölçer: overflowX=0 + hit≥44 (≤1199).
// <a> text linkleri bilinçli istisna (§2). Kullanım: node scripts/kiro-breakpoints.mjs
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const STATIC = path.join(ROOT, 'storybook-static');
const PORT = Number(process.env.KIRO_BP_PORT || 6098);
const WIDTHS = [390, 768, 834, 1024, 1194, 1280, 1440];
const SCREENS = [
  { id: 'kiro-ekran-giris--varsayilan', ad: 'Giriş' },
  { id: 'kiro-ekran-odevlerim--varsayilan', ad: 'Ödevlerim' },
];

if (!existsSync(path.join(STATIC, 'iframe.html'))) {
  console.error('storybook-static yok — önce `npm run build-storybook`.');
  process.exit(2);
}

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
  '.woff': 'font/woff', '.map': 'application/json', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};
const server = http.createServer(async (req, res) => {
  try {
    let p = decodeURIComponent((req.url || '/').split('?')[0]);
    if (p.endsWith('/')) p += 'index.html';
    const fp = path.normalize(path.join(STATIC, p));
    if (!fp.startsWith(STATIC)) { res.writeHead(403); return res.end(); }
    res.writeHead(200, { 'content-type': MIME[path.extname(fp)] || 'application/octet-stream' });
    res.end(await readFile(fp));
  } catch { res.writeHead(404); res.end('404'); }
});
await new Promise((r) => server.listen(PORT, r));

const browser = await chromium.launch({ args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'] });
let fails = 0;
for (const sc of SCREENS) {
  for (const w of WIDTHS) {
    const page = await browser.newPage({ viewport: { width: w, height: 900 } });
    await page.goto(`http://localhost:${PORT}/iframe.html?id=${sc.id}&viewMode=story`, { waitUntil: 'load' }).catch(() => {});
    await page.waitForSelector('#storybook-root', { timeout: 8000 }).catch(() => {});
    await page.waitForTimeout(700); // font + async veri
    const r = await page.evaluate(() => {
      const de = document.documentElement;
      const kucuk = [];
      document.querySelectorAll('button, input, [role="radio"]').forEach((el) => {
        const h = el.getBoundingClientRect().height;
        if (h > 0 && h < 44) kucuk.push(((el.textContent || el.getAttribute('aria-label') || el.tagName) + '').trim().slice(0, 20) + '=' + Math.round(h));
      });
      return { overflow: de.scrollWidth - de.clientWidth, cw: de.clientWidth, sw: de.scrollWidth, kucuk };
    });
    const overflowOk = r.overflow <= 1;
    const hitOk = w > 1199 || r.kucuk.length === 0;
    const ok = overflowOk && hitOk;
    if (!ok) fails++;
    console.log(`${ok ? 'OK  ' : 'FAIL'} ${sc.ad.padEnd(9)} @${String(w).padStart(4)}: overflowX=${r.overflow} (sw${r.sw}/cw${r.cw})${w <= 1199 && r.kucuk.length ? '  hit<44: ' + r.kucuk.join(', ') : ''}`);
    await page.close();
  }
}
await browser.close();
server.close();
console.log(`\nkiro-breakpoints: ${fails} FAIL / ${SCREENS.length * WIDTHS.length} kontrol`);
process.exit(fails ? 1 : 0);
