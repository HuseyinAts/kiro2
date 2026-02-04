import React from 'react'
import { Box, Toolbar, useTheme, useMediaQuery } from '@mui/material'
// import { RoleBasedNavigation } from '../Navigation/RoleBasedNavigation'  // Old navigation
import { ModernNavigation } from '../Navigation/ModernNavigation'  // New modern navigation
import { useAuthStore } from '@/store/authStore'
import modernColors from '@/theme/modern-colors'

interface RoleBasedLayoutProps {
  children: React.ReactNode
}

export const RoleBasedLayout: React.FC<RoleBasedLayoutProps> = ({ children }) => {
  const {  isAuthenticated  } = useAuthStore()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // Giriş yapılmamışsa navigation gösterme
  if (!isAuthenticated) {
    return <>{children}</>
  }

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Skip Navigation Link - WCAG 2.4.1 Bypass Blocks */}
      <Box
        component="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: '-9999px',
          zIndex: 9999,
          padding: '1rem',
          backgroundColor: 'primary.main',
          color: 'white',
          textDecoration: 'none',
          fontWeight: 600,
          '&:focus': {
            left: '1rem',
            top: '1rem',
          },
        }}
      >
        Ana içeriğe geç
      </Box>

      <ModernNavigation />
      <Box
        component="main"
        role="main"
        id="main-content"
        aria-label="Ana içerik"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - 280px)` },
          minHeight: '100vh',
          background: modernColors.background.gradient,
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}

export default RoleBasedLayout