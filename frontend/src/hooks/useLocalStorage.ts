/**
 * useLocalStorage Hook
 *
 * Centralized localStorage access with:
 * - Type safety with generics
 * - Error handling
 * - SSR compatibility
 * - Automatic JSON serialization/deserialization
 * - Cross-tab synchronization via storage events
 * - Memory caching to avoid repeated reads
 *
 * Usage:
 * ```typescript
 * const [value, setValue, removeValue] = useLocalStorage<string>('key', 'default')
 * const [settings, setSettings] = useLocalStorage('settings', { theme: 'dark' })
 * ```
 */

import { useState, useEffect, useCallback, useMemo } from 'react';

/**
 * Type for the setValue function that can accept a value or updater function
 */
type SetValue<T> = (value: T | ((prev: T) => T)) => void

/**
 * Return type of useLocalStorage hook
 */
type UseLocalStorageReturn<T> = [T, SetValue<T>, () => void]

/**
 * Options for useLocalStorage hook
 */
interface UseLocalStorageOptions<T> {
  /** Custom serializer (default: JSON.stringify) */
  serializer?: (value: T) => string
  /** Custom deserializer (default: JSON.parse) */
  deserializer?: (value: string) => T
  /** Whether to sync across tabs (default: true) */
  syncTabs?: boolean
  /** Error handler for storage errors */
  onError?: (error: Error) => void
}

/**
 * Check if we're in a browser environment
 */
const isBrowser = typeof window !== 'undefined';

/**
 * In-memory cache for localStorage values to avoid repeated reads
 */
const storageCache = new Map<string, unknown>();

/**
 * Custom hook for localStorage with type safety and error handling
 *
 * @param key - Storage key
 * @param initialValue - Default value if key doesn't exist
 * @param options - Optional configuration
 * @returns Tuple of [value, setValue, removeValue]
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options: UseLocalStorageOptions<T> = {},
): UseLocalStorageReturn<T> {
  const {
    serializer = JSON.stringify,
    deserializer = JSON.parse,
    syncTabs = true,
    onError,
  } = options;

  // Get stored value or initial value
  const readValue = useCallback((): T => {
    // Return initial value during SSR
    if (!isBrowser) {
      return initialValue;
    }

    // Check cache first
    if (storageCache.has(key)) {
      return storageCache.get(key) as T;
    }

    try {
      const item = window.localStorage.getItem(key);
      if (item === null) {
        return initialValue;
      }

      const parsed = deserializer(item);
      storageCache.set(key, parsed);
      return parsed;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      if (onError && error instanceof Error) {
        onError(error);
      }
      return initialValue;
    }
  }, [key, initialValue, deserializer, onError]);

  // State to store our value
  const [storedValue, setStoredValue] = useState<T>(readValue);

  // Return a wrapped version of useState's setter function that
  // persists the new value to localStorage
  const setValue: SetValue<T> = useCallback(
    (value) => {
      if (!isBrowser) {
        console.warn(`Cannot set localStorage key "${key}" during SSR`);
        return;
      }

      try {
        // Allow value to be a function so we have same API as useState
        const valueToStore = value instanceof Function ? value(storedValue) : value;

        // Save to state
        setStoredValue(valueToStore);

        // Save to localStorage
        const serialized = serializer(valueToStore);
        window.localStorage.setItem(key, serialized);

        // Update cache
        storageCache.set(key, valueToStore);

        // Dispatch storage event for cross-tab sync (same tab doesn't receive it)
        window.dispatchEvent(
          new StorageEvent('storage', {
            key,
            newValue: serialized,
            storageArea: localStorage,
          }),
        );
      } catch (error) {
        console.error(`Error setting localStorage key "${key}":`, error);
        if (onError && error instanceof Error) {
          onError(error);
        }
      }
    },
    [key, storedValue, serializer, onError],
  );

  // Remove value from storage
  const removeValue = useCallback(() => {
    if (!isBrowser) {return;}

    try {
      window.localStorage.removeItem(key);
      storageCache.delete(key);
      setStoredValue(initialValue);

      // Dispatch storage event
      window.dispatchEvent(
        new StorageEvent('storage', {
          key,
          newValue: null,
          storageArea: localStorage,
        }),
      );
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
      if (onError && error instanceof Error) {
        onError(error);
      }
    }
  }, [key, initialValue, onError]);

  // Listen for changes in other tabs
  useEffect(() => {
    if (!isBrowser || !syncTabs) {return;}

    const handleStorageChange = (event: StorageEvent) => {
      if (event.key !== key || event.storageArea !== localStorage) {return;}

      try {
        if (event.newValue === null) {
          setStoredValue(initialValue);
          storageCache.delete(key);
        } else {
          const newValue = deserializer(event.newValue);
          setStoredValue(newValue);
          storageCache.set(key, newValue);
        }
      } catch (error) {
        console.warn(`Error handling storage change for key "${key}":`, error);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, initialValue, syncTabs, deserializer]);

  return [storedValue, setValue, removeValue];
}

/**
 * Hook for storing Set values in localStorage
 *
 * @param key - Storage key
 * @param initialValue - Default Set value
 * @returns Tuple with Set-specific operations
 */
