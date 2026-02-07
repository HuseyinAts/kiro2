/**
 * 🚀 Devrimsel Özellik Ayarları Paneli
 * Öğrenci için tüm devrimsel özelliklerin merkezi ayar paneli
 */

import {
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  Schedule as ScheduleIcon,
  Hub as HubIcon,
  AutoFixHigh as AutoFixHighIcon,
  School as SchoolIcon,
  Accessibility as AccessibilityIcon,
  Save as SaveIcon,
  Restore as RestoreIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  Grid,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  IconButton,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { RevolutionaryFeatureSettings } from '../../types';

interface RevolutionarySettingsProps {
  studentId: string;
  onSettingsChange?: (settings: RevolutionaryFeatureSettings) => void;
}

const RevolutionarySettings: React.FC<RevolutionarySettingsProps> = ({
  studentId,
  onSettingsChange,
}) => {
  const [settings, setSettings] = useState<RevolutionaryFeatureSettings>({
    fsrs_enabled: true,
    bionic_reading_enabled: false,
    text_simplification_level: 'semantic',
    multi_agent_coordination: true,
    cultural_adaptations: {
      ramadan_mode: false,
      exam_season_stress: true,
      group_study_preference: true,
    },
    accessibility_features: {
      high_contrast: false,
      large_text: false,
      screen_reader_optimized: false,
    },
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);

  // Ayarları yükle
  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log(`Loading revolutionary settings for student: ${studentId}`);

        // Import revolutionary features service
        const { revolutionaryFeaturesService } = await import('../../services/revolutionaryFeaturesService');

        // Backend API çağrısı - Ayarları yükle
        const loadedSettings = await revolutionaryFeaturesService.getRevolutionarySettings(studentId);

        setSettings(loadedSettings);
        onSettingsChange?.(loadedSettings);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Beklenmeyen hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    if (studentId) {
      loadSettings();
    }
  }, [studentId, onSettingsChange]);

  // Ayarları kaydet
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      console.log(`Saving revolutionary settings for student: ${studentId}`, settings);

      // Import revolutionary features service
      const { revolutionaryFeaturesService } = await import('../../services/revolutionaryFeaturesService');

      // Backend API çağrısı - Ayarları kaydet
      await revolutionaryFeaturesService.updateRevolutionarySettings(studentId, settings);

      setSuccess('Ayarlar başarıyla kaydedildi');
      onSettingsChange?.(settings);

      // Başarı mesajını 3 saniye sonra temizle
      setTimeout(() => setSuccess(null), 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Beklenmeyen hata oluştu');
    } finally {
      setSaving(false);
    }
  };

  // Ayarları sıfırla
  const handleReset = async () => {
    try {
      setSaving(true);
      setError(null);

      console.log(`Resetting revolutionary settings for student: ${studentId}`);

      // Import revolutionary features service
      const { revolutionaryFeaturesService } = await import('../../services/revolutionaryFeaturesService');

      // Backend API çağrısı - Ayarları sıfırla
      const defaultSettings = await revolutionaryFeaturesService.resetRevolutionarySettings(studentId);

      setSettings(defaultSettings);
      setSuccess('Ayarlar varsayılan değerlere sıfırlandı');
      onSettingsChange?.(defaultSettings);
      setResetDialogOpen(false);

      setTimeout(() => setSuccess(null), 3000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Beklenmeyen hata oluştu');
    } finally {
      setSaving(false);
    }
  };

  // Ayar değişikliği
  const handleSettingChange = (path: string, value: any) => {
    setSettings(prev => {
      const newSettings = { ...prev };
      const keys = path.split('.');
      let current: any = newSettings;

      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }

      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
  };

  // Özellik bilgileri
  const featureInfo = {
    fsrs: {
      title: 'FSRS Tekrar Sistemi',
      description: '17 parametreli Türk öğrenci davranışlarına optimize edilmiş spaced repetition sistemi',
      benefits: ['Optimal tekrar zamanlaması', 'Kültürel faktör desteği', 'Anki FSRS 4.5\'i geliştiren algoritma'],
    },
    bionic_reading: {
      title: 'Türkçe Bionic Reading',
      description: 'Disleksi için Türkçe\'ye özel okuma desteği',
      benefits: ['Okuma hızı artışı', 'Kök-ek ayrımı', 'Disleksi desteği'],
    },
    text_simplification: {
      title: '3 Seviyeli Metin Basitleştirme',
      description: 'Dünyada ilk 3 seviyeli Türkçe metin basitleştirme sistemi',
      benefits: ['Kelime seviyesi basitleştirme', 'Cümle yapısı düzenleme', 'Anlam korunumu'],
    },
    multi_agent: {
      title: 'Multi-Agent Koordinasyon',
      description: 'Blackboard Pattern ile gerçek zamanlı agent koordinasyonu',
      benefits: ['Agent sinerji', 'Gerçek zamanlı adaptasyon', 'Koordineli öğrenme desteği'],
    },
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4 }}>
        <CircularProgress size={32} />
        <Typography variant="body1" sx={{ ml: 2, color: 'text.secondary' }}>
          Devrimsel özellik ayarları yükleniyor...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <SettingsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h3" component="h1" fontWeight="bold">
            Devrimsel Özellik Ayarları
          </Typography>
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          7 dünya çapında yenilikçi özelliğin merkezi ayar paneli
        </Typography>
        <Chip
          label="🚀 DEVRİMSEL ÖZELLİKLER"
          color="primary"
          variant="outlined"
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      {/* Bildirimler */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Ana Özellikler */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* FSRS Sistemi */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScheduleIcon />
                FSRS Tekrar Sistemi
                <Tooltip title="Bilgi al">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSelectedFeature('fsrs');
                      setInfoDialogOpen(true);
                    }}
                  >
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Typography>
            </CardHeader>
            <CardContent>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.fsrs_enabled}
                    onChange={(e) => handleSettingChange('fsrs_enabled', e.target.checked)}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">
                      FSRS Etkin
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      17 parametreli Türk öğrenci optimizasyonu
                    </Typography>
                  </Box>
                }
              />

              <Box sx={{ mt: 2, p: 2, bgcolor: 'primary.50', borderRadius: 1 }}>
                <Typography variant="caption" color="primary.main">
                  Anki&apos;nin FSRS 4.5&apos;ini geliştiren sistem
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Bionic Reading */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <VisibilityIcon />
                Türkçe Bionic Reading
                <Tooltip title="Bilgi al">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSelectedFeature('bionic_reading');
                      setInfoDialogOpen(true);
                    }}
                  >
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Typography>
            </CardHeader>
            <CardContent>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.bionic_reading_enabled}
                    onChange={(e) => handleSettingChange('bionic_reading_enabled', e.target.checked)}
                    color="secondary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">
                      Bionic Reading Etkin
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Disleksi için Türkçe&apos;ye özel okuma desteği
                    </Typography>
                  </Box>
                }
              />

              <Box sx={{ mt: 2, p: 2, bgcolor: 'secondary.50', borderRadius: 1 }}>
                <Typography variant="caption" color="secondary.main">
                  Kök-ek ayrımı ile Türkçe&apos;ye özel
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Metin Basitleştirme */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AutoFixHighIcon />
                Metin Basitleştirme
                <Tooltip title="Bilgi al">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSelectedFeature('text_simplification');
                      setInfoDialogOpen(true);
                    }}
                  >
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Typography>
            </CardHeader>
            <CardContent>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Basitleştirme Seviyesi</InputLabel>
                <Select
                  value={settings.text_simplification_level}
                  label="Basitleştirme Seviyesi"
                  onChange={(e) => handleSettingChange('text_simplification_level', e.target.value)}
                >
                  <MenuItem value="lexical">Kelime Seviyesi</MenuItem>
                  <MenuItem value="syntactic">Sözdizimi Seviyesi</MenuItem>
                  <MenuItem value="semantic">Anlam Seviyesi</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ p: 2, bgcolor: 'warning.50', borderRadius: 1 }}>
                <Typography variant="caption" color="warning.main">
                  Dünyada ilk 3 seviyeli Türkçe sistem
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Multi-Agent Koordinasyon */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardHeader>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HubIcon />
                Multi-Agent Koordinasyon
                <Tooltip title="Bilgi al">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSelectedFeature('multi_agent');
                      setInfoDialogOpen(true);
                    }}
                  >
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Typography>
            </CardHeader>
            <CardContent>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.multi_agent_coordination}
                    onChange={(e) => handleSettingChange('multi_agent_coordination', e.target.checked)}
                    color="success"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1" fontWeight="medium">
                      Agent Koordinasyonu Etkin
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Blackboard Pattern ile gerçek zamanlı sinerji
                    </Typography>
                  </Box>
                }
              />

              <Box sx={{ mt: 2, p: 2, bgcolor: 'success.50', borderRadius: 1 }}>
                <Typography variant="caption" color="success.main">
                  Gerçek zamanlı agent koordinasyonu
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Gelişmiş Ayarlar */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SchoolIcon />
            Kültürel Adaptasyonlar
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.cultural_adaptations.ramadan_mode}
                    onChange={(e) => handleSettingChange('cultural_adaptations.ramadan_mode', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">Ramazan Modu</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Ramazan ayında özel ayarlamalar
                    </Typography>
                  </Box>
                }
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.cultural_adaptations.exam_season_stress}
                    onChange={(e) => handleSettingChange('cultural_adaptations.exam_season_stress', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">Sınav Dönemi Stresi</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Sınav döneminde stres faktörü
                    </Typography>
                  </Box>
                }
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.cultural_adaptations.group_study_preference}
                    onChange={(e) => handleSettingChange('cultural_adaptations.group_study_preference', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">Grup Çalışması Tercihi</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Türk öğrenci grup çalışması eğilimi
                    </Typography>
                  </Box>
                }
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Erişilebilirlik Ayarları */}
      <Accordion sx={{ mb: 4 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccessibilityIcon />
            Erişilebilirlik Özellikleri
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.accessibility_features.high_contrast}
                    onChange={(e) => handleSettingChange('accessibility_features.high_contrast', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">Yüksek Kontrast</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Görme zorluğu için kontrast artırma
                    </Typography>
                  </Box>
                }
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.accessibility_features.large_text}
                    onChange={(e) => handleSettingChange('accessibility_features.large_text', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">Büyük Metin</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Metin boyutunu artır
                    </Typography>
                  </Box>
                }
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.accessibility_features.screen_reader_optimized}
                    onChange={(e) => handleSettingChange('accessibility_features.screen_reader_optimized', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2" fontWeight="medium">Ekran Okuyucu Optimizasyonu</Typography>
                    <Typography variant="caption" color="text.secondary">
                      ARIA etiketleri ve ekran okuyucu desteği
                    </Typography>
                  </Box>
                }
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Kaydet/Sıfırla Butonları */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button
          startIcon={<RestoreIcon />}
          onClick={() => setResetDialogOpen(true)}
          color="warning"
          variant="outlined"
        >
          Varsayılana Sıfırla
        </Button>

        <Button
          startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
          onClick={handleSave}
          disabled={saving}
          variant="contained"
          size="medium"
        >
          {saving ? 'Kaydediliyor...' : 'Ayarları Kaydet'}
        </Button>
      </Box>

      {/* Sıfırlama Onay Dialog'u */}
      <Dialog open={resetDialogOpen} onClose={() => setResetDialogOpen(false)}>
        <DialogTitle>
          Ayarları Sıfırla
        </DialogTitle>
        <DialogContent>
          <Typography>
            Tüm devrimsel özellik ayarlarını varsayılan değerlere sıfırlamak istediğinizden emin misiniz?
            Bu işlem geri alınamaz.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialogOpen(false)}>İptal</Button>
          <Button
            onClick={handleReset}
            color="warning"
            variant="contained"
            disabled={saving}
          >
            Sıfırla
          </Button>
        </DialogActions>
      </Dialog>

      {/* Özellik Bilgi Dialog'u */}
      <Dialog open={infoDialogOpen} onClose={() => setInfoDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedFeature && featureInfo[selectedFeature as keyof typeof featureInfo]?.title}
        </DialogTitle>
        <DialogContent>
          {selectedFeature && (
            <Box>
              <Typography variant="body1" paragraph>
                {featureInfo[selectedFeature as keyof typeof featureInfo]?.description}
              </Typography>

              <Typography variant="h6" gutterBottom>
                Faydalar:
              </Typography>
              <List dense>
                {featureInfo[selectedFeature as keyof typeof featureInfo]?.benefits.map((benefit, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={benefit} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoDialogOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RevolutionarySettings;