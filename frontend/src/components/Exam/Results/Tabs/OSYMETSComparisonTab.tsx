/**
 * ÖSYM/ETS Standards Comparison Tab Component
 *
 * Displays comparison between Turkish ÖSYM and international ETS standards
 * Extracted from AdvancedExamResults.tsx
 */

import {
  CompareArrows,
  Lightbulb,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import * as React from 'react';

export interface OSYMETSComparisonTabProps {
  analiz: {
    sonuc_degerlendirmesi?: string
    osym_karsilastirma?: {
      ayirt_edicilik_durumu?: {
        durum: string
        skor: number
      }
      zorluk_durumu?: {
        durum: string
        skor: number
      }
      sans_faktoru_durumu?: {
        durum: string
        skor: number
      }
      genel_uyum_skoru?: number
    }
    ets_karsilastirma?: {
      ayirt_edicilik_durumu?: {
        durum: string
        skor: number
      }
      zorluk_durumu?: {
        durum: string
        skor: number
      }
      sans_faktoru_durumu?: {
        durum: string
        skor: number
      }
      genel_uyum_skoru?: number
    }
    morfoloji_avantaji?: {
      osym_ets_uzerindeki_avantaj?: string
      ek_bilgi_boyutlari?: string[]
    }
  } | null
}

/**
 * Get chip color based on status
 */
const getStatusColor = (durum: string): 'success' | 'warning' | 'error' | 'default' => {
  if (durum === 'ideal' || durum === 'uygun') {return 'success';}
  if (durum === 'kabul_edilebilir') {return 'warning';}
  return 'error';
};

/**
 * ÖSYM/ETS Comparison Tab
 *
 * Shows:
 * - ÖSYM standards comparison
 * - ETS standards comparison
 * - Turkish morphology advantage
 */
export const OSYMETSComparisonTab: React.FC<OSYMETSComparisonTabProps> = ({ analiz }) => {
  if (!analiz) {
    return (
      <Alert severity="info">
        ÖSYM/ETS karşılaştırması yükleniyor...
      </Alert>
    );
  }

  const osym_karsilastirma = analiz.osym_karsilastirma || {};
  const ets_karsilastirma = analiz.ets_karsilastirma || {};
  const morfoloji_avantaji = analiz.morfoloji_avantaji || {};

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <CompareArrows sx={{ mr: 1, color: 'primary.main' }} />
        ÖSYM/ETS Standartları Karşılaştırması
      </Typography>

      {/* Genel Değerlendirme */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="h6">
          Genel Değerlendirme: {analiz.sonuc_degerlendirmesi || 'Bilinmiyor'}
        </Typography>
      </Alert>

      {/* Karşılaştırma Tabloları */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'error.main' }}>
              🇹🇷 ÖSYM Standartları
            </Typography>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Parametre</TableCell>
                    <TableCell align="center">Durum</TableCell>
                    <TableCell align="center">Skor</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Ayırt Edicilik</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={osym_karsilastirma.ayirt_edicilik_durumu?.durum || 'N/A'}
                        size="small"
                        color={getStatusColor(osym_karsilastirma.ayirt_edicilik_durumu?.durum || '')}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {osym_karsilastirma.ayirt_edicilik_durumu?.skor?.toFixed(0) || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Zorluk Seviyesi</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={osym_karsilastirma.zorluk_durumu?.durum || 'N/A'}
                        size="small"
                        color={getStatusColor(osym_karsilastirma.zorluk_durumu?.durum || '')}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {osym_karsilastirma.zorluk_durumu?.skor?.toFixed(0) || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Şans Faktörü</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={osym_karsilastirma.sans_faktoru_durumu?.durum || 'N/A'}
                        size="small"
                        color={getStatusColor(osym_karsilastirma.sans_faktoru_durumu?.durum || '')}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {osym_karsilastirma.sans_faktoru_durumu?.skor?.toFixed(0) || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow sx={{ backgroundColor: 'rgba(255, 0, 0, 0.1)' }}>
                    <TableCell><strong>Genel Uyum</strong></TableCell>
                    <TableCell align="center">-</TableCell>
                    <TableCell align="center">
                      <strong>{osym_karsilastirma.genel_uyum_skoru?.toFixed(0) || 'N/A'}</strong>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'info.main' }}>
              🌍 ETS Standartları
            </Typography>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Parametre</TableCell>
                    <TableCell align="center">Durum</TableCell>
                    <TableCell align="center">Skor</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Ayırt Edicilik</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={ets_karsilastirma.ayirt_edicilik_durumu?.durum || 'N/A'}
                        size="small"
                        color={getStatusColor(ets_karsilastirma.ayirt_edicilik_durumu?.durum || '')}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {ets_karsilastirma.ayirt_edicilik_durumu?.skor?.toFixed(0) || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Zorluk Seviyesi</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={ets_karsilastirma.zorluk_durumu?.durum || 'N/A'}
                        size="small"
                        color={getStatusColor(ets_karsilastirma.zorluk_durumu?.durum || '')}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {ets_karsilastirma.zorluk_durumu?.skor?.toFixed(0) || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Şans Faktörü</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={ets_karsilastirma.sans_faktoru_durumu?.durum || 'N/A'}
                        size="small"
                        color={getStatusColor(ets_karsilastirma.sans_faktoru_durumu?.durum || '')}
                      />
                    </TableCell>
                    <TableCell align="center">
                      {ets_karsilastirma.sans_faktoru_durumu?.skor?.toFixed(0) || 'N/A'}
                    </TableCell>
                  </TableRow>
                  <TableRow sx={{ backgroundColor: 'rgba(0, 0, 255, 0.1)' }}>
                    <TableCell><strong>Genel Uyum</strong></TableCell>
                    <TableCell align="center">-</TableCell>
                    <TableCell align="center">
                      <strong>{ets_karsilastirma.genel_uyum_skoru?.toFixed(0) || 'N/A'}</strong>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Türkçe Morfoloji Avantajı */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
          🔤 Türkçe Morfoloji Avantajı
        </Typography>

        <Typography variant="body1" paragraph>
          {morfoloji_avantaji.osym_ets_uzerindeki_avantaj || 'Avantaj açıklaması mevcut değil'}
        </Typography>

        {morfoloji_avantaji.ek_bilgi_boyutlari && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>Ek Analiz Boyutları:</Typography>
            <List dense>
              {morfoloji_avantaji.ek_bilgi_boyutlari.map((boyut: string, index: number) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Lightbulb color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={boyut} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default OSYMETSComparisonTab;
