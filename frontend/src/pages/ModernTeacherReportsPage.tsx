/**
 * Modern Teacher Reports Page - Glassmorphism Design
 * Öğretmen raporları ve analizler
 */

import {
  Assessment,
  Download,
  Class,
  Person,
  School,
  TrendingUp,
  CalendarToday,
  FilterList,
  PictureAsPdf,
  InsertDriveFile,
} from '@mui/icons-material';
import {
  Typography,
  Box,
  Grid,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';

import { GlassCard } from '../components/ui/GlassCard';
import { ModernButton } from '../components/ui/ModernButton';
import { DashboardScaffold } from '../components/Layout/DashboardScaffold';
import apiClient from '../services/apiClient';
import modernColors from '../theme/modern-colors';
import { useAuthStore } from '@/store/authStore';

interface Report {
  id: string
  baslik: string
  aciklama: string
  tarih: string
  tip: 'sinif' | 'ogrenci' | 'konu' | 'sinav' | 'genel'
  format: 'pdf' | 'excel' | 'csv'
  boyut: string
}

export function ModernTeacherReportsPage() {
  const { user: _user } = useAuthStore();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/teacher/reports');
      setReports(response?.data?.reports || []);
    } catch (error) {
      setReports([]);
      // ErrorBoundary or Empty State will handle the missing items
    } finally {
      setLoading(false);
    }
  };

  const getTypeGradient = (tip: string): string => {
    switch (tip) {
      case 'sinif':
        return modernColors.gradients.primary;
      case 'ogrenci':
        return modernColors.gradients.sunset;
      case 'konu':
        return modernColors.gradients.ocean;
      case 'sinav':
        return modernColors.gradients.success;
      case 'genel':
        return modernColors.gradients.forest;
      default:
        return modernColors.gradients.primary;
    }
  };

  const getTypeIcon = (tip: string) => {
    switch (tip) {
      case 'sinif':
        return <Class sx={{ fontSize: 32 }} />;
      case 'ogrenci':
        return <Person sx={{ fontSize: 32 }} />;
      case 'konu':
        return <School sx={{ fontSize: 32 }} />;
      case 'sinav':
        return <Assessment sx={{ fontSize: 32 }} />;
      case 'genel':
        return <TrendingUp sx={{ fontSize: 32 }} />;
      default:
        return <Assessment sx={{ fontSize: 32 }} />;
    }
  };

  const getTypeLabel = (tip: string): string => {
    switch (tip) {
      case 'sinif':
        return 'Sınıf';
      case 'ogrenci':
        return 'Öğrenci';
      case 'konu':
        return 'Konu';
      case 'sinav':
        return 'Sınav';
      case 'genel':
        return 'Genel';
      default:
        return tip;
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf':
        return <PictureAsPdf fontSize="small" />;
      case 'excel':
      case 'csv':
        return <InsertDriveFile fontSize="small" />;
      default:
        return <InsertDriveFile fontSize="small" />;
    }
  };

  const handleDownloadReport = async (report: Report) => {
    try {
      // Simulate download
      alert(`${report.baslik} raporu indiriliyor...`);
    } catch (error) {
      throw error;
    }
  };

  const filteredReports = reports.filter((report) => {
    const matchesSearch =
      report.baslik.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.aciklama.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || report.tip === filterType;
    return matchesSearch && matchesType;
  });

  const getReportCountByType = (tip: string) => {
    return reports.filter((r) => r.tip === tip).length;
  };

  return (
    <DashboardScaffold
      loading={loading}
      loadingMessage="Raporlar yükleniyor..."
      icon={<Assessment />}
      iconGradient={modernColors.gradients.forest}
      title="Raporlar ve Analizler"
      titleGradient={modernColors.gradients.forest}
      subtitle="Detaylı performans raporlarını görüntüleyin ve indirin"
      maxWidth="lg"
    >
        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard glassIntensity="medium" elevated sx={{ mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  placeholder="Rapor ara..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <FilterList />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Rapor Tipi</InputLabel>
                  <Select
                    value={filterType}
                    label="Rapor Tipi"
                    onChange={(e) => setFilterType(e.target.value)}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    <MenuItem value="sinif">Sınıf</MenuItem>
                    <MenuItem value="ogrenci">Öğrenci</MenuItem>
                    <MenuItem value="konu">Konu</MenuItem>
                    <MenuItem value="sinav">Sınav</MenuItem>
                    <MenuItem value="genel">Genel</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </GlassCard>
        </motion.div>

        {/* Stats Summary */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={4} md={2.4}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.primary}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getReportCountByType('sinif')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Sınıf
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={4} md={2.4}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.sunset}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getReportCountByType('ogrenci')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Öğrenci
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={4} md={2.4}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.ocean}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getReportCountByType('konu')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Konu
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={4} md={2.4}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.success}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getReportCountByType('sinav')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Sınav
                </Typography>
              </GlassCard>
            </Grid>
            <Grid item xs={6} sm={4} md={2.4}>
              <GlassCard glassIntensity="light" hoverable gradient={modernColors.gradients.forest}>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 0.5 }}>
                  {getReportCountByType('genel')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Genel
                </Typography>
              </GlassCard>
            </Grid>
          </Grid>
        </motion.div>

        {/* Report Cards */}
        <AnimatePresence mode="wait">
          {filteredReports.length > 0 ? (
            <Grid container spacing={3}>
              {filteredReports.map((report, index) => (
                <Grid item xs={12} sm={6} md={4} key={report.id}>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                  >
                    <GlassCard
                      glassIntensity="medium"
                      elevated
                      hoverable
                      gradient={getTypeGradient(report.tip)}
                    >
                      {/* Report Header */}
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                        <Box
                          sx={{
                            width: 56,
                            height: 56,
                            borderRadius: 2,
                            background: getTypeGradient(report.tip),
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                          }}
                        >
                          {getTypeIcon(report.tip)}
                        </Box>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          <Chip
                            label={getTypeLabel(report.tip)}
                            size="small"
                            sx={{
                              background: getTypeGradient(report.tip),
                              color: 'white',
                              fontWeight: 600,
                            }}
                          />
                          <Chip
                            icon={getFormatIcon(report.format)}
                            label={report.format.toUpperCase()}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </Box>

                      {/* Report Info */}
                      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                        {report.baslik}
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mb: 2,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                        }}
                      >
                        {report.aciklama}
                      </Typography>

                      {/* Report Metadata */}
                      <Box
                        sx={{
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 1,
                          mb: 3,
                          p: 1.5,
                          borderRadius: 2,
                          background: modernColors.glass.white.medium,
                        }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CalendarToday fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            {new Date(report.tarih).toLocaleDateString('tr-TR', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <InsertDriveFile fontSize="small" color="action" />
                          <Typography variant="caption" color="text.secondary">
                            {report.boyut}
                          </Typography>
                        </Box>
                      </Box>

                      {/* Actions */}
                      <ModernButton
                        variant="gradient"
                        gradient={getTypeGradient(report.tip)}
                        icon={<Download />}
                        fullWidth
                        onClick={() => handleDownloadReport(report)}
                        glow
                      >
                        Raporu İndir
                      </ModernButton>
                    </GlassCard>
                  </motion.div>
                </Grid>
              ))}
            </Grid>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
            >
              <GlassCard glassIntensity="medium" elevated>
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Box
                    sx={{
                      width: 120,
                      height: 120,
                      borderRadius: '50%',
                      background: modernColors.gradients.forest,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mx: 'auto',
                      mb: 3,
                    }}
                  >
                    <Assessment sx={{ fontSize: 64, color: 'white' }} />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                    Rapor bulunamadı
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    Arama kriterlerinize uygun rapor bulunmamaktadır
                  </Typography>
                </Box>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>
    </DashboardScaffold>
  );
}

export default ModernTeacherReportsPage;
