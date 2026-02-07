/**
 * Temel Sonuçlar Tab
 * Basic results with statistics, charts and topic performance
 */
import {
  Assessment,
  CheckCircle,
  Cancel,
  RemoveCircle,
  ExpandMore,
} from '@mui/icons-material';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Chip,
} from '@mui/material';
import * as React from 'react';
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

import { SinavSonucu, KonuPerformansi } from '../../../types';

interface BasicResultsTabProps {
  sonuc: SinavSonucu;
}

export const BasicResultsTab: React.FC<BasicResultsTabProps> = ({ sonuc }) => {
  const preparePieChartData = (sonuc: SinavSonucu) => {
    return [
      { name: 'Doğru', value: sonuc.dogru_sayisi, color: '#10b981' },
      { name: 'Yanlış', value: sonuc.yanlis_sayisi, color: '#ef4444' },
      { name: 'Boş', value: sonuc.bos_sayisi, color: '#6b7280' },
    ];
  };

  const prepareTopicPerformanceData = (konuPerformanslari: KonuPerformansi[]) => {
    return konuPerformanslari.map(konu => ({
      konu: konu.konu.length > 15 ? konu.konu.substring(0, 15) + '...' : konu.konu,
      basari: konu.basari_yuzdesi,
      dogru: konu.dogru_sayisi,
      yanlis: konu.yanlis_sayisi,
      bos: konu.bos_sayisi,
    }));
  };

  const pieData = preparePieChartData(sonuc);
  const topicData = prepareTopicPerformanceData(sonuc.konu_performanslari);

  return (
    <Box>
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
      <Accordion>
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
    </Box>
  );
};

export default BasicResultsTab;
