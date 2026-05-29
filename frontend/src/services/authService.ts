import { User, LoginRequest, LoginResponse, RegisterRequest, getErrorMessage } from '../types';
import { apiRequest } from '../utils/apiHelpers';

/**
 * Authentication Service
 *
 * SECURITY: Uses httpOnly cookie-based authentication.
 * All requests include credentials: 'include' for cookie transmission.
 * Tokens are managed by the server via secure httpOnly cookies.
 */
class AuthService {
  private baseUrl = '/api/v1/auth';

  /**
   * Login with secure httpOnly cookie authentication
   * Server sets access_token and refresh_token as httpOnly cookies
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await apiRequest<LoginResponse>(`${this.baseUrl}/login/secure`, {
        method: 'POST',
        body: JSON.stringify(credentials),
        credentials: 'include', // SECURITY: Enable cookie transmission
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Giriş işlemi başarısız');
    }
  }

  async register(userData: RegisterRequest): Promise<{ success: boolean; message?: string }> {
    try {
      // Backend (KullaniciOlustur) `ad_soyad` + `sifre` bekler; form ad/soyad/password
      // toplar. Gönderim öncesi backend sözleşmesine eşle (aksi halde 422).
      const payload = {
        email: userData.email,
        ad_soyad: `${userData.ad ?? ''} ${userData.soyad ?? ''}`.trim(),
        sifre: userData.password,
        rol: userData.rol,
        birth_date: userData.birth_date,
        // veli_email yalnızca doluysa gönder (boş string EmailStr validation'ı bozar)
        veli_email: userData.veli_email || undefined,
      };
      const response = await apiRequest<{ success: boolean; message?: string }>(`${this.baseUrl}/register`, {
        method: 'POST',
        body: JSON.stringify(payload),
        credentials: 'include',
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Kayıt işlemi başarısız');
    }
  }

  /**
   * Logout with secure cookie clearing
   * Server clears httpOnly cookies via response headers
   */
  async logout(): Promise<void> {
    try {
      await apiRequest(`${this.baseUrl}/logout/secure`, {
        method: 'POST',
        credentials: 'include', // SECURITY: Include cookies for server-side clearing
      });
    } catch (error) {
      // Logout hatası kritik değil, sadece log'la
      console.warn('Logout request failed:', error);
    }
  }

  /**
   * Refresh token via secure endpoint
   * Server reads refresh token from httpOnly cookie and sets new access token cookie
   */
  async refreshToken(): Promise<{ success: boolean }> {
    try {
      const response = await apiRequest<{ success: boolean }>(`${this.baseUrl}/refresh/secure`, {
        method: 'POST',
        credentials: 'include', // SECURITY: Include cookies
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Token yenileme başarısız');
    }
  }

  /**
   * KVKK Faz 2: Veli onay token'ını onaylar (public — token=auth)
   */
  async veliOnayVerify(token: string): Promise<{ status: string; message: string }> {
    try {
      return await apiRequest(`${this.baseUrl}/veli-onay/verify`, {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Onay işlemi başarısız');
    }
  }

  /**
   * KVKK Faz 2: Veli onayını geri çeker (public — token=auth, KVKK Madde 11)
   */
  async veliOnayWithdraw(token: string): Promise<{ status: string; message: string }> {
    try {
      return await apiRequest(`${this.baseUrl}/veli-onay/withdraw`, {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Geri çekme başarısız');
    }
  }

  /**
   * Validate current session via httpOnly cookie
   */
  async validateToken(): Promise<boolean> {
    try {
      const response = await apiRequest<{ valid: boolean }>(`${this.baseUrl}/validate`, {
        method: 'POST',
        credentials: 'include', // SECURITY: Include cookies
      });

      return response.valid;
    } catch {
      return false;
    }
  }

  /**
   * Get current user from session cookie
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiRequest<{ user: User }>(`${this.baseUrl}/me`, {
        method: 'GET',
        credentials: 'include', // SECURITY: Include cookies
      });

      return response.user;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Kullanıcı bilgileri alınamadı');
    }
  }

  /**
   * Alias for getCurrentUser - used by useAuthQueries
   * No token parameter needed - uses httpOnly cookie
   */
  async getUserProfile(): Promise<User> {
    return this.getCurrentUser();
  }

  async updateProfile(userData: Partial<User>): Promise<{ success: boolean; user: User }> {
    try {
      const response = await apiRequest<{ success: boolean; user: User }>(`${this.baseUrl}/profile`, {
        method: 'PUT',
        body: JSON.stringify(userData),
        credentials: 'include', // SECURITY: Include cookies
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Profil güncelleme başarısız');
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiRequest<{ success: boolean; message: string }>(`${this.baseUrl}/change-password`, {
        method: 'POST',
        body: JSON.stringify({ currentPassword, newPassword }),
        credentials: 'include', // SECURITY: Include cookies
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Şifre değiştirme başarısız');
    }
  }

  async requestPasswordReset(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiRequest<{ success: boolean; message: string }>(`${this.baseUrl}/forgot-password`, {
        method: 'POST',
        body: JSON.stringify({ email }),
        credentials: 'include',
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Şifre sıfırlama isteği başarısız');
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiRequest<{ success: boolean; message: string }>(`${this.baseUrl}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ token, newPassword }),
        credentials: 'include',
      });

      return response;
    } catch (error: unknown) {
      throw new Error(getErrorMessage(error) || 'Şifre sıfırlama başarısız');
    }
  }
}

export const authService = new AuthService();