/**
 * Sınav Geçmişi Bileşeni
 * Kullanıcının tüm sınavlarını listeler ve analiz sağlar
 */
import {
  Visibility,
  Assessment,
  TrendingUp,
  School,
  Timer,
  CheckCircle,
  Search,
  FilterList,
} from '@mui/icons-material';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

import { examService, SinavTipi, SinavDurumu, ExamStatus, ExamType, ExamSessionResponse } from '../../services/examService';
import { dateUtils } from '@/utils/dateUtils';

interface ExamHistoryProps {
  onViewResult?: (sinavId: string) => void
}

export const ExamHistory: React.FC<ExamHistoryProps> = ({ onViewResult }) => {
  const navigate = useNavigate();

  const [sinavlar, setSinavlar] = useState<ExamSessionResponse[]>([]);
  const [filteredSinavlar, setFilteredSinavlar] = useState<ExamSessionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Filtreleme state'leri
  const [filterType, setFilterType] = useState<ExamType | 'ALL'>('ALL');
  const [filterStatus, setFilterStatus] = useState<ExamStatus | 'ALL'>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: '',
    end: '',
  });

  /**
   * Bileşen mount edildiğinde sınavları yükle
   */
  useEffect(() => {
    loadExams();
  }, []);

  /**
   * Filtreler değiştiğinde sınavları filtrele
   */
  useEffect(() => {
    applyFilters();
  }, [sinavlar, filterType, filterStatus, searchTerm, dateRange]);

  /**
   * Sınavları yükle
   */
  const loadExams = async () => {
    try {
      setLoading(true);
      setError(null);
      const sinavlarData = await examService.getMyExams();
      setSinavlar(sinavlarData);
    } catch (err: any) {
      setError(err.message || 'Sınavlar yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Filtreleri uygula
   */
  const applyFilters = () => {
    let filtered = [...sinavlar];

    // Sınav türü filtresi
    if (filterType !== 'ALL') {
      filtered = filtered.filter(sinav => sinav.exam_type === filterType);
    }

    // Durum filtresi
    if (filterStatus !== 'ALL') {
      filtered = filtered.filter(sinav => sinav.status === filterStatus);
    }

    // Arama terimi filtresi
    if (searchTerm) {
      filtered = filtered.filter(sinav =>
        sinav.exam_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sinav.session_id.toLowerCase().includes(searchTerm.toLowerCase()),
      );
    }

    // Tarih aralığı filtresi
    if (dateRange.start) {
      filtered = filtered.filter(sinav =>
        new Date(sinav.started_at || new Date()) >= new Date(dateRange.start),
      );
    }
    if (dateRange.end) {
      filtered = filtered.filter(sinav =>
        new Date(sinav.started_at || new Date()) <= new Date(dateRange.end),
      );
    }

    // Tarihe göre sırala (en yeni önce)
    filtered.sort((a, b) =>
      new Date(b.started_at || new Date()).getTime() - new Date(a.started_at || new Date()).getTime(),
    );

    setFilteredSinavlar(filtered);
    setPage(0); // Sayfa numarasını sıfırla
  };

  /**
   * Sınav durumu rengini getir
   */
  const getStatusColor = (durum: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (durum) {
      case ExamStatus.COMPLETED:
        return 'success';
      case ExamStatus.IN_PROGRESS:
        return 'warning';
      case ExamStatus.NOT_STARTED:
        return 'info';
      case ExamStatus.ABANDONED:
        return 'error';
      default:
        return 'default';
    }
  };

  /**
   * Sınav türü rengini getir
   */
  const getExamTypeColor = (tip: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (tip) {
      case ExamType.TYT:
        return 'primary';
      case ExamType.AYT:
        return 'secondary';
      case ExamType.YDT:
        return 'success';
      default:
        return 'default';
    }
  };

  /**
   * Süreyi formatla
   */
  const formatDuration = (dakika: number): string => {
    const saat = Math.floor(dakika / 60);
    const kalanDakika = dakika % 60;
    return saat > 0 ? `${saat}s ${kalanDakika}dk` : `${kalanDakika}dk`;
  };

  /**
   * Tarihi formatla
   */
  const formatDate = (dateString: string): string => {
    try {
      return dateUtils.format(dateString, 'DD MMM YYYY HH:mm');
    } catch {
      return dateString;
    }
  };

  /**
   * İstatistikleri hesapla
   */
  const calculateStats = () => {
    const tamamlananSinavlar = sinavlar.filter(s => s.status === ExamStatus.COMPLETED);
    const toplamSinav = sinavlar.length;
    const tamamlananSayi = tamamlananSinavlar.length;
    const devamEdenSayi = sinavlar.filter(s => s.status === ExamStatus.IN_PROGRESS).length;

    // Sınav türü dağılımı
    const tipDagilimi = sinavlar.reduce((acc, sinav) => {
      acc[sinav.exam_type] = (acc[sinav.exam_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      toplamSinav,
      tamamlananSayi,
      devamEdenSayi,
      tamamlanmaOrani: toplamSinav > 0 ? (tamamlananSayi / toplamSinav) * 100 : 0,
      tipDagilimi,
    };
  };

  /**
   * Performans trend verilerini hazırla
   */
  const preparePerformanceTrendData = () => {
    const tamamlananSinavlar = sinavlar
      .filter(s => s.status === ExamStatus.COMPLETED)
      .sort((a, b) => new Date(a.started_at || new Date()).getTime() - new Date(b.started_at || new Date()).getTime())
      .slice(-10); // Son 10 sınav

    return tamamlananSinavlar.map((sinav, index) => ({
      sinav: `Sınav ${index + 1}`,
      tarih: dateUtils.format(sinav.started_at || new Date().toISOString(), 'DD/MM'),
      tip: sinav.exam_type,
      // Not: Gerçek performans verileri için sınav sonuçları gerekli
      // Şimdilik mock veri kullanıyoruz
      puan: Math.random() * 100,
    }));
  };

  const stats = calculateStats();
  const trendData = preparePerformanceTrendData();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Sınav geçmişi yükleniyor...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Hata</Typography>
        <Typography>{error}</Typography>
        <Button onClick={loadExams} sx={{ mt: 1 }}>
          Tekrar Dene
        </Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📚 Sınav Geçmişim
      </Typography>

      {/* İstatistik Kartları */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Assessment sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {stats.toplamSinav}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Toplam Sınav
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <CheckCircle sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {stats.tamamlananSayi}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Tamamlanan
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Timer sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" color="warning.main">
                {stats.devamEdenSayi}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Devam Eden
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" color="info.main">
                %{stats.tamamlanmaOrani.toFixed(0)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Tamamlanma Oranı
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performans Trend Grafiği */}
      {trendData.length > 0 && (
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            📈 Performans Trendi
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tarih" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="puan"
                stroke="#10b981"
                strokeWidth={2}
                name="Puan"
              />
            </LineChart>
          </ResponsiveContainer>
        </Paper>
      )}

      {/* Filtreler */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterList />
          Filtreler
        </Typography>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Sınav Türü</InputLabel>
              <Select
                value={filterType}
                label="Sınav Türü"
                onChange={(e) => setFilterType(e.target.value as SinavTipi | 'ALL')}
              >
                <MenuItem value="ALL">Tümü</MenuItem>
                <MenuItem value={SinavTipi.TYT}>TYT</MenuItem>
                <MenuItem value={SinavTipi.AYT}>AYT</MenuItem>
                <MenuItem value={SinavTipi.YDT}>YDT</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Durum</InputLabel>
              <Select
                value={filterStatus}
                label="Durum"
                onChange={(e) => setFilterStatus(e.target.value as SinavDurumu | 'ALL')}
              >
                <MenuItem value="ALL">Tümü</MenuItem>
                <MenuItem value={ExamStatus.COMPLETED}>Tamamlandı</MenuItem>
                <MenuItem value={ExamStatus.IN_PROGRESS}>Devam Ediyor</MenuItem>
                <MenuItem value={ExamStatus.NOT_STARTED}>Hazır</MenuItem>
                <MenuItem value={ExamStatus.ABANDONED}>İptal Edildi</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Ara"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              onClick={() => {
                setFilterType('ALL');
                setFilterStatus('ALL');
                setSearchTerm('');
                setDateRange({ start: '', end: '' });
              }}
            >
              Filtreleri Temizle
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Sınav Listesi */}
      <Paper elevation={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Sınav Türü</TableCell>
                <TableCell>Tarih</TableCell>
                <TableCell align="center">Süre</TableCell>
                <TableCell align="center">Soru Sayısı</TableCell>
                <TableCell align="center">Durum</TableCell>
                <TableCell align="center">İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSinavlar
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((sinav) => (
                  <TableRow key={sinav.session_id} hover>
                    <TableCell>
                      <Chip
                        label={sinav.exam_type}
                        color={getExamTypeColor(sinav.exam_type)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(sinav.started_at || new Date().toISOString())}
                      </Typography>
                      {sinav.started_at && (
                        <Typography variant="caption" color="textSecondary">
                          Başlangıç: {formatDate(sinav.started_at)}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      {formatDuration(sinav.duration_minutes)}
                    </TableCell>
                    <TableCell align="center">
                      {sinav.total_questions}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={sinav.status}
                        color={getStatusColor(sinav.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                        {sinav.status === ExamStatus.COMPLETED && (
                          <Tooltip title="Sonuçları Görüntüle">
                            <IconButton
                              size="small"
                              onClick={() => {
                                if (onViewResult) {
                                  onViewResult(sinav.session_id);
                                } else {
                                  navigate(`/exam/${sinav.session_id}/results`);
                                }
                              }}
                            >
                              <Visibility />
                            </IconButton>
                          </Tooltip>
                        )}
                        {sinav.status === ExamStatus.IN_PROGRESS && (
                          <Tooltip title="Sınava Devam Et">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => navigate(`/exam/${sinav.session_id}`)}
                            >
                              <Assessment />
                            </IconButton>
                          </Tooltip>
                        )}
                        {sinav.status === ExamStatus.NOT_STARTED && (
                          <Tooltip title="Sınavı Başlat">
                            <IconButton
                              size="small"
                              color="success"
                              onClick={() => navigate(`/exam/${sinav.session_id}`)}
                            >
                              <Assessment />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredSinavlar.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          labelRowsPerPage="Sayfa başına satır:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} / ${count !== -1 ? count : `${to}'den fazla`}`
          }
        />
      </Paper>

      {filteredSinavlar.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <School sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="textSecondary">
            {sinavlar.length === 0
              ? 'Henüz hiç sınav çözmediniz'
              : 'Filtrelere uygun sınav bulunamadı'
            }
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            {sinavlar.length === 0
              ? 'İlk sınavınızı çözmek için sınav başlatın'
              : 'Farklı filtreler deneyebilirsiniz'
            }
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/exam/start')}
          >
            Sınav Başlat
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default ExamHistory;