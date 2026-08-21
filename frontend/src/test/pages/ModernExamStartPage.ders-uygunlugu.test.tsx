/**
 * #514 — Ders açılır listesi: içeriği OLMAYAN dersler görünür ama TIKLANAMAZ.
 *
 * Neden bu dosya var (ölçüldü, 21 Ağu 2026): `ModernExamStartPage` 8 TYT dersini
 * sabit kodluyordu, ama sayfanın GÖNDERDİĞİ payload ile canlı uca vurulduğunda
 * 8 seçeneğin **6'sı HTTP 400** ("Mevcut: 0") döndürüyordu. Yani öğrencinin
 * gördüğü seçeneklerin çoğu ham backend hatasına çıkıyordu.
 *
 * Bu test uygunluk zincirini uçtan uca koşturur (MSW → apiRequest → sayfa):
 *   GET /api/v1/osym/subjects  →  data[].subject (ASCII etiket)  →  MenuItem disabled
 *
 * 🔴 Üç şeyi ÇİVİLER:
 *   1. `question_count` EKRANA YAZILMAZ (uç `question_bank` toplamını verir,
 *      motor `mv_safe_for_beta`'dan servis eder — sayı tutmaz, iddia edilemez).
 *   2. 'Türkçe' → 'TURKCE' eşlemesi AÇIK TABLODAN gelir. `.toUpperCase()`
 *      JS'te 'TÜRKÇE' üretir ve API'nin 'TURKCE'siyle ASLA eşleşmez.
 *   3. FAIL-OPEN: uç hata verirse hiçbir ders kapatılmaz (altın yol açık kalır).
 */

import { screen, waitFor, within, fireEvent } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import * as React from 'react';
import { describe, it, expect, beforeEach } from 'vitest';

import ModernExamStartPage, { DERS_API_ETIKETI } from '../../pages/ModernExamStartPage';
import { server } from '../mocks/server';
import { render } from '../utils/test-utils';

const DERSLER_UCU = '/api/v1/osym/subjects';

/** Uç, ders başına `question_count` DA döndürür — testte bilerek dolduruyoruz ki
 *  o sayının ekrana sızmadığını assert edebilelim. */
const uygunlukHandleri = (asciiEtiketler: string[]) =>
  http.get(DERSLER_UCU, () =>
    HttpResponse.json({
      success: true,
      data: asciiEtiketler.map((etiket) => ({
        subject: etiket,
        question_count: 3531,
      })),
      count: asciiEtiketler.length,
    }),
  );

const sayfayiKur = () => render(<ModernExamStartPage />, { routerType: 'memory' });

/**
 * "Ders" açılır listesini açar ve seçenekleri döndürür.
 * Sayfada iki Select var: 0 = Sınav Türü, 1 = Ders (DOM sırası).
 */
const dersMenusunuAc = async () => {
  const seciciler = await screen.findAllByRole('combobox');
  expect(seciciler.length).toBeGreaterThanOrEqual(2);
  // Ankraj: ders seçicisi varsayılan değeri ('Matematik') gösteriyor olmalı.
  expect(seciciler[1]).toHaveTextContent('Matematik');
  fireEvent.mouseDown(seciciler[1]);
  return screen.findAllByRole('option');
};

/** MUI Select, MenuItem'lara `data-value` koyar — etiketle güvenli eşleşme. */
const secenek = (etiket: string): HTMLElement => {
  const bulunan = screen
    .getAllByRole('option')
    .find((o) => o.getAttribute('data-value') === etiket);
  if (!bulunan) {
    throw new Error(`"${etiket}" seçeneği bulunamadı`);
  }
  return bulunan;
};

const kapaliMi = (el: HTMLElement) => el.getAttribute('aria-disabled') === 'true';

