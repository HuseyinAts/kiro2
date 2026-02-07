/**
 * ZPD + MEB Maarif Dashboard Bileşeni
 * Türk eğitim kültürüne uyarlanmış ZPD sistemi görüntüleme
 */

import {
  Psychology as PsychologyIcon,
  School as SchoolIcon,
  Groups as GroupsIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Paper,
  Alert,
  CircularProgress,
  Button,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { revolutionaryFeaturesService } from '../../services/revolutionaryFeaturesService';
import { TurkishZPDRange, ZPDRecommendation, CulturalContext } from '../../types';

interface ZPDMaarifDashboardProps {
  studentId: string;
  onZPDUpdate?: (zpd: TurkishZPDRange) => void;
}

const ZPDMaarifDashboard: React.FC<ZPDMaarifDashboardProps> = ({
  studentId,
  onZPDUpdate,
}) => {
  const [zpdRange, setZpdRange] = useState<TurkishZPDRange | null>(null);
  const [recommendation, setRecommendation] = useState<ZPDRecommendation | null>(null);
  const [culturalContext, setCulturalContext] = useState<CulturalContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ZPD verilerini yükle
  useEffect(() => {
    const loadZPDData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Örnek davranışsal veri
        const sampleBehavioralData = {
          group_study_sessions: 15,
          individual_study_sessions: 8,
          teacher_question_count: 12,
          peer_interaction_count: 25,
          help_seeking_frequency: 10,
          video_watch_time: 120,
          text_reading_time: 90,
          interactive_engagement: 35,
          quiz_completion_rate: 0.85,
          hands_on_performance: 0.78,
          visual_content_performance: 0.82,
          auditory_content_performance: 0.75,
          text_content_performance: 0.80,
          note_taking_frequency: 8,
        };

        // ZPD aralığını hesapla
        const zpd = await revolutionaryFeaturesService.calculateRevolutionaryZPD(
          studentId,
          'matematik',
          6.5,
          sampleBehavioralData,
          'Türk matematikçilerin katkıları ve geometri',
        );
        setZpdRange(zpd);
        onZPDUpdate?.(zpd);

        // Öneri al
        const rec = await revolutionaryFeaturesService.generateRevolutionaryRecommendation(
          studentId,
          'matematik',
          6.5,
          sampleBehavioralData,
          'Geometri konusunda uzmanlaşma',
          'Türk matematikçilerin katkıları ve geometri',
        );
        setRecommendation(rec);

        // Kültürel bağlamı al
        const context = await revolutionaryFeaturesService.detectCulturalContext(studentId, sampleBehavioralData);
        setCulturalContext(context);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'ZPD verileri yüklenirken hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      loadZPDData();
    }
  }, [studentId, onZPDUpdate]);

  // Zorluk seviyesi renk kodlaması
  const _getDifficultyColor = (level: string): 'success' | 'warning' | 'error' | 'default' => {
    switch (level) {
      case 'kolay': return 'success';
      case 'orta': return 'warning';
      case 'zor': return 'error';
      default: return 'default';
    }
  };

  // Maarif değeri renk kodlaması
  const _getMaarifColor = (value: string): 'error' | 'primary' | 'success' | 'default' => {
    switch (value) {
      case 'milli': return 'error';
      case 'evrensel': return 'primary';
      case 'kök': return 'success';
      default: return 'default';
    }
  };

  // Öğrenme modu renk kodlaması
  const getLearningModeColor = (mode: string): 'primary' | 'secondary' | 'info' | 'default' => {
    switch (mode) {
      case 'group': return 'primary';
      case 'individual': return 'secondary';
      case 'mixed': return 'info';
      default: return 'default';
    }
  };

  // Mark unused functions as available for future use
  void _getDifficultyColor;
  void _getMaarifColor;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
        <CircularProgress size={32} />
        <Typography variant="body1" sx={{ ml: 2, color: 'text.secondary' }}>
          ZPD analizi yükleniyor...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={() => window.location.reload()}
          sx={{ mt: 1 }}
        >
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  if (!zpdRange) {
    return (
      <Box sx={{ textAlign: 'center', p: 4, color: 'text.secondary' }}>
        <Typography>ZPD verisi bulunamadı</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* ZPD Aralığı Görselleştirme */}
      <Card>
        <CardHeader>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PsychologyIcon />
            Yakınsal Gelişim Alanı (ZPD) - Türk Eğitim Modeli
          </Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main" fontWeight="bold">
                  {zpdRange.current_level.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Mevcut Seviye
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary.main" fontWeight="bold">
                  {(zpdRange.upper_bound - zpdRange.lower_bound).toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ZPD Aralığı
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="secondary.main" fontWeight="bold">
                  {zpdRange.optimal_challenge.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Optimal Zorluk
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* ZPD Çubuğu */}
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Alt Sınır ({zpdRange.lower_bound.toFixed(1)})
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Mevcut ({zpdRange.current_level.toFixed(1)})
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Optimal ({zpdRange.optimal_challenge.toFixed(1)})
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Üst Sınır ({zpdRange.upper_bound.toFixed(1)})
              </Typography>
            </Box>
            <Box sx={{ position: 'relative' }}>
              <LinearProgress
                variant="determinate"
                value={((zpdRange.current_level - zpdRange.lower_bound) / (zpdRange.upper_bound - zpdRange.lower_bound)) * 100}
                sx={{
                  height: 12,
                  borderRadius: 6,
                  '& .MuiLinearProgress-bar': {
                    background: 'linear-gradient(to right, #4ade80, #3b82f6)',
                  },
                }}
              />
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: `${((zpdRange.optimal_challenge - zpdRange.lower_bound) / (zpdRange.upper_bound - zpdRange.lower_bound)) * 100}%`,
                  width: 8,
                  height: 12,
                  bgcolor: 'secondary.main',
                  borderRadius: 6,
                  opacity: 0.75,
                }}
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Kültürel Bağlam */}
      {culturalContext && (
        <Card>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <GroupsIcon />
              Kültürel Bağlam Analizi
            </Typography>
          </CardHeader>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                  Öğrenme Tercihleri
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Grup Çalışması</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.group_learning_preference * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Öğretmen Saygısı</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.teacher_respect_level * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Aile Katılımı</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.family_involvement * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Akran Rekabeti</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.peer_competition * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                  Kültürel Değerler
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Kolektif Başarı</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.collective_success * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Büyük Bilgeliği</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.elder_wisdom_value * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Sosyal Uyum</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.social_harmony * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">Otorite Kabulü</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {(culturalContext.authority_acceptance * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* MEB Maarif Değerleri */}
      <Card>
        <CardHeader>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SchoolIcon />
            MEB Maarif Değerleri Entegrasyonu
          </Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, border: 2, borderColor: 'error.light', bgcolor: 'error.50' }}>
                <Typography variant="subtitle1" fontWeight="semibold" color="error.main" gutterBottom>
                  Milli Değerler
                </Typography>
                <Typography variant="body2" color="error.main" sx={{ mb: 1 }}>
                  Vatan, millet, aile değerleri
                </Typography>
                <Typography variant="caption" color="error.main" sx={{ opacity: 0.75 }}>
                  Uyum: {(zpdRange.maarif_alignment.national_values_alignment * 100).toFixed(0)}%
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, border: 2, borderColor: 'primary.light', bgcolor: 'primary.50' }}>
                <Typography variant="subtitle1" fontWeight="semibold" color="primary.main" gutterBottom>
                  Evrensel Değerler
                </Typography>
                <Typography variant="body2" color="primary.main" sx={{ mb: 1 }}>
                  Adalet, dostluk, dürüstlük
                </Typography>
                <Typography variant="caption" color="primary.main" sx={{ opacity: 0.75 }}>
                  Uyum: {(zpdRange.maarif_alignment.universal_values_alignment * 100).toFixed(0)}%
                </Typography>
              </Paper>
            </Grid>

            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, border: 2, borderColor: 'success.light', bgcolor: 'success.50' }}>
                <Typography variant="subtitle1" fontWeight="semibold" color="success.main" gutterBottom>
                  Kök Değerler
                </Typography>
                <Typography variant="body2" color="success.main" sx={{ mb: 1 }}>
                  Sabır, saygı, sevgi
                </Typography>
                <Typography variant="caption" color="success.main" sx={{ opacity: 0.75 }}>
                  Uyum: {(zpdRange.maarif_alignment.root_values_alignment * 100).toFixed(0)}%
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="body1" fontWeight="medium" color="text.primary">
                Genel Maarif Uyumu
              </Typography>
              <Typography variant="h5" fontWeight="bold" color="secondary.main">
                {(zpdRange.maarif_alignment.overall_alignment * 100).toFixed(0)}%
              </Typography>
            </Box>
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Uyumlu Değerler: {zpdRange.maarif_alignment.aligned_values.join(', ')}
              </Typography>
            </Box>
          </Paper>
        </CardContent>
      </Card>

      {/* ZPD Önerileri */}
      {recommendation && (
        <Card>
          <CardHeader>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon />
              Kişiselleştirilmiş Öneri
            </Typography>
          </CardHeader>
          <CardContent>
            <Paper sx={{ p: 2, border: 1, borderColor: 'grey.300', '&:hover': { boxShadow: 1 } }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" fontWeight="medium" gutterBottom>
                    {recommendation.subject.charAt(0).toUpperCase() + recommendation.subject.slice(1)} Öğrenme Önerisi
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {recommendation.reasoning}
                  </Typography>

                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="body2" fontWeight="medium" color="primary.main">
                          {recommendation.recommended_difficulty.toFixed(1)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Önerilen Zorluk
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Chip
                          label={recommendation.learning_mode}
                          color={getLearningModeColor(recommendation.learning_mode)}
                          size="small"
                        />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Öğrenme Modu
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="body2" fontWeight="medium" color="success.main">
                          {(recommendation.teacher_guidance_level * 100).toFixed(0)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Öğretmen Rehberliği
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="body2" fontWeight="medium" color="secondary.main">
                          {(recommendation.confidence_score * 100).toFixed(0)}%
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Güven Skoru
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Chip
                      label={recommendation.content_type}
                      color="primary"
                      variant="outlined"
                      size="small"
                    />
                    <Typography variant="caption" color="text.secondary">
                      Akran Desteği: {(recommendation.peer_support_level * 100).toFixed(0)}%
                    </Typography>
                  </Box>

                  {recommendation.maarif_integration.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Maarif Entegrasyonu:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {recommendation.maarif_integration.map((value, idx) => (
                          <Chip
                            key={idx}
                            label={value}
                            color="success"
                            variant="outlined"
                            size="small"
                          />
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>

                <Button
                  variant="contained"
                  color="primary"
                  size="small"
                  sx={{ ml: 2 }}
                >
                  Başla
                </Button>
              </Box>
            </Paper>
          </CardContent>
        </Card>
      )}

      {/* İstatistikler */}
      <Card>
        <CardHeader>
          <Typography variant="h6">ZPD İstatistikleri</Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" fontWeight="bold" color="primary.main">
                  {(zpdRange.group_individual_balance * 100).toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Grup/Birey Dengesi
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" fontWeight="bold" color="success.main">
                  {(zpdRange.maarif_alignment.overall_alignment * 100).toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Maarif Uyumu
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" fontWeight="bold" color="secondary.main">
                  {(zpdRange.cultural_context.social_harmony * 100).toFixed(0)}%
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Sosyal Uyum
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h5" fontWeight="bold" color="warning.main">
                  {recommendation ? 1 : 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Aktif Öneri
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};
export default ZPDMaarifDashboard;