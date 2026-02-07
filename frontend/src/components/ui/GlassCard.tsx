/**
 * Glassmorphism Card Component
 * Modern frosted glass effect with blur and transparency
 */

import { MoreVert as MoreIcon } from '@mui/icons-material';
import { Box, Typography, IconButton } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import { motion, HTMLMotionProps } from 'framer-motion';
import * as React from 'react';
import {  forwardRef  } from 'react';

import modernColors from '@/theme/modern-colors';

export interface GlassCardProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  /** Card title */
  title?: string
  /** Card subtitle */
  subtitle?: string
  /** Icon element to display */
  icon?: React.ReactNode
  /** Gradient background (defaults to primary gradient) */
  gradient?: string
  /** Glass intensity: 'light' | 'medium' | 'dark' */
  glassIntensity?: 'light' | 'medium' | 'dark'
  /** Enable hover effect */
  hoverable?: boolean
  /** Menu click handler */
  onMenuClick?: () => void
  /** Elevated style with stronger shadow */
  elevated?: boolean
  /** Border color (defaults to glass border) */
  borderColor?: string
  /** Children content */
  children: React.ReactNode
  /** Custom className */
  className?: string
  /** Test ID for testing */
  'data-testid'?: string
  /** MUI sx prop for additional styling */
  sx?: SxProps<Theme>
}

const glassIntensities = {
  light: modernColors.glass.white.light,
  medium: modernColors.glass.white.medium,
  dark: modernColors.glass.white.dark,
};

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(({
  title,
  subtitle,
  icon,
  gradient = modernColors.gradients.primary,
  glassIntensity = 'medium',
  hoverable = false,
  onMenuClick,
  elevated = false,
  borderColor = modernColors.glass.border,
  children,
  className = '',
  'data-testid': testId,
  onClick,
  sx,
  ...motionProps
}, ref) => {
  const backgroundOpacity = glassIntensities[glassIntensity];

  return (
    <motion.div
      ref={ref}
      onClick={onClick}
      data-testid={testId}
      className={className}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={hoverable ? { scale: 1.02, y: -4 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      }}
      style={{
        position: 'relative',
        borderRadius: '20px',
        overflow: 'hidden',
        cursor: onClick ? 'pointer' : 'default',
      }}
      {...motionProps}
    >
      {/* Gradient Border Top */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: gradient,
        }}
      />

      {/* Glass Background */}
      <Box
        sx={{
          background: backgroundOpacity,
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: `1px solid ${borderColor}`,
          borderTop: 'none',
          borderRadius: '20px',
          padding: '24px',
          boxShadow: elevated ? modernColors.shadow.glass : modernColors.shadow.md,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': hoverable ? {
            boxShadow: modernColors.shadow.modern,
            borderColor: modernColors.glass.white.medium,
          } : {},
          ...sx as object,
        }}
      >
        {/* Header */}
        {(icon || title || subtitle || onMenuClick) && (
          <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: title || subtitle ? 3 : 0 }}>
            {/* Icon */}
            {icon && (
              <Box
                sx={{
                  mr: 2,
                  color: 'primary.main',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 48,
                  height: 48,
                  borderRadius: '12px',
                  background: modernColors.glass.white.light,
                  backdropFilter: 'blur(8px)',
                }}
              >
                {icon}
              </Box>
            )}

            {/* Title & Subtitle */}
            <Box sx={{ flex: 1 }}>
              {title && (
                <Typography
                  variant="h5"
                  component="h3"
                  sx={{
                    fontWeight: 700,
                    mb: subtitle ? 0.5 : 0,
                    background: gradient,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }}
                >
                  {title}
                </Typography>
              )}
              {subtitle && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ fontWeight: 500 }}
                >
                  {subtitle}
                </Typography>
              )}
            </Box>

            {/* Menu Button */}
            {onMenuClick && (
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onMenuClick();
                }}
                sx={{
                  ml: 1,
                  background: modernColors.glass.white.light,
                  backdropFilter: 'blur(8px)',
                  '&:hover': {
                    background: modernColors.glass.white.medium,
                  },
                }}
              >
                <MoreIcon />
              </IconButton>
            )}
          </Box>
        )}

        {/* Content */}
        <Box>{children}</Box>
      </Box>
    </motion.div>
  );
});

GlassCard.displayName = 'GlassCard';

export default GlassCard;
