/**
 * Auth-related React Query Hooks
 *
 * Provides React Query hooks for authentication operations
 * Integrates with authStore for state management
 */

import { useQuery, useMutation, useQueryClient } from 'react-query';

import { authService } from '../../services/authService';
import { useAuthStore } from '../../store';
import type { User, LoginRequest, RegisterRequest } from '../../types';
import { queryKeys } from '../useQueryKeys';

/**
 * Query: Get current user
 * Fetches current user data and syncs with authStore
 * SECURITY: Uses httpOnly cookie for authentication (no token in state)
 */
export const useCurrentUser = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return useQuery(
    queryKeys.auth.user(),
    async () => {
      if (!isAuthenticated) {return null;}
      // SECURITY: authService.getCurrentUser() uses httpOnly cookie
      const user = await authService.getCurrentUser();
      return user;
    },
    {
      enabled: isAuthenticated,
      staleTime: 1000 * 60 * 10, // 10 minutes
      onSuccess: (user) => {
        if (user) {
          useAuthStore.setState({ user });
        }
      },
    },
  );
};

/**
 * Query: Get user profile
 */
export const useUserProfile = (userId: string) => {
  return useQuery(
    queryKeys.auth.profile(userId),
    async () => {
      // authService.getUserProfile uses token-based auth, userId is for cache key only
      const profile = await authService.getUserProfile();
      return profile;
    },
    {
      enabled: !!userId,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  );
};

/**
 * Mutation: Login
 * Handles login and updates authStore
 */
export const useLoginMutation = () => {
  const login = useAuthStore((state) => state.login);
  const queryClient = useQueryClient();

  return useMutation(
    async (credentials: LoginRequest) => {
      const success = await login(credentials);
      if (!success) {
        throw new Error('Login failed');
      }
      return success;
    },
    {
      onSuccess: () => {
        // Invalidate and refetch user data
        queryClient.invalidateQueries(queryKeys.auth.all);
      },
    },
  );
};

/**
 * Mutation: Register
 * Handles registration and auto-login
 */
export const useRegisterMutation = () => {
  const register = useAuthStore((state) => state.register);
  const queryClient = useQueryClient();

  return useMutation(
    async (userData: RegisterRequest) => {
      const success = await register(userData);
      if (!success) {
        throw new Error('Registration failed');
      }
      return success;
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.auth.all);
      },
    },
  );
};

/**
 * Mutation: Logout
 * Handles logout and clears all cached data
 * SECURITY: Calls secure endpoint to clear httpOnly cookies
 */
export const useLogoutMutation = () => {
  const logout = useAuthStore((state) => state.logout);
  const queryClient = useQueryClient();

  return useMutation(
    async () => {
      // SECURITY: logout() is now async - calls server to clear httpOnly cookies
      await logout();
    },
    {
      onSuccess: () => {
        // Clear all cached data on logout
        queryClient.clear();
      },
    },
  );
};

/**
 * Mutation: Update profile
 */
export const useUpdateProfileMutation = () => {
  const updateProfile = useAuthStore((state) => state.updateProfile);
  const queryClient = useQueryClient();

  return useMutation(
    async (userData: Partial<User>) => {
      await updateProfile(userData);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.auth.user());
      },
    },
  );
};
