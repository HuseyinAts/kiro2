/**
 * Modern Loader Component
 * Beautiful loading states with animations
 */

import { Box, CircularProgress, Typography } from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';

import modernColors from '@/theme/modern-colors';

export interface ModernLoaderProps {
  /** Loading message */
  message?: string
  /** Loader size */
  size?: 'small' | 'medium' | 'large'
  /** Full screen loader */
  fullScreen?: boolean
  /** Show gradient text */
  gradientText?: boolean
}

export const ModernLoader: React.FC<ModernLoaderProps> = ({
  message = 'Yükleniyor...',
  size = 'medium',
  fullScreen = false,
  gradientText = true,
}) => {
  const sizeConfig = {
    small: { loader: 40, fontSize: '0.875rem' },
    medium: { loader: 60, fontSize: '1rem' },
    large: { loader: 80, fontSize: '1.125rem' },
  };

  const config = sizeConfig[size];

  const containerStyle = fullScreen
    ? {
        position: 'fixed' as const,
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        zIndex: 9999,
      }
    : {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '200px',
        width: '100%',
      };

  return (
    <Box sx={containerStyle}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3,
        }}
      >
        {/* Animated Loader */}
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            rotate: [0, 360],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          <Box
            sx={{
              position: 'relative',
              display: 'inline-flex',
            }}
          >
            {/* Outer ring with gradient */}
            <CircularProgress
              size={config.loader}
              thickness={3}
              sx={{
                color: modernColors.primary[500],
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                },
              }}
            />

            {/* Inner glow effect */}
            <Box
              sx={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: config.loader * 0.7,
                height: config.loader * 0.7,
                borderRadius: '50%',
                background: modernColors.gradients.primary,
                opacity: 0.2,
                filter: 'blur(10px)',
              }}
            />
          </Box>
        </motion.div>

        {/* Loading Message */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Typography
            variant="body1"
            sx={{
              fontSize: config.fontSize,
              fontWeight: 600,
              ...(gradientText
                ? {
                    background: modernColors.gradients.primary,
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                  }
                : {
                    color: 'text.primary',
                  }),
            }}
          >
            {message}
          </Typography>
        </motion.div>

        {/* Animated Dots */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              animate={{
                y: [0, -8, 0],
              }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: index * 0.15,
                ease: 'easeInOut',
              }}
            >
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: modernColors.gradients.primary,
                }}
              />
            </motion.div>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

/**
 * Simple Spinner Component
 */
export const ModernSpinner: React.FC<{ size?: number }> = ({ size = 40 }) => {
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Infinity,
        ease: 'linear',
      }}
    >
      <CircularProgress
        size={size}
        thickness={4}
        sx={{
          color: modernColors.primary[500],
          '& .MuiCircularProgress-circle': {
            strokeLinecap: 'round',
          },
        }}
      />
    </motion.div>
  );
};

/**
 * Skeleton Loader Component
 */
export interface SkeletonLoaderProps {
  lines?: number
  avatar?: boolean
  height?: number
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  lines = 3,
  avatar = false,
  height = 16,
}) => {
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', gap: 2, mb: avatar ? 2 : 0 }}>
        {avatar && (
          <motion.div
            animate={{ opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                background: modernColors.glass.black.light,
              }}
            />
          </motion.div>
        )}
        <Box sx={{ flex: 1 }}>
          {Array.from({ length: lines }).map((_, index) => (
            <motion.div
              key={index}
              animate={{ opacity: [0.4, 0.8, 0.4] }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                delay: index * 0.2,
              }}
            >
              <Box
                sx={{
                  height: height,
                  mb: 1.5,
                  borderRadius: '8px',
                  background: modernColors.glass.black.light,
                  width: index === lines - 1 ? '70%' : '100%',
                }}
              />
            </motion.div>
          ))}
        </Box>
      </Box>
    </Box>
  );
};

export default ModernLoader;
