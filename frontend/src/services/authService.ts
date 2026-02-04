import { User, LoginRequest, LoginResponse, RegisterRequest } from '../types'
import { apiRequest } from '../utils/apiHelpers'

class AuthService {
  private baseUrl = '/api/v1/auth'

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await apiRequest<LoginResponse>(`${this.baseUrl}/login`, {
        method: 'POST',
        body: JSON.stringify(credentials)
      })
      
      return response
    } catch (error: any) {
      throw new Error(error.message || 'Giriş işlemi başarısız')
    }
  }

  async register(userData: RegisterRequest): Promise<{ success: boolean; message?: string }> {
    try {
      const response = await apiRequest<{ success: boolean; message?: string }>(`${this.baseUrl}/register`, {
        method: 'POST',
        body: JSON.stringify(userData)
      })
      
      return response
    } catch (error: any) {
      throw new Error(error.message || 'Kayıt işlemi başarısız')
    }
  }

  async logout(): Promise<void> {
    try {
      const token = localStorage.getItem('access_token')
      if (token) {
        await apiRequest(`${this.baseUrl}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      }
    } catch (error) {
      // Logout hatası kritik değil, sadece log'la
      console.warn('Logout request failed:', error)
    }
  }

  async refreshToken(refreshToken: string): Promise<{ success: boolean; token: string; refreshToken: string }> {
    try {
      const response = await apiRequest<{ success: boolean; token: string; refreshToken: string }>(`${this.baseUrl}/refresh`, {
        method: 'POST',
        body: JSON.stringify({ refreshToken })
      })
      
      return response
    } catch (error: any) {
      throw new Error(error.message || 'Token yenileme başarısız')
    }
  }

  async validateToken(token: string): Promise<boolean> {
    try {
      const response = await apiRequest<{ valid: boolean }>(`${this.baseUrl}/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      return response.valid
    } catch (error) {
      return false
    }
  }

  async getCurrentUser(token: string): Promise<User> {
    try {
      const response = await apiRequest<{ user: User }>(`${this.baseUrl}/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      return response.user
    } catch (error: any) {
      throw new Error(error.message || 'Kullanıcı bilgileri alınamadı')
    }
  }

  async updateProfile(userData: Partial<User>): Promise<{ success: boolean; user: User }> {
    try {
      const token = localStorage.getItem('access_token')
      const response = await apiRequest<{ success: boolean; user: User }>(`${this.baseUrl}/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(userData)
      })

      return response
    } catch (error: any) {
      throw new Error(error.message || 'Profil güncelleme başarısız')
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    try {
      const token = localStorage.getItem('access_token')
      const response = await apiRequest<{ success: boolean; message: string }>(`${this.baseUrl}/change-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ currentPassword, newPassword })
      })

      return response
    } catch (error: any) {
      throw new Error(error.message || 'Şifre değiştirme başarısız')
    }
  }

  async requestPasswordReset(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiRequest<{ success: boolean; message: string }>(`${this.baseUrl}/forgot-password`, {
        method: 'POST',
        body: JSON.stringify({ email })
      })
      
      return response
    } catch (error: any) {
      throw new Error(error.message || 'Şifre sıfırlama isteği başarısız')
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiRequest<{ success: boolean; message: string }>(`${this.baseUrl}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ token, newPassword })
      })
      
      return response
    } catch (error: any) {
      throw new Error(error.message || 'Şifre sıfırlama başarısız')
    }
  }
}

export const authService = new AuthService()