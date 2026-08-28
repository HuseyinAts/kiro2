import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * Uygulama ici bir baglantinin App.tsx'te GERCEKTEN bir rotasi var mi.
 *
 * NEDEN
 * -----
 * `EpostaDogrulaPage.tsx:65` basarili dogrulamadan sonra `/giris`e yolluyordu;
 * App.tsx'te tanimli olan `/login` (:256). Sonuc: kullanici e-postasini
 * dogruluyor, "Giris yap"a basiyor ve `/404` goruyor. 26 Agu 2026'da canli
 * tarayicida goruldu (Playwright anlik goruntusu: `link "Giris yap" /url: /giris`).
 *
 * NEDEN "HTTP 200" BU KUSURU GIZLER
 * ---------------------------------
 * nginx SPA fallback'i her yola `index.html` doner: `/giris`, `/bugun`, `/panel`
 * hepsi **HTTP 200** (olculdu). Rota yoklugu yalniz ISTEMCI tarafinda, App.tsx'in
 * catch-all (`path="*"`) daliyla ortaya cikar. Bu yuzden bekci HTTP'ye degil
 * **iki bagimsiz kaynaga** bakar: App.tsx'in rota bildirimleri vs kaynaktaki
 * href/to/navigate hedefleri.
 *
 * 🔴 CATCH-ALL ESLESME SAYILMAZ. `path="*"` her seyi eslestirir; onu gecerli
 * saymak bekciyi ölü dogururdu — kusurun ta kendisi o daldir.
 */

const BURASI = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(BURASI, '..', '..');
const APP = join(SRC, 'App.tsx');

/**
 * Bu turda DUZELTILMEYEN, ONCEDEN VAR OLAN olu baglantilarin sayisi.
 *
 * 26 Agu 2026 olcumu: 114 ic bagin **40**'inin App.tsx'te rotasi yoktu.
 * Bunlarin 2'si (`/giris`) A1 altin yolundaydi ve duzeltildi; kalan 38'i
 * `src/kiro/screens/*` tasarim-portundan geliyor ve AYRI bir istir
 * (`/bugun` 8x, `/ogrenme-yolu` 4x, `/panel` 3x, ...).
 *
 * Sayi TAM ESITLIKLE civileniyor, `<=` ile DEGIL: bir tavan ust sinirla
 * korunmaz — 38'i 999 yapmak hicbir testi dusurmezdi (S252'de mutasyon tam
 * bunu yakaladi). Borcu azalttiginda bu sayiyi da DUSUR.
 */
const ONCEDEN_VAR_OLAN_OLU_BAG = 38;

function tsxDosyalari(dizin: string, birikim: string[] = []): string[] {
  for (const ad of readdirSync(dizin)) {
    const tam = join(dizin, ad);
    if (statSync(tam).isDirectory()) {
      if (ad === 'node_modules' || ad === '__tests__' || ad === 'test') continue;
      tsxDosyalari(tam, birikim);
    } else if (ad.endsWith('.tsx') && !ad.includes('.test.')) {
      birikim.push(tam);
    }
  }
  return birikim;
}

/** App.tsx'teki `path="..."` bildirimleri; catch-all HARIC. */
function bildirilenRotalar(): string[] {
  const metin = readFileSync(APP, 'utf-8');
  return [...metin.matchAll(/path="([^"]+)"/g)]
    .map((m) => m[1])
    .filter((p) => p !== '*');
}

/** React Router v6 esdegeri kaba eslesme: `:param` joker, sondaki `*` onek. */
function rotaEsliyor(yol: string, rota: string): boolean {
  const temiz = (yol.split('?')[0].split('#')[0].replace(/\/+$/, '') || '/').toLowerCase();
  const r = ('/' + rota.replace(/^\/+/, '')).replace(/\/+$/, '') || '/';
  const rp = r.split('/');
  const yp = temiz.split('/');
  if (rp[rp.length - 1] === '*') {
    const govde = rp.slice(0, -1);
    return (
      yp.length >= govde.length &&
      govde.every((seg, i) => seg.startsWith(':') || seg.toLowerCase() === yp[i])
    );
  }
  if (rp.length !== yp.length) return false;
  return rp.every((seg, i) => seg.startsWith(':') || seg.toLowerCase() === yp[i]);
}

interface Bag {
  dosya: string;
  yol: string;
}

function icBaglar(): Bag[] {
  const desen = /(?:href|to)=["'](\/[^"'{}$]*)["']|navigate\(\s*["'](\/[^"'{}$]*)["']/g;
  const cikti: Bag[] = [];
  for (const dosya of tsxDosyalari(SRC)) {
    const metin = readFileSync(dosya, 'utf-8');
    for (const m of metin.matchAll(desen)) {
      const yol = m[1] ?? m[2];
      if (!yol || yol.startsWith('//')) continue;
      cikti.push({ dosya: dosya.replace(/\\/g, '/').split('/src/')[1] ?? dosya, yol });
    }
  }
  return cikti;
}

function oluBaglar(): Bag[] {
  const rotalar = bildirilenRotalar();
  return icBaglar().filter((b) => !rotalar.some((r) => rotaEsliyor(b.yol, r)));
}

describe('rota butunlugu', () => {
  it('ALET DOGRULAMASI: tarayici gercekten rota ve bag buluyor', () => {
    // Bu assert olmadan asagidaki testler BOS kume uzerinde gecerdi:
    // regex bozulsa "0 olu bag" cikar ve bekci yanlis-YESIL olurdu.
    expect(bildirilenRotalar().length).toBeGreaterThanOrEqual(50);
    expect(icBaglar().length).toBeGreaterThanOrEqual(80);
  });

  it('ALET DOGRULAMASI: catch-all gecerli rota SAYILMAZ', () => {
    // `path="*"` gecerli sayilsaydi hicbir bag olu gorunmezdi.
    expect(bildirilenRotalar()).not.toContain('*');
    expect(rotaEsliyor('/kesinlikle-olmayan-bir-yol', '/login')).toBe(false);
  });

  it('bilinen calisan rotalar OLU sayilmiyor (yanlis-pozitif kontrolu)', () => {
    const rotalar = bildirilenRotalar();
    for (const yol of ['/login', '/eposta-dogrula', '/404']) {
      expect(rotalar.some((r) => rotaEsliyor(yol, r)), yol).toBe(true);
    }
  });

  it('A1 altin yolu: dogrulama sonrasi giris baglantisi OLU DEGIL', () => {
    // Kok kusur: /giris rotasi HIC olmadi; giris ekrani /login (App.tsx:256).
    const giris = icBaglar().filter((b) => b.yol.split('?')[0] === '/giris');
    expect(
      giris,
      `"/giris" App.tsx'te tanimli degil -> catch-all -> /404. Bulundugu yerler: ${giris
        .map((b) => b.dosya)
        .join(', ')}`,
    ).toHaveLength(0);
  });

  it('CIRCIR: onceden var olan olu bag sayisi ARTMIYOR', () => {
    const olu = oluBaglar();
    const ozet = [...new Set(olu.map((b) => b.yol))].sort().join(', ');
    expect(
      olu.length,
      `Olu ic bag sayisi ${ONCEDEN_VAR_OLAN_OLU_BAG} olmali, ${olu.length} bulundu.\n` +
        `Yeni bir olu bag eklediysen App.tsx'e rotasini ekle.\n` +
        `Borcu azalttiysan ONCEDEN_VAR_OLAN_OLU_BAG sabitini DUSUR.\nHedefler: ${ozet}`,
    ).toBe(ONCEDEN_VAR_OLAN_OLU_BAG);
  });
});
