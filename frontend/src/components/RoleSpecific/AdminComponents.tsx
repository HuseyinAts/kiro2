import {
  People,
  Assessment,
  Computer,
  CheckCircle,
  Error,
  Info,
  Settings,
  Storage,
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
  Alert,
} from '@mui/material';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';

interface AdminQuickActionsProps {
  onUserManagement?: () => void
  onContentManagement?: () => void
  onSystemSettings?: () => void
  onViewLogs?: () => void
}

export const AdminQuickActions: React.FC<AdminQuickActionsProps> = ({
  onUserManagement,
  onContentManagement,
  onSystemSettings,
  onViewLogs,
}) => {
  const navigate = useNavigate();

  const quickActions = [
    {
      label: 'Kullanıcı Yönetimi',
      icon: <People />,
      color: 'primary' as const,
      onClick: () => onUserManagement ? onUserManagement() : navigate('/admin/users'),
    },
    {
      label: 'İçerik Yönetimi',
      icon: <Assessment />,
      color: 'secondary' as const,
      onClick: () => onContentManagement ? onContentManagement() : navigate('/admin/content'),
    },
    {
      label: 'Sistem Ayarları',
      icon: <Settings />,
      color: 'warning' as const,
      onClick: () => onSystemSettings ? onSystemSettings() : navigate('/admin/settings'),
    },
    {
      label: 'Sistem Logları',
      icon: <Storage />,
      color: 'info' as const,
      onClick: () => onViewLogs ? onViewLogs() : alert('Log görüntüleme özelliği yakında eklenecek'),
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Admin Hızlı Eylemler
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

interface SystemStatsProps {
  stats: {
    toplam_kullanici: number
    aktif_kullanici: number
    toplam_sinav: number
    sistem_yuklemesi: number
  }
}

export const SystemStats: React.FC<SystemStatsProps> = ({ stats }) => {
  const getSystemHealthColor = (value: number): 'success' | 'warning' | 'error' => {
    if (value >= 95) {return 'success';}
    if (value >= 80) {return 'warning';}
    return 'error';
  };

  const statItems = [
    {
      label: 'Toplam Kullanıcı',
      value: stats.toplam_kullanici.toLocaleString(),
      subValue: `${stats.aktif_kullanici} aktif`,
      icon: <People />,
      color: 'primary',
    },
    {
      label: 'Toplam Sınav',
      value: stats.toplam_sinav.toLocaleString(),
      icon: <Assessment />,
      color: 'success',
    },
    {
      label: 'Sistem Yükü',
      value: `${stats.sistem_yuklemesi.toFixed(1)}%`,
      icon: <Computer />,
      color: getSystemHealthColor(100 - stats.sistem_yuklemesi),
    },
    {
      label: 'Sistem Durumu',
      value: 'Çevrimiçi',
      icon: <CheckCircle />,
      color: 'success',
    },
  ];

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
              {item.subValue && (
                <Typography variant="caption" color="text.secondary">
                  {item.subValue}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

interface UserStatsProps {
  stats: {
    ogrenci_sayisi: number
    ogretmen_sayisi: number
    veli_sayisi: number
    yeni_kayitlar: number
  }
}

export const UserStats: React.FC<UserStatsProps> = ({ stats }) => {
  const userTypes = [
    {
      label: 'Öğrenci',
      value: stats.ogrenci_sayisi,
      color: 'primary',
      percentage: (stats.ogrenci_sayisi / (stats.ogrenci_sayisi + stats.ogretmen_sayisi + stats.veli_sayisi)) * 100,
    },
    {
      label: 'Öğretmen',
      value: stats.ogretmen_sayisi,
      color: 'success',
      percentage: (stats.ogretmen_sayisi / (stats.ogrenci_sayisi + stats.ogretmen_sayisi + stats.veli_sayisi)) * 100,
    },
    {
      label: 'Veli',
      value: stats.veli_sayisi,
      color: 'warning',
      percentage: (stats.veli_sayisi / (stats.ogrenci_sayisi + stats.ogretmen_sayisi + stats.veli_sayisi)) * 100,
    },
    {
      label: 'Yeni Kayıt',
      value: stats.yeni_kayitlar,
      color: 'info',
      percentage: 100, // Bu hafta için
    },
  ];

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Kullanıcı Dağılımı
        </Typography>
        <Grid container spacing={2}>
          {userTypes.map((type, index) => (
            <Grid item xs={6} sm={3} key={index}>
              <Box sx={{ textAlign: 'center', p: 2 }}>
                <Typography variant="h4" color={`${type.color}.main`}>
                  {type.value}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {type.label}
                </Typography>
                {index < 3 && (
                  <LinearProgress
                    variant="determinate"
                    value={type.percentage}
                    color={type.color as any}
                    sx={{ mt: 1 }}
                  />
                )}
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

interface PerformanceMetricsProps {
  metrics: {
    ortalama_yanit_suresi: number
    sistem_kullanilabilirlik: number
    hata_orani: number
    kullanici_memnuniyeti: number
  }
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metrics }) => {
  const getHealthColor = (value: number, isInverted: boolean = false): 'success' | 'warning' | 'error' => {
    if (isInverted) {
      if (value <= 1) {return 'success';}
      if (value <= 5) {return 'warning';}
      return 'error';
    } else {
      if (value >= 95) {return 'success';}
      if (value >= 80) {return 'warning';}
      return 'error';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Performans Metrikleri
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Ortalama Yanıt Süresi</Typography>
            <Typography variant="body2">{metrics.ortalama_yanit_suresi}ms</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.max(0, 100 - (metrics.ortalama_yanit_suresi / 10))}
            color={metrics.ortalama_yanit_suresi < 200 ? 'success' : 'warning'}
          />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Sistem Kullanılabilirlik</Typography>
            <Typography variant="body2">{metrics.sistem_kullanilabilirlik}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={metrics.sistem_kullanilabilirlik}
            color={getHealthColor(metrics.sistem_kullanilabilirlik)}
          />
        </Box>

        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Hata Oranı</Typography>
            <Typography variant="body2">{metrics.hata_orani}%</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={metrics.hata_orani * 10}
            color={getHealthColor(metrics.hata_orani, true)}
          />
        </Box>

        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">Kullanıcı Memnuniyeti</Typography>
            <Typography variant="body2">{metrics.kullanici_memnuniyeti}/5.0</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={(metrics.kullanici_memnuniyeti / 5) * 100}
            color="success"
          />
        </Box>
      </CardContent>
    </Card>
  );
};

interface RecentActivityListProps {
  activities: Array<{
    aktivite_id: string
    kullanici: string
    eylem: string
    tarih: string
    detay?: string
  }>
}

export const RecentActivityList: React.FC<RecentActivityListProps> = ({ activities }) => {
  const getActivityIcon = (eylem: string) => {
    if (eylem.includes('sınav')) {return <Assessment />;}
    if (eylem.includes('oluştur')) {return <CheckCircle />;}
    if (eylem.includes('görüntüle')) {return <Info />;}
    if (eylem.includes('hata')) {return <Error />;}
    return <Info />;
  };

  const getActivityColor = (eylem: string): 'primary' | 'success' | 'info' | 'error' => {
    if (eylem.includes('sınav')) {return 'primary';}
    if (eylem.includes('oluştur')) {return 'success';}
    if (eylem.includes('hata')) {return 'error';}
    return 'info';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Son Aktiviteler
        </Typography>
        <List sx={{ p: 0 }}>
          {activities.map((aktivite, _index) => (
            <ListItem
              key={aktivite.aktivite_id}
              sx={{ px: 0, py: 1 }}
            >
              <ListItemIcon>
                <Avatar sx={{ bgcolor: `${getActivityColor(aktivite.eylem)}.main`, width: 32, height: 32 }}>
                  {getActivityIcon(aktivite.eylem)}
                </Avatar>
              </ListItemIcon>
              <ListItemText
                primary={aktivite.eylem}
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      {aktivite.kullanici}
                    </Typography>
                    {aktivite.detay && (
                      <Chip
                        label={aktivite.detay}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ mt: 0.5, mr: 1 }}
                      />
                    )}
                    <Typography variant="caption" color="text.secondary" display="block">
                      {new Date(aktivite.tarih).toLocaleString('tr-TR')}
                    </Typography>
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

interface SystemHealthAlertProps {
  alerts?: Array<{
    id: string
    type: 'warning' | 'error' | 'info'
    message: string
    timestamp: string
  }>
}

export const SystemHealthAlert: React.FC<SystemHealthAlertProps> = ({ alerts = [] }) => {
  if (alerts.length === 0) {
    return (
      <Alert severity="success" sx={{ mb: 2 }}>
        <Typography variant="body2">
          Sistem sağlıklı çalışıyor. Herhangi bir uyarı bulunmuyor.
        </Typography>
      </Alert>
    );
  }

  return (
    <Box sx={{ mb: 2 }}>
      {alerts.map((alert) => (
        <Alert key={alert.id} severity={alert.type} sx={{ mb: 1 }}>
          <Typography variant="body2">
            {alert.message}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {new Date(alert.timestamp).toLocaleString('tr-TR')}
          </Typography>
        </Alert>
      ))}
    </Box>
  );
};

export default {
  AdminQuickActions,
  SystemStats,
  UserStats,
  PerformanceMetrics,
  RecentActivityList,
  SystemHealthAlert,
};