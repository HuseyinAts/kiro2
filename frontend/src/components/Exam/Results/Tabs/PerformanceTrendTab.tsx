/**
 * Performance Trend Analysis Tab Component
 *
 * Displays historical performance trends across multiple exams
 * Extracted from AdvancedExamResults.tsx
 */

import {
  Insights,
  TrendingUp,
  Star,
  Warning,
  Assessment,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Alert,
  Chip,
} from '@mui/material';
import * as React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

export interface PerformanceTrendTabProps {
  trend: {
    son_5_sinav?: number[]
    ortalama_artis?: number
    en_iyi_performans?: number
    en_dusuk_performans?: number
    tutarlilik_skoru?: number
    trend_yonu?: string
  } | null
}

/**
 * Performance Trend Tab
 *
 * Shows:
 * - Last 5 exam scores trend
 * - Average improvement rate
 * - Best and worst performance
 * - Consistency score
 */
export const PerformanceTrendTab: React.FC<PerformanceTrendTabProps> = ({ trend }) => {
  if (!trend) {
    return (
      <Alert severity="info">
        Performans trendi yükleniyor...
      </Alert>
    );
  }

  const trendData = trend.son_5_sinav?.map((puan: number, index: number) => ({
    sinav: `Sınav ${index + 1}`,
    puan,
  })) || [];

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <Insights sx={{ mr: 1, color: 'primary.main' }} />
        Performans Trendi Analizi
      </Typography>

      {/* Trend İstatistikleri */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h5" color="success.main">
                {trend.ortalama_artis?.toFixed(2) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Ortalama Artış
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Star sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h5" color="warning.main">
                {trend.en_iyi_performans || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                En İyi Performans
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Warning sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
              <Typography variant="h5" color="error.main">
                {trend.en_dusuk_performans || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                En Düşük Performans
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Assessment sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h5" color="info.main">
                {((trend.tutarlilik_skoru || 0) * 100).toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Tutarlılık Skoru
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Trend Grafiği */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          📈 Son 5 Sınav Performans Trendi
        </Typography>

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="sinav" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="puan"
              stroke="#8884d8"
              strokeWidth={3}
              dot={{ fill: '#8884d8', strokeWidth: 2, r: 6 }}
              name="Puan"
            />
          </LineChart>
        </ResponsiveContainer>

        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Chip
            label={`Trend: ${trend.trend_yonu || 'Bilinmiyor'}`}
            color={
              trend.trend_yonu === 'yukselis' ? 'success' :
              trend.trend_yonu === 'dusus' ? 'error' : 'default'
            }
            size="medium"
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default PerformanceTrendTab;
