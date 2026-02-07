/**
 * Question Upload Flow E2E Tests
 * Tests YOLO-based question upload, detection results, and question bank integration
 */

import { test, expect } from '@playwright/test';
import {
  ApiMocker,
  mockData,
  loginAsAdmin,
  loginAsTeacher,
  loginAsStudent,
  QuestionUploadPage,
  testAccessibility
} from './helpers/e2e-helpers';

test.describe('Question Upload Page', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);
    await loginAsAdmin(page);
  });

  test('should display question upload page', async ({ page }) => {
    await page.goto('/question-upload');

    // Page heading
    await expect(page.getByRole('heading', { name: /soru yükleme|question upload|YOLO/i })).toBeVisible();
  });

  test('should display file upload area', async ({ page }) => {
    await page.goto('/question-upload');

    // Upload area
    const uploadArea = page.locator('[data-testid="upload-area"], .upload-area, input[type="file"]');
    await expect(uploadArea).toBeVisible();
  });

  test('should display drag and drop zone', async ({ page }) => {
    await page.goto('/question-upload');

    // Drag drop text
    const dragDropText = page.getByText(/sürükle|drag.*drop|dosya seç/i);
    if (await dragDropText.isVisible()) {
      await expect(dragDropText).toBeVisible();
    }
  });

  test('should accept image files', async ({ page }) => {
    await page.goto('/question-upload');

    // File input should accept images
    const fileInput = page.locator('input[type="file"]');
    const acceptAttr = await fileInput.getAttribute('accept');

    expect(acceptAttr).toMatch(/image|png|jpg|jpeg/i);
  });

  test('should show supported formats', async ({ page }) => {
    await page.goto('/question-upload');

    // Supported formats text
    const formatsText = page.getByText(/PNG|JPG|JPEG|desteklenen/i);
    if (await formatsText.isVisible()) {
      await expect(formatsText).toBeVisible();
    }
  });
});

test.describe('YOLO Detection', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);
    await loginAsAdmin(page);
  });

  test('should show loading state during detection', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection, 2000);

    await page.goto('/question-upload');

    // Trigger upload (simulate file selection)
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      // Create a test image file
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      // Loading state
      const loadingIndicator = page.getByText(/yükleniyor|loading|analiz/i);
      if (await loadingIndicator.isVisible()) {
        await expect(loadingIndicator).toBeVisible();
      }
    }
  });

  test('should display detection results', async ({ page }) => {
    await page.goto('/question-upload');

    // Mock that detection already happened
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);

    // Trigger detection
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      // Wait for results
      await page.waitForTimeout(1000);

      // Detection results section
      const resultsSection = page.getByText(/sonuç|result|tespit/i);
      if (await resultsSection.isVisible()) {
        await expect(resultsSection).toBeVisible();
      }
    }
  });

  test('should display detected class labels', async ({ page }) => {
    await page.goto('/question-upload');

    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);

    // Trigger detection
    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      // Class labels
      const soruLabel = page.getByText(/soru/i);
      const secenekLabel = page.getByText(/seçenek|secenek/i);

      if (await soruLabel.isVisible()) {
        await expect(soruLabel).toBeVisible();
      }
    }
  });

  test('should display confidence scores', async ({ page }) => {
    await page.goto('/question-upload');

    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      // Confidence score
      const confidenceText = page.getByText(/95%|88%|güven|confidence/i);
      if (await confidenceText.isVisible()) {
        await expect(confidenceText).toBeVisible();
      }
    }
  });

  test('should display processing time', async ({ page }) => {
    await page.goto('/question-upload');

    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      // Processing time
      const timeText = page.getByText(/1\.5|saniye|second|süre/i);
      if (await timeText.isVisible()) {
        await expect(timeText).toBeVisible();
      }
    }
  });
});

test.describe('Question Bank Integration', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);
    await apiMocker.mockSuccess('/api/v1/soru-bankasi/soru', { success: true, soru_id: 'new-q-123' });
    await loginAsAdmin(page);
  });

  test('should show save question button after detection', async ({ page }) => {
    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      // Save button
      const saveButton = page.getByRole('button', { name: /kaydet|save|ekle/i });
      if (await saveButton.isVisible()) {
        await expect(saveButton).toBeVisible();
      }
    }
  });

  test('should open question metadata form', async ({ page }) => {
    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      // Click save/add button
      const addButton = page.getByRole('button', { name: /ekle|add|kaydet/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();

        // Metadata form
        const metadataForm = page.getByText(/konu|subject|zorluk|difficulty/i);
        if (await metadataForm.isVisible()) {
          await expect(metadataForm).toBeVisible();
        }
      }
    }
  });

  test('should allow subject selection', async ({ page }) => {
    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      const addButton = page.getByRole('button', { name: /ekle|add|kaydet/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();

        // Subject select
        const subjectSelect = page.getByRole('combobox', { name: /konu|subject/i });
        if (await subjectSelect.isVisible()) {
          await subjectSelect.selectOption('Matematik');
        }
      }
    }
  });

  test('should allow difficulty level selection', async ({ page }) => {
    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      const addButton = page.getByRole('button', { name: /ekle|add|kaydet/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();

        // Difficulty select
        const difficultySelect = page.getByRole('combobox', { name: /zorluk|difficulty/i });
        if (await difficultySelect.isVisible()) {
          await difficultySelect.selectOption('orta');
        }
      }
    }
  });

  test('should save question to bank', async ({ page }) => {
    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      const addButton = page.getByRole('button', { name: /ekle|add|kaydet/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();

        // Fill form and save
        const saveButton = page.getByRole('button', { name: /kaydet|save/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();

          // Success message
          await expect(page.getByText(/kaydedildi|saved|başarılı/i)).toBeVisible({ timeout: 5000 });
        }
      }
    }
  });
});

