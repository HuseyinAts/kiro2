/**
 * #516 — `ModernExamStart`'ın "session yoksa tam sınav yarat" dalı SİLİNDİ.
 *
 * Neden bu dosya var (ölçüldü, 21 Ağu 2026): `handleStartExam` içinde
 * `sessionId` yoksa `examService.createExam({ exam_type })` çağıran bir
 * fallback dalı vardı. O çağrı **subject taşımadığı** için TAM sınav ister
 * (TYT = 120 soru); canlı havuz karşılamıyor ve uç
 * `400 "Yeterli soru bulunamadı. Gerekli: 120, Mevcut: 33"` döndürüyordu —
 * yani dal çalışsaydı kullanıcıya ham backend hatası çıkacaktı.
 *
 * Dal ÖLÜYDÜ (yalnızca "kullanılmıyor" değil, ROTADAN ULAŞILAMAZ):
 *   • `ModernExamStart`'ı render eden tek yer `pages/ExamPage.tsx`
 *   • `ExamPage` tek bir rotaya bağlı: `App.tsx` → `path="/exam/:sinavId"`
 *   • `:sinavId` ZORUNLU bir segment → `useParams().sinavId` hep dolu
 *   • Dalı ekleyen commit'te (7d7025b71, 8 Mar 2026) de rota tablosu AYNIydı
 *     → dal "kaldırılmış bir rotadan artakalan" değil, baştan spekülatifti
 *
 * Bu dosya iki yarımı birlikte çiviler — biri diğeri olmadan yetmez:
 *   1. BİLEŞEN: `sessionId` yokken başlatma AÇIK hata verir ve `createExam`
 *      ÇAĞRILMAZ. (Silmeyi çivileyen assert budur.)
 *   2. ROTA TABLOSU: `ExamPage`'i render eden her rotanın `path`'i `:sinavId`
 *      içerir. Biri bu segmenti kaldırırsa silinen dalın YOKLUĞU gerçek bir
 *      hataya döner — o an bu test düşer.
 *
 * 🔴 Rota testi neden metin-tabanlı: `App.tsx` kendi `<BrowserRouter>`'ını
 * kurar, 150+ `lazy()` import + ServiceWorker/telemetri yan etkileri taşır;
 * render ederek rota tablosunu saymak bu dosyanın ölçmek istediği tek şeyi
 * (path ↔ element eşleşmesi) devasa bir kurulumun arkasına gömerdi.
 * Kaynak metni okumak burada DAHA doğrudan bir ölçüm. Yanlış-SIFIR'a karşı
 * korunmak için "en az 1 ExamPage rotası bulundu" DA assert ediliyor —
 * aksi halde bileşen yeniden adlandırıldığında test sessizce yeşil kalırdı.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { screen, waitFor, fireEvent } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import * as React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

import { ModernExamStart } from '../../../components/Exam/ModernExamStart';
import { examService, ExamType, ExamStatus } from '../../../services/examService';
import { server } from '../../mocks/server';
import { render } from '../../utils/test-utils';

// `import.meta.url` vite-node altında file:// DEĞİL → fileURLToPath patlar.
// vitest kökü `frontend/` (vite.config.ts), o yüzden cwd güvenilir ankraj.
const APP_TSX = resolve(process.cwd(), 'src/App.tsx');

/** Sistem kontrolü `/health`'e vurur; 4 kontrolün 4'ü de geçmeden
 *  "Sınavı Başlat" butonu `disabled` kalır. */
const saglikHandleri = http.get('/health', () => HttpResponse.json({ status: 'ok' }));

const sahteOturum = (sessionId: string) =>
  ({
    session_id: sessionId,
    exam_type: ExamType.TYT,
    status: ExamStatus.IN_PROGRESS,
  }) as never;

/**
 * Butonu açan üç koşulu sağlar: talimat okundu + kurallar kabul edildi +
 * sistem kontrolü geçti. Sonra "Sınavı Başlat"a basar.
 */
const sinaviBaslat = async () => {
  fireEvent.click(await screen.findByRole('checkbox', { name: /talimatlarını okudum/i }));
  fireEvent.click(screen.getByRole('checkbox', { name: /kurallarını kabul ediyorum/i }));

  // Sistem kontrolü bir MUI Dialog açar ve arkadaki sayfayı `aria-hidden`
  // yapar → kapatmadan "Sınavı Başlat" role sorgusuyla görünmez.
  fireEvent.click(screen.getByRole('button', { name: /Sistem Kontrolü/i }));
  await screen.findByText(/Sisteminiz sınav için hazır/i);
  fireEvent.click(screen.getByRole('button', { name: /^Kapat$/i }));

  const baslatButonu = await screen.findByRole('button', { name: /Sınavı Başlat/i });
  await waitFor(() => {
    expect(baslatButonu).toBeEnabled();
  });
  fireEvent.click(baslatButonu);
};

