/**
 * `apiRequest` backend'in Türkçe hata mesajını YUTUYOR.
 *
 * CANLI ÖLÇÜM (26 Ağu 2026, Playwright anlık görüntüsü):
 *   backend  -> {"detail": "Doğrulama bağlantısı geçersiz veya süresi dolmuş…"}
 *   EKRANDA  -> "HTTP 400"
 *
 * Kök neden `apiHelpers.ts:485`: `errorData.message` okunuyor. FastAPI ise
 * mesajı `detail` ALTINDA gönderiyor — iki şekilde:
 *   • düz string        `{"detail": "…"}`                    (api/auth.py:2251)
 *   • iç içe nesne      `{"detail": {"code","message","email"}}` (api/auth.py:802-805)
 * İkisi de `.message` DEĞİL, dolayısıyla her seferinde `HTTP <kod>` fallback'i.
 *
 * NEDEN BU SADECE BİR "ÇİRKİN MESAJ" DEĞİL
 * ----------------------------------------
 * `EPOSTA_DOGRULAMA_ZORUNLU` kapısı açıldığında giriş 403 + "Giriş yapabilmek
 * için e-posta adresinizi doğrulayın" döndürüyor. Bu metin yutulduğu için
 * `GirisPage.tsx:172` sabit "E-posta ya da şifre eşleşmedi" yazıyor ve kullanıcı
 * şifresini yanlış sanıp sıfırlamaya gidiyor — tam da `api/auth.py:686-688`'in
 * 401 yerine 403 seçerek ÖNLEMEK istediği sonuç.
 *
 * 🔴 5xx AYRICALIKLI: kardeş `extractErrorDetail.ts:56-58` sunucu içini ASLA
 * sızdırmıyor. `apiRequest` de sızdırmamalı — aksi hâlde aynı depoda iki ayrı
 * ve ÇELİŞEN hata politikası olurdu.
 */

import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it } from 'vitest';

import { apiRequest } from '../apiHelpers';
import { server } from '../../test/mocks/server';

const BURASI = dirname(fileURLToPath(import.meta.url));
const UC = 'http://localhost:3000/api/v1/olcum/hata';

function govdeDondur(govde: unknown, status: number) {
  server.use(http.post(UC, () => HttpResponse.json(govde as never, { status })));
}

async function firlatilanMesaj(): Promise<string> {
  try {
    await apiRequest(UC, { method: 'POST' });
  } catch (e) {
    return (e as Error).message;
  }
  throw new Error('ALET ARIZASI: apiRequest hata FIRLATMADI');
}

beforeEach(() => {
  // Test URL'i public rota listesinde olmadığından 401 dalı yönlendirme
  // yapardı; bu testler 401 KULLANMIYOR (o dal ayrıca ele alınıyor).
});

