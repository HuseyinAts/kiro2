// KIRO2 Şafak bileşen görsel-regresyon (BackstopJS) — LOKAL dev gate.
// Q2 kararı: referans = BİZİM bileşenimiz (regresyon guard). misMatchThreshold=1 → ≤%1.
// Cross-OS font-render farkı nedeniyle CI'da koşmaz; CI gate'i = kanon-lint + tsc + vitest + axe.
// Senaryolar build edilmiş storybook-static/index.json'dan türetilir (20 bileşene ölçeklenir).
const fs = require('node:fs');
const path = require('node:path');

const PORT = process.env.KIRO_SB_PORT || 6099;
const base = `http://localhost:${PORT}/iframe.html`;
const indexPath = path.join(__dirname, 'storybook-static', 'index.json');

let entries = {};
try {
  entries = JSON.parse(fs.readFileSync(indexPath, 'utf8')).entries || {};
} catch (e) {
  console.warn('backstop.kiro: storybook-static/index.json yok — önce `npm run build-storybook`. ' + e.message);
}

const scenarios = Object.values(entries)
  .filter((e) => e.type === 'story')
  .map((e) => ({
    label: `${String(e.title).replace(/^Kiro\//, '')} · ${e.name}`,
    url: `${base}?id=${e.id}&viewMode=story`,
    selectors: ['#storybook-root'],
    readySelector: '#storybook-root',
    delay: 500,
    misMatchThreshold: 1,
  }));

module.exports = {
  id: 'kiro-components',
  viewports: [
    { label: 'desktop', width: 1280, height: 800 },
    { label: 'mobile', width: 390, height: 844 },
  ],
  scenarios,
  paths: {
    bitmaps_reference: 'backstop_data_kiro/bitmaps_reference',
    bitmaps_test: 'backstop_data_kiro/bitmaps_test',
    html_report: 'backstop_data_kiro/html_report',
    ci_report: 'backstop_data_kiro/ci_report',
  },
  engine: 'playwright',
  engineOptions: {
    browser: 'chromium',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  },
  asyncCaptureLimit: 2,
  asyncCompareLimit: 6,
  report: ['CI'],
};