describe('ModernExamStart — #516 oturum kimliği yoksa AÇIK hata', () => {
  let createExamCasusu: ReturnType<typeof vi.spyOn>;
  let startExamCasusu: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    server.resetHandlers();
    server.use(saglikHandleri);
    // Canlıda ölçülen davranışı kodla: subject'siz create TAM sınav ister
    // (TYT=120) ve havuz karşılamadığı için 400 döner. Böylece SİLİNEN dal
    // hâlâ dursaydı test hızlıca "createExam çağrıldı"ya düşer — ağ
    // zaman aşımına değil.
    createExamCasusu = vi
      .spyOn(examService, 'createExam')
      .mockRejectedValue(new Error('Yeterli soru bulunamadı. Gerekli: 120, Mevcut: 33'));
    startExamCasusu = vi
      .spyOn(examService, 'startExam')
      .mockResolvedValue(sahteOturum('mevcut-oturum'));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sessionId YOKKEN createExam ÇAĞRILMAZ ve hata ekranda görünür', async () => {
    const onStart = vi.fn();
    render(<ModernExamStart examType={ExamType.TYT} onStart={onStart} />, {
      routerType: 'memory',
    });

    await sinaviBaslat();

    // Hata bandını bekle. Bu bekleme ESKİ kodda da karşılanır (fallback dalı
    // createExam'e gidip patlıyordu) — yani RED, aşağıdaki asıl assert'e düşer,
    // "hiç render olmadı" gibi bir yan sebebe değil.
    await screen.findByRole('alert');

    // 🔴 Silmeyi çivileyen assert: tam-TYT (subject'siz) create ASLA denenmez.
    // Eski kodda bu dal `createExam({exam_type:'TYT'})` çağırıp 400 alırdı.
    expect(createExamCasusu).not.toHaveBeenCalled();
    expect(startExamCasusu).not.toHaveBeenCalled();
    expect(onStart).not.toHaveBeenCalled();
    // Hata kullanıcıya GÖRÜNÜR (sessiz yutulma değil)
    expect(screen.getByText(/Oturum kimliği yok/i)).toBeInTheDocument();
  });

  it('sessionId VARKEN mevcut oturum başlatılır (altın yol bozulmadı)', async () => {
    const onStart = vi.fn();
    render(
      <ModernExamStart examType={ExamType.TYT} sessionId="oturum-42" onStart={onStart} />,
      { routerType: 'memory' },
    );

    await sinaviBaslat();

    await waitFor(() => {
      expect(startExamCasusu).toHaveBeenCalledWith('oturum-42');
    });
    expect(onStart).toHaveBeenCalledWith('oturum-42');
    // Mevcut oturum varken de yeni sınav yaratılmaz
    expect(createExamCasusu).not.toHaveBeenCalled();
    expect(screen.queryByText(/Oturum kimliği yok/i)).not.toBeInTheDocument();
  });
});

describe('App rota tablosu — #516 ExamPage her zaman :sinavId ile bağlanır', () => {
  const appKaynagi = readFileSync(APP_TSX, 'utf-8');

  /** `<Route ... />` bloklarını ayır; `<ExamPage` geçen her blok bir aday. */
  const examPageRotalari = appKaynagi
    .split('<Route')
    .slice(1)
    .filter((blok) => /<ExamPage\b/.test(blok));

  it('ExamPage en az bir rotada bağlı (yanlış-SIFIR koruması)', () => {
    // Bu assert olmasaydı bileşen yeniden adlandırıldığında aşağıdaki
    // döngü BOŞ küme üzerinde dönüp sessizce geçerdi.
    expect(examPageRotalari.length).toBeGreaterThanOrEqual(1);
    // Tembel import da adıyla duruyor mu — rename'i ikinci bir ankrajla yakala
    expect(appKaynagi).toMatch(/const ExamPage = lazy\(/);
  });

  it('ExamPage render eden HER rotanın path\'i :sinavId içerir', () => {
    for (const blok of examPageRotalari) {
      const yol = blok.match(/path="([^"]+)"/)?.[1];
      expect(yol, 'ExamPage rotasında path bulunamadı').toBeTruthy();
      // Segment zorunlu olmalı: ':sinavId' evet, ':sinavId?' HAYIR.
      // Opsiyonel yapılırsa sessionId yeniden undefined olabilir ve
      // silinen dalın yokluğu gerçek bir hataya döner.
      expect(yol, `ExamPage rotası "${yol}" zorunlu :sinavId taşımıyor`).toContain(':sinavId');
      expect(yol, `ExamPage rotası "${yol}" :sinavId'i OPSİYONEL yapmış`).not.toContain(
        ':sinavId?',
      );
    }
  });
});
