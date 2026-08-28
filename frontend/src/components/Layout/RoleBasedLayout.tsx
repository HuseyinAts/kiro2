import * as React from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Box, Fab, Zoom } from '@mui/material';
import { KeyboardArrowUp as ScrollTopIcon } from '@mui/icons-material';

import { useAuthStore } from '@/store/authStore';
import { isKiroFullBleed } from '@/kiro/kiroRoutes';
import { SideNav, SideNavRole, SideNavItem } from '@/kiro/ui/SideNav';
import { KiroThemeProvider } from '@/kiro/ui/theme';
import { color, font } from '@/kiro/tokens';
import { useAccessibilitySettings } from '@/hooks/useAccessibilitySettings';
import { useScreenReader } from '@/hooks/useScreenReader';
import { useAyar } from '@/kiro/lib/ayarStore';

interface RoleBasedLayoutProps {
  children: React.ReactNode;
}

function getActiveNavId(path: string): string {
  if (path.includes('/exam') || path.includes('/deneme')) return 'deneme';
  if (path.includes('/learning-path') || path.includes('/ogrenme-yolu')) return 'path';
  if (path.includes('/chat') || path.includes('/ai-sohbet')) return 'assistant';
  if (path.includes('/sokratik')) return 'ai';
  if (path.includes('/weekly-plan') || path.includes('/plan')) return 'plan';
  if (path.includes('/odevlerim') || path.includes('/assignments')) return 'odev';
  if (path.includes('/soru-cozme')) return 'solve';
  if (path.includes('/cat') || path.includes('/adaptif-test')) return 'cat';
  if (path.includes('/tekrar') || path.includes('/review')) return 'review';
  if (path.includes('/league') || path.includes('/lig')) return 'league';
  if (path.includes('/duel') || path.includes('/duello')) return 'duel';
  if (path.includes('/boss')) return 'boss';
  if (path.includes('/veli') || path.includes('/parent')) return 'overview';
  if (path.includes('/ogretmen') || path.includes('/teacher')) return 'panel';
  return 'panel';
}

export const RoleBasedLayout: React.FC<RoleBasedLayoutProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuthStore();
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const { settings } = useAccessibilitySettings();
  const { manageFocus } = useScreenReader();
  const [showScrollTop, setShowScrollTop] = React.useState(false);

  // Read theme to determine light/dark mode for global layout
  const kulturelTema = useAyar(s => s.kulturelTema);
  const isDarkTheme = kulturelTema !== 'varsayilan' && kulturelTema !== 'ebru';
  const themeType = isDarkTheme ? 'dusk' : 'paper';

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

  const roleStr = String(user?.rol || 'ogrenci');
  const sideNavRole: SideNavRole =
    roleStr === 'admin' || roleStr === 'ogretmen' || roleStr === 'teacher' ? 'ogretmen' :
    roleStr === 'veli' || roleStr === 'parent' ? 'veli' : 'ogrenci';

  const activeId = getActiveNavId(pathname);
  const userName = user?.ad || (user as any)?.name || 'Kullanıcı';
  const userSub = roleStr === 'ogrenci' ? '12. Sınıf' : roleStr === 'ogretmen' ? 'Öğretmen' : 'Veli';

  const isFullBleed = !isAuthenticated || isKiroFullBleed(pathname);

  return (
    <KiroThemeProvider theme={themeType}>
      <div
        className={`k-${themeType}`}
        style={{
          minHeight: '100vh',
          display: 'flex',
          background: 'var(--k-bg, #F7F4EF)',
          fontFamily: font.sans,
          color: 'var(--k-text, #2A2433)',
        }}
      >
        {/* Skip Navigation Link - WCAG 2.4.1 */}
        <Box
          component="a"
          href="#main-content"
          sx={{
            position: 'absolute',
            left: '-9999px',
            zIndex: 9999,
            padding: '1rem',
            backgroundColor: color.dawn.coralCtaBg,
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

        {!isFullBleed && (
          <SideNav
            role={sideNavRole}
            activeId={activeId}
            userName={userName}
            userSub={userSub}
            onAssistant={() => navigate('/chat')}
            renderLink={(item: SideNavItem, inner: React.ReactNode, linkProps: any) => (
              <Link to={item.href} {...linkProps}>
                {inner}
              </Link>
            )}
          />
        )}

        {/* Main Content Area */}
        <main
          id="main-content"
          role="main"
          aria-label="Ana içerik"
          style={{
            flex: 1,
            minWidth: 0,
            background: 'transparent',
            minHeight: '100vh',
            boxSizing: 'border-box',
          }}
        >
          {children}
        </main>

        <Zoom in={showScrollTop}>
          <Fab
            size="medium"
            onClick={scrollToTop}
            aria-label="Sayfanın başına git"
            sx={{
              position: 'fixed',
              bottom: 20,
              right: 20,
              zIndex: 1000,
              minHeight: 44,
              minWidth: 44,
              background: color.dawn.coralCtaBg,
              color: '#ffffff',
              '&:hover': {
                background: color.dawn.coralCtaBg,
                opacity: 0.9,
              },
            }}
          >
            <ScrollTopIcon />
          </Fab>
        </Zoom>
      </div>
    </KiroThemeProvider>
  );
};

export default RoleBasedLayout;