/**
 * Modern API Client
 * Enhanced API client with TypeScript, error handling, and performance optimization
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosError,
} from 'axios';

import config from '../config';
import { errorHandler } from '../utils/errorHandler';

// Extend Axios config types for custom properties
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    metadata?: { startTime: number }
    _retry?: boolean
    retries?: number
  }
  export interface AxiosRequestConfig {
    skipAuth?: boolean
    retries?: number
  }
}

// Types
export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  success: boolean
  status: number
}

export interface ApiError {
  message: string
  status: number
  code?: string
  details?: any
}

export interface RequestConfig extends AxiosRequestConfig {
  skipAuth?: boolean
  retries?: number
  cache?: boolean
  timeout?: number
}

// Configuration
const API_CONFIG = {
  baseURL: config.api.baseURL,
  timeout: config.api.timeout || 30000,
  retries: 3,
  retryDelay: 1000,
};

class ModernApiClient {
  private client: AxiosInstance;
  private cache: Map<string, { data: any; expiry: number }> = new Map();
  private requestQueue: Map<string, Promise<any>> = new Map();

  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      withCredentials: true, // SECURITY: Enable httpOnly cookie-based auth
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    // SECURITY: No token handling - httpOnly cookies are automatically sent
    this.client.interceptors.request.use(
      (config) => {
        // Add request timestamp for performance tracking
        config.metadata = { startTime: Date.now() };

        return config;
      },
      (error) => Promise.reject(this.handleError(error)),
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Track response time
        const startTime = response.config.metadata?.startTime;
        if (startTime !== undefined) {
          const duration = Date.now() - startTime;
          if (duration > 2000) {
            console.warn(`Slow API response: ${response.config.url} (${duration}ms)`);
          }
        }

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await this.refreshToken();
            return this.client(originalRequest);
          } catch {
            this.handleAuthError();
            return Promise.reject(this.handleError(error));
          }
        }

        // Handle retries
        if (this.shouldRetry(error) && originalRequest.retries > 0) {
          originalRequest.retries--;
          await this.delay(API_CONFIG.retryDelay);
          return this.client(originalRequest);
        }

        return Promise.reject(this.handleError(error));
      },
    );
  }

  /**
   * SECURITY: Token refresh via httpOnly cookie
   * Server reads refresh_token from httpOnly cookie and sets new access_token cookie
   */
  private async refreshToken(): Promise<void> {
    // Server handles token via httpOnly cookies - no client-side token storage
    await this.client.post('/api/v1/auth/refresh/secure', {}, { skipAuth: true });
  }

  /**
   * SECURITY: Logout via secure endpoint
   * Server clears httpOnly cookies
   */
  private handleAuthError(): void {
    // Redirect to login - server will clear cookies on logout
    window.location.href = '/login';
  }

  private shouldRetry(error: AxiosError): boolean {
    if (!error.response) {return true;} // Network error

    const status = error.response.status;
    return status >= 500 || status === 408 || status === 429;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private handleError(error: AxiosError): ApiError {
    // Use centralized error handler
    const appError = errorHandler.handleApiError(error);

    const apiError: ApiError = {
      message: errorHandler.getUserMessage(appError),
      status: appError.status || 500,
      code: appError.type,
      details: appError.details,
    };

    if (error.response) {
      // Server responded with error
      apiError.status = error.response.status;
      apiError.message = appError.message;
      apiError.details = error.response.data;
    } else if (error.request) {
      // Network error
      apiError.message = 'Sunucuya bağlanılamıyor';
      apiError.status = 0;
    } else {
      // Request setup error
      apiError.message = error.message;
    }

    return apiError;
  }

  private getCacheKey(url: string, params?: any): string {
    return `${url}:${JSON.stringify(params || {})}`;
  }

  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && cached.expiry > Date.now()) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  private setCache(key: string, data: any, ttl: number = 5 * 60 * 1000): void {
    // Memory leak prevention: limit cache size
    const MAX_CACHE_SIZE = 100;

    // Evict oldest entries if cache is full
    if (this.cache.size >= MAX_CACHE_SIZE) {
      // Remove expired entries first
      const now = Date.now();
      for (const [k, v] of this.cache.entries()) {
        if (v.expiry <= now) {
          this.cache.delete(k);
        }
      }

      // If still at limit, remove oldest entries (FIFO)
      if (this.cache.size >= MAX_CACHE_SIZE) {
        const keysToDelete = Array.from(this.cache.keys()).slice(0, 10);
        keysToDelete.forEach(k => this.cache.delete(k));
      }
    }

    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl,
    });
  }

  // Public API methods
  async get<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const cacheKey = this.getCacheKey(url, config.params);

    // Check cache
    if (config.cache !== false) {
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        return cached;
      }
    }

    // Check if request is already in progress
    if (this.requestQueue.has(cacheKey)) {
      return this.requestQueue.get(cacheKey)!;
    }

    const requestPromise = this.client.get<T>(url, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries,
    }).then(response => {
      const responseData = response.data as Record<string, unknown>;
      const result: ApiResponse<T> = {
        data: response.data,
        success: true,
        status: response.status,
        message: typeof responseData === 'object' && responseData !== null ? (responseData.message as string | undefined) : undefined,
      };

      // Cache successful responses
      if (config.cache !== false) {
        this.setCache(cacheKey, result);
      }

      return result;
    }).finally(() => {
      this.requestQueue.delete(cacheKey);
    });

    this.requestQueue.set(cacheKey, requestPromise);
    return requestPromise;
  }

  async post<T>(url: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const response = await this.client.post<T>(url, data, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries,
    });
    const responseData = response.data as Record<string, unknown>;

    return {
      data: response.data,
      success: true,
      status: response.status,
      message: typeof responseData === 'object' && responseData !== null ? (responseData.message as string | undefined) : undefined,
    };
  }

  async put<T>(url: string, data?: unknown, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const response = await this.client.put<T>(url, data, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries,
    });
    const responseData = response.data as Record<string, unknown>;

    return {
      data: response.data,
      success: true,
      status: response.status,
      message: typeof responseData === 'object' && responseData !== null ? (responseData.message as string | undefined) : undefined,
    };
  }

  async delete<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const response = await this.client.delete<T>(url, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries,
    });
    const responseData = response.data as Record<string, unknown>;

    return {
      data: response.data,
      success: true,
      status: response.status,
      message: typeof responseData === 'object' && responseData !== null ? (responseData.message as string | undefined) : undefined,
    };
  }

  // Utility methods
  clearCache(): void {
    this.cache.clear();
  }

  setBaseURL(url: string): void {
    this.client.defaults.baseURL = url;
  }

  setDefaultHeaders(headers: Record<string, string>): void {
    Object.assign(this.client.defaults.headers, headers);
  }

  // Request cancellation
  createCancelToken() {
    return axios.CancelToken.source();
  }

  isCancel(error: any): boolean {
    return axios.isCancel(error);
  }
}

