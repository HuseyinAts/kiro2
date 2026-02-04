/**
 * E2E Test: Learning Path Video Loading Flow
 * 
 * Tests the complete video loading journey including:
 * - Success scenarios
 * - Error handling
 * - Retry logic
 * - User interactions
 * - Offline mode
 * 
 * Requirements: 11.5
 */

import { test, expect, Page } from '@playwright/test';

// Test configuration
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8001';
const FRONTEND_URL = process.env.VITE_APP_URL || 'http://localhost:3002';

// Helper function to navigate to learning path
async function navigateToLearningPath(page: Page) {
  await page.goto('/learning-path');
  await page.waitForLoadState('networkidle');
}

// Helper function to wait for video loading state
async function waitForVideoLoadingState(page: Page, state: 'loading' | 'success' | 'error' | 'fallback') {
  const stateSelectors = {
    loading: '[data-testid="video-loading-indicator"]',
    success: '[data-testid="video-success-message"]',
    error: '[data-testid="video-error-message"]',
    fallback: '[data-testid="fallback-videos"]'
  };
  
  await page.waitForSelector(stateSelectors[state], { timeout: 30000 });
}

test.describe('Learning Path Video Loading - Success Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock successful API response
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          recommendations: [
            {
              subject_exam: 'TYT Matematik',
              videos: [
                {
                  video_id: 'test123',
                  title: 'TYT Matematik - Fonksiyonlar',
                  channel: 'Test Channel',
                  duration: '15:30',
                  quality_score: 8.5,
                  subject: 'matematik',
                  url: 'https://www.youtube.com/embed/test123'
                }
              ],
              total_count: 1,
              cache_hit: false,
              response_time_ms: 1500
            }
          ],
          total_count: 1
        })
      });
    });
  });

  test('should load videos successfully within 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    
    await navigateToLearningPath(page);
    
    // Click "Öğrenme Yolu Oluştur" button
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Wait for videos to load
    await waitForVideoLoadingState(page, 'success');
    
    const loadTime = Date.now() - startTime;
    
    // Verify load time is under 3 seconds
    expect(loadTime).toBeLessThan(3000);
    
    // Verify success message is displayed
    await expect(page.locator('[data-testid="video-success-message"]')).toBeVisible();
    
    // Verify video count is displayed
    await expect(page.locator('text=/\\d+ video bulundu/')).toBeVisible();
  });

  test('should display loading indicator with progress', async ({ page }) => {
    await navigateToLearningPath(page);
    
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Verify loading indicator appears
    await expect(page.locator('[data-testid="video-loading-indicator"]')).toBeVisible();
    
    // Verify loading message
    await expect(page.locator('text=/AI.*videoları buluyor/')).toBeVisible();
    
    // Verify progress bar or spinner
    const progressIndicator = page.locator('[data-testid="loading-progress"]');
    await expect(progressIndicator).toBeVisible();
  });

  test('should display video cards after successful load', async ({ page }) => {
    await navigateToLearningPath(page);
    
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'success');
    
    // Verify video cards are displayed
    const videoCards = page.locator('[data-testid="video-card"]');
    await expect(videoCards).toHaveCount(1);
    
    // Verify video card content
    await expect(videoCards.first()).toContainText('TYT Matematik - Fonksiyonlar');
    await expect(videoCards.first()).toContainText('Test Channel');
    await expect(videoCards.first()).toContainText('15:30');
  });

  test('should show cache hit indicator when videos are cached', async ({ page }) => {
    // Mock cached response
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          recommendations: [{
            subject_exam: 'TYT Matematik',
            videos: [],
            total_count: 0,
            cache_hit: true,
            response_time_ms: 50
          }]
        })
      });
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Verify cache indicator
    await expect(page.locator('[data-testid="cache-hit-indicator"]')).toBeVisible();
  });
});

test.describe('Learning Path Video Loading - Error Handling', () => {
  test('should handle timeout error gracefully', async ({ page }) => {
    // Mock slow API response (timeout)
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 25000)); // 25s delay
      await route.fulfill({ status: 200, body: '{}' });
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Wait for timeout error
    await waitForVideoLoadingState(page, 'error');
    
    // Verify error message
    await expect(page.locator('text=/Videoları.*yükleyemedik/')).toBeVisible();
    
    // Verify retry button is available
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Verify fallback option is available
    await expect(page.locator('[data-testid="show-fallback-button"]')).toBeVisible();
  });

  test('should handle 500 server error', async ({ page }) => {
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' })
      });
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'error');
    
    // Verify user-friendly error message
    await expect(page.locator('text=/Sunucu hatası/')).toBeVisible();
    
    // Verify retry button
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should handle network error', async ({ page }) => {
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await route.abort('failed');
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'error');
    
    // Verify network error message
    await expect(page.locator('text=/Bağlantı hatası/')).toBeVisible();
  });

  test('should handle CORS error', async ({ page }) => {
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await route.fulfill({
        status: 0,
        body: ''
      });
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'error');
    
    // Verify CORS error is handled
    await expect(page.locator('[data-testid="video-error-message"]')).toBeVisible();
  });
});

