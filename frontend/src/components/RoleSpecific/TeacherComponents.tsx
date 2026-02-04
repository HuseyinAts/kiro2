import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material'
import {
  Class,
  People,
  Assessment,
  TrendingUp,
  Add,
  Edit,
  Visibility,
  Assignment,
  BarChart
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

interface TeacherClassCardProps {
  classInfo: {
    sinif_id: string
    sinif_adi: string
    ogrenci_sayisi: number
    ortalama_basari: number
  }
  onViewStudents?: (classId: string) => void
  onCreateExam?: (classId: string) => void
  onViewReports?: (classId: string) => void
}

export const TeacherClassCard: React.FC<TeacherClassCardProps> = ({
  classInfo,
  onViewStudents,
  onCreateExam,
  onViewReports
}) => {
  const getSuccessColor = (basari: number): 'success' | 'warning' | 'error' => {
    if (basari >= 80) return 'success'
    if (basari >= 60) return 'warning'
    return 'error'
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Class sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="h3">
            {classInfo.sinif_adi}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <People sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {classInfo.ogrenci_sayisi} öğrenci
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TrendingUp sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Ortalama:
          </Typography>
          <Chip
            label={`${classInfo.ortalama_basari.toFixed(1)}%`}
            color={getSuccessColor(classInfo.ortalama_basari)}
            size="small"
          />
        </Box>

        <LinearProgress
          variant="determinate"
          value={classInfo.ortalama_basari}
          color={getSuccessColor(classInfo.ortalama_basari)}
          sx={{ mb: 2 }}
        />
        
        <Grid container spacing={1}>
          <Grid item xs={4}>
            <Button
              size="small"
              fullWidth
              startIcon={<People />}
              onClick={() => onViewStudents?.(classInfo.sinif_id)}
            >
              Öğrenciler
            </Button>
          </Grid>
          <Grid item xs={4}>
            <Button
              size="small"
              fullWidth
              startIcon={<Assessment />}
              onClick={() => onCreateExam?.(classInfo.sinif_id)}
            >
              Sınav
            </Button>
          </Grid>
          <Grid item xs={4}>
            <Button
              size="small"
              fullWidth
              startIcon={<BarChart />}
              onClick={() => onViewReports?.(classInfo.sinif_id)}
            >
              Rapor
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )
}

interface TeacherQuickActionsProps {
  onCreateClass?: () => void
  onCreateExam?: () => void
  onViewReports?: () => void
  onManageContent?: () => void
}

export const TeacherQuickActions: React.FC<TeacherQuickActionsProps> = ({
  onCreateClass,
  onCreateExam,
  onViewReports,
  onManageContent
}) => {
  const navigate = useNavigate()

  const quickActions = [
    {
      label: 'Sınıf Oluştur',
      icon: <Add />,
      color: 'primary' as const,
      onClick: () => onCreateClass ? onCreateClass() : navigate('/teacher/classes')
    },
    {
      label: 'Sınav Oluştur',
      icon: <Assessment />,
      color: 'secondary' as const,
      onClick: () => onCreateExam ? onCreateExam() : navigate('/teacher/exams')
    },
    {
      label: 'Raporları Gör',
      icon: <BarChart />,
      color: 'info' as const,
      onClick: () => onViewReports ? onViewReports() : navigate('/teacher/reports')
    },
    {
      label: 'İçerik Yönet',
      icon: <Assignment />,
      color: 'success' as const,
      onClick: () => onManageContent ? onManageContent() : navigate('/teacher/content')
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

interface StudentPerformanceTableProps {
  students: Array<{
    ogrenci_id: string
    ad_soyad: string
    sinif: string
    son_sinav_puani: number
    genel_ortalama: number
  }>
  onViewStudent?: (studentId: string) => void
}

export const StudentPerformanceTable: React.FC<StudentPerformanceTableProps> = ({
  students,
  onViewStudent
}) => {
  const getPerformanceColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 80) return 'success'
    if (score >= 60) return 'warning'
    return 'error'
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Öğrenci Performansı
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Öğrenci</TableCell>
                <TableCell>Sınıf</TableCell>
                <TableCell align="center">Son Sınav</TableCell>
                <TableCell align="center">Genel Ortalama</TableCell>
                <TableCell align="center">İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {students.map((student) => (
                <TableRow key={student.ogrenci_id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, width: 32, height: 32 }}>
                        {student.ad_soyad.split(' ').map(n => n.charAt(0)).join('')}
                      </Avatar>
                      {student.ad_soyad}
                    </Box>
                  </TableCell>
                  <TableCell>{student.sinif}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={student.son_sinav_puani}
                      color={getPerformanceColor(student.son_sinav_puani)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={student.genel_ortalama.toFixed(1)}
                      color={getPerformanceColor(student.genel_ortalama)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Button
                      size="small"
                      startIcon={<Visibility />}
                      onClick={() => onViewStudent?.(student.ogrenci_id)}
                    >
                      Detay
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  )
}

interface TeacherStatsProps {
  stats: {
    toplam_ogrenci: number
    aktif_ogrenci: number
    ortalama_basari: number
    gelisme_trendi: number
  }
}

export const TeacherStats: React.FC<TeacherStatsProps> = ({ stats }) => {
  const statItems = [
    {
      label: 'Toplam Öğrenci',
      value: stats.toplam_ogrenci.toString(),
      icon: <People />,
      color: 'primary'
    },
    {
      label: 'Aktif Öğrenci',
      value: stats.aktif_ogrenci.toString(),
      icon: <People />,
      color: 'success'
    },
    {
      label: 'Ortalama Başarı',
      value: `${stats.ortalama_basari.toFixed(1)}%`,
      icon: <Assessment />,
      color: 'warning'
    },
    {
      label: 'Gelişim Trendi',
      value: `+${stats.gelisme_trendi.toFixed(1)}%`,
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
  TeacherClassCard,
  TeacherQuickActions,
  StudentPerformanceTable,
  TeacherStats
}