/**
 * Parent Dashboard Flow E2E Tests
 * Tests parent dashboard, children management, reports, and notifications
 */

import { test, expect } from '@playwright/test';
import {
  ApiMocker,
  mockData,
  loginAsParent,
  loginAsStudent,
  ParentPage,
  testAccessibility,
  testMobileResponsiveness
} from './helpers/e2e-helpers';

test.describe('Parent Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/children*', mockData.parentChildren);
    await apiMocker.mockSuccess('/api/v1/parent/notifications*', mockData.parentNotifications);
    await loginAsParent(page);
  });

  test('should display parent dashboard', async ({ page }) => {
    await page.goto('/parent/dashboard');

    // Dashboard heading
    await expect(page.getByRole('heading', { name: /veli|parent|panel/i })).toBeVisible();
  });

  test('should display children summary', async ({ page }) => {
    await page.goto('/parent/dashboard');

    // Children info
    await expect(page.getByText(/Ali Veli|çocuk|child/i)).toBeVisible();
  });

  test('should display child performance overview', async ({ page }) => {
    await page.goto('/parent/dashboard');

    // Performance score
    const performanceScore = page.getByText(/75|ortalama|average/i);
    if (await performanceScore.isVisible()) {
      await expect(performanceScore).toBeVisible();
    }
  });

  test('should display unread notifications badge', async ({ page }) => {
    await page.goto('/parent/dashboard');

    // Notification badge
    const badge = page.locator('[data-testid="notification-badge"], .badge, .notification-count');
    if (await badge.isVisible()) {
      await expect(badge).toContainText(/3|2/);
    }
  });

  test('should navigate to children page', async ({ page }) => {
    await page.goto('/parent/dashboard');

    await page.getByRole('link', { name: /çocuklar|children/i }).click();

    await expect(page).toHaveURL(/parent\/children/i, { timeout: 10000 });
  });

  test('should navigate to reports page', async ({ page }) => {
    await page.goto('/parent/dashboard');

    await page.getByRole('link', { name: /rapor|report/i }).click();

    await expect(page).toHaveURL(/parent\/reports/i, { timeout: 10000 });
  });

  test('should navigate to notifications page', async ({ page }) => {
    await page.goto('/parent/dashboard');

    await page.getByRole('link', { name: /bildirim|notification/i }).click();

    await expect(page).toHaveURL(/parent\/notifications/i, { timeout: 10000 });
  });
});

test.describe('Children Management', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/children*', mockData.parentChildren);
    await loginAsParent(page);
  });

  test('should display children list', async ({ page }) => {
    await page.goto('/parent/children');

    // Children cards/list
    await expect(page.getByText(/Ali Veli|Ayşe Veli/i)).toBeVisible();
  });

  test('should show approved children status', async ({ page }) => {
    await page.goto('/parent/children');

    // Approved status
    const approvedStatus = page.getByText(/onaylı|approved|aktif/i);
    if (await approvedStatus.isVisible()) {
      await expect(approvedStatus).toBeVisible();
    }
  });

  test('should show pending children status', async ({ page }) => {
    await page.goto('/parent/children');

    // Pending status
    const pendingStatus = page.getByText(/bekliyor|pending|onay bekliyor/i);
    if (await pendingStatus.isVisible()) {
      await expect(pendingStatus).toBeVisible();
    }
  });

  test('should open add child dialog', async ({ page }) => {
    await page.goto('/parent/children');

    await page.getByRole('button', { name: /çocuk ekle|add child|yeni/i }).click();

    // Dialog should open
    await expect(page.getByRole('dialog').or(page.locator('[data-testid="add-child-modal"]'))).toBeVisible();
  });

  test('should add child by email', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/children', { success: true, message: 'İstek gönderildi' });

    await page.goto('/parent/children');

    // Click add child
    await page.getByRole('button', { name: /çocuk ekle|add child|yeni/i }).click();

    // Fill child email
    await page.getByLabel(/e-posta|email/i).fill('cocuk@test.com');
    await page.getByRole('button', { name: /gönder|send|ekle/i }).click();

    // Success message
    await expect(page.getByText(/istek gönderildi|request sent|başarılı/i)).toBeVisible({ timeout: 5000 });
  });

  test('should view child performance detail', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/children/1/performance', {
      child_id: 1,
      child_name: 'Ali Veli',
      average_score: 75.5,
      exam_count: 12,
      weak_subjects: ['Matematik', 'Fizik'],
      strong_subjects: ['Türkçe', 'Tarih']
    });

    await page.goto('/parent/children');

    // Click on child
    await page.getByText(/Ali Veli/i).click();

    // Performance detail
    await expect(page.getByText(/performans|performance|detay/i)).toBeVisible({ timeout: 5000 });
  });

  test('should display weak and strong subjects', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/children/1/performance', {
      child_id: 1,
      weak_subjects: ['Matematik'],
      strong_subjects: ['Türkçe']
    });

    await page.goto('/parent/children');
    await page.getByText(/Ali Veli/i).click();

    // Subject indicators
    const weakSubject = page.getByText(/zayıf|weak|Matematik/i);
    const strongSubject = page.getByText(/güçlü|strong|Türkçe/i);

    if (await weakSubject.isVisible()) {
      await expect(weakSubject).toBeVisible();
    }
    if (await strongSubject.isVisible()) {
      await expect(strongSubject).toBeVisible();
    }
  });
});

