/**
 * ModernApiClient Integration Tests
 * Comprehensive test suite for API client functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import { apiClient, AuthAPI, ExamAPI, StudentsAPI } from '../modernApiClient'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios)
const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() }
  },
  defaults: {
    headers: {},
    baseURL: ''
  }
}

describe('ModernApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.create.mockReturnValue(mockAxiosInstance as any)
    
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn()
      },
      writable: true
    })
    
    // Mock sessionStorage
    Object.defineProperty(window, 'sessionStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn()
      },
      writable: true
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('creates axios instance with correct config', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8001/api',
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      })
    })

    it('sets up request and response interceptors', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled()
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled()
    })
  })

  describe('GET Requests', () => {
    it('makes successful GET request', async () => {
      const mockData = { users: [{ id: 1, name: 'Test' }] }
      mockAxiosInstance.get.mockResolvedValue({
        data: mockData,
        status: 200
      })

      const result = await apiClient.get('/users')

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/users', {
        retries: 3
      })
      expect(result).toEqual({
        data: mockData,
        success: true,
        status: 200,
        message: undefined
      })
    })

    it('caches GET requests by default', async () => {
      const mockData = { id: 1, name: 'Test' }
      mockAxiosInstance.get.mockResolvedValue({
        data: mockData,
        status: 200
      })

      // First request
      await apiClient.get('/user/1')
      
      // Second request should use cache
      await apiClient.get('/user/1')

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1)
    })

    it('bypasses cache when cache: false', async () => {
      const mockData = { id: 1, name: 'Test' }
      mockAxiosInstance.get.mockResolvedValue({
        data: mockData,
        status: 200
      })

      await apiClient.get('/user/1', { cache: false })
      await apiClient.get('/user/1', { cache: false })

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2)
    })

    it('deduplicates concurrent requests', async () => {
      const mockData = { id: 1, name: 'Test' }
      mockAxiosInstance.get.mockResolvedValue({
        data: mockData,
        status: 200
      })

      // Make concurrent requests
      const promise1 = apiClient.get('/user/1')
      const promise2 = apiClient.get('/user/1')

      await Promise.all([promise1, promise2])

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(1)
    })
  })

  describe('POST Requests', () => {
    it('makes successful POST request', async () => {
      const mockData = { id: 1, message: 'Created' }
      const postData = { name: 'New User' }
      
      mockAxiosInstance.post.mockResolvedValue({
        data: mockData,
        status: 201
      })

      const result = await apiClient.post('/users', postData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/users', postData, {
        retries: 3
      })
      expect(result).toEqual({
        data: mockData,
        success: true,
        status: 201,
        message: undefined
      })
    })
  })

  describe('PUT Requests', () => {
    it('makes successful PUT request', async () => {
      const mockData = { id: 1, message: 'Updated' }
      const putData = { name: 'Updated User' }
      
      mockAxiosInstance.put.mockResolvedValue({
        data: mockData,
        status: 200
      })

      const result = await apiClient.put('/users/1', putData)

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/users/1', putData, {
        retries: 3
      })
      expect(result).toEqual({
        data: mockData,
        success: true,
        status: 200,
        message: undefined
      })
    })
  })

  describe('DELETE Requests', () => {
    it('makes successful DELETE request', async () => {
      const mockData = { message: 'Deleted' }
      
      mockAxiosInstance.delete.mockResolvedValue({
        data: mockData,
        status: 200
      })

      const result = await apiClient.delete('/users/1')

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/users/1', {
        retries: 3
      })
      expect(result).toEqual({
        data: mockData,
        success: true,
        status: 200,
        message: undefined
      })
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      const networkError = new Error('Network Error')
      mockAxiosInstance.get.mockRejectedValue(networkError)

      await expect(apiClient.get('/users')).rejects.toEqual({
        message: 'Network Error',
        status: 500
      })
    })

    it('handles HTTP error responses', async () => {
      const httpError = {
        response: {
          status: 404,
          data: { message: 'Not Found' }
        }
      }
      mockAxiosInstance.get.mockRejectedValue(httpError)

      await expect(apiClient.get('/users/999')).rejects.toEqual({
        message: 'Not Found',
        status: 404,
        details: { message: 'Not Found' }
      })
    })

    it('handles server connection errors', async () => {
      const connectionError = {
        request: {},
        message: 'Connection failed'
      }
      mockAxiosInstance.get.mockRejectedValue(connectionError)

      await expect(apiClient.get('/users')).rejects.toEqual({
        message: 'Sunucuya bağlanılamıyor',
        status: 0
      })
    })
  })

  describe('Authentication', () => {
    it('adds auth token to requests', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('test-token')
      
      // Trigger a request to test the interceptor
      apiClient.get('/protected')
      
      expect(localStorage.getItem).toHaveBeenCalledWith('authToken')
    })

    it('skips auth for requests with skipAuth flag', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('test-token')
      
      apiClient.get('/public', { skipAuth: true })
      
      // Auth token should not be added
      expect(localStorage.getItem).not.toHaveBeenCalled()
    })
  })

  describe('Cache Management', () => {
    it('clears cache when requested', async () => {
      const mockData = { id: 1, name: 'Test' }
      mockAxiosInstance.get.mockResolvedValue({
        data: mockData,
        status: 200
      })

      // Cache a request
      await apiClient.get('/user/1')
      
      // Clear cache
      apiClient.clearCache()
      
      // Next request should hit the API again
      await apiClient.get('/user/1')

      expect(mockAxiosInstance.get).toHaveBeenCalledTimes(2)
    })
  })

  describe('Utility Methods', () => {
    it('sets base URL', () => {
      apiClient.setBaseURL('https://api.example.com')
      
      expect(mockAxiosInstance.defaults.baseURL).toBe('https://api.example.com')
    })

    it('sets default headers', () => {
      apiClient.setDefaultHeaders({ 'X-Custom': 'value' })
      
      expect(mockAxiosInstance.defaults.headers).toEqual({
        'X-Custom': 'value'
      })
    })

    it('creates cancel token', () => {
      mockedAxios.CancelToken = {
        source: vi.fn().mockReturnValue({ token: 'test-token', cancel: vi.fn() })
      } as any

      const cancelToken = apiClient.createCancelToken()
      
      expect(mockedAxios.CancelToken.source).toHaveBeenCalled()
      expect(cancelToken).toEqual({ token: 'test-token', cancel: expect.any(Function) })
    })

    it('checks if error is cancel', () => {
      mockedAxios.isCancel = vi.fn().mockReturnValue(true)
      
      const result = apiClient.isCancel(new Error('Cancelled'))
      
      expect(mockedAxios.isCancel).toHaveBeenCalled()
      expect(result).toBe(true)
    })
  })
})

describe('AuthAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.create.mockReturnValue(mockAxiosInstance as any)
  })

  describe('login', () => {
    it('calls login endpoint with credentials', async () => {
      const credentials = { email: 'test@example.com', password: 'password' }
      const mockResponse = { token: 'auth-token', user: { id: 1 } }
      
      mockAxiosInstance.post.mockResolvedValue({
        data: mockResponse,
        status: 200
      })

      const result = await AuthAPI.login(credentials)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', credentials, {
        skipAuth: true,
        retries: 3
      })
      expect(result.data).toEqual(mockResponse)
    })
  })

  describe('register', () => {
    it('calls register endpoint with user data', async () => {
      const userData = { email: 'test@example.com', password: 'password', name: 'Test' }
      const mockResponse = { message: 'User created' }
      
      mockAxiosInstance.post.mockResolvedValue({
        data: mockResponse,
        status: 201
      })

      const result = await AuthAPI.register(userData)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/register', userData, {
        skipAuth: true,
        retries: 3
      })
      expect(result.data).toEqual(mockResponse)
    })
  })

  describe('getProfile', () => {
    it('calls profile endpoint with caching', async () => {
      const mockProfile = { id: 1, email: 'test@example.com' }
      
      mockAxiosInstance.get.mockResolvedValue({
        data: mockProfile,
        status: 200
      })

      const result = await AuthAPI.getProfile()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/profile', {
        cache: true,
        retries: 3
      })
      expect(result.data).toEqual(mockProfile)
    })
  })
})

describe('ExamAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.create.mockReturnValue(mockAxiosInstance as any)
  })

  describe('getExams', () => {
    it('fetches exams with caching', async () => {
      const mockExams = [{ id: 1, title: 'Math Exam' }]
      
      mockAxiosInstance.get.mockResolvedValue({
        data: mockExams,
        status: 200
      })

      const result = await ExamAPI.getExams()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/exams', {
        cache: true,
        retries: 3
      })
      expect(result.data).toEqual(mockExams)
    })
  })

  describe('submitExam', () => {
    it('submits exam answers', async () => {
      const examId = '123'
      const answers = { question1: 'A', question2: 'B' }
      const mockResponse = { score: 85, passed: true }
      
      mockAxiosInstance.post.mockResolvedValue({
        data: mockResponse,
        status: 200
      })

      const result = await ExamAPI.submitExam(examId, answers)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        `/exams/${examId}/submit`, 
        answers,
        { retries: 3 }
      )
      expect(result.data).toEqual(mockResponse)
    })
  })
})

describe('StudentsAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.create.mockReturnValue(mockAxiosInstance as any)
  })

  describe('getDashboardData', () => {
    it('fetches dashboard data with caching', async () => {
      const mockDashboard = { 
        stats: { completedExams: 5, averageScore: 85 },
        recentActivity: []
      }
      
      mockAxiosInstance.get.mockResolvedValue({
        data: mockDashboard,
        status: 200
      })

      const result = await StudentsAPI.getDashboardData()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/students/dashboard', {
        cache: true,
        retries: 3
      })
      expect(result.data).toEqual(mockDashboard)
    })
  })

  describe('updateProfile', () => {
    it('updates student profile', async () => {
      const profileData = { name: 'Updated Name', phone: '123456789' }
      const mockResponse = { message: 'Profile updated' }
      
      mockAxiosInstance.put.mockResolvedValue({
        data: mockResponse,
        status: 200
      })

      const result = await StudentsAPI.updateProfile(profileData)

      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/students/profile', 
        profileData,
        { retries: 3 }
      )
      expect(result.data).toEqual(mockResponse)
    })
  })
})