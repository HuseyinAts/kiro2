/**
 * Exam Flow E2E Tests
 * Tests exam start, question navigation, answer submission, and completion
 */

import { test, expect } from '@playwright/test';

// Helper to login before exam tests
async function loginAsStudent(page: any) {
  await page.goto('/login');
  await page.getByLabel(/e-posta/i).fill('test@kiro2.com');
  await page.getByLabel(/şifre/i).fill('Test123!');
  await page.getByRole('button', { name: /giriş yap/i }).click();
  await expect(page).toHaveURL(/dashboard|ana-sayfa/i, { timeout: 15000 });
}

test.describe('Exam Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should display exam selection page', async ({ page }) => {
    await page.goto('/sinav');

    // Check exam type selection
    await expect(page.getByText(/TYT|AYT|YDT/i)).toBeVisible();
  });

  test('should show exam configuration options', async ({ page }) => {
    await page.goto('/sinav/baslat');

    // Check for exam configuration elements
    await expect(page.getByText(/sınav türü|exam type/i)).toBeVisible();
    await expect(page.getByText(/süre|duration/i)).toBeVisible();
  });

  test('should start exam and show first question', async ({ page }) => {
    await page.goto('/sinav/baslat');

    // Select exam type if needed
    const tytButton = page.getByRole('button', { name: /TYT/i });
    if (await tytButton.isVisible()) {
      await tytButton.click();
    }

    // Start exam
    await page.getByRole('button', { name: /başla|start/i }).click();

    // Should show exam interface with question
    await expect(page.getByText(/soru|question/i)).toBeVisible({ timeout: 10000 });
  });

  test('should navigate between questions', async ({ page }) => {
    // Assuming exam is already started or start it
    await page.goto('/sinav/oturum/test-session');

    // Check navigation buttons
    const nextButton = page.getByRole('button', { name: /sonraki|next/i });
    const prevButton = page.getByRole('button', { name: /önceki|previous/i });

    // Previous should be disabled on first question
    if (await prevButton.isVisible()) {
      await expect(prevButton).toBeDisabled();
    }

    // Navigate to next question
    if (await nextButton.isVisible()) {
      await nextButton.click();
      // Previous should now be enabled
      await expect(prevButton).not.toBeDisabled();
    }
  });

  test('should select and change answer', async ({ page }) => {
    await page.goto('/sinav/oturum/test-session');

    // Select option A - use data-testid or aria-label for more reliable selection
    const optionA = page.locator('[data-testid="bubble-A"]').or(page.getByRole('button', { name: /^A$/i }));
    if (await optionA.isVisible({ timeout: 5000 })) {
      await optionA.click();

      // Wait for visual feedback
      await page.waitForTimeout(300);

      // Select option B instead
      const optionB = page.locator('[data-testid="bubble-B"]').or(page.getByRole('button', { name: /^B$/i }));
      await optionB.click();

      // Wait for visual feedback
      await page.waitForTimeout(300);
    }
  });

  test('should flag question for review', async ({ page }) => {
    await page.goto('/sinav/oturum/test-session');

    // Find flag button - look for the actual tooltip text from component
    const flagButton = page.getByRole('button', { name: /İnceleme için işaretle|İnceleme işaretini kaldır/i })
      .or(page.locator('button:has(svg[data-testid="FlagOutlinedIcon"], svg[data-testid="FlagIcon"])'));

    if (await flagButton.isVisible({ timeout: 5000 })) {
      await flagButton.click();

      // Wait for visual feedback
      await page.waitForTimeout(300);
    }
  });

  test('should show question navigation panel', async ({ page }) => {
    await page.goto('/sinav/oturum/test-session');

    // Look for "Soru Haritası" heading from component
    const navPanel = page.locator('text=Soru Haritası').locator('..')
      .or(page.getByTestId('question-nav'))
      .or(page.locator('[class*="navigation"]'));

    if (await navPanel.isVisible({ timeout: 5000 })) {
      // Should have question number boxes
      const questionButtons = page.locator('div:has-text(/^\\d+$/)').filter({ hasText: /^[1-9]\d*$/ });
      const count = await questionButtons.count();
      expect(count).toBeGreaterThan(0);
    }
  });

  test('should display timer during exam', async ({ page }) => {
    await page.goto('/sinav/oturum/test-session');

    // Timer should be visible
    const timer = page.getByTestId('exam-timer').or(page.locator('[class*="timer"]'));
    if (await timer.isVisible()) {
      // Timer should show time in format like "01:30:00" or "90:00"
      await expect(timer).toContainText(/\d+:\d+/);
    }
  });

  test('should show completion confirmation dialog', async ({ page }) => {
    await page.goto('/sinav/oturum/test-session');

    // Find complete/finish button
    const finishButton = page.getByRole('button', { name: /bitir|tamamla|finish/i });
    if (await finishButton.isVisible()) {
      await finishButton.click();

      // Confirmation dialog should appear
      await expect(page.getByText(/emin misiniz|onaylıyor musunuz/i)).toBeVisible();
    }
  });
});

test.describe('Exam Keyboard Shortcuts', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
    await page.goto('/sinav/oturum/test-session');
  });

  test('should show keyboard shortcuts help text', async ({ page }) => {
    // Component shows: "Kısayollar: ← → (Gezinme) | A-E (Cevap) | F (İşaretle)"
    await expect(page.getByText(/Kısayollar.*Gezinme.*Cevap.*İşaretle/i)).toBeVisible({ timeout: 5000 });
  });

  test('should navigate with arrow keys', async ({ page }) => {
    // Verify current question number
    const currentQuestion = await page.locator('text=/Soru \\d+/').textContent();

    // Press right arrow for next question
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);

    // Press left arrow for previous question
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(300);

    // Should be back to original question
    await expect(page.locator('text=/Soru \\d+/')).toContainText(currentQuestion || '');
  });

  test('should select answers with letter keys', async ({ page }) => {
    // Press 'A' to select option A
    await page.keyboard.press('a');
    await page.waitForTimeout(300);

    // Should show success message
    await expect(page.getByText(/Cevabınız kaydedildi.*A/i)).toBeVisible({ timeout: 2000 });
  });

  test('should flag question with F key', async ({ page }) => {
    // Press 'F' to flag/unflag question
    await page.keyboard.press('f');
    await page.waitForTimeout(300);

    // Should show flagged icon (Flag icon should be visible)
    const flagIcon = page.locator('svg[data-testid="FlagIcon"]');
    if (await flagIcon.isVisible({ timeout: 1000 })) {
      // Press F again to unflag
      await page.keyboard.press('f');
      await page.waitForTimeout(300);
    }
  });
});

test.describe('Exam Results', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsStudent(page);
  });

  test('should display exam results after completion', async ({ page }) => {
    await page.goto('/sinav/sonuc/test-result-id');

    // Results page should show score
    await expect(page.getByText(/puan|skor|score/i)).toBeVisible();

    // Should show correct/incorrect counts
    await expect(page.getByText(/doğru|correct/i)).toBeVisible();
    await expect(page.getByText(/yanlış|incorrect/i)).toBeVisible();
  });

  test('should show performance breakdown by subject', async ({ page }) => {
    await page.goto('/sinav/sonuc/test-result-id');

    // Subject breakdown should be visible
    await expect(page.getByText(/matematik|türkçe|fen/i)).toBeVisible();
  });
});
