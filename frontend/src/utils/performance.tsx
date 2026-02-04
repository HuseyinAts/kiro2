/**
 * KIRO2 Frontend Performance Utilities
 * React performance optimization and lazy loading utilities
 */

import { lazy, Suspense, ComponentType, ReactNode } from 'react';
import { Route } from 'react-router-dom';

// Performance monitoring
interface PerformanceMetrics {
  navigationStart: number;
  domContentLoaded: number;
  loadComplete: number;
  firstContentfulPaint?: number;
  largestContentfulPaint?: number;
  firstInputDelay?: number;
  cumulativeLayoutShift?: number;
}

export class PerformanceMonitor {
  private static metrics: PerformanceMetrics = {
    navigationStart: 0,
    domContentLoaded: 0,
    loadComplete: 0,
  };

  static initialize() {
    if (typeof window === 'undefined') return;

    // Navigation timing
    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      this.metrics = {
        navigationStart: navigation.startTime,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.startTime,
        loadComplete: navigation.loadEventEnd - navigation.startTime,
      };

      this.measureWebVitals();
      this.logMetrics();
    });
  }

  private static measureWebVitals() {
    // First Contentful Paint (FCP)
    const fcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const fcp = entries[entries.length - 1];
      this.metrics.firstContentfulPaint = fcp.startTime;
    });

    try {
      fcpObserver.observe({ entryTypes: ['paint'] });
    } catch (e) {
      console.warn('FCP measurement not supported');
    }

    // Largest Contentful Paint (LCP)
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lcp = entries[entries.length - 1];
      this.metrics.largestContentfulPaint = lcp.startTime;
    });

    try {
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      console.warn('LCP measurement not supported');
    }

    // First Input Delay (FID)
    const fidObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry: any) => {
        this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
      });
    });

    try {
      fidObserver.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      console.warn('FID measurement not supported');
    }

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry: any) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          this.metrics.cumulativeLayoutShift = clsValue;
        }
      });
    });

    try {
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (e) {
      console.warn('CLS measurement not supported');
    }
  }

  private static logMetrics() {
    console.group('🚀 KIRO2 Performance Metrics');
    console.log('📊 Navigation Start:', this.metrics.navigationStart, 'ms');
    console.log('🎯 DOM Content Loaded:', this.metrics.domContentLoaded, 'ms');
    console.log('✅ Load Complete:', this.metrics.loadComplete, 'ms');
    
    if (this.metrics.firstContentfulPaint) {
      console.log('🎨 First Contentful Paint:', this.metrics.firstContentfulPaint, 'ms');
    }
    
    if (this.metrics.largestContentfulPaint) {
      console.log('🖼️ Largest Contentful Paint:', this.metrics.largestContentfulPaint, 'ms');
    }
    
    if (this.metrics.firstInputDelay) {
      console.log('⚡ First Input Delay:', this.metrics.firstInputDelay, 'ms');
    }
    
    if (this.metrics.cumulativeLayoutShift) {
      console.log('📐 Cumulative Layout Shift:', this.metrics.cumulativeLayoutShift);
    }
    
    console.groupEnd();

    // Send metrics to analytics (if implemented)
    this.sendToAnalytics(this.metrics);
  }

  private static sendToAnalytics(metrics: PerformanceMetrics) {
    // Send performance metrics to your analytics service
    // This is where you'd integrate with Google Analytics, Mixpanel, etc.
    if (process.env.NODE_ENV === 'production') {
      // Example: gtag('event', 'performance', metrics);
      console.log('📈 Performance metrics would be sent to analytics:', metrics);
    }
  }

  static getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }
}

// Lazy loading utilities
interface LazyComponentProps {
  fallback?: ReactNode;
  error?: ReactNode;
}

export function createLazyComponent<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options: LazyComponentProps = {}
) {
  const LazyComponent = lazy(importFunc);
  
  const WrappedComponent = (props: any) => {
    return (
      <Suspense
        fallback={
          options.fallback || (
            <div className="flex items-center justify-center min-h-[200px]">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )
        }
      >
        <LazyComponent {...props} />
      </Suspense>
    );
  };

  WrappedComponent.displayName = `LazyComponent(${(LazyComponent as any).displayName || 'Component'})`;
  
  return WrappedComponent;
}

// Route-based code splitting
export function createLazyRoute(
  path: string,
  importFunc: () => Promise<{ default: ComponentType<any> }>,
  options: LazyComponentProps = {}
) {
  const LazyComponent = createLazyComponent(importFunc, options);
  
  return <Route path={path} element={<LazyComponent />} />;
}

// Image optimization utilities
interface ImageOptimizationOptions {
  quality?: number;
  format?: 'webp' | 'avif' | 'jpg' | 'png';
  sizes?: string;
  loading?: 'lazy' | 'eager';
  placeholder?: string;
}

export class ImageOptimizer {
  private static cache = new Map<string, HTMLImageElement>();

  static preloadImage(src: string): Promise<HTMLImageElement> {
    if (this.cache.has(src)) {
      return Promise.resolve(this.cache.get(src)!);
    }

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.cache.set(src, img);
        resolve(img);
      };
      img.onerror = reject;
      img.src = src;
    });
  }

  static preloadImages(srcs: string[]): Promise<HTMLImageElement[]> {
    return Promise.all(srcs.map(src => this.preloadImage(src)));
  }

  static generateSrcSet(
    baseUrl: string,
    widths: number[] = [320, 640, 768, 1024, 1280, 1536],
    options: ImageOptimizationOptions = {}
  ): string {
    const { quality = 80, format = 'webp' } = options;
    
    return widths
      .map(width => {
        const url = `${baseUrl}?w=${width}&q=${quality}&f=${format}`;
        return `${url} ${width}w`;
      })
      .join(', ');
  }

  static generateSizes(breakpoints: Record<string, string> = {
    '(max-width: 640px)': '100vw',
    '(max-width: 768px)': '50vw',
    '(max-width: 1024px)': '33vw',
    default: '25vw'
  }): string {
    const entries = Object.entries(breakpoints);
    const mediaQueries = entries.slice(0, -1).map(([media, size]) => `${media} ${size}`);
    const defaultSize = entries[entries.length - 1][1];
    
    return [...mediaQueries, defaultSize].join(', ');
  }
}

