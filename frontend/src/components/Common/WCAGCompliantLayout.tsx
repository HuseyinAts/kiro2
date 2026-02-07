/**
 * WCAG 2.1 Level AA Uyumlu Ana Layout Bileşeni
 *
 * Özellikler:
 * - Semantic HTML5 landmarks
 * - Skip navigation links
 * - Proper heading hierarchy
 * - ARIA labels ve roles
 * - Keyboard navigation support
 * - Screen reader optimization
 */

import { Box, Container, useTheme } from '@mui/material';
import * as React from 'react';
import {  useRef, useEffect  } from 'react';

import { useScreenReader } from '../../hooks/useScreenReader';
import AccessibleNavigation from '../Navigation/AccessibleNavigation';

import { useAccessibility } from './AccessibilityProvider';

interface WCAGCompliantLayoutProps {
  children: React.ReactNode;
  navigationItems: Array<{
    id: string;
    label: string;
    href?: string;
    onClick?: () => void;
    icon?: React.ReactNode;
  }>;
  breadcrumbs?: Array<{
    label: string;
    href?: string;
    onClick?: () => void;
  }>;
  title: string;
  pageTitle?: string;
  pageDescription?: string;
}

export const WCAGCompliantLayout: React.FC<WCAGCompliantLayoutProps> = ({
  children,
  navigationItems,
  breadcrumbs,
  title,
  pageTitle,
  pageDescription,
}) => {
  const theme = useTheme();
  const mainRef = useRef<HTMLElement>(null);
  const { settings } = useAccessibility();
  const { announcePageChange, announceLandmark } = useScreenReader();

  // Sayfa değişikliği duyurusu
  useEffect(() => {
    if (pageTitle) {
      document.title = `${pageTitle} - ${title}`;
      announcePageChange(pageTitle);
    }
  }, [pageTitle, title, announcePageChange]);

  // Ana içerik landmark duyurusu
  useEffect(() => {
    const handleMainFocus = () => {
      announceLandmark('main', 'Ana içerik');
    };

    const mainElement = mainRef.current;
    if (mainElement) {
      mainElement.addEventListener('focus', handleMainFocus);
      return () => mainElement.removeEventListener('focus', handleMainFocus);
    }
  }, [announceLandmark]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        backgroundColor: theme.palette.background.default,
      }}
    >
      {/* Header - Banner landmark */}
      <Box component="header" role="banner">
        <AccessibleNavigation
          title={title}
          navigationItems={navigationItems.map(item => ({
            id: item.id,
            label: item.label,
            path: item.href,
            icon: item.icon,
          }))}
          breadcrumbs={breadcrumbs?.map(b => ({
            label: b.label,
            path: b.href,
          }))}
          showAccessibilityButton={true}
        />
      </Box>

      {/* Main Content - Main landmark */}
      <Container
        component="main"
        ref={mainRef}
        id="main-content"
        role="main"
        aria-label="Ana içerik"
        tabIndex={-1}
        sx={{
          flexGrow: 1,
          py: 3,
          px: { xs: 2, sm: 3 },
          // Focus için outline
          '&:focus': {
            outline: 'none',
          },
          '&:focus-visible': {
            outline: `3px solid ${theme.palette.primary.main}`,
            outlineOffset: '2px',
          },
        }}
      >
        {/* Sayfa başlığı - H1 */}
        {pageTitle && (
          <Box
            component="h1"
            sx={{
              fontSize: {
                small: '1.75rem',
                medium: '2rem',
                large: '2.25rem',
                'extra-large': '2.5rem',
              }[settings.fontSize],
              fontWeight: 'bold',
              mb: 2,
              color: theme.palette.text.primary,
              // Ekran okuyucu için
              '&:focus': {
                outline: 'none',
              },
            }}
            tabIndex={-1}
            id="page-title"
          >
            {pageTitle}
          </Box>
        )}

        {/* Sayfa açıklaması */}
        {pageDescription && (
          <Box
            component="p"
            sx={{
              fontSize: {
                small: '0.875rem',
                medium: '1rem',
                large: '1.125rem',
                'extra-large': '1.25rem',
              }[settings.fontSize],
              mb: 3,
              color: theme.palette.text.secondary,
              lineHeight: settings.dyslexiaSupport ? 1.8 : 1.6,
            }}
            id="page-description"
          >
            {pageDescription}
          </Box>
        )}

        {/* Ana içerik */}
        <Box
          sx={{
            // Disleksi desteği için satır aralığı
            lineHeight: settings.dyslexiaSupport ? 1.8 : 1.6,
            // Motor bozukluk desteği için daha büyük aralıklar
            '& > *': {
              mb: settings.motorImpairmentSupport ? 3 : 2,
            },
          }}
        >
          {children}
        </Box>
      </Container>

      {/* Footer - Contentinfo landmark */}
      <Box
        component="footer"
        role="contentinfo"
        aria-label="Sayfa bilgileri"
        sx={{
          mt: 'auto',
          py: 2,
          px: 3,
          backgroundColor: theme.palette.grey[100],
          borderTop: `1px solid ${theme.palette.divider}`,
          // Yüksek kontrast modu
          ...(settings.highContrast && {
            backgroundColor: '#f5f5f5',
            borderTop: '2px solid #000000',
            color: '#000000',
          }),
        }}
      >
        <Container>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', sm: 'center' },
              gap: 2,
            }}
          >
            {/* Telif hakkı */}
            <Box
              component="p"
              sx={{
                margin: 0,
                fontSize: {
                  small: '0.75rem',
                  medium: '0.875rem',
                  large: '1rem',
                  'extra-large': '1.125rem',
                }[settings.fontSize],
                color: theme.palette.text.secondary,
              }}
            >
              © 2024 {title}. Tüm hakları saklıdır.
            </Box>

            {/* Erişilebilirlik beyanı */}
            <Box
              component="nav"
              role="navigation"
              aria-label="Footer navigasyonu"
            >
              <Box
                component="a"
                href="/erisebilirlik"
                sx={{
                  fontSize: {
                    small: '0.75rem',
                    medium: '0.875rem',
                    large: '1rem',
                    'extra-large': '1.125rem',
                  }[settings.fontSize],
                  color: theme.palette.primary.main,
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                  '&:focus-visible': {
                    outline: `3px solid ${theme.palette.primary.main}`,
                    outlineOffset: '2px',
                  },
                }}
              >
                Erişilebilirlik Beyanı
              </Box>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Live region for announcements */}
      <Box
        id="live-announcements"
        aria-live="polite"
        aria-atomic="true"
        sx={{
          position: 'absolute',
          left: '-9999px',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
        }}
      />

      {/* Assertive live region for urgent announcements */}
      <Box
        id="urgent-announcements"
        aria-live="assertive"
        aria-atomic="true"
        sx={{
          position: 'absolute',
          left: '-9999px',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
        }}
      />
    </Box>
  );
};

export default WCAGCompliantLayout;