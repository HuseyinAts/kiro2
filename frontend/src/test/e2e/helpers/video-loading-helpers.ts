/**
 * E2E Test Helpers for Video Loading Tests
 * 
 * Common utilities and mock data for video loading E2E tests
 */

import { Page, Route } from '@playwright/test';

/**
 * Mock video data for testing
 */
export const mockVideoData = {
  success: {
    recommendations: [
      {
        subject_exam: 'TYT Matematik',
        videos: [
          {
            video_id: 'test_video_1',
            title: 'TYT Matematik - Fonksiyonlar Konu Anlatımı',
            channel: 'Matematik Öğretmeni',
            duration: '15:30',
            quality_score: 8.5,
            subject: 'matematik',
            difficulty: 'orta',
            language_score: 0.95,
            relevance_score: 0.88,
            url: 'https://www.youtube.com/embed/test_video_1'
          },
          {
            video_id: 'test_video_2',
            title: 'TYT Matematik - Türev Konusu',
            channel: 'TonguçAkademi',
            duration: '18:45',
            quality_score: 9.2,
            subject: 'matematik',
            difficulty: 'orta',
            language_score: 0.98,
            relevance_score: 0.92,
            url: 'https://www.youtube.com/embed/test_video_2'
          }
        ],
        total_count: 2,
        cache_hit: false,
        response_time_ms: 1500
      },
      {
        subject_exam: 'TYT Fizik',
        videos: [
          {
            video_id: 'test_video_3',
            title: 'TYT Fizik - Hareket Konusu',
            channel: 'Fizik Öğretmeni',
            duration: '20:15',
            quality_score: 8.8,
            subject: 'fizik',
            difficulty: 'orta',
            language_score: 0.96,
            relevance_score: 0.85,
            url: 'https://www.youtube.com/embed/test_video_3'
          }
        ],
        total_count: 1,
        cache_hit: false,
        response_time_ms: 1800
      }
    ],
    total_count: 3
  },
  
  cached: {
    recommendations: [
      {
        subject_exam: 'TYT Matematik',
        videos: [
          {
            video_id: 'cached_video_1',
            title: 'TYT Matematik - Cached Video',
            channel: 'Test Channel',
            duration: '10:00',
            quality_score: 8.0,
            subject: 'matematik',
            url: 'https://www.youtube.com/embed/cached_video_1'
          }
        ],
        total_count: 1,
        cache_hit: true,
        response_time_ms: 50
      }
    ],
    total_count: 1
  },
  
  empty: {
    recommendations: [],
    total_count: 0
  }
};

/**
 * Mock API responses for different scenarios
 */
export class VideoLoadingMocks {
  private page: Page;
  private apiBaseUrl: string;

  constructor(page: Page, apiBaseUrl: string = 'http://localhost:8001') {
    this.page = page;
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Mock successful video loading
   */
  async mockSuccess(delay: number = 1000) {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await new Promise(resolve => setTimeout(resolve, delay));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockVideoData.success)
      });
    });
  }

  /**
   * Mock cached video response
   */
  async mockCached() {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockVideoData.cached)
      });
    });
  }

  /**
   * Mock timeout (slow response)
   */
  async mockTimeout(delay: number = 25000) {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await new Promise(resolve => setTimeout(resolve, delay));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockVideoData.success)
      });
    });
  }

  /**
   * Mock server error (500)
   */
  async mockServerError() {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal Server Error',
          message: 'Sunucu hatası oluştu'
        })
      });
    });
  }

  /**
   * Mock network error
   */
  async mockNetworkError() {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await route.abort('failed');
    });
  }

  /**
   * Mock rate limit error (429)
   */
  async mockRateLimitError() {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Too Many Requests',
          message: 'Çok fazla istek gönderildi',
          retry_after: 60
        })
      });
    });
  }

  /**
   * Mock progressive success (fail first, then succeed)
   */
  async mockProgressiveSuccess(failCount: number = 1) {
    let requestCount = 0;
    
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      requestCount++;
      
      if (requestCount <= failCount) {
        await route.abort('failed');
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockVideoData.success)
        });
      }
    });
  }

  /**
   * Mock empty results
   */
  async mockEmptyResults() {
    await this.page.route(`${this.apiBaseUrl}/api/v1/youtube/recommendations`, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockVideoData.empty)
      });
    });
  }

  /**
   * Clear all mocks
   */
  async clearMocks() {
    await this.page.unroute(`${this.apiBaseUrl}/api/v1/youtube/recommendations`);
  }
}

/**
 * Page object for Learning Path page
 */
