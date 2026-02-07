/**
 * System Monitoring Dashboard
 * Comprehensive monitoring for API, Database, and System performance
 */
import {
  Refresh,
  Speed,
  Storage,
  Computer,
  Warning,
  CheckCircle,
  Error as ErrorIcon,
  PlayArrow,
  Stop,
  Analytics,
  BugReport,
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
  Chip,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  services: {
    database?: string;
    redis?: string;
    elasticsearch?: string;
    performance_monitor?: string;
  };
}

interface PerformanceMetrics {
  total_requests?: number;
  avg_response_time?: number;
  min_response_time?: number;
  max_response_time?: number;
  error_rate?: number;
  requests_per_second?: number;
}

interface Bottleneck {
  type: string;
  description: string;
  severity: string;
  metric_value?: number;
  threshold?: number;
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
      id={`monitoring-tabpanel-${index}`}
      aria-labelledby={`monitoring-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export function SystemMonitoringPage() {
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [apiPerformance, setApiPerformance] = useState<PerformanceMetrics | null>(null);
  const [dbPerformance, setDbPerformance] = useState<PerformanceMetrics | null>(null);
  const [systemPerformance, setSystemPerformance] = useState<any>(null);
  const [bottlenecks, setBottlenecks] = useState<Bottleneck[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [monitoringActive, setMonitoringActive] = useState(true);

  useEffect(() => {
    loadMonitoringData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(loadMonitoringData, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadMonitoringData = async () => {
    try {
      setLoading(true);
      setError(null);

      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      // Load all monitoring data in parallel
      const [healthRes, apiPerfRes, dbPerfRes, sysPerfRes, bottlenecksRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/v1/monitoring/health`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/monitoring/performance/api?hours=1`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/monitoring/performance/database?hours=1`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/monitoring/performance/system?hours=1`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
        fetch(`${API_URL}/api/v1/monitoring/bottlenecks`, {
          headers: { 'Authorization': `Bearer ${token}` },
        }),
      ]);

      if (healthRes.status === 'fulfilled' && healthRes.value.ok) {
        const data = await healthRes.value.json();
        setHealth(data.data);
      }

      if (apiPerfRes.status === 'fulfilled' && apiPerfRes.value.ok) {
        const data = await apiPerfRes.value.json();
        setApiPerformance(data.data);
      }

      if (dbPerfRes.status === 'fulfilled' && dbPerfRes.value.ok) {
        const data = await dbPerfRes.value.json();
        setDbPerformance(data.data);
      }

      if (sysPerfRes.status === 'fulfilled' && sysPerfRes.value.ok) {
        const data = await sysPerfRes.value.json();
        setSystemPerformance(data.data);
      }

      if (bottlenecksRes.status === 'fulfilled' && bottlenecksRes.value.ok) {
        const data = await bottlenecksRes.value.json();
        setBottlenecks(data.data?.bottlenecks || []);
      }

    } catch (err: any) {
      console.error('Monitoring data loading error:', err);
      setError(err.message || 'Monitoring verileri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleMonitoring = async (start: boolean) => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');

      const endpoint = start ? 'start' : 'stop';
      const response = await fetch(`${API_URL}/api/v1/monitoring/monitoring/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        setMonitoringActive(start);
        alert(start ? '✅ Monitoring başlatıldı' : '⏸️ Monitoring durduruldu');
      }
    } catch (err: any) {
      console.error('Toggle monitoring error:', err);
      alert('❌ Monitoring durumu değiştirilemedi');
    }
  };

  const getHealthColor = (status?: string) => {
    if (!status) {return 'default';}
    if (status === 'healthy') {return 'success';}
    if (status === 'degraded') {return 'warning';}
    return 'error';
  };

  const getServiceStatus = (service?: string) => {
    if (!service) {return { text: 'Unknown', color: 'default', icon: <ErrorIcon /> };}
    if (service === 'healthy') {return { text: 'Healthy', color: 'success', icon: <CheckCircle /> };}
    if (service.includes('unhealthy')) {return { text: 'Unhealthy', color: 'error', icon: <ErrorIcon /> };}
    return { text: service, color: 'warning', icon: <Warning /> };
  };

  // Color palette available for charts (prefixed to indicate intentionally unused for future use)
  const _CHART_COLORS: readonly string[] = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
  void _CHART_COLORS; // Suppress unused variable warning - reserved for future chart implementation

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Analytics sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              System Monitoring
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Gerçek zamanlı performans izleme ve sistem sağlığı
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            color={monitoringActive ? 'error' : 'success'}
            startIcon={monitoringActive ? <Stop /> : <PlayArrow />}
            onClick={() => handleToggleMonitoring(!monitoringActive)}
          >
            {monitoringActive ? 'Durdur' : 'Başlat'}
          </Button>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
            onClick={loadMonitoringData}
            disabled={loading}
          >
            Yenile
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Health Status */}
      {health && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">System Health</Typography>
            <Chip
              label={health.status?.toUpperCase()}
              color={getHealthColor(health.status) as any}
              size="medium"
            />
          </Box>

          <Grid container spacing={2}>
            {Object.entries(health.services || {}).map(([service, status]) => {
              const statusInfo = getServiceStatus(status);
              return (
                <Grid item xs={12} sm={6} md={3} key={service}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Box sx={{ color: `${statusInfo.color}.main`, mb: 1 }}>
                        {statusInfo.icon}
                      </Box>
                      <Typography variant="body2" fontWeight="bold">
                        {service.replace('_', ' ').toUpperCase()}
                      </Typography>
                      <Chip
                        label={statusInfo.text}
                        color={statusInfo.color as any}
                        size="small"
                        sx={{ mt: 1 }}
                      />
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            Son güncelleme: {health.timestamp || 'Bilinmiyor'} | Version: {health.version || '1.0.0'}
          </Typography>
        </Paper>
      )}

      {/* Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Speed sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {apiPerformance?.avg_response_time?.toFixed(2) || 0}ms
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Ortalama API Yanıt Süresi
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {apiPerformance?.total_requests || 0} toplam istek
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Storage sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {dbPerformance?.avg_response_time?.toFixed(2) || 0}ms
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Ortalama DB Sorgu Süresi
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {dbPerformance?.total_requests || 0} toplam sorgu
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={2}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Computer sx={{ fontSize: 40, color: 'info.main', mb: 1 }} />
              <Typography variant="h4" color="info.main">
                {((apiPerformance?.error_rate || 0) * 100).toFixed(2)}%
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Hata Oranı
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {apiPerformance?.requests_per_second?.toFixed(2) || 0} req/s
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bottlenecks Alert */}
      {bottlenecks.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }} icon={<BugReport />}>
          <Typography variant="h6" gutterBottom>
            {bottlenecks.length} Performans Darboğazı Tespit Edildi
          </Typography>
          {bottlenecks.slice(0, 3).map((bottleneck, index) => (
            <Typography key={index} variant="body2">
              • {bottleneck.description} ({bottleneck.severity})
            </Typography>
          ))}
        </Alert>
      )}

      {/* Tabs */}
      <Paper elevation={2}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="API Performance" />
          <Tab label="Database Performance" />
          <Tab label="System Metrics" />
          <Tab label="Bottlenecks" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            API Performance Metrics (Son 1 Saat)
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Toplam İstek</Typography>
                <Typography variant="h5">{apiPerformance?.total_requests || 0}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Ortalama Süre</Typography>
                <Typography variant="h5">{apiPerformance?.avg_response_time?.toFixed(2) || 0}ms</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Min Süre</Typography>
                <Typography variant="h5">{apiPerformance?.min_response_time?.toFixed(2) || 0}ms</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Max Süre</Typography>
                <Typography variant="h5">{apiPerformance?.max_response_time?.toFixed(2) || 0}ms</Typography>
              </Paper>
            </Grid>
          </Grid>

          <Typography variant="body2" color="text.secondary">
            Request/Second: {apiPerformance?.requests_per_second?.toFixed(2) || 0} |
            Error Rate: {((apiPerformance?.error_rate || 0) * 100).toFixed(2)}%
          </Typography>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Database Performance Metrics (Son 1 Saat)
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Toplam Sorgu</Typography>
                <Typography variant="h5">{dbPerformance?.total_requests || 0}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Ortalama Süre</Typography>
                <Typography variant="h5">{dbPerformance?.avg_response_time?.toFixed(2) || 0}ms</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Min Süre</Typography>
                <Typography variant="h5">{dbPerformance?.min_response_time?.toFixed(2) || 0}ms</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={3}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="caption" color="text.secondary">Max Süre</Typography>
                <Typography variant="h5">{dbPerformance?.max_response_time?.toFixed(2) || 0}ms</Typography>
              </Paper>
            </Grid>
          </Grid>

          <Alert severity="info">
            Database bağlantı havuzu ve sorgu optimizasyonu otomatik olarak yönetilmektedir.
          </Alert>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            System Metrics
          </Typography>

          {systemPerformance ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="body2" color="text.secondary">CPU Kullanımı</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemPerformance.cpu_usage || 0}
                    sx={{ mt: 1, mb: 1 }}
                  />
                  <Typography variant="h6">{systemPerformance.cpu_usage?.toFixed(1) || 0}%</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={4}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="body2" color="text.secondary">Memory Kullanımı</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemPerformance.memory_usage || 0}
                    sx={{ mt: 1, mb: 1 }}
                  />
                  <Typography variant="h6">{systemPerformance.memory_usage?.toFixed(1) || 0}%</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={4}>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="body2" color="text.secondary">Disk Kullanımı</Typography>
                  <LinearProgress
                    variant="determinate"
                    value={systemPerformance.disk_usage || 0}
                    sx={{ mt: 1, mb: 1 }}
                  />
                  <Typography variant="h6">{systemPerformance.disk_usage?.toFixed(1) || 0}%</Typography>
                </Paper>
              </Grid>
            </Grid>
          ) : (
            <Alert severity="info">
              System metrics yükleniyor...
            </Alert>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Performans Darboğazları
          </Typography>

          {bottlenecks.length > 0 ? (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Tip</TableCell>
                    <TableCell>Açıklama</TableCell>
                    <TableCell>Önem Derecesi</TableCell>
                    <TableCell align="right">Değer</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {bottlenecks.map((bottleneck, index) => (
                    <TableRow key={index}>
                      <TableCell>{bottleneck.type}</TableCell>
                      <TableCell>{bottleneck.description}</TableCell>
                      <TableCell>
                        <Chip
                          label={bottleneck.severity}
                          color={
                            bottleneck.severity === 'critical' ? 'error' :
                            bottleneck.severity === 'high' ? 'warning' : 'default'
                          }
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        {bottleneck.metric_value?.toFixed(2) || 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            <Alert severity="success" icon={<CheckCircle />}>
              Hiçbir performans darboğazı tespit edilmedi. Sistem optimal çalışıyor!
            </Alert>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
}

export default SystemMonitoringPage;
