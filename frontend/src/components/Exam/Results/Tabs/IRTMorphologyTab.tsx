/**
 * IRT + Morphology Analysis Tab Component
 *
 * Displays IRT (Item Response Theory) parameters and Turkish morphology analysis
 * Extracted from AdvancedExamResults.tsx
 */

import {
  Science,
  Speed,
  AutoGraph,
  Language,
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
  LinearProgress,
} from '@mui/material';
import * as React from 'react';

export interface IRTMorphologyTabProps {
  analiz: {
    genel_istatistikler?: {
      ortalama_zorluk?: number
      ortalama_ayirt_edicilik?: number
      ortalama_morfoloji_faktoru?: number
    }
    morfoloji_farkindaliği?: {
      genel_seviye?: string
      guclu_alanlar?: string[]
      gelisim_alanlari?: string[]
      oneri_skorlari?: Record<string, number>
    }
    irt_performans_profili?: {
      yetenek_tahmini?: number
      standart_hata?: number
      guven_araligi?: [number, number]
    }
  } | null
}

/**
 * IRT + Morphology Tab
 *
 * Shows:
 * - IRT parameters (difficulty, discrimination, morphology factor)
 * - Morphology awareness analysis (Turkish language complexity)
 * - IRT performance profile (ability estimate, confidence interval)
 */
export const IRTMorphologyTab: React.FC<IRTMorphologyTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        IRT + Morfoloji analizi yükleniyor...
      </Alert>
    );
  }

  const genel_stats = analiz.genel_istatistikler || {};
  const morfoloji_fark = analiz.morfoloji_farkindaliği || {};
  const irt_profil = analiz.irt_performans_profili || {};

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <Science sx={{ mr: 1, color: 'primary.main' }} />
        IRT + Morfoloji Analizi
      </Typography>

      {/* IRT Parametreleri */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Speed sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h5" color="info.main">
                {genel_stats.ortalama_zorluk?.toFixed(3) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Ortalama Zorluk
              </Typography>
              <Typography variant="caption" display="block">
                (-4 ile +4 arası)
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <AutoGraph sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h5" color="success.main">
                {genel_stats.ortalama_ayirt_edicilik?.toFixed(3) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Ayırt Edicilik
              </Typography>
              <Typography variant="caption" display="block">
                Soru kalitesi göstergesi
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Language sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h5" color="warning.main">
                {genel_stats.ortalama_morfoloji_faktoru?.toFixed(3) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Morfoloji Faktörü
              </Typography>
              <Typography variant="caption" display="block">
                Türkçe karmaşıklık
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Morfoloji Farkındalığı */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🔤 Morfoloji Farkındalığı Analizi
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Genel Seviye: <Chip label={morfoloji_fark.genel_seviye || 'Bilinmiyor'} color="primary" />
            </Typography>

            {morfoloji_fark.guclu_alanlar && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Güçlü Alanlar:</Typography>
                {morfoloji_fark.guclu_alanlar.map((alan: string, index: number) => (
                  <Chip key={index} label={alan} color="success" size="small" sx={{ mr: 1, mb: 1 }} />
                ))}
              </Box>
            )}

            {morfoloji_fark.gelisim_alanlari && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>Gelişim Alanları:</Typography>
                {morfoloji_fark.gelisim_alanlari.map((alan: string, index: number) => (
                  <Chip key={index} label={alan} color="warning" size="small" sx={{ mr: 1, mb: 1 }} />
                ))}
              </Box>
            )}
          </Grid>

          <Grid item xs={12} md={6}>
            {morfoloji_fark.oneri_skorlari && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>Öneri Skorları:</Typography>
                {Object.entries(morfoloji_fark.oneri_skorlari).map(([oneri, skor]: [string, any]) => (
                  <Box key={oneri} sx={{ mb: 1 }}>
                    <Typography variant="body2">{oneri.replace(/_/g, ' ')}</Typography>
                    <LinearProgress
                      variant="determinate"
                      value={skor}
                      sx={{ height: 8, borderRadius: 4 }}
                      color={skor >= 80 ? 'success' : skor >= 60 ? 'warning' : 'error'}
                    />
                    <Typography variant="caption">{skor}%</Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* IRT Performans Profili */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          📈 IRT Performans Profili
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {irt_profil.yetenek_tahmini?.toFixed(2) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Yetenek Tahmini (θ)
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {irt_profil.standart_hata?.toFixed(2) || 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Standart Hata
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" color="success.main">
                {irt_profil.guven_araligi ?
                  `${irt_profil.guven_araligi[0]?.toFixed(2)} - ${irt_profil.guven_araligi[1]?.toFixed(2)}` :
                  'N/A'
                }
              </Typography>
              <Typography variant="body2" color="textSecondary">
                %95 Güven Aralığı
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default IRTMorphologyTab;
