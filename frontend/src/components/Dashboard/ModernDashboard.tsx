/**
 * Modern Dashboard Component
 * Enhanced dashboard with responsive design and performance optimizations
 */

import React, { memo, useCallback, useMemo } from 'react'
import { 
  Grid, 
  Typography, 
  Box, 
  Paper,
  IconButton,
  Menu,
  MenuItem,
  Fade,
  useTheme
} from '@mui/material'
import { 
  MoreVert as MoreIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  Schedule as ScheduleIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material'

import { ModernCard } from '../ui/modern-card'
import { ModernButton } from '../ui/modern-button'
import { useResponsive } from '../../utils/responsive'
import { useAuthStore } from '@/store/authStore'

interface DashboardStats {
  completedExams: number
  averageScore: number
  studyTime: number
  upcomingExams: number
}

interface DashboardProps {
  stats?: DashboardStats
  loading?: boolean
}

// Stat card component
const StatCard = memo(({ 
  title, 
  value, 
  icon, 
  color = 'primary',
  loading = false 
}: {
  title: string
  value: string | number
  icon: React.ReactNode
  color?: 'primary' | 'secondary' | 'success' | 'warning'
  loading?: boolean
}) => {
  const theme = useTheme()
  
  return (
    <ModernCard loading={loading} size="small">
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box
          sx={{
            p: 1.5,
            borderRadius: 2,
            backgroundColor: theme.palette[color].main,
            color: theme.palette[color].contrastText,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {icon}
        </Box>
        
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" component="div" sx={{ fontWeight: 700, mb: 0.5 }}>
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
        </Box>
      </Box>
    </ModernCard>
  )
})

StatCard.displayName = 'StatCard'

// Recent activity component
const RecentActivity = memo(() => {
  const activities = useMemo(() => [
    { id: 1, title: 'Matematik Sınavı Tamamlandı', time: '2 saat önce', type: 'exam' },
    { id: 2, title: 'Fizik Dersi İzlendi', time: '5 saat önce', type: 'study' },
    { id: 3, title: 'Kimya Ödevi Gönderildi', time: '1 gün önce', type: 'assignment' }
  ], [])
  
  return (
    <ModernCard title="Son Aktiviteler" size="medium">
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {activities.map((activity) => (
          <Box 
            key={activity.id}
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 2,
              p: 2,
              borderRadius: 1,
              backgroundColor: 'background.paper',
              border: 1,
              borderColor: 'divider'
            }}
          >
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: activity.type === 'exam' ? 'success.main' : 
                               activity.type === 'study' ? 'primary.main' : 'warning.main'
              }}
            />
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {activity.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {activity.time}
              </Typography>
            </Box>
          </Box>
        ))}
      </Box>
    </ModernCard>
  )
})

RecentActivity.displayName = 'RecentActivity'

// Quick actions component
const QuickActions = memo(() => {
  const { isMobile } = useResponsive()
  
  const actions = useMemo(() => [
    { label: 'Sınav Başlat', color: 'primary', variant: 'contained' },
    { label: 'Ders İzle', color: 'secondary', variant: 'outlined' },
    { label: 'Ödev Gönder', color: 'success', variant: 'outlined' },
    { label: 'İstatistikler', color: 'info', variant: 'outlined' }
  ] as const, [])
  
  return (
    <ModernCard title="Hızlı İşlemler" size="medium">
      <Grid container spacing={2}>
        {actions.map((action, index) => (
          <Grid item xs={isMobile ? 12 : 6} key={index}>
            <ModernButton
              fullWidth
              variant={action.variant}
              color={action.color}
              size="large"
              touchOptimized
            >
              {action.label}
            </ModernButton>
          </Grid>
        ))}
      </Grid>
    </ModernCard>
  )
})

QuickActions.displayName = 'QuickActions'

export const ModernDashboard: React.FC<DashboardProps> = memo(({ 
  stats = {
    completedExams: 12,
    averageScore: 85,
    studyTime: 24,
    upcomingExams: 3
  },
  loading = false 
}) => {
  const {  user  } = useAuthStore()
  const { isMobile } = useResponsive()
  const [menuAnchor, setMenuAnchor] = React.useState<null | HTMLElement>(null)
  
  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget)
  }, [])
  
  const handleMenuClose = useCallback(() => {
    setMenuAnchor(null)
  }, [])
  
  // Memoize stat cards data
  const statCards = useMemo(() => [
    {
      title: 'Tamamlanan Sınavlar',
      value: stats.completedExams,
      icon: <AssignmentIcon />,
      color: 'primary' as const
    },
    {
      title: 'Ortalama Puan',
      value: `${stats.averageScore}%`,
      icon: <TrendingUpIcon />,
      color: 'success' as const
    },
    {
      title: 'Çalışma Saati',
      value: `${stats.studyTime}h`,
      icon: <ScheduleIcon />,
      color: 'warning' as const
    },
    {
      title: 'Yaklaşan Sınavlar',
      value: stats.upcomingExams,
      icon: <AnalyticsIcon />,
      color: 'secondary' as const
    }
  ], [stats])
  
  return (
    <Fade in timeout={500}>
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 1 }}>
              Merhaba, {user?.adi || 'Öğrenci'}! 👋
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Bugün nasıl ilerleme kaydedeceğiz?
            </Typography>
          </Box>
          
          <IconButton 
            onClick={handleMenuOpen}
            sx={{ display: { xs: 'block', md: 'none' } }}
          >
            <MoreIcon />
          </IconButton>
          
          <Menu
            anchorEl={menuAnchor}
            open={Boolean(menuAnchor)}
            onClose={handleMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleMenuClose}>Ayarlar</MenuItem>
            <MenuItem onClick={handleMenuClose}>Yardım</MenuItem>
            <MenuItem onClick={handleMenuClose}>Geri Bildirim</MenuItem>
          </Menu>
        </Box>
        
        {/* Stats Grid */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {statCards.map((stat, index) => (
            <Grid item xs={12} sm={6} lg={3} key={index}>
              <StatCard {...stat} loading={loading} />
            </Grid>
          ))}
        </Grid>
        
        {/* Main Content Grid */}
        <Grid container spacing={3}>
          {/* Recent Activity */}
          <Grid item xs={12} md={8}>
            <RecentActivity />
          </Grid>
          
          {/* Quick Actions */}
          <Grid item xs={12} md={4}>
            <QuickActions />
          </Grid>
          
          {/* Performance Chart Placeholder */}
          <Grid item xs={12}>
            <ModernCard title="Performans Grafiği" size="large">
              <Box 
                sx={{ 
                  height: 300, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  backgroundColor: 'background.default',
                  borderRadius: 1
                }}
              >
                <Typography variant="body1" color="text.secondary">
                  Grafik yakında eklenecek...
                </Typography>
              </Box>
            </ModernCard>
          </Grid>
        </Grid>
      </Box>
    </Fade>
  )
})

ModernDashboard.displayName = 'ModernDashboard'

export default ModernDashboard