import { Box, CircularProgress, Alert } from '@mui/material';
import * as React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { UserRole } from '../../types';
import { useAuthStore } from '@/store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRoles?: UserRole[]
  requiredPermissions?: Array<{ resource: string; action: string }>
  fallbackPath?: string
  showUnauthorized?: boolean
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  requiredPermissions = [],
  fallbackPath = '/login',
  showUnauthorized = false,
}) => {
  const {  isAuthenticated, user, loading, hasPermission, isAuthorized  } = useAuthStore();
  const location = useLocation();

  // Show loading spinner while initializeAuth is in progress.
  // Do NOT trust persisted isAuthenticated — cookie may have expired.
  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  // Kimlik doğrulama kontrolü
  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Rol kontrolü
  if (requiredRoles.length > 0 && !isAuthorized(requiredRoles)) {
    if (showUnauthorized) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert severity="error">
            Bu sayfaya erişim yetkiniz bulunmamaktadır.
            Gerekli rol: {requiredRoles.join(', ')}
            {user && ` (Mevcut rolünüz: ${user.rol})`}
          </Alert>
        </Box>
      );
    }

    // Rol bazlı yönlendirme
    const redirectPath = getRedirectPathByRole(user?.rol);
    return <Navigate to={redirectPath} replace />;
  }

  // İzin kontrolü
  if (requiredPermissions.length > 0) {
    const hasAllPermissions = requiredPermissions.every(permission =>
      hasPermission(permission.resource, permission.action),
    );

    if (!hasAllPermissions) {
      if (showUnauthorized) {
        return (
          <Box sx={{ p: 3 }}>
            <Alert severity="error">
              Bu işlem için yetkiniz bulunmamaktadır.
            </Alert>
          </Box>
        );
      }

      const redirectPath = getRedirectPathByRole(user?.rol);
      return <Navigate to={redirectPath} replace />;
    }
  }

  return <>{children}</>;
};

// Rol bazlı varsayılan yönlendirme yolları
export function getRedirectPathByRole(role?: UserRole): string {
  switch (role) {
    case 'ogrenci':
      return '/dashboard';
    case 'ogretmen':
      return '/teacher/dashboard';
    case 'veli':
      return '/parent/dashboard';
    case 'admin':
      return '/admin/dashboard';
    default:
      return '/login';
  }
}

export default ProtectedRoute;