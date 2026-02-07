/**
 * Zustand Store Helpers
 *
 * Reduces boilerplate for async actions in Zustand stores.
 * Provides standardized error handling, loading states, and type-safe wrappers.
 *
 * Usage:
 * ```typescript
 * import { createAsyncAction, withLoadingState } from '../utils/storeHelpers'
 *
 * const myAction = createAsyncAction(
 *   async (params, set, get) => {
 *     const result = await api.call(params)
 *     set({ data: result })
 *     return result
 *   },
 *   { errorMessage: 'Operation failed' }
 * )
 * ```
 */

import { getErrorMessage } from '../types';

// Type definitions for Zustand store helpers
type SetState<S> = (
  partial: S | Partial<S> | ((state: S) => S | Partial<S>),
  replace?: boolean
) => void

type GetState<S> = () => S

/**
 * Standard loading state interface that stores can implement
 */
export interface LoadingState {
  loading: boolean
  error: string | null
}

/**
 * Configuration for async action behavior
 */
export interface AsyncActionConfig {
  /** Error message to show if no message is extracted from error */
  errorMessage?: string
  /** Whether to set loading state during execution (default: true) */
  setLoading?: boolean
  /** Whether to clear error before starting (default: true) */
  clearError?: boolean
  /** Custom error handler */
  onError?: (error: unknown) => void
}

/**
 * Creates a wrapped async action with standardized error handling
 *
 * @param action - The async function to wrap
 * @param config - Configuration for error handling
 * @returns Wrapped async function with loading/error state management
 */
export function createAsyncAction<
  S extends LoadingState,
  Args extends unknown[],
  R
>(
  action: (set: SetState<S>, get: GetState<S>, ...args: Args) => Promise<R>,
  config: AsyncActionConfig = {},
): (set: SetState<S>, get: GetState<S>) => (...args: Args) => Promise<R | undefined> {
  const {
    errorMessage = 'Bir hata oluştu',
    setLoading = true,
    clearError = true,
    onError,
  } = config;

  return (set: SetState<S>, get: GetState<S>) =>
    async (...args: Args): Promise<R | undefined> => {
      try {
        if (setLoading || clearError) {
          const updates: Partial<LoadingState> = {};
          if (setLoading) {updates.loading = true;}
          if (clearError) {updates.error = null;}
          set(updates as Partial<S>);
        }

        const result = await action(set, get, ...args);

        if (setLoading) {
          set({ loading: false } as Partial<S>);
        }

        return result;
      } catch (error: unknown) {
        const message = getErrorMessage(error) || errorMessage;

        set({
          error: message,
          ...(setLoading ? { loading: false } : {}),
        } as Partial<S>);

        if (onError) {
          onError(error);
        }

        return undefined;
      }
    };
}

/**
 * Creates a simple action wrapper that doesn't require the action function
 * to accept set/get - they're captured in closure
 *
 * @param actionFn - The async function to execute
 * @param setState - Zustand set function
 * @param config - Configuration for error handling
 * @returns Wrapped async function
 */
export function wrapAsyncAction<S extends LoadingState, Args extends unknown[], R>(
  actionFn: (...args: Args) => Promise<R>,
  setState: SetState<S>,
  config: AsyncActionConfig = {},
): (...args: Args) => Promise<R | undefined> {
  const {
    errorMessage = 'Bir hata oluştu',
    setLoading = true,
    clearError = true,
    onError,
  } = config;

  return async (...args: Args): Promise<R | undefined> => {
    try {
      if (setLoading || clearError) {
        const updates: Partial<LoadingState> = {};
        if (setLoading) {updates.loading = true;}
        if (clearError) {updates.error = null;}
        setState(updates as Partial<S>);
      }

      const result = await actionFn(...args);

      if (setLoading) {
        setState({ loading: false } as Partial<S>);
      }

      return result;
    } catch (error: unknown) {
      const message = getErrorMessage(error) || errorMessage;

      setState({
        error: message,
        ...(setLoading ? { loading: false } : {}),
      } as Partial<S>);

      if (onError) {
        onError(error);
      }

      return undefined;
    }
  };
}

/**
 * Save status state interface for stores with save functionality
 */
