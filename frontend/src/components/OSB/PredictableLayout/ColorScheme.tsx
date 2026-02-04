/**
 * Task 93.3: Consistent Color Scheme System
 * OSB desteği için değişmeyen renk paleti
 *
 * Özellikler:
 * - Asla değişmeyen renk değerleri
 * - Tutarlı renk kullanımı
 * - Tanıdık renkler
 * - Tema değişikliği yok (OSB modunda)
 */

import React, { createContext, useContext, ReactNode } from 'react';
import './ColorScheme.css';

/**
 * OSB için sabit renk paleti
 * Bu renkler ASLA değişmez
 */
export const OSB_COLOR_PALETTE = {
  // Primary colors - Ana renkler (ASLA DEĞİŞMEZ)
  primary: {
    main: '#0d6efd', // Mavi - her zaman aynı
    light: '#6ea8fe',
    dark: '#0a58ca',
    contrast: '#ffffff'
  },

  // Secondary colors - İkincil renkler
  secondary: {
    main: '#6c757d', // Gri - her zaman aynı
    light: '#adb5bd',
    dark: '#495057',
    contrast: '#ffffff'
  },

  // Success - Başarı rengi (her zaman yeşil)
  success: {
    main: '#198754',
    light: '#75b798',
    dark: '#146c43',
    contrast: '#ffffff'
  },

  // Warning - Uyarı rengi (her zaman sarı)
  warning: {
    main: '#ffc107',
    light: '#ffcd39',
    dark: '#cc9a06',
    contrast: '#000000'
  },

  // Error - Hata rengi (her zaman kırmızı)
  error: {
    main: '#dc3545',
    light: '#e35d6a',
    dark: '#b02a37',
    contrast: '#ffffff'
  },

  // Info - Bilgi rengi (her zaman açık mavi)
  info: {
    main: '#0dcaf0',
    light: '#3dd5f3',
    dark: '#087990',
    contrast: '#000000'
  },

  // Neutral colors - Nötr renkler (ASLA DEĞİŞMEZ)
  neutral: {
    white: '#ffffff',
    black: '#000000',
    gray100: '#f8f9fa',
    gray200: '#e9ecef',
    gray300: '#dee2e6',
    gray400: '#ced4da',
    gray500: '#adb5bd',
    gray600: '#6c757d',
    gray700: '#495057',
    gray800: '#343a40',
    gray900: '#212529'
  },

  // Background colors - Arka plan renkleri
  background: {
    default: '#f8f9fa',
    paper: '#ffffff',
    elevated: '#ffffff'
  },

  // Text colors - Metin renkleri
  text: {
    primary: '#212529',
    secondary: '#6c757d',
    disabled: '#adb5bd',
    hint: '#ced4da'
  },

  // Border colors - Kenarlık renkleri
  border: {
    default: '#dee2e6',
    light: '#e9ecef',
    dark: '#adb5bd'
  }
} as const;

/**
 * Renk kullanım kuralları
 * Her renk her zaman aynı amaç için kullanılır
 */
export const COLOR_USAGE = {
  // Button colors
  buttonPrimary: OSB_COLOR_PALETTE.primary.main,
  buttonSecondary: OSB_COLOR_PALETTE.secondary.main,
  buttonSuccess: OSB_COLOR_PALETTE.success.main,
  buttonWarning: OSB_COLOR_PALETTE.warning.main,
  buttonDanger: OSB_COLOR_PALETTE.error.main,

  // Link colors
  link: OSB_COLOR_PALETTE.primary.main,
  linkHover: OSB_COLOR_PALETTE.primary.dark,
  linkVisited: OSB_COLOR_PALETTE.primary.dark,

  // Form colors
  inputBorder: OSB_COLOR_PALETTE.border.default,
  inputFocus: OSB_COLOR_PALETTE.primary.main,
  inputError: OSB_COLOR_PALETTE.error.main,
  inputSuccess: OSB_COLOR_PALETTE.success.main,

  // Status colors
  statusSuccess: OSB_COLOR_PALETTE.success.main,
  statusWarning: OSB_COLOR_PALETTE.warning.main,
  statusError: OSB_COLOR_PALETTE.error.main,
  statusInfo: OSB_COLOR_PALETTE.info.main
} as const;

interface ColorSchemeContextValue {
  palette: typeof OSB_COLOR_PALETTE;
  usage: typeof COLOR_USAGE;
  osbMode: boolean;
}

const ColorSchemeContext = createContext<ColorSchemeContextValue>({
  palette: OSB_COLOR_PALETTE,
  usage: COLOR_USAGE,
  osbMode: true
});

export const useColorScheme = () => useContext(ColorSchemeContext);

interface ColorSchemeProviderProps {
  children: ReactNode;
  osbMode?: boolean;
}

/**
 * Color Scheme Provider
 * OSB modunda renk değişikliği yapılamaz
 */
export const ColorSchemeProvider: React.FC<ColorSchemeProviderProps> = ({
  children,
  osbMode = true
}) => {
  // OSB modunda tema değişikliği devre dışı
  const value: ColorSchemeContextValue = {
    palette: OSB_COLOR_PALETTE,
    usage: COLOR_USAGE,
    osbMode
  };

  return (
    <ColorSchemeContext.Provider value={value}>
      <div
        className={`color-scheme-root ${osbMode ? 'osb-mode' : ''}`}
        style={{
          '--color-primary': OSB_COLOR_PALETTE.primary.main,
          '--color-primary-light': OSB_COLOR_PALETTE.primary.light,
          '--color-primary-dark': OSB_COLOR_PALETTE.primary.dark,
          '--color-secondary': OSB_COLOR_PALETTE.secondary.main,
          '--color-success': OSB_COLOR_PALETTE.success.main,
          '--color-warning': OSB_COLOR_PALETTE.warning.main,
          '--color-error': OSB_COLOR_PALETTE.error.main,
          '--color-info': OSB_COLOR_PALETTE.info.main,
          '--color-bg-default': OSB_COLOR_PALETTE.background.default,
          '--color-bg-paper': OSB_COLOR_PALETTE.background.paper,
          '--color-text-primary': OSB_COLOR_PALETTE.text.primary,
          '--color-text-secondary': OSB_COLOR_PALETTE.text.secondary,
          '--color-border': OSB_COLOR_PALETTE.border.default
        } as React.CSSProperties}
      >
        {children}
      </div>
    </ColorSchemeContext.Provider>
  );
};

/**
 * Renk sınıfları component'i
 * Tutarlı renk kullanımı için yardımcı component
 */
interface ColorBoxProps {
  variant: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
  children: ReactNode;
  className?: string;
}

export const ColorBox: React.FC<ColorBoxProps> = ({
  variant,
  children,
  className = ''
}) => {
  return (
    <div className={`color-box color-box--${variant} ${className}`}>
      {children}
    </div>
  );
};

export default ColorSchemeProvider;
