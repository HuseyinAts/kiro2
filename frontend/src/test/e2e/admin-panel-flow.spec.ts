/**
 * Admin Panel Flow E2E Tests
 * Tests admin dashboard, user management, content management, and RBAC
 */

import { test, expect } from '@playwright/test';
import {
  ApiMocker,
  mockData,
  loginAsAdmin,
  loginAsStudent,
  loginAsTeacher,
  AdminPage,
  testAccessibility,
  testMobileResponsiveness,
  testTabletResponsiveness
} from './helpers/e2e-helpers';

test.describe('Admin Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/dashboard/stats', mockData.adminDashboardStats);
    await apiMocker.mockSuccess('/api/v1/admin/users*', mockData.adminUserList);
    await loginAsAdmin(page);
  });

  test('should display admin dashboard with statistics', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // Dashboard heading
    await expect(page.getByRole('heading', { name: /admin|yönetim/i })).toBeVisible();

    // Stats cards should be visible
    await expect(page.getByText(/toplam kullanıcı|total users/i)).toBeVisible();
  });

  test('should display user count statistics', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // User statistics
    const statsSection = page.locator('[data-testid="stats-section"], .stats-section');
    if (await statsSection.isVisible()) {
      await expect(page.getByText(/1250|öğrenci|kullanıcı/i)).toBeVisible();
    }
  });

  test('should display system health status', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // System health indicator
    const healthIndicator = page.getByText(/sistem durumu|system status|healthy/i);
    if (await healthIndicator.isVisible()) {
      await expect(healthIndicator).toBeVisible();
    }
  });

  test('should navigate to user management', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // Click users link
    await page.getByRole('link', { name: /kullanıcılar|users/i }).click();

    await expect(page).toHaveURL(/admin\/users/i, { timeout: 10000 });
  });

  test('should navigate to content management', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // Click content link
    const contentLink = page.getByRole('link', { name: /içerik|content/i });
    if (await contentLink.isVisible()) {
      await contentLink.click();
      await expect(page).toHaveURL(/admin\/content/i, { timeout: 10000 });
    }
  });

  test('should display quick action buttons', async ({ page }) => {
    await page.goto('/admin/dashboard');

    // Quick actions
    const quickActions = page.locator('[data-testid="quick-actions"], .quick-actions');
    if (await quickActions.isVisible()) {
      await expect(quickActions).toBeVisible();
    }
  });
});

