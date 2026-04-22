/**
 * J3 — kısa FE duman: öğrenci girişi + /learning-path kabuğu (API golden ile eşleşen yüzey).
 * Çalıştırmak: FE dev açık (varsayılan :3001), E2E_TEST_PASSWORD ayarlı.
 * Örnek:  E2E_TEST_PASSWORD=... npx playwright test j3-learning-path-smoke
 */
import { test, expect } from '@playwright/test';

const EMAIL = process.env.E2E_TEST_EMAIL ?? 'test@kiro2.com';
const PASSWORD = process.env.E2E_TEST_PASSWORD;

test.describe('J3 FE smoke (learning path shell)', () => {
  test('student opens /learning-path after login without crash', async ({
    page,
  }, testInfo) => {
    if (!PASSWORD) {
      testInfo.skip(true, 'Set E2E_TEST_PASSWORD (e.g. seed MVP password from backend/scripts/seed_mvp_data.py).');
    }

    await page.goto('/login');
    await page.getByRole('textbox', { name: /e-posta/i }).fill(EMAIL);
    await page.getByRole('textbox', { name: /şifre/i }).fill(PASSWORD!);
    await page.getByRole('button', { name: /giriş yap/i }).click();
    await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 20_000 });

    await page.goto('/learning-path');
    await expect(page.locator('body')).toBeVisible();
    const html = (await page.content()).slice(0, 50_000);
    expect(html).not.toMatch(/Application error|ChunkLoadError|Something went wrong/i);
  });
});
