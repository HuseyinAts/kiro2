import { Box, Toolbar, useTheme, useMediaQuery } from '@mui/material';
import * as React from 'react';

// import { RoleBasedNavigation } from '../Navigation/RoleBasedNavigation'  // Old navigation
import { ModernNavigation } from '../Navigation/ModernNavigation';  // New modern navigation
import { useLocation } from 'react-router-dom';

import { useAuthStore } from '@/store/authStore';
import { isKiroFullBleed } from '@/kiro/kiroRoutes';
import modernColors from '@/theme/modern-colors';

interface RoleBasedLayoutProps {
  children: React.ReactNode
}

export const RoleBasedLayout: React.FC<RoleBasedLayoutProps> = ({ children }) => {
  const {  isAuthenticated  } = useAuthStore();
  const { pathname } = useLocation();
  // theme and useMediaQuery kept for future responsive enhancements
  useTheme();
  useMediaQuery('(max-width:900px)');

  // Giriş yapılmamışsa VEYA kiro full-bleed rotasında App kabuğunu (nav+header) gösterme —
  // kiro ekranları kendi tema/SideNav'ını (KiroThemeProvider) getirir (tam-ekran, Faz 4).
  if (!isAuthenticated || isKiroFullBleed(pathname)) {
    return <>{children}</>;
  }

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Skip Navigation Link - WCAG 2.4.1 Bypass Blocks */}
      <Box
        component="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: '-9999px',
          zIndex: 9999,
          padding: '1rem',
          backgroundColor: 'primary.main',
          color: 'white',
          textDecoration: 'none',
          fontWeight: 600,
          '&:focus': {
            left: '1rem',
            top: '1rem',
          },
        }}
      >
        Ana içeriğe geç
      </Box>

      <ModernNavigation />
      <Box
        component="main"
        role="main"
        id="main-content"
        aria-label="Ana içerik"
        sx={{
          flexGrow: 1,
          width: { md: 'calc(100% - 280px)' },
          minHeight: '100vh',
          background: modernColors.background.gradient,
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default RoleBasedLayout;