import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock apiRequest before importing authService
const mockApiRequest = vi.fn()
vi.mock('../../utils/apiHelpers', () => ({
  apiRequest: (...args: unknown[]) => mockApiRequest(...args),
}))

// Import after mock setup
const { authService } = await import('../authService')

// Test fixtures
const mockUser = {
  id: 'user-123',
  email: 'ogrenci@example.com',
  ad: 'Ali',
  soyad: 'Yilmaz',
  rol: 'ogrenci' as const,
  aktif: true,
  olusturma_tarihi: '2025-01-01T00:00:00Z',
}

describe('AuthService', () => {
  beforeEach(() => {
    mockApiRequest.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ─── Login ───────────────────────────────────────────────

  describe('login', () => {
    const credentials = { email: 'ogrenci@example.com', password: 'Sifre123!' }

    it('should return LoginResponse on successful login', async () => {
      const loginResponse = {
        success: true,
        user: mockUser,
        token: 'jwt-token',
        refreshToken: 'refresh-token',
      }
      mockApiRequest.mockResolvedValueOnce(loginResponse)

      const result = await authService.login(credentials)

      expect(result).toEqual(loginResponse)
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/login/secure',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(credentials),
          credentials: 'include',
        }),
      )
    })

    it('should throw with server error message on 401', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Geçersiz e-posta veya şifre'))

      await expect(authService.login(credentials)).rejects.toThrow('Geçersiz e-posta veya şifre')
    })

    it('should throw default Turkish message when error has no message', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error(''))

      await expect(authService.login(credentials)).rejects.toThrow('Giriş işlemi başarısız')
    })

    it('should throw on network error', async () => {
      mockApiRequest.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await expect(authService.login(credentials)).rejects.toThrow('Failed to fetch')
    })
  })

  // ─── Register ────────────────────────────────────────────

  describe('register', () => {
    const registerData = {
      email: 'yeni@example.com',
      password: 'GuvenliSifre1!',
      ad: 'Ayse',
      soyad: 'Demir',
      rol: 'ogrenci' as const,
    }

    it('should return success on valid registration', async () => {
      mockApiRequest.mockResolvedValueOnce({ success: true, message: 'Kayıt başarılı' })

      const result = await authService.register(registerData)

      expect(result.success).toBe(true)
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/register',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(registerData),
          credentials: 'include',
        }),
      )
    })

    it('should throw on duplicate email', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Bu e-posta adresi zaten kayıtlı'))

      await expect(authService.register(registerData)).rejects.toThrow('Bu e-posta adresi zaten kayıtlı')
    })

    it('should throw default Turkish message when error has no message', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error(''))

      await expect(authService.register(registerData)).rejects.toThrow('Kayıt işlemi başarısız')
    })
  })

  // ─── Logout ──────────────────────────────────────────────

  describe('logout', () => {
    it('should call secure logout endpoint', async () => {
      mockApiRequest.mockResolvedValueOnce(undefined)

      await authService.logout()

      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/logout/secure',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        }),
      )
    })

    it('should not throw on logout failure (logs warning instead)', async () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      mockApiRequest.mockRejectedValueOnce(new Error('Network error'))

      // logout swallows errors
      await expect(authService.logout()).resolves.toBeUndefined()
      expect(warnSpy).toHaveBeenCalledWith('Logout request failed:', expect.any(Error))
    })
  })

  // ─── Refresh Token ───────────────────────────────────────

  describe('refreshToken', () => {
    it('should return success on valid refresh', async () => {
      mockApiRequest.mockResolvedValueOnce({ success: true })

      const result = await authService.refreshToken()

      expect(result).toEqual({ success: true })
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/refresh/secure',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        }),
      )
    })

    it('should throw when refresh token is expired', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Refresh token expired'))

      await expect(authService.refreshToken()).rejects.toThrow('Refresh token expired')
    })

    it('should throw default Turkish message when error has no message', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error(''))

      await expect(authService.refreshToken()).rejects.toThrow('Token yenileme başarısız')
    })
  })

  // ─── Validate Token ──────────────────────────────────────

  describe('validateToken', () => {
    it('should return true when session is valid', async () => {
      mockApiRequest.mockResolvedValueOnce({ valid: true })

      const result = await authService.validateToken()

      expect(result).toBe(true)
    })

    it('should return false when session is invalid', async () => {
      mockApiRequest.mockResolvedValueOnce({ valid: false })

      const result = await authService.validateToken()

      expect(result).toBe(false)
    })

    it('should return false on network error (does not throw)', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Network error'))

      const result = await authService.validateToken()

      expect(result).toBe(false)
    })
  })

  // ─── Get Current User ────────────────────────────────────

  describe('getCurrentUser', () => {
    it('should return user data from /me endpoint', async () => {
      mockApiRequest.mockResolvedValueOnce({ user: mockUser })

      const result = await authService.getCurrentUser()

      expect(result).toEqual(mockUser)
      expect(result.id).toBe('user-123')
      expect(result.rol).toBe('ogrenci')
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/me',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        }),
      )
    })

    it('should throw when not authenticated', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Unauthorized'))

      await expect(authService.getCurrentUser()).rejects.toThrow('Unauthorized')
    })
  })

  // ─── getUserProfile (alias) ──────────────────────────────

  describe('getUserProfile', () => {
    it('should delegate to getCurrentUser', async () => {
      mockApiRequest.mockResolvedValueOnce({ user: mockUser })

      const result = await authService.getUserProfile()

      expect(result).toEqual(mockUser)
    })
  })

  // ─── Update Profile ──────────────────────────────────────

  describe('updateProfile', () => {
    it('should send partial user data and return updated user', async () => {
      const updateData = { ad: 'Mehmet', telefon: '+905551234567' }
      const updatedUser = { ...mockUser, ...updateData }
      mockApiRequest.mockResolvedValueOnce({ success: true, user: updatedUser })

      const result = await authService.updateProfile(updateData)

      expect(result.success).toBe(true)
      expect(result.user.ad).toBe('Mehmet')
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/profile',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
          credentials: 'include',
        }),
      )
    })

    it('should throw on validation error', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Doğrulama hatası: email: geçersiz format'))

      await expect(authService.updateProfile({ email: 'bad' })).rejects.toThrow('Doğrulama hatası')
    })
  })

  // ─── Change Password ─────────────────────────────────────

  describe('changePassword', () => {
    it('should send current and new passwords', async () => {
      mockApiRequest.mockResolvedValueOnce({ success: true, message: 'Şifre değiştirildi' })

      const result = await authService.changePassword('EskiSifre1!', 'YeniSifre2!')

      expect(result.success).toBe(true)
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/change-password',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ currentPassword: 'EskiSifre1!', newPassword: 'YeniSifre2!' }),
        }),
      )
    })

    it('should throw when current password is wrong', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Mevcut şifre yanlış'))

      await expect(authService.changePassword('wrong', 'YeniSifre2!')).rejects.toThrow('Mevcut şifre yanlış')
    })
  })

  // ─── Request Password Reset ──────────────────────────────

  describe('requestPasswordReset', () => {
    it('should post email to forgot-password endpoint', async () => {
      mockApiRequest.mockResolvedValueOnce({ success: true, message: 'E-posta gönderildi' })

      const result = await authService.requestPasswordReset('ogrenci@example.com')

      expect(result.success).toBe(true)
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/forgot-password',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'ogrenci@example.com' }),
        }),
      )
    })

    it('should throw on non-existent email', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Bu e-posta adresi bulunamadı'))

      await expect(authService.requestPasswordReset('yok@example.com')).rejects.toThrow('Bu e-posta adresi bulunamadı')
    })
  })

  // ─── Reset Password ─────────────────────────────────────

  describe('resetPassword', () => {
    it('should post token and new password to reset endpoint', async () => {
      mockApiRequest.mockResolvedValueOnce({ success: true, message: 'Şifre sıfırlandı' })

      const result = await authService.resetPassword('reset-token-abc', 'YeniSifre3!')

      expect(result.success).toBe(true)
      expect(mockApiRequest).toHaveBeenCalledWith(
        '/api/v1/auth/reset-password',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ token: 'reset-token-abc', newPassword: 'YeniSifre3!' }),
        }),
      )
    })

    it('should throw when reset token is invalid or expired', async () => {
      mockApiRequest.mockRejectedValueOnce(new Error('Geçersiz veya süresi dolmuş token'))

      await expect(authService.resetPassword('bad-token', 'YeniSifre3!')).rejects.toThrow('Geçersiz veya süresi dolmuş token')
    })
  })
})