// Create singleton instance
export const apiClient = new ModernApiClient();

// Export specialized clients
export class AuthAPI {
  static async login(credentials: { email: string; password: string }) {
    return apiClient.post('/auth/login', credentials, { skipAuth: true });
  }

  static async register(userData: any) {
    return apiClient.post('/auth/register', userData, { skipAuth: true });
  }

  static async logout() {
    return apiClient.post('/auth/logout');
  }

  static async getProfile() {
    return apiClient.get('/auth/profile', { cache: true });
  }
}

export class ExamAPI {
  static async getExams() {
    return apiClient.get('/exams', { cache: true });
  }

  static async getExam(id: string) {
    return apiClient.get(`/exams/${id}`, { cache: true });
  }

  static async submitExam(id: string, answers: any) {
    return apiClient.post(`/exams/${id}/submit`, answers);
  }

  static async getResults(id: string) {
    return apiClient.get(`/exams/${id}/results`, { cache: true });
  }
}

export class StudentsAPI {
  static async getDashboardData() {
    return apiClient.get('/students/dashboard', { cache: true });
  }

  static async getPerformance() {
    return apiClient.get('/students/performance', { cache: true });
  }

  static async updateProfile(data: any) {
    return apiClient.put('/students/profile', data);
  }
}

export default apiClient;