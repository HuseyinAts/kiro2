/**
 * Erişilebilirlik Sağlayıcı Bileşeni
 * Tüm erişilebilirlik özelliklerini merkezi olarak yönetir
 */

import { CssBaseline } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import * as React from 'react';
import {  createContext, useContext, useEffect  } from 'react';

import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useScreenReader } from '../../hooks/useScreenReader';
import '../../styles/accessibility.css';

interface AccessibilityContextType {
  settings: ReturnType<typeof useAccessibilitySettings>['settings'];
  updateSetting: ReturnType<typeof useAccessibilitySettings>['updateSetting'];
  toggleHighContrast: ReturnType<typeof useAccessibilitySettings>['toggleHighContrast'];
  toggleReducedMotion: ReturnType<typeof useAccessibilitySettings>['toggleReducedMotion'];
  increaseFontSize: ReturnType<typeof useAccessibilitySettings>['increaseFontSize'];
  decreaseFontSize: ReturnType<typeof useAccessibilitySettings>['decreaseFontSize'];
  announce: ReturnType<typeof useScreenReader>['announce'];
}

const AccessibilityContext = createContext<AccessibilityContextType | null>(null);

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
};

interface AccessibilityProviderProps {
  children: React.ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const accessibilitySettings = useAccessibilitySettings();
  const { announce } = useScreenReader();

  // Tema oluştur
  const theme = createTheme({
    palette: {
      mode: accessibilitySettings.settings.highContrast ? 'light' : 'light',
      primary: {
        main: accessibilitySettings.settings.highContrast ? '#000000' : '#1976d2',
      },
      background: {
        default: accessibilitySettings.settings.highContrast ? '#ffffff' : '#fafafa',
      },
      text: {
        primary: accessibilitySettings.settings.highContrast ? '#000000' : '#333333',
      },
    },
    typography: {
      fontSize: {
        small: 14,
        medium: 16,
        large: 18,
        'extra-large': 20,
      }[accessibilitySettings.settings.fontSize],
      fontFamily: accessibilitySettings.settings.dyslexiaSupport
        ? '"OpenDyslexic", "Comic Sans MS", cursive'
        : '"Inter", "system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            minHeight: accessibilitySettings.settings.motorImpairmentSupport ? 60 : 44,
            minWidth: accessibilitySettings.settings.motorImpairmentSupport ? 60 : 44,
            fontSize: {
              small: '0.875rem',
              medium: '1rem',
              large: '1.125rem',
              'extra-large': '1.25rem',
            }[accessibilitySettings.settings.fontSize],
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiInputBase-root': {
              minHeight: accessibilitySettings.settings.motorImpairmentSupport ? 60 : 44,
            },
          },
        },
      },
    },
  });

  // Erişilebilirlik ayarları değiştiğinde duyuru yap
  useEffect(() => {
    const status = accessibilitySettings?.getAccessibilityStatus?.();
    if (status?.isOptimized) {
      announce(status.summary, 'polite');
    }
  }, [accessibilitySettings?.settings, announce, accessibilitySettings]);

  const contextValue: AccessibilityContextType = {
    settings: accessibilitySettings.settings,
    updateSetting: accessibilitySettings.updateSetting,
    toggleHighContrast: accessibilitySettings.toggleHighContrast,
    toggleReducedMotion: accessibilitySettings.toggleReducedMotion,
    increaseFontSize: accessibilitySettings.increaseFontSize,
    decreaseFontSize: accessibilitySettings.decreaseFontSize,
    announce,
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </AccessibilityContext.Provider>
  );
};

export default AccessibilityProvider;