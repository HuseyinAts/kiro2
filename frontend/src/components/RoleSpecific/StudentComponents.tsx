import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar
} from '@mui/material'
import {
  School,
  Assessment,
  TrendingUp,
  Star,
  PlayArrow,
  History,
  Chat,
  MenuBook
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

interface StudentQuickActionsProps {
  onExamStart?: () => void
  onChatOpen?: () => void
}

export const StudentQuickActions: React.FC<StudentQuickActionsProps> = ({
  onExamStart,
  onChatOpen
}) => {
  const navigate = useNavigate()

  const quickActions = [
    {
      label: 'Sınav Başlat',
      icon: <PlayArrow />,
      color: 'primary' as const,
      onClick: () => onExamStart ? onExamStart() : navigate('/exam/start')
    },
    {
      label: 'AI Sohbet',
      icon: <Chat />,
      color: 'secondary' as const,
      onClick: () => onChatOpen ? onChatOpen() : navigate('/chat')
    },
    {
      label: 'Sınav Geçmişi',
      icon: <History />,
      color: 'info' as const,
      onClick: () => navigate('/exam/history')
    },
    {
      label: 'Öğrenme Yolu',
      icon: <MenuBook />,
      color: 'success' as const,
      onClick: () => navigate('/learning-path')
    }
  ]

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Hızlı Eylemler
        </Typography>
        <Grid container spacing={2}>
          {quickActions.map((action, index) => (
            <Grid item xs={6} sm={3} key={index}>
              <Button
                fullWidth
                variant="outlined"
                color={action.color}
                startIcon={action.icon}
                onClick={action.onClick}
                sx={{ py: 2, flexDirection: 'column', gap: 1 }}
              >
                {action.label}
              </Button>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  )
}

interface StudentProgressCardProps {
  title: string
  current: number
  total: number
  percentage: number
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error'
}

export const StudentProgressCard: React.FC<StudentProgressCardProps> = ({
  title,
  current,
  total,
  percentage,
  color = 'primary'
}) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" color={`${color}.main`} sx={{ mr: 1 }}>
            {current}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            / {total}
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={color}
          sx={{ mb: 1 }}
        />
        <Typography variant="body2" color="text.secondary">
          %{percentage.toFixed(1)} tamamlandı
        </Typography>
      </CardContent>
    </Card>
  )
}

interface StudentAchievementProps {
  achievements: Array<{
    id: string
    title: string
    description: string
    earned: boolean
    earnedDate?: string
  }>
}

export const StudentAchievements: React.FC<StudentAchievementProps> = ({
  achievements
}) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Başarılar
        </Typography>
        <List>
          {achievements.slice(0, 5).map((achievement) => (
            <ListItem key={achievement.id} sx={{ px: 0 }}>
              <ListItemIcon>
                <Avatar
                  sx={{
                    bgcolor: achievement.earned ? 'success.main' : 'grey.300',
                    width: 32,
                    height: 32
                  }}
                >
                  <Star sx={{ fontSize: 20 }} />
                </Avatar>
              </ListItemIcon>
              <ListItemText
                primary={achievement.title}
                secondary={
                  achievement.earned
                    ? `Kazanıldı: ${achievement.earnedDate}`
                    : achievement.description
                }
              />
              {achievement.earned && (
                <Chip label="Kazanıldı" color="success" size="small" />
              )}
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  )
}

interface StudentStatsProps {
  stats: {
    totalStudyTime: number // dakika
    completedLessons: number
    averageScore: number
    currentStreak: number
  }
}

export const StudentStats: React.FC<StudentStatsProps> = ({ stats }) => {
  const formatStudyTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}s ${mins}dk`
  }

  const statItems = [
    {
      label: 'Toplam Çalışma',
      value: formatStudyTime(stats.totalStudyTime),
      icon: <School />,
      color: 'primary'
    },
    {
      label: 'Tamamlanan Ders',
      value: stats.completedLessons.toString(),
      icon: <MenuBook />,
      color: 'success'
    },
    {
      label: 'Ortalama Puan',
      value: `${stats.averageScore.toFixed(1)}`,
      icon: <Assessment />,
      color: 'warning'
    },
    {
      label: 'Günlük Seri',
      value: `${stats.currentStreak} gün`,
      icon: <TrendingUp />,
      color: 'info'
    }
  ]

  return (
    <Grid container spacing={2}>
      {statItems.map((item, index) => (
        <Grid item xs={6} sm={3} key={index}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Box sx={{ color: `${item.color}.main`, mb: 1 }}>
                {item.icon}
              </Box>
              <Typography variant="h6" color={`${item.color}.main`}>
                {item.value}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {item.label}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  )
}

export default {
  StudentQuickActions,
  StudentProgressCard,
  StudentAchievements,
  StudentStats
}