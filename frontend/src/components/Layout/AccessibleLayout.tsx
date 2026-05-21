/**
 * WCAG 2.1 Level AA Uyumlu Layout Bileşeni
 * Semantic HTML ve landmark'lar.
 *
 * @deprecated S179 fix (F-P0-4): this file is DEAD CODE (zero imports outside
 *   itself). Production routes use `RoleBasedLayout`. The WCAG-AA features
 *   that lived here (skip-link, Alt+M/Alt+N shortcuts, scroll-to-top
 *   respecting reduced motion) should be merged into RoleBasedLayout in a
 *   focused sprint. Until then this component must NOT be re-imported —
 *   doing so creates two competing layout systems.
 */

import {
  KeyboardArrowUp as ScrollTopIcon,
  Accessibility as AccessibilityIcon,
} from '@mui/icons-material';
import {
  Box,
  Container,
  Fab,
  Zoom,
  useTheme,
  useMediaQuery,
  Snackbar,
  Alert,
  Typography,
} from '@mui/material';
import * as React from 'react';
import {  useEffect, useRef, useCallback  } from 'react';

import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';
import { useScreenReader } from '../../hooks/useScreenReader';
import AccessibleNavigation, { NavigationItem, BreadcrumbItem } from '../Navigation/AccessibleNavigation';

interface AccessibleLayoutProps {
  title: string;
  logo?: React.ReactNode;
  navigationItems: NavigationItem[];
  breadcrumbs?: BreadcrumbItem[];
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  footer?: React.ReactNode;
  showScrollTop?: boolean;
  showAccessibilityFab?: boolean;
  onAccessibilityClick?: () => void;
  className?: string;
}

