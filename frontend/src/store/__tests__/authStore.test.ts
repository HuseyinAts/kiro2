/**
 * authStore Tests
 *
 * Comprehensive tests for the Zustand authentication store.
 * Covers login, logout, refresh, role/permission checks, error handling,
 * and persist/hydration behavior.
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest'
import { act } from '@testing-library/react'
import { useAuthStore } from '../authStore'
import { authService } from '../../services/authService'
import type { User, UserRole } from '../../types'

// Mock authService
vi.mock('../../services/authService', () => ({
  authService: {
    login: vi.fn(),
    loginVerify2FA: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    validateToken: vi.fn(),
    getCurrentUser: vi.fn(),
    updateProfile: vi.fn(),
  },
}))

// Mock localStorage for persist middleware
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value }),
    removeItem: vi.fn((key: string) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
  }
})()
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

function createMockUser(overrides: Partial<User> = {}): User {
  return {
    id: 'user-1',
    email: 'test@example.com',
    ad: 'Test',
    soyad: 'User',
    rol: 'ogrenci' as UserRole,
    aktif: true,
    olusturma_tarihi: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

function resetStore(): void {
  useAuthStore.setState({
    isAuthenticated: false,
    user: null,
    loading: false,
    error: null,
  })
}

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    resetStore()
  })

  describe('Initial State', () => {
    it('should have user as null', () => {
      const { user } = useAuthStore.getState()
      expect(user).toBeNull()
    })

    it('should have isAuthenticated as false', () => {
      const { isAuthenticated } = useAuthStore.getState()
      expect(isAuthenticated).toBe(false)
    })

    it('should have error as null', () => {
      const { error } = useAuthStore.getState()
      expect(error).toBeNull()
    })

    it('should have loading as false after reset', () => {
      const { loading } = useAuthStore.getState()
      expect(loading).toBe(false)
    })
  })

  describe('Login', () => {
    it('should set user and isAuthenticated on successful login', async () => {
      const mockUser = createMockUser()
      ;(authService.login as Mock).mockResolvedValue({
        success: true,
        user: mockUser,
        token: 'tok',
        refreshToken: 'ref',
      })

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().login({
          email: 'test@example.com',
          password: 'password123',
        })
      })

      const state = useAuthStore.getState()
      expect(result!).toBe(true)
      expect(state.isAuthenticated).toBe(true)
      expect(state.user).toEqual(mockUser)
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('should set error on failed login response', async () => {
      ;(authService.login as Mock).mockResolvedValue({
        success: false,
        message: 'Hatali kimlik bilgileri',
      })

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().login({
          email: 'bad@example.com',
          password: 'wrong',
        })
      })

      const state = useAuthStore.getState()
      expect(result!).toBe(false)
      expect(state.isAuthenticated).toBe(false)
      expect(state.user).toBeNull()
      expect(state.error).toBe('Hatali kimlik bilgileri')
      expect(state.loading).toBe(false)
    })

    it('should set error when login throws an exception', async () => {
      ;(authService.login as Mock).mockRejectedValue(new Error('Network error'))

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().login({
          email: 'test@example.com',
          password: 'password123',
        })
      })

      const state = useAuthStore.getState()
      expect(result!).toBe(false)
      expect(state.error).toBe('Network error')
      expect(state.loading).toBe(false)
    })

    it('should set loading to true during login', async () => {
      let loadingDuringCall = false
      ;(authService.login as Mock).mockImplementation(async () => {
        loadingDuringCall = useAuthStore.getState().loading
        return { success: true, user: createMockUser() }
      })

      await act(async () => {
        await useAuthStore.getState().login({ email: 'a@b.com', password: 'p' })
      })

      expect(loadingDuringCall).toBe(true)
    })

    it('should use default error message when response has no message', async () => {
      ;(authService.login as Mock).mockResolvedValue({ success: false })

      await act(async () => {
        await useAuthStore.getState().login({ email: 'a@b.com', password: 'p' })
      })

      expect(useAuthStore.getState().error).toContain('ba')
    })
  })

  describe('Two-Factor Verification (S200 audit: 2FA dead-end fix)', () => {
    it('should set user and isAuthenticated on successful TOTP verification', async () => {
      const mockUser = createMockUser()
      ;(authService.loginVerify2FA as Mock).mockResolvedValue({
        success: true,
        user: mockUser,
      })

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().verifyTwoFactor('test@example.com', 'password123', '123456')
      })

      expect(authService.loginVerify2FA).toHaveBeenCalledWith('test@example.com', 'password123', '123456')
      const state = useAuthStore.getState()
      expect(result!).toBe(true)
      expect(state.isAuthenticated).toBe(true)
      expect(state.user).toEqual(mockUser)
      expect(state.error).toBeNull()
    })

    it('should set error and return false on invalid TOTP code', async () => {
      ;(authService.loginVerify2FA as Mock).mockRejectedValue(new Error('Geçersiz 2FA kodu'))

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().verifyTwoFactor('test@example.com', 'password123', '000000')
      })

      const state = useAuthStore.getState()
      expect(result!).toBe(false)
      expect(state.isAuthenticated).toBe(false)
      expect(state.error).toBe('Geçersiz 2FA kodu')
    })
  })

  describe('Logout', () => {
    it('should clear user and isAuthenticated', async () => {
      // Set up authenticated state first
      useAuthStore.setState({
        isAuthenticated: true,
        user: createMockUser(),
        loading: false,
        error: null,
      })

      ;(authService.logout as Mock).mockResolvedValue(undefined)

      await act(async () => {
        await useAuthStore.getState().logout()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.user).toBeNull()
      expect(state.loading).toBe(false)
      expect(state.error).toBeNull()
    })

    it('should call authService.logout', async () => {
      ;(authService.logout as Mock).mockResolvedValue(undefined)

      await act(async () => {
        await useAuthStore.getState().logout()
      })

      expect(authService.logout).toHaveBeenCalledOnce()
    })
  })

  describe('Refresh Auth', () => {
    it('should update user on successful refresh', async () => {
      const updatedUser = createMockUser({ ad: 'Updated' })
      ;(authService.refreshToken as Mock).mockResolvedValue({ success: true })
      ;(authService.getCurrentUser as Mock).mockResolvedValue(updatedUser)

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().refreshAuth()
      })

      expect(result!).toBe(true)
      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(true)
      expect(state.user).toEqual(updatedUser)
    })

    it('should return false on failed refresh', async () => {
      ;(authService.refreshToken as Mock).mockResolvedValue({ success: false })

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().refreshAuth()
      })

      expect(result!).toBe(false)
    })

    it('should return false when refresh throws', async () => {
      ;(authService.refreshToken as Mock).mockRejectedValue(new Error('fail'))

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().refreshAuth()
      })

      expect(result!).toBe(false)
    })
  })

  describe('Role Checking - hasRole', () => {
    it('should return true when user has the specified role', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogretmen' }) })
      expect(useAuthStore.getState().hasRole('ogretmen')).toBe(true)
    })

    it('should return false when user has a different role', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogrenci' }) })
      expect(useAuthStore.getState().hasRole('admin')).toBe(false)
    })

    it('should return false when user is null', () => {
      useAuthStore.setState({ user: null })
      expect(useAuthStore.getState().hasRole('ogrenci')).toBe(false)
    })
  })

  describe('Permission Checking - hasPermission', () => {
    it('should grant admin all permissions', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'admin' }) })
      expect(useAuthStore.getState().hasPermission('anything', 'anything')).toBe(true)
    })

    it('should allow ogrenci to read dashboard', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogrenci' }) })
      expect(useAuthStore.getState().hasPermission('dashboard', 'read')).toBe(true)
    })

    it('should deny ogrenci access to students resource', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogrenci' }) })
      expect(useAuthStore.getState().hasPermission('students', 'read')).toBe(false)
    })

    it('should allow ogretmen to update exam', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogretmen' }) })
      expect(useAuthStore.getState().hasPermission('exam', 'update')).toBe(true)
    })

    it('should allow veli to read child-progress', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'veli' }) })
      expect(useAuthStore.getState().hasPermission('child-progress', 'read')).toBe(true)
    })

    it('should return false when user is null', () => {
      useAuthStore.setState({ user: null })
      expect(useAuthStore.getState().hasPermission('dashboard', 'read')).toBe(false)
    })
  })

  describe('Authorization - isAuthorized', () => {
    it('should return true when user role is in required roles', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogretmen' }) })
      expect(useAuthStore.getState().isAuthorized(['ogretmen', 'admin'])).toBe(true)
    })

    it('should return false when user role is not in required roles', () => {
      useAuthStore.setState({ user: createMockUser({ rol: 'ogrenci' }) })
      expect(useAuthStore.getState().isAuthorized(['ogretmen', 'admin'])).toBe(false)
    })

    it('should return false when user is null', () => {
      useAuthStore.setState({ user: null })
      expect(useAuthStore.getState().isAuthorized(['ogrenci'])).toBe(false)
    })
  })

  describe('Register', () => {
    it('should auto-login after successful registration', async () => {
      const mockUser = createMockUser()
      ;(authService.register as Mock).mockResolvedValue({ success: true })
      ;(authService.login as Mock).mockResolvedValue({
        success: true,
        user: mockUser,
      })

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().register({
          email: 'new@example.com',
          password: 'pass123',
          ad: 'New',
          soyad: 'User',
          rol: 'ogrenci',
        })
      })

      expect(result!).toBe(true)
      expect(authService.login).toHaveBeenCalledWith({
        email: 'new@example.com',
        password: 'pass123',
      })
      expect(useAuthStore.getState().isAuthenticated).toBe(true)
    })

    it('kayit BASARILI ama otomatik giris ENGELLENDI: false DEGIL, sebep doner', async () => {
      // MUTASYON BOSLUGU (26 Agu 2026): `return loginResult === true` katlamasini
      // geri getirmek ModernRegisterPage testlerinin HICBIRINI dusurmuyordu --
      // o testler store'u `vi.mock`'luyor, yani SOZLESMEYI hic olcmuyorlar.
      // Yuk tasiyan yer burasi.
      //
      // Gercek senaryo: EPOSTA_DOGRULAMA_ZORUNLU acikken kayit 201 doner (hesap
      // OLUSUR) ama otomatik giris 403 EPOSTA_DOGRULANMAMIS alir. Bunu "kayit
      // basarisiz" saymak ekrani SESSIZ birakiyordu.
      ;(authService.register as Mock).mockResolvedValue({ success: true })
      ;(authService.login as Mock).mockResolvedValue({
        success: false,
        message: 'Giris yapabilmek icin e-posta adresinizi dogrulayin.',
      })

      let result: unknown
      await act(async () => {
        result = await useAuthStore.getState().register({
          email: 'dogrulanmamis@example.com',
          password: 'pass123', // pragma: allowlist secret
          ad: 'Dogrulanmamis',
          soyad: 'User',
          rol: 'ogrenci',
        })
      })

      expect(result).not.toBe(false)
      expect(result).toMatchObject({ kayitOldu: true })
      expect((result as { girisEngellendi: string | null }).girisEngellendi).toBe(
        'Giris yapabilmek icin e-posta adresinizi dogrulayin.',
      )
      // KONTROL KOLU: hesap olustu ama kullanici GIRMIS sayilmamali.
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
    })

    it('kayit BASARISIZ ise hala duz false doner (geriye uyum)', async () => {
      // Sozlesme GENISLETILDI, kirilmadi: cagiranin `=== true` ve dogrudan
      // falsy kontrolleri calismaya devam etmeli.
      ;(authService.register as Mock).mockResolvedValue({ success: false })

      let result: unknown
      await act(async () => {
        result = await useAuthStore.getState().register({
          email: 'dup@example.com',
          password: 'pass123', // pragma: allowlist secret
          ad: 'Dup',
          soyad: 'User',
          rol: 'ogrenci',
        })
      })

      expect(result).toBe(false)
      expect(authService.login).not.toHaveBeenCalled()
    })

    it('should set error on failed registration', async () => {
      ;(authService.register as Mock).mockResolvedValue({
        success: false,
        message: 'Email zaten kayitli',
      })

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().register({
          email: 'dup@example.com',
          password: 'pass123',
          ad: 'Dup',
          soyad: 'User',
          rol: 'ogrenci',
        })
      })

      expect(result!).toBe(false)
      expect(useAuthStore.getState().error).toBe('Email zaten kayitli')
    })

    it('should handle register exception', async () => {
      ;(authService.register as Mock).mockRejectedValue(new Error('Server down'))

      let result: boolean
      await act(async () => {
        result = await useAuthStore.getState().register({
          email: 'x@x.com',
          password: 'p',
          ad: 'X',
          soyad: 'Y',
          rol: 'ogrenci',
        })
      })

      expect(result!).toBe(false)
      expect(useAuthStore.getState().error).toBe('Server down')
    })
  })

  describe('Update Profile', () => {
    it('should update user in state on success', async () => {
      const updatedUser = createMockUser({ ad: 'Updated' })
      ;(authService.updateProfile as Mock).mockResolvedValue({
        success: true,
        user: updatedUser,
      })

      useAuthStore.setState({ user: createMockUser() })

      await act(async () => {
        await useAuthStore.getState().updateProfile({ ad: 'Updated' })
      })

      expect(useAuthStore.getState().user?.ad).toBe('Updated')
    })

    it('should throw on failed profile update', async () => {
      ;(authService.updateProfile as Mock).mockResolvedValue({ success: false })

      await expect(
        useAuthStore.getState().updateProfile({ ad: 'Fail' })
      ).rejects.toThrow()
    })
  })

  describe('State Setters', () => {
    it('setLoading should update loading state', () => {
      act(() => { useAuthStore.getState().setLoading(true) })
      expect(useAuthStore.getState().loading).toBe(true)

      act(() => { useAuthStore.getState().setLoading(false) })
      expect(useAuthStore.getState().loading).toBe(false)
    })

    it('setError should update error state', () => {
      act(() => { useAuthStore.getState().setError('Something went wrong') })
      expect(useAuthStore.getState().error).toBe('Something went wrong')

      act(() => { useAuthStore.getState().setError(null) })
      expect(useAuthStore.getState().error).toBeNull()
    })
  })

  describe('Initialize Auth', () => {
    it('should set authenticated state when token is valid', async () => {
      const mockUser = createMockUser()
      ;(authService.validateToken as Mock).mockResolvedValue(true)
      ;(authService.getCurrentUser as Mock).mockResolvedValue(mockUser)

      await act(async () => {
        await useAuthStore.getState().initializeAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(true)
      expect(state.user).toEqual(mockUser)
      expect(state.loading).toBe(false)
    })

    it('should attempt refresh when token is invalid', async () => {
      ;(authService.validateToken as Mock).mockResolvedValue(false)
      ;(authService.refreshToken as Mock).mockResolvedValue({ success: false })

      await act(async () => {
        await useAuthStore.getState().initializeAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.user).toBeNull()
      expect(authService.refreshToken).toHaveBeenCalled()
    })

    it('should clear state on initialization error', async () => {
      ;(authService.validateToken as Mock).mockRejectedValue(new Error('Network'))

      await act(async () => {
        await useAuthStore.getState().initializeAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.user).toBeNull()
      expect(state.error).toBeNull() // no error shown on init
    })
  })

  describe('Persist Middleware', () => {
    it('should only persist user and isAuthenticated (partialize)', () => {
      const mockUser = createMockUser()
      useAuthStore.setState({
        isAuthenticated: true,
        user: mockUser,
        loading: true,
        error: 'some error',
      })

      // Check that persist was called - the store name should be 'auth-storage'
      const calls = localStorageMock.setItem.mock.calls
      const authStorageCall = calls.find(
        (c: [string, string]) => c[0] === 'auth-storage'
      )

      if (authStorageCall) {
        const stored = JSON.parse(authStorageCall[1])
        // partialize should only include user and isAuthenticated
        expect(stored.state).toHaveProperty('user')
        expect(stored.state).toHaveProperty('isAuthenticated')
        expect(stored.state).not.toHaveProperty('loading')
        expect(stored.state).not.toHaveProperty('error')
      }
    })
  })
})
