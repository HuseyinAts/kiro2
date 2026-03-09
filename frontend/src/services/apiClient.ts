/**
 * API Client - Merkezi HTTP istemci konfigürasyonu
 * Axios tabanlı API çağrıları için temel yapılandırma
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

import config from '../config';
import { getErrorMessage, API_ERROR_MESSAGES } from '../constants/errorMessages';

// API Base URL - standardized to use config
const API_BASE_URL = config.api.baseURL;

/**
 * httpOnly Cookie-based Authentication
 * Tokens are managed by the server via secure httpOnly cookies.
 * No more localStorage token storage - XSS attack surface eliminated.
 */

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 saniye timeout
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      // SECURITY: Enable cookie-based auth for all requests
      withCredentials: true,
    });

    this.setupInterceptors();
  }

  /**
   * Request ve Response interceptor'larını kur
   * SECURITY: Tokens are now managed via httpOnly cookies by the server.
   * No localStorage token handling needed - cookies are sent automatically.
   */
  private setupInterceptors(): void {
    // Request interceptor - Cookies are sent automatically with withCredentials: true
    this.client.interceptors.request.use(
      (config) => {
        // No manual token handling needed - httpOnly cookies are sent automatically
        return config;
      },
      (error) => {
        return Promise.reject(error);
      },
    );

    // Response interceptor - Token yenileme ve hata yönetimi
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // 401 Unauthorized - Try to refresh token via secure endpoint
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Refresh token is also in httpOnly cookie, server handles it
            await this.refreshAccessToken();

            // Retry original request - new cookie will be sent automatically
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed - redirect to login
            // Skip redirect if already on /login to prevent infinite reload loop
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          }
        }

        // Diğer hatalar için özel mesajlar
        if (error.response) {
          const errorMessage = this.getErrorMessage(error.response);
          return Promise.reject(new Error(errorMessage));
        }

        return Promise.reject(error);
      },
    );
  }

  /**
   * Hata mesajını çıkar (centralized error messages ile entegre)
   */
  private getErrorMessage(response: AxiosResponse): string {
    // ✅ Handle 422 Validation Errors (FastAPI/Pydantic)
    if (response.status === 422 && response.data?.detail && Array.isArray(response.data.detail)) {
      const validationErrors = response.data.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'bilinmeyen alan';  // Skip "body" prefix
        const message = err.msg || 'doğrulama hatası';
        return `${field}: ${message}`;
      }).join(', ');
      return `Doğrulama hatası: ${validationErrors}`;
    }

    // Check for API error code
    const errorCode = response.data?.code || response.data?.error_code;
    if (errorCode && API_ERROR_MESSAGES[errorCode]) {
      return API_ERROR_MESSAGES[errorCode];
    }

    // Use centralized error messages for HTTP status codes
    const message = getErrorMessage(response.status);
    if (message) {
      return message;
    }

    // Fallback to response data message
    if (response.data?.detail && typeof response.data.detail === 'string') {
      return response.data.detail;
    }

    if (response.data?.message) {
      return response.data.message;
    }

    return 'Bilinmeyen hata oluştu';
  }

  /**
   * Access token'ı yenile (via httpOnly cookie)
   * Server reads refresh token from cookie and sets new access token cookie
   */
  private async refreshAccessToken(): Promise<void> {
    await axios.post(
      `${API_BASE_URL}/api/v1/auth/refresh/secure`,
      {},
      { withCredentials: true },
    );
  }

  /**
   * Logout - Server clears httpOnly cookies
   */
  public async logout(): Promise<void> {
    try {
      await this.client.post('/api/v1/auth/logout/secure');
    } catch {
      // Logout request failed, but we should still redirect
      // Server may have already cleared cookies
    }
  }

  /**
   * Kullanıcı giriş yapmış mı kontrol et
   * With httpOnly cookies, we check by calling a protected endpoint
   * This is called once on app init, result is cached in authStore
   */
  public async isAuthenticated(): Promise<boolean> {
    try {
      await this.client.get('/api/v1/auth/me');
      return true;
    } catch {
      return false;
    }
  }

  // HTTP metodları
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  /**
   * File upload için özel metod
   */
  public async uploadFile<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  }

  /**
   * Raw axios instance'ı al (özel durumlar için)
   */
  public getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

// Singleton instance
export const apiClient = new ApiClient();
export default apiClient;