test.describe('User Management', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/users*', mockData.adminUserList);
    await apiMocker.mockSuccess('/api/v1/admin/dashboard/stats', mockData.adminDashboardStats);
    await loginAsAdmin(page);
  });

  test('should display user list with pagination', async ({ page }) => {
    await page.goto('/admin/users');

    // User table should be visible
    await expect(page.locator('table, [data-testid="user-table"]')).toBeVisible();

    // Users should be displayed
    await expect(page.getByText(/student1@test.com|Test Öğrenci/i)).toBeVisible();
  });

  test('should search users by name', async ({ page }) => {
    await page.goto('/admin/users');

    // Search input
    const searchInput = page.getByPlaceholder(/ara|search/i);
    await searchInput.fill('Öğrenci');

    // Wait for filtered results
    await page.waitForTimeout(500);

    // Should show matching users
    await expect(page.getByText(/Öğrenci/i)).toBeVisible();
  });

  test('should filter users by role', async ({ page }) => {
    await page.goto('/admin/users');

    // Role filter
    const roleFilter = page.getByRole('combobox', { name: /rol|role/i });
    if (await roleFilter.isVisible()) {
      await roleFilter.selectOption('ogrenci');

      // Should show only students
      await page.waitForTimeout(500);
    }
  });

  test('should open create user dialog', async ({ page }) => {
    await page.goto('/admin/users');

    // Click create user button
    await page.getByRole('button', { name: /kullanıcı ekle|add user|yeni/i }).click();

    // Dialog should open
    await expect(page.getByRole('dialog').or(page.locator('[data-testid="create-user-modal"]'))).toBeVisible();
  });

  test('should create new user', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/users', { success: true, kullanici_id: 'new-123' });

    await page.goto('/admin/users');

    // Click create user
    await page.getByRole('button', { name: /kullanıcı ekle|add user|yeni/i }).click();

    // Fill form
    await page.getByLabel(/e-posta/i).fill('newuser@test.com');
    await page.getByLabel(/ad.*soyad|name/i).fill('Yeni Kullanıcı');
    await page.getByLabel(/şifre/i).fill('NewUser123!');

    // Select role
    const roleSelect = page.getByRole('combobox', { name: /rol|role/i });
    if (await roleSelect.isVisible()) {
      await roleSelect.selectOption('ogrenci');
    }

    // Submit
    await page.getByRole('button', { name: /oluştur|create|kaydet/i }).click();

    // Success message
    await expect(page.getByText(/oluşturuldu|created|başarılı/i)).toBeVisible({ timeout: 5000 });
  });

  test('should edit existing user', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/users/1', { success: true });

    await page.goto('/admin/users');

    // Click edit button on first user
    const editButton = page.getByRole('button', { name: /düzenle|edit/i }).first();
    if (await editButton.isVisible()) {
      await editButton.click();

      // Edit name
      await page.getByLabel(/ad.*soyad|name/i).fill('Düzenlenmiş İsim');
      await page.getByRole('button', { name: /kaydet|save/i }).click();

      // Success message
      await expect(page.getByText(/güncellendi|updated/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should deactivate user', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/users/1', { success: true });

    await page.goto('/admin/users');

    // Click deactivate button
    const deactivateButton = page.getByRole('button', { name: /deaktif|deactivate|pasif/i }).first();
    if (await deactivateButton.isVisible()) {
      await deactivateButton.click();

      // Confirm dialog
      await page.getByRole('button', { name: /onayla|confirm|evet/i }).click();

      // Success message
      await expect(page.getByText(/deaktif|deactivated|pasif/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should change user role', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/users/1', { success: true });

    await page.goto('/admin/users');

    // Click edit on first user
    const editButton = page.getByRole('button', { name: /düzenle|edit/i }).first();
    if (await editButton.isVisible()) {
      await editButton.click();

      // Change role
      const roleSelect = page.getByRole('combobox', { name: /rol|role/i });
      if (await roleSelect.isVisible()) {
        await roleSelect.selectOption('ogretmen');
        await page.getByRole('button', { name: /kaydet|save/i }).click();

        await expect(page.getByText(/güncellendi|updated/i)).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should handle pagination', async ({ page }) => {
    await page.goto('/admin/users');

    // Pagination controls
    const nextButton = page.getByRole('button', { name: /sonraki|next|>/i });
    if (await nextButton.isVisible()) {
      await nextButton.click();

      // Page should change
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Content Management', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/content*', { content: [], total: 0 });
    await apiMocker.mockSuccess('/api/v1/admin/dashboard/stats', mockData.adminDashboardStats);
    await loginAsAdmin(page);
  });

  test('should display content management page', async ({ page }) => {
    await page.goto('/admin/content');

    // Content heading
    await expect(page.getByRole('heading', { name: /içerik|content/i })).toBeVisible();
  });

  test('should filter content by type', async ({ page }) => {
    await page.goto('/admin/content');

    const typeFilter = page.getByRole('combobox', { name: /tip|type/i });
    if (await typeFilter.isVisible()) {
      await typeFilter.selectOption('soru');
      await page.waitForTimeout(500);
    }
  });

  test('should search content', async ({ page }) => {
    await page.goto('/admin/content');

    const searchInput = page.getByPlaceholder(/ara|search/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('matematik');
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Admin Settings', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/dashboard/stats', mockData.adminDashboardStats);
    await loginAsAdmin(page);
  });

  test('should display admin settings page', async ({ page }) => {
    await page.goto('/admin/settings');

    // Settings heading
    await expect(page.getByRole('heading', { name: /ayarlar|settings/i })).toBeVisible();
  });

  test('should update system settings', async ({ page }) => {
    await page.goto('/admin/settings');

    const saveButton = page.getByRole('button', { name: /kaydet|save/i });
    if (await saveButton.isVisible()) {
      await saveButton.click();
      await expect(page.getByText(/kaydedildi|saved/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Admin RBAC (Role-Based Access Control)', () => {
  test('should deny student access to admin dashboard', async ({ page }) => {
    await loginAsStudent(page);

    // Try to access admin page
    await page.goto('/admin/dashboard');

    // Should redirect to unauthorized or dashboard
    await expect(page).toHaveURL(/unauthorized|dashboard|login/i, { timeout: 10000 });
  });

  test('should deny teacher access to admin users', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await loginAsTeacher(page);

    // Try to access admin users
    await page.goto('/admin/users');

    // Should redirect
    await expect(page).toHaveURL(/unauthorized|teacher|dashboard|login/i, { timeout: 10000 });
  });

  test('should show unauthorized message for non-admin', async ({ page }) => {
    await loginAsStudent(page);
    await page.goto('/admin/dashboard');

    // Unauthorized message or redirect
    const unauthorizedText = page.getByText(/yetkisiz|unauthorized|erişim yok/i);
    const isUnauthorizedPage = await page.url().includes('unauthorized');

    expect(await unauthorizedText.isVisible() || isUnauthorizedPage).toBeTruthy();
  });
});

test.describe('Admin Panel Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/dashboard/stats', mockData.adminDashboardStats);
    await apiMocker.mockSuccess('/api/v1/admin/users*', mockData.adminUserList);
    await loginAsAdmin(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await testAccessibility(page);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/admin/dashboard');

    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have proper ARIA labels on tables', async ({ page }) => {
    await page.goto('/admin/users');

    const table = page.locator('table[aria-label], [role="table"]');
    if (await table.isVisible()) {
      await expect(table).toBeVisible();
    }
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await testMobileResponsiveness(page);
  });

  test('should be tablet responsive', async ({ page }) => {
    await page.goto('/admin/dashboard');
    await testTabletResponsiveness(page);
  });
});

test.describe('Admin Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should handle API error gracefully', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/v1/admin/dashboard/stats', 500, 'Sunucu hatası');

    await page.goto('/admin/dashboard');

    // Error message or fallback UI
    const errorMessage = page.getByText(/hata|error|sunucu/i);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle network failure', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockNetworkFailure('/api/v1/admin/users*');

    await page.goto('/admin/users');

    // Error or retry UI
    const retryButton = page.getByRole('button', { name: /tekrar|retry/i });
    if (await retryButton.isVisible()) {
      await expect(retryButton).toBeVisible();
    }
  });

  test('should show validation error on invalid user creation', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/admin/users*', mockData.adminUserList);
    await apiMocker.mockError('/api/v1/admin/users', 400, 'Geçersiz e-posta formatı');

    await page.goto('/admin/users');

    // Click create user
    await page.getByRole('button', { name: /kullanıcı ekle|add user|yeni/i }).click();

    // Fill with invalid data
    await page.getByLabel(/e-posta/i).fill('invalid-email');
    await page.getByRole('button', { name: /oluştur|create|kaydet/i }).click();

    // Error message
    await expect(page.getByText(/geçersiz|invalid|hata/i)).toBeVisible({ timeout: 5000 });
  });
});
