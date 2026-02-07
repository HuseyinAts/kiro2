import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * AsyncState - Asenkron işlemlerin durumu
 */
export interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  isSuccess: boolean;
  isError: boolean;
}

/**
 * UseAsyncOptions - useAsync hook seçenekleri
 * Generic T type for type-safe onSuccess callback
 */
export interface UseAsyncOptions<T = unknown> {
  /**
   * Component unmount olduğunda işlemi iptal et
   */
  cancelOnUnmount?: boolean;

  /**
   * Otomatik olarak çalıştır (mount olduğunda)
   */
  immediate?: boolean;

  /**
   * Hata durumunda retry sayısı
   */
  retryCount?: number;

  /**
   * Retry arasındaki bekleme süresi (ms)
   */
  retryDelay?: number;

  /**
   * Başarılı sonuç için cache süresi (ms)
   */
  cacheTime?: number;

  /**
   * Başarılı callback - type-safe with T
   */
  onSuccess?: (data: T) => void;

  /**
   * Hata callback
   */
  onError?: (error: Error) => void;
}

/**
 * useAsync Hook
 *
 * API çağrıları ve diğer asenkron işlemler için kapsamlı state yönetimi sağlar.
 *
 * Özellikler:
 * - Loading, error, success state yönetimi
 * - Otomatik retry mekanizması
 * - Request cancellation
 * - Result caching
 * - Success/error callbacks
 *
 * @example
 * const { execute, data, isLoading, error } = useAsync(fetchUserData);
 *
 * // Kullanım
 * useEffect(() => {
 *   execute(userId);
 * }, [userId]);
 */
export function useAsync<T, Args extends unknown[] = []>(
  asyncFunction: (...args: Args) => Promise<T>,
  options: UseAsyncOptions<T> = {},
) {
  const {
    cancelOnUnmount = true,
    immediate = false,
    retryCount = 0,
    retryDelay = 1000,
    cacheTime = 0,
    onSuccess,
    onError,
  } = options;

  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    isLoading: false,
    isSuccess: false,
    isError: false,
  });

  const isMountedRef = useRef(true);
  const cacheRef = useRef<{ data: T; timestamp: number } | null>(null);
  const retryCountRef = useRef(0);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const execute = useCallback(
    async (...args: Args): Promise<T | undefined> => {
      // Cache kontrolü
      if (cacheRef.current && cacheTime > 0) {
        const cacheAge = Date.now() - cacheRef.current.timestamp;
        if (cacheAge < cacheTime) {
          setState({
            data: cacheRef.current.data,
            error: null,
            isLoading: false,
            isSuccess: true,
            isError: false,
          });
          return cacheRef.current.data;
        }
      }

      if (!isMountedRef.current && cancelOnUnmount) {return;}

      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
        isError: false,
      }));

      try {
        const data = await asyncFunction(...args);

        if (!isMountedRef.current && cancelOnUnmount) {return;}

        // Cache kaydet
        if (cacheTime > 0) {
          cacheRef.current = {
            data,
            timestamp: Date.now(),
          };
        }

        setState({
          data,
          error: null,
          isLoading: false,
          isSuccess: true,
          isError: false,
        });

        retryCountRef.current = 0;
        onSuccess?.(data);

        return data;
      } catch (error) {
        if (!isMountedRef.current && cancelOnUnmount) {return;}

        const err = error instanceof Error ? error : new Error(String(error));

        // Retry logic
        if (retryCountRef.current < retryCount) {
          retryCountRef.current++;
          await new Promise((resolve) => setTimeout(resolve, retryDelay));
          return execute(...args);
        }

        setState({
          data: null,
          error: err,
          isLoading: false,
          isSuccess: false,
          isError: true,
        });

        retryCountRef.current = 0;
        onError?.(err);

        return undefined;
      }
    },
    [asyncFunction, cancelOnUnmount, cacheTime, retryCount, retryDelay, onSuccess, onError],
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      error: null,
      isLoading: false,
      isSuccess: false,
      isError: false,
    });
    cacheRef.current = null;
    retryCountRef.current = 0;
  }, []);

  // Immediate execution
  useEffect(() => {
    if (immediate) {
      // Cast to satisfy TypeScript when no args are needed
      (execute as () => Promise<T | undefined>)();
    }
  }, [immediate, execute]);

  return {
    ...state,
    execute,
    reset,
  };
}

/**
 * useFetch Hook
 *
 * Fetch API için özelleştirilmiş useAsync hook'u.
 *
 * @example
 * const { data, isLoading, error, refetch } = useFetch<User>(
 *   '/api/users/123',
 *   { method: 'GET' }
 * );
 */
