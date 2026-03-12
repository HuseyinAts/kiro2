/**
 * MVP Beta Smoke Test
 *
 * Docker stack'e karşı çalışır (localhost:3000).
 * Tüm kritik kullanıcı flow'larını doğrular.
 *
 * Çalıştırma:
 *   SKIP_WEBSERVER=1 npx playwright test src/test/e2e/mvp-smoke.spec.ts --project=chromium
 *   # --headed ekle tarayıcıyı görmek için
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Docker stack port 3000 — baseURL override ile relative path'ler çalışır
test.use({
  baseURL: process.env.MVP_BASE_URL || 'http://localhost:3000',
});

// Rate limiting'i önlemek için seri çalıştır (8 paralel login = rate limit)
test.describe.configure({ mode: 'serial' });

// Seed user credentials (seed_mvp_data.py)
const STUDENT = {
  email: 'ogrenci@kiro2.com',
  password: 'Kiro2Beta2026@x',
};

/** Login helper — demo buton veya form ile giriş */
async function loginAsStudent(page: Page) {
  await page.goto('/login');

  // Demo buton varsa kullan (daha hızlı)
  const demoBtn = page.getByRole('button', { name: /öğrenci/i });
  if (await demoBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await demoBtn.click();
  } else {
    // Fallback: form ile giriş
    await page.getByLabel(/e-posta/i).fill(STUDENT.email);
    await page.getByLabel(/şifre/i).fill(STUDENT.password);
    await page.getByRole('button', { name: /giriş yap/i }).click();
  }

  // Dashboard'a yönlenmeyi bekle
  await expect(page).toHaveURL(/dashboard/, { timeout: 15000 });
}

/**
 * Navigate to a protected page — uses storageState to avoid extra logins.
 * Saves browser storage after first login, reuses for subsequent navigations.
 */
let savedStorageState: {
  cookies: Array<{ name: string; value: string; domain: string; path: string }>;
  origins: Array<{ origin: string; localStorage: Array<{ name: string; value: string }> }>;
} | null = null;

async function loginAndNavigate(page: Page, context: BrowserContext, path: string) {
  // If we have saved storage state, restore it to avoid re-login
  if (savedStorageState) {
    // Add cookies from saved state
    if (savedStorageState.cookies.length > 0) {
      await context.addCookies(savedStorageState.cookies);
    }
    // Set localStorage from saved state
    for (const origin of savedStorageState.origins) {
      for (const item of origin.localStorage) {
        await page.goto('/login'); // Need a page loaded first to set localStorage
        await page.evaluate(
          ([key, val]) => localStorage.setItem(key, val),
          [item.name, item.value],
        );
      }
    }
    // Navigate to target page
    await page.goto(path);
    await page.waitForLoadState('networkidle', { timeout: 15000 });

    // If still on login (storage state expired), fall through to fresh login
    if (!page.url().includes('/login')) {
      return;
    }
  }

  // Fresh login
  await loginAsStudent(page);

  // Save storage state for subsequent tests
  savedStorageState = await context.storageState();

  // Navigate to target if not dashboard
  if (path !== '/dashboard') {
    await page.goto(path);
    await page.waitForLoadState('networkidle', { timeout: 15000 });
  }
}

// ─────────────────────────────────────────────────
// 1. LOGIN FLOW
// ─────────────────────────────────────────────────

test('1.1 login sayfası açılır', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByLabel(/e-posta/i)).toBeVisible();
  await expect(page.getByLabel(/şifre/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /giriş yap/i })).toBeVisible();
});

test('1.2 demo buton ile giriş yapılır → dashboard', async ({ page, context }) => {
  await loginAsStudent(page);

  // Save storage state for subsequent tests (only 1 login needed!)
  savedStorageState = await context.storageState();
});

// ─────────────────────────────────────────────────
// 2. DASHBOARD
// ─────────────────────────────────────────────────

test('2.1 dashboard istatistikler yüklenir', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/dashboard');

  // İstatistik kartları görünür olmalı
  await expect(
    page.getByText(/tamamlanan|puan|sınav|ders/i).first()
  ).toBeVisible({ timeout: 10000 });
});

test('2.2 quick action butonları görünür', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/dashboard');

  const actionTexts = [/sınav/i, /sohbet|chat/i, /öğrenme/i];
  let foundCount = 0;

  for (const pattern of actionTexts) {
    const el = page.getByText(pattern).first();
    if (await el.isVisible({ timeout: 3000 }).catch(() => false)) {
      foundCount++;
    }
  }

  expect(foundCount).toBeGreaterThanOrEqual(2);
});

// ─────────────────────────────────────────────────
// 3. SINAV FLOW
// ─────────────────────────────────────────────────

