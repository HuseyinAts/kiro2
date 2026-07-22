#!/usr/bin/env node
// ============================================================================
// KIRO2 — Kanon Lint (CI)
// Kullanım:  node design/scripts/kanon-lint.mjs frontend/src/kiro
// Çıkış kodu: ihlal varsa 1 (uyarılar hariç).
// Kaynak kurallar: CLAUDE.md (kanon) + URETIM_YOL_HARITASI Faz 5.
// ============================================================================
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';

const ROOT = process.argv[2] ?? 'frontend/src/kiro';
const EXT = new Set(['.ts', '.tsx', '.css', '.js', '.jsx']);

// --- YASAK: alarm-kırmızısı (risk HER ZAMAN amber) ---
const ALARM_RED = /#(DC2626|EF4444|B91C1C|F87171|991B1B|FEE2E2|FF0000|E11D48|BE123C)\b/i;
// --- YASAK: indigo/lacivert (mor yalnız Fizik ders rengi #8B5CF6 / #A77BFF) ---
const INDIGO = /#(4F46E5|6366F1|4338CA|3730A3|312E81|1E3A8A|1E40AF|A5B4FC|C7D2FE|E0E7FF)\b/i;
// --- YASAK: emoji (ikonlar bespoke inline SVG) ---
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}]/u;
// --- YASAK: ödev bağlamında "eksik" (kanon dil: "bekliyor") ---
const EKSIK = /['"`>][^'"`<\n]*\beksik\b/i;
// --- UYARI: açık-zemin grisi koyu (dusk) dosyada ---
const OPEN_GREY = /#6B6478\b/i;
const DUSK_HINT = /(k-dusk|theme=.dusk|'dusk'|"dusk"|#110C18|#150E20)/;
// --- MOTION KANONU (KIRO Motion Kanonu.dc.html · P0-1) ---
// Hareket var ama reduced-motion guard'ı yok → ihlal (dosya düzeyi).
const HAS_MOTION = /(@keyframes|animation\s*:|transition\s*:|\.animate\s*\()/;
const HAS_RM_GUARD = /(prefers-reduced-motion|useReducedMotion)/;
// transition: all → ihlal (özellik adı yazılır).
const TRANSITION_ALL = /transition\s*:\s*all\b/i;
// Kutlama dışı 600ms üstü süre → uyarı (`kanon-allow: kutlama` dosyada serbest bırakır).
const LONG_DURATION = /(animation|transition)[^;\n]*?\b(0?\.[7-9]\d*s|[1-9]\d*(\.\d+)?s|[7-9]\d{2,}ms|\d{4,}ms)\b/i;
// Layout animasyonu (yalnız transform + opacity hareket eder) → ihlal.
const LAYOUT_ANIM = /transition\s*:[^;\n]*\b(width|height|top|left|margin|padding)\b/i;
// --- İLLÜSTRASYON/İKON KANONU: stok ikon & UI kitaplığı importu yasak (bespoke inline SVG) ---
const BANNED_IMPORT = /from\s+['"](lucide-react|react-icons[^'"]*|@mui\/[^'"]+|@emotion\/[^'"]+|react-hot-toast|@heroicons\/[^'"]+|font-?awesome[^'"]*)['"]/i;

const errors = [];
const warnings = [];

// --- İSTİSNA: dosya başında `// kanon-allow: boss-arena` → kırmızı ailesi serbest ---
// (ONAYLI 2026-07-04 · SPRINT7_SPEC: ejderha = kurgusal düşman kimliği, alarm-semantiği değil.
//  Yalnız boss arena dosyasında kullan; kullanıcı-hatası geri bildirimi orada bile terracotta.)
const ALLOW_RE = /kanon-allow:\s*([a-z-]+(?:\s*,\s*[a-z-]+)*)/;

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) { if (!/node_modules|\.git|dist/.test(name)) walk(p); continue; }
    if (!EXT.has(extname(name))) continue;
    const src = readFileSync(p, 'utf8');
    const lines = src.split('\n');
    const isDusk = DUSK_HINT.test(src);
    const allowM = src.slice(0, 600).match(ALLOW_RE);
    const allows = new Set(allowM ? allowM[1].split(/\s*,\s*/) : []);
    const redOk = allows.has('boss-arena');
    const springOk = allows.has('kutlama'); // yalnız dusk kutlama yüzeyi dosyaları
    if (HAS_MOTION.test(src) && !HAS_RM_GUARD.test(src))
      errors.push(`${p}  HAREKET GUARD'SIZ — tüm animation/transition/WAAPI prefers-reduced-motion (veya useReducedMotion) guard'ı ister (Motion Kanonu §05)`);
    lines.forEach((line, i) => {
      const at = `${p}:${i + 1}`;
      if (!redOk && ALARM_RED.test(line)) errors.push(`${at}  ALARM-KIRMIZISI — risk amber olmalı (#C77A1E dolgu / #9A5D0D metin): ${line.trim().slice(0, 90)}`);
      if (INDIGO.test(line)) errors.push(`${at}  İNDİGO YASAK — dawn aksanı kullan: ${line.trim().slice(0, 90)}`);
      if (EMOJI.test(line)) errors.push(`${at}  EMOJİ YASAK — bespoke inline SVG kullan: ${line.trim().slice(0, 90)}`);
      if (EKSIK.test(line)) errors.push(`${at}  "eksik" YASAK — kanon dil "bekliyor": ${line.trim().slice(0, 90)}`);
      if (isDusk && OPEN_GREY.test(line)) warnings.push(`${at}  UYARI — #6B6478 açık-zemin grisidir; koyu ekranda dusk.textSecondary kullan`);
      if (TRANSITION_ALL.test(line)) errors.push(`${at}  transition:all YASAK — özellik adı yaz (Motion Kanonu §06): ${line.trim().slice(0, 90)}`);
      if (LAYOUT_ANIM.test(line)) errors.push(`${at}  LAYOUT ANİMASYONU YASAK — yalnız transform + opacity (+renk) hareket eder: ${line.trim().slice(0, 90)}`);
      if (!springOk && LONG_DURATION.test(line)) warnings.push(`${at}  UYARI — 600ms üstü süre yalnız kutlama yüzeyinde (kanon-allow: kutlama): ${line.trim().slice(0, 90)}`);
      if (BANNED_IMPORT.test(line)) errors.push(`${at}  STOK İKON/UI KİTAPLIĞI YASAK — bespoke inline SVG + kiro/ui kullan: ${line.trim().slice(0, 90)}`);
    });
  }
}

try { walk(ROOT); } catch (e) {
  console.error(`kanon-lint: '${ROOT}' okunamadı — yol doğru mu?`); process.exit(2);
}

for (const w of warnings) console.warn(w);
for (const e of errors) console.error(e);
console.log(`\nkanon-lint: ${errors.length} ihlal, ${warnings.length} uyarı (${ROOT})`);
process.exit(errors.length ? 1 : 0);
