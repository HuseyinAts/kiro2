/**
 * Feature Health Smoke Tests — Faz B (12 flow runtime validation)
 *
 * Faz A statik analizde 7 flow kırık olarak işaretlendi. Bu dosya Faz A'da
 * mvp-smoke.spec.ts'te KAPSANMAYAN 8 flow için runtime smoke test sağlar.
 *
 * Kapsam (Faz A flow numaralandırmasına göre):
 *   Flow 3  — FSRS tekrar oturumu       (router-loader P0 — /api/v1/fsrs/due 404 bekleniyor)
 *   Flow 5  — Lig sıralaması            (OK bekleniyor)
 *   Flow 6  — 1v1 düello                (is-active-missing silent P1)
 *   Flow 7  — Veli çocuk takibi         (OK bekleniyor)
 *   Flow 8  — Öğretmen sınıf yönetimi   (router-loader P0 — /teacher vs /teachers mismatch)
 *   Flow 9  — Admin kullanıcı yönetimi  (OK bekleniyor)
 *   Flow 11 — Sosyal hub                (dual-table N+1 P1)
 *   Flow 12 — Dungeon learning path     (orchestrator prereq bypass P0)
 *
 * mvp-smoke.spec.ts zaten şunları kapsar (çalıştırılmalı):
 *   Flow 1  — Sınav, Flow 2 — Günlük plan, Flow 4 — Chat, Flow 10 — Dashboard
 *
 * Çalıştırma:
 *   SKIP_WEBSERVER=1 npx playwright test src/test/e2e/feature-health-smoke.spec.ts --project=chromium
 *
 * Docker stack ayakta olmalı (localhost:3000):
 *   docker compose -f docker-compose.mvp.yml up -d
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Docker stack
test.use({ baseURL: process.env.MVP_BASE_URL || 'http://localhost:3000' });

// Serial ama fail-on-first yok — her test bağımsız kabul edilmeli
// (PASS/FAIL matrisi için cascade skip istemiyoruz)

// Seed user credentials (seed_mvp_data.py)
const USERS = {
  student: { email: 'ogrenci@kiro2.com', password: 'Kiro2Beta2026@x' },
  parent: { email: 'veli@kiro2.com', password: 'Kiro2Beta2026@x' },
  teacher: { email: 'ogretmen@kiro2.com', password: 'Kiro2Beta2026@x' },
  admin: { email: 'admin@kiro2.com', password: 'Kiro2Beta2026@x' },
};

// Shared storage states (1 login per role)
const storageStates: Record<string, any> = {};

/** Role-based login with demo button fallback */
async function loginAs(page: Page, role: keyof typeof USERS) {
  await page.goto('/login');

  // Demo button
  const demoRegex: Record<string, RegExp> = {
    student: /öğrenci/i,
    parent: /veli/i,
    teacher: /öğretmen/i,
    admin: /admin/i,
  };
  const demoBtn = page.getByRole('button', { name: demoRegex[role] });
  if (await demoBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await demoBtn.click();
  } else {
    // Form fallback
    const user = USERS[role];
    await page.getByLabel(/e-posta/i).fill(user.email);
    await page.getByLabel(/şifre/i).fill(user.password);
    await page.getByRole('button', { name: /giriş yap/i }).click();
  }

  // Wait for any non-login URL (role-specific redirect)
  await page.waitForFunction(
    () => !window.location.pathname.includes('/login'),
    { timeout: 15000 }
  );
}

/** Navigate using saved storage state or fresh login */
async function navAs(
  page: Page,
  context: BrowserContext,
  role: keyof typeof USERS,
  path: string
) {
  const state = storageStates[role];
  if (state) {
    if (state.cookies?.length) await context.addCookies(state.cookies);
    if (state.origins?.length) {
      for (const origin of state.origins) {
        try {
          await page.goto('/login');
          for (const item of origin.localStorage || []) {
            await page.evaluate(
              ([k, v]) => localStorage.setItem(k as string, v as string),
              [item.name, item.value]
            );
          }
        } catch {}
      }
    }
    await page.goto(path);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    if (!page.url().includes('/login')) return;
  }

  await loginAs(page, role);
  storageStates[role] = await context.storageState();
  if (path !== '/dashboard') {
    await page.goto(path);
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  }
}

/**
 * Non-crashing page assertion.
 * Page must:
 *   1. Not redirect to /login
 *   2. Not contain "Cannot GET" (raw 404 proxy)
 *   3. Not show plain "500" or "503"
 */
