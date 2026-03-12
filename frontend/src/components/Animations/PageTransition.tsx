/**
 * Page Transition Component
 * Smooth animations between page navigations
 */

import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import { useLocation } from 'react-router-dom';

import { useSettingsStore } from '../../store/settingsStore';

export interface PageTransitionProps {
  children: React.ReactNode
  /** Transition variant */
  variant?: 'fade' | 'slide' | 'scale' | 'fadeUp'
  /** Transition duration in seconds */
  duration?: number
}

const transitionVariants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  slide: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
  },
  scale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.05 },
  },
  fadeUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },
};

export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  variant = 'fadeUp',
  duration = 0.3,
}) => {
  const location = useLocation();
  const reduceMotion = useSettingsStore((s) => s.accessibility.reduceMotion);
  const variants = transitionVariants[variant];

  if (reduceMotion) {
    return <div style={{ width: '100%', minHeight: '100vh' }}>{children}</div>;
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={variants.initial}
        animate={variants.animate}
        exit={variants.exit}
        transition={{
          duration,
          ease: [0.4, 0, 0.2, 1], // Custom cubic-bezier
        }}
        style={{
          width: '100%',
          minHeight: '100vh',
        }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * Route Transition Wrapper
 * Wraps individual routes with transition
 */
export const RouteTransition: React.FC<{
  children: React.ReactNode
  variant?: PageTransitionProps['variant']
}> = ({ children, variant: _variant = 'fadeUp' }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * Stagger Children Animation
 * Animates children elements with stagger effect
 */
export const StaggerContainer: React.FC<{
  children: React.ReactNode
  staggerDelay?: number
  className?: string
}> = ({ children, staggerDelay = 0.1, className }) => {
  const reduceMotion = useSettingsStore((s) => s.accessibility.reduceMotion);

  if (reduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial="hidden"
      animate="visible"
      variants={{
        visible: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * Stagger Item
 * Individual item in stagger container
 */
export const StaggerItem: React.FC<{
  children: React.ReactNode
  className?: string
  sx?: { mt?: number; mb?: number; mx?: number; my?: number; p?: number; [key: string]: any }
}> = ({ children, className, sx }) => {
  // Convert MUI-style sx to CSS properties
  const style: React.CSSProperties = sx ? {
    marginTop: sx.mt ? `${sx.mt * 8}px` : undefined,
    marginBottom: sx.mb ? `${sx.mb * 8}px` : undefined,
    marginLeft: sx.mx ? `${sx.mx * 8}px` : undefined,
    marginRight: sx.mx ? `${sx.mx * 8}px` : undefined,
    padding: sx.p ? `${sx.p * 8}px` : undefined,
  } : {};
  return (
    <motion.div
      className={className}
      style={style}
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 },
      }}
      transition={{
        duration: 0.4,
        ease: [0.4, 0, 0.2, 1],
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * Slide In Animation
 * Slides element in from specified direction
 */
export const SlideIn: React.FC<{
  children: React.ReactNode
  direction?: 'left' | 'right' | 'up' | 'down'
  delay?: number
  className?: string
}> = ({ children, direction = 'up', delay = 0, className }) => {
  const directions = {
    left: { x: -50, y: 0 },
    right: { x: 50, y: 0 },
    up: { x: 0, y: 50 },
    down: { x: 0, y: -50 },
  };

  const offset = directions[direction];

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, ...offset }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{
        duration: 0.5,
        delay,
        ease: [0.4, 0, 0.2, 1],
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * Scale In Animation
 * Scales element in with bounce effect
 */
export const ScaleIn: React.FC<{
  children: React.ReactNode
  delay?: number
  className?: string
}> = ({ children, delay = 0, className }) => {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.5,
        delay,
        ease: [0.34, 1.56, 0.64, 1], // Bounce easing
      }}
    >
      {children}
    </motion.div>
  );
};

/**
 * Fade In Animation
 * Simple fade in with optional delay
 */
export const FadeIn: React.FC<{
  children: React.ReactNode
  delay?: number
  duration?: number
  className?: string
}> = ({ children, delay = 0, duration = 0.5, className }) => {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{
        duration,
        delay,
        ease: 'easeOut',
      }}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;
