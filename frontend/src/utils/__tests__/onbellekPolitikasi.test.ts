import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * Dağıtım tazelik politikası: bayat kabuk bir daha servis edilmemeli.
 *
 * NEDEN (26 Ağu 2026, ÜÇ bağımsız canlı ölçüm)
 * --------------------------------------------
 * `vite-plugin-pwa` varsayılan olarak
 *   `registerRoute(new NavigationRoute(createHandlerBoundToURL("index.html")))`
 * üretiyordu. Bu, TÜM navigasyonları precache'ten, AĞA HİÇ ÇIKMADAN servis eder:
 *   1. Kullanıcının doğrulama linki tıklaması nginx log'una HİÇ düşmedi
 *      (`GET /eposta-dogrula` sayacı Δ0) ve eski kabuk rotayı bilmediği için
 *      catch-all -> `/404`.
 *   2. Deploy sonrası ilk yükleme ESKİ bundle'ı çalıştırdı; SW güncelleyip
 *      sayfayı yenileyince aynı doğrulama token'ı İKİNCİ kez tüketildi ve
 *      BAŞARI, "HTTP 400" olarak göründü.
 *   3. Aynı şey BLOKE-1 propunda birebir tekrarlandı.
 * Düzeltmeden sonra aynı sayaç 2 gezinmede 1 -> 3 (Δ+2) ölçüldü.
 *
 * İkinci katman: nginx hiçbir yola `Cache-Control` göndermiyordu. Başlık yokken
 * tarayıcı `Last-Modified`'a bakıp SEZGİSEL önbellekleme yapar — kabuk sessizce
 * bayatlar.
 *
 * 🔴 BU BEKÇİ METİN OKUR, DAVRANIŞ ÖLÇMEZ. Gerçek kanıt canlı sayaçtı; burada
 * korunan şey KARARIN GERİ ALINMAMASI. Bu yüzden her assert, geri alındığında
 * ne olacağını mesajında söyler.
 */

const BURASI = dirname(fileURLToPath(import.meta.url));
const KOK = resolve(BURASI, '..', '..', '..');
const NGINX = readFileSync(resolve(KOK, 'nginx.conf'), 'utf-8');
const VITE = readFileSync(resolve(KOK, 'vite.config.ts'), 'utf-8');

