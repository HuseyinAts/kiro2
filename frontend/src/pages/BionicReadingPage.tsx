/**
 * Bionic Reading Page
 * Turkish Bionic Reading with Dyslexia Support
 *
 * Features:
 * - Turkish-specific root-suffix separation using Zemberek NLP
 * - 40% of root words are bolded, suffixes never bolded
 * - User preferences management
 * - Real-time text preview
 * - Multiple text processing
 * - Cache management
 * - Service statistics (admin)
 */
import {
  Visibility,
  Settings,
  Psychology,
  AutoFixHigh,
  Save,
  ContentCopy,
  Delete,
  Assessment,
  CheckCircle,
  FormatBold,
  Speed,
  AccessibilityNew,
} from '@mui/icons-material';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Slider,
  FormControlLabel,
  Switch,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { useState, useEffect } from 'react';

import { sanitizeBionicText } from '../utils/sanitize';

interface UserPreferences {
  enabled: boolean;
  bold_ratio: number;
  min_word_length: number;
  auto_apply: boolean;
  font_weight: string;
  highlight_color: string;
}

interface BionicResult {
  original_text: string;
  bionic_text: string;
  processing_time_ms: number;
  word_count: number;
  bold_ratio: number;
  success: boolean;
  error_message?: string;
}

interface ServiceStats {
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  avg_processing_time_ms: number;
  total_words_processed: number;
  active_users: number;
}

