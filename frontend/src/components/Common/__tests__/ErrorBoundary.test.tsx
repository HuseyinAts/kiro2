/**
 * ErrorBoundary Component Tests
 * Comprehensive test suite for error boundary functionality
 */

import * as React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach, afterAll, beforeAll } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../../test/utils/test-utils'
import ErrorBoundary from '../ErrorBoundary'

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  AlertTriangle: () => <span data-testid="alert-icon">AlertTriangle</span>,
  Home: () => <span data-testid="home-icon">Home</span>,
  RefreshCw: () => <span data-testid="refresh-icon">RefreshCw</span>
}))

// Mock window methods
const originalLocation = window.location
const mockReload = vi.fn()
const mockHref = vi.fn()

beforeAll(() => {
  // Mock window.location
  delete (window as any).location
  window.location = {
    ...originalLocation,
    reload: mockReload,
    href: '',
    assign: mockHref
  } as unknown as Location

  Object.defineProperty(window.location, 'href', {
    set: mockHref,
    get: () => 'http://localhost:3000/test'
  })
})

afterAll(() => {
  window.location = originalLocation
})

// Component that throws an error for testing
const ThrowError: React.FC<{ error?: Error }> = ({ error }) => {
  throw error || new Error('Test error message')
}

// Component that can be toggled to throw error
const ToggleError: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Toggled error')
  }
  return <div data-testid="child-content">Content rendered successfully</div>
}

