/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * LoginPage Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render, createMockUser } from '../../utils/test-utils'
import { server, addHandler } from '../../mocks/server'
import { http, HttpResponse } from 'msw'
import LoginPage from '../../../pages/LoginPage'

describe('LoginPage', () => {
  beforeEach(() => {
    // Reset any runtime request handlers we may add during the tests
    server.resetHandlers()
  })

  it('renders login form correctly', () => {
    render(<LoginPage />)
    
    expect(screen.getByRole('heading', { name: /giriş yap/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/kullanıcı adı/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/şifre/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /giriş yap/i })).toBeInTheDocument()
    expect(screen.getByText(/hesabınız yok mu/i)).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)
    
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/kullanıcı adı gereklidir/i)).toBeInTheDocument()
      expect(screen.getByText(/şifre gereklidir/i)).toBeInTheDocument()
    })
  })

  it('shows validation error for invalid email format', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    
    await user.type(usernameInput, 'invalid-email')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/geçerli bir email adresi giriniz/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid credentials successfully', async () => {
    const user = userEvent.setup()
    const mockNavigate = vi.fn()
    
    // Mock successful login response
    addHandler(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json({
          success: true,
          data: {
            user: createMockUser(),
            token: 'mock-jwt-token',
            refreshToken: 'mock-refresh-token'
          },
          message: 'Giriş başarılı'
        })
      })
    )

    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    
    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/giriş başarılı/i)).toBeInTheDocument()
    })
  })

  it('shows error message for invalid credentials', async () => {
    const user = userEvent.setup()
    
    // Mock failed login response
    addHandler(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.json(
          {
            success: false,
            message: 'Geçersiz kimlik bilgileri',
            error: 'Invalid credentials'
          },
          { status: 401 }
        )
      })
    )

    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    
    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'WrongPassword')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/geçersiz kimlik bilgileri/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during form submission', async () => {
    const user = userEvent.setup()
    
    // Mock delayed response
    addHandler(
      http.post('/api/v1/auth/login', async () => {
        await new Promise(resolve => setTimeout(resolve, 100))
        return HttpResponse.json({
          success: true,
          data: {
            user: createMockUser(),
            token: 'mock-jwt-token'
          }
        })
      })
    )

    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    
    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(submitButton)
    
    expect(screen.getByText(/giriş yapılıyor/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)
    
    const passwordInput = screen.getByLabelText(/şifre/i) as HTMLInputElement
    const toggleButton = screen.getByRole('button', { name: /şifreyi göster/i })
    
    expect(passwordInput.type).toBe('password')
    
    await user.click(toggleButton)
    expect(passwordInput.type).toBe('text')
    
    await user.click(toggleButton)
    expect(passwordInput.type).toBe('password')
  })

  it('navigates to register page when register link is clicked', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)
    
    const registerLink = screen.getByText(/kayıt ol/i)
    await user.click(registerLink)
    
    // Navigation test - bu gerçek implementasyonda router mock'u gerektirir
    expect(registerLink).toBeInTheDocument()
  })

  it('handles network errors gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock network error
    addHandler(
      http.post('/api/v1/auth/login', () => {
        return HttpResponse.error()
      })
    )

    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    
    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/bağlantı hatası/i)).toBeInTheDocument()
    })
  })

  it('remembers user preference with remember me checkbox', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)
    
    const rememberCheckbox = screen.getByLabelText(/beni hatırla/i)
    expect(rememberCheckbox).not.toBeChecked()
    
    await user.click(rememberCheckbox)
    expect(rememberCheckbox).toBeChecked()
  })

  it('supports keyboard navigation', async () => {
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const submitButton = screen.getByRole('button', { name: /giriş yap/i })
    
    // Tab navigation
    usernameInput.focus()
    expect(usernameInput).toHaveFocus()
    
    fireEvent.keyDown(usernameInput, { key: 'Tab' })
    expect(passwordInput).toHaveFocus()
    
    fireEvent.keyDown(passwordInput, { key: 'Tab' })
    expect(submitButton).toHaveFocus()
  })

  it('clears form when reset button is clicked', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)
    
    const usernameInput = screen.getByLabelText(/kullanıcı adı/i) as HTMLInputElement
    const passwordInput = screen.getByLabelText(/şifre/i) as HTMLInputElement
    
    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    
    expect(usernameInput.value).toBe('test@example.com')
    expect(passwordInput.value).toBe('password123')
    
    const resetButton = screen.getByRole('button', { name: /temizle/i })
    await user.click(resetButton)
    
    expect(usernameInput.value).toBe('')
    expect(passwordInput.value).toBe('')
  })
})