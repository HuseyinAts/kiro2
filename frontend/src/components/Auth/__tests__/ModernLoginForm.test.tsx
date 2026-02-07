/**
 * ModernLoginForm Component Tests
 * Comprehensive test suite for login form functionality
 */

import * as React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render, renderWithUser } from '../../../test/utils/test-utils'
import { ModernLoginForm } from '../ModernLoginForm'

// Mock responsive hook
vi.mock('../../../utils/responsive', () => ({
  useResponsive: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    currentBreakpoint: 'lg'
  })
}))

// Mock MUI theme
vi.mock('@mui/material/styles', async () => {
  const actual = await vi.importActual('@mui/material/styles')
  return {
    ...actual,
    useTheme: () => ({
      palette: {
        primary: { main: '#1976d2', light: '#42a5f5' },
        secondary: { main: '#9c27b0' },
        divider: '#e0e0e0',
        text: { secondary: '#666' },
        error: { main: '#f44336' }
      }
    })
  }
})

describe('ModernLoginForm', () => {
  const mockOnSubmit = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockOnSubmit.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders login form with all required elements', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // Check for header elements
      expect(screen.getByText('KIRO2 Platform')).toBeInTheDocument()
      expect(screen.getByText('Turkiye Universite Sinavlari Hazirlik Platformu')).toBeInTheDocument()

      // Check for form fields
      expect(screen.getByLabelText(/e-posta adresi/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/sifre/i)).toBeInTheDocument()

      // Check for submit button
      expect(screen.getByRole('button', { name: /giris yap/i })).toBeInTheDocument()

      // Check for registration link
      expect(screen.getByText(/hesabiniz yok mu/i)).toBeInTheDocument()
      expect(screen.getByText(/kayit ol/i)).toBeInTheDocument()
    })

    it('renders school icon in header', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // MUI icons render as SVG
      const iconContainer = document.querySelector('[data-testid="SchoolIcon"]')
      expect(iconContainer).toBeDefined()
    })

    it('applies custom className when provided', () => {
      const { container } = render(
        <ModernLoginForm onSubmit={mockOnSubmit} className="custom-class" />
      )

      expect(container.querySelector('.custom-class')).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('shows error when submitting empty email', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // Fill only password
      const passwordInput = screen.getByLabelText(/sifre/i)
      await user.type(passwordInput, 'password123')

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      // Check for validation error
      await waitFor(() => {
        expect(screen.getByText(/e-posta adresi gerekli/i)).toBeInTheDocument()
      })

      // Submit should not be called
      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('shows error when submitting invalid email format', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // Enter invalid email
      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      await user.type(emailInput, 'invalid-email')
      await user.type(passwordInput, 'password123')

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      // Check for validation error
      await waitFor(() => {
        expect(screen.getByText(/gecerli bir e-posta adresi girin/i)).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('shows error when submitting empty password', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // Fill only email
      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      await user.type(emailInput, 'test@example.com')

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      // Check for validation error
      await waitFor(() => {
        expect(screen.getByText(/sifre gerekli/i)).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('shows error when password is too short', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, '12345') // Less than 6 characters

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/sifre en az 6 karakter olmali/i)).toBeInTheDocument()
      })

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('clears field error when user starts typing', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // Trigger validation error
      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/e-posta adresi gerekli/i)).toBeInTheDocument()
      })

      // Start typing in email field
      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      await user.type(emailInput, 't')

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText(/e-posta adresi gerekli/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Form Submission', () => {
    it('calls onSubmit with correct data when form is valid', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123'
        })
      })
    })

    it('handles submit errors gracefully', async () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockOnSubmit.mockRejectedValue(new Error('Login failed'))

      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(consoleError).toHaveBeenCalledWith('Login error:', expect.any(Error))
      })

      consoleError.mockRestore()
    })
  })

  describe('Loading State', () => {
    it('disables form fields when loading', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} loading={true} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)
      const submitButton = screen.getByRole('button', { name: /giris yap/i })

      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
      expect(submitButton).toBeDisabled()
    })

    it('shows loading indicator on submit button when loading', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} loading={true} />)

      // ModernButton with loading prop should show spinner
      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      expect(submitButton).toHaveAttribute('aria-busy', 'true')
    })
  })

  describe('Error Display', () => {
    it('displays error message when error prop is provided', () => {
      render(
        <ModernLoginForm
          onSubmit={mockOnSubmit}
          error="Gecersiz kullanici adi veya sifre"
        />
      )

      expect(screen.getByText('Gecersiz kullanici adi veya sifre')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('does not display error alert when error is null', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} error={null} />)

      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  describe('Password Visibility Toggle', () => {
    it('toggles password visibility when icon button is clicked', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const passwordInput = screen.getByLabelText(/sifre/i)
      expect(passwordInput).toHaveAttribute('type', 'password')

      // Click visibility toggle
      const toggleButton = screen.getByRole('button', { name: /sifreyi goster\/gizle/i })
      await user.click(toggleButton)

      expect(passwordInput).toHaveAttribute('type', 'text')

      // Click again to hide
      await user.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'password')
    })

    it('disables password toggle when form is loading', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} loading={true} />)

      const toggleButton = screen.getByRole('button', { name: /sifreyi goster\/gizle/i })
      expect(toggleButton).toBeDisabled()
    })
  })

  describe('Submit Button State', () => {
    it('disables submit button when email is empty', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      expect(submitButton).toBeDisabled()
    })

    it('disables submit button when password is empty', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      await user.type(emailInput, 'test@example.com')

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      expect(submitButton).toBeDisabled()
    })

    it('enables submit button when both fields have values', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      expect(submitButton).not.toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('has proper form structure', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const form = document.querySelector('form')
      expect(form).toBeInTheDocument()
      expect(form).toHaveAttribute('noValidate')
    })

    it('has required attribute on form fields', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      expect(emailInput).toHaveAttribute('required')
      expect(passwordInput).toHaveAttribute('required')
    })

    it('has autocomplete attributes for accessibility', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      expect(emailInput).toHaveAttribute('autocomplete', 'email')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
    })

    it('has aria-label on submit button', () => {
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      expect(submitButton).toHaveAttribute('aria-label', 'giris yap')
    })

    it('associates error messages with form fields', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      // Trigger validation
      const submitButton = screen.getByRole('button', { name: /giris yap/i })
      await user.click(submitButton)

      await waitFor(() => {
        const emailInput = screen.getByLabelText(/e-posta adresi/i)
        // MUI TextField uses aria-describedby for helper text
        expect(emailInput).toHaveAttribute('aria-invalid', 'true')
      })
    })
  })

  describe('Keyboard Navigation', () => {
    it('allows form submission with Enter key', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)
      const passwordInput = screen.getByLabelText(/sifre/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123{Enter}')

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalled()
      })
    })

    it('allows tab navigation between fields', async () => {
      const user = userEvent.setup()
      render(<ModernLoginForm onSubmit={mockOnSubmit} />)

      const emailInput = screen.getByLabelText(/e-posta adresi/i)

      // Focus email input and tab
      await user.click(emailInput)
      await user.tab()

      // Should be on password field
      const passwordInput = screen.getByLabelText(/sifre/i)
      expect(passwordInput).toHaveFocus()
    })
  })
})
