// ============================================================================
// KIRO2 — MSW handler seti. Kaynak: design/kiro-api.js (sözleşmenin çalışan mock'u).
// api-client 'live' modda / Storybook / Playwright smoke için ağ katmanını taklit eder.
// Hata zarfı { error: { code, message } }; sunucu-otoriter kanon (dogru yalnız answer'da).
// Ekranlar mock modda bu dosyaya ihtiyaç duymaz — bu, live/E2E yolu içindir.
// ============================================================================
import { http, HttpResponse } from 'msw';

import { buildMockPlanWeek, markEnZayif, seviyeBilgiFrom, type MockData } from './api-client';
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

  // --- SPRINT8 · Grup 6 Oyunlaştırma uçları ---
  // /level — Lig kompozisyonu getLevel() için (getLeague live → /me + /level).
  http.get('*/level', () => HttpResponse.json(seviyeBilgiFrom(D.seviyeEsik, D.persona.xp))),

  // Lig — backend snake_case DTO (client snake→camel + /me/level ile map eder).
  http.get('*/api/v1/leagues/current', () =>
    HttpResponse.json({
      tier: D.league.tier,
      rank: D.league.rank,
      weekly_xp: D.league.haftalikXp,
      total_in_tier: D.league.tierToplam,
      week_start: '2026-07-20',
      standings: D.league.standings.map((s) => ({
        student_id: s.studentId,
        display_name: s.ad,
        xp: s.xp,
        rank: s.rank,
        is_self: s.benMi,
      })),
    }),
  ),

  // Düello — gerçek backend snake_case sözleşmesi (STRIP'li: correct_answer sızmaz).
  http.post('*/api/v1/duel/matchmake', () =>
    HttpResponse.json({ status: 'matched', session_id: 'duel-msw', message: 'Eşleşme bulundu!' }),
  ),
  http.get('*/api/v1/duel/rating', () =>
    HttpResponse.json({ elo_rating: 1240, wins: 14, losses: 6, draws: 2, peak_rating: 1310 }),
  ),
  http.get('*/api/v1/duel/:id/current-question', ({ params }) => {
    const q = D.questionBank.find((x) => x.ders === 'mat');
    const opts: Record<string, string> = {};
    (q?.secenekler ?? []).forEach((s, i) => { opts['ABCDE'[i]!] = s; });
    return HttpResponse.json({
      session_id: params.id,
      status: 'active',
      question_order: 0,
      question_id: q?.id ?? 'mat-turev-1',
      question_text: q?.soru ?? '',
      options: opts,
      time_per_question_sec: q?.sure ?? 60,
      total_questions: 5,
      player1_score: 0,
      player2_score: 0,
      answered: false,
    });
  }),
  http.post('*/api/v1/duel/:id/answer', async ({ request }) => {
    const b = (await request.json().catch(() => ({}))) as { question_order?: number };
    return HttpResponse.json({
      round_complete: true,
      question_order: b.question_order ?? 0,
      player1_score: 1,
      player2_score: 0,
      is_correct: true,
    });
  }),
  http.get('*/api/v1/duel/:id/result', ({ params }) =>
    HttpResponse.json({
      session_id: params.id,
      status: 'finished',
      subject: 'MATEMATIK',
      finished: true,
      my_score: 3,
      opponent_score: 2,
      won: true,
      draw: false,
      elo_change: 18,
      finished_at: '2026-07-22T12:00:00Z',
    }),
  ),
  // Not: SSE (/api/v1/duel/stream/:id) MSW ile taklit edilmez — EventSource E2E'de
  // gerçek backend'e bağlanır; jsdom/Storybook mock kolu setTimeout server-sim kullanır.

  // Arkadaş Serisi — client sözleşmesi (camelCase; backend ileri faz).
  http.get('*/friends', () => HttpResponse.json(D.friends)),
  http.post('*/friends/:id/nudge', () => HttpResponse.json({ durum: 'sent' })),
  http.post('*/friends/:id/congrats', () => HttpResponse.json({ gonderildi: true })),

  // Seri Dondurma — client sözleşmesi (camelCase; backend YOK, freeze mock).
  http.get('*/streak', () => HttpResponse.json(D.streak)),

  // --- SPRINT9 · Grup 7-A Rol panelleri (best-effort; SSE yok) ---
  // Veli — dashboard + children + performance kompoze (client snake VEYA camel okur).
  http.get('*/parent/dashboard', () => HttpResponse.json(D.veliDashboard)),
  http.get('*/parent/children', () => HttpResponse.json(D.veliDashboard.cocuklar)),
  http.get('*/parent/children/:id/performance', () =>
    HttpResponse.json({ kpi: D.veliDashboard.kpi, haftalik: D.veliDashboard.haftalik }),
  ),

  // Öğretmen — students + reports (classes handler yukarıda mevcut, çift kayıt YOK).
  http.get('*/teacher/students', () => HttpResponse.json(D.ogretmenPanel.ogrenciler)),
  http.get('*/teacher/reports', () =>
    HttpResponse.json({
      kpi: D.ogretmenPanel.kpi,
      dikkat: D.ogretmenPanel.dikkat,
      sinifHakimiyet: D.ogretmenPanel.sinifHakimiyet,
    }),
  ),
  http.get('*/teacher/students/:id', ({ params }) => {
    const map = D.ogrenciOzetleri;
    const o = map[params.id as string] ?? Object.values(map)[0];
    return o ? HttpResponse.json(o) : hata('ogrenci_yok', 'Öğrenci bulunamadı.', 404);
  }),

  // Sınıf kurulumu — POST create + rotate-code (snake_case body; server-sim kod).
  http.post('*/api/v1/teacher/classes', async ({ request }) => {
    const b = (await request.json().catch(() => ({}))) as { name?: string; grade_level?: string; subject_area?: string };
    return HttpResponse.json({
      id: 'sinif-msw',
      ad: b.name ?? '12-A',
      seviye: b.grade_level ?? '12. Sınıf',
      ders: b.subject_area ?? 'Sayısal',
      katilimKodu: '482913',
      katilimLink: 'https://kiro2.app/katil/482913',
    }, { status: 201 });
  }),
  http.post('*/api/v1/teacher/classes/:id/rotate-code', () =>
    HttpResponse.json({ katilimKodu: '731028', katilimLink: 'https://kiro2.app/katil/731028' }),
  ),

  // --- SPRINT9-B · Grup 7-B Veli Bağlama (KVKK) + Ödev Atama (best-effort) ---
  // KVKK — aydınlatma metni sürümü + açık rıza kaydı (server-sim; consentId sunucudan).
  http.get('*/api/v1/kvkk/notice', () => HttpResponse.json({ version: 'v3' })),
  http.post('*/api/v1/kvkk/consent/give', async ({ request }) => {
    const b = (await request.json().catch(() => ({}))) as { purpose?: string };
    return HttpResponse.json({ ok: true, consentId: 'consent-' + (b.purpose ?? 'veli') }, { status: 201 });
  }),
  // Veli bağlama — ilişki onayı/reddi (PUT; ?approved query). Öğrenci-tarafı GET ucu YOK.
  http.put('*/api/v1/parent/approval/:id', () => HttpResponse.json({ ok: true })),
  // Ödev Atama — konu atomları (zayıflık sıralı) + atama (server-sim id; θ-set sunucuda).
  // Not: /teacher/students SPRINT9-A'da mevcut (getAtamaRoster onu kullanır) — çift kayıt YOK.
  http.get('*/teacher/class/:id/topics', () => HttpResponse.json(D.odevAtama.konular)),
  http.post('*/teacher/assignments', async ({ request }) => {
    const b = (await request.json().catch(() => ({}))) as { student_ids?: string[] };
    return HttpResponse.json({ id: 'atama-msw', atananSayi: (b.student_ids ?? []).length }, { status: 201 });
  }),
];

export default kiroHandlers;
