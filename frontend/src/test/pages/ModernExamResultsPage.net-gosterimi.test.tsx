/**
 * A1 kabul kriterinin son ayağı: öğrenci **netini** görür.
 *
 * ÖLÇÜLEN KUSUR (27 Ağu 2026)
 * ---------------------------
 * Zincirin 5 hopunun 4'ü canlı yeşildi; kriter en son hopta düşüyordu:
 *
 *     ModernExamResultsPage.tsx:119   score: perfData.raw_score
 *
 * Aynı `fetch` (`:84 GET /api/v1/osym-exam/{sid}/performance`) `net_score`'u DA
 * döndürüyor ama mapper onu hiç okumuyordu. Kaynakta ve dağıtılan pakette
 * `net_score` **0 eşleşme**. Ekran `raw_score`'u — ki o bir YÜZDE — birimsiz,
 * dev puntoda basıyordu.
 *
 * Yani öğrenci "40 soruluk testi çöz → **netini** gör" akışının sonunda netini
 * DEĞİL, yüzdesini görüyordu; üstelik hangisi olduğunu söyleyen bir etiket de
 * yoktu.
 *
 * 🔴 `score` ALANI KALDIRILMIYOR. Yüzde eşiklerinde kullanılıyor
 * (`getScoreGradient/Icon/Message`, 85/70/50). Net en fazla soru sayısı kadar
 * olabildiği için `score`'u net ile değiştirmek o eşikleri sessizce ölü hâle
 * getirirdi (`net >= 85` asla doğru olmaz). Bu yüzden `net` EKLENİYOR ve
 * daire artık `% başarı` diye ETİKETLENİYOR.
 */

