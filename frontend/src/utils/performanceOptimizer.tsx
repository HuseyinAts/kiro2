/**
 * Frontend Performance Optimizer
 * Lazy loading, code splitting ve performans optimizasyonları
 */

import React, { lazy, ComponentType, ReactElement, Suspense } from 'react';
import { QueryClient } from 'react-query';

// Performance metrikleri
interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  componentName: string;
  timestamp: number;
}

class PerformanceTracker {
  private metrics: PerformanceMetrics[] = [];
  private observers: Map<string, PerformanceObserver> = new Map();

  // Component load time'ını ölç
  trackComponentLoad(componentName: string, startTime: number): void {
    const loadTime = performance.now() - startTime;
    
    this.metrics.push({
      loadTime,
      renderTime: 0,
      componentName,
      timestamp: Date.now()
    });

    // Yavaş yüklenen component'leri logla
    if (loadTime > 1000) {
      console.warn(`Yavaş component yüklendi: ${componentName} - ${loadTime.toFixed(2)}ms`);
    }
  }

  // Render performance'ını ölç
  trackRenderTime(componentName: string, renderTime: number): void {
    const existingMetric = this.metrics.find(
      m => m.componentName === componentName && m.renderTime === 0
    );

    if (existingMetric) {
      existingMetric.renderTime = renderTime;
    }

    // Yavaş render'ları logla
    if (renderTime > 100) {
      console.warn(`Yavaş render: ${componentName} - ${renderTime.toFixed(2)}ms`);
    }
  }

  // Web Vitals metrikleri
  initWebVitals(): void {
    // Largest Contentful Paint (LCP)
    this.observeMetric('largest-contentful-paint', (entries) => {
      const lcp = entries[entries.length - 1];
      console.log('LCP:', lcp.startTime);
    });

    // First Input Delay (FID)
    this.observeMetric('first-input', (entries) => {
      const fid = entries[0];
      console.log('FID:', (fid as any).processingStart - fid.startTime);
    });

    // Cumulative Layout Shift (CLS)
    this.observeMetric('layout-shift', (entries) => {
      let cls = 0;
      for (const entry of entries) {
        if (!(entry as any).hadRecentInput) {
          cls += (entry as any).value;
        }
      }
      console.log('CLS:', cls);
    });
  }

  private observeMetric(type: string, callback: (entries: PerformanceEntry[]) => void): void {
    try {
      const observer = new PerformanceObserver((list) => {
        callback(list.getEntries());
      });
      
      observer.observe({ type, buffered: true });
      this.observers.set(type, observer);
    } catch (error) {
      console.warn(`Performance observer not supported: ${type}`);
    }
  }

  getMetrics(): PerformanceMetrics[] {
    return [...this.metrics];
  }

  clearMetrics(): void {
    this.metrics = [];
  }

  disconnect(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
  }
}

// Global performance tracker
export const performanceTracker = new PerformanceTracker();

// Lazy loading wrapper with performance tracking
export function createLazyComponent<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  componentName: string
): ComponentType<T extends ComponentType<infer P> ? P : never> {
  const startTime = performance.now();
  
  const LazyComponent = lazy(async () => {
    try {
      const module = await importFunc();
      performanceTracker.trackComponentLoad(componentName, startTime);
      return module;
    } catch (error) {
      console.error(`Component yükleme hatası: ${componentName}`, error);
      throw error;
    }
  });

  // Display name set et
  (LazyComponent as any).displayName = `Lazy(${componentName})`;

  return LazyComponent as any;
}

// Suspense wrapper with loading indicator
export function withSuspense<P extends object>(
  Component: ComponentType<P>,
  fallback?: ReactElement
): ComponentType<P> {
  const SuspenseWrapper = (props: P) => (
    <Suspense fallback={fallback || <div className="loading-spinner">Yükleniyor...</div>}>
      <Component {...props} />
    </Suspense>
  );

  SuspenseWrapper.displayName = `withSuspense(${Component.displayName || Component.name})`;
  return SuspenseWrapper;
}

// Image lazy loading
export class ImageLazyLoader {
  private observer: IntersectionObserver | null = null;
  private loadedImages: Set<string> = new Set();

  init(): void {
    if (!('IntersectionObserver' in window)) {
      console.warn('IntersectionObserver not supported');
      return;
    }

    this.observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            this.loadImage(img);
            this.observer?.unobserve(img);
          }
        });
      },
      {
        rootMargin: '50px 0px', // 50px önce yüklemeye başla
        threshold: 0.1
      }
    );
  }

  observe(img: HTMLImageElement): void {
    if (this.observer && !this.loadedImages.has(img.src)) {
      this.observer.observe(img);
    }
  }

  private loadImage(img: HTMLImageElement): void {
    const dataSrc = img.getAttribute('data-src');
    if (dataSrc && !this.loadedImages.has(dataSrc)) {
      img.src = dataSrc;
      img.classList.add('loaded');
      this.loadedImages.add(dataSrc);
    }
  }

  disconnect(): void {
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }
  }
}

// Global image lazy loader
export const imageLazyLoader = new ImageLazyLoader();

// React Query optimizasyonları
export const createOptimizedQueryClient = (): QueryClient => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Cache süresi: 5 dakika
        staleTime: 5 * 60 * 1000,
        // Background refetch: 10 dakika
        cacheTime: 10 * 60 * 1000,
        // Retry stratejisi
        retry: (failureCount, error: any) => {
          // 4xx hatalarında retry yapma
          if (error?.response?.status >= 400 && error?.response?.status < 500) {
            return false;
          }
          // Maksimum 3 retry
          return failureCount < 3;
        },
        // Retry delay
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        // Background refetch
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        refetchOnMount: true
      },
      mutations: {
        // Mutation retry
        retry: 1,
        retryDelay: 1000
      }
    }
  });
};

