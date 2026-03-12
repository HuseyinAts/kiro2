/**
 * Authentication Provider Component
 * Initializes auth state on app mount by validating httpOnly cookie session.
 */

import * as React from 'react';
import { ReactNode, useEffect } from 'react';

import { useAuthStore } from '../store/authStore';

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const initializeAuth = useAuthStore((state) => state.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return <>{children}</>;
};

export default AuthProvider;
