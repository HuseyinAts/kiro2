/**
 * Gelişmiş Sınav Sonuçları Bileşeni
 * IRT, Morfoloji, ZPD ve Hibrit Öğrenme Stili analizleri dahil
 */
import {
  ExpandMore,
  TrendingUp,
  TrendingDown,
  Assessment,
  CheckCircle,
  Cancel,
  RemoveCircle,
  Star,
  Warning,
  Download,
  Share,
  Refresh,
} from '@mui/icons-material';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Alert,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import { advancedReportsService } from '../../services/advancedReportsService';
import { examService } from '../../services/examService';
import { SinavSonucu, KonuPerformansi, performanceToSinavSonucu } from '../../types';

interface ExamResultsProps {
  sinavId: string
  onRetake?: () => void
}

export const ExamResults: React.FC<ExamResultsProps> = ({ sinavId, onRetake }) => {
  const [sonuc, setSonuc] = useState<SinavSonucu | null>(null);
  const [_gelismisRapor, setGelismisRapor] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Bileşen mount edildiğinde sonuçları yükle
   */
  useEffect(() => {
    loadResults();
  }, [sinavId]);

  /**
   * Sınav sonuçlarını ve gelişmiş analizi yükle
   */
  const loadResults = async () => {
    try {
      setLoading(true);
      setError(null);

      // Paralel olarak temel sonuç ve gelişmiş raporu yükle
      const [sonucData, gelismisRaporData] = await Promise.allSettled([
        examService.getExamResult(sinavId),
        advancedReportsService.getAdvancedExamReport(sinavId),
      ]);

      if (sonucData.status === 'fulfilled') {
        // Convert PerformanceResponse to SinavSonucu
        const convertedSonuc = performanceToSinavSonucu(sonucData.value, sinavId);
        setSonuc(convertedSonuc);
      } else {
        throw new Error('Temel sınav sonucu yüklenemedi');
      }

      if (gelismisRaporData.status === 'fulfilled') {
        setGelismisRapor(gelismisRaporData.value);
      } else {
        console.warn('Gelişmiş rapor yüklenemedi:', gelismisRaporData.reason);
      }

    } catch (err: any) {
      setError(err.message || 'Sonuçlar yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Başarı durumunu belirle
   */
  const getSuccessLevel = (puan: number): { level: string; color: string; icon: React.ReactNode } => {
    if (puan >= 80) {
      return { level: 'Mükemmel', color: 'success', icon: <Star /> };
    } else if (puan >= 70) {
      return { level: 'İyi', color: 'info', icon: <TrendingUp /> };
    } else if (puan >= 60) {
      return { level: 'Orta', color: 'warning', icon: <Assessment /> };
    } else {
      return { level: 'Geliştirilmeli', color: 'error', icon: <TrendingDown /> };
    }
  };

  /**
   * Pasta grafik verileri hazırla
   */
  const preparePieChartData = (sonuc: SinavSonucu) => {
    return [
      { name: 'Doğru', value: sonuc.dogru_sayisi, color: '#10b981' },
      { name: 'Yanlış', value: sonuc.yanlis_sayisi, color: '#ef4444' },
      { name: 'Boş', value: sonuc.bos_sayisi, color: '#6b7280' },
    ];
  };

  /**
   * Konu performans grafik verileri hazırla
   */
  const prepareTopicPerformanceData = (konuPerformanslari: KonuPerformansi[]) => {
    return konuPerformanslari.map(konu => ({
      konu: konu.konu.length > 15 ? konu.konu.substring(0, 15) + '...' : konu.konu,
      basari: konu.basari_yuzdesi,
      dogru: konu.dogru_sayisi,
      yanlis: konu.yanlis_sayisi,
      bos: konu.bos_sayisi,
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Sonuçlar yükleniyor...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button onClick={loadResults} startIcon={<Refresh />} sx={{ mt: 1 }}>
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  if (!sonuc) {
    return (
      <Alert severity="info" sx={{ m: 2 }}>
        Sonuç bulunamadı
      </Alert>
    );
  }

  const successInfo = getSuccessLevel(sonuc.ham_puan);
  const pieData = preparePieChartData(sonuc);
  const topicData = prepareTopicPerformanceData(sonuc.konu_performanslari);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Paper elevation={3} sx={{ p: 3, mb: 3, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
          {successInfo.icon}
          <Typography variant="h4" sx={{ ml: 1 }}>
            Sınav Sonuçları
          </Typography>
        </Box>

        <Typography variant="h6" color="textSecondary" gutterBottom>
          {examService.getExamTypeDescription(sonuc.sinav_tipi as unknown as import('../../services/examService').ExamType)}
        </Typography>

        <Chip
          label={successInfo.level}
          color={successInfo.color as any}
          size="medium"
          sx={{ fontSize: '1rem', px: 2 }}
        />
      </Paper>

      {/* Temel İstatistikler */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Assessment sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {sonuc.ham_puan.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Ham Puan
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {sonuc.dogru_sayisi}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Doğru Cevap
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Cancel sx={{ fontSize: 40, color: 'error.main', mb: 1 }} />
              <Typography variant="h4" color="error.main">
                {sonuc.yanlis_sayisi}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Yanlış Cevap
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <RemoveCircle sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" color="warning.main">
                {sonuc.bos_sayisi}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Boş Cevap
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Net Hesaplama */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          📊 Net Hesaplama
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" color="primary" sx={{ mr: 2 }}>
            {sonuc.net_sayisi.toFixed(2)}
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Net (Doğru - Yanlış/4)
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={(sonuc.net_sayisi / sonuc.toplam_soru) * 100}
          sx={{ height: 10, borderRadius: 5 }}
          color={sonuc.ham_puan >= 60 ? 'success' : 'error'}
        />
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          {sonuc.dogru_sayisi} doğru - ({sonuc.yanlis_sayisi}/4) yanlış = {sonuc.net_sayisi.toFixed(2)} net
        </Typography>
      </Paper>

      {/* Grafikler */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Cevap Dağılımı Pasta Grafik */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              📈 Cevap Dağılımı
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Konu Performansı Bar Grafik */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              📚 Konu Bazlı Performans
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topicData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="konu" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="basari" fill="#10b981" name="Başarı %" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Detaylı Konu Analizi */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">📋 Detaylı Konu Analizi</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Konu</TableCell>
                  <TableCell align="center">Toplam Soru</TableCell>
                  <TableCell align="center">Doğru</TableCell>
                  <TableCell align="center">Yanlış</TableCell>
                  <TableCell align="center">Boş</TableCell>
                  <TableCell align="center">Başarı %</TableCell>
                  <TableCell align="center">Durum</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sonuc.konu_performanslari.map((konu, index) => (
                  <TableRow key={index}>
                    <TableCell>{konu.konu}</TableCell>
                    <TableCell align="center">{konu.toplam_soru}</TableCell>
                    <TableCell align="center" sx={{ color: 'success.main' }}>
                      {konu.dogru_sayisi}
                    </TableCell>
                    <TableCell align="center" sx={{ color: 'error.main' }}>
                      {konu.yanlis_sayisi}
                    </TableCell>
                    <TableCell align="center" sx={{ color: 'warning.main' }}>
                      {konu.bos_sayisi}
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <LinearProgress
                            variant="determinate"
                            value={konu.basari_yuzdesi}
                            color={konu.basari_yuzdesi >= 70 ? 'success' : konu.basari_yuzdesi >= 50 ? 'warning' : 'error'}
                          />
                        </Box>
                        <Typography variant="body2" sx={{ minWidth: 35 }}>
                          {konu.basari_yuzdesi.toFixed(0)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      {konu.basari_yuzdesi >= 70 ? (
                        <Chip label="İyi" color="success" size="small" />
                      ) : konu.basari_yuzdesi >= 50 ? (
                        <Chip label="Orta" color="warning" size="small" />
                      ) : (
                        <Chip label="Zayıf" color="error" size="small" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Güçlü ve Zayıf Alanlar */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
              💪 Güçlü Alanlarınız
            </Typography>
            {sonuc.guclu_konular.length > 0 ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {sonuc.guclu_konular.map((konu, index) => (
                  <Chip
                    key={index}
                    label={konu}
                    color="success"
                    variant="outlined"
                    icon={<CheckCircle />}
                  />
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="textSecondary">
                Henüz güçlü alan tespit edilemedi. Daha fazla çalışarak güçlü alanlarınızı geliştirebilirsiniz.
              </Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'error.main' }}>
              📚 Geliştirilmesi Gereken Alanlar
            </Typography>
            {sonuc.zayif_konular.length > 0 ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {sonuc.zayif_konular.map((konu, index) => (
                  <Chip
                    key={index}
                    label={konu}
                    color="error"
                    variant="outlined"
                    icon={<Warning />}
                  />
                ))}
              </Box>
            ) : (
              <Typography variant="body2" color="textSecondary">
                Tebrikler! Tüm konularda yeterli performans gösterdiniz.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Çalışma Önerileri */}
      {sonuc.calisma_onerileri.length > 0 && (
        <Accordion sx={{ mb: 3 }}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Typography variant="h6">💡 Kişiselleştirilmiş Çalışma Önerileri</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {sonuc.calisma_onerileri.map((oneri, index) => (
              <Alert key={index} severity="info" sx={{ mb: 2 }}>
                {oneri}
              </Alert>
            ))}
          </AccordionDetails>
        </Accordion>
      )}

      {/* Karşılaştırma Verileri */}
      {(sonuc.sinif_ortalamasi || sonuc.okul_ortalamasi || sonuc.ulusal_ortalama) && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            📊 Karşılaştırmalı Analiz
          </Typography>
          <Grid container spacing={3}>
            {sonuc.sinif_ortalamasi && (
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="textSecondary">
                    Sınıf Ortalaması
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {sonuc.sinif_ortalamasi.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color={sonuc.ham_puan > sonuc.sinif_ortalamasi ? 'success.main' : 'error.main'}>
                    {sonuc.ham_puan > sonuc.sinif_ortalamasi ? 'Ortalamanın üstünde' : 'Ortalamanın altında'}
                  </Typography>
                </Box>
              </Grid>
            )}
            {sonuc.okul_ortalamasi && (
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="textSecondary">
                    Okul Ortalaması
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {sonuc.okul_ortalamasi.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color={sonuc.ham_puan > sonuc.okul_ortalamasi ? 'success.main' : 'error.main'}>
                    {sonuc.ham_puan > sonuc.okul_ortalamasi ? 'Ortalamanın üstünde' : 'Ortalamanın altında'}
                  </Typography>
                </Box>
              </Grid>
            )}
            {sonuc.ulusal_ortalama && (
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="textSecondary">
                    Ulusal Ortalama
                  </Typography>
                  <Typography variant="h5" color="primary">
                    {sonuc.ulusal_ortalama.toFixed(1)}
                  </Typography>
                  <Typography variant="body2" color={sonuc.ham_puan > sonuc.ulusal_ortalama ? 'success.main' : 'error.main'}>
                    {sonuc.ham_puan > sonuc.ulusal_ortalama ? 'Ortalamanın üstünde' : 'Ortalamanın altında'}
                  </Typography>
                </Box>
              </Grid>
            )}
          </Grid>
        </Paper>
      )}

      {/* Eylem Butonları */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          startIcon={<Download />}
          onClick={() => {
            // PDF indirme işlevi
          }}
        >
          Raporu İndir
        </Button>
        <Button
          variant="outlined"
          startIcon={<Share />}
          onClick={() => {
            // Paylaşma işlevi
          }}
        >
          Paylaş
        </Button>
        {onRetake && (
          <Button
            variant="contained"
            color="secondary"
            startIcon={<Refresh />}
            onClick={onRetake}
          >
            Tekrar Çöz
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default ExamResults;