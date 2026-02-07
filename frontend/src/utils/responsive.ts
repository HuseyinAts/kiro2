/**
 * Responsive Design System
 * Modern responsive utilities and breakpoint helpers
 */

/* eslint-disable react-hooks/rules-of-hooks */
// Note: up/down/between functions intentionally call hooks inside object methods
// These should only be called at the top level of components, not in callbacks

import { useTheme, useMediaQuery, Theme } from '@mui/material';
import { useMemo } from 'react';

// Breakpoint utilities
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 900,
  lg: 1200,
  xl: 1536,
} as const;

export type Breakpoint = keyof typeof breakpoints

// Responsive hook for modern breakpoint detection
export const useResponsive = () => {
  const theme = useTheme();

  const isXs = useMediaQuery(theme.breakpoints.only('xs'));
  const isSm = useMediaQuery(theme.breakpoints.only('sm'));
  const isMd = useMediaQuery(theme.breakpoints.only('md'));
  const isLg = useMediaQuery(theme.breakpoints.only('lg'));
  const isXl = useMediaQuery(theme.breakpoints.only('xl'));

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('md', 'lg'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('lg'));

  const currentBreakpoint: Breakpoint = useMemo(() => {
    if (isXs) {return 'xs' as const;}
    if (isSm) {return 'sm' as const;}
    if (isMd) {return 'md' as const;}
    if (isLg) {return 'lg' as const;}
    if (isXl) {return 'xl' as const;}
    return 'md' as const;
  }, [isXs, isSm, isMd, isLg, isXl]);

  return {
    // Individual breakpoints
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,

    // Device categories
    isMobile,
    isTablet,
    isDesktop,

    // Current breakpoint
    currentBreakpoint,

    // Utility functions - call at component top level only, not in callbacks
    up: (breakpoint: Breakpoint) => useMediaQuery(theme.breakpoints.up(breakpoint)),
    down: (breakpoint: Breakpoint) => useMediaQuery(theme.breakpoints.down(breakpoint)),
    between: (start: Breakpoint, end: Breakpoint) =>
      useMediaQuery(theme.breakpoints.between(start, end)),
  };
};

// Responsive value selector
export const useResponsiveValue = <T>(values: Partial<Record<Breakpoint, T>>) => {
  const { currentBreakpoint } = useResponsive();

  return useMemo(() => {
    // Try current breakpoint first
    if (values[currentBreakpoint]) {
      return values[currentBreakpoint];
    }

    // Fallback to smaller breakpoints
    const orderedBreakpoints: Breakpoint[] = ['xs', 'sm', 'md', 'lg', 'xl'];
    const currentIndex = orderedBreakpoints.indexOf(currentBreakpoint);

    for (let i = currentIndex - 1; i >= 0; i--) {
      const breakpoint = orderedBreakpoints[i];
      if (values[breakpoint]) {
        return values[breakpoint];
      }
    }

    // Fallback to largest available
    for (let i = currentIndex + 1; i < orderedBreakpoints.length; i++) {
      const breakpoint = orderedBreakpoints[i];
      if (values[breakpoint]) {
        return values[breakpoint];
      }
    }

    return undefined;
  }, [values, currentBreakpoint]);
};

// Grid system utilities
export const getResponsiveSpacing = (_theme: Theme, size: 'small' | 'medium' | 'large' = 'medium') => {
  const spacingMap = {
    small: { xs: 1, sm: 2, md: 3 },
    medium: { xs: 2, sm: 3, md: 4 },
    large: { xs: 3, sm: 4, md: 6 },
  };

  return spacingMap[size];
};

// Container utilities
export const getResponsiveContainer = (theme: Theme) => ({
  maxWidth: {
    xs: '100%',
    sm: theme.breakpoints.values.sm,
    md: theme.breakpoints.values.md,
    lg: theme.breakpoints.values.lg,
    xl: theme.breakpoints.values.xl,
  },
  mx: 'auto',
  px: { xs: 2, sm: 3, md: 4 },
});

// Typography responsive utilities
export const getResponsiveTypography = (variant: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2') => {
  const scales = {
    h1: { xs: '2rem', sm: '2.5rem', md: '3rem', lg: '3.5rem' },
    h2: { xs: '1.75rem', sm: '2rem', md: '2.5rem', lg: '3rem' },
    h3: { xs: '1.5rem', sm: '1.75rem', md: '2rem', lg: '2.25rem' },
    h4: { xs: '1.25rem', sm: '1.5rem', md: '1.75rem', lg: '2rem' },
    h5: { xs: '1.125rem', sm: '1.25rem', md: '1.5rem', lg: '1.75rem' },
    h6: { xs: '1rem', sm: '1.125rem', md: '1.25rem', lg: '1.5rem' },
    body1: { xs: '0.875rem', sm: '1rem', md: '1rem', lg: '1.125rem' },
    body2: { xs: '0.75rem', sm: '0.875rem', md: '0.875rem', lg: '1rem' },
  };

  return { fontSize: scales[variant] };
};

// Touch-optimized sizes
export const getTouchOptimizedSize = (size: 'small' | 'medium' | 'large') => {
  const sizes = {
    small: { minHeight: 40, minWidth: 40 },
    medium: { minHeight: 48, minWidth: 48 },
    large: { minHeight: 56, minWidth: 56 },
  };

  return sizes[size];
};

// Responsive grid columns
export const getResponsiveColumns = (config: {
  xs?: number
  sm?: number
  md?: number
  lg?: number
  xl?: number
}) => {
  return {
    xs: 12 / (config.xs || 1),
    sm: 12 / (config.sm || config.xs || 1),
    md: 12 / (config.md || config.sm || config.xs || 1),
    lg: 12 / (config.lg || config.md || config.sm || config.xs || 1),
    xl: 12 / (config.xl || config.lg || config.md || config.sm || config.xs || 1),
  };
};

// Safe area utilities for mobile devices
export const getSafeAreaStyles = () => ({
  paddingTop: 'env(safe-area-inset-top)',
  paddingBottom: 'env(safe-area-inset-bottom)',
  paddingLeft: 'env(safe-area-inset-left)',
  paddingRight: 'env(safe-area-inset-right)',
});

// Animation utilities for responsive design
export const getResponsiveAnimation = (isMobile: boolean) => ({
  transition: isMobile ? 'none' : 'all 0.3s ease-in-out',
  animationDuration: isMobile ? '0s' : undefined,
});

export default {
  useResponsive,
  useResponsiveValue,
  getResponsiveSpacing,
  getResponsiveContainer,
  getResponsiveTypography,
  getTouchOptimizedSize,
  getResponsiveColumns,
  getSafeAreaStyles,
  getResponsiveAnimation,
};