/** `location <eşleyici> { … }` bloklarını süslü parantez sayarak ayıklar. */
function locationBloklari(conf: string): { eslesme: string; govde: string }[] {
  const bloklar: { eslesme: string; govde: string }[] = [];
  const bas = /location\s+([^{]+?)\s*\{/g;
  let m: RegExpExecArray | null;
  while ((m = bas.exec(conf)) !== null) {
    let derinlik = 1;
    let i = bas.lastIndex;
    while (i < conf.length && derinlik > 0) {
      if (conf[i] === '{') derinlik++;
      else if (conf[i] === '}') derinlik--;
      i++;
    }
    bloklar.push({ eslesme: m[1].trim(), govde: conf.slice(bas.lastIndex, i - 1) });
  }
  return bloklar;
}

function blokBul(eslesme: string): string {
  const blok = locationBloklari(NGINX).find((b) => b.eslesme === eslesme);
  if (!blok) throw new Error(`nginx.conf'ta "location ${eslesme}" bloğu YOK`);
  return blok.govde;
}

describe('dağıtım tazelik politikası', () => {
  it('ALET DOĞRULAMASI: nginx ayrıştırıcısı blokları gerçekten buluyor', () => {
    // Ayrıştırıcı 0 blok bulursa aşağıdaki testler BOŞ kümede geçerdi.
    const bloklar = locationBloklari(NGINX);
    expect(bloklar.length).toBeGreaterThanOrEqual(10);
    expect(bloklar.map((b) => b.eslesme)).toContain('/');
  });

  it('SPA kabuğu her istekte yeniden doğrulanır (expires -1)', () => {
    expect(blokBul('/'), 'kabuk önbelleğe alınırsa deploy sonrası bayat kalır').toContain(
      'expires -1',
    );
  });

  it('service worker ASLA önbelleğe alınmaz', () => {
    // Bayat bir SW, bayat bir uygulamayı süresiz servis eder VE kendini
    // güncelleyemez — kilitlenme.
    for (const yol of ['= /sw.js', '= /registerSW.js']) {
      expect(blokBul(yol), `${yol} önbelleğe alınırsa SW kendini güncelleyemez`).toContain(
        'expires -1',
      );
    }
  });

  it('içerik-hash’li varlıklar uzun önbelleklenir', () => {
    for (const yol of ['/js/', '/css/', '/assets/', '/fonts/']) {
      expect(blokBul(yol), `${yol} hash'li; uzun önbellek güvenli ve gerekli`).toMatch(
        /expires\s+1y/,
      );
    }
  });

  it('🔴 hiçbir location bloğu add_header KULLANMAZ (güvenlik başlığı düşürür)', () => {
    // nginx kalıtım kuralı: bir location HERHANGİ bir `add_header` içerirse
    // server bloğundaki TÜM add_header'lar (CSP, HSTS, X-Frame-Options,
    // Referrer-Policy, Permissions-Policy, X-Content-Type-Options) o konum için
    // DÜŞER. `always` bunu değiştirmez. Önbellek politikası bu yüzden `expires`
    // ile yazıldı. Canlı kontrol kolu: /, /js/, /sw.js -> 6/6 güvenlik başlığı.
    // 🔴 `^\s*add_header` ANKRAJI KULLANMA. İlk sürüm öyleydi ve mutasyon
    // hayatta kaldı: bu dosyadaki konumların çoğu TEK SATIRLIK
    // (`location /js/ { expires 1y; add_header ...; }`) ve orada `add_header`
    // satır başında DEĞİL. Dedektör tam da korumak istediği bloklara kördü.
    const ihlal = locationBloklari(NGINX).filter((b) => /\badd_header\b/.test(b.govde));
    expect(
      ihlal.map((b) => b.eslesme),
      'bu location(lar)da add_header var -> o yolda CSP/HSTS dahil TÜM güvenlik ' +
        'başlıkları kaybolur. Önbellek için `expires` kullan.',
    ).toEqual([]);
  });

  it('server bloğu güvenlik başlıklarını HÂLÂ tanımlıyor (kontrol kolu)', () => {
    // Üstteki test "add_header hiç yok" diye de geçebilirdi; o zaman güvenlik
    // başlıkları tamamen kaybolmuş olurdu ve bekçi bunu ALKIŞLARDI.
    //
    // 🔴 YORUMLAR AYIKLANIYOR. İlk sürüm ham metinde arıyordu ve mutasyon
    // hayatta kaldı: `nginx.conf`'a yazdığım AÇIKLAMA satırı bu başlık
    // adlarını (CSP, HSTS, X-Frame-Options…) sayıyor, dolayısıyla direktif
    // silinse bile eşleşme sürüyordu. "Bir deseni anlatan yorum o deseni
    // İÇERİR" — `.claude/rules/audit-methodology.md`.
    const yorumsuz = NGINX.replace(/#.*$/gm, '');
    expect(
      yorumsuz.length,
      'alet doğrulaması: yorum ayıklama hiçbir şey silmedi',
    ).toBeLessThan(NGINX.length);

    for (const baslik of [
      'Content-Security-Policy',
      'Strict-Transport-Security',
      'X-Frame-Options',
      'X-Content-Type-Options',
      'Referrer-Policy',
      'Permissions-Policy',
    ]) {
      expect(yorumsuz, `server bloğunda \`add_header ${baslik}\` DİREKTİFİ yok`).toMatch(
        new RegExp(`add_header\\s+${baslik}\\b`),
      );
    }
  });

  it('PWA navigasyonu precache-first DEĞİL', () => {
    expect(
      VITE,
      'navigateFallback varsayılanı geri gelirse workbox NavigationRoute üretir ' +
        've navigasyonlar tekrar AĞA ÇIKMADAN precache’ten servis edilir',
    ).toContain('navigateFallback: undefined');
  });

  it('PWA navigasyonu network-first bir rotaya sahip', () => {
    expect(VITE).toContain('kiro2-html-shell');
    expect(VITE).toMatch(/request\.mode\s*===\s*'navigate'/);

    // 🔴 ANKRAJ ŞART. İlk sürüm yalnız `VITE.toContain("handler: 'NetworkFirst'")`
    // diyordu ve mutasyon hayatta kaldı: navigate rotası CacheFirst'e çevrilse
    // bile /api/realms ve /api/gamification rotaları hâlâ NetworkFirst olduğu
    // için assert geçiyordu. Yargı, ölçmek istediği ROTAYA bağlanmalı.
    const bas = VITE.indexOf("request.mode === 'navigate'");
    const son = VITE.indexOf("'kiro2-html-shell'");
    expect(bas, 'navigate eşleyicisi bulunamadı').toBeGreaterThan(-1);
    expect(son, 'kiro2-html-shell bulunamadı').toBeGreaterThan(bas);

    const navigasyonRotasi = VITE.slice(bas, son);
    // Çevrimdışı desteği korunuyor: NetworkFirst ağ yoksa önbelleğe düşer.
    expect(
      navigasyonRotasi,
      'navigasyon rotasının handler’ı NetworkFirst değil — bayat kabuk geri döner',
    ).toContain("handler: 'NetworkFirst'");
    expect(navigasyonRotasi).not.toContain("handler: 'CacheFirst'");
  });
});
