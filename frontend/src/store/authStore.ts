/**
 * Authentication Store (Zustand)
 *
 * Centralized authentication state management with Zustand
 *
 * SECURITY UPDATE: httpOnly Cookie-based Authentication
 * - Tokens are now managed by the server via httpOnly cookies
 * - No more localStorage token storage - XSS attack surface eliminated
 * - Store only manages user state and authentication status
 *
 * Features:
 * - DevTools integration
 * - Type-safe state management
 * - Role-based permissions
 * - Automatic session validation via cookies
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

import { authService } from '../services/authService';
import { User, UserRole, LoginRequest, RegisterRequest, AuthState, getErrorMessage } from '../types';

// Role-based permissions configuration
const rolePermissions = {
  ogrenci: [
    { resource: 'dashboard', action: 'read' },
    { resource: 'exam', action: 'read' },
    { resource: 'exam', action: 'create' },
    { resource: 'profile', action: 'read' },
    { resource: 'profile', action: 'update' },
    { resource: 'chat', action: 'read' },
    { resource: 'chat', action: 'create' },
    { resource: 'learning-path', action: 'read' },
  ],
  ogretmen: [
    { resource: 'dashboard', action: 'read' },
    { resource: 'students', action: 'read' },
    { resource: 'class', action: 'read' },
    { resource: 'class', action: 'update' },
    { resource: 'exam', action: 'read' },
    { resource: 'exam', action: 'create' },
    { resource: 'exam', action: 'update' },
    { resource: 'reports', action: 'read' },
    { resource: 'content', action: 'read' },
    { resource: 'content', action: 'create' },
  ],
  veli: [
    { resource: 'dashboard', action: 'read' },
    { resource: 'child-progress', action: 'read' },
    { resource: 'reports', action: 'read' },
    { resource: 'notifications', action: 'read' },
    { resource: 'profile', action: 'read' },
    { resource: 'profile', action: 'update' },
  ],
  admin: [
    { resource: '*', action: '*' }, // Admin has access to all resources
  ],
};

// Race condition prevention flag
let isInitializing = false;
let initPromise: Promise<void> | null = null;

interface AuthStore extends Omit<AuthState, 'token' | 'refreshToken'> {
  // Actions
  login: (credentials: LoginRequest) => Promise<boolean>
  register: (userData: RegisterRequest) => Promise<boolean>
  logout: () => Promise<void>
  refreshAuth: () => Promise<boolean>
  initializeAuth: () => Promise<void>

  // Permission checks
  hasRole: (role: UserRole) => boolean
  hasPermission: (resource: string, action: string) => boolean
  isAuthorized: (requiredRoles: UserRole[]) => boolean

  // User management
  updateProfile: (userData: Partial<User>) => Promise<void>

  // State setters
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state - SECURITY: No token storage, using httpOnly cookies
        isAuthenticated: false,
        user: null,
        loading: true,
        error: null,

        /**
         * Initialize authentication on app load
         * SECURITY: Validates session via httpOnly cookie
         * RACE CONDITION PROTECTION: Prevents concurrent calls
         */
        initializeAuth: async () => {
          // Prevent concurrent initialization (race condition fix)
          if (isInitializing && initPromise) {
            return initPromise;
          }

          isInitializing = true;
          initPromise = (async () => {
            try {
              // Validate session via cookie - server checks httpOnly cookie
              const isValid = await authService.validateToken();

              if (isValid) {
                // Get user data - server reads from cookie
                const user = await authService.getCurrentUser();
                set({
                  isAuthenticated: true,
                  user,
                  loading: false,
                  error: null,
                });
              } else {
                // Try to refresh session via cookie
                const refreshed = await get().refreshAuth();
                if (!refreshed) {
                  set({
                    isAuthenticated: false,
                    user: null,
                    loading: false,
                    error: null,
                  });
                }
              }
            } catch (error) {
              console.error('Auth initialization error:', error);
              set({
                isAuthenticated: false,
                user: null,
                loading: false,
                error: null, // Don't show error on init - user may just not be logged in
              });
            } finally {
              isInitializing = false;
              initPromise = null;
            }
          })();

          return initPromise;
        },

        /**
         * Login action
         * SECURITY: Server sets httpOnly cookies, we only store user state
         */
        login: async (credentials: LoginRequest): Promise<boolean | '2fa_required'> => {
          try {
            set({ loading: true, error: null });

            const response = await authService.login(credentials);

            if (response.success && response.user) {
              // SECURITY: No localStorage token storage
              // Server has set httpOnly cookies via response headers
              set({
                isAuthenticated: true,
                user: response.user,
                loading: false,
                error: null,
              });

              return true;
            }

            // S179 fix (B-P0-24): backend returns {success:false, requires_2fa:true}
            // when the user has TOTP enabled. We surface this as a distinct
            // signal so ModernLoginPage can route to the 2FA challenge step
            // instead of showing "Giriş başarısız".
            if (response.requires_2fa) {
              set({
                loading: false,
                error: null,
              });
              // Stash the pending email on window for the 2FA form to pick up.
              // (No store field added — kept narrow per CLAUDE.md "no new
              // fields beyond what the task requires".)
              if (typeof window !== 'undefined' && response.email) {
                (window as Window & { __pending2faEmail?: string }).__pending2faEmail = response.email;
              }
              return '2fa_required';
            }

            set({
              loading: false,
              error: response.message || 'Giriş başarısız',
            });
            return false;
          } catch (error: unknown) {
            set({
              loading: false,
              error: getErrorMessage(error),
            });
            return false;
          }
        },

        /**
         * Register action
         */
        register: async (userData: RegisterRequest): Promise<boolean> => {
          try {
            set({ loading: true, error: null });

            const response = await authService.register(userData);

            if (response.success) {
              // Auto-login after successful registration
              return await get().login({
                email: userData.email,
                password: userData.password,
              });
            } else {
              set({
                loading: false,
                error: response.message || 'Kayıt başarısız',
              });
              return false;
            }
          } catch (error: unknown) {
            set({
              loading: false,
              error: getErrorMessage(error),
            });
            return false;
          }
        },

        /**
         * Logout action
         * SECURITY: Server clears httpOnly cookies via /logout/secure endpoint
         */
        logout: async () => {
          // Call server to clear httpOnly cookies
          await authService.logout();

          // Clear local state
          set({
            isAuthenticated: false,
            user: null,
            loading: false,
            error: null,
          });
        },

        /**
         * Refresh authentication
         * SECURITY: Server handles refresh via httpOnly cookie
         */
        refreshAuth: async (): Promise<boolean> => {
          try {
            // Server reads refresh token from httpOnly cookie
            const response = await authService.refreshToken();

            if (response.success) {
              // Get updated user data
              const user = await authService.getCurrentUser();
              set({
                isAuthenticated: true,
                user,
                loading: false,
                error: null,
              });
              return true;
            }
            return false;
          } catch (error) {
            console.error('Token refresh error:', error);
            return false;
          }
        },

        // Check if user has specific role
        hasRole: (role: UserRole): boolean => {
          const { user } = get();
          return user?.rol === role;
        },

        // Check if user has specific permission
        hasPermission: (resource: string, action: string): boolean => {
          const { user } = get();
          if (!user) {return false;}

          const userRole = user.rol;
          const permissions = rolePermissions[userRole] || [];

          // Admin has all permissions
          if (userRole === 'admin') {return true;}

          // Check specific permission
          return permissions.some(permission =>
            (permission.resource === resource || permission.resource === '*') &&
            (permission.action === action || permission.action === '*'),
          );
        },

        // Check if user is authorized (has one of required roles)
        isAuthorized: (requiredRoles: UserRole[]): boolean => {
          const { user } = get();
          if (!user) {return false;}
          return requiredRoles.includes(user.rol);
        },

        // Update user profile
        updateProfile: async (userData: Partial<User>): Promise<void> => {
          try {
            const response = await authService.updateProfile(userData);

            if (response.success) {
              set({ user: response.user });
            } else {
              throw new Error('Profil güncelleme başarısız');
            }
          } catch (error: unknown) {
            throw new Error(getErrorMessage(error));
          }
        },

        // Set loading state
        setLoading: (loading: boolean) => {
          set({ loading });
        },

        // Set error state
        setError: (error: string | null) => {
          set({ error });
        },
      }),
      {
        name: 'auth-storage',
        // SECURITY: Only persist user display info, no tokens
        // Tokens are now in httpOnly cookies (not accessible to JS)
        partialize: (state) => ({
          user: state.user,
          isAuthenticated: state.isAuthenticated,
        }),
      },
    ),
    { name: 'AuthStore' },
  ),
);

/**
 * Selector hooks for better performance
 * Use these instead of accessing the whole store
 */
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.loading);
export const useAuthError = () => useAuthStore((state) => state.error);

export default useAuthStore;
