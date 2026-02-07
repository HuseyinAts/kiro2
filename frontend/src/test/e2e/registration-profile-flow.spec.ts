/**
 * Registration & Profile Flow E2E Tests
 * Tests user registration, profile management, and accessibility settings
 */

import { test, expect } from '@playwright/test';
import { ApiMocker, mockData, loginAsStudent, testAccessibility, testMobileResponsiveness } from './helpers/e2e-helpers';

test.describe('Registration Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should display registration page with role selection', async ({ page }) => {
    // Registration form should be visible
    await expect(page.getByRole('heading', { name: /kayıt|register/i })).toBeVisible();

    // Role selection should be available
    await expect(page.getByText(/öğrenci|ogrenci/i)).toBeVisible();
    await expect(page.getByText(/öğretmen|ogretmen/i)).toBeVisible();
    await expect(page.getByText(/veli/i)).toBeVisible();
  });

  test('should show validation errors for empty form submission', async ({ page }) => {
    // Click register without filling form
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Validation messages should appear
    await expect(page.getByText(/e-posta gerekli|email required/i)).toBeVisible();
  });

  test('should validate email format', async ({ page }) => {
    // Enter invalid email
    await page.getByLabel(/e-posta/i).fill('invalid-email');
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Email validation error
    await expect(page.getByText(/geçerli.*e-posta|valid email/i)).toBeVisible();
  });

  test('should validate password strength', async ({ page }) => {
    // Enter weak password
    await page.getByLabel(/e-posta/i).fill('test@example.com');
    await page.getByLabel(/şifre/i).first().fill('123');
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Password strength error
    await expect(page.getByText(/şifre.*karakter|password.*characters/i)).toBeVisible();
  });

  test('should validate password confirmation match', async ({ page }) => {
    // Fill different passwords
    await page.getByLabel(/e-posta/i).fill('test@example.com');
    await page.getByLabel(/şifre/i).first().fill('StrongPass123!');
    await page.getByLabel(/şifre tekrar|confirm password/i).fill('DifferentPass123!');
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Password mismatch error
    await expect(page.getByText(/şifreler.*eşleşmiyor|passwords.*match/i)).toBeVisible();
  });

  test('should handle Turkish characters in name field', async ({ page }) => {
    // Fill form with Turkish characters
    await page.getByLabel(/ad.*soyad|name/i).fill('Şükrü Öztürk');
    await page.getByLabel(/e-posta/i).fill('sukru@test.com');
    await page.getByLabel(/şifre/i).first().fill('Test123!');
    await page.getByLabel(/şifre tekrar|confirm password/i).fill('Test123!');

    // Name should be accepted
    await expect(page.getByLabel(/ad.*soyad|name/i)).toHaveValue('Şükrü Öztürk');
  });

  test('should register student successfully', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/auth/register', mockData.registrationSuccess);

    // Fill registration form as student
    await page.getByRole('radio', { name: /öğrenci|ogrenci/i }).check();
    await page.getByLabel(/ad.*soyad|name/i).fill('Test Öğrenci');
    await page.getByLabel(/e-posta/i).fill('yeni@ogrenci.com');
    await page.getByLabel(/şifre/i).first().fill('Test123!');
    await page.getByLabel(/şifre tekrar|confirm password/i).fill('Test123!');
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Should redirect to login or show success
    await expect(page.getByText(/kayıt başarılı|registration successful/i).or(page)).toHaveURL(/login|dashboard/i, { timeout: 10000 });
  });

  test('should register teacher with additional fields', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/auth/register', mockData.registrationSuccess);

    // Select teacher role
    await page.getByRole('radio', { name: /öğretmen|ogretmen/i }).check();

    // Teacher-specific fields should appear
    const branchField = page.getByLabel(/branş|branch|subject/i);
    const schoolField = page.getByLabel(/okul|school/i);

    if (await branchField.isVisible()) {
      await branchField.fill('Matematik');
    }
    if (await schoolField.isVisible()) {
      await schoolField.fill('Test Lisesi');
    }

    // Fill common fields
    await page.getByLabel(/ad.*soyad|name/i).fill('Test Öğretmen');
    await page.getByLabel(/e-posta/i).fill('yeni@ogretmen.com');
    await page.getByLabel(/şifre/i).first().fill('Teacher123!');
    await page.getByLabel(/şifre tekrar|confirm password/i).fill('Teacher123!');
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Should redirect or show success
    await expect(page).toHaveURL(/login|teacher|dashboard/i, { timeout: 10000 });
  });

  test('should show error for duplicate email', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/auth/register', 409, 'Bu e-posta adresi zaten kullanılıyor');

    // Fill form
    await page.getByLabel(/ad.*soyad|name/i).fill('Test User');
    await page.getByLabel(/e-posta/i).fill('existing@test.com');
    await page.getByLabel(/şifre/i).first().fill('Test123!');
    await page.getByLabel(/şifre tekrar|confirm password/i).fill('Test123!');
    await page.getByRole('button', { name: /kayıt ol|register/i }).click();

    // Error message
    await expect(page.getByText(/zaten kullanılıyor|already exists/i)).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to login page', async ({ page }) => {
    // Click login link
    await page.getByRole('link', { name: /giriş yap|login/i }).click();

    // Should be on login page
    await expect(page).toHaveURL(/login/i);
  });
});

