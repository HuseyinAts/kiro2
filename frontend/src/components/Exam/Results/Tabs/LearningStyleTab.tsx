/**
 * Hybrid Learning Style Analysis Tab Component
 *
 * Displays VARK learning style profile and performance alignment
 * Extracted from AdvancedExamResults.tsx
 */

import {
  MenuBook,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Alert,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import * as React from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

export interface LearningStyleTabProps {
  analiz: {
    vark_profili?: {
      visual?: number
      auditory?: number
      reading?: number
      kinesthetic?: number
    }
    hibrit_profil_ozeti?: {
      hibrit_kod?: string
      dominant_vark_stili?: string
      guven_seviyesi?: number
      profil_aciklamasi?: string
    }
    performans_uyumu?: Array<{
      konu: string
      basari_yuzdesi?: number
      ogrenme_stili_uyumu?: number
      onerilen_yontem?: string
      uyum_analizi: string
    }>
  } | null
}

/**
 * Learning Style Tab
 *
 * Shows:
 * - VARK profile (Visual, Auditory, Reading, Kinesthetic)
 * - Hybrid profile summary
 * - Topic-based learning style alignment
 */
export const LearningStyleTab: React.FC<LearningStyleTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        Öğrenme stili analizi yükleniyor...
      </Alert>
    );
  }

  const vark_profili = analiz.vark_profili || {};
  const hibrit_ozet = analiz.hibrit_profil_ozeti || {};
  const performans_uyumu = analiz.performans_uyumu || [];

  // VARK radar chart verisi
  const varkRadarData = [
    { subject: 'Görsel', A: (vark_profili.visual || 0) * 100, fullMark: 100 },
    { subject: 'İşitsel', A: (vark_profili.auditory || 0) * 100, fullMark: 100 },
    { subject: 'Okuma', A: (vark_profili.reading || 0) * 100, fullMark: 100 },
    { subject: 'Kinestetik', A: (vark_profili.kinesthetic || 0) * 100, fullMark: 100 },
  ];

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <MenuBook sx={{ mr: 1, color: 'primary.main' }} />
        Hibrit Öğrenme Stili Analizi
      </Typography>

      {/* Hibrit Profil Özeti */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          📋 Öğrenme Stili Profili
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Hibrit Kod:</strong> {hibrit_ozet.hibrit_kod || 'Bilinmiyor'}
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Dominant VARK Stili:</strong>
                <Chip
                  label={hibrit_ozet.dominant_vark_stili || 'Bilinmiyor'}
                  color="primary"
                  sx={{ ml: 1 }}
                />
              </Typography>
              <Typography variant="subtitle1" gutterBottom>
                <strong>Güven Seviyesi:</strong> {((hibrit_ozet.guven_seviyesi || 0) * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" gutterBottom>Profil Açıklaması:</Typography>
            <Typography variant="body2" color="textSecondary">
              {hibrit_ozet.profil_aciklamasi || 'Açıklama mevcut değil'}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* VARK Radar Chart */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              👁️ VARK Öğrenme Tercihleri
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={varkRadarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="VARK Profili"
                  dataKey="A"
                  stroke="#8884d8"
                  fill="#8884d8"
                  fillOpacity={0.6}
                />
              </RadarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              📊 VARK Skor Detayları
            </Typography>
            {Object.entries(vark_profili).map(([stil, skor]: [string, any]) => (
              <Box key={stil} sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  {stil.charAt(0).toUpperCase() + stil.slice(1)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={skor * 100}
                  sx={{ height: 10, borderRadius: 5 }}
                  color={skor >= 0.7 ? 'success' : skor >= 0.5 ? 'warning' : 'error'}
                />
                <Typography variant="caption">{(skor * 100).toFixed(0)}%</Typography>
              </Box>
            ))}
          </Paper>
        </Grid>
      </Grid>

      {/* Performans Uyumu */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          📊 Konu Bazlı Öğrenme Stili Uyumu
        </Typography>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Konu</TableCell>
                <TableCell align="center">Başarı %</TableCell>
                <TableCell align="center">Stil Uyumu %</TableCell>
                <TableCell align="center">Önerilen Yöntem</TableCell>
                <TableCell align="center">Uyum Durumu</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {performans_uyumu.map((uyum: any, index: number) => (
                <TableRow key={index}>
                  <TableCell>{uyum.konu}</TableCell>
                  <TableCell align="center">{uyum.basari_yuzdesi?.toFixed(1)}%</TableCell>
                  <TableCell align="center">{uyum.ogrenme_stili_uyumu?.toFixed(1)}%</TableCell>
                  <TableCell align="center">
                    {uyum.onerilen_yontem?.replace(/_/g, ' ')}
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={uyum.uyum_analizi}
                      color={
                        uyum.uyum_analizi === 'yuksek' ? 'success' :
                        uyum.uyum_analizi === 'orta' ? 'warning' : 'error'
                      }
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default LearningStyleTab;
