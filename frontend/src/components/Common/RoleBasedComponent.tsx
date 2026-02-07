import { Box, Alert } from '@mui/material';
import * as React from 'react';

import { useRoleAccess } from '../../hooks/useRoleAccess.tsx';
import { UserRole } from '../../types';

interface RoleBasedComponentProps {
  children: React.ReactNode
  allowedRoles?: UserRole[]
  requiredPermissions?: Array<{ resource: string; action: string }>
  fallback?: React.ReactNode
  showUnauthorized?: boolean
}

/**
 * Rol tabanlı bileşen görüntüleme komponenti
 * Belirli rollere veya izinlere sahip kullanıcılara içerik gösterir
 */
export const RoleBasedComponent: React.FC<RoleBasedComponentProps> = ({
  children,
  allowedRoles = [],
  requiredPermissions = [],
  fallback = null,
  showUnauthorized = false,
}) => {
  const { hasAccess, isLoading, userRole } = useRoleAccess({
    allowedRoles,
    requiredPermissions,
    showUnauthorized,
  });

  if (isLoading) {
    return <Box>Yükleniyor...</Box>;
  }

  if (!hasAccess) {
    if (showUnauthorized) {
      return (
        <Alert severity="warning">
          Bu içeriği görüntüleme yetkiniz bulunmamaktadır.
          {userRole && ` (Mevcut rolünüz: ${userRole})`}
        </Alert>
      );
    }

    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Convenience components for specific roles
export const StudentOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => (
  <RoleBasedComponent allowedRoles={['ogrenci']} fallback={fallback}>
    {children}
  </RoleBasedComponent>
);

export const TeacherOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => (
  <RoleBasedComponent allowedRoles={['ogretmen']} fallback={fallback}>
    {children}
  </RoleBasedComponent>
);

export const ParentOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => (
  <RoleBasedComponent allowedRoles={['veli']} fallback={fallback}>
    {children}
  </RoleBasedComponent>
);

export const AdminOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => (
  <RoleBasedComponent allowedRoles={['admin']} fallback={fallback}>
    {children}
  </RoleBasedComponent>
);

export const TeacherOrAdmin: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => (
  <RoleBasedComponent allowedRoles={['ogretmen', 'admin']} fallback={fallback}>
    {children}
  </RoleBasedComponent>
);

export const AuthenticatedOnly: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({
  children,
  fallback = null,
}) => (
  <RoleBasedComponent allowedRoles={['ogrenci', 'ogretmen', 'veli', 'admin']} fallback={fallback}>
    {children}
  </RoleBasedComponent>
);

export default RoleBasedComponent;