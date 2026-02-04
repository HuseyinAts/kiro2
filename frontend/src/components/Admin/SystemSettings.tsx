import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Typography,
  Grid,
  Box,
  Alert
} from '@mui/material';

interface SystemSettings {
  general: {
    siteName: string;
    siteUrl: string;
    adminEmail: string;
    maintenanceMode: boolean;
    registrationEnabled: boolean;
  };
}

const SystemSettings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings>({
    general: {
      siteName: 'Türkiye Üniversite Sınavları Hazırlık Platformu',
      siteUrl: 'https://localhost:3000',
      adminEmail: 'admin@example.com',
      maintenanceMode: false,
      registrationEnabled: true,
    },
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Settings save failed:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (section: keyof SystemSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Sistem Ayarları
        </Typography>
        <Button 
          variant="contained"
          onClick={handleSave} 
          disabled={saving}
        >
          {saving ? 'Kaydediliyor...' : saved ? 'Kaydedildi' : 'Kaydet'}
        </Button>
      </Box>

      <Card>
        <CardHeader>
          <Typography variant="h6">
            Genel Ayarlar
          </Typography>
        </CardHeader>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Site Adı"
                value={settings.general.siteName}
                onChange={(e) => updateSetting('general', 'siteName', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Site URL"
                value={settings.general.siteUrl}
                onChange={(e) => updateSetting('general', 'siteUrl', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Admin E-posta"
                type="email"
                value={settings.general.adminEmail}
                onChange={(e) => updateSetting('general', 'adminEmail', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.general.maintenanceMode}
                    onChange={(e) => updateSetting('general', 'maintenanceMode', e.target.checked)}
                  />
                }
                label="Bakım Modu"
              />
              <Typography variant="body2" color="text.secondary">
                Site bakım modunda olduğunda kullanıcılar erişemez
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.general.registrationEnabled}
                    onChange={(e) => updateSetting('general', 'registrationEnabled', e.target.checked)}
                  />
                }
                label="Kayıt Olma"
              />
              <Typography variant="body2" color="text.secondary">
                Yeni kullanıcıların kayıt olmasına izin ver
              </Typography>
            </Grid>
            {settings.general.maintenanceMode && (
              <Grid item xs={12}>
                <Alert severity="warning">
                  Bakım modu aktif. Site kullanıcılara kapalı.
                </Alert>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemSettings;