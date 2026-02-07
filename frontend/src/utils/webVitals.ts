/**
 * Web Vitals Performance Monitoring
 *
 * Core Web Vitals tracking for performance optimization
 * Monitors: LCP, FID, CLS, FCP, TTFB, INP
 *
 * @see https://web.dev/vitals/
 */

export interface VitalsMetric {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  delta: number
  id: string
  navigationType?: string
}

interface AnalyticsData {
  event_category: string
  event_label: string
  value: number
  metric_id: string
  metric_value: number
  metric_delta: number
  metric_rating: string
}

/**
 * Sends Web Vitals metrics to analytics service
 */
const sendToAnalytics = (metric: VitalsMetric): void => {
  // Google Analytics 4 (gtag.js)
  if (typeof window !== 'undefined' && (window as any).gtag) {
    const analyticsData: AnalyticsData = {
      event_category: 'Web Vitals',
      event_label: metric.id,
      value: Math.round(metric.value),
      metric_id: metric.id,
      metric_value: metric.value,
      metric_delta: metric.delta,
      metric_rating: metric.rating,
    }

    ;(window as any).gtag('event', metric.name, analyticsData);
  }

  // Send to custom backend analytics endpoint
  if (process.env.NODE_ENV === 'production') {
    try {
      navigator.sendBeacon(
        '/api/analytics/web-vitals',
        JSON.stringify({
          name: metric.name,
          value: metric.value,
          rating: metric.rating,
          delta: metric.delta,
          id: metric.id,
          timestamp: Date.now(),
          url: window.location.href,
          userAgent: navigator.userAgent,
        }),
      );
    } catch (error) {
      console.error('Failed to send Web Vitals metric:', error);
    }
  }

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.log(
      `%c[Web Vitals] ${metric.name}`,
      `color: ${metric.rating === 'good' ? '#0cce6b' : metric.rating === 'needs-improvement' ? '#ffa400' : '#ff4e42'}`,
      {
        value: `${metric.value.toFixed(2)}ms`,
        rating: metric.rating,
        delta: metric.delta,
      },
    );
  }
};

/**
 * Initialize Web Vitals monitoring
 * Dynamically imports web-vitals library and sets up tracking
 */
export const initWebVitals = async (): Promise<void> => {
  try {
    // Dynamically import web-vitals to reduce initial bundle size
    const webVitalsModule = await import('web-vitals');

    // Track all Core Web Vitals
    webVitalsModule.onCLS(sendToAnalytics);   // Cumulative Layout Shift
    webVitalsModule.onLCP(sendToAnalytics);   // Largest Contentful Paint
    webVitalsModule.onFCP(sendToAnalytics);   // First Contentful Paint
    webVitalsModule.onTTFB(sendToAnalytics);  // Time to First Byte
    webVitalsModule.onINP(sendToAnalytics);   // Interaction to Next Paint (replaces FID)

    console.log('[Web Vitals] Monitoring initialized');
  } catch (error) {
    console.warn('[Web Vitals] Failed to initialize:', error);
    console.info('[Web Vitals] Run: npm install web-vitals');
  }
};

/**
 * Fallback implementation when web-vitals library is not available
 * Uses Performance Observer API
 */
export const initWebVitalsFallback = (): void => {
  if (typeof window === 'undefined' || !window.PerformanceObserver) {
    return;
  }

  // Observe Largest Contentful Paint (LCP)
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as any;

      const value = lastEntry.renderTime || lastEntry.loadTime;
      const rating: 'good' | 'needs-improvement' | 'poor' =
        value <= 2500 ? 'good' : value <= 4000 ? 'needs-improvement' : 'poor';

      sendToAnalytics({
        name: 'LCP',
        value,
        rating,
        delta: value,
        id: `lcp-${Date.now()}`,
      });
    });

    lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (error) {
    console.warn('[Web Vitals] LCP observer failed:', error);
  }

  // Observe First Input Delay (FID)
  try {
    const fidObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry: any) => {
        const value = entry.processingStart - entry.startTime;
        const rating: 'good' | 'needs-improvement' | 'poor' =
          value <= 100 ? 'good' : value <= 300 ? 'needs-improvement' : 'poor';

        sendToAnalytics({
          name: 'FID',
          value,
          rating,
          delta: value,
          id: `fid-${Date.now()}`,
        });
      });
    });

    fidObserver.observe({ type: 'first-input', buffered: true });
  } catch (error) {
    console.warn('[Web Vitals] FID observer failed:', error);
  }

  // Observe Cumulative Layout Shift (CLS)
  try {
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry: any) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      });

      const rating: 'good' | 'needs-improvement' | 'poor' =
        clsValue <= 0.1 ? 'good' : clsValue <= 0.25 ? 'needs-improvement' : 'poor';

      sendToAnalytics({
        name: 'CLS',
        value: clsValue,
        rating,
        delta: clsValue,
        id: `cls-${Date.now()}`,
      });
    });

    clsObserver.observe({ type: 'layout-shift', buffered: true });
  } catch (error) {
    console.warn('[Web Vitals] CLS observer failed:', error);
  }

  console.log('[Web Vitals] Fallback monitoring initialized');
};

/**
 * Report custom performance metrics
 */
export const reportCustomMetric = (metricName: string, value: number): void => {
  const rating: 'good' | 'needs-improvement' | 'poor' = 'good'; // Simplified

  sendToAnalytics({
    name: metricName,
    value,
    rating,
    delta: value,
    id: `custom-${metricName}-${Date.now()}`,
  });
};

/**
 * Get current performance metrics snapshot
 */
export const getPerformanceSnapshot = (): Record<string, any> => {
  if (typeof window === 'undefined' || !window.performance) {
    return {};
  }

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  const paint = performance.getEntriesByType('paint');

  return {
    // Navigation Timing
    dns: navigation?.domainLookupEnd - navigation?.domainLookupStart,
    tcp: navigation?.connectEnd - navigation?.connectStart,
    ttfb: navigation?.responseStart - navigation?.requestStart,
    download: navigation?.responseEnd - navigation?.responseStart,
    domInteractive: navigation?.domInteractive,
    domComplete: navigation?.domComplete,
    loadComplete: navigation?.loadEventEnd,

    // Paint Timing
    fcp: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime,

    // Resource Timing
    resourceCount: performance.getEntriesByType('resource').length,

    // Memory (if available)
    memory: (performance as any).memory ? {
      usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
      totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
      jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit,
    } : null,
  };
};

export default initWebVitals;
