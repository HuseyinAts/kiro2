/**
 * API Helper Utilities
 * API çağrıları için yardımcı fonksiyonlar
 */

import type { AxiosResponse } from 'axios';

import { apiClient } from '../services/apiClient';

interface ApiResponse<T = any> {
  success: boolean
  data: T
  message: string
  timestamp?: string
}

class ApiHelpers {
  /**
   * GET isteği gönder
   */
  async get<T = any>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await apiClient.get(url, { params });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * POST isteği gönder
   */
  async post<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await apiClient.post(url, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * PUT isteği gönder
   */
  async put<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await apiClient.put(url, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * DELETE isteği gönder
   */
  async delete<T = any>(url: string): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await apiClient.delete(url);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * PATCH isteği gönder
   */
  async patch<T = any>(url: string, data?: any): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await apiClient.patch(url, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * File upload
   */
  async uploadFile<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await apiClient.uploadFile(url, file, onProgress);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Hata yönetimi
   */
  private handleError(error: unknown): Error {
    // Type guard for Axios-like error
    const axiosError = error as { response?: { status?: number; data?: { message?: string; detail?: unknown } }; message?: string };

    // 422 Validation Error (FastAPI/Pydantic)
    if (axiosError.response?.status === 422 && axiosError.response?.data?.detail) {
      const validationErrors = this.parseValidationErrors(axiosError.response.data.detail);
      return new Error(`Doğrulama hatası: ${validationErrors}`);
    }

    if (axiosError.response?.data?.message) {
      return new Error(axiosError.response.data.message);
    }

    if (axiosError.response?.data?.detail) {
      // Generic detail message (non-422 errors)
      if (typeof axiosError.response.data.detail === 'string') {
        return new Error(axiosError.response.data.detail);
      }
    }

    if (error instanceof Error) {
      return error;
    }

    if (axiosError.message) {
      return new Error(axiosError.message);
    }

    return new Error('Bilinmeyen API hatası');
  }

  /**
   * Parse FastAPI/Pydantic validation errors (422)
   * Format: { detail: [{ loc: ["body", "field"], msg: "error message", type: "value_error" }] }
   */
  private parseValidationErrors(detail: any): string {
    if (!Array.isArray(detail)) {
      return String(detail);
    }

    const errors = detail.map((err: any) => {
      const field = err.loc?.slice(1).join('.') || 'unknown';  // Skip "body" prefix
      const message = err.msg || 'validation error';
      return `${field}: ${message}`;
    });

    return errors.join(', ');
  }

  /**
   * Loading state yönetimi için wrapper
   */
  async withLoading<T>(
    apiCall: () => Promise<T>,
    setLoading: (loading: boolean) => void,
    setError: (error: string | null) => void,
  ): Promise<T | null> {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Bilinmeyen hata';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }

  /**
   * Retry mekanizması ile API çağrısı
   */
  async withRetry<T>(
    apiCall: () => Promise<T>,
    maxRetries = 3,
    delay = 1000,
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Bilinmeyen hata');

        if (attempt === maxRetries) {
          throw lastError;
        }

        // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt - 1)));
      }
    }

    throw lastError!;
  }

  /**
   * Batch API çağrıları
   */
  async batch<T>(apiCalls: (() => Promise<T>)[]): Promise<(T | Error)[]> {
    const results = await Promise.allSettled(apiCalls.map(call => call()));

    return results.map(result => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return result.reason instanceof Error ? result.reason : new Error('Batch API hatası');
      }
    });
  }

  /**
   * Cache mekanizması (basit in-memory cache)
   */
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();

  async withCache<T>(
    key: string,
    apiCall: () => Promise<T>,
    ttlMs = 5 * 60 * 1000, // 5 dakika
  ): Promise<T> {
    const cached = this.cache.get(key);
    const now = Date.now();

    // Cache hit ve henüz expire olmamış
    if (cached && (now - cached.timestamp) < cached.ttl) {
      return cached.data;
    }

    // API çağrısı yap ve cache'le
    const data = await apiCall();
    this.cache.set(key, {
      data,
      timestamp: now,
      ttl: ttlMs,
    });

    return data;
  }

  /**
   * Cache temizleme
   */
  clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }

  /**
   * Query string oluşturma
   */
  buildQueryString(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, String(item)));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });

    return searchParams.toString();
  }

  /**
   * URL path parametrelerini değiştir
   */
  interpolatePath(path: string, params: Record<string, string | number>): string {
    let result = path;

    Object.entries(params).forEach(([key, value]) => {
      result = result.replace(`:${key}`, String(value));
      result = result.replace(`{${key}}`, String(value));
    });

    return result;
  }
}

// Cache class for API responses
export class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number }>();
  private ttl: number;

  constructor(ttl: number = 30000) {
    this.ttl = ttl;
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) {return null;}

    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  set(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  clear(): void {
    this.cache.clear();
  }
}

// Rate limiter class
export class RateLimiter {
  private queue: Array<() => void> = [];
  private processing = false;
  private minDelay: number;

  constructor(_maxConcurrent: number = 10, minDelay: number = 100) {
    this.minDelay = minDelay;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      this.processQueue();
    });
  }

  private async processQueue(): Promise<void> {
    if (this.processing || this.queue.length === 0) {return;}

    this.processing = true;
    const fn = this.queue.shift();

    if (fn) {
      await fn();
      await new Promise(resolve => setTimeout(resolve, this.minDelay));
    }

    this.processing = false;

    if (this.queue.length > 0) {
      this.processQueue();
    }
  }
}

// Utility functions
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000,
): Promise<T> {
  let lastError: Error;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error('Unknown error');

      if (attempt === maxRetries) {
        throw lastError;
      }

      await new Promise(resolve => setTimeout(resolve, delay * attempt));
    }
  }

  throw lastError!;
}

/**
 * Fetch with error handling and httpOnly cookie support
 * SECURITY: credentials: 'include' enables httpOnly cookie transmission
 */
export async function fetchWithErrorHandling(
  url: string,
  options?: RequestInit,
): Promise<Response> {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // SECURITY: Enable httpOnly cookie transmission
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Network error - please check your connection');
    }
    throw error;
  }
}

export function mergeSignals(...signals: (AbortSignal | undefined)[]): AbortSignal {
  const controller = new AbortController();

  for (const signal of signals) {
    if (signal?.aborted) {
      controller.abort();
      break;
    }

    signal?.addEventListener('abort', () => {
      controller.abort();
    });
  }

  return controller.signal;
}

export const apiHelpers = new ApiHelpers();
export default apiHelpers;

/**
 * Generic API request function (legacy compatibility)
 * Used by authService.ts - wrapper around fetch
 * SECURITY: credentials: 'include' enables httpOnly cookie transmission
 */
export async function apiRequest<T = any>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
      credentials: 'include', // SECURITY: Enable httpOnly cookie transmission
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Request failed' }));

      // Handle 422 validation errors from FastAPI
      if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
        const validationErrors = errorData.detail.map((err: any) => {
          const field = err.loc?.slice(1).join('.') || 'unknown';
          const message = err.msg || 'validation error';
          return `${field}: ${message}`;
        }).join(', ');
        throw new Error(`Doğrulama hatası: ${validationErrors}`);
      }

      throw new Error(errorData.message || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error: unknown) {
    if (error instanceof Error) {
      throw new Error(error.message || 'API request failed');
    }
    throw new Error('API request failed');
  }
}