describe('ModernExamStartPage — #514 ders uygunluğu', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  it('içeriği OLAN dersler tıklanabilir kalır, question_count EKRANA YAZILMAZ', async () => {
    server.use(uygunlukHandleri(['KIMYA', 'MATEMATIK']));

    sayfayiKur();
    await dersMenusunuAc();

    await waitFor(() => {
      expect(kapaliMi(secenek('Matematik'))).toBe(false);
    });
    expect(kapaliMi(secenek('Kimya'))).toBe(false);

    // Açık olan derste "hazırlanıyor" gerekçesi GÖRÜNMEZ
    expect(within(secenek('Matematik')).queryByText(/hazırlanıyor/i)).toBeNull();

    // 🔴 question_count hiçbir biçimde ekranda olmamalı (3531 / 3.531)
    expect(screen.queryByText(/3\.?531/)).not.toBeInTheDocument();
  });

  it('içeriği OLMAYAN dersler görünür ama KAPALI ve gerekçesi yazıyor', async () => {
    server.use(uygunlukHandleri(['KIMYA', 'MATEMATIK']));

    sayfayiKur();
    await dersMenusunuAc();

    // 6 kova canlıda HTTP 400 dönüyordu — hepsi listede KALIR ama kapalıdır
    for (const etiket of ['Geometri', 'Türkçe', 'Fizik', 'Biyoloji', 'Tarih', 'Sosyal']) {
      await waitFor(() => {
        expect(kapaliMi(secenek(etiket))).toBe(true);
      });
      // Seçenek listeden SİLİNMEDİ (kullanıcı kapsamı görmeye devam ediyor)
      expect(within(secenek(etiket)).getByText(etiket)).toBeInTheDocument();
      // Gerekçe görünür
      expect(within(secenek(etiket)).getByText(/hazırlanıyor/i)).toBeInTheDocument();
    }
  });

  it('Türkçe → TURKCE eşlenir (.toUpperCase() regresyonunu öldürür)', async () => {
    // Uç 'TURKCE' diyor. Naif `'Türkçe'.toUpperCase()` === 'TÜRKÇE' ≠ 'TURKCE'
    // olduğu için Türkçe'yi YANLIŞ SEBEPLE kapatırdı.
    server.use(uygunlukHandleri(['TURKCE']));

    sayfayiKur();
    await dersMenusunuAc();

    await waitFor(() => {
      expect(kapaliMi(secenek('Türkçe'))).toBe(false);
    });
    // Ayırt edici: fail-open ile karışmasın diye içeriği OLMAYAN ders KAPALI olmalı
    expect(kapaliMi(secenek('Matematik'))).toBe(true);
  });

  it('eşleme tablosu ASCII etiket üretir — locale kaymasına yer yok', () => {
    expect(DERS_API_ETIKETI['Türkçe']).toBe('TURKCE');
    expect(DERS_API_ETIKETI['Matematik']).toBe('MATEMATIK');
    expect(DERS_API_ETIKETI['Geometri']).toBe('GEOMETRI');
    expect(DERS_API_ETIKETI['Biyoloji']).toBe('BIYOLOJI');
    expect(DERS_API_ETIKETI['Tarih']).toBe('TARIH');

    // Hiçbir değer Türkçe'ye özgü karakter TAŞIMAZ (ASCII-only sözleşme)
    for (const [etiket, ascii] of Object.entries(DERS_API_ETIKETI)) {
      expect(ascii, `${etiket} → ${ascii}`).toMatch(/^[A-Z ]+$/);
    }

    // Sayfadaki 9 UI etiketinin hepsi tabloda karşılığını bulur
    for (const etiket of [
      'Matematik', 'Geometri', 'Türkçe', 'Fizik', 'Kimya',
      'Biyoloji', 'Tarih', 'Sosyal', 'Edebiyat',
    ]) {
      expect(DERS_API_ETIKETI[etiket], `${etiket} eşlenmemiş`).toBeTruthy();
    }
  });

  it('FAIL-OPEN: uç 500 dönerse HİÇBİR ders kapanmaz', async () => {
    server.use(
      http.get(DERSLER_UCU, () =>
        HttpResponse.json({ detail: 'sunucu hatası' }, { status: 500 }),
      ),
    );

    sayfayiKur();
    const secenekler = await dersMenusunuAc();

    // Uç ölçülemedi → bugünkü davranışa dön: hepsi açık (altın yol TYT/Matematik/40 yaşar)
    await waitFor(() => {
      expect(secenekler.some((o) => kapaliMi(o))).toBe(false);
    });
    expect(kapaliMi(secenek('Matematik'))).toBe(false);
    expect(kapaliMi(secenek('Türkçe'))).toBe(false);
    expect(screen.queryByText(/hazırlanıyor/i)).not.toBeInTheDocument();
  });

  it('FAIL-OPEN: ağ hatasında da hiçbir ders kapanmaz', async () => {
    server.use(http.get(DERSLER_UCU, () => HttpResponse.error()));

    sayfayiKur();
    const secenekler = await dersMenusunuAc();

    await waitFor(() => {
      expect(secenekler.some((o) => kapaliMi(o))).toBe(false);
    });
  });
});