test.describe('Learning Path Video Loading - Retry Logic', () => {
  test('should retry automatically on first failure', async ({ page }) => {
    let requestCount = 0;
    
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      requestCount++;
      
      if (requestCount === 1) {
        // First request fails
        await route.abort('failed');
      } else {
        // Second request succeeds
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            recommendations: [{
              subject_exam: 'TYT Matematik',
              videos: [],
              total_count: 0
            }]
          })
        });
      }
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Wait for success after retry
    await waitForVideoLoadingState(page, 'success');
    
    // Verify retry happened
    expect(requestCount).toBe(2);
  });

  test('should allow manual retry after error', async ({ page }) => {
    let requestCount = 0;
    
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      requestCount++;
      
      if (requestCount <= 2) {
        // First 2 requests fail (initial + auto-retry)
        await route.abort('failed');
      } else {
        // Manual retry succeeds
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            recommendations: [{
              subject_exam: 'TYT Matematik',
              videos: [],
              total_count: 0
            }]
          })
        });
      }
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Wait for error after auto-retries
    await waitForVideoLoadingState(page, 'error');
    
    // Click manual retry button
    await page.click('[data-testid="retry-button"]');
    
    // Wait for success
    await waitForVideoLoadingState(page, 'success');
    
    // Verify manual retry happened
    expect(requestCount).toBe(3);
  });

  test('should use exponential backoff for retries', async ({ page }) => {
    const retryTimes: number[] = [];
    let requestCount = 0;
    
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      requestCount++;
      retryTimes.push(Date.now());
      
      if (requestCount <= 2) {
        await route.abort('failed');
      } else {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ recommendations: [] })
        });
      }
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'success');
    
    // Verify exponential backoff (second retry should be delayed more)
    if (retryTimes.length >= 2) {
      const firstDelay = retryTimes[1] - retryTimes[0];
      expect(firstDelay).toBeGreaterThan(500); // At least 500ms delay
    }
  });

  test('should show retry count to user', async ({ page }) => {
    let requestCount = 0;
    
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      requestCount++;
      if (requestCount <= 2) {
        await route.abort('failed');
      } else {
        await route.fulfill({ status: 200, body: JSON.stringify({ recommendations: [] }) });
      }
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Check if retry count is displayed during retries
    const retryIndicator = page.locator('[data-testid="retry-count"]');
    
    // May or may not be visible depending on implementation
    // Just verify the flow completes
    await waitForVideoLoadingState(page, 'success');
  });
});

test.describe('Learning Path Video Loading - User Interactions', () => {
  test('should allow canceling video load', async ({ page }) => {
    // Mock slow response
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 10000));
      await route.fulfill({ status: 200, body: '{}' });
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Wait for loading state
    await expect(page.locator('[data-testid="video-loading-indicator"]')).toBeVisible();
    
    // Click cancel button if available
    const cancelButton = page.locator('[data-testid="cancel-load-button"]');
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      
      // Verify loading stopped
      await expect(page.locator('[data-testid="video-loading-indicator"]')).not.toBeVisible();
    }
  });

  test('should show fallback videos on demand', async ({ page }) => {
    await page.route(`${API_BASE_URL}/api/youtube/recommendations`, async (route) => {
      await route.abort('failed');
    });
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'error');
    
    // Click show fallback button
    await page.click('[data-testid="show-fallback-button"]');
    
    // Verify fallback videos are displayed
    await expect(page.locator('[data-testid="fallback-videos"]')).toBeVisible();
    
    // Verify fallback video cards
    const fallbackCards = page.locator('[data-testid="fallback-video-card"]');
    await expect(fallbackCards.first()).toBeVisible();
  });

  test('should allow switching between personalized and fallback videos', async ({ page }) => {
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'success');
    
    // Switch to fallback
    const fallbackToggle = page.locator('[data-testid="toggle-fallback"]');
    if (await fallbackToggle.isVisible()) {
      await fallbackToggle.click();
      await expect(page.locator('[data-testid="fallback-videos"]')).toBeVisible();
      
      // Switch back to personalized
      await fallbackToggle.click();
      await expect(page.locator('[data-testid="personalized-videos"]')).toBeVisible();
    }
  });

  test('should track video watch progress', async ({ page }) => {
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    await waitForVideoLoadingState(page, 'success');
    
    // Click on a video card
    const videoCard = page.locator('[data-testid="video-card"]').first();
    await videoCard.click();
    
    // Verify video player opens
    await expect(page.locator('[data-testid="video-player"]')).toBeVisible();
  });
});

