/**
 * React Hook for Performance Monitoring
 * Tracks LLM pool, vector store, cache, and RAG pipeline metrics
 *
 * Features:
 * - Real-time performance metrics
 * - Auto-refresh capability
 * - Cache invalidation controls
 * - TypeScript type safety
 */

import { useState, useEffect, useCallback } from 'react';

import {
  getPerformanceMetrics,
  getLLMPoolStats,
  getVectorStoreStats,
  getCacheStats,
  getRAGPipelineStats,
  clearCacheByTag,
  PerformanceMetrics,
} from '../api';

// ==================== PERFORMANCE MONITOR HOOK ====================

export interface UsePerformanceMonitorResult {
  metrics: PerformanceMetrics | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  clearCache: (tag: string) => Promise<void>;
}

export function usePerformanceMonitor(autoRefresh: boolean = false, refreshInterval: number = 10000): UsePerformanceMonitorResult {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getPerformanceMetrics();
      setMetrics(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearCache = useCallback(async (tag: string) => {
    try {
      await clearCacheByTag(tag);
      await refresh(); // Refresh metrics after clearing cache
    } catch (err) {
      setError(err as Error);
    }
  }, [refresh]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refresh, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refresh]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    metrics,
    isLoading,
    error,
    refresh,
    clearCache,
  };
}

// ==================== LLM POOL STATS HOOK ====================

export interface LLMPoolStats {
  total_requests: number;
  active_connections: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
  errors: number;
}

export interface UseLLMPoolStatsResult {
  stats: LLMPoolStats | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useLLMPoolStats(autoRefresh: boolean = false, refreshInterval: number = 5000): UseLLMPoolStatsResult {
  const [stats, setStats] = useState<LLMPoolStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getLLMPoolStats();
      setStats(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refresh, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refresh]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    stats,
    isLoading,
    error,
    refresh,
  };
}

// ==================== VECTOR STORE STATS HOOK ====================

export interface VectorStoreStats {
  total_searches: number;
  avg_search_time_ms: number;
  cache_hits: number;
  cache_misses: number;
  cache_hit_rate: number;
  index_size: number;
  hnsw_enabled: boolean;
}

export interface UseVectorStoreStatsResult {
  stats: VectorStoreStats | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useVectorStoreStats(autoRefresh: boolean = false, refreshInterval: number = 5000): UseVectorStoreStatsResult {
  const [stats, setStats] = useState<VectorStoreStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getVectorStoreStats();
      setStats(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refresh, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refresh]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    stats,
    isLoading,
    error,
    refresh,
  };
}

// ==================== CACHE STATS HOOK ====================

export interface CacheStats {
  l1_hits: number;
  l2_hits: number;
  misses: number;
  hit_ratio: number;
  total_keys: number;
  l1_size: number;
  l2_size: number;
  evictions: number;
}

export interface UseCacheStatsResult {
  stats: CacheStats | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
  clearByTag: (tag: string) => Promise<void>;
}

export function useCacheStats(autoRefresh: boolean = false, refreshInterval: number = 5000): UseCacheStatsResult {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getCacheStats();
      setStats(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearByTag = useCallback(async (tag: string) => {
    try {
      await clearCacheByTag(tag);
      await refresh();
    } catch (err) {
      setError(err as Error);
    }
  }, [refresh]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refresh, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refresh]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    stats,
    isLoading,
    error,
    refresh,
    clearByTag,
  };
}

// ==================== RAG PIPELINE STATS HOOK ====================

export interface RAGPipelineStats {
  total_queries: number;
  avg_query_time_ms: number;
  parallel_speedup: number;
  avg_documents_retrieved: number;
  reranking_enabled: boolean;
  query_expansion_enabled: boolean;
}

export interface UseRAGPipelineStatsResult {
  stats: RAGPipelineStats | null;
  isLoading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useRAGPipelineStats(autoRefresh: boolean = false, refreshInterval: number = 5000): UseRAGPipelineStatsResult {
  const [stats, setStats] = useState<RAGPipelineStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getRAGPipelineStats();
      setStats(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refresh, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refresh]);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    stats,
    isLoading,
    error,
    refresh,
  };
}