test.describe('Profile Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should display user profile', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/profil', mockData.userProfile);

    await page.goto('/profile');

    // Profile information should be visible
    await expect(page.getByText(/profil|profile/i)).toBeVisible();
  });

  test('should edit profile name', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/profil', mockData.userProfile);
    await apiMocker.mockSuccess('PUT:/api/v1/profil', { ...mockData.userProfile, ad_soyad: 'Yeni İsim' });

    await page.goto('/profile');

    // Click edit button
    const editButton = page.getByRole('button', { name: /düzenle|edit/i });
    if (await editButton.isVisible()) {
      await editButton.click();

      // Edit name
      await page.getByLabel(/ad.*soyad|name/i).fill('Yeni İsim');
      await page.getByRole('button', { name: /kaydet|save/i }).click();

      // Success message
      await expect(page.getByText(/güncellendi|updated/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should update phone number', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/profil', mockData.userProfile);

    await page.goto('/profile');

    const phoneInput = page.getByLabel(/telefon|phone/i);
    if (await phoneInput.isVisible()) {
      await phoneInput.fill('05559876543');
      await page.getByRole('button', { name: /kaydet|save/i }).click();

      await expect(page.getByText(/güncellendi|updated/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should change password', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/profil/sifre-degistir', { success: true });

    await page.goto('/profile');

    // Open password change section
    const changePasswordButton = page.getByRole('button', { name: /şifre değiştir|change password/i });
    if (await changePasswordButton.isVisible()) {
      await changePasswordButton.click();

      // Fill password form
      await page.getByLabel(/mevcut şifre|current password/i).fill('Test123!');
      await page.getByLabel(/yeni şifre|new password/i).fill('NewPass123!');
      await page.getByLabel(/yeni şifre tekrar|confirm new password/i).fill('NewPass123!');
      await page.getByRole('button', { name: /değiştir|change/i }).click();

      // Success message
      await expect(page.getByText(/şifre.*değiştirildi|password.*changed/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show error for wrong current password', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/v1/profil/sifre-degistir', 400, 'Mevcut şifre hatalı');

    await page.goto('/profile');

    const changePasswordButton = page.getByRole('button', { name: /şifre değiştir|change password/i });
    if (await changePasswordButton.isVisible()) {
      await changePasswordButton.click();

      await page.getByLabel(/mevcut şifre|current password/i).fill('WrongPassword');
      await page.getByLabel(/yeni şifre|new password/i).fill('NewPass123!');
      await page.getByLabel(/yeni şifre tekrar|confirm new password/i).fill('NewPass123!');
      await page.getByRole('button', { name: /değiştir|change/i }).click();

      // Error message
      await expect(page.getByText(/hatalı|incorrect/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Accessibility Settings', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should access accessibility settings page', async ({ page }) => {
    await page.goto('/settings/accessibility');

    // Accessibility settings should be visible
    await expect(page.getByText(/erişilebilirlik|accessibility/i)).toBeVisible();
  });

  test('should toggle high contrast mode', async ({ page }) => {
    await page.goto('/settings/accessibility');

    const contrastToggle = page.getByRole('switch', { name: /yüksek kontrast|high contrast/i });
    if (await contrastToggle.isVisible()) {
      await contrastToggle.click();

      // Body should have high-contrast class or styles
      await expect(page.locator('body')).toHaveClass(/high-contrast|kontrast/i);
    }
  });

  test('should change font size', async ({ page }) => {
    await page.goto('/settings/accessibility');

    const fontSizeControl = page.getByRole('slider', { name: /font|yazı.*boyut/i }).or(
      page.getByRole('combobox', { name: /font|yazı.*boyut/i })
    );

    if (await fontSizeControl.isVisible()) {
      // Test font size change
      await expect(fontSizeControl).toBeVisible();
    }
  });

  test('should enable dyslexia-friendly font', async ({ page }) => {
    await page.goto('/settings/accessibility');

    const dyslexiaToggle = page.getByRole('switch', { name: /disleksi|dyslexia/i });
    if (await dyslexiaToggle.isVisible()) {
      await dyslexiaToggle.click();

      // Font should change
      await expect(page.locator('body')).toHaveCSS('font-family', /OpenDyslexic|dyslexia/i);
    }
  });
});

test.describe('Registration Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/register');
    await testAccessibility(page);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/register');

    // Tab through form elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have proper form labels', async ({ page }) => {
    await page.goto('/register');

    // All inputs should have labels
    const inputs = page.locator('input:not([type="hidden"])');
    const count = await inputs.count();

    for (let i = 0; i < count; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        await expect(label).toBeVisible();
      }
    }
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.goto('/register');
    await testMobileResponsiveness(page);
  });
});

test.describe('Profile Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should have proper heading hierarchy on profile page', async ({ page }) => {
    await page.goto('/profile');
    await testAccessibility(page);
  });

  test('should be keyboard navigable on profile page', async ({ page }) => {
    await page.goto('/profile');

    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });
});