export function useFetch<T>(
  url: string | null,
  options?: RequestInit & UseAsyncOptions<T>,
) {
  const { immediate = true, ...asyncOptions } = options || {};

  const fetchData = useCallback(async (): Promise<T> => {
    if (!url) {throw new Error('URL is required');}

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }, [url, options]);

  const asyncState = useAsync<T>(fetchData, {
    ...asyncOptions,
    immediate: immediate && !!url,
  });

  return {
    ...asyncState,
    refetch: asyncState.execute,
  };
}

/**
 * useMutation Hook
 *
 * POST, PUT, DELETE gibi mutation işlemleri için hook.
 *
 * @example
 * const { mutate, isLoading, error } = useMutation(
 *   (data) => fetch('/api/users', {
 *     method: 'POST',
 *     body: JSON.stringify(data)
 *   })
 * );
 *
 * // Kullanım
 * await mutate({ name: 'John' });
 */
export function useMutation<T, Args extends unknown[] = []>(
  mutationFn: (...args: Args) => Promise<T>,
  options?: UseAsyncOptions<T>,
) {
  const asyncState = useAsync<T, Args>(mutationFn, {
    ...options,
    immediate: false, // Mutations are never immediate
  });

  return {
    ...asyncState,
    mutate: asyncState.execute,
    mutateAsync: asyncState.execute,
  };
}

/**
 * useLoadingState Hook
 *
 * Basit loading state yönetimi için minimal hook.
 *
 * @example
 * const { isLoading, startLoading, stopLoading, withLoading } = useLoadingState();
 *
 * // Manuel kullanım
 * startLoading();
 * await doSomething();
 * stopLoading();
 *
 * // Wrapper kullanım
 * await withLoading(async () => {
 *   await doSomething();
 * });
 */
export function useLoadingState(initialState = false) {
  const [isLoading, setIsLoading] = useState(initialState);
  const [error, setError] = useState<Error | null>(null);

  const startLoading = useCallback(() => {
    setIsLoading(true);
    setError(null);
  }, []);

  const stopLoading = useCallback(() => {
    setIsLoading(false);
  }, []);

  const setLoadingError = useCallback((err: Error | string) => {
    setError(err instanceof Error ? err : new Error(err));
    setIsLoading(false);
  }, []);

  const withLoading = useCallback(
    async <T,>(fn: () => Promise<T>): Promise<T | undefined> => {
      try {
        startLoading();
        const result = await fn();
        stopLoading();
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setLoadingError(error);
        return undefined;
      }
    },
    [startLoading, stopLoading, setLoadingError],
  );

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
  }, []);

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setError: setLoadingError,
    withLoading,
    reset,
  };
}

/**
 * useDebounce Hook
 *
 * Değer değişikliklerini geciktirerek API çağrılarını optimize eder.
 *
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearchTerm = useDebounce(searchTerm, 500);
 *
 * useEffect(() => {
 *   if (debouncedSearchTerm) {
 *     searchAPI(debouncedSearchTerm);
 *   }
 * }, [debouncedSearchTerm]);
 */
export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * useThrottle Hook
 *
 * Fonksiyon çağrılarını belirli aralıklarla sınırlandırır.
 *
 * @example
 * const handleScroll = useThrottle(() => {
 *   console.log('Scrolling...');
 * }, 200);
 */
export function useThrottle<T extends (...args: unknown[]) => unknown>(
  callback: T,
  delay: number = 500,
): T {
  const lastRun = useRef(Date.now());
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(
    ((...args: Parameters<T>) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRun.current;

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      if (timeSinceLastRun >= delay) {
        callback(...args);
        lastRun.current = now;
      } else {
        timeoutRef.current = setTimeout(
          () => {
            callback(...args);
            lastRun.current = Date.now();
          },
          delay - timeSinceLastRun,
        );
      }
    }) as T,
    [callback, delay],
  );
}

/**
 * useApiState Hook
 *
 * API çağrıları için önceden yapılandırılmış state yönetimi.
 * Backend API'sine uygun şekilde yapılandırılmış.
 *
 * @example
 * const api = useApiState();
 *
 * const fetchUsers = async () => {
 *   await api.execute(async () => {
 *     const response = await fetch('/api/users');
 *     return response.json();
 *   });
 * };
 */
export function useApiState<T>() {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const execute = useCallback(async (apiCall: () => Promise<T>) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiCall();
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bir hata oluştu';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    data,
    error,
    isLoading,
    execute,
    reset,
    setData,
    setError,
  };
}

export default useAsync;