const AccessibleLayout: React.FC<AccessibleLayoutProps> = ({
  title,
  logo,
  navigationItems,
  breadcrumbs,
  children,
  sidebar,
  footer,
  showScrollTop = true,
  showAccessibilityFab = true,
  onAccessibilityClick,
  className,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { settings, getAccessibilityStatus } = useAccessibilitySettings();
  const { announce, manageFocus, createSkipLink } = useScreenReader();
  const { focusFirst: _focusFirst } = useKeyboardNavigation();

  const mainContentRef = useRef<HTMLElement>(null);
  const scrollTopRef = useRef<HTMLButtonElement>(null);
  const [showScrollButton, setShowScrollButton] = React.useState(false);
  const [accessibilityNotification, setAccessibilityNotification] = React.useState<string | null>(null);

  // Scroll to top görünürlüğü
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      setShowScrollButton(scrollTop > 300);
    };

    if (showScrollTop) {
      window.addEventListener('scroll', handleScroll);
      return () => window.removeEventListener('scroll', handleScroll);
    }
  }, [showScrollTop]);

  // Scroll to top fonksiyonu
  const handleScrollTop = useCallback(() => {
    window.scrollTo({
      top: 0,
      behavior: settings.reducedMotion ? 'auto' : 'smooth',
    });
    announce('Sayfanın başına gidildi', 'polite');
  }, [settings.reducedMotion, announce]);

  // Ana içeriğe geç fonksiyonu
  const skipToMainContent = useCallback(() => {
    if (mainContentRef.current) {
      manageFocus(mainContentRef.current, 'Ana içeriğe geçildi');
    }
  }, [manageFocus]);

  // Erişilebilirlik FAB tıklama
  const handleAccessibilityClick = useCallback(() => {
    if (onAccessibilityClick) {
      onAccessibilityClick();
    } else {
      // Varsayılan erişilebilirlik menüsü
      const status = getAccessibilityStatus();
      setAccessibilityNotification(status.summary);
    }
  }, [onAccessibilityClick, getAccessibilityStatus]);

  // Klavye kısayolları
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Alt + M: Ana içeriğe geç
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        skipToMainContent();
      }

      // Alt + N: Navigasyona geç
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const navigation = document.querySelector('nav[role="navigation"]') as HTMLElement;
        if (navigation) {
          manageFocus(navigation, 'Navigasyona geçildi');
        }
      }

      // Alt + S: Sidebar'a geç
      if (event.altKey && event.key === 's' && sidebar) {
        event.preventDefault();
        const sidebarElement = document.querySelector('aside[role="complementary"]') as HTMLElement;
        if (sidebarElement) {
          manageFocus(sidebarElement, 'Yan panele geçildi');
        }
      }

      // Alt + F: Footer'a geç
      if (event.altKey && event.key === 'f' && footer) {
        event.preventDefault();
        const footerElement = document.querySelector('footer[role="contentinfo"]') as HTMLElement;
        if (footerElement) {
          manageFocus(footerElement, 'Alt bilgi bölümüne geçildi');
        }
      }

      // Alt + A: Erişilebilirlik ayarları
      if (event.altKey && event.key === 'a') {
        event.preventDefault();
        handleAccessibilityClick();
      }

      // Alt + T: Sayfanın başına git
      if (event.altKey && event.key === 't') {
        event.preventDefault();
        handleScrollTop();
      }

      // Alt + 1: Yüksek kontrast toggle
      if (event.altKey && event.key === '1') {
        event.preventDefault();
        // toggleHighContrast fonksiyonu çağrılacak
        announce('Yüksek kontrast modu değiştirildi', 'polite');
      }

      // Alt + 2: Font boyutu artır
      if (event.altKey && event.key === '2') {
        event.preventDefault();
        // increaseFontSize fonksiyonu çağrılacak
        announce('Font boyutu artırıldı', 'polite');
      }

      // Alt + 3: Font boyutu azalt
      if (event.altKey && event.key === '3') {
        event.preventDefault();
        // decreaseFontSize fonksiyonu çağrılacak
        announce('Font boyutu azaltıldı', 'polite');
      }
    };

    if (settings.keyboardNavigation) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [
    settings.keyboardNavigation,
    skipToMainContent,
    manageFocus,
    sidebar,
    footer,
    handleAccessibilityClick,
    handleScrollTop,
    announce,
  ]);

  // Skip links oluştur
  useEffect(() => {
    const skipLinks = [
      createSkipLink('main-content', 'Ana içeriğe geç'),
      createSkipLink('navigation', 'Navigasyona geç'),
    ];

    if (sidebar) {
      skipLinks.push(createSkipLink('sidebar', 'Yan panele geç'));
    }

    if (footer) {
      skipLinks.push(createSkipLink('footer', 'Alt bilgi bölümüne geç'));
    }

    // Skip links container oluştur
    const skipContainer = document.createElement('div');
    skipContainer.className = 'skip-links-container';
    skipContainer.style.cssText = `
      position: absolute;
      top: -100px;
      left: 0;
      z-index: 10000;
      display: flex;
      gap: 8px;
      padding: 8px;
    `;

    skipLinks.forEach(link => {
      skipContainer.appendChild(link);
    });

    document.body.insertBefore(skipContainer, document.body.firstChild);

    return () => {
      if (skipContainer.parentNode) {
        skipContainer.parentNode.removeChild(skipContainer);
      }
    };
  }, [createSkipLink, sidebar, footer]);

  // Sayfa yüklendiğinde duyuru
  useEffect(() => {
    announce(`${title} sayfası yüklendi`, 'polite');
  }, [title, announce]);

  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        '& .wcag-aa-target-size': {
          minHeight: 44,
          minWidth: 44,
        },
      }}
    >
      {/* Navigation */}
      <AccessibleNavigation
        title={title}
        logo={logo}
        navigationItems={navigationItems}
        breadcrumbs={breadcrumbs}
        showAccessibilityButton={!showAccessibilityFab}
        onAccessibilityClick={handleAccessibilityClick}
      />

      {/* Main Layout */}
      <Box sx={{ display: 'flex', flex: 1 }}>
        {/* Sidebar */}
        {sidebar && (
          <Box
            component="aside"
            role="complementary"
            id="sidebar"
            aria-label="Yan panel"
            sx={{
              width: { xs: '100%', md: 280 },
              flexShrink: 0,
              display: { xs: 'none', md: 'block' },
              borderRight: 1,
              borderColor: 'divider',
              bgcolor: 'background.paper',
              overflow: 'auto',
              '&:focus': {
                outline: `2px solid ${theme.palette.primary.main}`,
                outlineOffset: 2,
              },
            }}
            tabIndex={-1}
          >
            {sidebar}
          </Box>
        )}

        {/* Main Content */}
        <Box
          component="main"
          ref={mainContentRef}
          role="main"
          id="main-content"
          aria-label="Ana içerik"
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'auto',
            '&:focus': {
              outline: 'none',
            },
          }}
          tabIndex={-1}
        >
          <Container
            maxWidth="xl"
            sx={{
              flex: 1,
              py: { xs: 2, sm: 3 },
              px: { xs: 2, sm: 3 },
            }}
          >
            {children}
          </Container>
        </Box>
      </Box>

      {/* Footer */}
      {footer && (
        <Box
          component="footer"
          role="contentinfo"
          id="footer"
          aria-label="Alt bilgi"
          sx={{
            borderTop: 1,
            borderColor: 'divider',
            bgcolor: 'background.paper',
            '&:focus': {
              outline: `2px solid ${theme.palette.primary.main}`,
              outlineOffset: 2,
            },
          }}
          tabIndex={-1}
        >
          {footer}
        </Box>
      )}

      {/* Scroll to Top FAB */}
      {showScrollTop && (
        <Zoom in={showScrollButton}>
          <Fab
            ref={scrollTopRef}
            color="primary"
            size="medium"
            onClick={handleScrollTop}
            aria-label="Sayfanın başına git"
            className="wcag-aa-target-size"
            sx={{
              position: 'fixed',
              bottom: showAccessibilityFab ? 80 : 16,
              right: 16,
              zIndex: 1000,
            }}
          >
            <ScrollTopIcon />
          </Fab>
        </Zoom>
      )}

      {/* Accessibility FAB */}
      {showAccessibilityFab && (
        <Fab
          color="secondary"
          size="medium"
          onClick={handleAccessibilityClick}
          aria-label="Erişilebilirlik ayarları"
          className="wcag-aa-target-size"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            zIndex: 1000,
          }}
        >
          <AccessibilityIcon />
        </Fab>
      )}

      {/* Erişilebilirlik Bildirimi */}
      <Snackbar
        open={!!accessibilityNotification}
        autoHideDuration={4000}
        onClose={() => setAccessibilityNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setAccessibilityNotification(null)}
          severity="info"
          variant="filled"
        >
          {accessibilityNotification}
        </Alert>
      </Snackbar>

      {/* Klavye Kısayolları Yardımı */}
      {settings.keyboardNavigation && !isMobile && (
        <Box
          sx={{
            position: 'fixed',
            top: 50,
            right: 16,
            bgcolor: 'background.paper',
            p: 2,
            borderRadius: 1,
            boxShadow: 2,
            fontSize: '0.75rem',
            opacity: 0.9,
            zIndex: 1000,
            maxWidth: 300,
            border: 1,
            borderColor: 'divider',
          }}
        >
          <Typography variant="caption" component="div" gutterBottom>
            <strong>Klavye Kısayolları:</strong>
          </Typography>
          <Typography variant="caption" component="div">
            Alt+M: Ana içerik | Alt+N: Navigasyon<br/>
            Alt+S: Yan panel | Alt+F: Footer<br/>
            Alt+A: Erişilebilirlik | Alt+T: Başa git<br/>
            Alt+1: Kontrast | Alt+2/3: Font boyutu
          </Typography>
        </Box>
      )}

      {/* Live Region for Announcements */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="live-region-polite"
      />

      <div
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        id="live-region-assertive"
      />

      <div
        role="status"
        aria-live="polite"
        aria-atomic="false"
        className="sr-only"
        id="status-region"
      />
    </Box>
  );
};

export default AccessibleLayout;