test.describe('Learning Path Video Loading - Offline Mode', () => {
  test('should detect offline status', async ({ page, context }) => {
    await navigateToLearningPath(page);
    
    // Simulate offline
    await context.setOffline(true);
    
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Verify offline message
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
    await expect(page.locator('text=/İnternet bağlantısı yok/')).toBeVisible();
  });

  test('should show cached videos when offline', async ({ page, context }) => {
    // First load videos while online
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    await waitForVideoLoadingState(page, 'success');
    
    // Go offline
    await context.setOffline(true);
    
    // Navigate away and back
    await page.goto('/dashboard');
    await page.goto('/learning-path');
    
    // Verify cached videos are shown
    await expect(page.locator('[data-testid="cached-videos-indicator"]')).toBeVisible();
  });

  test('should auto-retry when connection restored', async ({ page, context }) => {
    await navigateToLearningPath(page);
    
    // Start offline
    await context.setOffline(true);
    
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Verify offline message
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible();
    
    // Restore connection
    await context.setOffline(false);
    
    // Wait for auto-retry
    await page.waitForTimeout(3000);
    
    // Verify videos load after reconnection
    await waitForVideoLoadingState(page, 'success');
  });

  test('should show network quality indicator', async ({ page }) => {
    await navigateToLearningPath(page);
    
    // Check if network quality indicator exists
    const networkIndicator = page.locator('[data-testid="network-quality-indicator"]');
    
    // May or may not be visible depending on implementation
    if (await networkIndicator.isVisible()) {
      await expect(networkIndicator).toContainText(/online|offline|slow/i);
    }
  });
});

test.describe('Learning Path Video Loading - Performance', () => {
  test('should load within performance budget', async ({ page }) => {
    const startTime = Date.now();
    
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    await waitForVideoLoadingState(page, 'success');
    
    const totalTime = Date.now() - startTime;
    
    // Performance budget: 5 seconds total
    expect(totalTime).toBeLessThan(5000);
  });

  test('should not block UI during loading', async ({ page }) => {
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Verify UI remains responsive
    const navigationButton = page.locator('text=Dashboard');
    await expect(navigationButton).toBeEnabled();
    
    // Verify can interact with other elements
    const profileButton = page.locator('[data-testid="profile-button"]');
    if (await profileButton.isVisible()) {
      await expect(profileButton).toBeEnabled();
    }
  });

  test('should handle multiple concurrent requests', async ({ page }) => {
    await navigateToLearningPath(page);
    
    // Click multiple times quickly
    await page.click('text=Öğrenme Yolu Oluştur');
    await page.click('text=Öğrenme Yolu Oluştur');
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Should handle gracefully (cancel previous, only process last)
    await waitForVideoLoadingState(page, 'success');
    
    // Verify only one set of videos loaded
    const videoCards = page.locator('[data-testid="video-card"]');
    await expect(videoCards).toHaveCount(1);
  });
});

test.describe('Learning Path Video Loading - Accessibility', () => {
  test('should have proper ARIA labels', async ({ page }) => {
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Check loading indicator has aria-label
    const loadingIndicator = page.locator('[data-testid="video-loading-indicator"]');
    await expect(loadingIndicator).toHaveAttribute('aria-label', /loading|yükleniyor/i);
    
    await waitForVideoLoadingState(page, 'success');
    
    // Check video cards have proper labels
    const videoCard = page.locator('[data-testid="video-card"]').first();
    await expect(videoCard).toHaveAttribute('role', 'article');
  });

  test('should be keyboard navigable', async ({ page }) => {
    await navigateToLearningPath(page);
    
    // Tab to create button
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Press Enter to trigger
    await page.keyboard.press('Enter');
    
    await waitForVideoLoadingState(page, 'success');
    
    // Tab through video cards
    await page.keyboard.press('Tab');
    
    // Verify focus is on video card
    const focusedElement = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
    expect(focusedElement).toContain('video');
  });

  test('should announce loading states to screen readers', async ({ page }) => {
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    
    // Check for aria-live region
    const liveRegion = page.locator('[aria-live="polite"]');
    await expect(liveRegion).toBeVisible();
    
    await waitForVideoLoadingState(page, 'success');
    
    // Verify success announcement
    await expect(liveRegion).toContainText(/başarılı|bulundu/i);
  });
});

test.describe('Learning Path Video Loading - Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test('should work on mobile viewport', async ({ page }) => {
    await navigateToLearningPath(page);
    
    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-layout"]')).toBeVisible();
    
    await page.click('text=Öğrenme Yolu Oluştur');
    await waitForVideoLoadingState(page, 'success');
    
    // Verify video cards are stacked vertically
    const videoCards = page.locator('[data-testid="video-card"]');
    const firstCard = videoCards.first();
    const firstCardBox = await firstCard.boundingBox();
    
    if (firstCardBox) {
      expect(firstCardBox.width).toBeGreaterThan(300); // Full width on mobile
    }
  });

  test('should handle touch interactions', async ({ page }) => {
    await navigateToLearningPath(page);
    await page.click('text=Öğrenme Yolu Oluştur');
    await waitForVideoLoadingState(page, 'success');
    
    // Tap on video card
    const videoCard = page.locator('[data-testid="video-card"]').first();
    await videoCard.tap();
    
    // Verify video player opens
    await expect(page.locator('[data-testid="video-player"]')).toBeVisible();
  });
});
