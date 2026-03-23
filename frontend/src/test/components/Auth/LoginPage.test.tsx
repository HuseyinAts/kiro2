/**
 * Teknofest 2025 Egitim Eylemci Platformu
 * LoginPage Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../utils/test-utils'
import LoginPage from '../../../pages/ModernLoginPage'

const { loginMock } = vi.hoisted(() => ({
  loginMock: vi.fn(),
}))

vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    login: loginMock,
    isAuthenticated: false,
    user: null,
  }),
}))

describe('LoginPage', () => {
  beforeEach(() => {
    loginMock.mockReset()
  })

  it('renders login form correctly', () => {
    render(<LoginPage />)

    expect(screen.getByRole('heading', { name: /giri/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/posta/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/ifre/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /giri/i })).toBeInTheDocument()
    expect(screen.getByText(/hesab/i)).toBeInTheDocument()
    expect(screen.getByText(/kayit/i)).toBeInTheDocument()
  })

  it('shows validation error for empty fields', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: /giri/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/alanlar/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid credentials', async () => {
    const user = userEvent.setup()
    loginMock.mockResolvedValue(true)

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/posta/i)
    const passwordInput = screen.getByLabelText(/ifre/i)
    const submitButton = screen.getByRole('button', { name: /giri/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(submitButton)

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'SecurePass123!',
      })
    })
  })

  it('shows error message for invalid credentials', async () => {
    const user = userEvent.setup()
    loginMock.mockResolvedValue(false)

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/posta/i)
    const passwordInput = screen.getByLabelText(/ifre/i)
    const submitButton = screen.getByRole('button', { name: /giri/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'WrongPassword')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/hatal/i)).toBeInTheDocument()
    })
  })

  it('shows loading state during form submission', async () => {
    const user = userEvent.setup()
    loginMock.mockImplementation(() => new Promise(() => {}))

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/posta/i)
    const passwordInput = screen.getByLabelText(/ifre/i)
    const submitButton = screen.getByRole('button', { name: /giri/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(submitButton)

    expect(screen.getByText(/leniyor/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })

  it('handles login errors gracefully', async () => {
    const user = userEvent.setup()
    loginMock.mockRejectedValue(new Error('Network error'))

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/posta/i)
    const passwordInput = screen.getByLabelText(/ifre/i)
    const submitButton = screen.getByRole('button', { name: /giri/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/hata/i)).toBeInTheDocument()
    })
  })

  it('shows register and forgot password links', () => {
    render(<LoginPage />)

    expect(screen.getByText(/kayit/i)).toBeInTheDocument()
    expect(screen.getByText(/sifremi/i)).toBeInTheDocument()
  })
})
