import {
  TrendingUp,
  TrendingDown,
  School,
  EmojiEvents,
  Timer,
  CalendarToday as _CalendarToday,
  Assessment,
  Star,
  LocalFireDepartment,
  Timeline as _Timeline,
  CheckCircle,
  RadioButtonUnchecked,
  MoreVert,
  Download,
  Share,
  Print,
  Refresh,
  FilterList as _FilterList,
  DateRange as _DateRange,
} from '@mui/icons-material';
import {
  Grid,
  Paper,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  CircularProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
  Button,
  ButtonGroup,
  Tabs,
  Tab,
  Box,
  Divider as _Divider,
  Badge as _Badge,
  Tooltip,
  Menu,
  MenuItem,
} from '@mui/material';
import clsx from 'clsx';
import { AnimatePresence as _AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart as _BarChart,
  Bar as _Bar,
  PieChart as _PieChart,
  Pie as _Pie,
  Cell as _Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

import { dateUtils } from '@/utils/dateUtils';

interface DashboardData {
  user: {
    name: string
    avatar?: string
    level: number
    experience: number
    nextLevelExp: number
    streakDays: number
    totalPoints: number
    rank: number
    badges: Badge[]
  }
  stats: {
    completedLessons: number
    totalLessons: number
    completedQuizzes: number
    averageScore: number
    studyTime: number
    weeklyGoal: number
    weeklyProgress: number
  }
  recentActivities: Activity[]
  progressHistory: ProgressPoint[]
  skillsRadar: SkillData[]
  achievements: Achievement[]
  leaderboard: LeaderboardEntry[]
}

interface Badge {
  id: string
  name: string
  icon: string
  color: string
  earnedAt: string
}

interface Activity {
  id: string
  type: 'lesson' | 'quiz' | 'achievement' | 'milestone'
  title: string
  timestamp: string
  score?: number
  duration?: number
}

interface ProgressPoint {
  date: string
  lessons: number
  quizzes: number
  points: number
}

interface SkillData {
  skill: string
  value: number
  fullMark: 100
}

interface Achievement {
  id: string
  title: string
  description: string
  icon: string
  progress: number
  maxProgress: number
  unlocked: boolean
}

interface LeaderboardEntry {
  rank: number
  name: string
  avatar?: string
  points: number
  change: 'up' | 'down' | 'same'
}

interface ProgressDashboardProps {
  data?: DashboardData
  className?: string
  onRefresh?: () => void
}

const mockData: DashboardData = {
  user: {
    name: 'Ahmet Yılmaz',
    level: 12,
    experience: 2850,
    nextLevelExp: 3500,
    streakDays: 7,
    totalPoints: 15420,
    rank: 23,
    badges: [
      { id: '1', name: 'Hızlı Başlangıç', icon: '🚀', color: '#3b82f6', earnedAt: '2024-01-15' },
      { id: '2', name: 'Quiz Ustası', icon: '🎯', color: '#10b981', earnedAt: '2024-01-20' },
      { id: '3', name: 'Hafta Sonu Savaşçısı', icon: '⚔️', color: '#f59e0b', earnedAt: '2024-01-22' },
    ],
  },
  stats: {
    completedLessons: 45,
    totalLessons: 120,
    completedQuizzes: 23,
    averageScore: 78,
    studyTime: 1250,
    weeklyGoal: 300,
    weeklyProgress: 210,
  },
  recentActivities: [
    { id: '1', type: 'lesson', title: 'Python Temelleri', timestamp: '2024-01-26T14:30:00', duration: 45 },
    { id: '2', type: 'quiz', title: 'Veri Yapıları Quiz', timestamp: '2024-01-26T10:15:00', score: 85 },
    { id: '3', type: 'achievement', title: 'İlk 10 Ders Tamamlandı', timestamp: '2024-01-25T18:00:00' },
    { id: '4', type: 'lesson', title: 'Algoritmalar', timestamp: '2024-01-25T15:20:00', duration: 60 },
  ],
  progressHistory: [
    { date: '2024-01-20', lessons: 3, quizzes: 1, points: 120 },
    { date: '2024-01-21', lessons: 2, quizzes: 2, points: 150 },
    { date: '2024-01-22', lessons: 4, quizzes: 1, points: 180 },
    { date: '2024-01-23', lessons: 3, quizzes: 0, points: 90 },
    { date: '2024-01-24', lessons: 5, quizzes: 2, points: 220 },
    { date: '2024-01-25', lessons: 2, quizzes: 1, points: 110 },
    { date: '2024-01-26', lessons: 3, quizzes: 2, points: 170 },
  ],
  skillsRadar: [
    { skill: 'Python', value: 85, fullMark: 100 },
    { skill: 'JavaScript', value: 70, fullMark: 100 },
    { skill: 'Algoritmalar', value: 65, fullMark: 100 },
    { skill: 'Veri Yapıları', value: 75, fullMark: 100 },
    { skill: 'Veritabanı', value: 60, fullMark: 100 },
    { skill: 'Web Geliştirme', value: 80, fullMark: 100 },
  ],
  achievements: [
    { id: '1', title: 'İlk Adım', description: 'İlk dersini tamamla', icon: '👶', progress: 1, maxProgress: 1, unlocked: true },
    { id: '2', title: 'Hızlı Öğrenci', description: '10 dersi tamamla', icon: '🏃', progress: 10, maxProgress: 10, unlocked: true },
    { id: '3', title: 'Uzman', description: '50 dersi tamamla', icon: '🎓', progress: 45, maxProgress: 50, unlocked: false },
    { id: '4', title: 'Quiz Kralı', description: '25 quiz\'i %80+ ile geç', icon: '👑', progress: 18, maxProgress: 25, unlocked: false },
  ],
  leaderboard: [
    { rank: 1, name: 'Mehmet Öz', points: 23450, change: 'same' },
    { rank: 2, name: 'Ayşe Kaya', points: 22100, change: 'up' },
    { rank: 3, name: 'Can Demir', points: 21500, change: 'down' },
  ],
};

export function ProgressDashboard({
  data = mockData,
  className,
  onRefresh,
}: ProgressDashboardProps) {
  const [activeTab, setActiveTab] = useState(0);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [dateFilter, setDateFilter] = useState<'week' | 'month' | 'all'>('week');

  const chartColors = {
    primary: '#3b82f6',
    secondary: '#10b981',
    accent: '#f59e0b',
    error: '#ef4444',
    success: '#10b981',
  };

  const formatStudyTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}s ${mins}dk`;
  };

  const StatCard = ({
    title,
    value,
    subtitle,
    icon,
    color,
    trend,
  }: {
    title: string
    value: string | number
    subtitle?: string
    icon: React.ReactNode
    color: string
    trend?: { value: number; direction: 'up' | 'down' }
  }) => (
    <Card className="h-full">
      <CardContent>
        <div className="flex items-start justify-between mb-2">
          <div
            className="p-2 rounded-lg"
            style={{ backgroundColor: `${color}20` }}
          >
            <div style={{ color }}>{icon}</div>
          </div>
          {trend && (
            <Chip
              size="small"
              icon={trend.direction === 'up' ? <TrendingUp /> : <TrendingDown />}
              label={`${trend.value}%`}
              color={trend.direction === 'up' ? 'success' : 'error'}
              variant="outlined"
            />
          )}
        </div>
        <Typography variant="h4" className="font-bold mb-1">
          {value}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="textSecondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header Section */}
      <Paper className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <Avatar
              src={data.user.avatar}
              sx={{ width: 80, height: 80 }}
              className="border-4 border-blue-500"
            >
              {data.user.name[0]}
            </Avatar>

            <div>
              <Typography variant="h4" className="font-bold">
                {data.user.name}
              </Typography>
              <div className="flex items-center gap-2 mt-1">
                <Chip
                  size="small"
                  label={`Seviye ${data.user.level}`}
                  color="primary"
                />
                <Chip
                  size="small"
                  icon={<LocalFireDepartment />}
                  label={`${data.user.streakDays} gün`}
                  color="warning"
                  variant="outlined"
                />
                <Chip
                  size="small"
                  icon={<EmojiEvents />}
                  label={`#${data.user.rank}`}
                  variant="outlined"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <IconButton onClick={onRefresh}>
              <Refresh />
            </IconButton>
            <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
              <MoreVert />
            </IconButton>
            <Menu
              anchorEl={menuAnchor}
              open={Boolean(menuAnchor)}
              onClose={() => setMenuAnchor(null)}
            >
              <MenuItem>
                <Download className="mr-2" /> Rapor İndir
              </MenuItem>
              <MenuItem>
                <Share className="mr-2" /> Paylaş
              </MenuItem>
              <MenuItem>
                <Print className="mr-2" /> Yazdır
              </MenuItem>
            </Menu>
          </div>
        </div>

        {/* Level Progress */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Deneyim</span>
            <span>{data.user.experience} / {data.user.nextLevelExp} XP</span>
          </div>
          <LinearProgress
            variant="determinate"
            value={(data.user.experience / data.user.nextLevelExp) * 100}
            className="h-2 rounded-full"
          />
        </div>

        {/* Badges */}
        <div className="flex gap-2 mt-4">
          {data.user.badges.map(badge => (
            <Tooltip key={badge.id} title={badge.name}>
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center text-2xl"
                style={{ backgroundColor: `${badge.color}20` }}
              >
                {badge.icon}
              </div>
            </Tooltip>
          ))}
        </div>
      </Paper>

      {/* Stats Grid */}
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Tamamlanan Dersler"
            value={`${data.stats.completedLessons}/${data.stats.totalLessons}`}
            subtitle={`%${Math.round((data.stats.completedLessons / data.stats.totalLessons) * 100)} tamamlandı`}
            icon={<School />}
            color={chartColors.primary}
            trend={{ value: 12, direction: 'up' }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Ortalama Quiz Puanı"
            value={`%${data.stats.averageScore}`}
            subtitle={`${data.stats.completedQuizzes} quiz tamamlandı`}
            icon={<Assessment />}
            color={chartColors.secondary}
            trend={{ value: 5, direction: 'up' }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Toplam Çalışma"
            value={formatStudyTime(data.stats.studyTime)}
            subtitle="Bu ay"
            icon={<Timer />}
            color={chartColors.accent}
            trend={{ value: 8, direction: 'up' }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Toplam Puan"
            value={data.user.totalPoints.toLocaleString()}
            subtitle={`Sıralama: #${data.user.rank}`}
            icon={<Star />}
            color={chartColors.error}
            trend={{ value: 15, direction: 'up' }}
          />
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Paper>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Genel Bakış" />
          <Tab label="İlerleme" />
          <Tab label="Beceriler" />
          <Tab label="Başarılar" />
          <Tab label="Liderlik Tablosu" />
        </Tabs>

        <Box p={3}>
          {/* Overview Tab */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              {/* Weekly Goal */}
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Haftalık Hedef
                    </Typography>
                    <div className="relative pt-1">
                      <CircularProgress
                        variant="determinate"
                        value={(data.stats.weeklyProgress / data.stats.weeklyGoal) * 100}
                        size={120}
                        thickness={4}
                        className="mx-auto block"
                      />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <Typography variant="h5" className="font-bold">
                            {data.stats.weeklyProgress}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            / {data.stats.weeklyGoal} dk
                          </Typography>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Grid>

              {/* Recent Activities */}
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Son Aktiviteler
                    </Typography>
                    <List>
                      {data.recentActivities.map((activity) => (
                        <ListItem key={activity.id} divider>
                          <ListItemAvatar>
                            <Avatar className={
                              activity.type === 'lesson' ? 'bg-blue-500' :
                              activity.type === 'quiz' ? 'bg-green-500' :
                              activity.type === 'achievement' ? 'bg-yellow-500' :
                              'bg-purple-500'
                            }>
                              {activity.type === 'lesson' && <School />}
                              {activity.type === 'quiz' && <Assessment />}
                              {activity.type === 'achievement' && <EmojiEvents />}
                              {activity.type === 'milestone' && <Star />}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={activity.title}
                            secondary={
                              <div className="flex items-center gap-2">
                                <span>{dateUtils.format(activity.timestamp, 'DD MMM HH:mm')}</span>
                                {activity.score && (
                                  <Chip size="small" label={`%${activity.score}`} color="success" />
                                )}
                                {activity.duration && (
                                  <Chip size="small" label={`${activity.duration} dk`} variant="outlined" />
                                )}
                              </div>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Progress Tab */}
          {activeTab === 1 && (
            <div className="space-y-4">
              <div className="flex justify-end mb-4">
                <ButtonGroup size="small">
                  <Button
                    variant={dateFilter === 'week' ? 'contained' : 'outlined'}
                    onClick={() => setDateFilter('week')}
                  >
                    Haftalık
                  </Button>
                  <Button
                    variant={dateFilter === 'month' ? 'contained' : 'outlined'}
                    onClick={() => setDateFilter('month')}
                  >
                    Aylık
                  </Button>
                  <Button
                    variant={dateFilter === 'all' ? 'contained' : 'outlined'}
                    onClick={() => setDateFilter('all')}
                  >
                    Tümü
                  </Button>
                </ButtonGroup>
              </div>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    İlerleme Grafiği
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={data.progressHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="lessons"
                        stackId="1"
                        stroke={chartColors.primary}
                        fill={chartColors.primary}
                        name="Dersler"
                      />
                      <Area
                        type="monotone"
                        dataKey="quizzes"
                        stackId="1"
                        stroke={chartColors.secondary}
                        fill={chartColors.secondary}
                        name="Quizler"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Puan İlerlemesi
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data.progressHistory}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <RechartsTooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="points"
                        stroke={chartColors.accent}
                        strokeWidth={2}
                        name="Günlük Puan"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Skills Tab */}
          {activeTab === 2 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Beceri Radarı
                </Typography>
                <ResponsiveContainer width="100%" height={400}>
                  <RadarChart data={data.skillsRadar}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="skill" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Beceri Seviyesi"
                      dataKey="value"
                      stroke={chartColors.primary}
                      fill={chartColors.primary}
                      fillOpacity={0.6}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Achievements Tab */}
          {activeTab === 3 && (
            <Grid container spacing={3}>
              {data.achievements.map((achievement) => (
                <Grid item xs={12} sm={6} md={4} key={achievement.id}>
                  <Card className={achievement.unlocked ? '' : 'opacity-60'}>
                    <CardContent>
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-3xl">{achievement.icon}</div>
                        {achievement.unlocked ? (
                          <CheckCircle color="success" />
                        ) : (
                          <RadioButtonUnchecked color="disabled" />
                        )}
                      </div>
                      <Typography variant="h6" className="mb-1">
                        {achievement.title}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" className="mb-2">
                        {achievement.description}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(achievement.progress / achievement.maxProgress) * 100}
                        className="mb-1"
                        color={achievement.unlocked ? 'success' : 'primary'}
                      />
                      <Typography variant="caption" color="textSecondary">
                        {achievement.progress} / {achievement.maxProgress}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {/* Leaderboard Tab */}
          {activeTab === 4 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Liderlik Tablosu
                </Typography>
                <List>
                  {data.leaderboard.map((entry) => (
                    <ListItem key={entry.rank} divider>
                      <div className="flex items-center gap-3 w-full">
                        <Typography variant="h6" className="w-8">
                          #{entry.rank}
                        </Typography>
                        <Avatar src={entry.avatar}>
                          {entry.name[0]}
                        </Avatar>
                        <ListItemText
                          primary={entry.name}
                          secondary={`${entry.points.toLocaleString()} puan`}
                        />
                        {entry.change === 'up' && <TrendingUp color="success" />}
                        {entry.change === 'down' && <TrendingDown color="error" />}
                      </div>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Box>
      </Paper>
    </div>
  );
}

export default ProgressDashboard;