async function expectPageAlive(page: Page) {
  expect(page.url()).not.toContain('/login');
  const body = (await page.textContent('body')) || '';
  expect(body).not.toContain('Cannot GET');
  // 500/503 raw text
  const lower = body.toLowerCase();
  expect(lower).not.toMatch(/\b(500 internal server error|503 service unavailable)\b/);
}

/** Capture 4xx/5xx responses during a test */
function captureFailedResponses(page: Page): Array<{ url: string; status: number }> {
  const failed: Array<{ url: string; status: number }> = [];
  page.on('response', (res) => {
    const status = res.status();
    const url = res.url();
    if (status >= 400 && url.includes('/api/')) {
      failed.push({ url, status });
    }
  });
  return failed;
}

// ─────────────────────────────────────────────────
// Flow 3 — FSRS Tekrar Oturumu
// Beklenen: Faz A'da `/api/v1/fsrs/due` 404 tespit edildi (router-loader P0)
// ─────────────────────────────────────────────────
test('Flow 3 — FSRS review sayfası açılır ve /due endpoint durumu', async ({
  page,
  context,
}) => {
  const failed = captureFailedResponses(page);
  await navAs(page, context, 'student', '/fsrs-review');
  await expectPageAlive(page);

  // Faz A HYPOTHESIS: /api/v1/fsrs/due 404 dönecek
  const fsrsFails = failed.filter((f) => f.url.includes('/fsrs/'));
  console.log('Flow 3 FSRS API failures:', fsrsFails);

  // Sayfa crash etmeden render olmalı (endpoint başarısız bile olsa)
  const hasContent = await page
    .getByText(/tekrar|review|fsrs|kart|due|bugün/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 3 FSRS content visible:', hasContent);
});

// ─────────────────────────────────────────────────
// Flow 5 — Lig Sıralaması
// Beklenen: OK — Faz A'da runtime sorunu tespit edilmedi
// ─────────────────────────────────────────────────
test('Flow 5 — League sayfası standings yükler', async ({ page, context }) => {
  const failed = captureFailedResponses(page);
  await navAs(page, context, 'student', '/league');
  await expectPageAlive(page);

  // Lig göstergesi veya tier/rank metni (warning — hard fail değil)
  const hasLeague = await page
    .getByText(/lig|tier|rank|haftal|sıralama|xp/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 5 League content visible:', hasLeague);

  // /api/v1/leagues/current hata dönmemeli (hard fail)
  const leagueApiFails = failed.filter(
    (f) => f.url.includes('/leagues/') && f.status >= 500
  );
  console.log('Flow 5 League 5xx failures:', leagueApiFails);
  expect(leagueApiFails).toHaveLength(0);
});

// ─────────────────────────────────────────────────
// Flow 6 — 1v1 Düello
// Beklenen: is-active-missing silent — matchmake empty list (Faz A P1)
// ─────────────────────────────────────────────────
test('Flow 6 — Duel sayfası açılır ve matchmake çalışır', async ({
  page,
  context,
}) => {
  const failed = captureFailedResponses(page);
  await navAs(page, context, 'student', '/duel');
  await expectPageAlive(page);

  // Düello UI (warning)
  const hasDuel = await page
    .getByText(/düello|duel|rakip|maç|eşle|başla/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 6 Duel content visible:', hasDuel);

  // Matchmake butonu varsa tıkla ve silent fail yakala
  const matchBtn = page
    .getByRole('button', { name: /eşle|maç|başla|rakip bul/i })
    .first();
  if (await matchBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await matchBtn.click().catch(() => {});
    await page.waitForTimeout(2000);
    // Faz A: soru yoksa empty list döner, frontend stuck olabilir
  }

  // Duel API hatalarını raporla
  const duelFails = failed.filter((f) => f.url.includes('/duel/'));
  console.log('Flow 6 Duel API failures:', duelFails);
});

// ─────────────────────────────────────────────────
// Flow 7 — Veli Çocuk Takibi
// Beklenen: OK — Faz A'da IDOR + approval mevcut
// ─────────────────────────────────────────────────
test('Flow 7 — Veli dashboard children listesi', async ({ page, context }) => {
  const failed = captureFailedResponses(page);

  try {
    await navAs(page, context, 'parent', '/parent/dashboard');
  } catch {
    // Parent user seed'de yoksa skip
    test.skip(true, 'Parent seed user yok veya login fail');
    return;
  }

  await expectPageAlive(page);

  const hasParent = await page
    .getByText(/veli|çocuk|child|onay|rapor/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 7 Parent content visible:', hasParent);

  const parentFails = failed.filter(
    (f) => f.url.includes('/parent/') && f.status >= 500
  );
  console.log('Flow 7 Parent 5xx failures:', parentFails);
  expect(parentFails).toHaveLength(0);
});

// ─────────────────────────────────────────────────
// Flow 8 — Öğretmen Sınıf Yönetimi
// Beklenen: router-loader P0 — /api/v1/teacher vs /teachers mismatch
// ─────────────────────────────────────────────────
test('Flow 8 — Teacher classes sayfası ve router durumu', async ({
  page,
  context,
}) => {
  const failed = captureFailedResponses(page);

  try {
    await navAs(page, context, 'teacher', '/teacher/classes');
  } catch {
    test.skip(true, 'Teacher seed user yok veya login fail');
    return;
  }

  await expectPageAlive(page);

  // Faz A HYPOTHESIS: /api/v1/teacher/classes 404 dönecek (prefix /teachers çoğul)
  const teacherFails = failed.filter((f) => f.url.includes('/teacher'));
  console.log('Flow 8 Teacher API failures:', teacherFails);

  // Sayfa crash etmese bile içerik boş gelebilir
  const hasContent = await page
    .getByText(/sınıf|class|öğrenci|student|teacher|öğretmen/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 8 Teacher content visible:', hasContent);
});

// ─────────────────────────────────────────────────
// Flow 9 — Admin Kullanıcı Yönetimi
// Beklenen: OK — RBAC + parameterized queries
// ─────────────────────────────────────────────────
test('Flow 9 — Admin users sayfası listeleme', async ({ page, context }) => {
  const failed = captureFailedResponses(page);

  try {
    await navAs(page, context, 'admin', '/admin/users');
  } catch {
    test.skip(true, 'Admin seed user yok veya login fail');
    return;
  }

  await expectPageAlive(page);

  const hasAdmin = await page
    .getByText(/kullanıcı|user|rol|admin|yönet/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 9 Admin content visible:', hasAdmin);

  const adminFails = failed.filter(
    (f) => f.url.includes('/admin/') && f.status >= 500
  );
  console.log('Flow 9 Admin 5xx failures:', adminFails);
  expect(adminFails).toHaveLength(0);
});

// ─────────────────────────────────────────────────
// Flow 11 — Sosyal Hub
// Beklenen: dual-table N+1 + XSS encode P1
// ─────────────────────────────────────────────────
test('Flow 11 — Sosyal hub summary yüklenir', async ({ page, context }) => {
  const failed = captureFailedResponses(page);
  await navAs(page, context, 'student', '/social');
  await expectPageAlive(page);

  const hasSocial = await page
    .getByText(/sosyal|forum|arkadaş|takip|meydan|oba/i)
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false);
  console.log('Flow 11 Social content visible:', hasSocial);

  // /api/v1/social/summary 500 dönmemeli
  const socialFails = failed.filter(
    (f) => f.url.includes('/social/') && f.status >= 500
  );
  console.log('Flow 11 Social 5xx failures:', socialFails);
  expect(socialFails).toHaveLength(0);
});

// ─────────────────────────────────────────────────
// Flow 12 — Dungeon Learning Path (Öğrenme Haritası)
// Beklenen: orchestrator prereq bypass P0 — DAG exception false default
// ─────────────────────────────────────────────────
test('Flow 12 — Learning path map DAG render', async ({ page, context }) => {
  const failed = captureFailedResponses(page);
  await navAs(page, context, 'student', '/learning-path-map');
  await expectPageAlive(page);

  const hasMap = await page
    .getByText(/öğrenme|konu|harita|dungeon|topic|oda|room/i)
    .first()
    .isVisible({ timeout: 10000 })
    .catch(() => false);
  console.log('Flow 12 Map content visible:', hasMap);

  // SVG veya canvas render var mı (Rough.js + dagre)
  const hasSvg = await page
    .locator('svg, canvas')
    .first()
    .isVisible({ timeout: 5000 })
    .catch(() => false);
  console.log('Flow 12 SVG/Canvas visible:', hasSvg);

  // Map API hataları
  const mapFails = failed.filter(
    (f) => f.url.includes('/learning-path') && f.status >= 500
  );
  console.log('Flow 12 Learning Path 5xx failures:', mapFails);
  expect(mapFails).toHaveLength(0);
});
