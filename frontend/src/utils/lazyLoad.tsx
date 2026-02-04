/**
 * Lazy Loading Utilities - Task 58.1
 * REQ-48.93-48.95: Frontend performance optimization
 *
 * Features:
 * - Route-based code splitting
 * - Component lazy loading
 * - Retry logic for failed imports
 * - Loading fallback components
 */
import React, { ComponentType, LazyExoticComponent } from 'react';

interface RetryOptions {
  maxRetries?: number;
  delay?: number;
}

/**
 * Lazy load a component with retry logic
 *
 * @param importFunc - Dynamic import function
 * @param options - Retry configuration
 * @returns Lazy-loaded component
 *
 * @example
 * const Dashboard = lazyWithRetry(() => import('./pages/Dashboard'));
 */
export function lazyWithRetry<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  options: RetryOptions = {}
): LazyExoticComponent<T> {
  const { maxRetries = 3, delay = 1000 } = options;

  const retry = async (fn: () => Promise<any>, retriesLeft = maxRetries): Promise<any> => {
    try {
      return await fn();
    } catch (error) {
      if (retriesLeft <= 0) {
        throw error;
      }

      console.warn(`Import failed, retrying... (${retriesLeft} attempts left)`);

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));

      return retry(fn, retriesLeft - 1);
    }
  };

  return React.lazy(() => retry(importFunc));
}

/**
 * Preload a lazy component
 * Useful for prefetching components before they're needed
 *
 * @param lazyComponent - Lazy component to preload
 *
 * @example
 * const Dashboard = lazyWithRetry(() => import('./pages/Dashboard'));
 * preloadComponent(Dashboard); // Preload on hover or beforehand
 */
export function preloadComponent<T extends ComponentType<any>>(
  lazyComponent: LazyExoticComponent<T>
): void {
  // Access the _payload to trigger the import
  const component = lazyComponent as any;
  if (component._payload && component._payload._result === null) {
    component._payload._init(component._payload);
  }
}

/**
 * Create a lazy component with custom loading fallback
 *
 * @param importFunc - Dynamic import function
 * @param fallback - Custom loading component
 * @returns Lazy component with Suspense wrapper
 *
 * @example
 * const Dashboard = lazyWithFallback(
 *   () => import('./pages/Dashboard'),
 *   <div>Loading Dashboard...</div>
 * );
 */
export function lazyWithFallback<T extends ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  fallback: React.ReactNode
) {
  const LazyComponent = lazyWithRetry(importFunc);

  return (props: any) => (
    <React.Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </React.Suspense>
  );
}

/**
 * Batch preload multiple components
 * Useful for preloading a set of related components
 *
 * @param components - Array of lazy components
 *
 * @example
 * batchPreload([Dashboard, Profile, Settings]);
 */
export function batchPreload(components: LazyExoticComponent<any>[]): void {
  components.forEach(component => {
    try {
      preloadComponent(component);
    } catch (error) {
      console.error('Failed to preload component:', error);
    }
  });
}

/**
 * Route-based preloading on hover
 * Attach to navigation links to preload destination
 *
 * @param lazyComponent - Component to preload
 * @returns Mouse event handler
 *
 * @example
 * <Link to="/dashboard" onMouseEnter={createPreloadHandler(Dashboard)}>
 *   Dashboard
 * </Link>
 */
export function createPreloadHandler<T extends ComponentType<any>>(
  lazyComponent: LazyExoticComponent<T>
) {
  let hasPreloaded = false;

  return () => {
    if (!hasPreloaded) {
      preloadComponent(lazyComponent);
      hasPreloaded = true;
    }
  };
}

/**
 * Check if browser supports dynamic imports
 * Fallback for older browsers
 */
export function supportsDynamicImport(): boolean {
  try {
    new Function('import("")');
    return true;
  } catch {
    return false;
  }
}

/**
 * Loading fallback component factory
 * Creates consistent loading components
 */
export const LoadingFallbacks = {
  // Page-level loading
  page: (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Yükleniyor...</p>
      </div>
    </div>
  ),

  // Component-level loading
  component: (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
    </div>
  ),

  // Inline loading
  inline: (
    <span className="inline-flex items-center">
      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
      Yükleniyor...
    </span>
  ),

  // Dashboard loading
  dashboard: (
    <div className="p-6">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
        <div className="grid grid-cols-3 gap-4">
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="h-24 bg-gray-200 rounded"></div>
        </div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    </div>
  )
};

/**
 * Route configuration with lazy loading
 * Template for route-based code splitting
 */
export interface LazyRoute {
  path: string;
  component: LazyExoticComponent<any>;
  preload?: boolean;
}

/**
 * Create lazy routes with automatic preloading
 *
 * @param routes - Array of route configurations
 * @returns Routes ready for React Router
 *
 * @example
 * const routes = createLazyRoutes([
 *   { path: '/dashboard', component: Dashboard, preload: true },
 *   { path: '/profile', component: Profile }
 * ]);
 */
export function createLazyRoutes(routes: LazyRoute[]) {
  // Preload routes marked for preloading
  const preloadableRoutes = routes.filter(r => r.preload);
  if (preloadableRoutes.length > 0) {
    // Preload after initial render
    setTimeout(() => {
      batchPreload(preloadableRoutes.map(r => r.component));
    }, 2000);
  }

  return routes;
}
