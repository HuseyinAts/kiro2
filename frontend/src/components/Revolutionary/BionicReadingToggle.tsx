/**
 * 🚀 Türkçe Bionic Reading Toggle Bileşeni (DEVRİMSEL)
 * Disleksi için Türkçe'ye özel okuma desteği
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  TextField,
  Box,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Slider,
  Grid,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  Psychology as BrainIcon,
  Settings as SettingsIcon,
  Info as InfoIcon,
  Speed as SpeedIcon,
  Accessibility as AccessibilityIcon,
  FormatBold as FormatBoldIcon,
  School as SchoolIcon
} from '@mui/icons-material';
import { BionicReadingResult, ApiResponse } from '../../types/revolutionary';
import { useBionicReading } from '../../hooks/useBionicReading';
import DyslexiaSupport from './DyslexiaSupport';

interface BionicReadingToggleProps {
  initialText?: string;
  onTextChange?: (bionicText: string, isEnabled: boolean) => void;
  studentId?: string;
}

const BionicReadingToggle: React.FC<BionicReadingToggleProps> = ({ 
  initialText = '',
  onTextChange,
  studentId 
}) => {
  const [inputText, setInputText] = useState(initialText);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const [autoApply, setAutoApply] = useState(true);
  const [dyslexiaEnabled, setDyslexiaEnabled] = useState(false);
  const [dyslexiaSettings, setDyslexiaSettings] = useState({
    fontScale: 1.2,
    lineSpacing: 1.5,
    letterSpacing: 0.1,
    contrastLevel: 0.8,
    readingSpeed: 0.7
  });

  // Bionic Reading hook'unu kullan
  const {
    enabled,
    loading,
    error,
    result: bionicResult,
    settings,
    toggleEnabled,
    updateSettings,
    applyBionicReading,
    applyBionicReadingDebounced,
    clearError
  } = useBionicReading({
    studentId,
    autoApply,
    debounceMs: 500,
    onError: (errorMessage) => {
      console.error('Bionic Reading hatası:', errorMessage);
    },
    onSuccess: (result) => {
      onTextChange?.(result.bionic_metin, enabled);
    }
  });

  // Toggle değişikliği
  const handleToggle = async (checked: boolean) => {
    await toggleEnabled(checked);
    
    if (checked && inputText.trim()) {
      applyBionicReading(inputText);
    }
  };

  // Ayarlar değişikliği
  const handleSettingsChange = async (newSettings: typeof settings) => {
    await updateSettings(newSettings);
    
    if (enabled && inputText.trim()) {
      applyBionicReading(inputText);
    }
  };

  // Metin değişikliği
  const handleTextChange = (text: string) => {
    setInputText(text);
    
    if (enabled && autoApply && text.trim()) {
      applyBionicReadingDebounced(text);
    }
  };





  // Bionic metni render et
  const renderBionicText = (text: string) => {
    // **bold** formatını HTML'e çevir
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  // Örnek metinler
  const sampleTexts = [
    "Çocuklar bahçede oynuyorlar ve çok eğleniyorlar.",
    "Matematik dersinde geometri konularını öğreniyoruz.",
    "Türkiye'nin en büyük şehri İstanbul'dur ve çok kalabalıktır.",
    "Öğrenciler sınavlarına hazırlanırken kitaplarını dikkatle okuyorlar."
  ];

  useEffect(() => {
    if (initialText !== inputText) {
      setInputText(initialText);
      if (enabled && initialText.trim()) {
        applyBionicReading(initialText);
      }
    }
  }, [initialText, enabled, applyBionicReading]);

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <VisibilityIcon sx={{ fontSize: 40, color: 'secondary.main' }} />
          <Typography variant="h4" component="h1" fontWeight="bold">
            Türkçe Bionic Reading
          </Typography>
          <Tooltip title="Disleksi için Türkçe'ye özel okuma desteği">
            <IconButton onClick={() => setInfoOpen(true)}>
              <InfoIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Disleksi için Türkçe'ye özel okuma desteği
        </Typography>
        <Chip 
          label="🚀 DEVRİMSEL ÖZELLİK" 
          color="secondary" 
          variant="outlined"
          sx={{ fontWeight: 'bold' }}
        />
      </Box>

      {/* Kontroller */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={enabled}
                    onChange={(e) => handleToggle(e.target.checked)}
                    color="secondary"
                  />
                }
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BrainIcon />
                    <Typography variant="body1" fontWeight="medium">
                      Bionic Reading {enabled ? 'Açık' : 'Kapalı'}
                    </Typography>
                  </Box>
                }
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={autoApply}
                    onChange={(e) => {
                      setAutoApply(e.target.checked);
                    }}
                    disabled={!enabled}
                  />
                }
                label="Otomatik Uygula"
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Button
                startIcon={<SettingsIcon />}
                onClick={() => setSettingsOpen(true)}
                variant="outlined"
                disabled={!enabled}
              >
                Ayarlar
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Disleksi Desteği */}
      <DyslexiaSupport
        enabled={dyslexiaEnabled}
        onEnabledChange={setDyslexiaEnabled}
        settings={dyslexiaSettings}
        onSettingsChange={setDyslexiaSettings}
      />

      {/* Metin Girişi */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SchoolIcon />
                Orijinal Metin
              </Typography>
            </CardHeader>
            <CardContent>
              <TextField
                multiline
                rows={8}
                placeholder="Bionic Reading uygulanacak metni buraya yazın..."
                value={inputText}
                onChange={(e) => handleTextChange(e.target.value)}
                variant="outlined"
                fullWidth
                sx={{ mb: 2 }}
              />
              
              <Typography variant="subtitle2" gutterBottom>
                Örnek Metinler:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {sampleTexts.map((sample, index) => (
                  <Chip
                    key={index}
                    label={`Örnek ${index + 1}`}
                    onClick={() => {
                      setInputText(sample);
                      if (enabled) {
                        applyBionicReading(sample);
                      }
                    }}
                    variant="outlined"
                    size="small"
                    sx={{ cursor: 'pointer' }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <FormatBoldIcon />
                Bionic Reading Sonucu
                {loading && <CircularProgress size={20} />}
              </Typography>
            </CardHeader>
            <CardContent>
              {error && (
                <Alert 
                  severity="warning" 
                  sx={{ mb: 2 }}
                  onClose={() => clearError()}
                >
                  {error}
                </Alert>
              )}

              {enabled && bionicResult ? (
                <Box>
                  <Paper 
                    sx={{ 
                      p: 2, 
                      bgcolor: 'grey.50', 
                      minHeight: 200,
                      fontSize: dyslexiaEnabled ? `${1.1 * dyslexiaSettings.fontScale}rem` : '1.1rem',
                      lineHeight: dyslexiaEnabled ? dyslexiaSettings.lineSpacing : 1.6,
                      letterSpacing: dyslexiaEnabled ? `${dyslexiaSettings.letterSpacing}em` : 'normal',
                      filter: dyslexiaEnabled ? `contrast(${dyslexiaSettings.contrastLevel})` : 'none',
                      '& strong': {
                        fontWeight: dyslexiaEnabled ? 'bold' : 'bold',
                        opacity: dyslexiaEnabled ? dyslexiaSettings.readingSpeed : 1
                      }
                    }}
                  >
                    <div 
                      dangerouslySetInnerHTML={{ 
                        __html: renderBionicText(bionicResult.bionic_metin) 
                      }}
                    />
                  </Paper>

                  {/* Performans ve Analiz Detayları */}
                  <Box sx={{ mt: 2 }}>
                    <Grid container spacing={2}>
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'success.50' }}>
                          <Typography variant="caption" color="text.secondary">
                            İşlem Süresi
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {bionicResult.processing_time}ms
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'info.50' }}>
                          <Typography variant="caption" color="text.secondary">
                            Kelime Sayısı
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {inputText.split(/\s+/).length}
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'warning.50' }}>
                          <Typography variant="caption" color="text.secondary">
                            Karmaşıklık
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {bionicResult.complexity_score.toFixed(1)}/10
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6} md={3}>
                        <Paper sx={{ p: 1, textAlign: 'center', bgcolor: 'secondary.50' }}>
                          <Typography variant="caption" color="text.secondary">
                            Okunabilirlik
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {bionicResult.readability_score.toFixed(1)}/10
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>
                  </Box>

                  {/* Analiz Detayları */}
                  {bionicResult.kok_ek_analizi.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Kök-Ek Analizi:
                      </Typography>
                      <Box sx={{ maxHeight: 150, overflowY: 'auto' }}>
                        {bionicResult.kok_ek_analizi.slice(0, 5).map((analiz, index) => (
                          <Paper key={index} sx={{ p: 1, mb: 1, bgcolor: 'primary.50' }}>
                            <Typography variant="caption" color="text.secondary">
                              <strong>{analiz.kelime}</strong> → 
                              Kök: <em>{analiz.kok}</em>, 
                              Ekler: [{analiz.ekler.join(', ')}]
                            </Typography>
                          </Paper>
                        ))}
                      </Box>
                    </Box>
                  )}
                </Box>
              ) : (
                <Box sx={{ 
                  textAlign: 'center', 
                  py: 4, 
                  color: 'text.secondary',
                  minHeight: 200,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}>
                  <AccessibilityIcon sx={{ fontSize: 48, opacity: 0.5, mb: 1 }} />
                  <Typography>
                    {enabled ? 'Bionic Reading sonucu burada görünecek' : 'Bionic Reading\'i etkinleştirin'}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Ayarlar Dialog'u */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Bionic Reading Ayarları
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Kök Bold Oranı: {settings.rootBoldRatio}%
            </Typography>
            <Slider
              value={settings.rootBoldRatio}
              onChange={(_, value) => setSettings(prev => ({ ...prev, rootBoldRatio: value as number }))}
              min={20}
              max={60}
              step={5}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />

            <Typography variant="subtitle1" gutterBottom>
              Ek Bold Oranı: {settings.suffixBoldRatio}%
            </Typography>
            <Slider
              value={settings.suffixBoldRatio}
              onChange={(_, value) => setSettings(prev => ({ ...prev, suffixBoldRatio: value as number }))}
              min={0}
              max={20}
              step={5}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />

            <Typography variant="subtitle1" gutterBottom>
              Minimum Bold Karakter: {settings.minBoldChars}
            </Typography>
            <Slider
              value={settings.minBoldChars}
              onChange={(_, value) => setSettings(prev => ({ ...prev, minBoldChars: value as number }))}
              min={1}
              max={4}
              step={1}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />

            <Typography variant="subtitle1" gutterBottom>
              Maksimum Bold Karakter: {settings.maxBoldChars}
            </Typography>
            <Slider
              value={settings.maxBoldChars}
              onChange={(_, value) => setSettings(prev => ({ ...prev, maxBoldChars: value as number }))}
              min={3}
              max={8}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>İptal</Button>
          <Button 
            onClick={() => {
              handleSettingsChange(settings);
              setSettingsOpen(false);
            }}
            variant="contained"
          >
            Uygula
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bilgi Dialog'u */}
      <Dialog open={infoOpen} onClose={() => setInfoOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          🚀 Türkçe Bionic Reading Hakkında
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Bionic Reading, kelimelerin ilk harflerini kalınlaştırarak okuma hızını ve 
            anlama yeteneğini artıran bir tekniktir. Bu sistem, Türkçe'nin ek yapısına 
            özel olarak uyarlanmıştır.
          </Typography>
          
          <Typography variant="h6" gutterBottom>
            Türkçe'ye Özel Özellikler:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon><FormatBoldIcon color="primary" /></ListItemIcon>
              <ListItemText 
                primary="Kök-Ek Ayrımı" 
                secondary="Zemberek NLP ile kelimelerin kök ve ekleri ayrılır"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><SpeedIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Kök Odaklı Bold" 
                secondary="Sadece kökün %40'ı kalınlaştırılır, ekler normal kalır"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><AccessibilityIcon color="secondary" /></ListItemIcon>
              <ListItemText 
                primary="Disleksi Desteği" 
                secondary="Okuma zorluğu çeken öğrenciler için özel optimizasyon"
              />
            </ListItem>
          </List>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Örnek:
          </Typography>
          <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
            <Typography variant="body1">
              Normal: "Çocuklar bahçede oynuyorlar"
            </Typography>
            <Typography variant="body1" sx={{ mt: 1 }}>
              Bionic: "<strong>Çoc</strong>uklar <strong>bah</strong>çede <strong>oyn</strong>uyorlar"
            </Typography>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BionicReadingToggle;