/**
 * Authentication Flow E2E Tests
 * Tests login, logout, and session management
 */

import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page for unauthenticated users', async ({ page }) => {
    await page.goto('/login');

    // Check login form elements
    await expect(page.getByRole('heading', { name: /giriş/i })).toBeVisible();
    await expect(page.getByLabel(/e-posta/i)).toBeVisible();
    await expect(page.getByLabel(/şifre/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /giriş yap/i })).toBeVisible();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    await page.goto('/login');

    // Click submit without filling form
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Check for validation messages
    await expect(page.getByText(/e-posta gerekli/i)).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill with invalid credentials
    await page.getByLabel(/e-posta/i).fill('invalid@test.com');
    await page.getByLabel(/şifre/i).fill('wrongpassword');
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Check for error message
    await expect(page.getByText(/geçersiz|hatalı/i)).toBeVisible({ timeout: 10000 });
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    await page.goto('/login');

    // Fill with valid credentials (using test user)
    await page.getByLabel(/e-posta/i).fill('test@kiro2.com');
    await page.getByLabel(/şifre/i).fill('Test123!');
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });
  });

  test('should persist session across page reloads', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/e-posta/i).fill('test@kiro2.com');
    await page.getByLabel(/şifre/i).fill('Test123!');
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
    await page.getByLabel(/e-posta/i).fill('test@kiro2.com');
    await page.getByLabel(/şifre/i).fill('Test123!');
    await page.getByRole('button', { name: /giriş yap/i }).click();

    // Wait for dashboard
    await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });

    // Click logout button
    await page.getByRole('button', { name: /çıkış|logout/i }).click();

    // Should redirect to login page
    await expect(page).toHaveURL(/login|giriş/i, { timeout: 10000 });
  });

  test('should toggle password visibility', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.getByLabel(/şifre/i);
    await passwordInput.fill('testpassword');

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click visibility toggle
    await page.getByRole('button', { name: /şifreyi göster|toggle/i }).click();

    // Password should be visible
    await expect(passwordInput).toHaveAttribute('type', 'text');
  });
});

test.describe('Protected Routes', () => {
  test('should redirect to login when accessing protected route', async ({ page }) => {
    // Try to access dashboard without login
    await page.goto('/dashboard');

    // Should redirect to login
    await expect(page).toHaveURL(/login|giriş/i, { timeout: 10000 });
  });

  test('should redirect to login when accessing exam route', async ({ page }) => {
    await page.goto('/sinav/baslat');

    // Should redirect to login
    await expect(page).toHaveURL(/login|giriş/i, { timeout: 10000 });
  });
});