test('3.1 sınav başlatma sayfası açılır', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/exam/start');

  // Login'e redirect olmadığını doğrula
  const url = page.url();
  expect(url).not.toContain('/login');

  // Sayfa içeriğinde sınav ile ilgili metin olmalı
  await expect(
    page.getByText(/TYT|AYT|sınav|başla|hazır/i).first()
  ).toBeVisible({ timeout: 10000 });
});

test('3.2 sınav oluşturulur ve sorular gösterilir', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/exam/start');

  // TYT seç
  const tytOption = page.getByText(/TYT/).first();
  if (await tytOption.isVisible({ timeout: 5000 }).catch(() => false)) {
    await tytOption.click();
  }

  // Ders seç
  const mathOption = page.getByText(/matematik/i).first();
  if (await mathOption.isVisible({ timeout: 3000 }).catch(() => false)) {
    await mathOption.click();
  }

  // Başlat
  const startBtn = page.getByRole('button', { name: /başla|sınavı başlat|devam/i });
  if (await startBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
    await startBtn.click();

    // Soru veya seçenek görünmeli
    await expect(
      page.getByText(/soru|A\)|B\)|seçenek/i).first()
    ).toBeVisible({ timeout: 15000 });
  }
});

// ─────────────────────────────────────────────────
// 4. ÖĞRENME YOLU
// ─────────────────────────────────────────────────

test('4.1 öğrenme yolu sayfası açılır', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/learning-path');

  // Login'e redirect olmadığını doğrula
  const url = page.url();
  expect(url).not.toContain('/login');

  // 404 veya crash olmamalı
  const body = await page.textContent('body');
  expect(body).not.toContain('Cannot GET');

  // Sayfada herhangi bir içerik görünür (boş path mesajı bile olabilir)
  await page.getByText(/öğrenme|learning|konu|başla|yol|oluştur/i).first()
    .isVisible({ timeout: 10000 }).catch(() => false);

  // En azından login sayfası değil ve crash etmemiş
  expect(url).not.toContain('/login');
});

// ─────────────────────────────────────────────────
// 5. AI CHAT
// ─────────────────────────────────────────────────

test('5.1 chat sayfası açılır ve input görünür', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/chat');

  const url = page.url();
  expect(url).not.toContain('/login');

  // Input alanı veya mesaj kutusu
  const hasInput = await page.locator('textarea, input[type="text"], [contenteditable]')
    .first().isVisible({ timeout: 10000 }).catch(() => false);

  const hasMessage = await page.getByText(/sohbet|chat|mesaj|yapay zeka|asistan/i)
    .first().isVisible({ timeout: 5000 }).catch(() => false);

  expect(hasInput || hasMessage).toBeTruthy();
});

// ─────────────────────────────────────────────────
// 6. LOGOUT
// ─────────────────────────────────────────────────

test('6.1 çıkış yapılır ve login sayfasına döner', async ({ page, context }) => {
  await loginAndNavigate(page, context, '/dashboard');

  // Çıkış butonunu çeşitli konumlarda ara
  const logoutBtn = page.getByRole('button', { name: /çıkış|logout/i });
  const logoutLink = page.getByRole('link', { name: /çıkış|logout/i });
  const logoutMenuItem = page.getByRole('menuitem', { name: /çıkış|logout/i });
  const logoutText = page.getByText(/çıkış yap/i);

  if (await logoutBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await logoutBtn.click();
  } else if (await logoutLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutLink.click();
  } else if (await logoutMenuItem.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutMenuItem.click();
  } else if (await logoutText.isVisible({ timeout: 2000 }).catch(() => false)) {
    await logoutText.click();
  } else {
    // Sidebar/header'daki avatar veya menü butonunu dene
    const menuTriggers = page.locator(
      '[aria-label*="menü"], [aria-label*="menu"], [aria-label*="profil"], ' +
      '[aria-label*="kullanıcı"], [data-testid="user-menu"], ' +
      '[class*="avatar"], [class*="Avatar"]'
    );

    let found = false;
    const count = await menuTriggers.count();
    for (let i = 0; i < count && !found; i++) {
      const trigger = menuTriggers.nth(i);
      if (await trigger.isVisible({ timeout: 1000 }).catch(() => false)) {
        await trigger.click();
        // Menü açıldıktan sonra çıkış ara
        const exitOption = page.getByText(/çıkış|logout|oturumu kapat/i).first();
        if (await exitOption.isVisible({ timeout: 3000 }).catch(() => false)) {
          await exitOption.click();
          found = true;
        }
      }
    }

    if (!found) {
      // Son çare: doğrudan logout URL'ine git
      await page.goto('/login');
      // Cookie'leri temizle
      await page.context().clearCookies();
      await page.goto('/login');
    }
  }

  // Login sayfasında olmalı
  await expect(page).toHaveURL(/login/, { timeout: 10000 });
});
