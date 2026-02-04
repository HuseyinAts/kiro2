/**
 * API Client - Merkezi HTTP istemci konfigürasyonu
 * Axios tabanlı API çağrıları için temel yapılandırma
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { getErrorMessage, API_ERROR_MESSAGES } from '../constants/errorMessages'

// API Base URL - standardized to use config
import config from '../config'
const API_BASE_URL = config.api.baseURL

// Token storage anahtarları
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 saniye timeout
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    this.setupInterceptors()
  }

  /**
   * Request ve Response interceptor'larını kur
   */
  private setupInterceptors(): void {
    // Request interceptor - Token ekleme
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor - Token yenileme ve hata yönetimi
    this.client.interceptors.response.use(
      (response) => {
        return response
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

        // 401 Unauthorized - Token yenileme dene
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = this.getRefreshToken()
            if (refreshToken) {
              const response = await this.refreshAccessToken(refreshToken)
              const newAccessToken = response.access_token

              this.setAccessToken(newAccessToken)
              
              // Orijinal isteği yeni token ile tekrar dene
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
              }
              
              return this.client(originalRequest)
            }
          } catch (refreshError) {
            // Refresh token da geçersizse logout yap
            this.clearTokens()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }

        // Diğer hatalar için özel mesajlar
        if (error.response) {
          const errorMessage = this.getErrorMessage(error.response)
          return Promise.reject(new Error(errorMessage))
        }

        return Promise.reject(error)
      }
    )
  }

  /**
   * Hata mesajını çıkar (centralized error messages ile entegre)
   */
  private getErrorMessage(response: AxiosResponse): string {
    // ✅ Handle 422 Validation Errors (FastAPI/Pydantic)
    if (response.status === 422 && response.data?.detail && Array.isArray(response.data.detail)) {
      const validationErrors = response.data.detail.map((err: any) => {
        const field = err.loc?.slice(1).join('.') || 'bilinmeyen alan'  // Skip "body" prefix
        const message = err.msg || 'doğrulama hatası'
        return `${field}: ${message}`
      }).join(', ')
      return `Doğrulama hatası: ${validationErrors}`
    }

    // Check for API error code
    const errorCode = response.data?.code || response.data?.error_code
    if (errorCode && API_ERROR_MESSAGES[errorCode]) {
      return API_ERROR_MESSAGES[errorCode]
    }

    // Use centralized error messages for HTTP status codes
    const message = getErrorMessage(response.status)
    if (message) {
      return message
    }

    // Fallback to response data message
    if (response.data?.detail && typeof response.data.detail === 'string') {
      return response.data.detail
    }

    if (response.data?.message) {
      return response.data.message
    }

    return 'Bilinmeyen hata oluştu'
  }

  /**
   * Access token'ı al
   */
  private getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  }

  /**
   * Refresh token'ı al
   */
  private getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  /**
   * Access token'ı kaydet
   */
  private setAccessToken(token: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
  }

  /**
   * Refresh token'ı kaydet
   */
  private setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  }

  /**
   * Token'ları temizle
   */
  private clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  /**
   * Access token'ı yenile
   */
  private async refreshAccessToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
      refresh_token: refreshToken
    })
    return response.data
  }

  /**
   * Token'ları kaydet (login sonrası)
   */
  public setTokens(accessToken: string, refreshToken: string): void {
    this.setAccessToken(accessToken)
    this.setRefreshToken(refreshToken)
  }

  /**
   * Logout - Token'ları temizle
   */
  public logout(): void {
    this.clearTokens()
  }

  /**
   * Kullanıcı giriş yapmış mı kontrol et
   */
  public isAuthenticated(): boolean {
    return !!this.getAccessToken()
  }

  // HTTP metodları
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config)
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config)
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config)
  }

  public async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config)
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config)
  }

  /**
   * File upload için özel metod
   */
  public async uploadFile<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<AxiosResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    return this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
  }

  /**
   * Raw axios instance'ı al (özel durumlar için)
   */
  public getAxiosInstance(): AxiosInstance {
    return this.client
  }
}

// Singleton instance
export const apiClient = new ApiClient()
export default apiClient