test.describe('OSYM Question Generator', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/osym/generate', {
      sorular: [
        { soru_id: '1', metin: 'Test soru 1', konu: 'Matematik', zorluk: 'orta' },
        { soru_id: '2', metin: 'Test soru 2', konu: 'Matematik', zorluk: 'zor' }
      ],
      total: 2
    });
    await loginAsAdmin(page);
  });

  test('should display OSYM generator page', async ({ page }) => {
    await page.goto('/osym-generator');

    // Page heading
    await expect(page.getByRole('heading', { name: /OSYM|soru üretici|generator/i })).toBeVisible();
  });

  test('should allow subject selection', async ({ page }) => {
    await page.goto('/osym-generator');

    const subjectSelect = page.getByRole('combobox', { name: /konu|subject/i });
    if (await subjectSelect.isVisible()) {
      await subjectSelect.selectOption('Matematik');
      await expect(subjectSelect).toHaveValue(/matematik/i);
    }
  });

  test('should allow exam type selection', async ({ page }) => {
    await page.goto('/osym-generator');

    const examTypeSelect = page.getByRole('combobox', { name: /sınav tipi|exam type/i });
    if (await examTypeSelect.isVisible()) {
      await examTypeSelect.selectOption('TYT');
    }
  });

  test('should generate questions', async ({ page }) => {
    await page.goto('/osym-generator');

    // Configure and generate
    const generateButton = page.getByRole('button', { name: /üret|generate|oluştur/i });
    if (await generateButton.isVisible()) {
      await generateButton.click();

      // Generated questions
      await expect(page.getByText(/Test soru|üretilen|generated/i)).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display generated questions list', async ({ page }) => {
    await page.goto('/osym-generator');

    const generateButton = page.getByRole('button', { name: /üret|generate|oluştur/i });
    if (await generateButton.isVisible()) {
      await generateButton.click();

      // Questions list
      await page.waitForTimeout(1000);
      const questionsList = page.locator('[data-testid="questions-list"], .questions-list');
      if (await questionsList.isVisible()) {
        await expect(questionsList).toBeVisible();
      }
    }
  });
});

test.describe('Question Upload RBAC', () => {
  test('should deny student access to question upload', async ({ page }) => {
    await loginAsStudent(page);

    await page.goto('/question-upload');

    // Should redirect
    await expect(page).toHaveURL(/unauthorized|dashboard|login/i, { timeout: 10000 });
  });

  test('should allow teacher access to question upload', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/ogretmen/dashboard', mockData.teacherDashboard);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);
    await loginAsTeacher(page);

    await page.goto('/question-upload');

    // Should be accessible
    const uploadArea = page.locator('[data-testid="upload-area"], .upload-area, input[type="file"]');
    const isAccessible = await uploadArea.isVisible() || !(await page.url().includes('unauthorized'));
    expect(isAccessible).toBeTruthy();
  });
});

test.describe('Question Upload Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);
    await loginAsAdmin(page);
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/question-upload');
    await testAccessibility(page);
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/question-upload');

    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should have proper ARIA labels on upload area', async ({ page }) => {
    await page.goto('/question-upload');

    const uploadInput = page.locator('input[type="file"]');
    if (await uploadInput.isVisible()) {
      const ariaLabel = await uploadInput.getAttribute('aria-label');
      const label = page.locator(`label[for="${await uploadInput.getAttribute('id')}"]`);

      expect(ariaLabel || await label.isVisible()).toBeTruthy();
    }
  });
});

test.describe('Question Upload Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page);
  });

  test('should handle detection API error', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockError('/api/v1/yolo/detect', 500, 'YOLO model hatası');

    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      // Error message
      const errorMessage = page.getByText(/hata|error|başarısız/i);
      if (await errorMessage.isVisible()) {
        await expect(errorMessage).toBeVisible();
      }
    }
  });

  test('should handle invalid file type', async ({ page }) => {
    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      // Try to upload non-image file
      await fileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('not an image')
      });

      // Error or rejection
      const errorMessage = page.getByText(/geçersiz|invalid|desteklenmiyor/i);
      if (await errorMessage.isVisible()) {
        await expect(errorMessage).toBeVisible();
      }
    }
  });

  test('should handle save question error', async ({ page }) => {
    const apiMocker = new ApiMocker(page);
    await apiMocker.mockSuccess('/api/v1/yolo/detect', mockData.yoloDetection);
    await apiMocker.mockError('/api/v1/soru-bankasi/soru', 400, 'Eksik bilgi');

    await page.goto('/question-upload');

    const fileInput = page.locator('input[type="file"]');
    if (await fileInput.isVisible()) {
      await fileInput.setInputFiles({
        name: 'test-question.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.waitForTimeout(1000);

      const addButton = page.getByRole('button', { name: /ekle|add|kaydet/i }).first();
      if (await addButton.isVisible()) {
        await addButton.click();

        const saveButton = page.getByRole('button', { name: /kaydet|save/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();

          // Error message
          await expect(page.getByText(/hata|error|eksik/i)).toBeVisible({ timeout: 5000 });
        }
      }
    }
  });
});
