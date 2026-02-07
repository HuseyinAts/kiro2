/**
 * Modern Button Component
 * Enhanced button with gradients, icons, and modern styling
 */

import { Button, ButtonProps, CircularProgress, Box } from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';
import {  forwardRef  } from 'react';

import modernColors from '@/theme/modern-colors';

export interface ModernButtonProps extends Omit<ButtonProps, 'variant'> {
  /** Button variant */
  variant?: 'gradient' | 'glass' | 'solid' | 'outlined' | 'text'
  /** Gradient background */
  gradient?: string
  /** Loading state */
  loading?: boolean
  /** Icon before text (alias for startIcon) */
  icon?: React.ReactNode
  /** Icon before text */
  startIcon?: React.ReactNode
  /** Icon after text */
  endIcon?: React.ReactNode
  /** Full width button */
  fullWidth?: boolean
  /** Button size */
  size?: 'small' | 'medium' | 'large'
  /** Enable glow effect */
  glow?: boolean
}

export const ModernButton = forwardRef<HTMLButtonElement, ModernButtonProps>(({
  variant = 'solid',
  gradient = modernColors.gradients.primary,
  loading = false,
  icon,
  startIcon,
  endIcon,
  fullWidth = false,
  size = 'medium',
  glow = false,
  children,
  disabled,
  ...buttonProps
}, ref) => {
  // Support both 'icon' and 'startIcon' props (icon takes precedence if both provided)
  const effectiveStartIcon = icon || startIcon;
  const sizeConfig = {
    small: {
      height: 36,
      px: 3,
      fontSize: '0.875rem',
    },
    medium: {
      height: 44,
      px: 4,
      fontSize: '0.9375rem',
    },
    large: {
      height: 52,
      px: 5,
      fontSize: '1rem',
    },
  };

  const config = sizeConfig[size];

  // Variant styles
  const variantStyles = {
    gradient: {
      background: gradient,
      color: '#FFFFFF',
      border: 'none',
      boxShadow: glow ? modernColors.shadow.glow : modernColors.shadow.md,
      '&:hover': {
        background: gradient,
        boxShadow: glow ? modernColors.shadow['glow-lg'] : modernColors.shadow.lg,
        transform: 'translateY(-2px)',
      },
      '&:active': {
        transform: 'translateY(0)',
      },
    },
    glass: {
      background: modernColors.glass.white.medium,
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: `1px solid ${modernColors.glass.border}`,
      color: 'text.primary',
      boxShadow: modernColors.shadow.sm,
      '&:hover': {
        background: modernColors.glass.white.light,
        boxShadow: modernColors.shadow.md,
        transform: 'translateY(-2px)',
      },
    },
    solid: {
      background: modernColors.primary[500],
      color: '#FFFFFF',
      border: 'none',
      boxShadow: modernColors.shadow.sm,
      '&:hover': {
        background: modernColors.primary[600],
        boxShadow: modernColors.shadow.lg,
        transform: 'translateY(-2px)',
      },
    },
    outlined: {
      background: 'transparent',
      border: `2px solid ${modernColors.primary[500]}`,
      color: modernColors.primary[500],
      '&:hover': {
        background: modernColors.primary[50],
        border: `2px solid ${modernColors.primary[600]}`,
        transform: 'translateY(-2px)',
      },
    },
    text: {
      background: 'transparent',
      color: modernColors.primary[500],
      '&:hover': {
        background: modernColors.primary[50],
      },
    },
  };

  const currentStyles = variantStyles[variant];

  return (
    <motion.div
      whileTap={{ scale: 0.98 }}
      style={{ width: fullWidth ? '100%' : 'auto' }}
    >
      <Button
        ref={ref}
        fullWidth={fullWidth}
        disabled={disabled || loading}
        startIcon={loading ? undefined : effectiveStartIcon}
        endIcon={loading ? undefined : endIcon}
        {...buttonProps}
        sx={{
          minHeight: config.height,
          px: config.px,
          fontSize: config.fontSize,
          fontWeight: 600,
          borderRadius: '12px',
          textTransform: 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative',
          overflow: 'hidden',
          ...currentStyles,
          '&:disabled': {
            opacity: 0.6,
            cursor: 'not-allowed',
          },
          ...buttonProps.sx,
        }}
      >
        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress
              size={20}
              sx={{
                color: variant === 'gradient' || variant === 'solid' ? '#FFFFFF' : 'primary.main',
              }}
            />
            <span>Yükleniyor...</span>
          </Box>
        ) : (
          children
        )}

        {/* Ripple effect background */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(255, 255, 255, 0.1)',
            opacity: 0,
            transition: 'opacity 0.3s',
            pointerEvents: 'none',
            '&:hover': {
              opacity: 1,
            },
          }}
        />
      </Button>
    </motion.div>
  );
});

ModernButton.displayName = 'ModernButton';

export default ModernButton;
