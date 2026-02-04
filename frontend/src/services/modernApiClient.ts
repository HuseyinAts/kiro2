/**
 * Modern API Client
 * Enhanced API client with TypeScript, error handling, and performance optimization
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError
} from 'axios'
import config from '../config'
import { errorHandler } from '../utils/errorHandler'

// Types
export interface ApiResponse<T = any> {
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
  retryDelay: 1000
}

class ModernApiClient {
  private client: AxiosInstance
  private cache: Map<string, { data: any; expiry: number }> = new Map()
  private requestQueue: Map<string, Promise<any>> = new Map()
  
  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })
    
    this.setupInterceptors()
  }
  
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = this.getAuthToken()
        if (token && !config.headers?.skipAuth) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // Add request timestamp for performance tracking
        config.metadata = { startTime: Date.now() }
        
        return config
      },
      (error) => Promise.reject(this.handleError(error))
    )
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Track response time
        const duration = Date.now() - response.config.metadata?.startTime
        if (duration > 2000) {
          console.warn(`Slow API response: ${response.config.url} (${duration}ms)`)
        }
        
        return response
      },
      async (error) => {
        const originalRequest = error.config
        
        // Handle token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true
          
          try {
            await this.refreshToken()
            return this.client(originalRequest)
          } catch (refreshError) {
            this.handleAuthError()
            return Promise.reject(this.handleError(error))
          }
        }
        
        // Handle retries
        if (this.shouldRetry(error) && originalRequest.retries > 0) {
          originalRequest.retries--
          await this.delay(API_CONFIG.retryDelay)
          return this.client(originalRequest)
        }
        
        return Promise.reject(this.handleError(error))
      }
    )
  }
  
  private getAuthToken(): string | null {
    return localStorage.getItem('authToken') || sessionStorage.getItem('authToken')
  }
  
  private async refreshToken(): Promise<void> {
    const refreshToken = localStorage.getItem('refreshToken')
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }
    
    const response = await this.client.post('/auth/refresh', {
      refreshToken
    }, { skipAuth: true })
    
    const { token } = response.data
    localStorage.setItem('authToken', token)
  }
  
  private handleAuthError(): void {
    localStorage.removeItem('authToken')
    localStorage.removeItem('refreshToken')
    window.location.href = '/login'
  }
  
  private shouldRetry(error: AxiosError): boolean {
    if (!error.response) return true // Network error
    
    const status = error.response.status
    return status >= 500 || status === 408 || status === 429
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
  
  private handleError(error: AxiosError): ApiError {
    // Use centralized error handler
    const appError = errorHandler.handleApiError(error)

    const apiError: ApiError = {
      message: errorHandler.getUserMessage(appError),
      status: appError.status || 500,
      code: appError.type,
      details: appError.details
    }

    if (error.response) {
      // Server responded with error
      apiError.status = error.response.status
      apiError.message = appError.message
      apiError.details = error.response.data
    } else if (error.request) {
      // Network error
      apiError.message = 'Sunucuya bağlanılamıyor'
      apiError.status = 0
    } else {
      // Request setup error
      apiError.message = error.message
    }
    
    return apiError
  }
  
  private getCacheKey(url: string, params?: any): string {
    return `${url}:${JSON.stringify(params || {})}`
  }
  
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key)
    if (cached && cached.expiry > Date.now()) {
      return cached.data
    }
    this.cache.delete(key)
    return null
  }
  
  private setCache(key: string, data: any, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl
    })
  }
  
  // Public API methods
  async get<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const cacheKey = this.getCacheKey(url, config.params)
    
    // Check cache
    if (config.cache !== false) {
      const cached = this.getFromCache(cacheKey)
      if (cached) {
        return cached
      }
    }
    
    // Check if request is already in progress
    if (this.requestQueue.has(cacheKey)) {
      return this.requestQueue.get(cacheKey)!
    }
    
    const requestPromise = this.client.get<T>(url, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries
    }).then(response => {
      const result = {
        data: response.data,
        success: true,
        status: response.status,
        message: response.data?.message
      }
      
      // Cache successful responses
      if (config.cache !== false) {
        this.setCache(cacheKey, result)
      }
      
      return result
    }).finally(() => {
      this.requestQueue.delete(cacheKey)
    })
    
    this.requestQueue.set(cacheKey, requestPromise)
    return requestPromise
  }
  
  async post<T>(url: string, data?: any, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const response = await this.client.post<T>(url, data, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries
    })
    
    return {
      data: response.data,
      success: true,
      status: response.status,
      message: response.data?.message
    }
  }
  
  async put<T>(url: string, data?: any, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const response = await this.client.put<T>(url, data, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries
    })
    
    return {
      data: response.data,
      success: true,
      status: response.status,
      message: response.data?.message
    }
  }
  
  async delete<T>(url: string, config: RequestConfig = {}): Promise<ApiResponse<T>> {
    const response = await this.client.delete<T>(url, {
      ...config,
      retries: config.retries ?? API_CONFIG.retries
    })
    
    return {
      data: response.data,
      success: true,
      status: response.status,
      message: response.data?.message
    }
  }
  
  // Utility methods
  clearCache(): void {
    this.cache.clear()
  }
  
  setBaseURL(url: string): void {
    this.client.defaults.baseURL = url
  }
  
  setDefaultHeaders(headers: Record<string, string>): void {
    Object.assign(this.client.defaults.headers, headers)
  }
  
  // Request cancellation
  createCancelToken() {
    return axios.CancelToken.source()
  }
  
  isCancel(error: any): boolean {
    return axios.isCancel(error)
  }
}

// Create singleton instance
export const apiClient = new ModernApiClient()

// Export specialized clients
export class AuthAPI {
  static async login(credentials: { email: string; password: string }) {
    return apiClient.post('/auth/login', credentials, { skipAuth: true })
  }
  
  static async register(userData: any) {
    return apiClient.post('/auth/register', userData, { skipAuth: true })
  }
  
  static async logout() {
    return apiClient.post('/auth/logout')
  }
  
  static async getProfile() {
    return apiClient.get('/auth/profile', { cache: true })
  }
}

export class ExamAPI {
  static async getExams() {
    return apiClient.get('/exams', { cache: true })
  }
  
  static async getExam(id: string) {
    return apiClient.get(`/exams/${id}`, { cache: true })
  }
  
  static async submitExam(id: string, answers: any) {
    return apiClient.post(`/exams/${id}/submit`, answers)
  }
  
  static async getResults(id: string) {
    return apiClient.get(`/exams/${id}/results`, { cache: true })
  }
}

export class StudentsAPI {
  static async getDashboardData() {
    return apiClient.get('/students/dashboard', { cache: true })
  }
  
  static async getPerformance() {
    return apiClient.get('/students/performance', { cache: true })
  }
  
  static async updateProfile(data: any) {
    return apiClient.put('/students/profile', data)
  }
}

export default apiClient