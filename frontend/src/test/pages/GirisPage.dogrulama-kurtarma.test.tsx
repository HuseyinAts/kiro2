/**
 * Giriş ekranı: doğrulanmamış kullanıcıya DOĞRU sebebi ve KURTARMA yolunu göster.
 *
 * ÖLÇÜLEN İKİ KUSUR (26 Ağu 2026)
 * -------------------------------
 * 1) YANLIŞ TEŞHİS. Backend `api/auth.py:802-805` giriş engellendiğinde
 *    403 + {"detail":{"code":"EPOSTA_DOGRULANMAMIS","message":"Giriş yapabilmek
 *    için e-posta adresinizi doğrulayın."}} döndürüyor. `authStore.ts:203` bu
 *    metni `error` alanına DOĞRU şekilde yazıyor — ama `GirisPage.tsx:172`
 *    onu ATIP sabit "E-posta ya da şifre eşleşmedi" yazıyordu. Kullanıcı
 *    şifresini yanlış sanıp sıfırlamaya gidiyordu; tam da `api/auth.py:686-688`'in
 *    401 yerine 403 seçerek ÖNLEMEK istediği sonuç.
 *
 * 2) KURTARMA YOLU YOK. Ölçüldü: `frontend/src`'de `EPOSTA_DOGRULANMAMIS`
 *    **0 eşleşme**, `/eposta-dogrula`'ya giden **0 href/navigate**. Postayı
 *    almayan veya silen kullanıcının tek yolu URL'yi ELLE yazmaktı.
 *
 * Bu iki kusur `EPOSTA_DOGRULAMA_ZORUNLU` kapısının ÖN KOŞULU: kapı açıldığı
 * anda doğrulanmamış her kullanıcı yanlış sebep görür ve çıkış yolu bulamaz.
 *
 * 🔴 `GirisPage` SAF SUNUM BİLEŞENİ — store'a erişmiyor, `onLogin` prop olarak
 * enjekte ediliyor (tek tüketici: `kiro/routes/KiroLoginRoute.tsx`). Bu yüzden
 * test store'u değil SÖZLEŞMEYİ ölçer: `onLogin` bir hata mesajı döndürdüğünde
 * ekran ne yapıyor.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as React from 'react';
import { describe, expect, it, vi } from 'vitest';

import { GirisPage } from '../../kiro/screens/GirisPage';

const KAPI_MESAJI = 'Giriş yapabilmek için e-posta adresinizi doğrulayın.';
const ESKI_SABIT = /şifre eşleşmedi/i;

async function girisDene(onLogin: ReturnType<typeof vi.fn>) {
  const kullanici = userEvent.setup();
  render(<GirisPage onLogin={onLogin} onLanding={() => {}} />);

  await kullanici.type(screen.getByLabelText(/e-posta adresin/i), 'ogrenci@ornek.com');
  await kullanici.type(screen.getByLabelText(/şifren/i), 'Zq7#Kv2!Rm9x');
  await kullanici.click(screen.getByRole('button', { name: /devam edelim/i }));
  return kullanici;
}

describe('GirisPage — doğrulanmamış e-posta kurtarma yolu', () => {
  it('ALET DOĞRULAMASI: form gerçekten gönderiliyor ve onLogin çağrılıyor', async () => {
    // Bu assert olmadan aşağıdaki testler, form hiç gönderilmese de
    // "sabit metin görünmüyor" diye YANLIŞ SEBEPLE geçerdi.
    const onLogin = vi.fn().mockResolvedValue(true);
    await girisDene(onLogin);
    await waitFor(() => expect(onLogin).toHaveBeenCalledTimes(1));
    expect(onLogin).toHaveBeenCalledWith({
      eposta: 'ogrenci@ornek.com',
      sifre: 'Zq7#Kv2!Rm9x',
    });
  });

  it('sunucunun GERÇEK sebebi gösterilir, sabit metin DEĞİL', async () => {
    const onLogin = vi.fn().mockResolvedValue({ hata: KAPI_MESAJI });
    await girisDene(onLogin);

    expect(await screen.findByText(KAPI_MESAJI)).toBeInTheDocument();
    expect(screen.queryByText(ESKI_SABIT)).not.toBeInTheDocument();
  });

  it('başarısız girişte /eposta-dogrula KURTARMA bağlantısı görünür', async () => {
    const onLogin = vi.fn().mockResolvedValue({ hata: KAPI_MESAJI });
    await girisDene(onLogin);

    const baglanti = await screen.findByRole('link', { name: /doğrulama/i });
    expect(baglanti).toHaveAttribute('href', '/eposta-dogrula');
  });

  it('mesajsız başarısızlıkta ESKİ metin korunur (geriye uyum)', async () => {
    // `onLogin` hâlâ düz `false` döndürebilir (sözleşme GENİŞLETİLDİ, kırılmadı).
    const onLogin = vi.fn().mockResolvedValue(false);
    await girisDene(onLogin);
    expect(await screen.findByText(ESKI_SABIT)).toBeInTheDocument();
  });

  it('KONTROL KOLU: başarılı girişte ne hata ne kurtarma bağlantısı çıkar', async () => {
    // Koruma "her zaman göster"e dönüşmemeli — aksi hâlde bağlantı testi,
    // bileşen hiçbir şey ölçmese de geçerdi.
    const onLogin = vi.fn().mockResolvedValue(true);
    await girisDene(onLogin);

    await waitFor(() => expect(onLogin).toHaveBeenCalled());
    expect(screen.queryByText(KAPI_MESAJI)).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /doğrulama/i })).not.toBeInTheDocument();
  });

  it('2FA dalı BOZULMADI (önceden var olan davranış)', async () => {
    const onLogin = vi.fn().mockResolvedValue('2fa_required');
    await girisDene(onLogin);

    // 2FA adımına geçilir: 6 haneli kod alanı belirir, hata kutusu çıkmaz.
    expect(await screen.findByPlaceholderText('123456')).toBeInTheDocument();
    expect(screen.queryByText(ESKI_SABIT)).not.toBeInTheDocument();
  });
});
