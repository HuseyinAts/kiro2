/**
 * ZPD + Maarif Visualization Page
 * Revolutionary: Zone of Proximal Development + Turkish Ministry of Education Maarif Model
 *
 * Features:
 * - ZPD calculation with Turkish cultural context
 * - MEB Maarif values integration (National, Universal, Core values)
 * - Cultural factors visualization (8 dimensions)
 * - Optimal difficulty level calculation
 * - Interactive radar charts and progress tracking
 * - Profile management for cultural and Maarif values
 */
import {
  Psychology,
  Insights,
  People,
  Star,
  Assessment,
  Refresh,
  Save,
  CheckCircle,
  Flag,
  Public,
  Favorite,
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
  Slider,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
} from '@mui/material';
import { useState, useEffect } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

interface CulturalProfile {
  ogrenci_id: string;
  grup_calismasi_tercihi: number;
  ogretmene_saygi_seviyesi: number;
  aile_katilim_derecesi: number;
  akran_rekabet_egilimi: number;
  otorite_kabul_seviyesi: number;
  toplumsal_onay_ihtiyaci: number;
  basari_odaklilik: number;
  kolektif_kimlik_gucu: number;
  bolge?: string;
  sosyoekonomik_durum?: string;
  okul_turu?: string;
}

interface MaarifProfile {
  ogrenci_id: string;
  // Milli Değerler
  vatan_sevgisi: number;
  millet_bilinci: number;
  aile_birligi: number;
  bayrak_sevgisi: number;
  istiklal_ruhu: number;
  // Evrensel Değerler
  adalet: number;
  dostluk: number;
  durustluk: number;
  ozgurluk: number;
  esitlik: number;
  baris: number;
  // Kök Değerler
  sabir: number;
  saygi: number;
  sevgi: number;
  sorumluluk: number;
  duyarlilik: number;
  hosgoru: number;
}

interface ZPDResult {
  alt_sinir: number;
  ust_sinir: number;
  optimal_zorluk: number;
  mevcut_seviye: number;
  zpd_genisligi: number;
  seviye: string;
  oneriler: string[];
  kulturel_faktör_etkileri: any;
  maarif_uyum_skoru: number;
}

export function ZPDMaarifVisualizationPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Student Selection
  const [studentId, setStudentId] = useState('demo_student_001');
  const [subject, setSubject] = useState('matematik');
  const [currentLevel, setCurrentLevel] = useState(5.0);

  // Profiles
  const [culturalProfile, setCulturalProfile] = useState<CulturalProfile | null>(null);
  const [maarifProfile, setMaarifProfile] = useState<MaarifProfile | null>(null);

  // ZPD Result
  const [zpdResult, setZpdResult] = useState<ZPDResult | null>(null);

  // Dialogs
  const [showCulturalDialog, setShowCulturalDialog] = useState(false);
  const [showMaarifDialog, setShowMaarifDialog] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';
  const token = localStorage.getItem('token');

  useEffect(() => {
    loadProfiles();
  }, [studentId]);

  const loadProfiles = async () => {
    try {
      setLoading(true);

      const [culturalRes, maarifRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/v1/zpd-maarif/profil/kulturel/${studentId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/zpd-maarif/profil/maarif/${studentId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
      ]);

      if (culturalRes.status === 'fulfilled' && culturalRes.value.ok) {
        const data = await culturalRes.value.json();
        if (data.success) {setCulturalProfile(data.data);}
      }

      if (maarifRes.status === 'fulfilled' && maarifRes.value.ok) {
        const data = await maarifRes.value.json();
        if (data.success) {setMaarifProfile(data.data);}
      }
    } catch (err) {
      console.error('Failed to load profiles:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCalculateZPD = async () => {
    if (!culturalProfile || !maarifProfile) {
      setError('Lütfen önce profilleri yükleyin');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_URL}/api/v1/zpd-maarif/hesapla`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ogrenci_id: studentId,
          konu: subject,
          mevcut_seviye: currentLevel,
          kulturel_profil: culturalProfile,
          maarif_profili: maarifProfile,
        }),
      });

      if (!response.ok) {
        throw new Error('ZPD hesaplama başarısız oldu');
      }

      const data = await response.json();
      if (data.success && data.data) {
        setZpdResult(data.data);
      }
    } catch (err: any) {
      console.error('ZPD calculation error:', err);
      setError(err.message || 'Hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCulturalProfile = async () => {
    if (!culturalProfile) {return;}

    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/v1/zpd-maarif/profil/kulturel/${studentId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(culturalProfile),
      });

      if (response.ok) {
        alert('✅ Kültürel profil güncellendi!');
        setShowCulturalDialog(false);
        loadProfiles();
      }
    } catch (err) {
      console.error('Update cultural profile error:', err);
      alert('❌ Profil güncellenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMaarifProfile = async () => {
    if (!maarifProfile) {return;}

    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/v1/zpd-maarif/profil/maarif/${studentId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(maarifProfile),
      });

      if (response.ok) {
        alert('✅ Maarif profili güncellendi!');
        setShowMaarifDialog(false);
        loadProfiles();
      }
    } catch (err) {
      console.error('Update maarif profile error:', err);
      alert('❌ Profil güncellenemedi');
    } finally {
      setLoading(false);
    }
  };

  const prepareCulturalRadarData = () => {
    if (!culturalProfile) {return [];}

    return [
      { factor: 'Grup Çalışması', value: culturalProfile.grup_calismasi_tercihi * 100 },
      { factor: 'Öğretmene Saygı', value: culturalProfile.ogretmene_saygi_seviyesi * 100 },
      { factor: 'Aile Katılımı', value: culturalProfile.aile_katilim_derecesi * 100 },
      { factor: 'Akran Rekabeti', value: culturalProfile.akran_rekabet_egilimi * 100 },
      { factor: 'Otorite Kabulü', value: culturalProfile.otorite_kabul_seviyesi * 100 },
      { factor: 'Toplumsal Onay', value: culturalProfile.toplumsal_onay_ihtiyaci * 100 },
      { factor: 'Başarı Odaklılık', value: culturalProfile.basari_odaklilik * 100 },
      { factor: 'Kolektif Kimlik', value: culturalProfile.kolektif_kimlik_gucu * 100 },
    ];
  };

  const prepareMaarifBarData = () => {
    if (!maarifProfile) {return [];}

    const { ogrenci_id: _ogrenci_id, ...values } = maarifProfile;
    return Object.entries(values).map(([key, value]) => ({
      name: key.replace(/_/g, ' ').toUpperCase(),
      value: (value as number) * 100,
    }));
  };

  const prepareZPDVisualizationData = () => {
    if (!zpdResult) {return [];}

    return [
      { level: 0, zone: 'Çok Kolay', inZPD: false },
      { level: zpdResult.mevcut_seviye - 1, zone: 'Kolay', inZPD: false },
      { level: zpdResult.mevcut_seviye, zone: 'Mevcut', inZPD: false, isCurrent: true },
      { level: zpdResult.alt_sinir, zone: 'ZPD Alt', inZPD: true },
      { level: zpdResult.optimal_zorluk, zone: 'OPTIMAL', inZPD: true, isOptimal: true },
      { level: zpdResult.ust_sinir, zone: 'ZPD Üst', inZPD: true },
      { level: 10, zone: 'Çok Zor', inZPD: false },
    ];
  };

  const getZPDLevelColor = (level: string): string => {
    switch (level) {
      case 'optimal': return 'success.main';
      case 'kolay': return 'info.main';
      case 'zor': return 'warning.main';
      case 'cok_zor': return 'error.main';
      default: return 'text.secondary';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Psychology sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              ZPD + MEB Maarif Modeli
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Türk Eğitim Kültürüne Uyarlanmış Gelişim Alanı Analizi
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadProfiles}
          >
            Yenile
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Info Banner */}
      <Alert severity="info" icon={<Star />} sx={{ mb: 3 }}>
        <Typography variant="body2" fontWeight="bold">
          🌟 Devrimsel Özellik: Vygotsky&apos;nin ZPD Teorisi + MEB Maarif Modeli
        </Typography>
        <Typography variant="caption">
          Türk öğrenci psikolojisine özel optimal zorluk seviyesi hesaplama sistemi.
          Kültürel faktörler ve Maarif değerleri ile desteklenir.
        </Typography>
      </Alert>

      {/* Control Panel */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🎯 Analiz Parametreleri
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Öğrenci ID"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Ders</InputLabel>
              <Select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                <MenuItem value="matematik">Matematik</MenuItem>
                <MenuItem value="fizik">Fizik</MenuItem>
                <MenuItem value="kimya">Kimya</MenuItem>
                <MenuItem value="biyoloji">Biyoloji</MenuItem>
                <MenuItem value="turkce">Türkçe</MenuItem>
                <MenuItem value="tarih">Tarih</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <Typography variant="body2" gutterBottom>
              Mevcut Seviye: {currentLevel.toFixed(1)} / 10
            </Typography>
            <Slider
              value={currentLevel}
              onChange={(_, value) => setCurrentLevel(value as number)}
              min={0}
              max={10}
              step={0.5}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>

          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                fullWidth
                startIcon={loading ? <CircularProgress size={20} /> : <Assessment />}
                onClick={handleCalculateZPD}
                disabled={loading || !culturalProfile || !maarifProfile}
                size="large"
              >
                {loading ? 'Hesaplanıyor...' : 'ZPD Hesapla'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<People />}
                onClick={() => setShowCulturalDialog(true)}
              >
                Kültürel Profil
              </Button>
              <Button
                variant="outlined"
                startIcon={<Flag />}
                onClick={() => setShowMaarifDialog(true)}
              >
                Maarif Profili
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabs */}
      <Paper elevation={2} sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab icon={<Assessment />} label="ZPD Analizi" />
          <Tab icon={<People />} label="Kültürel Faktörler" />
          <Tab icon={<Flag />} label="Maarif Değerleri" />
          <Tab icon={<Insights />} label="Öneriler" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {/* ZPD Analysis Tab */}
          {activeTab === 0 && (
            <Box>
              {zpdResult ? (
                <>
                  {/* Quick Stats */}
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} md={3}>
                      <Card elevation={1}>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Typography variant="h4" color="primary">
                            {zpdResult.optimal_zorluk.toFixed(1)}
                          </Typography>
                          <Typography variant="caption">Optimal Zorluk</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Card elevation={1}>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Typography variant="h4" color="secondary">
                            {zpdResult.zpd_genisligi.toFixed(1)}
                          </Typography>
                          <Typography variant="caption">ZPD Genişliği</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Card elevation={1}>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Typography variant="h4" color={getZPDLevelColor(zpdResult.seviye)}>
                            {zpdResult.seviye.replace(/_/g, ' ').toUpperCase()}
                          </Typography>
                          <Typography variant="caption">Seviye</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <Card elevation={1}>
                        <CardContent sx={{ textAlign: 'center' }}>
                          <Typography variant="h4" color="success.main">
                            {(zpdResult.maarif_uyum_skoru * 100).toFixed(0)}%
                          </Typography>
                          <Typography variant="caption">Maarif Uyumu</Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>

                  {/* ZPD Zone Visualization */}
                  <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      📊 ZPD Aralığı Görselleştirmesi
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={prepareZPDVisualizationData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="zone" />
                        <YAxis domain={[0, 10]} />
                        <RechartsTooltip />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="level"
                          stroke="#8884d8"
                          fill="#8884d8"
                          fillOpacity={0.6}
                        />
                      </AreaChart>
                    </ResponsiveContainer>

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" gutterBottom>
                        <strong>Alt Sınır:</strong> {zpdResult.alt_sinir.toFixed(1)} |
                        <strong> Üst Sınır:</strong> {zpdResult.ust_sinir.toFixed(1)} |
                        <strong> Optimal:</strong> {zpdResult.optimal_zorluk.toFixed(1)}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(zpdResult.optimal_zorluk / 10) * 100}
                        sx={{ height: 10, borderRadius: 5 }}
                      />
                    </Box>
                  </Paper>
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Assessment sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    ZPD analizi için &quot;ZPD Hesapla&quot; butonuna tıklayın
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Cultural Factors Tab */}
          {activeTab === 1 && (
            <Box>
              {culturalProfile ? (
                <>
                  <Typography variant="h6" gutterBottom>
                    🌍 Türk Öğrenci Kültürel Faktörleri (8 Boyut)
                  </Typography>

                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={prepareCulturalRadarData()}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="factor" />
                      <PolarRadiusAxis domain={[0, 100]} />
                      <Radar
                        name="Kültürel Profil"
                        dataKey="value"
                        stroke="#8884d8"
                        fill="#8884d8"
                        fillOpacity={0.6}
                      />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>

                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    {culturalProfile.bolge && (
                      <Grid item xs={12} md={4}>
                        <Chip label={`Bölge: ${culturalProfile.bolge}`} sx={{ width: '100%' }} />
                      </Grid>
                    )}
                    {culturalProfile.sosyoekonomik_durum && (
                      <Grid item xs={12} md={4}>
                        <Chip label={`Sosyoekonomik: ${culturalProfile.sosyoekonomik_durum}`} sx={{ width: '100%' }} />
                      </Grid>
                    )}
                    {culturalProfile.okul_turu && (
                      <Grid item xs={12} md={4}>
                        <Chip label={`Okul: ${culturalProfile.okul_turu}`} sx={{ width: '100%' }} />
                      </Grid>
                    )}
                  </Grid>
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <People sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Kültürel profil yükleniyor...
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Maarif Values Tab */}
          {activeTab === 2 && (
            <Box>
              {maarifProfile ? (
                <>
                  <Typography variant="h6" gutterBottom>
                    🇹🇷 MEB Maarif Değerleri (Milli, Evrensel, Kök)
                  </Typography>

                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={prepareMaarifBarData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" angle={-45} textAnchor="end" height={120} />
                      <YAxis domain={[0, 100]} />
                      <RechartsTooltip />
                      <Legend />
                      <Bar dataKey="value" fill="#82ca9d" />
                    </BarChart>
                  </ResponsiveContainer>

                  <Grid container spacing={2} sx={{ mt: 3 }}>
                    <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Flag sx={{ mr: 1, color: 'error.main' }} />
                            <Typography variant="subtitle1" fontWeight="bold">
                              Milli Değerler
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Vatan Sevgisi, Millet Bilinci, Aile Birliği, Bayrak Sevgisi, İstiklal Ruhu
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Public sx={{ mr: 1, color: 'primary.main' }} />
                            <Typography variant="subtitle1" fontWeight="bold">
                              Evrensel Değerler
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Adalet, Dostluk, Dürüstlük, Özgürlük, Eşitlik, Barış
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <Card>
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Favorite sx={{ mr: 1, color: 'secondary.main' }} />
                            <Typography variant="subtitle1" fontWeight="bold">
                              Kök Değerler
                            </Typography>
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            Sabır, Saygı, Sevgi, Sorumluluk, Duyarlılık, Hoşgörü
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Flag sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Maarif profili yükleniyor...
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Recommendations Tab */}
          {activeTab === 3 && (
            <Box>
              {zpdResult && zpdResult.oneriler ? (
                <>
                  <Typography variant="h6" gutterBottom>
                    💡 Kişiselleştirilmiş Öneriler
                  </Typography>

                  <Grid container spacing={2}>
                    {zpdResult.oneriler.map((oneri, idx) => (
                      <Grid item xs={12} key={idx}>
                        <Card elevation={1}>
                          <CardContent sx={{ display: 'flex', alignItems: 'center' }}>
                            <CheckCircle color="success" sx={{ mr: 2 }} />
                            <Typography variant="body1">{oneri}</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </>
              ) : (
                <Box sx={{ textAlign: 'center', py: 8 }}>
                  <Insights sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Önerileri görmek için ZPD analizi yapın
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </Box>
      </Paper>

      {/* Cultural Profile Dialog */}
      <Dialog
        open={showCulturalDialog}
        onClose={() => setShowCulturalDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>🌍 Kültürel Faktörler Profili</DialogTitle>
        <DialogContent>
          {culturalProfile && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                {Object.entries(culturalProfile)
                  .filter(([key]) => !['ogrenci_id', 'bolge', 'sosyoekonomik_durum', 'okul_turu'].includes(key))
                  .map(([key, value]) => (
                    <Grid item xs={12} key={key}>
                      <Typography variant="body2" gutterBottom>
                        {key.replace(/_/g, ' ').toUpperCase()}: {((value as number) * 100).toFixed(0)}%
                      </Typography>
                      <Slider
                        value={(value as number)}
                        onChange={(_, newValue) => setCulturalProfile({
                          ...culturalProfile,
                          [key]: newValue,
                        })}
                        min={0}
                        max={1}
                        step={0.1}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                      />
                    </Grid>
                  ))}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCulturalDialog(false)}>İptal</Button>
          <Button
            onClick={handleUpdateCulturalProfile}
            variant="contained"
            startIcon={<Save />}
          >
            Kaydet
          </Button>
        </DialogActions>
      </Dialog>

      {/* Maarif Profile Dialog */}
      <Dialog
        open={showMaarifDialog}
        onClose={() => setShowMaarifDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>🇹🇷 MEB Maarif Değerleri Profili</DialogTitle>
        <DialogContent>
          {maarifProfile && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                {Object.entries(maarifProfile)
                  .filter(([key]) => key !== 'ogrenci_id')
                  .map(([key, value]) => (
                    <Grid item xs={12} md={6} key={key}>
                      <Typography variant="body2" gutterBottom>
                        {key.replace(/_/g, ' ').toUpperCase()}: {((value as number) * 100).toFixed(0)}%
                      </Typography>
                      <Slider
                        value={(value as number)}
                        onChange={(_, newValue) => setMaarifProfile({
                          ...maarifProfile,
                          [key]: newValue,
                        })}
                        min={0}
                        max={1}
                        step={0.1}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(v) => `${(v * 100).toFixed(0)}%`}
                      />
                    </Grid>
                  ))}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowMaarifDialog(false)}>İptal</Button>
          <Button
            onClick={handleUpdateMaarifProfile}
            variant="contained"
            startIcon={<Save />}
          >
            Kaydet
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default ZPDMaarifVisualizationPage;
