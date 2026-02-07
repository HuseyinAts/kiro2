/**
 * Generic API Hook with Error Handling and Loading States
 * Provides a standardized way to make API calls with automatic error handling
 */

import { useState, useCallback } from 'react';

export interface UseAPIOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  initialData?: T;
}

export interface UseAPIReturn<T, P extends any[]> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: P) => Promise<T>;
  reset: () => void;
}

export function useAPI<T = any, P extends any[] = any[]>(
  apiFunction: (...args: P) => Promise<T>,
  options?: UseAPIOptions<T>,
): UseAPIReturn<T, P> {
  const [data, setData] = useState<T | null>(options?.initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async (...args: P): Promise<T> => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiFunction(...args);
      setData(result);

      if (options?.onSuccess) {
        options.onSuccess(result);
      }

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);

      if (options?.onError) {
        options.onError(err as Error);
      }

      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFunction, options]);

  const reset = useCallback(() => {
    setData(options?.initialData || null);
    setError(null);
    setLoading(false);
  }, [options?.initialData]);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

/**
 * Hook for paginated API calls
 */
export interface UsePaginatedAPIOptions<T> extends UseAPIOptions<T> {
  initialPage?: number;
  pageSize?: number;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export function usePaginatedAPI<T = any>(
  apiFunction: (page: number, pageSize: number) => Promise<PaginatedData<T>>,
  options?: UsePaginatedAPIOptions<PaginatedData<T>>,
) {
  const [page, setPage] = useState(options?.initialPage || 1);
  const pageSize = options?.pageSize || 20;

  const api = useAPI(
    () => apiFunction(page, pageSize),
    options,
  );

  const nextPage = useCallback(() => {
    if (api.data?.hasMore) {
      setPage(prev => prev + 1);
    }
  }, [api.data]);

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage(prev => prev - 1);
    }
  }, [page]);

  const goToPage = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const resetPagination = useCallback(() => {
    setPage(options?.initialPage || 1);
    api.reset();
  }, [api, options?.initialPage]);

  return {
    ...api,
    page,
    pageSize,
    nextPage,
    prevPage,
    goToPage,
    resetPagination,
  };
}

/**
 * Hook for infinite scroll API calls
 */
export function useInfiniteAPI<T = any>(
  apiFunction: (page: number, pageSize: number) => Promise<PaginatedData<T>>,
  options?: UsePaginatedAPIOptions<PaginatedData<T>>,
) {
  const [allItems, setAllItems] = useState<T[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const pageSize = options?.pageSize || 20;

  const api = useAPI(
    async () => {
      const result = await apiFunction(page, pageSize);

      setAllItems(prev => [...prev, ...result.items]);
      setHasMore(result.hasMore);

      return result;
    },
    options,
  );

  const loadMore = useCallback(() => {
    if (hasMore && !api.loading) {
      setPage(prev => prev + 1);
    }
  }, [hasMore, api.loading]);

  const reset = useCallback(() => {
    setAllItems([]);
    setPage(1);
    setHasMore(true);
    api.reset();
  }, [api]);

  return {
    items: allItems,
    loading: api.loading,
    error: api.error,
    hasMore,
    loadMore,
    reset,
  };
}

export default useAPI;
