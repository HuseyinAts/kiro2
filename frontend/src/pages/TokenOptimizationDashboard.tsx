/**
 * Token Optimization Dashboard
 * Real-time monitoring of token usage and cost savings
 */

import {
  TrendingDown,
  Savings,
  Assessment,
  Refresh,
  CloudDownload,
  ArrowUpward,
} from '@mui/icons-material';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface TokenStats {
  total_requests: number
  total_original_tokens: number
  total_optimized_tokens: number
  total_tokens_saved: number
  average_savings_percentage: number
  total_cost_saved_usd: number
  provider_breakdown: {
    [provider: string]: {
      requests: number
      original_tokens: number
      optimized_tokens: number
      tokens_saved: number
      cost_saved_usd: number
    }
  }
}

interface MonthlyProjection {
  projected_monthly_requests: number
  projected_monthly_cost_saved: number
  projected_annual_cost_saved: number
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

export const TokenOptimizationDashboard: React.FC = () => {
  const [stats, setStats] = useState<TokenStats | null>(null);
  const [projection, setProjection] = useState<MonthlyProjection | null>(null);
  const [timeRange, setTimeRange] = useState<number>(7);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [statsRes, projRes] = await Promise.all([
        fetch(`/api/v1/monitoring/token-stats?days=${timeRange}`),
        fetch('/api/v1/monitoring/token-projection'),
      ]);

      const statsData = await statsRes.json();
      const projData = await projRes.json();

      setStats(statsData);
      setProjection(projData);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const exportCSV = async () => {
    try {
      const response = await fetch(`/api/v1/monitoring/export-csv?days=${timeRange}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `token_usage_${timeRange}days.csv`;
      a.click();
    } catch (error) {
      console.error('Failed to export CSV:', error);
    }
  };

  if (!stats || !projection) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  const savingsPercentage = stats.average_savings_percentage;
  const providerData = Object.entries(stats.provider_breakdown).map(([name, data]) => ({
    name: name.toUpperCase(),
    requests: data.requests,
    tokens_saved: data.tokens_saved,
    cost_saved: data.cost_saved_usd,
  }));

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Savings color="primary" />
            Token Optimization Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Son güncelleme: {lastUpdated.toLocaleTimeString('tr-TR')}
          </Typography>
        </div>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Zaman Aralığı</InputLabel>
            <Select
              value={timeRange}
              label="Zaman Aralığı"
              onChange={(e) => setTimeRange(e.target.value as number)}
            >
              <MenuItem value={1}>Son 24 Saat</MenuItem>
              <MenuItem value={7}>Son 7 Gün</MenuItem>
              <MenuItem value={30}>Son 30 Gün</MenuItem>
              <MenuItem value={90}>Son 90 Gün</MenuItem>
            </Select>
          </FormControl>

          <Tooltip title="Yenile">
            <IconButton onClick={fetchStats} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>

          <Tooltip title="CSV İndir">
            <IconButton onClick={exportCSV}>
              <CloudDownload />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Toplam İstek
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.total_requests.toLocaleString()}
                  </Typography>
                </div>
                <Assessment color="primary" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Token Tasarrufu
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    {stats.total_tokens_saved.toLocaleString()}
                  </Typography>
                  <Chip
                    label={`${savingsPercentage.toFixed(1)}%`}
                    size="small"
                    color="success"
                    icon={<TrendingDown />}
                  />
                </div>
                <TrendingDown color="success" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Maliyet Tasarrufu
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="success.main">
                    ${stats.total_cost_saved_usd.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Son {timeRange} gün
                  </Typography>
                </div>
                <Savings color="success" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    Aylık Projeksiyon
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="primary">
                    ${projection.projected_monthly_cost_saved.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ~${projection.projected_annual_cost_saved.toFixed(0)}/yıl
                  </Typography>
                </div>
                <ArrowUpward color="primary" sx={{ fontSize: 40, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Provider Breakdown - Bar Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Provider Bazında Token Tasarrufu
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={providerData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="tokens_saved" fill="#8884d8" name="Token Tasarrufu" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Provider Distribution - Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Provider Kullanım Dağılımı
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={providerData}
                    dataKey="requests"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {providerData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Provider Details Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Provider Detayları
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Provider</strong></TableCell>
                  <TableCell align="right"><strong>İstek Sayısı</strong></TableCell>
                  <TableCell align="right"><strong>Orijinal Token</strong></TableCell>
                  <TableCell align="right"><strong>Optimize Token</strong></TableCell>
                  <TableCell align="right"><strong>Tasarruf</strong></TableCell>
                  <TableCell align="right"><strong>Tasarruf %</strong></TableCell>
                  <TableCell align="right"><strong>Maliyet Tasarrufu</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {providerData.map((provider) => {
                  const savingsPct = ((provider.tokens_saved / stats.provider_breakdown[provider.name.toLowerCase()].original_tokens) * 100) || 0;
                  return (
                    <TableRow key={provider.name}>
                      <TableCell>
                        <Chip label={provider.name} size="small" color="primary" variant="outlined" />
                      </TableCell>
                      <TableCell align="right">{provider.requests.toLocaleString()}</TableCell>
                      <TableCell align="right">
                        {stats.provider_breakdown[provider.name.toLowerCase()].original_tokens.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        {stats.provider_breakdown[provider.name.toLowerCase()].optimized_tokens.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="success.main" fontWeight="bold">
                          {provider.tokens_saved.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={`${savingsPct.toFixed(1)}%`}
                          size="small"
                          color={savingsPct >= 5 ? 'success' : savingsPct >= 3 ? 'warning' : 'default'}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="success.main" fontWeight="bold">
                          ${provider.cost_saved.toFixed(4)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default TokenOptimizationDashboard;
