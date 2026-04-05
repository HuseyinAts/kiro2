/**
 * React Query Configuration
 *
 * Global configuration for React Query (TanStack Query)
 * Defines default behaviors, caching strategies, and retry logic
 *
 * @see https://tanstack.com/query/latest/docs/react/guides/important-defaults
 */

import { QueryClient, DefaultOptions } from 'react-query';

// Default query options
const defaultQueryOptions: DefaultOptions = {
  queries: {
    // Stale time: How long data is considered fresh (default: 0)
    // Set to 5 minutes for most queries
    staleTime: 1000 * 60 * 5, // 5 minutes

    // Cache time: How long inactive data stays in memory (default: 5 minutes)
    // Keep cached data for 10 minutes
    cacheTime: 1000 * 60 * 10, // 10 minutes

    // Retry failed queries 3 times with exponential backoff
    retry: (failureCount, error: any) => {
      // Don't retry on 404 or 401
      if (error?.response?.status === 404 || error?.response?.status === 401) {
        return false;
      }
      return failureCount < 3;
    },

    // Retry delay with exponential backoff
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

    // Refetch on window focus (useful for keeping data fresh)
    refetchOnWindowFocus: true,

    // Refetch on reconnect (useful for offline scenarios)
    refetchOnReconnect: true,

    // Don't refetch on mount if data is still fresh
    refetchOnMount: true,

    // Keep previous data while fetching new data (better UX)
    keepPreviousData: true,

    // Suspense mode (set to false by default, enable per-query if needed)
    suspense: false,

    // Use error boundary (set to false by default, enable per-query if needed)
    useErrorBoundary: false,
  },

  mutations: {
    // Retry mutations once
    retry: 1,

    // Use error boundary for mutations
    useErrorBoundary: false,

    // On error, automatically rollback optimistic updates
    onError: (error, _variables, _context: any) => {
      // This will be overridden by individual mutation handlers
      console.error('Mutation error:', error);
    },
  },
};

// Create query client with default options
export const queryClient = new QueryClient({
  defaultOptions: defaultQueryOptions,
});

/**
 * Query configuration presets for different data types
 */
export const queryConfig = {
  // Frequently changing data (e.g., live stats, real-time data)
  realtime: {
    staleTime: 0,
    cacheTime: 1000 * 60, // 1 minute
    refetchInterval: 1000 * 30, // Refetch every 30 seconds
    refetchOnWindowFocus: true,
  },

  // Moderately changing data (e.g., user profile, dashboard stats)
  moderate: {
    staleTime: 1000 * 60 * 5, // 5 minutes
    cacheTime: 1000 * 60 * 10, // 10 minutes
    refetchOnWindowFocus: true,
  },

  // Rarely changing data (e.g., content, static lists)
  static: {
    staleTime: 1000 * 60 * 30, // 30 minutes
    cacheTime: 1000 * 60 * 60, // 1 hour
    refetchOnWindowFocus: false,
  },

  // Infinite scroll / pagination
  infinite: {
    staleTime: 1000 * 60 * 5,
    cacheTime: 1000 * 60 * 10,
    keepPreviousData: true,
    refetchOnWindowFocus: false,
  },

  // Session-specific data (cleared on logout)
  session: {
    staleTime: 1000 * 60 * 5,
    cacheTime: 1000 * 60 * 10,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  },
};

/**
 * Error handler for failed queries
 */
export const onQueryError = (error: unknown) => {
  const err = error as any;
  console.error('Query error:', err);

  // Handle specific error codes
  if (err?.response?.status === 401) {
    // Redirect to login or refresh token
    console.warn('Unauthorized - redirecting to login');
  } else if (err?.response?.status === 403) {
    console.warn('Forbidden - insufficient permissions');
  } else if (err?.response?.status === 500) {
    console.error('Server error');
  }
};

/**
 * Success handler for mutations
 */
export const onMutationSuccess = () => {
  // Show success toast or notification
};

/**
 * Error handler for mutations
 */
export const onMutationError = (error: unknown) => {
  const err = error as any;
  console.error('Mutation error:', err);

  // Show error toast or notification
};

export default queryClient;
