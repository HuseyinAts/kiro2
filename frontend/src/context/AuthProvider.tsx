/**
 * Authentication Provider Component
 * Note: With Zustand, this is now just a passthrough component
 * Kept for backward compatibility with existing code
 */

import React, { ReactNode } from 'react';

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  // With Zustand authStore, we don't need a context provider
  // The store is globally accessible via useAuthStore()
  // This component now just passes through children
  return <>{children}</>;
};

export default AuthProvider;
