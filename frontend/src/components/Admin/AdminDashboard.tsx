import {
  People,
  Assessment,
  TrendingUp,
  School,
  QuestionAnswer,
  Refresh,
} from '@mui/icons-material';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Chip,
  Button,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { adminService, DashboardStats } from '../../services/adminService';

// DashboardStats tipi artık adminService'den geliyor

interface StatCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error'
  subtitle?: string
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, subtitle }) => (
  <Card sx={{ height: '100%' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between">
        <Box>
          <Typography color="textSecondary" gutterBottom variant="h6">
            {title}
          </Typography>
          <Typography variant="h4" component="div" color={`${color}.main`}>
            {value}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="textSecondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box color={`${color}.main`}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const dashboardStats = await adminService.getDashboardStats();
      setStats(dashboardStats);
    } catch (err) {
      console.error('Dashboard stats error:', err);
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');

      // Geliştirme aşamasında mock data
      setStats({
        toplam_kullanici: 1250,
        aktif_kullanici: 980,
        toplam_ogrenci: 980,
        toplam_ogretmen: 45,
        toplam_veli: 225,
        toplam_admin: 5,
        bugun_kayit: 12,
        bu_hafta_kayit: 85,
        bu_ay_kayit: 340,
        aktif_sinav_sayisi: 156,
        tamamlanan_sinav_sayisi: 3240,
        ortalama_basari_orani: 72.5,
        sistem_durumu: 'healthy',
        son_guncelleme: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  const getSystemStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'primary';
    }
  };

  const getSystemStatusText = (status: string) => {
    switch (status) {
      case 'healthy': return 'Sağlıklı';
      case 'warning': return 'Uyarı';
      case 'error': return 'Hata';
      default: return 'Bilinmiyor';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error && !stats) {
    return (
      <Alert
        severity="error"
        action={
          <Button
            color="inherit"
            size="small"
            onClick={fetchDashboardStats}
            startIcon={<Refresh />}
          >
            Tekrar Dene
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h2">
          Dashboard
        </Typography>
        {stats && (
          <Chip
            label={`Sistem: ${getSystemStatusText(stats.sistem_durumu)}`}
            color={getSystemStatusColor(stats.sistem_durumu)}
            variant="outlined"
          />
        )}
      </Box>

      {error && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {error} (Mock veriler gösteriliyor)
        </Alert>
      )}

      {stats && (
        <Grid container spacing={3}>
          {/* Kullanıcı İstatistikleri */}
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Toplam Kullanıcı"
              value={stats.toplam_kullanici.toLocaleString()}
              icon={<People fontSize="large" />}
              color="primary"
              subtitle="Tüm kayıtlı kullanıcılar"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Aktif Öğrenci"
              value={stats.toplam_ogrenci.toLocaleString()}
              icon={<School fontSize="large" />}
              color="success"
              subtitle="Bu ay aktif olan"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Öğretmen"
              value={stats.toplam_ogretmen.toLocaleString()}
              icon={<People fontSize="large" />}
              color="secondary"
              subtitle="Kayıtlı öğretmenler"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Veli"
              value={stats.toplam_veli.toLocaleString()}
              icon={<People fontSize="large" />}
              color="warning"
              subtitle="Kayıtlı veliler"
            />
          </Grid>

          {/* İçerik İstatistikleri */}
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Aktif Sınavlar"
              value={stats.aktif_sinav_sayisi.toLocaleString()}
              icon={<QuestionAnswer fontSize="large" />}
              color="primary"
              subtitle="Devam eden sınavlar"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Tamamlanan Sınavlar"
              value={stats.tamamlanan_sinav_sayisi.toLocaleString()}
              icon={<Assessment fontSize="large" />}
              color="secondary"
              subtitle="Çözülen sınavlar"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Bu Hafta Kayıt"
              value={stats.bu_hafta_kayit.toLocaleString()}
              icon={<TrendingUp fontSize="large" />}
              color="success"
              subtitle="Yeni kayıtlar"
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Son Güncelleme"
              value={new Date(stats.son_guncelleme).toLocaleTimeString('tr-TR')}
              icon={<Assessment fontSize="large" />}
              color="primary"
              subtitle={new Date(stats.son_guncelleme).toLocaleDateString('tr-TR')}
            />
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default AdminDashboard;