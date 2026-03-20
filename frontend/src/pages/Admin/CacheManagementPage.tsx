/**
 * Cache Management Dashboard
 * Admin page for monitoring and managing Redis cache
 */
import {
  Refresh,
  Delete,
  Storage,
  Speed,
  TrendingUp,
  Warning,
  CheckCircle,
  Delete as DeleteIcon,
  Info,
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
  Alert,
  CircularProgress,
  TextField,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

interface CacheStats {
  main_cache?: {
    total_keys?: number;
    memory_usage?: string;
    hit_rate?: number;
  };
  exam_cache?: {
    total_keys?: number;
    memory_usage?: string;
  };
  session_cache?: {
    active_sessions?: number;
    total_sessions?: number;
  };
  invalidation?: {
    invalidated_keys?: number;
    last_invalidation?: string | null;
  };
  timestamp?: string;
}

interface CacheHealth {
  status?: string;
  redis_connected?: boolean;
  latency_ms?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`cache-tabpanel-${index}`}
      aria-labelledby={`cache-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function CacheManagementPage() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [health, setHealth] = useState<CacheHealth | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [invalidatePattern, setInvalidatePattern] = useState('');
  const [showInvalidateDialog, setShowInvalidateDialog] = useState(false);

  useEffect(() => {
    loadCacheData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadCacheData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadCacheData = async () => {
    try {
      setLoading(true);
      setError(null);

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      // Load stats and health in parallel
      const [statsRes, healthRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/v1/cache/stats`, {
          credentials: 'include',
        }),
        fetch(`${API_URL}/api/v1/cache/health`, {
          credentials: 'include',
        }),
      ]);

      if (statsRes.status === 'fulfilled' && statsRes.value.ok) {
        const statsData = await statsRes.value.json();
        setStats(statsData.data || {});
      }

      if (healthRes.status === 'fulfilled' && healthRes.value.ok) {
        const healthData = await healthRes.value.json();
        setHealth(healthData.data || {});
      }

    } catch (err: any) {
      console.error('Cache data loading error:', err);
      setError(err.message || 'Cache verileri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleInvalidatePattern = async () => {
    if (!invalidatePattern) {return;}

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/v1/cache/invalidate/pattern`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ pattern: invalidatePattern }),
      });

      if (response.ok) {
        alert('✅ Cache başarıyla invalidate edildi');
        setShowInvalidateDialog(false);
        setInvalidatePattern('');
        loadCacheData();
      } else {
        throw new Error('Invalidation failed');
      }
    } catch (err: any) {
      console.error('Invalidation error:', err);
      alert('❌ Cache invalidation başarısız oldu');
    }
  };

  const handleClearExamCache = async () => {
    if (!confirm('Tüm sınav cache verilerini silmek istediğinizden emin misiniz?')) {return;}

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/v1/cache/exam`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        alert('✅ Sınav cache başarıyla temizlendi');
        loadCacheData();
      }
    } catch (err: any) {
      console.error('Clear exam cache error:', err);
      alert('❌ Sınav cache temizleme başarısız oldu');
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Storage sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Cache Yönetimi
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Redis cache izleme ve yönetim paneli
            </Typography>
          </Box>
        </Box>

        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
          onClick={loadCacheData}
          disabled={loading}
        >
          Yenile
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Health Status */}
      {health && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {health.status === 'healthy' ? (
                <CheckCircle sx={{ color: 'success.main', fontSize: 32, mr: 2 }} />
              ) : (
                <Warning sx={{ color: 'warning.main', fontSize: 32, mr: 2 }} />
              )}
              <Box>
                <Typography variant="h6">
                  Cache Durumu: {health.status === 'healthy' ? 'Sağlıklı' : 'Uyarı'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Redis: {health.redis_connected ? 'Bağlı' : 'Bağlı Değil'} |
                  Latency: {health.latency_ms || 0}ms
                </Typography>
              </Box>
            </Box>

            <Chip
              label={health.redis_connected ? 'Connected' : 'Disconnected'}
              color={health.redis_connected ? 'success' : 'error'}
            />
          </Box>
        </Paper>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Storage sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {stats?.main_cache?.total_keys || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Toplam Cache Keys
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {stats?.main_cache?.memory_usage || '0MB'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Speed sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {Math.round((stats?.main_cache?.hit_rate || 0) * 100)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Hit Rate
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Cache performansı
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <TrendingUp sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" color="info.main">
                {stats?.session_cache?.active_sessions || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Aktif Oturumlar
              </Typography>
              <Typography variant="caption" color="textSecondary">
                / {stats?.session_cache?.total_sessions || 0} toplam
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <DeleteIcon sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
              <Typography variant="h4" color="warning.main">
                {stats?.invalidation?.invalidated_keys || 0}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Invalidated Keys
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Son 24 saat
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper elevation={2}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Genel Bakış" />
          <Tab label="Cache Yönetimi" />
          <Tab label="İstatistikler" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Alert severity="info" icon={<Info />} sx={{ mb: 2 }}>
            Cache sistemi otomatik olarak yönetilmektedir. Manuel müdahale sadece gerekli durumlarda yapılmalıdır.
          </Alert>

          <Typography variant="body1" paragraph>
            Son güncelleme: {stats?.timestamp || 'Bilinmiyor'}
          </Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper elevation={1} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Pattern ile Invalidate Et
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Belirli bir pattern&apos;e uyan tüm cache key&apos;lerini invalidate edin
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setShowInvalidateDialog(true)}
                  fullWidth
                >
                  Pattern Invalidation
                </Button>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper elevation={1} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Sınav Cache Temizle
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Tüm sınav cache verilerini temizle (dikkatli kullanın)
                </Typography>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<Delete />}
                  onClick={handleClearExamCache}
                  fullWidth
                >
                  Sınav Cache Sil
                </Button>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Detaylı İstatistikler
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Metrik</TableCell>
                  <TableCell align="right">Değer</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Main Cache Keys</TableCell>
                  <TableCell align="right">{stats?.main_cache?.total_keys || 0}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Memory Usage</TableCell>
                  <TableCell align="right">{stats?.main_cache?.memory_usage || '0MB'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Hit Rate</TableCell>
                  <TableCell align="right">{Math.round((stats?.main_cache?.hit_rate || 0) * 100)}%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Exam Cache Keys</TableCell>
                  <TableCell align="right">{stats?.exam_cache?.total_keys || 0}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Active Sessions</TableCell>
                  <TableCell align="right">{stats?.session_cache?.active_sessions || 0}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Paper>

      {/* Invalidate Dialog */}
      <Dialog open={showInvalidateDialog} onClose={() => setShowInvalidateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Pattern ile Invalidate Et</DialogTitle>
        <DialogContent>
          <TextField
            label="Cache Pattern"
            placeholder="user:*"
            fullWidth
            value={invalidatePattern}
            onChange={(e) => setInvalidatePattern(e.target.value)}
            sx={{ mt: 2 }}
            helperText="Örnek: user:*, exam:*, session:*"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowInvalidateDialog(false)}>İptal</Button>
          <Button onClick={handleInvalidatePattern} variant="contained" disabled={!invalidatePattern}>
            Invalidate Et
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default CacheManagementPage;
