/**
 * A/B Test Results Page
 * Statistical analysis and comparison of model optimization variants
 */

import {
  Science,
  TrendingDown,
  CheckCircle,
  Warning,
  Refresh,
  EmojiEvents,
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
  Alert,
} from '@mui/material';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface VersionStats {
  requests: number
  avg_tokens: number
  avg_cost: number
  avg_quality: number
  token_savings_vs_base: number
  cost_savings_vs_base: number
  quality_change_vs_base: number
}

interface ABTestResults {
  provider: string
  test_period_days: number
  total_requests: number
  versions: {
    [version: string]: VersionStats
  }
  winner: {
    version: string
    reason: string
    recommendation: string
    confidence: number
  }
  statistical_significance: {
    tokens_p_value: number
    quality_p_value: number
    is_significant: boolean
  }
}

const VERSION_LABELS = {
  base: 'Base (No Optimization)',
  optimized_prompt: 'Optimized Prompt',
  optimized_vocab: 'Optimized Vocabulary',
  optimized_full: 'Full Optimization',
};

const VERSION_COLORS = {
  base: '#9E9E9E',
  optimized_prompt: '#2196F3',
  optimized_vocab: '#FF9800',
  optimized_full: '#4CAF50',
};

export const ABTestResultsPage: React.FC = () => {
  const [results, setResults] = useState<ABTestResults | null>(null);
  const [provider, setProvider] = useState<string>('all');
  const [timeRange, setTimeRange] = useState<number>(7);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchResults = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/monitoring/ab-test-results?provider=${provider}&days=${timeRange}`, { credentials: 'include' });
      const data = await response.json();
      setResults(data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to fetch A/B test results:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
    const interval = setInterval(fetchResults, 60000);
    return () => clearInterval(interval);
  }, [provider, timeRange]);

  if (!results) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  const versionData = Object.entries(results.versions).map(([version, stats]) => ({
    version: VERSION_LABELS[version as keyof typeof VERSION_LABELS] || version,
    versionKey: version,
    requests: stats.requests,
    avg_tokens: stats.avg_tokens,
    avg_cost: stats.avg_cost * 1000,
    avg_quality: stats.avg_quality,
    token_savings: stats.token_savings_vs_base,
    cost_savings: stats.cost_savings_vs_base,
    quality_change: stats.quality_change_vs_base,
  }));

  const winner = results.winner;
  const isSignificant = results.statistical_significance.is_significant;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Science color="primary" />
            A/B Test Results
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Son güncelleme: {lastUpdated.toLocaleTimeString('tr-TR')}
          </Typography>
        </div>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Provider</InputLabel>
            <Select
              value={provider}
              label="Provider"
              onChange={(e) => setProvider(e.target.value)}
            >
              <MenuItem value="all">Tüm Providerlar</MenuItem>
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="claude">Claude</MenuItem>
              <MenuItem value="qwen">Qwen</MenuItem>
            </Select>
          </FormControl>

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
            </Select>
          </FormControl>

          <Tooltip title="Yenile">
            <IconButton onClick={fetchResults} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Winner Announcement */}
      {winner && (
        <Alert
          severity={isSignificant ? 'success' : 'warning'}
          icon={isSignificant ? <EmojiEvents /> : <Warning />}
          sx={{ mb: 3 }}
        >
          <Typography variant="h6" gutterBottom>
            {isSignificant ? 'Kazanan Versiyon Belirlendi!' : 'İstatistiksel Anlamlılık Düşük'}
          </Typography>
          <Typography variant="body2">
            <strong>{VERSION_LABELS[winner.version as keyof typeof VERSION_LABELS]}</strong>: {winner.reason}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {winner.recommendation}
          </Typography>
          <Box sx={{ mt: 1, display: 'flex', gap: 1, alignItems: 'center' }}>
            <Typography variant="caption">
              Güven: {(winner.confidence * 100).toFixed(1)}%
            </Typography>
            <Typography variant="caption">
              p-value (tokens): {results.statistical_significance.tokens_p_value.toFixed(4)}
            </Typography>
            <Typography variant="caption">
              p-value (quality): {results.statistical_significance.quality_p_value.toFixed(4)}
            </Typography>
          </Box>
        </Alert>
      )}

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Toplam Test
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {results.total_requests.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Son {results.test_period_days} gün
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Aktif Versiyon
              </Typography>
              <Typography variant="h6" fontWeight="bold">
                {Object.keys(results.versions).length}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Test edilen model versiyonu
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                En İyi Token Tasarrufu
              </Typography>
              <Typography variant="h4" fontWeight="bold" color="success.main">
                {Math.max(...versionData.map(v => v.token_savings)).toFixed(1)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Base versiyona göre
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom variant="body2">
                Kalite Değişimi
              </Typography>
              <Typography
                variant="h4"
                fontWeight="bold"
                color={Math.max(...versionData.map(v => v.quality_change)) >= 0 ? 'success.main' : 'error.main'}
              >
                {Math.max(...versionData.map(v => v.quality_change)) >= 0 ? '+' : ''}
                {Math.max(...versionData.map(v => v.quality_change)).toFixed(1)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Base versiyona göre
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Token Comparison */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Token Kullanımı Karşılaştırması
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={versionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="version" angle={-15} textAnchor="end" height={80} />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="avg_tokens" name="Ortalama Token">
                    {versionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={VERSION_COLORS[entry.versionKey as keyof typeof VERSION_COLORS]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Quality Comparison */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Kalite Skoru Karşılaştırması
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={versionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="version" angle={-15} textAnchor="end" height={80} />
                  <YAxis domain={[0, 100]} />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="avg_quality" name="Ortalama Kalite">
                    {versionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={VERSION_COLORS[entry.versionKey as keyof typeof VERSION_COLORS]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Savings Comparison */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tasarruf Karşılaştırması (Base Versiyona Göre)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={versionData.filter(v => v.versionKey !== 'base')}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="version" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="token_savings" name="Token Tasarrufu (%)" fill="#2196F3" />
                  <Bar dataKey="cost_savings" name="Maliyet Tasarrufu (%)" fill="#4CAF50" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Comparison Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Detaylı Karşılaştırma
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Versiyon</strong></TableCell>
                  <TableCell align="right"><strong>İstek Sayısı</strong></TableCell>
                  <TableCell align="right"><strong>Ort. Token</strong></TableCell>
                  <TableCell align="right"><strong>Token Tasarruf</strong></TableCell>
                  <TableCell align="right"><strong>Ort. Maliyet</strong></TableCell>
                  <TableCell align="right"><strong>Maliyet Tasarruf</strong></TableCell>
                  <TableCell align="right"><strong>Ort. Kalite</strong></TableCell>
                  <TableCell align="right"><strong>Kalite Değişimi</strong></TableCell>
                  <TableCell align="center"><strong>Durum</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {versionData.map((version) => {
                  const isWinner = version.versionKey === winner?.version;
                  return (
                    <TableRow
                      key={version.versionKey}
                      sx={{ bgcolor: isWinner ? 'success.light' : 'inherit' }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box
                            sx={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              bgcolor: VERSION_COLORS[version.versionKey as keyof typeof VERSION_COLORS],
                            }}
                          />
                          <Typography variant="body2" fontWeight={isWinner ? 'bold' : 'normal'}>
                            {version.version}
                          </Typography>
                          {isWinner && <EmojiEvents sx={{ fontSize: 20, color: 'warning.main' }} />}
                        </Box>
                      </TableCell>
                      <TableCell align="right">{version.requests.toLocaleString()}</TableCell>
                      <TableCell align="right">{version.avg_tokens.toFixed(0)}</TableCell>
                      <TableCell align="right">
                        {version.versionKey === 'base' ? '-' : (
                          <Chip
                            label={`${version.token_savings.toFixed(1)}%`}
                            size="small"
                            color={version.token_savings >= 30 ? 'success' : version.token_savings >= 5 ? 'primary' : 'default'}
                            icon={version.token_savings > 0 ? <TrendingDown /> : undefined}
                          />
                        )}
                      </TableCell>
                      <TableCell align="right">${version.avg_cost.toFixed(4)}</TableCell>
                      <TableCell align="right">
                        {version.versionKey === 'base' ? '-' : (
                          <Chip
                            label={`${version.cost_savings.toFixed(1)}%`}
                            size="small"
                            color={version.cost_savings >= 30 ? 'success' : version.cost_savings >= 5 ? 'primary' : 'default'}
                            icon={version.cost_savings > 0 ? <TrendingDown /> : undefined}
                          />
                        )}
                      </TableCell>
                      <TableCell align="right">{version.avg_quality.toFixed(1)}</TableCell>
                      <TableCell align="right">
                        {version.versionKey === 'base' ? '-' : (
                          <Typography
                            variant="body2"
                            color={version.quality_change >= 0 ? 'success.main' : 'error.main'}
                            fontWeight="bold"
                          >
                            {version.quality_change >= 0 ? '+' : ''}{version.quality_change.toFixed(1)}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {isWinner && (
                          <Chip
                            label="Kazanan"
                            size="small"
                            color="success"
                            icon={<CheckCircle />}
                          />
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Statistical Significance Info */}
      <Box sx={{ mt: 3 }}>
        <Alert severity="info">
          <Typography variant="body2">
            <strong>İstatistiksel Anlamlılık:</strong> p-value &lt; 0.05 değeri, sonuçların istatistiksel olarak anlamlı olduğunu gösterir.
            Düşük p-value, gözlemlenen farkların tesadüfi olmadığını ve güvenle bir kazanan belirlenebileceğini gösterir.
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            <strong>Öneri:</strong> {isSignificant
              ? 'Test sonuçları anlamlı. Kazanan versiyonu %100 trafiğe deploy edebilirsiniz.'
              : 'Daha fazla veri toplanması önerilir. Test süresini uzatın veya trafik miktarını artırın.'}
          </Typography>
        </Alert>
      </Box>
    </Box>
  );
};

export default ABTestResultsPage;