// Bundle size analyzer
export class BundleAnalyzer {
  private chunks: Map<string, number> = new Map();

  trackChunkLoad(chunkName: string, size: number): void {
    this.chunks.set(chunkName, size);
    console.log(`Chunk yüklendi: ${chunkName} (${(size / 1024).toFixed(2)} KB)`);
  }

  getTotalSize(): number {
    return Array.from(this.chunks.values()).reduce((total, size) => total + size, 0);
  }

  getLargestChunks(limit: number = 5): Array<{ name: string; size: number }> {
    return Array.from(this.chunks.entries())
      .map(([name, size]) => ({ name, size }))
      .sort((a, b) => b.size - a.size)
      .slice(0, limit);
  }

  getReport(): string {
    const totalSize = this.getTotalSize();
    const largestChunks = this.getLargestChunks();

    return `
Bundle Analiz Raporu:
- Toplam boyut: ${(totalSize / 1024).toFixed(2)} KB
- Chunk sayısı: ${this.chunks.size}
- En büyük chunk'lar:
${largestChunks.map(chunk => 
  `  - ${chunk.name}: ${(chunk.size / 1024).toFixed(2)} KB`
).join('\n')}
    `.trim();
  }
}

// Global bundle analyzer
export const bundleAnalyzer = new BundleAnalyzer();

// Memory usage tracker
export class MemoryTracker {
  private measurements: Array<{ timestamp: number; used: number; total: number }> = [];

  startTracking(interval: number = 30000): void {
    const track = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        this.measurements.push({
          timestamp: Date.now(),
          used: memory.usedJSHeapSize,
          total: memory.totalJSHeapSize
        });

        // Son 100 ölçümü tut
        if (this.measurements.length > 100) {
          this.measurements = this.measurements.slice(-100);
        }

        // Memory leak uyarısı
        if (this.measurements.length > 10) {
          const recent = this.measurements.slice(-10);
          const trend = recent[recent.length - 1].used - recent[0].used;
          
          if (trend > 10 * 1024 * 1024) { // 10MB artış
            console.warn('Potansiyel memory leak tespit edildi');
          }
        }
      }
    };

    // İlk ölçüm
    track();
    
    // Periyodik ölçüm
    setInterval(track, interval);
  }

  getCurrentUsage(): { used: number; total: number } | null {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize
      };
    }
    return null;
  }

  getUsageHistory(): Array<{ timestamp: number; used: number; total: number }> {
    return [...this.measurements];
  }
}

// Global memory tracker
export const memoryTracker = new MemoryTracker();

// Performance optimization hooks
export const usePerformanceOptimization = () => {
  // Component mount/unmount tracking
  const trackComponentLifecycle = (componentName: string) => {
    const startTime = performance.now();
    
    return () => {
      const renderTime = performance.now() - startTime;
      performanceTracker.trackRenderTime(componentName, renderTime);
    };
  };

  // Debounced function
  const debounce = <T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): ((...args: Parameters<T>) => void) => {
    let timeoutId: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func(...args), delay);
    };
  };

  // Throttled function
  const throttle = <T extends (...args: any[]) => any>(
    func: T,
    delay: number
  ): ((...args: Parameters<T>) => void) => {
    let lastCall = 0;
    
    return (...args: Parameters<T>) => {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        func(...args);
      }
    };
  };

  return {
    trackComponentLifecycle,
    debounce,
    throttle
  };
};

// Initialize performance tracking
export const initializePerformanceTracking = (): void => {
  // Web Vitals tracking
  performanceTracker.initWebVitals();
  
  // Image lazy loading
  imageLazyLoader.init();
  
  // Memory tracking
  memoryTracker.startTracking();
  
  // Bundle size tracking (development only)
  if (process.env.NODE_ENV === 'development') {
    console.log('Performance tracking initialized');
  }
};

// Cleanup function
export const cleanupPerformanceTracking = (): void => {
  performanceTracker.disconnect();
  imageLazyLoader.disconnect();
  performanceTracker.clearMetrics();
};

// Performance report
export const getPerformanceReport = (): string => {
  const metrics = performanceTracker.getMetrics();
  const memoryUsage = memoryTracker.getCurrentUsage();
  const bundleReport = bundleAnalyzer.getReport();

  const avgLoadTime = metrics.length > 0 
    ? metrics.reduce((sum, m) => sum + m.loadTime, 0) / metrics.length 
    : 0;

  const avgRenderTime = metrics.filter(m => m.renderTime > 0).length > 0
    ? metrics.filter(m => m.renderTime > 0).reduce((sum, m) => sum + m.renderTime, 0) / metrics.filter(m => m.renderTime > 0).length
    : 0;

  return `
Performans Raporu:
- Ortalama component yükleme süresi: ${avgLoadTime.toFixed(2)}ms
- Ortalama render süresi: ${avgRenderTime.toFixed(2)}ms
- Toplam component sayısı: ${metrics.length}
- Memory kullanımı: ${memoryUsage ? `${(memoryUsage.used / 1024 / 1024).toFixed(2)} MB` : 'N/A'}

${bundleReport}
  `.trim();
};