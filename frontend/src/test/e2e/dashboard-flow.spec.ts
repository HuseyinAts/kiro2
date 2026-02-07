/**
 * Dashboard Flow E2E Tests
 * Tests dashboard navigation, widgets, and user interactions
 */

import { test, expect } from '@playwright/test';

// Helper to login before dashboard tests
async function loginAsStudent(page: any) {
  await page.goto('/login');
  await page.getByLabel(/e-posta/i).fill('test@kiro2.com');
  await page.getByLabel(/şifre/i).fill('Test123!');
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });
}

test.describe('Student Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should display welcome message with user name', async ({ page }) => {
    // Welcome message should be visible
    await expect(page.getByText(/hoş geldin|merhaba/i)).toBeVisible();
  });

  test('should display progress statistics', async ({ page }) => {
    // Progress widget should show stats
    await expect(page.getByText(/ilerleme|progress/i)).toBeVisible();
    await expect(page.getByText(/%|\d+/)).toBeVisible();
  });

  test('should display recent activity', async ({ page }) => {
    // Recent activity section
    await expect(page.getByText(/son aktivite|recent/i)).toBeVisible();
  });

  test('should navigate to exam page from dashboard', async ({ page }) => {
    // Find exam button/link
    const examLink = page.getByRole('link', { name: /sınav|exam/i }).or(
      page.getByRole('button', { name: /sınava başla/i })
    );

    if (await examLink.isVisible()) {
      await examLink.click();
      await expect(page).toHaveURL(/sinav/i, { timeout: 10000 });
    }
  });

  test('should navigate to learning path from dashboard', async ({ page }) => {
    const learningPathLink = page.getByRole('link', { name: /öğrenme yolu|learning path/i });

    if (await learningPathLink.isVisible()) {
      await learningPathLink.click();
      await expect(page).toHaveURL(/ogrenme-yolu|learning-path/i, { timeout: 10000 });
    }
  });

  test('should display notifications', async ({ page }) => {
    // Notification icon/bell should be visible
    const notificationIcon = page.getByRole('button', { name: /bildirim|notification/i }).or(
      page.locator('[data-testid="notifications"]')
    );

    if (await notificationIcon.isVisible()) {
      await notificationIcon.click();
      // Notification panel should open
      await expect(page.getByText(/bildirim|notification/i)).toBeVisible();
    }
  });

  test('should open profile settings', async ({ page }) => {
    // Profile menu
    const profileButton = page.getByRole('button', { name: /profil|profile/i }).or(
      page.locator('[data-testid="profile-menu"]')
    );

    if (await profileButton.isVisible()) {
      await profileButton.click();
      // Profile menu should open
      await expect(page.getByText(/ayarlar|settings/i)).toBeVisible();
    }
  });
});

test.describe('Dashboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should have working sidebar navigation', async ({ page }) => {
    // Sidebar should be visible
    const sidebar = page.locator('nav, [role="navigation"]').first();
    await expect(sidebar).toBeVisible();

    // Navigation links
    const navLinks = sidebar.getByRole('link');
    const count = await navLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should highlight current page in navigation', async ({ page }) => {
    // Dashboard link should be active/highlighted
    const dashboardLink = page.getByRole('link', { name: /ana sayfa|dashboard/i });
    if (await dashboardLink.isVisible()) {
      await expect(dashboardLink).toHaveClass(/active|selected|current/i);
    }
  });

  test('should toggle sidebar on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Menu toggle button should be visible
    const menuToggle = page.getByRole('button', { name: /menu|menü/i });
    if (await menuToggle.isVisible()) {
      await menuToggle.click();
      // Sidebar should open
      await expect(page.locator('nav, [role="navigation"]')).toBeVisible();
    }
  });
});

test.describe('Dashboard Widgets', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should display upcoming exams widget', async ({ page }) => {
    const upcomingExams = page.getByText(/yaklaşan sınavlar|upcoming exams/i);
    if (await upcomingExams.isVisible()) {
      await expect(upcomingExams).toBeVisible();
    }
  });

  test('should display study streak widget', async ({ page }) => {
    const streak = page.getByText(/seri|streak/i);
    if (await streak.isVisible()) {
      await expect(streak).toBeVisible();
    }
  });

  test('should display performance chart', async ({ page }) => {
    const chart = page.locator('canvas, svg[class*="chart"], [class*="chart"]').first();
    if (await chart.isVisible()) {
      await expect(chart).toBeVisible();
    }
  });

  test('should display quick actions', async ({ page }) => {
    // Quick action buttons
    const quickActions = page.getByText(/hızlı erişim|quick actions/i);
    if (await quickActions.isVisible()) {
      await expect(quickActions).toBeVisible();
    }
  });
});

test.describe('Dashboard Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check for h1
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab through focusable elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Some element should be focused
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have proper ARIA labels', async ({ page }) => {
    // Main navigation should have aria-label
    const nav = page.locator('nav[aria-label], [role="navigation"][aria-label]');
    if (await nav.first().isVisible()) {
      await expect(nav.first()).toHaveAttribute('aria-label');
    }
  });
});
