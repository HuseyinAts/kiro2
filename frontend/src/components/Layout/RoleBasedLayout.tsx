import { Box, Toolbar, useTheme, useMediaQuery, Fab, Zoom } from '@mui/material';
import { KeyboardArrowUp as ScrollTopIcon } from '@mui/icons-material';
import * as React from 'react';

// import { RoleBasedNavigation } from '../Navigation/RoleBasedNavigation'  // Old navigation
import { ModernNavigation } from '../Navigation/ModernNavigation';  // New modern navigation
import { useLocation } from 'react-router-dom';

import { useAuthStore } from '@/store/authStore';
import { isKiroFullBleed } from '@/kiro/kiroRoutes';
import modernColors from '@/theme/modern-colors';
import { useAccessibilitySettings } from '@/hooks/useAccessibilitySettings';
import { useScreenReader } from '@/hooks/useScreenReader';

interface RoleBasedLayoutProps {
  children: React.ReactNode
}

export const RoleBasedLayout: React.FC<RoleBasedLayoutProps> = ({ children }) => {
  const {  isAuthenticated  } = useAuthStore();
  const { pathname } = useLocation();
  // theme and useMediaQuery kept for future responsive enhancements
  useTheme();
  useMediaQuery('(max-width:900px)');

  const { settings } = useAccessibilitySettings();
  const { manageFocus } = useScreenReader();
  const [showScrollTop, setShowScrollTop] = React.useState(false);

  // AccessibleLayout'tan tasinan ozellikler (S179: AccessibleLayout dead-code,
  // RoleBasedLayout production layout'u — bkz. AccessibleLayout.tsx ust yorumu).
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        const main = document.getElementById('main-content');
        if (main) { manageFocus(main, 'Ana içeriğe geçildi'); }
      }
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const nav = document.querySelector('nav[role="navigation"]') as HTMLElement | null;
        if (nav) { manageFocus(nav, 'Navigasyona geçildi'); }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [manageFocus]);

  React.useEffect(() => {
    const handleScroll = () => setShowScrollTop(window.pageYOffset > 300);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: settings.reducedMotion ? 'auto' : 'smooth' });
  };

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

      <Zoom in={showScrollTop}>
        <Fab
          color="primary"
          size="medium"
          onClick={scrollToTop}
          aria-label="Sayfanın başına git"
          sx={{ position: 'fixed', bottom: 16, right: 16, zIndex: 1000, minHeight: 44, minWidth: 44 }}
        >
          <ScrollTopIcon />
        </Fab>
      </Zoom>
    </Box>
  );
};

export default RoleBasedLayout;