// storybook-static'i serve edip BackstopJS'i (reference|test) koşar. Saf node (ek dep yok).
// Kullanım: node scripts/kiro-visual.mjs reference | test
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import backstop from 'backstopjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const STATIC = path.join(ROOT, 'storybook-static');
const PORT = Number(process.env.KIRO_SB_PORT || 6099);
const command = process.argv[2] === 'reference' ? 'reference' : 'test';

if (!existsSync(path.join(STATIC, 'iframe.html'))) {
  console.error('storybook-static yok — önce `npm run build-storybook`.');
  process.exit(2);
}

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.map': 'application/json', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};

const server = http.createServer(async (req, res) => {
  try {
    let p = decodeURIComponent((req.url || '/').split('?')[0]);
    if (p.endsWith('/')) p += 'index.html';
    const fp = path.normalize(path.join(STATIC, p));
    if (!fp.startsWith(STATIC)) { res.writeHead(403); return res.end(); }
    const body = await readFile(fp);
    res.writeHead(200, { 'content-type': MIME[path.extname(fp)] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404);
    res.end('not found');
  }
});

await new Promise((r) => server.listen(PORT, r));
console.log(`storybook-static @ http://localhost:${PORT} — backstop ${command}`);

let code = 0;
try {
  await backstop(command, { config: path.join(ROOT, 'backstop.kiro.cjs') });
} catch (e) {
  code = 1;
  console.error(`backstop ${command} FAIL:`, e && e.message ? e.message : e);
} finally {
  server.close();
}
process.exit(code);
