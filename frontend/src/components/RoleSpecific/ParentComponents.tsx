import {
  ChildCare,
  School,
  Assessment,
  CalendarToday,
  Timer,
  Star,
  Notifications,
  BarChart,
  Phone,
} from '@mui/icons-material';
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
  Divider,
} from '@mui/material';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

interface ParentChildCardProps {
  child: {
    ogrenci_id: string
    ad_soyad: string
    sinif: string
    okul: string
    son_aktivite: string
    haftalik_ilerleme: number
  }
  onViewDetails?: (childId: string) => void
  onViewReports?: (childId: string) => void
  onContactTeacher?: (childId: string) => void
}

export const ParentChildCard: React.FC<ParentChildCardProps> = ({
  child,
  onViewDetails,
  onViewReports,
  onContactTeacher,
}) => {
  const getProgressColor = (progress: number): 'success' | 'warning' | 'error' => {
    if (progress >= 80) {return 'success';}
    if (progress >= 60) {return 'warning';}
    return 'error';
  };

  const getInitials = (name: string): string => {
    return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase();
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
            {getInitials(child.ad_soyad)}
          </Avatar>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="h3">
              {child.ad_soyad}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {child.sinif} - {child.okul}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <CalendarToday sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            Son Aktivite: {new Date(child.son_aktivite).toLocaleDateString('tr-TR')}
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Haftalık İlerleme</Typography>
            <Typography variant="body2" color={`${getProgressColor(child.haftalik_ilerleme)}.main`}>
              {child.haftalik_ilerleme}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={child.haftalik_ilerleme}
            color={getProgressColor(child.haftalik_ilerleme)}
          />
        </Box>

        <Grid container spacing={1}>
          <Grid item xs={4}>
            <Button
              size="small"
              fullWidth
              startIcon={<BarChart />}
              onClick={() => onViewDetails?.(child.ogrenci_id)}
            >
              Detay
            </Button>
          </Grid>
          <Grid item xs={4}>
            <Button
              size="small"
              fullWidth
              startIcon={<Assessment />}
              onClick={() => onViewReports?.(child.ogrenci_id)}
            >
              Rapor
            </Button>
          </Grid>
          <Grid item xs={4}>
            <Button
              size="small"
              fullWidth
              startIcon={<Phone />}
              onClick={() => onContactTeacher?.(child.ogrenci_id)}
            >
              İletişim
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

interface ParentQuickActionsProps {
  onViewAllChildren?: () => void
  onViewReports?: () => void
  onViewNotifications?: () => void
  onContactSchool?: () => void
}

export const ParentQuickActions: React.FC<ParentQuickActionsProps> = ({
  onViewAllChildren,
  onViewReports,
  onViewNotifications,
  onContactSchool,
}) => {
  const navigate = useNavigate();

  const quickActions = [
    {
      label: 'Çocuklarım',
      icon: <ChildCare />,
      color: 'primary' as const,
      onClick: () => onViewAllChildren ? onViewAllChildren() : navigate('/parent/children'),
    },
    {
      label: 'Raporlar',
      icon: <BarChart />,
      color: 'secondary' as const,
      onClick: () => onViewReports ? onViewReports() : navigate('/parent/reports'),
    },
    {
      label: 'Bildirimler',
      icon: <Notifications />,
      color: 'warning' as const,
      onClick: () => onViewNotifications ? onViewNotifications() : navigate('/parent/notifications'),
    },
    {
      label: 'Okul İletişim',
      icon: <Phone />,
      color: 'info' as const,
      onClick: () => onContactSchool ? onContactSchool() : alert('İletişim özelliği yakında eklenecek'),
    },
  ];

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
  );
};

interface WeeklyReportCardProps {
  report: {
    hafta: string
    calisma_suresi: number
    tamamlanan_dersler: number
    sinav_puanlari: number[]
    ortalama_puan: number
  }
  weekLabel: string
}

export const WeeklyReportCard: React.FC<WeeklyReportCardProps> = ({
  report,
  weekLabel,
}) => {
  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}s ${mins}dk`;
  };

  const getPerformanceColor = (score: number): 'success' | 'warning' | 'error' => {
    if (score >= 80) {return 'success';}
    if (score >= 60) {return 'warning';}
    return 'error';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {weekLabel}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Timer sx={{ mr: 1, fontSize: 20, color: 'primary.main' }} />
          <Typography variant="body2">
            {formatDuration(report.calisma_suresi)}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <School sx={{ mr: 1, fontSize: 20, color: 'success.main' }} />
          <Typography variant="body2">
            {report.tamamlanan_dersler} ders
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Assessment sx={{ mr: 1, fontSize: 20, color: 'warning.main' }} />
          <Typography variant="body2">
            {report.sinav_puanlari.length} sınav
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Star sx={{ mr: 1, fontSize: 20, color: 'info.main' }} />
          <Typography variant="body2" sx={{ mr: 1 }}>
            Ortalama:
          </Typography>
          <Chip
            label={report.ortalama_puan.toFixed(1)}
            color={getPerformanceColor(report.ortalama_puan)}
            size="small"
          />
        </Box>
      </CardContent>
    </Card>
  );
};

interface ParentNotificationListProps {
  notifications: Array<{
    bildirim_id: string
    baslik: string
    mesaj: string
    tip: 'basari' | 'uyari' | 'bilgi' | 'hata'
    okundu: boolean
    tarih: string
  }>
  onMarkAsRead?: (notificationId: string) => void
  onViewAll?: () => void
}

export const ParentNotificationList: React.FC<ParentNotificationListProps> = ({
  notifications,
  onMarkAsRead: _onMarkAsRead,
  onViewAll,
}) => {
  const getNotificationIcon = (tip: string) => {
    switch (tip) {
      case 'basari':
        return <Star sx={{ color: 'success.main' }} />;
      case 'uyari':
        return <Notifications sx={{ color: 'warning.main' }} />;
      case 'hata':
        return <Notifications sx={{ color: 'error.main' }} />;
      default:
        return <Notifications sx={{ color: 'info.main' }} />;
    }
  };

  const getNotificationColor = (tip: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (tip) {
      case 'basari':
        return 'success';
      case 'uyari':
        return 'warning';
      case 'hata':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Son Bildirimler
          </Typography>
          <Button size="small" onClick={onViewAll}>
            Tümünü Gör
          </Button>
        </Box>

        <List sx={{ p: 0 }}>
          {notifications.slice(0, 5).map((notification, index) => (
            <React.Fragment key={notification.bildirim_id}>
              <ListItem
                sx={{
                  px: 0,
                  backgroundColor: notification.okundu ? 'transparent' : 'action.hover',
                  borderRadius: 1,
                  mb: 1,
                }}
              >
                <ListItemIcon>
                  <Avatar sx={{
                    bgcolor: `${getNotificationColor(notification.tip)}.main`,
                    width: 32,
                    height: 32,
                  }}>
                    {getNotificationIcon(notification.tip)}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={notification.baslik}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {notification.mesaj}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(notification.tarih).toLocaleString('tr-TR')}
                      </Typography>
                    </Box>
                  }
                />
                {!notification.okundu && (
                  <Chip label="Yeni" color="primary" size="small" />
                )}
              </ListItem>
              {index < Math.min(notifications.length, 5) - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default {
  ParentChildCard,
  ParentQuickActions,
  WeeklyReportCard,
  ParentNotificationList,
};