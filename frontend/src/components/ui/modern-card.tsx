/**
 * Modern Card Component
 * Optimized card component with accessibility and performance features
 */

import React, { memo, forwardRef } from 'react'
import { 
  Card as MuiCard, 
  CardContent, 
  CardHeader, 
  CardActions,
  Typography,
  Box,
  Skeleton,
  Fade,
  IconButton,
  useTheme
} from '@mui/material'
import { MoreVert as MoreIcon } from '@mui/icons-material'

interface ModernCardProps {
  title?: string
  subtitle?: string
  children: React.ReactNode
  actions?: React.ReactNode
  loading?: boolean
  elevation?: number
  variant?: 'default' | 'outlined' | 'elevated'
  size?: 'small' | 'medium' | 'large'
  className?: string
  onClick?: () => void
  onMenuClick?: () => void
  'aria-label'?: string
  'data-testid'?: string
}

// Loading skeleton component
const CardSkeleton = memo(({ size = 'medium' }: { size?: 'small' | 'medium' | 'large' }) => {
  const heights = {
    small: 120,
    medium: 200,
    large: 300
  }
  
  return (
    <MuiCard elevation={1}>
      <CardHeader
        title={<Skeleton variant="text" width="60%" />}
        subtitle={<Skeleton variant="text" width="40%" />}
      />
      <CardContent>
        <Skeleton variant="rectangular" height={heights[size]} />
      </CardContent>
    </MuiCard>
  )
})

CardSkeleton.displayName = 'CardSkeleton'

export const ModernCard = memo(forwardRef<HTMLDivElement, ModernCardProps>(({
  title,
  subtitle,
  children,
  actions,
  loading = false,
  elevation = 1,
  variant = 'default',
  size = 'medium',
  className,
  onClick,
  onMenuClick,
  'aria-label': ariaLabel,
  'data-testid': testId,
  ...props
}, ref) => {
  const theme = useTheme()
  
  // Size configurations
  const sizeConfig = {
    small: { p: 2, headerTypography: 'h6' },
    medium: { p: 3, headerTypography: 'h5' },
    large: { p: 4, headerTypography: 'h4' }
  } as const
  
  const config = sizeConfig[size]
  
  // Variant styles
  const variantStyles = {
    default: {
      elevation,
      sx: {}
    },
    outlined: {
      elevation: 0,
      sx: {
        border: 1,
        borderColor: 'divider'
      }
    },
    elevated: {
      elevation: 4,
      sx: {
        boxShadow: theme.shadows[8]
      }
    }
  }
  
  const cardStyles = variantStyles[variant]
  
  if (loading) {
    return <CardSkeleton size={size} />
  }
  
  return (
    <Fade in timeout={300}>
      <MuiCard
        ref={ref}
        elevation={cardStyles.elevation}
        className={className}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
        aria-label={ariaLabel}
        data-testid={testId}
        sx={{
          cursor: onClick ? 'pointer' : 'default',
          transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
          '&:hover': onClick ? {
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows[4]
          } : {},
          '&:focus-visible': {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: 2
          },
          ...cardStyles.sx
        }}
        onKeyDown={(e) => {
          if (onClick && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault()
            onClick()
          }
        }}
        {...props}
      >
        {(title || subtitle || onMenuClick) && (
          <CardHeader
            title={title && (
              <Typography 
                variant={config.headerTypography as any}
                component="h2"
                sx={{ fontWeight: 600 }}
              >
                {title}
              </Typography>
            )}
            subtitle={subtitle && (
              <Typography 
                variant="body2" 
                color="text.secondary"
                sx={{ mt: 0.5 }}
              >
                {subtitle}
              </Typography>
            )}
            action={onMenuClick && (
              <IconButton 
                aria-label="diğer seçenekler"
                onClick={(e) => {
                  e.stopPropagation()
                  onMenuClick()
                }}
                size="small"
              >
                <MoreIcon />
              </IconButton>
            )}
            sx={{ pb: title || subtitle ? 2 : 0 }}
          />
        )}
        
        <CardContent sx={{ p: config.p, '&:last-child': { pb: config.p } }}>
          <Box>
            {children}
          </Box>
        </CardContent>
        
        {actions && (
          <CardActions sx={{ px: config.p, pb: config.p }}>
            {actions}
          </CardActions>
        )}
      </MuiCard>
    </Fade>
  )
}))

ModernCard.displayName = 'ModernCard'

export default ModernCard