import { screen, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import * as React from 'react';
import { Route, Routes } from 'react-router-dom';
import { describe, it, expect, beforeEach } from 'vitest';

import ModernExamResultsPage from '../../pages/ModernExamResultsPage';
import { server } from '../mocks/server';
import { render } from '../utils/test-utils';

const SINAV_ID = 'sess-net';

/**
 * 6 doğru + 8 yanlış → ÖSYM neti 6 − 8/4 = 4.0 (canlı proplandı, 27 Ağu).
 *
 * 🔴 HER SAYI AYIRT EDİCİ. İlk yazdığımda boş da 6'ydı ve alet doğrulaması
 * "Found multiple elements with the text: 6" ile düştü — yani test kodu ölçmek
 * istediği şeyi DEĞİL, kendi fixture çakışmasını ölçmüştü. `19/6/8/5/4/30`
 * kümesinde hiçbir değer tekrar etmiyor, dolayısıyla bulunan her eşleşme
 * TEK bir alana izlenebilir.
 */
const performansGovdesi = {
  total_questions: 19,
  correct_answers: 6,
  wrong_answers: 8,
  empty_answers: 5,
  net_score: 4.0,
  raw_score: 30.0, // yüzde — net DEĞİL
};

const oturumGovdesi = {
  exam_type: 'tyt',
  duration_minutes: 30,
  started_at: '2026-08-27T09:00:00Z',
  completed_at: '2026-08-27T09:20:00Z',
};

const handlerlar = (perf: Record<string, unknown> = performansGovdesi) => [
  http.get(`/api/v1/osym-exam/${SINAV_ID}/performance`, () => HttpResponse.json(perf)),
  http.get(`/api/v1/osym-exam/${SINAV_ID}/session`, () => HttpResponse.json(oturumGovdesi)),
  http.get(`/api/v1/osym-exam/${SINAV_ID}/subject-performance`, () => HttpResponse.json([])),
];

const sayfayiKur = () =>
  render(
    <Routes>
      <Route path="/exam/:sinavId/results" element={<ModernExamResultsPage />} />
    </Routes>,
    { routerType: 'memory', initialEntries: [`/exam/${SINAV_ID}/results`] },
  );

beforeEach(() => {
  server.resetHandlers();
});

describe('ModernExamResultsPage — net gösterimi', () => {
  it('ALET DOĞRULAMASI: sayfa gerçekten render oluyor ve veriyi çekiyor', async () => {
    // Bu assert olmadan aşağıdakiler, sayfa hiç render olmasa da
    // "net görünmüyor" diye YANLIŞ SEBEPLE geçerdi.
    server.use(...handlerlar());
    sayfayiKur();
    expect(await screen.findByText('6')).toBeInTheDocument(); // doğru sayısı
    expect(screen.getByText('8')).toBeInTheDocument(); // yanlış sayısı
  });

  it('NET ekranda ETİKETLİ olarak gösterilir', async () => {
    server.use(...handlerlar());
    sayfayiKur();

    const netEtiketi = await screen.findByText(/^Net$/);
    const kutu = netEtiketi.closest('div');
    expect(kutu, 'Net etiketinin kapsayıcısı yok').not.toBeNull();
    expect(within(kutu as HTMLElement).getByText('4')).toBeInTheDocument();
  });

  it('NEGATİF net gizlenmez (kırpma yok — backend kanonuyla aynı karar)', async () => {
    // `core/osym_puanlama.py`: net 0'a kırpılmaz; ekran da kırpmamalı,
    // yoksa öğrenci "0 net" görüp "hiç değilse sıfırdayım" sanar.
    server.use(
      ...handlerlar({
        ...performansGovdesi,
        total_questions: 13,
        correct_answers: 0,
        empty_answers: 5,
        net_score: -2.0,
      }),
    );
    sayfayiKur();

    const netEtiketi = await screen.findByText(/^Net$/);
    const kutu = netEtiketi.closest('div') as HTMLElement;
    expect(within(kutu).getByText('-2')).toBeInTheDocument();
  });

  it('yüzde dairesi ETİKETLENİR — birimsiz sayı net sanılmamalı', async () => {
    server.use(...handlerlar());
    sayfayiKur();
    expect(await screen.findByText(/% başarı/i)).toBeInTheDocument();
  });

  it('yüzde HAM kayan nokta olarak basılmaz', async () => {
    // Canlı proplandı (27 Ağu): 11 doğru / 40 soru -> backend raw_score
    // 27.500000000000004 dönüyor ve daire bunu 17 haneli olarak basıyordu;
    // metin dairenin dışına taşıyordu. Alt karttaki "Başarı Oranı" zaten
    // `.toFixed(1)` kullanıyor — ev geleneği bu, daire ona uymuyordu.
    server.use(...handlerlar({ ...performansGovdesi, raw_score: 27.500000000000004 }));
    sayfayiKur();

    expect(await screen.findByText('27.5')).toBeInTheDocument();
    expect(screen.queryByText('27.500000000000004')).not.toBeInTheDocument();
  });

  it('tam sayı yüzde gereksiz ".0" ile basılmaz', async () => {
    // `.toFixed(1)` tek başına 85 -> "85.0" yapardı. Manşet sayı için çirkin;
    // bu yüzden biçimlendirme sondaki sıfırı düşürüyor.
    server.use(...handlerlar({ ...performansGovdesi, raw_score: 85 }));
    sayfayiKur();

    expect(await screen.findByText('85')).toBeInTheDocument();
    expect(screen.queryByText('85.0')).not.toBeInTheDocument();
  });

  it('en düşük bant mesajı öğrenciye "başarısız olabilirsin" DEMEZ', async () => {
    // Bu mesajı en çok öğrenci görüyor (score < 50). Metin bozuktu:
    // "Pes etmeyin, başarısız olabilirsiniz!" — yani "pes etme, başaramayabilirsin".
    // Öğrenciyi cesaretlendirmesi gereken cümle tam tersini söylüyordu.
    server.use(...handlerlar({ ...performansGovdesi, raw_score: 27.5 }));
    sayfayiKur();

    // POZİTİF ANKRAJ ÖNCE: yoksa sayfa hiç render olmasa da "yok" testi geçerdi.
    const mesaj = await screen.findByText(/Daha fazla çalışmanız gerekiyor/);
    expect(mesaj.textContent).not.toMatch(/başarısız olabilirsiniz/);
    expect(mesaj.textContent).toMatch(/başarabilirsiniz/);
  });

  it('en yüksek bant mesajında bitişik kelime yok', async () => {
    // "sergiledinizyürümeye" — iki kelime kaynaşmış.
    server.use(...handlerlar({ ...performansGovdesi, raw_score: 90 }));
    sayfayiKur();

    const mesaj = await screen.findByText(/Mükemmel!/);
    expect(mesaj.textContent).not.toMatch(/sergiledinizyürümeye/);
    expect(mesaj.textContent).toMatch(/sergilediniz/);
  });

  it('KONTROL KOLU: yüzde eşik mantığı net ile DEĞİL raw_score ile besleniyor', async () => {
    // `score`'u net ile değiştirseydik 85/70/50 eşikleri sessizce ölürdü.
    // raw_score=30 -> "geliştirilmeli" bandı; net=4 olsaydı da aynı banda
    // düşerdi, bu yüzden ayırt edici bir değer seçiliyor: raw_score=90.
    server.use(...handlerlar({ ...performansGovdesi, raw_score: 90.0, net_score: 4.0 }));
    sayfayiKur();

    // 90 yüzdesi dairede görünmeli (net 4 değil).
    expect(await screen.findByText('90')).toBeInTheDocument();
  });
});
