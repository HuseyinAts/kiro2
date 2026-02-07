/**
 * ZPD + Maarif Analysis Tab Component
 *
 * Displays Zone of Proximal Development (ZPD) analysis and MEB Maarif values
 * Extracted from AdvancedExamResults.tsx
 */

import {
  Psychology,
  Timeline,
  TrendingUp,
  School,
  Star,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Alert,
  LinearProgress,
} from '@mui/material';
import * as React from 'react';

export interface ZPDAnalysisTabProps {
  analiz: {
    genel_zpd_profili?: {
      ortalama_mevcut_seviye?: number
      ortalama_optimal_zorluk?: number
      kulturel_uyum_seviyesi?: string
      maarif_degerleri_uyumu?: string
    }
    kulturel_faktorler?: Record<string, number>
    maarif_degerleri_profili?: Record<string, number>
  } | null
}

/**
 * ZPD Analysis Tab
 *
 * Shows:
 * - General ZPD profile (current level, optimal difficulty)
 * - Turkish cultural factors
 * - MEB Maarif values alignment
 */
export const ZPDAnalysisTab: React.FC<ZPDAnalysisTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        ZPD analizi yükleniyor...
      </Alert>
    );
  }

  const genel_profil = analiz.genel_zpd_profili || {};
  const kulturel_faktorler = analiz.kulturel_faktorler || {};
  const maarif_profili = analiz.maarif_degerleri_profili || {};

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <Psychology sx={{ mr: 1, color: 'primary.main' }} />
        ZPD + Maarif Analizi
      </Typography>

      {/* Genel ZPD Profili */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Timeline sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h5" color="primary.main">
                {genel_profil.ortalama_mevcut_seviye?.toFixed(1) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Mevcut Seviye
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h5" color="success.main">
                {genel_profil.ortalama_optimal_zorluk?.toFixed(1) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Optimal Zorluk
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <School sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h6" color="info.main">
                {genel_profil.kulturel_uyum_seviyesi || 'Bilinmiyor'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Kültürel Uyum
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Star sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h6" color="warning.main">
                {genel_profil.maarif_degerleri_uyumu || 'Bilinmiyor'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Maarif Uyumu
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Kültürel Faktörler */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🏛️ Türk Kültürü Faktörleri
        </Typography>

        <Grid container spacing={2}>
          {Object.entries(kulturel_faktorler).map(([faktor, deger]: [string, any]) => (
            <Grid item xs={12} md={6} key={faktor}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  {faktor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={deger * 100}
                  sx={{ height: 10, borderRadius: 5 }}
                  color={deger >= 0.8 ? 'success' : deger >= 0.6 ? 'warning' : 'error'}
                />
                <Typography variant="caption">{(deger * 100).toFixed(0)}%</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* MEB Maarif Değerleri */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          🇹🇷 MEB Maarif Değerleri Uyumu
        </Typography>

        <Grid container spacing={2}>
          {Object.entries(maarif_profili).map(([deger, uyum]: [string, any]) => (
            <Grid item xs={12} md={4} key={deger}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  {deger.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={uyum * 100}
                  sx={{ height: 10, borderRadius: 5 }}
                  color={uyum >= 0.8 ? 'success' : uyum >= 0.6 ? 'warning' : 'error'}
                />
                <Typography variant="caption">{(uyum * 100).toFixed(0)}%</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default ZPDAnalysisTab;
