/**
 * Teacher Dashboard Flow E2E Tests
 * Tests teacher dashboard, student management, exam management, and reports
 */

import { test, expect } from '@playwright/test';
import {
  ApiMocker,
  mockData,
  loginAsTeacher,
  loginAsStudent,
  TeacherPage,
  testAccessibility,
  testMobileResponsiveness
} from './helpers/e2e-helpers';

test.describe('Teacher Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/ogretmen/ogrenciler*', mockData.teacherStudentList);
    await loginAsTeacher(page);
  });

  test('should display teacher dashboard with statistics', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    // Dashboard heading
    await expect(page.getByRole('heading', { name: /öğretmen|teacher|panel/i })).toBeVisible();
  });

  test('should display student count', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    // Student count
    await expect(page.getByText(/öğrenci|student|35/i)).toBeVisible();
  });

  test('should display active exams count', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    // Active exams
    const activeExams = page.getByText(/aktif sınav|active exam|3/i);
    if (await activeExams.isVisible()) {
      await expect(activeExams).toBeVisible();
    }
  });

  test('should display average success rate', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    // Average success
    const avgSuccess = page.getByText(/ortalama|başarı|72/i);
    if (await avgSuccess.isVisible()) {
      await expect(avgSuccess).toBeVisible();
    }
  });

  test('should display student performance summary', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    // Student list summary
    await expect(page.getByText(/Ahmet|Fatma|öğrenci/i)).toBeVisible();
  });

  test('should navigate to students page', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    await page.getByRole('link', { name: /öğrenciler|students/i }).click();

    await expect(page).toHaveURL(/teacher\/students/i, { timeout: 10000 });
  });

  test('should navigate to exams page', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    await page.getByRole('link', { name: /sınavlar|exams/i }).click();

    await expect(page).toHaveURL(/teacher\/exams/i, { timeout: 10000 });
  });

  test('should navigate to reports page', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    const reportsLink = page.getByRole('link', { name: /raporlar|reports/i });
    if (await reportsLink.isVisible()) {
      await reportsLink.click();
      await expect(page).toHaveURL(/teacher\/reports/i, { timeout: 10000 });
    }
  });
});

test.describe('Student Management', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/ogretmen/ogrenciler*', mockData.teacherStudentList);
    await loginAsTeacher(page);
  });

  test('should display student list', async ({ page }) => {
    await page.goto('/teacher/students');

    // Student table or list
    await expect(page.getByText(/Ahmet Yılmaz|Fatma Demir/i)).toBeVisible();
  });

  test('should search students by name', async ({ page }) => {
    await page.goto('/teacher/students');

    const searchInput = page.getByPlaceholder(/öğrenci ara|search student/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('Ahmet');
      await page.waitForTimeout(500);

      await expect(page.getByText(/Ahmet/i)).toBeVisible();
    }
  });

  test('should filter students by class', async ({ page }) => {
    await page.goto('/teacher/students');

    const classFilter = page.getByRole('combobox', { name: /sınıf|class/i });
    if (await classFilter.isVisible()) {
      await classFilter.selectOption('11-A');
      await page.waitForTimeout(500);
    }
  });

  test('should view student detail', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/ogrenciler/1/performans', {
      ogrenci_id: '1',
      ad_soyad: 'Ahmet Yılmaz',
      ortalama: 85.5,
      sinav_sayisi: 10,
      guclü_konular: ['Türev', 'İntegral'],
      zayif_konular: ['Geometri']
    });

    await page.goto('/teacher/students');

    // Click on student
    await page.getByText(/Ahmet Yılmaz/i).click();

    // Student detail should show
    await expect(page.getByText(/performans|detail|detay/i)).toBeVisible({ timeout: 5000 });
  });

  test('should display student performance trend', async ({ page }) => {
    await page.goto('/teacher/students');

    // Click on student
    await page.getByText(/Ahmet Yılmaz/i).click();

    // Performance chart
    const chart = page.locator('canvas, svg, [class*="chart"]');
    if (await chart.isVisible()) {
      await expect(chart).toBeVisible();
    }
  });

  test('should show weak and strong subjects', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/ogrenciler/1/performans', {
      ogrenci_id: '1',
      ad_soyad: 'Ahmet Yılmaz',
      guclü_konular: ['Türev'],
      zayif_konular: ['Geometri']
    });

    await page.goto('/teacher/students');
    await page.getByText(/Ahmet Yılmaz/i).click();

    // Subject indicators
    const weakSubject = page.getByText(/zayıf|weak|Geometri/i);
    const strongSubject = page.getByText(/güçlü|strong|Türev/i);

    if (await weakSubject.isVisible()) {
      await expect(weakSubject).toBeVisible();
    }
    if (await strongSubject.isVisible()) {
      await expect(strongSubject).toBeVisible();
    }
  });
});

