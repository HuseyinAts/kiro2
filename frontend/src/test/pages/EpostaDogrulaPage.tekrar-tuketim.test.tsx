/**
 * L2 — doğrulama token'ı YENİDEN TÜKETİLMEMELİ.
 *
 * CANLI ÖLÇÜM (26 Ağu 2026, Playwright + nginx ağ izi + DB):
 *   4.  GET  /js/index-CrlvyBKM.js   <- service worker'ın önbelleklediği ESKİ bundle
 *   21. POST /eposta-dogrula/verify  -> 200   (token TÜKETİLDİ, doğrulama BAŞARILI)
 *   43. GET  /eposta-dogrula?token=… <- SW güncellendi, sayfayı YENİDEN YÜKLEDİ
 *   46. GET  /js/index-DbwQm5xm.js   <- YENİ bundle
 *   64. POST /eposta-dogrula/verify  -> 400   (AYNI token, zaten tüketilmiş)
 *
 *   DB    : users.is_verified = TRUE   (18:11:40)
 *   EKRAN : "HTTP 400" + "Bağlantının süresi dolduysa yeni bir tane isteyin"
 *
 * Yani doğrulama BAŞARILI olduğu hâlde kullanıcıya BAŞARISIZ gösteriliyor.
 * Tetikleyiciler: service worker güncelleme yeniden yüklemesi · F5 · React 18
 * StrictMode'un efekti iki kez koşturması (`main.tsx:58` — geliştirmede HER
 * ZAMAN olur, yani bu kusur dev ortamında %100 tekrarlanabilir).
 *
 * 🔴 BU TEST NEDEN SAYIYOR, "MESAJ DOĞRU MU" DİYE BAKMIYOR
 * Kusur mesajda değil **çağrı sayısında**. Sadece son mesaja bakan bir test,
 * ikinci çağrı yapılmaya devam ederken de yeşile dönebilirdi (mesela hata
 * yutulsaydı). Ölçülen şey: uca kaç POST gitti.
 *
 * MSW kullanılıyor çünkü `authService`'i mocklamak `apiRequest`/fetch zincirini
 * atlar; bu kusur tam o zincirin ucunda (gerçek HTTP) yaşıyor.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import * as React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { EpostaDogrulaPage } from '../../pages/EpostaDogrulaPage';
import { server } from '../mocks/server';

const TOKEN = 'tkn-a1-tekrar-tuketim-olcumu';

/** Uca giden POST sayısı — testin ölçtüğü TEK şey bu. */
let cagriSayisi = 0;

/**
 * Gerçek backend sözleşmesi: token tek kullanımlık.
 * İlk POST 200, sonrakiler 400 `{"detail": ...}` (api/auth.py:2249-2253).
 */
function tekKullanimlikUc() {
  return http.post('*/api/v1/auth/eposta-dogrula/verify', () => {
    cagriSayisi += 1;
    if (cagriSayisi === 1) {
      return HttpResponse.json({
        status: 'verified',
        message: 'E-posta adresiniz doğrulandı. Artık giriş yapabilirsiniz.',
      });
    }
    return HttpResponse.json(
      { detail: 'Doğrulama bağlantısı geçersiz veya süresi dolmuş. Yeni bir bağlantı isteyin.' },
      { status: 400 },
    );
  });
}

function ekranaBas(token = TOKEN) {
  return render(
    <React.StrictMode>
      <MemoryRouter initialEntries={[`/eposta-dogrula?token=${token}`]}>
        <EpostaDogrulaPage />
      </MemoryRouter>
    </React.StrictMode>,
  );
}

beforeEach(() => {
  cagriSayisi = 0;
  sessionStorage.clear();
  server.use(tekKullanimlikUc());
});

afterEach(() => {
  sessionStorage.clear();
});

describe('EpostaDogrulaPage — token yeniden tüketimi', () => {
  it('ALET DOĞRULAMASI: sayaç gerçekten sayıyor ve uç 2. çağrıda 400 dönüyor', async () => {
    // Bu assert olmadan aşağıdaki "1 kere çağrıldı" testleri, uç HİÇ
    // çağrılmasa da (sayaç 0'da donsa da) yeşil görünürdü.
    const cevap1 = await fetch('/api/v1/auth/eposta-dogrula/verify', { method: 'POST' });
    const cevap2 = await fetch('/api/v1/auth/eposta-dogrula/verify', { method: 'POST' });
    expect(cevap1.status).toBe(200);
    expect(cevap2.status).toBe(400);
    expect(cagriSayisi).toBe(2);
  });

  it('tek yüklemede uç YALNIZ BİR KEZ çağrılır (StrictMode çift efekti dahil)', async () => {
    ekranaBas();
    await screen.findByText(/doğrulandı/i);
    // React 18 StrictMode efekti iki kez koşturur; koruma yoksa sayaç 2 olur
    // ve ikinci çağrı 400 dönüp ekranı hataya çevirir.
    expect(cagriSayisi).toBe(1);
  });

  it('BAŞARIDAN SONRA yeniden yükleme: uç TEKRAR çağrılmaz, başarı korunur', async () => {
    const ilk = ekranaBas();
    await screen.findByText(/doğrulandı/i);
    expect(cagriSayisi).toBe(1);

    // Tam sayfa yeniden yüklemesinin test karşılığı: bileşen sökülür ve AYNI
    // URL ile yeniden kurulur. (SW güncellemesi / F5 canlıda tam bunu yapıyor.)
    ilk.unmount();
    ekranaBas();

    expect(await screen.findByText(/doğrulandı/i)).toBeInTheDocument();
    expect(cagriSayisi, 'ikinci yükleme token’ı yeniden tüketti').toBe(1);
    expect(screen.queryByText(/HTTP 400/)).not.toBeInTheDocument();
  });

  it('GERÇEKTEN geçersiz token: hata ve kurtarma formu gösterilir', async () => {
    // Kontrol kolu: koruma "her şeyi başarı say"a dönüşmemeli. Bu token için
    // daha önce BAŞARI kaydı yok, dolayısıyla uç çağrılmalı ve hata görünmeli.
    server.use(
      http.post('*/api/v1/auth/eposta-dogrula/verify', () => {
        cagriSayisi += 1;
        return HttpResponse.json({ detail: 'Doğrulama bağlantısı geçersiz.' }, { status: 400 });
      }),
    );
    ekranaBas('bambaska-bir-token');

    await waitFor(() => expect(cagriSayisi).toBe(1));
    expect(await screen.findByRole('button', { name: /yeniden gönder/i })).toBeInTheDocument();
  });

  it('token TAŞIMAYAN bağlantı ucu HİÇ çağırmaz', async () => {
    render(
      <React.StrictMode>
        <MemoryRouter initialEntries={['/eposta-dogrula']}>
          <EpostaDogrulaPage />
        </MemoryRouter>
      </React.StrictMode>,
    );
    expect(await screen.findByText(/geçersiz bağlantı/i)).toBeInTheDocument();
    expect(cagriSayisi).toBe(0);
  });
});
