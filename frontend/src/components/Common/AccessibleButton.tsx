/**
 * WCAG 2.1 Level AA Uyumlu Erişilebilir Buton Bileşeni
 * 
 * Özellikler:
 * - Klavye navigasyonu (Tab, Enter, Space)
 * - Ekran okuyucu desteği
 * - Yüksek kontrast renk desteği
 * - Focus yönetimi
 * - ARIA etiketleri
 */

import React, { forwardRef, KeyboardEvent, MouseEvent } from 'react';
import { Button, ButtonProps, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';

interface AccessibleButtonProps extends Omit<ButtonProps, 'onClick'> {
  onClick?: (event: MouseEvent<HTMLButtonElement> | KeyboardEvent<HTMLButtonElement>) => void;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  loading?: boolean;
  loadingText?: string;
  highContrast?: boolean;
}

const StyledAccessibleButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== 'highContrast',
})<{ highContrast?: boolean }>(({ theme, highContrast }) => ({
  // WCAG 2.1 AA minimum kontrast oranı: 4.5:1
  minHeight: '44px', // WCAG minimum dokunma hedefi boyutu
  minWidth: '44px',
  
  // Focus görünürlüğü
  '&:focus-visible': {
    outline: `3px solid ${theme.palette.primary.main}`,
    outlineOffset: '2px',
    boxShadow: `0 0 0 3px ${theme.palette.primary.main}40`,
  },
  
  // Yüksek kontrast modu
  ...(highContrast && {
    backgroundColor: '#000000',
    color: '#FFFFFF',
    border: '2px solid #FFFFFF',
    '&:hover': {
      backgroundColor: '#FFFFFF',
      color: '#000000',
      border: '2px solid #000000',
    },
    '&:focus-visible': {
      outline: '3px solid #FFFF00',
      outlineOffset: '2px',
    },
    '&:disabled': {
      backgroundColor: '#666666',
      color: '#CCCCCC',
      border: '2px solid #CCCCCC',
    },
  }),
  
  // Animasyonları azalt (prefers-reduced-motion)
  '@media (prefers-reduced-motion: reduce)': {
    transition: 'none',
  },
}));

export const AccessibleButton = forwardRef<HTMLButtonElement, AccessibleButtonProps>(
  (
    {
      onClick,
      onKeyDown,
      ariaLabel,
      ariaDescribedBy,
      loading = false,
      loadingText = 'Yükleniyor...',
      highContrast = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const theme = useTheme();

    const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
      if (loading || disabled) return;
      onClick?.(event);
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
      // Enter ve Space tuşları ile aktivasyon
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        if (!loading && !disabled) {
          onClick?.(event);
        }
      }
      onKeyDown?.(event);
    };

    return (
      <StyledAccessibleButton
        ref={ref}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        disabled={disabled || loading}
        aria-label={ariaLabel || (typeof children === 'string' ? children : undefined)}
        aria-describedby={ariaDescribedBy}
        aria-busy={loading}
        highContrast={highContrast}
        role="button"
        tabIndex={disabled ? -1 : 0}
        {...props}
      >
        {loading ? loadingText : children}
      </StyledAccessibleButton>
    );
  }
);

AccessibleButton.displayName = 'AccessibleButton';

export default AccessibleButton;