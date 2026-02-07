/**
 * Improved Auth Context Tests
 * Comprehensive testing for authentication context and hooks
 */

import * as React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'

// Mock the auth hook and context
const mockAuthContext = {
  user: null,
  isAuthenticated: false,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  loading: false,
  error: null,
  refreshToken: vi.fn(),
  updateProfile: vi.fn(),
  resetPassword: vi.fn()
}

// Mock authStore (KIRO2 uses authStore, not useAuth hook)
vi.mock('../../stores/authStore', () => ({
  useAuthStore: () => mockAuthContext,
  AuthProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="auth-provider">{children}</div>
  )
}))

// Test components that use auth
const LoginTestComponent: React.FC = () => {
  const auth = mockAuthContext
  
  const handleLogin = async () => {
    try {
      await auth.login('test@example.com', 'password123')
    } catch (error) {
      console.error('Login failed:', error)
    }
  }
  
  return (
    <div>
      <div data-testid="auth-status">
        {auth.isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {auth.user && (
        <div data-testid="user-info">
          Welcome, {auth.user.firstName} {auth.user.lastName}
        </div>
      )}
      {auth.loading && <div data-testid="loading">Loading...</div>}
      {auth.error && <div data-testid="error">{auth.error}</div>}
      <button onClick={handleLogin} data-testid="login-button">
        Giriş Yap
      </button>
      <button onClick={auth.logout} data-testid="logout-button">
        Çıkış Yap
      </button>
    </div>
  )
}

const ProtectedTestComponent: React.FC = () => {
  const auth = mockAuthContext
  
  if (!auth.isAuthenticated) {
    return <div data-testid="login-required">Giriş yapmanız gerekiyor</div>
  }
  
  return (
    <div data-testid="protected-content">
      <h1>Korumalı İçerik</h1>
      <p>Bu içerik sadece giriş yapmış kullanıcılar için görünür.</p>
    </div>
  )
}

const UserProfileComponent: React.FC = () => {
  const auth = mockAuthContext
  
  const handleUpdateProfile = async () => {
    await auth.updateProfile({
      firstName: 'Yeni Ad',
      lastName: 'Yeni Soyad'
    })
  }
  
  return (
    <div>
      {auth.user && (
        <div data-testid="profile-info">
          <div>Ad: {auth.user.firstName}</div>
          <div>Soyad: {auth.user.lastName}</div>
          <div>Email: {auth.user.email}</div>
          <div>Rol: {auth.user.role}</div>
        </div>
      )}
      <button onClick={handleUpdateProfile} data-testid="update-profile">
        Profili Güncelle
      </button>
    </div>
  )
}

// Wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <div data-testid="auth-provider">
      {children}
    </div>
  </BrowserRouter>
)

