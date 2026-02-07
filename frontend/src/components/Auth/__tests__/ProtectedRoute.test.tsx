import * as React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ProtectedRoute } from '../ProtectedRoute'
import { AuthProvider } from '../../../context/AuthProvider'
import { UserRole } from '../../../types'
import { vi } from 'vitest';

// Mock useAuthStore hook
const mockUseAuthStore: {
  isAuthenticated: boolean;
  user: any;
  loading: boolean;
  hasPermission: ReturnType<typeof vi.fn>;
  isAuthorized: ReturnType<typeof vi.fn>;
} = {
  isAuthenticated: false,
  user: null,
  loading: false,
  hasPermission: vi.fn(),
  isAuthorized: vi.fn()
}

vi.mock('../../../store/authStore', () => ({
  useAuthStore: () => mockUseAuthStore
}))

const TestComponent = () => <div>Protected Content</div>

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading when auth is loading', () => {
    mockUseAuthStore.loading = true

    renderWithRouter(
      <ProtectedRoute>
        <TestComponent />
      </ProtectedRoute>
    )

    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuthStore.loading = false
    mockUseAuthStore.isAuthenticated = false

    renderWithRouter(
      <ProtectedRoute>
        <TestComponent />
      </ProtectedRoute>
    )

    // Should redirect to login (tested via navigation)
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('shows content when authenticated and authorized', () => {
    mockUseAuthStore.loading = false
    mockUseAuthStore.isAuthenticated = true
    mockUseAuthStore.user = {
      id: '1',
      email: 'test@test.com',
      ad: 'Test',
      soyad: 'User',
      rol: 'ogrenci' as UserRole,
      aktif: true,
      olusturma_tarihi: '2024-01-01'
    }
    mockUseAuthStore.isAuthorized.mockReturnValue(true)

    renderWithRouter(
      <ProtectedRoute requiredRoles={['ogrenci']}>
        <TestComponent />
      </ProtectedRoute>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('shows unauthorized message when showUnauthorized is true', () => {
    mockUseAuthStore.loading = false
    mockUseAuthStore.isAuthenticated = true
    mockUseAuthStore.user = {
      id: '1',
      email: 'test@test.com',
      ad: 'Test',
      soyad: 'User',
      rol: 'ogrenci' as UserRole,
      aktif: true,
      olusturma_tarihi: '2024-01-01'
    }
    mockUseAuthStore.isAuthorized.mockReturnValue(false)

    renderWithRouter(
      <ProtectedRoute requiredRoles={['admin']} showUnauthorized={true}>
        <TestComponent />
      </ProtectedRoute>
    )

    expect(screen.getByText(/Bu sayfaya erişim yetkiniz bulunmamaktadır/)).toBeInTheDocument()
  })

  it('checks permissions when requiredPermissions is provided', () => {
    mockUseAuthStore.loading = false
    mockUseAuthStore.isAuthenticated = true
    mockUseAuthStore.user = {
      id: '1',
      email: 'test@test.com',
      ad: 'Test',
      soyad: 'User',
      rol: 'ogrenci' as UserRole,
      aktif: true,
      olusturma_tarihi: '2024-01-01'
    }
    mockUseAuthStore.isAuthorized.mockReturnValue(true)
    mockUseAuthStore.hasPermission.mockReturnValue(true)

    renderWithRouter(
      <ProtectedRoute
        requiredRoles={['ogrenci']}
        requiredPermissions={[{ resource: 'exam', action: 'read' }]}
      >
        <TestComponent />
      </ProtectedRoute>
    )

    expect(mockUseAuthStore.hasPermission).toHaveBeenCalledWith('exam', 'read')
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})