export interface SaveState {
  saveStatus: 'saved' | 'saving' | 'error' | null
  saveMessage: string
}

/**
 * Wraps a save action with save status management
 *
 * @param saveFn - The async save function
 * @param setState - Zustand set function
 * @param config - Configuration options
 * @returns Wrapped save function with status updates
 */
export function wrapSaveAction<S extends SaveState, Args extends unknown[], R>(
  saveFn: (...args: Args) => Promise<R>,
  setState: SetState<S>,
  config: {
    successMessage?: string
    errorMessage?: string
    clearDelay?: number
    errorClearDelay?: number
  } = {},
): (...args: Args) => Promise<R | undefined> {
  const {
    successMessage = 'Kaydedildi',
    errorMessage = 'Kaydetme hatası',
    clearDelay = 2000,
    errorClearDelay = 5000,
  } = config;

  return async (...args: Args): Promise<R | undefined> => {
    try {
      setState({ saveStatus: 'saving', saveMessage: '' } as Partial<S>);

      const result = await saveFn(...args);

      setState({
        saveStatus: 'saved',
        saveMessage: successMessage,
      } as Partial<S>);

      // Auto-clear success status
      setTimeout(() => {
        setState({ saveStatus: null, saveMessage: '' } as Partial<S>);
      }, clearDelay);

      return result;
    } catch (error: unknown) {
      const message = getErrorMessage(error) || errorMessage;

      setState({
        saveStatus: 'error',
        saveMessage: message,
      } as Partial<S>);

      // Auto-clear error status
      setTimeout(() => {
        setState({ saveStatus: null, saveMessage: '' } as Partial<S>);
      }, errorClearDelay);

      return undefined;
    }
  };
}

/**
 * Utility to check if a session exists before executing an action
 *
 * @param getSession - Function to get the session from state
 * @param action - The action to execute if session exists
 * @returns Wrapped action that checks for session
 */
export function withSession<S, Session, Args extends unknown[], R>(
  getSession: (state: S) => Session | null | undefined,
  action: (session: Session, ...args: Args) => Promise<R>,
): (get: GetState<S>) => (...args: Args) => Promise<R | undefined> {
  return (get: GetState<S>) =>
    async (...args: Args): Promise<R | undefined> => {
      const session = getSession(get());
      if (!session) {return undefined;}
      return action(session, ...args);
    };
}

/**
 * Creates a debounced version of a function
 *
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced function
 */
export function debounce<Args extends unknown[]>(
  fn: (...args: Args) => void,
  delay: number,
): (...args: Args) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Args): void => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Creates a throttled version of a function
 *
 * @param fn - Function to throttle
 * @param limit - Minimum time between calls in milliseconds
 * @returns Throttled function
 */
export function throttle<Args extends unknown[]>(
  fn: (...args: Args) => void,
  limit: number,
): (...args: Args) => void {
  let lastRan: number | null = null;
  let lastArgs: Args | null = null;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Args): void => {
    if (lastRan === null) {
      fn(...args);
      lastRan = Date.now();
    } else {
      lastArgs = args;
      if (timeoutId === null) {
        const remaining = limit - (Date.now() - lastRan);
        timeoutId = setTimeout(() => {
          if (lastArgs) {
            fn(...lastArgs);
            lastRan = Date.now();
            lastArgs = null;
          }
          timeoutId = null;
        }, remaining > 0 ? remaining : 0);
      }
    }
  };
}

/**
 * Type-safe selector creator for Zustand stores
 *
 * @param selector - Selector function
 * @returns Typed selector
 */
export function createSelector<S, R>(
  selector: (state: S) => R,
): (state: S) => R {
  return selector;
}

/**
 * Creates multiple selectors at once
 *
 * @param selectors - Object with selector functions
 * @returns Object with typed selectors
 */
export function createSelectors<S, Selectors extends Record<string, (state: S) => unknown>>(
  selectors: Selectors,
): Selectors {
  return selectors;
}

export default {
  createAsyncAction,
  wrapAsyncAction,
  wrapSaveAction,
  withSession,
  debounce,
  throttle,
  createSelector,
  createSelectors,
};