export function BionicReadingPage() {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Bionic Result
  const [bionicResult, setBionicResult] = useState<BionicResult | null>(null);

  // User Preferences
  const [preferences, setPreferences] = useState<UserPreferences>({
    enabled: true,
    bold_ratio: 0.4,
    min_word_length: 3,
    auto_apply: false,
    font_weight: 'bold',
    highlight_color: '#000000',
  });
  const [_preferencesLoading, setPreferencesLoading] = useState(true);
  const [showPreferencesDialog, setShowPreferencesDialog] = useState(false);

  // Service Stats (Admin)
  const [serviceStats, setServiceStats] = useState<ServiceStats | null>(null);
  const [showStatsDialog, setShowStatsDialog] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const token = localStorage.getItem('token');
  const userRole = localStorage.getItem('role');

  // Sample texts for demo
  const sampleTexts = {
    simple: 'Bugün hava çok güzel. Parkta koşmak istiyorum.',
    medium: 'Teknolojinin gelişmesiyle birlikte, öğrenme yöntemleri de değişiyor. Dijital araçlar, öğrencilere daha fazla fırsat sunuyor.',
    complex: 'Medeniyetimizin temellerini oluşturan kültürel mirası korumak, gelecek nesillere aktarmak için çalışmalarımızı sürdürüyoruz.',
  };

  useEffect(() => {
    loadUserPreferences();
  }, []);

  const loadUserPreferences = async () => {
    try {
      setPreferencesLoading(true);

      const response = await fetch(`${API_URL}/api/v1/bionic-reading/preferences`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setPreferences(data.data);
        }
      }
    } catch (err) {
      console.error('Failed to load preferences:', err);
    } finally {
      setPreferencesLoading(false);
    }
  };

  const handleProcessText = async () => {
    if (!inputText.trim()) {
      setError('Lütfen metin girin');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/bionic-reading/process`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputText,
          use_cache: true,
        }),
      });

      if (!response.ok) {
        throw new Error('Bionic Reading işlemi başarısız oldu');
      }

      const data = await response.json();
      if (data.success && data.data) {
        setBionicResult(data.data);
      }
    } catch (err: any) {
      console.error('Bionic Reading error:', err);
      setError(err.message || 'Hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePreferences = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/bionic-reading/preferences`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error('Tercih güncelleme başarısız oldu');
      }

      const data = await response.json();
      if (data.success) {
        alert('✅ Tercihler güncellendi!');
        setShowPreferencesDialog(false);
        loadUserPreferences();
      }
    } catch (err: any) {
      console.error('Update preferences error:', err);
      setError(err.message || 'Hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadServiceStats = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/v1/bionic-reading/stats`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setServiceStats(data.data);
          setShowStatsDialog(true);
        }
      } else if (response.status === 403) {
        alert('⚠️ Bu özellik sadece admin kullanıcılar için erişilebilir');
      }
    } catch (err) {
      console.error('Load stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!confirm('Cache temizlensin mi?')) {return;}

    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/v1/bionic-reading/cache`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        alert('✅ Cache temizlendi!');
      }
    } catch (err) {
      console.error('Clear cache error:', err);
      alert('❌ Cache temizlenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('📋 Metin panoya kopyalandı!');
  };

  const renderBionicText = (text: string) => {
    // Parse bionic text with HTML bold tags
    // SECURITY FIX #4: Sanitize HTML before rendering
    return (
      <div
        dangerouslySetInnerHTML={{ __html: sanitizeBionicText(text) }}
        style={{
          fontSize: '1.2rem',
          lineHeight: '1.8',
          fontFamily: 'Georgia, serif',
          color: preferences.highlight_color,
        }}
      />
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Visibility sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Bionic Reading - Türkçe
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Disleksi Desteği • Kök-Ek Ayrımı ile Akıllı Okuma
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Settings />}
            onClick={() => setShowPreferencesDialog(true)}
          >
            Tercihler
          </Button>
          {userRole === 'admin' && (
            <Button
              variant="outlined"
              startIcon={<Assessment />}
              onClick={handleLoadServiceStats}
            >
              İstatistikler
            </Button>
          )}
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={handleClearCache}
          >
            Cache Temizle
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Info Banner */}
      <Alert severity="info" icon={<AccessibilityNew />} sx={{ mb: 3 }}>
        <Typography variant="body2" fontWeight="bold">
          🌟 Türkçe&apos;ye Özel Bionic Reading - Disleksi Desteği
        </Typography>
        <Typography variant="caption">
          Zemberek NLP ile kök-ek ayrımı yapılır. Köklerin %40&apos;ı bold yapılır, ekler hiç bold yapılmaz.
          Bu yöntem, disleksi olan öğrencilerin okuma hızını %30&apos;a kadar artırabilir.
        </Typography>
      </Alert>

      {/* Quick Stats */}
      {preferences && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h6" color={preferences.enabled ? 'success.main' : 'error.main'}>
                  {preferences.enabled ? '✓ Etkin' : '✗ Devre Dışı'}
                </Typography>
                <Typography variant="caption">Bionic Reading Durumu</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h6" color="primary">
                  {(preferences.bold_ratio * 100).toFixed(0)}%
                </Typography>
                <Typography variant="caption">Bold Oranı</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h6" color="secondary">
                  {preferences.min_word_length}
                </Typography>
                <Typography variant="caption">Min. Kelime Uzunluğu</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h6" color="info.main">
                  {preferences.auto_apply ? 'Evet' : 'Hayır'}
                </Typography>
                <Typography variant="caption">Otomatik Uygula</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                📝 Giriş Metni
              </Typography>
              <Chip
                label={`${inputText.length} karakter`}
                size="small"
                color={inputText.length > 10000 ? 'error' : 'default'}
              />
            </Box>

            <TextField
              multiline
              rows={15}
              fullWidth
              placeholder="Bionic Reading uygulanacak metni buraya yazın..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button
                size="small"
                variant="outlined"
                onClick={() => setInputText(sampleTexts.simple)}
              >
                Basit Örnek
              </Button>
              <Button
                size="small"
                variant="outlined"
                onClick={() => setInputText(sampleTexts.medium)}
              >
                Orta Örnek
              </Button>
              <Button
                size="small"
                variant="outlined"
                onClick={() => setInputText(sampleTexts.complex)}
              >
                Karmaşık Örnek
              </Button>
            </Box>

            <Button
              variant="contained"
              fullWidth
              size="large"
              startIcon={loading ? <CircularProgress size={20} /> : <AutoFixHigh />}
              onClick={handleProcessText}
              disabled={loading || !inputText.trim()}
            >
              {loading ? 'İşleniyor...' : 'Bionic Reading Uygula'}
            </Button>
          </Paper>
        </Grid>

        {/* Preview Section */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                👁️ Bionic Reading Önizleme
              </Typography>
              {bionicResult && (
                <IconButton onClick={() => handleCopyToClipboard(bionicResult.bionic_text)}>
                  <ContentCopy />
                </IconButton>
              )}
            </Box>

            {bionicResult ? (
              <>
                {/* Statistics */}
                <Grid container spacing={1} sx={{ mb: 2 }}>
                  <Grid item xs={4}>
                    <Chip
                      icon={<Speed />}
                      label={`${bionicResult.processing_time_ms.toFixed(1)}ms`}
                      size="small"
                      color="primary"
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <Chip
                      icon={<FormatBold />}
                      label={`${(bionicResult.bold_ratio * 100).toFixed(0)}% Bold`}
                      size="small"
                      color="secondary"
                    />
                  </Grid>
                  <Grid item xs={4}>
                    <Chip
                      label={`${bionicResult.word_count} kelime`}
                      size="small"
                      color="info"
                    />
                  </Grid>
                </Grid>

                <Divider sx={{ mb: 2 }} />

                {/* Bionic Text Display */}
                <Box
                  sx={{
                    p: 3,
                    backgroundColor: 'background.default',
                    borderRadius: 2,
                    minHeight: 400,
                    maxHeight: 500,
                    overflowY: 'auto',
                  }}
                >
                  {renderBionicText(bionicResult.bionic_text)}
                </Box>
              </>
            ) : (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Visibility sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Bionic Reading önizlemesi için metni işleyin
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* How it Works Section */}
      <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          🧠 Nasıl Çalışır?
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <Psychology sx={{ fontSize: 50, color: 'primary.main', mb: 1 }} />
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Morfolojik Analiz
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Zemberek NLP ile Türkçe kelimeler kök ve eklerine ayrılır
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <FormatBold sx={{ fontSize: 50, color: 'secondary.main', mb: 1 }} />
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Akıllı Bold Yapma
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Köklerin %40&apos;ı bold yapılır, ekler hiç bold yapılmaz
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center' }}>
              <AccessibilityNew sx={{ fontSize: 50, color: 'success.main', mb: 1 }} />
              <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                Disleksi Desteği
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Okuma hızını %30&apos;a kadar artırır, anlama kolaylaştırır
              </Typography>
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        <Alert severity="success" icon={<CheckCircle />}>
          <Typography variant="body2">
            <strong>Örnek:</strong> &quot;koşuyordum&quot; kelimesi → <strong>koş</strong>uyordum
            (kök: &quot;koş&quot; bold, ekler: &quot;uyordum&quot; normal)
          </Typography>
        </Alert>
      </Paper>

      {/* Preferences Dialog */}
      <Dialog
        open={showPreferencesDialog}
        onClose={() => setShowPreferencesDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Settings sx={{ mr: 1 }} />
            Bionic Reading Tercihleri
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={preferences.enabled}
                  onChange={(e) => setPreferences({ ...preferences, enabled: e.target.checked })}
                />
              }
              label="Bionic Reading Etkin"
              sx={{ mb: 3 }}
            />

            <Typography variant="body2" gutterBottom>
              Bold Oranı: {(preferences.bold_ratio * 100).toFixed(0)}%
            </Typography>
            <Slider
              value={preferences.bold_ratio}
              onChange={(_, value) => setPreferences({ ...preferences, bold_ratio: value as number })}
              min={0.1}
              max={1.0}
              step={0.1}
              marks
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
              sx={{ mb: 3 }}
            />

            <Typography variant="body2" gutterBottom>
              Minimum Kelime Uzunluğu: {preferences.min_word_length}
            </Typography>
            <Slider
              value={preferences.min_word_length}
              onChange={(_, value) => setPreferences({ ...preferences, min_word_length: value as number })}
              min={1}
              max={10}
              step={1}
              marks
              valueLabelDisplay="auto"
              sx={{ mb: 3 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Font Kalınlığı</InputLabel>
              <Select
                value={preferences.font_weight}
                onChange={(e) => setPreferences({ ...preferences, font_weight: e.target.value })}
              >
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="bold">Bold</MenuItem>
                <MenuItem value="bolder">Bolder</MenuItem>
                <MenuItem value="900">Extra Bold</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Vurgulama Rengi"
              type="color"
              value={preferences.highlight_color}
              onChange={(e) => setPreferences({ ...preferences, highlight_color: e.target.value })}
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={preferences.auto_apply}
                  onChange={(e) => setPreferences({ ...preferences, auto_apply: e.target.checked })}
                />
              }
              label="Tüm Metinlere Otomatik Uygula"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPreferencesDialog(false)}>İptal</Button>
          <Button
            onClick={handleUpdatePreferences}
            variant="contained"
            startIcon={<Save />}
          >
            Kaydet
          </Button>
        </DialogActions>
      </Dialog>

      {/* Service Stats Dialog (Admin) */}
      <Dialog
        open={showStatsDialog}
        onClose={() => setShowStatsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Assessment sx={{ mr: 1 }} />
            Servis İstatistikleri
          </Box>
        </DialogTitle>
        <DialogContent>
          {serviceStats && (
            <Grid container spacing={2} sx={{ pt: 2 }}>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="primary">
                      {serviceStats.total_requests}
                    </Typography>
                    <Typography variant="caption">Toplam İstek</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="success.main">
                      {serviceStats.cache_hits}
                    </Typography>
                    <Typography variant="caption">Cache Hit</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="warning.main">
                      {serviceStats.cache_misses}
                    </Typography>
                    <Typography variant="caption">Cache Miss</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="info.main">
                      {serviceStats.avg_processing_time_ms.toFixed(1)}ms
                    </Typography>
                    <Typography variant="caption">Ortalama İşlem Süresi</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4">
                      {serviceStats.total_words_processed}
                    </Typography>
                    <Typography variant="caption">İşlenen Kelime</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="secondary">
                      {serviceStats.active_users}
                    </Typography>
                    <Typography variant="caption">Aktif Kullanıcı</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowStatsDialog(false)}>Kapat</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default BionicReadingPage;