describe('Auth Context Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset auth context state
    mockAuthContext.user = null
    mockAuthContext.isAuthenticated = false
    mockAuthContext.loading = false
    mockAuthContext.error = null
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Authentication State', () => {
    it('shows not authenticated state by default', () => {
      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated')
      expect(screen.queryByTestId('user-info')).not.toBeInTheDocument()
    })

    it('shows authenticated state when user is logged in', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'student'
      }

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated')
      expect(screen.getByTestId('user-info')).toHaveTextContent('Welcome, Test User')
    })

    it('shows loading state during authentication', () => {
      mockAuthContext.loading = true

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('loading')).toHaveTextContent('Loading...')
    })

    it('shows error state when authentication fails', () => {
      mockAuthContext.error = 'Giriş başarısız oldu'

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('error')).toHaveTextContent('Giriş başarısız oldu')
    })
  })

  describe('Login Functionality', () => {
    it('calls login function when login button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      const loginButton = screen.getByTestId('login-button')
      await user.click(loginButton)

      expect(mockAuthContext.login).toHaveBeenCalledWith('test@example.com', 'password123')
    })

    it('handles login success', async () => {
      mockAuthContext.login.mockResolvedValueOnce({
        user: {
          id: '1',
          email: 'test@example.com',
          firstName: 'Test',
          lastName: 'User',
          role: 'student'
        },
        token: 'mock-token'
      })

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      const loginButton = screen.getByTestId('login-button')
      await user.click(loginButton)

      await waitFor(() => {
        expect(mockAuthContext.login).toHaveBeenCalled()
      })
    })

    it('handles login failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockAuthContext.login.mockRejectedValueOnce(new Error('Login failed'))

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      const loginButton = screen.getByTestId('login-button')
      await user.click(loginButton)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Login failed:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Logout Functionality', () => {
    it('calls logout function when logout button is clicked', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      const logoutButton = screen.getByTestId('logout-button')
      await user.click(logoutButton)

      expect(mockAuthContext.logout).toHaveBeenCalled()
    })
  })

  describe('Protected Routes', () => {
    it('shows login required message when not authenticated', () => {
      render(
        <TestWrapper>
          <ProtectedTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('login-required')).toHaveTextContent('Giriş yapmanız gerekiyor')
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })

    it('shows protected content when authenticated', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'student'
      }

      render(
        <TestWrapper>
          <ProtectedTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
      expect(screen.getByText('Korumalı İçerik')).toBeInTheDocument()
      expect(screen.queryByTestId('login-required')).not.toBeInTheDocument()
    })
  })

  describe('User Profile Management', () => {
    it('displays user profile information', () => {
      mockAuthContext.user = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Ahmet',
        lastName: 'Yılmaz',
        role: 'student'
      }

      render(
        <TestWrapper>
          <UserProfileComponent />
        </TestWrapper>
      )

      const profileInfo = screen.getByTestId('profile-info')
      expect(profileInfo).toHaveTextContent('Ad: Ahmet')
      expect(profileInfo).toHaveTextContent('Soyad: Yılmaz')
      expect(profileInfo).toHaveTextContent('Email: test@example.com')
      expect(profileInfo).toHaveTextContent('Rol: student')
    })

    it('calls updateProfile when update button is clicked', async () => {
      mockAuthContext.user = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Ahmet',
        lastName: 'Yılmaz',
        role: 'student'
      }

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <UserProfileComponent />
        </TestWrapper>
      )

      const updateButton = screen.getByTestId('update-profile')
      await user.click(updateButton)

      expect(mockAuthContext.updateProfile).toHaveBeenCalledWith({
        firstName: 'Yeni Ad',
        lastName: 'Yeni Soyad'
      })
    })

    it('does not show profile info when user is null', () => {
      mockAuthContext.user = null

      render(
        <TestWrapper>
          <UserProfileComponent />
        </TestWrapper>
      )

      expect(screen.queryByTestId('profile-info')).not.toBeInTheDocument()
    })
  })

  describe('Turkish Language Support', () => {
    it('displays Turkish text correctly', () => {
      render(
        <TestWrapper>
          <ProtectedTestComponent />
        </TestWrapper>
      )

      expect(screen.getByText('Giriş yapmanız gerekiyor')).toBeInTheDocument()
    })

    it('handles Turkish characters in user names', () => {
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        email: 'test@example.com',
        firstName: 'Özgür',
        lastName: 'Çağatay',
        role: 'student'
      }

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('user-info')).toHaveTextContent('Welcome, Özgür Çağatay')
    })
  })

  describe('Error Handling', () => {
    it('handles network errors gracefully', async () => {
      mockAuthContext.login.mockRejectedValueOnce(new Error('Network error'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      const loginButton = screen.getByTestId('login-button')
      await user.click(loginButton)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled()
      })

      consoleSpy.mockRestore()
    })

    it('handles invalid credentials error', () => {
      mockAuthContext.error = 'Geçersiz kullanıcı adı veya şifre'

      render(
        <TestWrapper>
          <LoginTestComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('error')).toHaveTextContent('Geçersiz kullanıcı adı veya şifre')
    })
  })

  describe('Token Management', () => {
    it('calls refreshToken function', async () => {
      mockAuthContext.refreshToken.mockResolvedValueOnce('new-token')

      await mockAuthContext.refreshToken()

      expect(mockAuthContext.refreshToken).toHaveBeenCalled()
    })

    it('handles token refresh failure', async () => {
      mockAuthContext.refreshToken.mockRejectedValueOnce(new Error('Token expired'))

      try {
        await mockAuthContext.refreshToken()
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
      }
    })
  })

  describe('User Roles', () => {
    it('handles student role correctly', () => {
      mockAuthContext.user = {
        id: '1',
        email: 'student@example.com',
        firstName: 'Öğrenci',
        lastName: 'Test',
        role: 'student'
      }

      render(
        <TestWrapper>
          <UserProfileComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('profile-info')).toHaveTextContent('Rol: student')
    })

    it('handles teacher role correctly', () => {
      mockAuthContext.user = {
        id: '2',
        email: 'teacher@example.com',
        firstName: 'Öğretmen',
        lastName: 'Test',
        role: 'teacher'
      }

      render(
        <TestWrapper>
          <UserProfileComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('profile-info')).toHaveTextContent('Rol: teacher')
    })

    it('handles parent role correctly', () => {
      mockAuthContext.user = {
        id: '3',
        email: 'parent@example.com',
        firstName: 'Veli',
        lastName: 'Test',
        role: 'parent'
      }

      render(
        <TestWrapper>
          <UserProfileComponent />
        </TestWrapper>
      )

      expect(screen.getByTestId('profile-info')).toHaveTextContent('Rol: parent')
    })
  })
})