export function useLocalStorageSet<T>(
  key: string,
  initialValue: Set<T> = new Set(),
): [Set<T>, (value: T) => void, (value: T) => void, () => void] {
  const [set, setSet, removeSet] = useLocalStorage<T[]>(
    key,
    Array.from(initialValue),
    {
      serializer: JSON.stringify,
      deserializer: (value) => JSON.parse(value),
    },
  );

  const currentSet = useMemo(() => new Set(set), [set]);

  const addItem = useCallback(
    (item: T) => {
      setSet((prev) => {
        const newSet = new Set(prev);
        newSet.add(item);
        return Array.from(newSet);
      });
    },
    [setSet],
  );

  const removeItem = useCallback(
    (item: T) => {
      setSet((prev) => {
        const newSet = new Set(prev);
        newSet.delete(item);
        return Array.from(newSet);
      });
    },
    [setSet],
  );

  const clearSet = useCallback(() => {
    removeSet();
  }, [removeSet]);

  return [currentSet, addItem, removeItem, clearSet];
}

/**
 * Hook for storing Map values in localStorage
 *
 * @param key - Storage key
 * @param initialValue - Default Map value
 * @returns Tuple with Map-specific operations
 */
export function useLocalStorageMap<K extends string | number, V>(
  key: string,
  initialValue: Map<K, V> = new Map(),
): [
  Map<K, V>,
  (key: K, value: V) => void,
  (key: K) => void,
  () => void
] {
  const [entries, setEntries, removeEntries] = useLocalStorage<[K, V][]>(
    key,
    Array.from(initialValue.entries()),
    {
      serializer: JSON.stringify,
      deserializer: (value) => JSON.parse(value),
    },
  );

  const currentMap = useMemo(() => new Map(entries), [entries]);

  const setItem = useCallback(
    (k: K, v: V) => {
      setEntries((prev) => {
        const newMap = new Map(prev);
        newMap.set(k, v);
        return Array.from(newMap.entries());
      });
    },
    [setEntries],
  );

  const removeItem = useCallback(
    (k: K) => {
      setEntries((prev) => {
        const newMap = new Map(prev);
        newMap.delete(k);
        return Array.from(newMap.entries());
      });
    },
    [setEntries],
  );

  const clearMap = useCallback(() => {
    removeEntries();
  }, [removeEntries]);

  return [currentMap, setItem, removeItem, clearMap];
}

/**
 * Simple getter for localStorage value without React state
 *
 * @param key - Storage key
 * @param defaultValue - Default value if key doesn't exist
 * @returns Stored value or default
 */
export function getLocalStorageValue<T>(key: string, defaultValue: T): T {
  if (!isBrowser) {return defaultValue;}

  // Check cache first
  if (storageCache.has(key)) {
    return storageCache.get(key) as T;
  }

  try {
    const item = localStorage.getItem(key);
    if (item === null) {return defaultValue;}

    const parsed = JSON.parse(item) as T;
    storageCache.set(key, parsed);
    return parsed;
  } catch {
    return defaultValue;
  }
}

/**
 * Simple setter for localStorage value without React state
 *
 * @param key - Storage key
 * @param value - Value to store
 */
export function setLocalStorageValue<T>(key: string, value: T): void {
  if (!isBrowser) {return;}

  try {
    const serialized = JSON.stringify(value);
    localStorage.setItem(key, serialized);
    storageCache.set(key, value);
  } catch (error) {
    console.error(`Error setting localStorage key "${key}":`, error);
  }
}

/**
 * Clear the in-memory cache
 * Useful when you know localStorage has been modified externally
 */
export function clearLocalStorageCache(): void {
  storageCache.clear();
}

/**
 * Remove a specific key from cache
 */
export function invalidateLocalStorageCache(key: string): void {
  storageCache.delete(key);
}

export default useLocalStorage;