describe('apiRequest — backend hata mesajı', () => {
  it('ALET DOĞRULAMASI: hata gövdesi gerçekten okunuyor', async () => {
    // Bu assert olmadan aşağıdakiler, gövde hiç ayrıştırılmasa da
    // "HTTP 400" görüp yanlış sebeple geçebilirdi.
    govdeDondur({ message: 'ust-duzey mesaj' }, 400);
    expect(await firlatilanMesaj()).toBe('ust-duzey mesaj');
  });

  it('DÜZ STRING detail kullanıcıya ULAŞIR', async () => {
    govdeDondur({ detail: 'Doğrulama bağlantısı geçersiz veya süresi dolmuş.' }, 400);
    expect(await firlatilanMesaj()).toBe('Doğrulama bağlantısı geçersiz veya süresi dolmuş.');
  });

  it('İÇ İÇE detail.message kullanıcıya ULAŞIR (kapının 403 gövdesi)', async () => {
    govdeDondur(
      {
        detail: {
          code: 'EPOSTA_DOGRULANMAMIS',
          message: 'Giriş yapabilmek için e-posta adresinizi doğrulayın.',
          email: 'ogrenci@ornek.com',
        },
      },
      403,
    );
    expect(await firlatilanMesaj()).toBe('Giriş yapabilmek için e-posta adresinizi doğrulayın.');
  });

  it('401 sunucunun sebebini gösterir, "Oturum süresi doldu" DEĞİL', async () => {
    // 🔴 CANLI ÖLÇÜM (26 Ağu 2026): `/login`de yanlış şifreyle giriş denendi.
    //    backend -> 401 {"detail":"Islem basarisiz. Lutfen tekrar deneyin."}
    //    EKRANDA -> "Oturum süresi doldu"
    // Hiç oturumu olmayan kullanıcıya "oturumun doldu" demek yanlış teşhis —
    // BLOKE-1 ile aynı sınıf. Kök neden `apiHelpers.ts:466-471`: 401 dalı
    // gövdeyi OKUMADAN kısa devre yapıyordu.
    //
    // ⚠️ Yol `/login`e kuruluyor: `girisYonlendirmesiGerekli('/login')` false
    // döner, yani yönlendirme dalı tetiklenmez ve jsdom'da gezinme gürültüsü
    // olmaz. Yönlendirme davranışı bu düzeltmede DEĞİŞMEDİ.
    window.history.replaceState({}, '', '/login');
    govdeDondur({ detail: 'Islem basarisiz. Lutfen tekrar deneyin.' }, 401);
    expect(await firlatilanMesaj()).toBe('Islem basarisiz. Lutfen tekrar deneyin.');
  });

  it('401 gövdesi kullanışsızsa "Oturum süresi doldu" KORUNUR (geriye uyum)', async () => {
    // Gerçek süresi-dolmuş-oturum durumunda backend gövde göndermeyebilir;
    // o zaman eski mesaj hâlâ doğru olan.
    window.history.replaceState({}, '', '/login');
    server.use(http.post(UC, () => new HttpResponse(null, { status: 401 })));
    expect(await firlatilanMesaj()).toBe('Oturum süresi doldu');
  });

  it('401 dalı yönlendirme kararını HÂLÂ veriyor (üretim kablosu)', () => {
    // MUTASYON BOŞLUĞU (26 Ağu 2026): yönlendirme koşulunu tamamen silmek
    // 10 testin hiçbirini düşürmüyordu. Sebep dürüst: testler yolu bilerek
    // `/login`e kuruyor, yani o dal HİÇ tetiklenmiyor.
    //
    // jsdom'da `window.location.href` atamasını proplamak kırılgan (location
    // yeniden tanımlanamaz; navigasyon "Not implemented" üretir). Bu yüzden
    // ölçüm YAPISAL: 401 bloğu, `publicRoutes` kararını veren fonksiyonu
    // çağırıyor mu? Karar fonksiyonunun KENDİ 7 testi zaten var
    // (publicRoutes.test.ts) — burada eksik olan tek şey ÇAĞRILDIĞIYDI.
    //
    // Arama 401 BLOĞUNA ankrajlı, dosyanın tamamına değil: ankrajsız bir
    // `toContain` başka bir daldaki çağrıya eşleşip yanlış-yeşil verirdi.
    const kaynak = readFileSync(resolve(BURASI, '..', 'apiHelpers.ts'), 'utf-8');
    const bas = kaynak.indexOf('if (response.status === 401) {');
    expect(bas, '401 dalı bulunamadı — ölçüm geçersiz').toBeGreaterThan(-1);

    let derinlik = 1;
    let i = bas + 'if (response.status === 401) {'.length;
    while (i < kaynak.length && derinlik > 0) {
      if (kaynak[i] === '{') derinlik++;
      else if (kaynak[i] === '}') derinlik--;
      i++;
    }
    const blok = kaynak.slice(bas, i);

    expect(blok, 'yönlendirme kararı 401 dalından kaldırılmış').toContain(
      'girisYonlendirmesiGerekli(',
    );
    expect(blok, 'yönlendirme eylemi 401 dalından kaldırılmış').toContain(
      "window.location.href = '/login'",
    );
  });

  it('5xx sunucu içini SIZDIRMAZ (extractErrorDetail.ts:56-58 ile aynı politika)', async () => {
    govdeDondur({ detail: 'psycopg2.errors.UndefinedColumn: users.gizli_kolon' }, 500);
    const mesaj = await firlatilanMesaj();
    expect(mesaj).not.toContain('psycopg2');
    expect(mesaj).not.toContain('gizli_kolon');
  });

  it('429 backend’in İNGİLİZCE rate-limit metnini göstermez', async () => {
    // MUTASYON BOŞLUĞU (26 Ağu 2026): 429 dalını silmek 7 testin hiçbirini
    // düşürmüyordu (M4 hayatta kaldı) — yani politika ölçülmemiş bir daldı.
    // Bu dal FARAZİ DEĞİL: `_TRUSTED_PROXIES` compose ağını kapsamadığı için
    // (`api/auth.py:83`) nginx arkasındaki tüm kullanıcılar tek kovayı
    // paylaşıyor ve 6. istek 429 alıyor (canlı ölçüldü).
    govdeDondur({ detail: 'Rate limit exceeded: 5 per 300 second' }, 429);
    const mesaj = await firlatilanMesaj();
    expect(mesaj).not.toContain('Rate limit exceeded');
    expect(mesaj).toContain('Çok fazla istek');
  });

  it('422 doğrulama dalı BOZULMADI (önceden var olan davranış)', async () => {
    govdeDondur(
      { detail: [{ loc: ['body', 'email'], msg: 'value is not a valid email address' }] },
      422,
    );
    expect(await firlatilanMesaj()).toContain('email: value is not a valid email address');
  });

  it('hiçbir tanınan alan yoksa HTTP <kod> fallback KORUNUR', async () => {
    govdeDondur({ beklenmedik: 'sekil' }, 418);
    expect(await firlatilanMesaj()).toBe('HTTP 418');
  });

  it('gövde JSON DEĞİLSE çağıran çökmez', async () => {
    server.use(http.post(UC, () => new HttpResponse('<html>502</html>', { status: 502 })));
    const mesaj = await firlatilanMesaj();
    expect(mesaj.length).toBeGreaterThan(0);
    expect(mesaj).not.toContain('<html>');
  });
});
