import { getHealth, getMetrics } from '../api';

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services?: {
    [key: string]: {
      status: string;
      latency?: number;
      error?: string;
    };
  };
}

export interface PerformanceMetrics {
  responseTime: number;
  throughput: number;
  errorRate: number;
  activeConnections: number;
}

class MonitoringService {
  private metricsInterval: NodeJS.Timeout | null = null;
  private healthCheckInterval: NodeJS.Timeout | null = null;
  private performanceObserver: PerformanceObserver | null = null;
  private metrics: Map<string, any> = new Map();

  async checkHealth(): Promise<HealthStatus> {
    try {
      const health = await getHealth();
      return health;
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        services: {
          api: {
            status: 'down',
            error: error instanceof Error ? error.message : 'Unknown error',
          },
        },
      };
    }
  }

  async fetchMetrics(): Promise<string> {
    try {
      const metrics = await getMetrics();
      return metrics;
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      throw error;
    }
  }

  startMonitoring(options?: {
    healthInterval?: number;
    metricsInterval?: number;
    onHealthChange?: (status: HealthStatus) => void;
    onMetricsUpdate?: (metrics: string) => void;
  }) {
    const {
      healthInterval = 30000, // 30 seconds
      metricsInterval = 60000, // 1 minute
      onHealthChange,
      onMetricsUpdate,
    } = options || {};

    // Start health checks
    if (onHealthChange) {
      this.healthCheckInterval = setInterval(async () => {
        const health = await this.checkHealth();
        onHealthChange(health);
      }, healthInterval);
    }

    // Start metrics collection
    if (onMetricsUpdate) {
      this.metricsInterval = setInterval(async () => {
        try {
          const metrics = await this.fetchMetrics();
          onMetricsUpdate(metrics);
        } catch (error) {
          console.error('Metrics update failed:', error);
        }
      }, metricsInterval);
    }

    // Start browser performance monitoring
    this.startPerformanceMonitoring();
  }

  stopMonitoring() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }

    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }

    this.stopPerformanceMonitoring();
  }

  private startPerformanceMonitoring() {
    if (!window.PerformanceObserver) {
      console.warn('PerformanceObserver not supported');
      return;
    }

    try {
      this.performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.processPerformanceEntry(entry);
        }
      });

      this.performanceObserver.observe({
        entryTypes: ['navigation', 'resource', 'measure'],
      });
    } catch (error) {
      console.error('Failed to start performance monitoring:', error);
    }
  }

  private stopPerformanceMonitoring() {
    if (this.performanceObserver) {
      this.performanceObserver.disconnect();
      this.performanceObserver = null;
    }
  }

  private processPerformanceEntry(entry: PerformanceEntry) {
    if (entry.entryType === 'navigation') {
      const navEntry = entry as PerformanceNavigationTiming;
      this.metrics.set('pageLoadTime', navEntry.loadEventEnd - navEntry.fetchStart);
      this.metrics.set('domContentLoadedTime', navEntry.domContentLoadedEventEnd - navEntry.fetchStart);
    } else if (entry.entryType === 'resource') {
      const resourceEntry = entry as PerformanceResourceTiming;
      if (resourceEntry.name.includes('/api/')) {
        const duration = resourceEntry.duration;
        const apiCallMetrics = this.metrics.get('apiCalls') || [];
        apiCallMetrics.push({
          url: resourceEntry.name,
          duration,
          timestamp: Date.now(),
        });
        this.metrics.set('apiCalls', apiCallMetrics);
      }
    }
  }

  getClientMetrics(): PerformanceMetrics {
    const apiCalls = this.metrics.get('apiCalls') || [];
    const recentCalls = apiCalls.filter((call: any) =>
      Date.now() - call.timestamp < 60000, // Last minute
    );

    const avgResponseTime = recentCalls.length > 0
      ? recentCalls.reduce((sum: number, call: any) => sum + call.duration, 0) / recentCalls.length
      : 0;

    const errorCalls = recentCalls.filter((call: any) => call.error);
    const errorRate = recentCalls.length > 0
      ? (errorCalls.length / recentCalls.length) * 100
      : 0;

    return {
      responseTime: Math.round(avgResponseTime),
      throughput: recentCalls.length,
      errorRate: Math.round(errorRate * 100) / 100,
      activeConnections: navigator.onLine ? 1 : 0,
    };
  }

  trackApiCall(url: string, duration: number, error?: boolean) {
    const apiCalls = this.metrics.get('apiCalls') || [];
    apiCalls.push({
      url,
      duration,
      error,
      timestamp: Date.now(),
    });
    this.metrics.set('apiCalls', apiCalls);

    // Keep only last 1000 calls to prevent memory issues
    if (apiCalls.length > 1000) {
      apiCalls.shift();
    }
  }

  trackUserAction(action: string, metadata?: any) {
    const userActions = this.metrics.get('userActions') || [];
    userActions.push({
      action,
      metadata,
      timestamp: Date.now(),
    });
    this.metrics.set('userActions', userActions);

    // Keep only last 500 actions
    if (userActions.length > 500) {
      userActions.shift();
    }
  }

  getMetricsSummary() {
    const clientMetrics = this.getClientMetrics();
    const pageLoadTime = this.metrics.get('pageLoadTime') || 0;
    const userActions = this.metrics.get('userActions') || [];

    return {
      performance: clientMetrics,
      pageLoadTime,
      recentActions: userActions.slice(-10), // Last 10 actions
      timestamp: new Date().toISOString(),
    };
  }

  clearMetrics() {
    this.metrics.clear();
  }
}

export default new MonitoringService();