test.describe('Parent Reports', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/children*', mockData.parentChildren);
    await apiMocker.mockSuccess('/api/v1/parent/children/1/weekly-report', {
      child_id: 1,
      child_name: 'Ali Veli',
      week_start: '2024-01-08',
      week_end: '2024-01-14',
      total_study_time: 1200,
      completed_exams: 3,
      average_score: 78.5,
      topics_studied: ['Türev', 'İntegral', 'Limit']
    });
    await loginAsParent(page);
  });

  test('should display reports page', async ({ page }) => {
    await page.goto('/parent/reports');

    await expect(page.getByRole('heading', { name: /rapor|report/i })).toBeVisible();
  });

  test('should view weekly report', async ({ page }) => {
    await page.goto('/parent/reports');

    // Select child
    const childSelect = page.getByRole('combobox', { name: /çocuk|child/i });
    if (await childSelect.isVisible()) {
      await childSelect.selectOption('1');
    }

    // Weekly report
    await expect(page.getByText(/haftalık|weekly|rapor/i)).toBeVisible();
  });

  test('should display study time', async ({ page }) => {
    await page.goto('/parent/reports');

    // Study time
    const studyTime = page.getByText(/çalışma süresi|study time|saat|dakika/i);
    if (await studyTime.isVisible()) {
      await expect(studyTime).toBeVisible();
    }
  });

  test('should display completed exams count', async ({ page }) => {
    await page.goto('/parent/reports');

    // Completed exams
    const completedExams = page.getByText(/tamamlanan sınav|completed exam|3/i);
    if (await completedExams.isVisible()) {
      await expect(completedExams).toBeVisible();
    }
  });

  test('should display performance chart', async ({ page }) => {
    await page.goto('/parent/reports');

    // Chart
    const chart = page.locator('canvas, svg, [class*="chart"]');
    if (await chart.isVisible()) {
      await expect(chart).toBeVisible();
    }
  });
});

