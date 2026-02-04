/**
 * Disleksi Desteği Bileşeni
 * Bionic Reading ile entegre disleksi desteği ayarları
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Switch,
  FormControlLabel,
  Slider,
  Grid,
  Box,
  Chip,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Accessibility as AccessibilityIcon,
  Visibility as VisibilityIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
  School as SchoolIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface DyslexiaSupportProps {
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
  settings: {
    fontScale: number;
    lineSpacing: number;
    letterSpacing: number;
    contrastLevel: number;
    readingSpeed: number;
  };
  onSettingsChange: (settings: any) => void;
}

const DyslexiaSupport: React.FC<DyslexiaSupportProps> = ({
  enabled,
  onEnabledChange,
  settings,
  onSettingsChange
}) => {
  const [infoOpen, setInfoOpen] = useState(false);

  const handleSettingChange = (key: string, value: number) => {
    onSettingsChange({
      ...settings,
      [key]: value
    });
  };

  const resetToDefaults = () => {
    onSettingsChange({
      fontScale: 1.2,
      lineSpacing: 1.5,
      letterSpacing: 0.1,
      contrastLevel: 0.8,
      readingSpeed: 0.7
    });
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardHeader>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccessibilityIcon color="secondary" />
          <Typography variant="h6">
            Disleksi Desteği
          </Typography>
          <Chip 
            label="ERİŞİLEBİLİRLİK" 
            color="secondary" 
            size="small"
            variant="outlined"
          />
          <Button
            size="small"
            startIcon={<InfoIcon />}
            onClick={() => setInfoOpen(true)}
          >
            Bilgi
          </Button>
        </Box>
      </CardHeader>
      
      <CardContent>
        <Grid container spacing={3}>
          {/* Ana Switch */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={enabled}
                  onChange={(e) => onEnabledChange(e.target.checked)}
                  color="secondary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PsychologyIcon />
                  <Typography variant="body1" fontWeight="medium">
                    Disleksi Desteği {enabled ? 'Açık' : 'Kapalı'}
                  </Typography>
                </Box>
              }
            />
          </Grid>

          {enabled && (
            <>
              <Grid item xs={12}>
                <Alert severity="info" sx={{ mb: 2 }}>
                  Bu ayarlar Bionic Reading ile birlikte çalışarak okuma deneyiminizi iyileştirir.
                </Alert>
              </Grid>

              {/* Font Boyutu */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Font Boyutu: {settings.fontScale}x
                </Typography>
                <Slider
                  value={settings.fontScale}
                  onChange={(_, value) => handleSettingChange('fontScale', value as number)}
                  min={1.0}
                  max={2.0}
                  step={0.1}
                  marks={[
                    { value: 1.0, label: 'Normal' },
                    { value: 1.5, label: 'Orta' },
                    { value: 2.0, label: 'Büyük' }
                  ]}
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Satır Aralığı */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Satır Aralığı: {settings.lineSpacing}x
                </Typography>
                <Slider
                  value={settings.lineSpacing}
                  onChange={(_, value) => handleSettingChange('lineSpacing', value as number)}
                  min={1.0}
                  max={2.5}
                  step={0.1}
                  marks={[
                    { value: 1.0, label: 'Sık' },
                    { value: 1.5, label: 'Normal' },
                    { value: 2.5, label: 'Geniş' }
                  ]}
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Harf Aralığı */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Harf Aralığı: {settings.letterSpacing}em
                </Typography>
                <Slider
                  value={settings.letterSpacing}
                  onChange={(_, value) => handleSettingChange('letterSpacing', value as number)}
                  min={0}
                  max={0.3}
                  step={0.05}
                  marks={[
                    { value: 0, label: 'Normal' },
                    { value: 0.15, label: 'Orta' },
                    { value: 0.3, label: 'Geniş' }
                  ]}
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Kontrast Seviyesi */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Kontrast Seviyesi: {Math.round(settings.contrastLevel * 100)}%
                </Typography>
                <Slider
                  value={settings.contrastLevel}
                  onChange={(_, value) => handleSettingChange('contrastLevel', value as number)}
                  min={0.5}
                  max={1.0}
                  step={0.1}
                  marks={[
                    { value: 0.5, label: 'Düşük' },
                    { value: 0.8, label: 'Normal' },
                    { value: 1.0, label: 'Yüksek' }
                  ]}
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Okuma Hızı Ayarı */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Okuma Hızı Optimizasyonu: {Math.round(settings.readingSpeed * 100)}%
                </Typography>
                <Slider
                  value={settings.readingSpeed}
                  onChange={(_, value) => handleSettingChange('readingSpeed', value as number)}
                  min={0.3}
                  max={1.0}
                  step={0.1}
                  marks={[
                    { value: 0.3, label: 'Yavaş' },
                    { value: 0.7, label: 'Orta' },
                    { value: 1.0, label: 'Hızlı' }
                  ]}
                  valueLabelDisplay="auto"
                />
                <Typography variant="caption" color="text.secondary">
                  Düşük değerler daha fazla bold karakter, yüksek değerler daha az bold karakter anlamına gelir.
                </Typography>
              </Grid>

              {/* Reset Butonu */}
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  onClick={resetToDefaults}
                  sx={{ mt: 2 }}
                >
                  Varsayılan Ayarlara Dön
                </Button>
              </Grid>
            </>
          )}
        </Grid>
      </CardContent>

      {/* Bilgi Dialog'u */}
      <Dialog open={infoOpen} onClose={() => setInfoOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccessibilityIcon color="secondary" />
            Disleksi Desteği Hakkında
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Disleksi desteği, okuma zorluğu yaşayan öğrenciler için özel olarak tasarlanmış 
            erişilebilirlik özelliklerini içerir. Bu özellikler Bionic Reading teknolojisi 
            ile birlikte çalışarak okuma deneyimini önemli ölçüde iyileştirir.
          </Typography>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
            Özellikler:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon><VisibilityIcon color="primary" /></ListItemIcon>
              <ListItemText 
                primary="Bionic Reading Entegrasyonu" 
                secondary="Türkçe'ye özel kök-ek ayrımı ile optimize edilmiş okuma desteği"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><SchoolIcon color="success" /></ListItemIcon>
              <ListItemText 
                primary="Kişiselleştirilebilir Ayarlar" 
                secondary="Font boyutu, satır aralığı ve kontrast ayarları"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><SpeedIcon color="warning" /></ListItemIcon>
              <ListItemText 
                primary="Okuma Hızı Optimizasyonu" 
                secondary="Bireysel okuma hızına göre bold karakter oranı ayarlama"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon><PsychologyIcon color="secondary" /></ListItemIcon>
              <ListItemText 
                primary="Bilimsel Temelli" 
                secondary="Disleksi araştırmalarına dayalı tasarım prensipleri"
              />
            </ListItem>
          </List>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Kullanım İpuçları:
          </Typography>
          <Typography variant="body2" component="div">
            <ul>
              <li>Başlangıçta orta seviye ayarları deneyin</li>
              <li>Okuma hızınıza göre bold oranını ayarlayın</li>
              <li>Göz yorgunluğu hissederseniz kontrast seviyesini düşürün</li>
              <li>Uzun metinler için satır aralığını artırın</li>
            </ul>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInfoOpen(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default DyslexiaSupport;