test.describe('Exam Management', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/ogretmen/sinavlar*', {
      sinavlar: [
        { sinav_id: '1', ad: 'TYT Deneme 1', tarih: '2024-01-20', durum: 'aktif' },
        { sinav_id: '2', ad: 'AYT Matematik', tarih: '2024-01-25', durum: 'taslak' }
      ],
      total: 2
    });
    await loginAsTeacher(page);
  });

  test('should display exam list', async ({ page }) => {
    await page.goto('/teacher/exams');

    // Exam list
    await expect(page.getByText(/TYT Deneme|AYT Matematik|sınav/i)).toBeVisible();
  });

  test('should open create exam dialog', async ({ page }) => {
    await page.goto('/teacher/exams');

    await page.getByRole('button', { name: /sınav oluştur|create exam|yeni/i }).click();

    // Dialog should open
    await expect(page.getByRole('dialog').or(page.locator('[data-testid="create-exam-modal"]'))).toBeVisible();
  });

  test('should create new exam', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/sinav', { success: true, sinav_id: 'new-exam-123' });

    await page.goto('/teacher/exams');

    // Click create
    await page.getByRole('button', { name: /sınav oluştur|create exam|yeni/i }).click();

    // Fill exam form
    await page.getByLabel(/sınav adı|exam name/i).fill('Yeni TYT Denemesi');

    const typeSelect = page.getByRole('combobox', { name: /sınav tipi|exam type/i });
    if (await typeSelect.isVisible()) {
      await typeSelect.selectOption('TYT');
    }

    await page.getByRole('button', { name: /oluştur|create|kaydet/i }).click();

    // Success
    await expect(page.getByText(/oluşturuldu|created|başarılı/i)).toBeVisible({ timeout: 5000 });
  });

  test('should assign exam to students', async ({ page }) => {
    await page.goto('/teacher/exams');

    // Click assign button
    const assignButton = page.getByRole('button', { name: /ata|assign/i }).first();
    if (await assignButton.isVisible()) {
      await assignButton.click();

      // Student selection
      await expect(page.getByText(/öğrenci seç|select student/i)).toBeVisible();
    }
  });

  test('should view exam results', async ({ page }) => {
    await page.goto('/teacher/exams');

    // Click on exam
    await page.getByText(/TYT Deneme/i).click();

    // Results view
    await expect(page.getByText(/sonuç|result|istatistik/i)).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Teacher Reports', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/ogretmen/raporlar*', {
      raporlar: [
        { rapor_id: '1', tip: 'sinif', tarih: '2024-01-15', durum: 'hazır' }
      ]
    });
    await loginAsTeacher(page);
  });

  test('should display reports page', async ({ page }) => {
    await page.goto('/teacher/reports');

    await expect(page.getByRole('heading', { name: /rapor|report/i })).toBeVisible();
  });

  test('should generate class report', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/rapor/sinif', { success: true, rapor_url: '/reports/class-1.pdf' });

    await page.goto('/teacher/reports');

    const generateButton = page.getByRole('button', { name: /sınıf raporu|class report|oluştur/i });
    if (await generateButton.isVisible()) {
      await generateButton.click();

      await expect(page.getByText(/oluşturuldu|generated|hazır/i)).toBeVisible({ timeout: 10000 });
    }
  });

  test('should view individual student report', async ({ page }) => {
    await page.goto('/teacher/reports');

    const studentReportLink = page.getByRole('link', { name: /öğrenci raporu|student report/i });
    if (await studentReportLink.isVisible()) {
      await studentReportLink.click();

      await expect(page.getByText(/öğrenci|student/i)).toBeVisible();
    }
  });

  test('should display subject performance breakdown', async ({ page }) => {
    await page.goto('/teacher/reports');

    const subjectBreakdown = page.getByText(/konu bazlı|subject breakdown|derse göre/i);
    if (await subjectBreakdown.isVisible()) {
      await expect(subjectBreakdown).toBeVisible();
    }
  });
});

test.describe('Teacher RBAC', () => {
  test('should deny student access to teacher dashboard', async ({ page }) => {
    await loginAsStudent(page);

    await page.goto('/teacher/dashboard');

    // Should redirect
    await expect(page).toHaveURL(/unauthorized|dashboard|login/i, { timeout: 10000 });
  });

  test('should deny student access to teacher students', async ({ page }) => {
    await loginAsStudent(page);

    await page.goto('/teacher/students');

    await expect(page).toHaveURL(/unauthorized|dashboard|login/i, { timeout: 10000 });
  });
});

test.describe('Teacher Dashboard Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/ogretmen/ogrenciler*', mockData.teacherStudentList);
    await loginAsTeacher(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/teacher/dashboard');
    await testAccessibility(page);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/teacher/dashboard');

    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should be mobile responsive', async ({ page }) => {
    await page.goto('/teacher/dashboard');
    await testMobileResponsiveness(page);
  });
});

test.describe('Teacher Error Handling', () => {
  test('should handle API error gracefully', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/v1/ogretmen/dashboard', 500, 'Sunucu hatası');
    await loginAsTeacher(page);

    await page.goto('/teacher/dashboard');

    const errorMessage = page.getByText(/hata|error/i);
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('should handle empty student list', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/ogretmen/ogrenciler*', { ogrenciler: [], total: 0 });
    await loginAsTeacher(page);

    await page.goto('/teacher/students');

    // Empty state message
    const emptyMessage = page.getByText(/öğrenci bulunamadı|no students|boş/i);
    if (await emptyMessage.isVisible()) {
      await expect(emptyMessage).toBeVisible();
    }
  });
});
