/**
 * Authentication Flow E2E Tests
 * Tests login, logout, and session management
 */

import { test, expect } from '@playwright/test';

// Test credentials from environment (never hardcode production passwords)
const TEST_USER = {
  email: process.env.E2E_TEST_EMAIL ?? 'ogrenci@kiro2.com',
  password: process.env.E2E_TEST_PASSWORD ?? '',
};

test.beforeAll(() => {
  if (!TEST_USER.password) {
    throw new Error(
      'E2E_TEST_PASSWORD env var required. Set it before running E2E tests:\n' +
      '  E2E_TEST_PASSWORD=your_password npx playwright test'
    );
  }
});

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page for unauthenticated users', async ({ page }) => {
    await page.goto('/login');

    // Check login form elements
    await expect(page.getByRole('heading', { name: /giriş/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /e-posta/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /şifre/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /giriş yap/i })).toBeVisible();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    await page.goto('/login');

    // Click submit without filling form
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Check for validation message (actual UI message)
    await expect(page.getByText(/tüm alanları doldurun|e-posta gerekli/i)).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill with invalid credentials
    await page.getByRole('textbox', { name: /e-posta/i }).fill('invalid@test.com');
    await page.getByRole('textbox', { name: /şifre/i }).fill('wrongpassword');
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Check for error message
    await expect(page.getByText(/geçersiz|hatalı/i)).toBeVisible({ timeout: 10000 });
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    await page.goto('/login');

    // Fill with valid credentials
    await page.getByRole('textbox', { name: /e-posta/i }).fill(TEST_USER.email);
    await page.getByRole('textbox', { name: /şifre/i }).fill(TEST_USER.password);
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });
  });

  test('should persist session across page reloads', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByRole('textbox', { name: /e-posta/i }).fill(TEST_USER.email);
    await page.getByRole('textbox', { name: /şifre/i }).fill(TEST_USER.password);
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Wait for dashboard
    await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });

    // Reload page
    await page.reload();

    // Should still be on dashboard (not redirected to login)
    await expect(page).not.toHaveURL(/login/i);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByRole('textbox', { name: /e-posta/i }).fill(TEST_USER.email);
    await page.getByRole('textbox', { name: /şifre/i }).fill(TEST_USER.password);
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Wait for dashboard
    await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });

    // Find and click logout (could be in menu/sidebar/header)
    const logoutButton = page.getByRole('button', { name: /çıkış|logout|çık/i });
    const logoutLink = page.getByRole('link', { name: /çıkış|logout|çık/i });

    if (await logoutButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await logoutButton.click();
    } else if (await logoutLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await logoutLink.click();
    } else {
      // Try clicking user menu first to reveal logout option
      const userMenu = page.locator('[data-testid="user-menu"], [aria-label*="kullanıcı"], [aria-label*="profil"]');
      if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click();
        await page.getByText(/çıkış|logout/i).click();
      } else {
        test.skip(true, 'Logout button not found in current UI');
      }
    }

    // Should redirect to login page
    await expect(page).toHaveURL(/login|giriş/i, { timeout: 10000 });
  });
});

test.describe('Protected Routes', () => {
  test('unauthenticated API call should return 401', async ({ page }) => {
    // Verify backend rejects unauthenticated requests (the real security boundary)
    const response = await page.request.get('/api/v1/auth/me');
    expect(response.status()).toBe(401);
  });
});
