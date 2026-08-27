/**
 * Kayıt BAŞARILI olduğu hâlde ekran SESSİZ kalıyor (kapı açıkken).
 *
 * ÖLÇÜLEN ZİNCİR (26 Ağu 2026)
 * ----------------------------
 * `EPOSTA_DOGRULAMA_ZORUNLU` açıkken:
 *   1. Kullanıcı kayıt olur -> backend 201, satır oluşur (`is_verified=false`)
 *   2. `authStore.ts:258` OTOMATİK GİRİŞ dener -> backend 403 EPOSTA_DOGRULANMAMIS
 *   3. `login` `false` döner; `authStore.ts:262` `return loginResult === true`
 *      -> `register` de **false** döner
 *   4. `ModernRegisterPage.tsx:186` `if (success)` düşer -> HİÇBİR dal koşmaz
 *   5. Sayfa store `error`'ını da okumuyor (`:64` yalnız `{ register }`)
 *   => Kullanıcı kayıt oldu, ekranda HİÇBİR ŞEY yok. Ne başarı, ne hata.
 *
 * Bugün kapı KAPALI olduğu için görünmüyor; açıldığı gün HER yeni kullanıcı
 * bunu yaşar. Bu yüzden kapının ön koşulu.
 *
 * 🔴 SÖZLEŞME HATASI: `register` iki AYRI sonucu tek boolean'a katlıyor —
 * "kayıt başarısız" ile "kayıt başarılı ama giriş engellendi". İkincisi
 * kullanıcı için TAMAMEN farklı bir durum: hesabı VAR, yapması gereken şey
 * e-postasını doğrulamak.
 *
 * Sözleşme GENİŞLETİLİYOR, kırılmıyor: `true` hâlâ "kayıt + giriş tamam".
 * Tek üretim çağıranı `ModernRegisterPage.tsx:184` (ölçüldü).
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const gezin = vi.fn();
const kayitOl = vi.fn();

vi.mock('react-router-dom', async () => {
  const gercek = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...gercek, useNavigate: () => gezin };
});

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({ register: kayitOl }),
}));

import { ModernRegisterPage } from '../ModernRegisterPage';

const KAPI_MESAJI = 'Giriş yapabilmek için e-posta adresinizi doğrulayın.';

async function formuDoldurVeGonder() {
  const kullanici = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/register']}>
      <ModernRegisterPage />
    </MemoryRouter>,
  );

  // Alanlar `name` niteliginden secilyor, etiketten DEGIL: MUI `required`
  // alanlarda etiketi "Ad *" olarak render ediyor ve tam eslesme tutmuyor
  // (olculdu). `name` degerleri kaynakta sabit:
  // ModernRegisterPage.tsx:465,493,521,604,676
  const yaz = async (ad: string, deger: string) => {
    const alan = document.querySelector<HTMLInputElement>(`input[name="${ad}"]`);
    if (!alan) throw new Error(`ALET ARIZASI: input[name="${ad}"] bulunamadi`);
    await kullanici.clear(alan);
    await kullanici.type(alan, deger);
  };

  await yaz('ad', 'Ogrenci');
  await yaz('soyad', 'Deneme');
  await yaz('email', 'ogrenci@ornek.com');
  // Sifre politikasi ModernRegisterPage.tsx:140-152'de olculdu:
  // 8+ karakter, buyuk + kucuk + rakam + ozel karakter.
  await yaz('password', 'Zq7#Kv2!Rm9x');
  await yaz('confirmPassword', 'Zq7#Kv2!Rm9x');
  // birth_date ZORUNLU (ModernRegisterPage.tsx:160) ve baslangic degeri BOS
  // (:50). Yetiskin bir tarih seciliyor; kucukse veli_email de zorunlu olurdu.
  await yaz('birth_date', '2000-01-01');

  await kullanici.click(screen.getByRole('button', { name: /kayıt ol/i }));
  return kullanici;
}

beforeEach(() => {
  gezin.mockReset();
  kayitOl.mockReset();
});

describe('ModernRegisterPage — doğrulama adımı', () => {
  it('ALET DOĞRULAMASI: form gönderiliyor ve register çağrılıyor', async () => {
    // Bu assert olmadan aşağıdakiler, form HİÇ gönderilmese de
    // "mesaj görünmüyor" diye YANLIŞ SEBEPLE geçerdi.
    kayitOl.mockResolvedValue(true);
    await formuDoldurVeGonder();
    await waitFor(() => expect(kayitOl).toHaveBeenCalledTimes(1));
  });

  it('kayıt + otomatik giriş TAMAM: mevcut davranış korunur', async () => {
    kayitOl.mockResolvedValue(true);
    await formuDoldurVeGonder();
    expect(await screen.findByText(/kayıt başarılı/i)).toBeInTheDocument();
  });

  it('kayıt BAŞARILI ama giriş engellendi: doğrulama adımı gösterilir', async () => {
    // Bugün bu dalda ekran TAMAMEN sessiz kalıyor.
    kayitOl.mockResolvedValue({ kayitOldu: true, girisEngellendi: KAPI_MESAJI });
    await formuDoldurVeGonder();

    expect(await screen.findByText(new RegExp(KAPI_MESAJI, 'i'))).toBeInTheDocument();
    const baglanti = await screen.findByRole('link', { name: /doğrulama/i });
    expect(baglanti).toHaveAttribute('href', '/eposta-dogrula');
  });

  it('giriş engellendiğinde /login’e YÖNLENDİRİLMEZ', async () => {
    // Yönlendirilseydi kullanıcı giriş ekranında yine bloklanır ve neden
    // bloklandığını anlamadan döngüye girerdi.
    kayitOl.mockResolvedValue({ kayitOldu: true, girisEngellendi: KAPI_MESAJI });
    await formuDoldurVeGonder();

    await waitFor(() => expect(kayitOl).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 2300)); // mevcut kod 2000ms sonra gezinir
    expect(gezin).not.toHaveBeenCalled();
  });

  it('kayıt BAŞARISIZ: kullanıcı sessiz bırakılmaz', async () => {
    // Bugün `false` dalında da hiçbir şey gösterilmiyor (sayfa store error'ını
    // okumuyor). En azından eyleme dönüştürülebilir bir metin çıkmalı.
    kayitOl.mockResolvedValue(false);
    await formuDoldurVeGonder();

    await waitFor(() => expect(kayitOl).toHaveBeenCalled());
    const uyari = await screen.findByRole('alert');
    expect(uyari.textContent ?? '').not.toHaveLength(0);
  });

  it('KONTROL KOLU: başarılı kayıtta doğrulama adımı ÇIKMAZ', async () => {
    // Koruma "her zaman göster"e dönüşmemeli.
    kayitOl.mockResolvedValue(true);
    await formuDoldurVeGonder();

    await waitFor(() => expect(kayitOl).toHaveBeenCalled());
    expect(screen.queryByRole('link', { name: /doğrulama/i })).not.toBeInTheDocument();
  });
});