export class LearningPathPage {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to learning path page
   */
  async navigate() {
    await this.page.goto('/learning-path');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Click create learning path button
   */
  async clickCreateLearningPath() {
    await this.page.click('text=Öğrenme Yolu Oluştur');
  }

  /**
   * Wait for loading state
   */
  async waitForLoading() {
    await this.page.waitForSelector('[data-testid="video-loading-indicator"]', { timeout: 5000 });
  }

  /**
   * Wait for success state
   */
  async waitForSuccess() {
    await this.page.waitForSelector('[data-testid="video-success-message"]', { timeout: 30000 });
  }

  /**
   * Wait for error state
   */
  async waitForError() {
    await this.page.waitForSelector('[data-testid="video-error-message"]', { timeout: 30000 });
  }

  /**
   * Wait for fallback state
   */
  async waitForFallback() {
    await this.page.waitForSelector('[data-testid="fallback-videos"]', { timeout: 5000 });
  }

  /**
   * Click retry button
   */
  async clickRetry() {
    await this.page.click('[data-testid="retry-button"]');
  }

  /**
   * Click show fallback button
   */
  async clickShowFallback() {
    await this.page.click('[data-testid="show-fallback-button"]');
  }

  /**
   * Click cancel button
   */
  async clickCancel() {
    const cancelButton = this.page.locator('[data-testid="cancel-load-button"]');
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
    }
  }

  /**
   * Get video cards
   */
  getVideoCards() {
    return this.page.locator('[data-testid="video-card"]');
  }

  /**
   * Get fallback video cards
   */
  getFallbackVideoCards() {
    return this.page.locator('[data-testid="fallback-video-card"]');
  }

  /**
   * Get loading indicator
   */
  getLoadingIndicator() {
    return this.page.locator('[data-testid="video-loading-indicator"]');
  }

  /**
   * Get error message
   */
  getErrorMessage() {
    return this.page.locator('[data-testid="video-error-message"]');
  }

  /**
   * Get success message
   */
  getSuccessMessage() {
    return this.page.locator('[data-testid="video-success-message"]');
  }

  /**
   * Get offline indicator
   */
  getOfflineIndicator() {
    return this.page.locator('[data-testid="offline-indicator"]');
  }

  /**
   * Get cache hit indicator
   */
  getCacheHitIndicator() {
    return this.page.locator('[data-testid="cache-hit-indicator"]');
  }

  /**
   * Get network quality indicator
   */
  getNetworkQualityIndicator() {
    return this.page.locator('[data-testid="network-quality-indicator"]');
  }

  /**
   * Check if loading
   */
  async isLoading() {
    return await this.getLoadingIndicator().isVisible();
  }

  /**
   * Check if error displayed
   */
  async hasError() {
    return await this.getErrorMessage().isVisible();
  }

  /**
   * Check if success displayed
   */
  async hasSuccess() {
    return await this.getSuccessMessage().isVisible();
  }

  /**
   * Get video count from success message
   */
  async getVideoCount() {
    const successMessage = await this.getSuccessMessage().textContent();
    const match = successMessage?.match(/(\d+)\s+video/);
    return match ? parseInt(match[1]) : 0;
  }

  /**
   * Get loading time from UI
   */
  async getLoadingTime() {
    const timeElement = this.page.locator('[data-testid="loading-time"]');
    if (await timeElement.isVisible()) {
      const text = await timeElement.textContent();
      const match = text?.match(/(\d+\.?\d*)\s*(ms|s)/);
      if (match) {
        const value = parseFloat(match[1]);
        const unit = match[2];
        return unit === 's' ? value * 1000 : value;
      }
    }
    return 0;
  }
}

/**
 * Utility functions for E2E tests
 */
export class TestUtils {
  /**
   * Wait for network idle
   */
  static async waitForNetworkIdle(page: Page, timeout: number = 5000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Measure performance
   */
  static async measurePerformance(page: Page, action: () => Promise<void>) {
    const startTime = Date.now();
    await action();
    const endTime = Date.now();
    return endTime - startTime;
  }

  /**
   * Take screenshot on failure
   */
  static async screenshotOnFailure(page: Page, testName: string) {
    await page.screenshot({
      path: `test-results/screenshots/${testName}-failure.png`,
      fullPage: true
    });
  }

  /**
   * Get console logs
   */
  static setupConsoleCapture(page: Page) {
    const logs: string[] = [];
    
    page.on('console', msg => {
      logs.push(`${msg.type()}: ${msg.text()}`);
    });
    
    return logs;
  }

  /**
   * Get network requests
   */
  static setupNetworkCapture(page: Page) {
    const requests: any[] = [];
    
    page.on('request', request => {
      requests.push({
        url: request.url(),
        method: request.method(),
        timestamp: Date.now()
      });
    });
    
    return requests;
  }

  /**
   * Simulate slow network
   */
  static async simulateSlowNetwork(page: Page) {
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: 50 * 1024, // 50 KB/s
      uploadThroughput: 20 * 1024,   // 20 KB/s
      latency: 500                    // 500ms latency
    });
  }

  /**
   * Simulate offline
   */
  static async simulateOffline(page: Page) {
    await page.context().setOffline(true);
  }

  /**
   * Restore online
   */
  static async restoreOnline(page: Page) {
    await page.context().setOffline(false);
  }
}
