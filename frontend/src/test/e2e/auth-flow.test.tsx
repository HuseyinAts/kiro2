/**
 * Authentication Flow E2E Tests
 * End-to-end tests for user authentication scenarios
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render, mockApiResponse, mockApiError } from '../utils/test-utils'
import App from '../../app'

// Mock the API client
vi.mock('../../services/modernApiClient', () => ({
  AuthAPI: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getProfile: vi.fn()
  },
  StudentsAPI: {
    getDashboardData: vi.fn()
  }
}))

// Mock router to start at login page
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/login', state: {} })
  }
})

describe('Authentication Flow E2E', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  describe('Login Flow', () => {
    it('allows user to login with valid credentials', async () => {
      const mockLoginResponse = {
        data: {
          token: 'mock-jwt-token',
          user: {
            id: '1',
            adi: 'Test',
            soyadi: 'Öğrenci',
            email: 'test@example.com',
            rol: 'ogrenci'
          }
        },
        success: true,
        status: 200
      }

      const mockDashboardData = {
        data: {
          stats: { completedExams: 5, averageScore: 85 },
          recentActivity: []
        },
        success: true,
        status: 200
      }

      vi.mocked(require('../../services/modernApiClient').AuthAPI.login)
        .mockResolvedValue(mockLoginResponse)
      
      vi.mocked(require('../../services/modernApiClient').StudentsAPI.getDashboardData)
        .mockResolvedValue(mockDashboardData)

      const { user } = render(<App />)

      // Find and fill login form
      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(loginButton)

      // Wait for login to complete and dashboard to load
      await waitFor(() => {
        expect(require('../../services/modernApiClient').AuthAPI.login)
          .toHaveBeenCalledWith({
            email: 'test@example.com',
            password: 'password123'
          })
      })

      // Verify user is redirected to dashboard
      await waitFor(() => {
        expect(screen.getByText(/merhaba, test/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('shows error message for invalid credentials', async () => {
      const mockErrorResponse = {
        message: 'Geçersiz e-posta veya şifre',
        status: 401
      }

      vi.mocked(require('../../services/modernApiClient').AuthAPI.login)
        .mockRejectedValue(mockErrorResponse)

      const { user } = render(<App />)

      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      await user.type(emailInput, 'invalid@example.com')
      await user.type(passwordInput, 'wrongpassword')
      await user.click(loginButton)

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText('Geçersiz e-posta veya şifre')).toBeInTheDocument()
      })
    })

    it('validates form fields before submission', async () => {
      const { user } = render(<App />)

      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      // Try to submit empty form
      await user.click(loginButton)

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/e-posta adresi gerekli/i)).toBeInTheDocument()
        expect(screen.getByText(/şifre gerekli/i)).toBeInTheDocument()
      })

      // API should not be called
      expect(require('../../services/modernApiClient').AuthAPI.login).not.toHaveBeenCalled()
    })

    it('validates email format', async () => {
      const { user } = render(<App />)

      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      await user.type(emailInput, 'invalid-email')
      await user.type(passwordInput, 'password123')
      await user.click(loginButton)

      await waitFor(() => {
        expect(screen.getByText(/geçerli bir e-posta adresi girin/i)).toBeInTheDocument()
      })
    })

    it('shows loading state during login', async () => {
      // Mock delayed response
      vi.mocked(require('../../services/modernApiClient').AuthAPI.login)
        .mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

      const { user } = render(<App />)

      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(loginButton)

      // Should show loading spinner
      expect(document.querySelector('.MuiCircularProgress-root')).toBeInTheDocument()
      expect(loginButton).toBeDisabled()
    })
  })

  describe('Password Visibility Toggle', () => {
    it('toggles password visibility', async () => {
      const { user } = render(<App />)

      const passwordInput = screen.getByLabelText(/şifre/i)
      const toggleButton = screen.getByLabelText(/şifreyi göster\/gizle/i)

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password')

      // Click toggle to show password
      await user.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'text')

      // Click toggle to hide password again
      await user.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'password')
    })
  })

  describe('Form Accessibility', () => {
    it('supports keyboard navigation', async () => {
      const { user } = render(<App />)

      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      // Tab navigation should work
      await user.tab()
      expect(emailInput).toHaveFocus()

      await user.tab()
      expect(passwordInput).toHaveFocus()

      await user.tab()
      expect(screen.getByLabelText(/şifreyi göster\/gizle/i)).toHaveFocus()

      await user.tab()
      expect(loginButton).toHaveFocus()
    })

    it('has proper ARIA labels', () => {
      render(<App />)

      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const toggleButton = screen.getByLabelText(/şifreyi göster\/gizle/i)
      const loginButton = screen.getByLabelText(/giriş yap/i)

      expect(emailInput).toHaveAttribute('aria-label')
      expect(passwordInput).toHaveAttribute('aria-label')
      expect(toggleButton).toHaveAttribute('aria-label')
      expect(loginButton).toHaveAttribute('aria-label')
    })
  })

  describe('Logout Flow', () => {
    it('logs out user and redirects to login', async () => {
      // Start with authenticated user
      const mockUser = {
        id: '1',
        adi: 'Test',
        soyadi: 'Öğrenci',
        email: 'test@example.com',
        rol: 'ogrenci'
      }

      localStorage.setItem('authToken', 'mock-token')

      vi.mocked(require('../../services/modernApiClient').AuthAPI.logout)
        .mockResolvedValue({ success: true })

      const { user } = render(<App />, { user: mockUser })

      // Find and click logout button (this would be in the navigation)
      const logoutButton = screen.getByText(/çıkış yap/i)
      await user.click(logoutButton)

      // Wait for logout to complete
      await waitFor(() => {
        expect(require('../../services/modernApiClient').AuthAPI.logout).toHaveBeenCalled()
      })

      // Should be redirected to login page
      await waitFor(() => {
        expect(screen.getByText(/kiro2 platform/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /giriş yap/i })).toBeInTheDocument()
      })

      // Token should be removed
      expect(localStorage.getItem('authToken')).toBeNull()
    })
  })

  describe('Auto-login on Page Refresh', () => {
    it('automatically logs in user with valid token', async () => {
      const mockUser = {
        id: '1',
        adi: 'Test',
        soyadi: 'Öğrenci',
        email: 'test@example.com',
        rol: 'ogrenci'
      }

      localStorage.setItem('authToken', 'valid-token')

      vi.mocked(require('../../services/modernApiClient').AuthAPI.getProfile)
        .mockResolvedValue({
          data: mockUser,
          success: true,
          status: 200
        })

      vi.mocked(require('../../services/modernApiClient').StudentsAPI.getDashboardData)
        .mockResolvedValue({
          data: { stats: {}, recentActivity: [] },
          success: true,
          status: 200
        })

      render(<App />)

      // Should automatically fetch profile and redirect to dashboard
      await waitFor(() => {
        expect(require('../../services/modernApiClient').AuthAPI.getProfile).toHaveBeenCalled()
      })

      await waitFor(() => {
        expect(screen.getByText(/merhaba, test/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('redirects to login with invalid token', async () => {
      localStorage.setItem('authToken', 'invalid-token')

      vi.mocked(require('../../services/modernApiClient').AuthAPI.getProfile)
        .mockRejectedValue({
          message: 'Invalid token',
          status: 401
        })

      render(<App />)

      // Should clear token and show login page
      await waitFor(() => {
        expect(localStorage.getItem('authToken')).toBeNull()
        expect(screen.getByRole('button', { name: /giriş yap/i })).toBeInTheDocument()
      })
    })
  })

  describe('Network Error Handling', () => {
    it('handles network connectivity issues gracefully', async () => {
      vi.mocked(require('../../services/modernApiClient').AuthAPI.login)
        .mockRejectedValue({
          message: 'Sunucuya bağlanılamıyor',
          status: 0
        })

      const { user } = render(<App />)

      const emailInput = screen.getByLabelText(/e-posta/i)
      const passwordInput = screen.getByLabelText(/şifre/i)
      const loginButton = screen.getByRole('button', { name: /giriş yap/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(loginButton)

      await waitFor(() => {
        expect(screen.getByText('Sunucuya bağlanılamıyor')).toBeInTheDocument()
      })
    })
  })
})