// Component memoization utilities
export function createMemoizedComponent<T extends ComponentType<any>>(
  Component: T,
  areEqual?: (prevProps: any, nextProps: any) => boolean
): React.MemoExoticComponent<T> {
  const MemoizedComponent = React.memo(Component, areEqual);
  MemoizedComponent.displayName = `Memo(${Component.displayName || Component.name})`;
  return MemoizedComponent;
}

// Bundle analysis utilities
export class BundleAnalyzer {
  private static componentSizes = new Map<string, number>();

  static measureComponentSize(componentName: string, size: number) {
    this.componentSizes.set(componentName, size);
  }

  static getComponentSizes(): Record<string, number> {
    return Object.fromEntries(this.componentSizes);
  }

  static logLargestComponents(limit: number = 10) {
    const sorted = Array.from(this.componentSizes.entries())
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit);

    console.group('📦 Largest Components');
    sorted.forEach(([name, size]) => {
      console.log(`${name}: ${(size / 1024).toFixed(2)}KB`);
    });
    console.groupEnd();
  }
}

// Resource prefetching
export class ResourcePrefetcher {
  private static prefetched = new Set<string>();

  static prefetchRoute(route: string) {
    if (this.prefetched.has(route) || typeof window === 'undefined') {
      return;
    }

    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = route;
    document.head.appendChild(link);

    this.prefetched.add(route);
  }

  static prefetchRoutes(routes: string[]) {
    routes.forEach(route => this.prefetchRoute(route));
  }

  static preconnect(domain: string) {
    if (typeof window === 'undefined') return;

    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = domain;
    document.head.appendChild(link);
  }

  static dnsPrefetch(domain: string) {
    if (typeof window === 'undefined') return;

    const link = document.createElement('link');
    link.rel = 'dns-prefetch';
    link.href = domain;
    document.head.appendChild(link);
  }
}

// Virtual scrolling for large lists
interface VirtualScrollProps {
  items: any[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: any, index: number) => ReactNode;
  buffer?: number;
}

export function useVirtualScroll({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  buffer = 5
}: VirtualScrollProps) {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - buffer);
  const visibleEnd = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + buffer
  );

  const visibleItems = items.slice(visibleStart, visibleEnd);
  const totalHeight = items.length * itemHeight;
  const offsetY = visibleStart * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    visibleStart,
    visibleEnd
  };
}

// Turkish content optimization
export class TurkishContentOptimizer {
  private static turkishChars: Record<string, string> = {
    'ç': 'c', 'ğ': 'g', 'ı': 'i', 'İ': 'I', 'ö': 'o', 'ş': 's', 'ü': 'u',
    'Ç': 'C', 'Ğ': 'G', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
  };

  static normalizeForSearch(text: string): string {
    let normalized = text.toLowerCase();
    Object.entries(this.turkishChars).forEach(([turkish, latin]) => {
      normalized = normalized.replace(new RegExp(turkish, 'g'), latin.toLowerCase());
    });
    return normalized;
  }

  static optimizeFont(): string {
    // Return optimized font stack for Turkish content
    return `
      font-family: 
        "Inter", 
        -apple-system, 
        BlinkMacSystemFont, 
        "Segoe UI", 
        "Roboto", 
        "Helvetica Neue", 
        Arial, 
        "Noto Sans", 
        sans-serif, 
        "Apple Color Emoji", 
        "Segoe UI Emoji", 
        "Segoe UI Symbol", 
        "Noto Color Emoji";
    `;
  }

  static getCollator(): Intl.Collator {
    return new Intl.Collator('tr-TR', {
      sensitivity: 'base',
      numeric: true,
      ignorePunctuation: true
    });
  }
}

// Service Worker utilities
export class ServiceWorkerManager {
  private static swRegistration: ServiceWorkerRegistration | null = null;

  static async register(swUrl: string = '/sw.js'): Promise<ServiceWorkerRegistration | null> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker not supported');
      return null;
    }

    try {
      const registration = await navigator.serviceWorker.register(swUrl);
      this.swRegistration = registration;
      
      console.log('Service Worker registered successfully:', registration.scope);
      
      // Check for updates
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New content available, notify user
              this.notifyUpdate();
            }
          });
        }
      });

      return registration;
    } catch (error) {
      console.error('Service Worker registration failed:', error);
      return null;
    }
  }

  private static notifyUpdate() {
    if (window.confirm('Yeni bir sürüm mevcut. Sayfayı yeniden yüklemek istiyor musunuz?')) {
      window.location.reload();
    }
  }

  static async unregister(): Promise<boolean> {
    if (!this.swRegistration) return false;

    try {
      const result = await this.swRegistration.unregister();
      this.swRegistration = null;
      return result;
    } catch (error) {
      console.error('Service Worker unregistration failed:', error);
      return false;
    }
  }
}

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  PerformanceMonitor.initialize();
}

// Export React import
import React, { useState, useCallback } from 'react';