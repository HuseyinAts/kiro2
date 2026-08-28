import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Avatar,
  Chip,
  LinearProgress,
  Paper
} from '@mui/material';
import {
  WarningAmber,
  LocalHospital,
  Speed,
  TrendingDown,
  Psychology,
  AssignmentTurnedIn
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { GlassCard } from '../ui/GlassCard';
import modernColors from '../../theme/modern-colors';
import apiClient from '../../services/apiClient';

interface AtRiskStudent {
  id: string;
  name: string;
  risk_level: 'high' | 'medium' | 'low';
  recent_accuracy: number;
  fsrs_retrievability_drop: number;
  misconceptions: string[];
  root_causes: string[];
  avatar_url: string;
}

interface RiskHeatmapData {
  class_average_retrievability: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  at_risk_students: AtRiskStudent[];
  recommended_actions: string[];
}

export function EarlyWarningDashboard() {
  const [data, setData] = useState<RiskHeatmapData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/analytics/predictive/at-risk-students');
      setData(response.data);
    } catch (error) {
      console.error('Erken uyarı verisi alınamadı:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <LinearProgress color="secondary" />
        <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>
          Yapay Zeka (Predictive AI) öğrenci risk profillerini hesaplıyor...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Üst İstatistikler */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <GlassCard sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ p: 2, borderRadius: '50%', bgcolor: 'error.main', color: 'white' }}>
              <WarningAmber />
            </Box>
            <Box>
              <Typography variant="h4" fontWeight="bold">
                {data.high_risk_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Yüksek Riskli Öğrenci
              </Typography>
            </Box>
          </GlassCard>
        </Grid>
        <Grid item xs={12} md={4}>
          <GlassCard sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ p: 2, borderRadius: '50%', bgcolor: 'warning.main', color: 'white' }}>
              <Speed />
            </Box>
            <Box>
              <Typography variant="h4" fontWeight="bold">
                {data.medium_risk_count}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Orta Riskli Öğrenci
              </Typography>
            </Box>
          </GlassCard>
        </Grid>
        <Grid item xs={12} md={4}>
          <GlassCard sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2, background: 'linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.05) 100%)' }}>
            <Box sx={{ p: 2, borderRadius: '50%', bgcolor: 'primary.main', color: 'white' }}>
              <Psychology />
            </Box>
            <Box>
              <Typography variant="h4" fontWeight="bold">
                %{data.class_average_retrievability.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sınıf Ortalama Hatırlama (FSRS)
              </Typography>
            </Box>
          </GlassCard>
        </Grid>
      </Grid>

      {/* AI Önerileri */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <LocalHospital color="secondary" /> AI Kurtarma Önerileri (Co-Pilot)
        </Typography>
        <Grid container spacing={2}>
          {data.recommended_actions.map((action, index) => (
            <Grid item xs={12} md={6} key={index}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    borderRadius: 3,
                    border: '1px solid',
                    borderColor: modernColors.primary[200],
                    bgcolor: 'rgba(33, 150, 243, 0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2
                  }}
                >
                  <AssignmentTurnedIn color="primary" />
                  <Typography variant="body1">{action}</Typography>
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Riskli Öğrenciler Listesi */}
      <Typography variant="h6" fontWeight="bold" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingDown color="error" /> Riskli Öğrenci Radarı
      </Typography>
      <Grid container spacing={3}>
        {data.at_risk_students.map((student, i) => (
          <Grid item xs={12} key={student.id}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard
                sx={{
                  p: 3,
                  display: 'flex',
                  flexDirection: { xs: 'column', md: 'row' },
                  alignItems: { xs: 'flex-start', md: 'center' },
                  gap: 3,
                  borderLeft: '6px solid',
                  borderLeftColor: student.risk_level === 'high' ? modernColors.error[500] : modernColors.warning[500]
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, minWidth: 250 }}>
                  <Avatar src={student.avatar_url} sx={{ width: 64, height: 64 }} />
                  <Box>
                    <Typography variant="h6" fontWeight="bold">{student.name}</Typography>
                    <Chip
                      size="small"
                      label={student.risk_level === 'high' ? 'Kritik Düşüş' : 'Uyarı'}
                      color={student.risk_level === 'high' ? 'error' : 'warning'}
                      sx={{ mt: 0.5, fontWeight: 'bold' }}
                    />
                  </Box>
                </Box>

                <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Kavram Yanılgıları (Kök Nedenler)
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {student.misconceptions.map((m, idx) => (
                        <Chip key={idx} label={m} size="small" variant="outlined" color="error" />
                      ))}
                      {student.root_causes.map((rc, idx) => (
                        <Chip key={idx} label={rc} size="small" variant="outlined" color="secondary" />
                      ))}
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 4 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">FSRS Hafıza Kaybı</Typography>
                      <Typography variant="body1" fontWeight="bold" color="error.main">
                        -%{student.fsrs_retrievability_drop.toFixed(1)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Son 7 Gün Başarı</Typography>
                      <Typography variant="body1" fontWeight="bold" color={student.recent_accuracy < 50 ? "error.main" : "warning.main"}>
                        %{student.recent_accuracy.toFixed(1)}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              </GlassCard>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
