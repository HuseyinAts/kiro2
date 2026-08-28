/**
 * B3 — Konu Bazlı Kırılım (frontend sözleşme ölçümü)
 *
 * Neden bu dosya var: keşif turunda ölçüldü ki `/subject-performance` ucunu
 * tüketen TEK canlı yüzey `ModernExamResultsPage` ve bu sayfayı render eden
 * HİÇBİR test yoktu (`grep -rln "ModernExamResultsPage" src --include=*.test.tsx`
 * → 0 sonuç). MSW handler'ları da bu ucu mocklamıyordu, yani `tsc`/`build`/`eslint`
 * yeşil olsa bile tablonun konu kırılımını GERÇEKTEN gösterdiği ölçülmüyordu.
 *
 * Bu test fetch → apiRequest → sayfa zincirini uçtan uca koşturur (MSW ile),
 * yani gerçek sözleşmeyi ölçer.
 */

import { screen, waitFor, within } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import * as React from 'react';
import { Route, Routes } from 'react-router-dom';
import { describe, it, expect, beforeEach } from 'vitest';

import ModernExamResultsPage from '../../pages/ModernExamResultsPage';
import { server } from '../mocks/server';
import { render } from '../utils/test-utils';

const SINAV_ID = 'sess-b3';

const performansGovdesi = {
  total_questions: 6,
  correct_answers: 3,
  wrong_answers: 2,
  empty_answers: 1,
  raw_score: 50,
};

const oturumGovdesi = {
  exam_type: 'tyt',
  duration_minutes: 30,
  started_at: '2026-08-21T09:00:00Z',
  completed_at: '2026-08-21T09:20:00Z',
};

/** Ortak uçlar: performance + session. subject-performance testte ayrı verilir. */
const ortakHandlerlar = () => [
  http.get(`/api/v1/osym-exam/${SINAV_ID}/performance`, () =>
    HttpResponse.json(performansGovdesi),
  ),
  http.get(`/api/v1/osym-exam/${SINAV_ID}/session`, () =>
    HttpResponse.json(oturumGovdesi),
  ),
];

// test-utils'in `render`'ı zaten MemoryRouter sarmalıyor (initialEntries ile);
// burada ikinci bir Router açmak "You cannot render a <Router> inside another
// <Router>" hatası verir — yalnız Routes veriyoruz.
const sayfayiKur = () =>
  render(
    <Routes>
      <Route path="/exam/:sinavId/results" element={<ModernExamResultsPage />} />
    </Routes>,
    // routerType varsayılanı 'browser' — o dalda initialEntries YOK SAYILIR ve
    // URL "/" kalır, rota eşleşmez (ölçüldü: body tamamen boş <div /> döndü).
    { routerType: 'memory', initialEntries: [`/exam/${SINAV_ID}/results`] },
  );

/** "Konu Bazlı Performans" tablosunun başlık + gövde satırlarını döndürür. */
const tabloSatirlari = () => {
  const tablolar = screen.getAllByRole('table');
  const tablo = tablolar[tablolar.length - 1];
  const basliklar = within(tablo).getAllByRole('columnheader');
  const govdeSatirlari = within(tablo)
    .getAllByRole('row')
    .slice(1); // 0. satır başlık satırı
  return { tablo, basliklar, govdeSatirlari };
};

describe('ModernExamResultsPage — B3 konu bazlı kırılım', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('aynı dersin farklı konuları AYRI satır olarak gösterilir', async () => {
    server.use(
      ...ortakHandlerlar(),
      http.get(`/api/v1/osym-exam/${SINAV_ID}/subject-performance`, () =>
        HttpResponse.json([
          {
            subject: 'MATEMATIK',
            topic_code: 'MAT.KMB',
            topic_name: 'Kombinasyon',
            total_questions: 3,
            correct_answers: 2,
            wrong_answers: 1,
            empty_answers: 0,
            success_rate: 66.7,
            average_response_time: 40,
            difficulty_level: 3,
          },
          {
            subject: 'MATEMATIK',
            topic_code: 'MAT.OLS',
            topic_name: 'Olasılık',
            total_questions: 2,
            correct_answers: 1,
            wrong_answers: 1,
            empty_answers: 0,
            success_rate: 50,
            average_response_time: 55,
            difficulty_level: 3,
          },
          {
            subject: 'MATEMATIK',
            topic_code: null,
            topic_name: 'Konu atanmamis',
            total_questions: 1,
            correct_answers: 0,
            wrong_answers: 0,
            empty_answers: 1,
            success_rate: 0,
            average_response_time: 0,
            difficulty_level: 3,
          },
        ]),
      ),
    );

    sayfayiKur();

    // Üç konu da AYRI satır olmalı (eski davranışta tek "MATEMATIK" satırı vardı)
    expect(await screen.findByText('Kombinasyon')).toBeInTheDocument();
    expect(screen.getByText('Olasılık')).toBeInTheDocument();
    expect(screen.getByText('Konu atanmamis')).toBeInTheDocument();

    const { basliklar, govdeSatirlari } = tabloSatirlari();

    // Başlık artık tek "Konu" değil, "Ders" + "Konu"
    const baslikMetinleri = basliklar.map((h) => h.textContent);
    expect(baslikMetinleri).toEqual(['Ders', 'Konu', 'Doğru', 'Yanlış', 'Boş', 'Başarı', 'Durum']);

    // 3 kova => 3 gövde satırı
    expect(govdeSatirlari).toHaveLength(3);

    // Hizalama: her gövde satırının hücre sayısı başlık sayısına EŞİT olmalı
    for (const satir of govdeSatirlari) {
      expect(within(satir).getAllByRole('cell')).toHaveLength(basliklar.length);
    }

    // İlk satır: ders hücresi MATEMATIK, konu hücresi Kombinasyon
    const ilkSatirHucreleri = within(govdeSatirlari[0]).getAllByRole('cell');
    expect(ilkSatirHucreleri[0]).toHaveTextContent('MATEMATIK');
    expect(ilkSatirHucreleri[1]).toHaveTextContent('Kombinasyon');
  });

  it('backend topic_name göndermezse konu hücresi ders adına düşer (geri uyum)', async () => {
    server.use(
      ...ortakHandlerlar(),
      http.get(`/api/v1/osym-exam/${SINAV_ID}/subject-performance`, () =>
        HttpResponse.json([
          {
            subject: 'TURKCE',
            total_questions: 6,
            correct_answers: 3,
            wrong_answers: 2,
            empty_answers: 1,
            success_rate: 50,
            average_response_time: 45,
            difficulty_level: 3,
          },
        ]),
      ),
    );

    sayfayiKur();

    await waitFor(() => {
      expect(screen.getAllByRole('table').length).toBeGreaterThan(0);
    });

    const { basliklar, govdeSatirlari } = tabloSatirlari();
    expect(govdeSatirlari).toHaveLength(1);

    const hucreler = within(govdeSatirlari[0]).getAllByRole('cell');
    expect(hucreler).toHaveLength(basliklar.length);
    expect(hucreler[0]).toHaveTextContent('TURKCE');
    // topic_name yok => `|| s.subject` devreye girer, hücre BOŞ KALMAZ
    expect(hucreler[1]).toHaveTextContent('TURKCE');
  });
});