describe('ErrorBoundary', () => {
  let consoleError: ReturnType<typeof vi.spyOn>
  let consoleLogs: string[] = []

  beforeEach(() => {
    vi.clearAllMocks()
    consoleLogs = []

    // Suppress console.error for cleaner test output
    consoleError = vi.spyOn(console, 'error').mockImplementation((...args) => {
      consoleLogs.push(args.join(' '))
    })

    // Mock fetch for error reporting
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true })
    })
  })

  afterEach(() => {
    consoleError.mockRestore()
    vi.restoreAllMocks()
  })

  describe('Normal Rendering', () => {
    it('renders children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div data-testid="child">Child Content</div>
        </ErrorBoundary>
      )

      expect(screen.getByTestId('child')).toBeInTheDocument()
      expect(screen.getByText('Child Content')).toBeInTheDocument()
    })

    it('renders multiple children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div data-testid="child1">First Child</div>
          <div data-testid="child2">Second Child</div>
        </ErrorBoundary>
      )

      expect(screen.getByTestId('child1')).toBeInTheDocument()
      expect(screen.getByTestId('child2')).toBeInTheDocument()
    })

    it('does not show error UI when children render successfully', () => {
      render(
        <ErrorBoundary>
          <div>Normal Content</div>
        </ErrorBoundary>
      )

      expect(screen.queryByText(/beklenmeyen bir hata olustu/i)).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('catches error and displays error UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText(/beklenmeyen bir hata olustu/i)).toBeInTheDocument()
      expect(screen.getByText('Test error message')).toBeInTheDocument()
    })

    it('displays custom error message', () => {
      const customError = new Error('Custom error from child component')

      render(
        <ErrorBoundary>
          <ThrowError error={customError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error from child component')).toBeInTheDocument()
    })

    it('displays fallback message for unknown errors', () => {
      // Create error without message
      const errorWithoutMessage = new Error()
      errorWithoutMessage.message = ''

      render(
        <ErrorBoundary>
          <ThrowError error={errorWithoutMessage} />
        </ErrorBoundary>
      )

      // Should show default error text
      expect(screen.getByText(/bilinmeyen bir hata/i)).toBeInTheDocument()
    })

    it('logs error to console', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(consoleError).toHaveBeenCalled()
      const errorLog = consoleLogs.find(log => log.includes('ErrorBoundary caught an error'))
      expect(errorLog).toBeDefined()
    })
  })

  describe('Custom Fallback', () => {
    it('renders custom fallback when provided', () => {
      const customFallback = <div data-testid="custom-fallback">Custom Error UI</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
      expect(screen.getByText('Custom Error UI')).toBeInTheDocument()
      expect(screen.queryByText(/beklenmeyen bir hata olustu/i)).not.toBeInTheDocument()
    })
  })

  describe('Error Callback', () => {
    it('calls onError callback when error occurs', () => {
      const onError = vi.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(onError).toHaveBeenCalledTimes(1)
      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String)
        })
      )
    })

    it('passes correct error to onError callback', () => {
      const onError = vi.fn()
      const testError = new Error('Specific test error')

      render(
        <ErrorBoundary onError={onError}>
          <ThrowError error={testError} />
        </ErrorBoundary>
      )

      const [passedError] = onError.mock.calls[0]
      expect(passedError.message).toBe('Specific test error')
    })
  })

  describe('Reset Keys', () => {
    it('resets error boundary when resetKeys change', async () => {
      const { rerender } = render(
        <ErrorBoundary resetKeys={['key1']}>
          <ToggleError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Should show error UI
      expect(screen.getByText(/beklenmeyen bir hata olustu/i)).toBeInTheDocument()

      // Change reset key and render non-throwing component
      rerender(
        <ErrorBoundary resetKeys={['key2']}>
          <ToggleError shouldThrow={false} />
        </ErrorBoundary>
      )

      await waitFor(() => {
        expect(screen.getByTestId('child-content')).toBeInTheDocument()
      })
    })

    it('does not reset when resetKeys remain the same', () => {
      const { rerender } = render(
        <ErrorBoundary resetKeys={['key1']}>
          <ToggleError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/beklenmeyen bir hata olustu/i)).toBeInTheDocument()

      // Same reset keys
      rerender(
        <ErrorBoundary resetKeys={['key1']}>
          <ToggleError shouldThrow={false} />
        </ErrorBoundary>
      )

      // Should still show error
      expect(screen.getByText(/beklenmeyen bir hata olustu/i)).toBeInTheDocument()
    })
  })

  describe('Action Buttons', () => {
    it('calls window.location.reload when reload button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const reloadButton = screen.getByRole('button', { name: /sayfayi yenile/i })
      await user.click(reloadButton)

      expect(mockReload).toHaveBeenCalled()
    })

    it('navigates to home when home button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const homeButton = screen.getByRole('button', { name: /ana sayfaya don/i })
      await user.click(homeButton)

      expect(mockHref).toHaveBeenCalledWith('/')
    })

    it('displays both action buttons', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /sayfayi yenile/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /ana sayfaya don/i })).toBeInTheDocument()
    })
  })

  describe('Help Section', () => {
    it('displays help suggestions', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText(/ne yapabilirsiniz/i)).toBeInTheDocument()
      expect(screen.getByText(/sayfayi yenileyin/i)).toBeInTheDocument()
      expect(screen.getByText(/ana sayfaya donun/i)).toBeInTheDocument()
      expect(screen.getByText(/tarayici onbellegini temizleyin/i)).toBeInTheDocument()
    })
  })

  describe('Development Mode Features', () => {
    const originalEnv = process.env.NODE_ENV

    afterEach(() => {
      process.env.NODE_ENV = originalEnv
    })

    it('shows developer info in development mode', () => {
      process.env.NODE_ENV = 'development'

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText(/gelistirici bilgileri/i)).toBeInTheDocument()
    })

    it('shows reset boundary button in development mode', () => {
      process.env.NODE_ENV = 'development'

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /error boundary.*sifirla/i })).toBeInTheDocument()
    })

    it('resets boundary when reset button is clicked in development', async () => {
      process.env.NODE_ENV = 'development'
      const user = userEvent.setup()

      const { rerender } = render(
        <ErrorBoundary>
          <ToggleError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/beklenmeyen bir hata olustu/i)).toBeInTheDocument()

      const resetButton = screen.getByRole('button', { name: /error boundary.*sifirla/i })
      await user.click(resetButton)

      // Rerender with non-throwing component
      rerender(
        <ErrorBoundary>
          <ToggleError shouldThrow={false} />
        </ErrorBoundary>
      )

      await waitFor(() => {
        expect(screen.queryByText(/beklenmeyen bir hata olustu/i)).not.toBeInTheDocument()
      })
    })

    it('shows error stack in development mode', () => {
      process.env.NODE_ENV = 'development'

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText(/error stack/i)).toBeInTheDocument()
    })

    it('hides developer info in production mode', () => {
      process.env.NODE_ENV = 'production'

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.queryByText(/gelistirici bilgileri/i)).not.toBeInTheDocument()
    })
  })

  describe('Error Reporting', () => {
    it('reports error to service in production', async () => {
      process.env.NODE_ENV = 'production'

      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/errors/report',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          })
        )
      })
    })

    it('handles error reporting failure gracefully', async () => {
      process.env.NODE_ENV = 'production'
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

      // Should not throw
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      // Error UI should still be displayed
      expect(screen.getByText(/beklenmeyen bir hata olustu/i)).toBeInTheDocument()
    })
  })

  describe('UI Elements', () => {
    it('displays alert icon', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByTestId('alert-icon')).toBeInTheDocument()
    })

    it('displays home icon in button', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByTestId('home-icon')).toBeInTheDocument()
    })

    it('displays refresh icon in button', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByTestId('refresh-icon')).toBeInTheDocument()
    })

    it('displays support contact footer', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      expect(screen.getByText(/destek ekibi ile iletisime gecin/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent(/beklenmeyen bir hata olustu/i)
    })

    it('action buttons are keyboard accessible', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabindex', '-1')
      })
    })

    it('error message is marked up semantically', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )

      // Error message should be in a container that screen readers can identify
      const errorContainer = screen.getByText('Test error message').closest('div')
      expect(errorContainer).toBeInTheDocument()
    })
  })
})
