// ============================================================================
// KIRO2 — MSW handler seti. Kaynak: design/kiro-api.js (sözleşmenin çalışan mock'u).
// api-client 'live' modda / Storybook / Playwright smoke için ağ katmanını taklit eder.
// Hata zarfı { error: { code, message } }; sunucu-otoriter kanon (dogru yalnız answer'da).
// Ekranlar mock modda bu dosyaya ihtiyaç duymaz — bu, live/E2E yolu içindir.
// ============================================================================
import { http, HttpResponse } from 'msw';

import { buildMockPlanWeek, markEnZayif, type MockData } from './api-client';
import kiroData from './kiro-data.json';

const D = kiroData as unknown as MockData;

const hata = (code: string, message: string, status = 400) =>
  HttpResponse.json({ error: { code, message } }, { status });

export const kiroHandlers = [
  http.get('*/me', () => HttpResponse.json(D.persona)),
  http.get('*/engine', () => HttpResponse.json(D.engine)),
  http.get('*/subjects', () => HttpResponse.json(D.subjects)),
  http.get('*/topics', () => HttpResponse.json(D.topics)),
  http.get('*/exams/last', () => HttpResponse.json(D.lastExam)),
  http.get('*/assignments', () => HttpResponse.json(D.odevler ?? [])),
  http.get('*/review/due', () => HttpResponse.json((D.reviewQueue ?? []).filter((r) => r.dueIn === 0))),
  http.get('*/teacher/classes', () =>
    HttpResponse.json([{ id: 'c1', ad: '12-A', katilimKodu: '482913', ogrenci: (D.sinifRoster ?? []).length }]),
  ),

  // --- SPRINT5 Planlama uçları ---
  http.get('*/plan/week', () => HttpResponse.json(buildMockPlanWeek(D))),
  http.get('*/curriculum', () => HttpResponse.json(D.curriculum)),
  http.get('*/curriculum/:ders', ({ params }) => {
    const c = D.curriculum[params.ders as keyof typeof D.curriculum];
    return c ? HttpResponse.json(c) : hata('ders_yok', 'Ders bulunamadı.', 404);
  }),
  http.get('*/topics/:konu/atoms', ({ params }) => {
    const konu = decodeURIComponent(params.konu as string);
    const a = (D.atomKirilim ?? []).find((x) => x.konu === konu);
    return HttpResponse.json(a ? markEnZayif(a) : null);
  }),

  http.post('*/auth/login', async ({ request }) => {
    const b = (await request.json().catch(() => ({}))) as { eposta?: string };
    if (!b.eposta) return hata('eposta_gerekli', 'E-posta zorunlu.');
    return HttpResponse.json({ token: 'mock.jwt', refresh: 'mock.refresh' });
  }),
  http.post('*/auth/register', async ({ request }) => {
    const b = (await request.json().catch(() => ({}))) as { eposta?: string; ad?: string };
    if (!b.eposta) return hata('eposta_gerekli', 'E-posta zorunlu.');
    if (!b.ad || b.ad.trim().length < 2) return hata('ad_gerekli', 'Adını da alalım — sana adınla seslenelim.');
    return HttpResponse.json({ token: 'mock.jwt', refresh: 'mock.refresh' }, { status: 201 });
  }),
  http.post('*/auth/recover', () => HttpResponse.json({ ok: true })),
  http.post('*/assignments/:id/progress', async ({ params, request }) => {
    const b = (await request.json().catch(() => ({}))) as { cozulen?: number };
    return HttpResponse.json({ id: params.id, cozulen: b.cozulen ?? 0 });
  }),
];

export default kiroHandlers;