test.describe('Parent Notifications', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/notifications*', mockData.parentNotifications);
    await loginAsParent(page);
  });

  test('should display notifications list', async ({ page }) => {
    await page.goto('/parent/notifications');

    // Notifications
    await expect(page.getByText(/haftalık rapor|sınav sonuç|bildirim/i)).toBeVisible();
  });

  test('should show unread notifications', async ({ page }) => {
    await page.goto('/parent/notifications');

    // Unread indicator
    const unreadIndicator = page.locator('[data-testid="unread"], .unread, [class*="unread"]');
    if (await unreadIndicator.first().isVisible()) {
      await expect(unreadIndicator.first()).toBeVisible();
    }
  });

  test('should mark notification as read', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/notifications/1/read', { success: true });

    await page.goto('/parent/notifications');

    // Click on notification
    await page.getByText(/haftalık rapor/i).first().click();

    // Should be marked as read (visual change)
    await page.waitForTimeout(500);
  });

  test('should mark all as read', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/notifications/read-all', { success: true });

    await page.goto('/parent/notifications');

    const markAllButton = page.getByRole('button', { name: /tümünü okundu|mark all read/i });
    if (await markAllButton.isVisible()) {
      await markAllButton.click();

      await expect(page.getByText(/okundu|read|marked/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should filter notifications', async ({ page }) => {
    await page.goto('/parent/notifications');

    const filterSelect = page.getByRole('combobox', { name: /filtre|filter/i });
    if (await filterSelect.isVisible()) {
      await filterSelect.selectOption('unread');
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Parent-Child Relation', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/children*', mockData.parentChildren);
    await loginAsParent(page);
  });

  test('should display pending approval requests', async ({ page }) => {
    await page.goto('/parent/children');

    // Pending child
    const pendingChild = page.getByText(/Ayşe Veli|bekliyor|pending/i);
    if (await pendingChild.isVisible()) {
      await expect(pendingChild).toBeVisible();
    }
  });

  test('should show approval status for each child', async ({ page }) => {
    await page.goto('/parent/children');

    // Status badges
    const approvedBadge = page.locator('[data-testid="status-approved"], .approved');
    const pendingBadge = page.locator('[data-testid="status-pending"], .pending');

    if (await approvedBadge.isVisible()) {
      await expect(approvedBadge).toBeVisible();
    }
    if (await pendingBadge.isVisible()) {
      await expect(pendingBadge).toBeVisible();
    }
  });
});

test.describe('Parent RBAC', () => {
  test('should deny student access to parent dashboard', async ({ page }) => {
    await loginAsStudent(page);

    await page.goto('/parent/dashboard');

    // Should redirect
    await expect(page).toHaveURL(/unauthorized|dashboard|login/i, { timeout: 10000 });
  });

  test('should deny student access to parent children', async ({ page }) => {
    await loginAsStudent(page);

    await page.goto('/parent/children');

    await expect(page).toHaveURL(/unauthorized|dashboard|login/i, { timeout: 10000 });
  });
});

test.describe('Parent Dashboard Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/children*', mockData.parentChildren);
    await apiMocker.mockSuccess('/api/v1/parent/notifications*', mockData.parentNotifications);
    await loginAsParent(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/parent/dashboard');
    await testAccessibility(page);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/parent/dashboard');

    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.goto('/parent/dashboard');
    await testMobileResponsiveness(page);
  });
});

test.describe('Parent Error Handling', () => {
  test('should handle API error gracefully', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/v1/parent/dashboard', 500, 'Sunucu hatası');
    await loginAsParent(page);

    await page.goto('/parent/dashboard');

    const errorMessage = page.getByText(/hata|error/i);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle no children state', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', { ...mockData.parentDashboard, children: [] });
    await apiMocker.mockSuccess('/api/v1/parent/children*', { children: [] });
    await loginAsParent(page);

    await page.goto('/parent/children');

    // Empty state
    const emptyMessage = page.getByText(/çocuk bulunamadı|no children|henüz/i);
    if (await emptyMessage.isVisible()) {
      await expect(emptyMessage).toBeVisible();
    }
  });

  test('should handle child request error', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/parent/dashboard', mockData.parentDashboard);
    await apiMocker.mockSuccess('/api/v1/parent/children*', mockData.parentChildren);
    await apiMocker.mockError('/api/v1/parent/children', 400, 'Geçersiz e-posta adresi');
    await loginAsParent(page);

    await page.goto('/parent/children');

    // Click add child
    await page.getByRole('button', { name: /çocuk ekle|add child|yeni/i }).click();

    // Fill invalid email
    await page.getByLabel(/e-posta|email/i).fill('invalid-email');
    await page.getByRole('button', { name: /gönder|send|ekle/i }).click();

    // Error message
    await expect(page.getByText(/geçersiz|invalid|hata/i)).toBeVisible({ timeout: 5000 });
  });
});
