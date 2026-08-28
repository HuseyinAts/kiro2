/**
 * CalibrationStatusPage — /admin/calibration
 * IRT kalibrasyon pipeline durumu
 */
import { useEffect, useState } from 'react';
import {
  Alert, Box, Card, CardContent, Chip, CircularProgress,
  LinearProgress, Stack, Typography,
} from '@mui/material';
import { CheckCircle, Science, Warning, HourglassEmpty } from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

interface CalibStatus {
  total_questions:           number;
  genuinely_calibrated:      number;
  genuinely_calibrated_pct:  number;
  bootstrap_only:            number;
  uncalibrated:              number;
  pending_calibration:       number;
  response_data: {
    cat_responses:               number;
    exam_responses:              number;
    total_responses:             number;
    responses_needed_for_first_3pl: number;
  };
  last_genuine_calibration:  string | null;
  pipeline_status:           'NO_DATA' | 'ACCUMULATING' | 'READY';
  recommendation:            string;
}

const STATUS_CONFIG = {
  NO_DATA:     { label: 'Veri Yok',    color: 'error'   as const, icon: <Warning /> },
  ACCUMULATING:{ label: 'Biriyor',     color: 'warning' as const, icon: <HourglassEmpty /> },
  READY:       { label: 'Hazır',       color: 'success' as const, icon: <CheckCircle /> },
};

export default function CalibrationStatusPage() {
  const [data,    setData]    = useState<CalibStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    apiRequest<CalibStatus>('/api/v1/calibration/status')
      .then(setData)
      .catch(e => setError(String(e?.message ?? e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {return <Box textAlign="center" py={8}><CircularProgress /></Box>;}
  if (error || !data) {return <Box maxWidth={520} mx="auto" mt={4}><Alert severity="error">{error ?? 'Veri alınamadı'}</Alert></Box>;}

  const sc = STATUS_CONFIG[data.pipeline_status];
  const genuinePct = data.genuinely_calibrated_pct;
  const totalResp  = data.response_data.total_responses;
  const needed3pl  = data.response_data.responses_needed_for_first_3pl;
  const resp3plPct = Math.min(100, Math.round((totalResp / Math.max(totalResp + needed3pl, 1)) * 100));

  return (
    <Box maxWidth={800} mx="auto" py={3}>
      {/* Başlık */}
      <Stack direction="row" spacing={2} alignItems="center" mb={3}>
        <Science color="primary" sx={{ fontSize: 36 }} />
        <Box>
          <Typography variant="h5" fontWeight={800}>IRT Kalibrasyon Durumu</Typography>
          <Typography variant="body2" color="text.secondary">
            3PL Item Response Theory — Gerçek parametre kalibrasyonu
          </Typography>
        </Box>
        <Chip label={sc.label} color={sc.color} icon={sc.icon} sx={{ ml: 'auto' }} />
      </Stack>

      {/* Ana metrikler */}
      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(180px, 1fr))" gap={2} mb={3}>
        {[
          { label: 'Toplam Soru',         value: data.total_questions.toLocaleString('tr-TR'),     color: 'text.primary' },
          { label: 'Gerçek Kalibre',       value: data.genuinely_calibrated.toLocaleString('tr-TR'), color: 'success.main' },
          { label: 'Bootstrap',            value: data.bootstrap_only.toLocaleString('tr-TR'),       color: 'warning.main' },
          { label: 'Kalibre Edilmemiş',    value: data.uncalibrated.toLocaleString('tr-TR'),         color: 'error.main' },
          { label: 'Sıradaki (≥50 yanıt)',value: data.pending_calibration.toLocaleString('tr-TR'),  color: 'info.main' },
        ].map(m => (
          <Card variant="outlined" key={m.label} sx={{ borderRadius: 2 }}>
            <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
              <Typography variant="h5" fontWeight={800} color={m.color}>{m.value}</Typography>
              <Typography variant="caption" color="text.secondary">{m.label}</Typography>
            </CardContent>
          </Card>
        ))}
      </Box>

      {/* Gerçek kalibrasyon oranı */}
      <Card variant="outlined" sx={{ borderRadius: 2, mb: 2 }}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" mb={1}>
            <Typography variant="subtitle2" fontWeight={700}>Gerçek Kalibrasyon Oranı</Typography>
            <Typography variant="subtitle2" color={genuinePct > 10 ? 'success.main' : 'error.main'}>
              %{genuinePct}
            </Typography>
          </Stack>
          <LinearProgress variant="determinate" value={genuinePct}
            color={genuinePct > 50 ? 'success' : genuinePct > 10 ? 'warning' : 'error'}
            sx={{ height: 8, borderRadius: 4 }} />
          <Typography variant="caption" color="text.secondary" mt={0.5} display="block">
            Hedef: %80 → {Math.round(data.total_questions * 0.8 - data.genuinely_calibrated).toLocaleString('tr-TR')} soru daha
          </Typography>
        </CardContent>
      </Card>

      {/* Yanıt biriktirme */}
      <Card variant="outlined" sx={{ borderRadius: 2, mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle2" fontWeight={700} mb={1}>
            EM-3PL İçin Yanıt Biriktirme
          </Typography>
          <Stack direction="row" spacing={3} mb={1.5}>
            <Box>
              <Typography variant="h6" fontWeight={700}>{totalResp.toLocaleString('tr-TR')}</Typography>
              <Typography variant="caption" color="text.secondary">Toplam yanıt</Typography>
            </Box>
            <Box>
              <Typography variant="h6" fontWeight={700}>{data.response_data.cat_responses.toLocaleString('tr-TR')}</Typography>
              <Typography variant="caption" color="text.secondary">CAT'ten</Typography>
            </Box>
            <Box>
              <Typography variant="h6" fontWeight={700}>{data.response_data.exam_responses.toLocaleString('tr-TR')}</Typography>
              <Typography variant="caption" color="text.secondary">Sınavdan</Typography>
            </Box>
          </Stack>
          <LinearProgress variant="determinate" value={resp3plPct}
            color="primary" sx={{ height: 6, borderRadius: 3 }} />
          <Typography variant="caption" color="text.secondary" mt={0.5} display="block">
            İlk EM-3PL için {needed3pl > 0 ? `${needed3pl.toLocaleString('tr-TR')} yanıt daha gerekiyor` : '✅ hazır!'}
          </Typography>
        </CardContent>
      </Card>

      {/* Yol haritası */}
      <Card variant="outlined" sx={{ borderRadius: 2, mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle2" fontWeight={700} mb={1.5}>Kalibrasyon Yol Haritası</Typography>
          {[
            { label: '50 yanıt/soru',  desc: 'CTT fallback başlar',         threshold: 50,   current: totalResp },
            { label: '200 yanıt/soru', desc: 'EM-3PL güvenilir olur',       threshold: 200,  current: totalResp },
            { label: '~10K toplam',    desc: 'İlk 50 soru 3PL kalibre',     threshold: 10000, current: totalResp },
            { label: '~50K toplam',    desc: 'Top 250 soru kalibre',        threshold: 50000, current: totalResp },
            { label: '~200K toplam',   desc: 'Üst 1000 soru kalibre',      threshold: 200000, current: totalResp },
          ].map((step, i) => {
            const done = step.current >= step.threshold;
            return (
              <Stack key={i} direction="row" spacing={2} alignItems="center" py={0.8}
                sx={{ borderBottom: i < 4 ? '1px solid' : 'none', borderColor: 'divider' }}>
                <Box sx={{ width: 24, height: 24, borderRadius: '50%',
                  bgcolor: done ? 'success.main' : 'grey.200',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {done && <CheckCircle sx={{ fontSize: 16, color: '#fff' }} />}
                </Box>
                <Box flex={1}>
                  <Typography variant="body2" fontWeight={done ? 700 : 400}
                    color={done ? 'success.main' : 'text.primary'}>
                    {step.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">{step.desc}</Typography>
                </Box>
                <Chip size="small" label={done ? 'Geçildi ✓' : `${step.threshold.toLocaleString('tr-TR')}`}
                  color={done ? 'success' : 'default'} variant={done ? 'filled' : 'outlined'} />
              </Stack>
            );
          })}
        </CardContent>
      </Card>

      {/* Son bilgi */}
      <Alert severity="info" sx={{ borderRadius: 2 }}>
        <Typography variant="body2" fontWeight={600}>Öneri</Typography>
        <Typography variant="body2">{data.recommendation}</Typography>
        {data.last_genuine_calibration && (
          <Typography variant="caption" display="block" mt={0.5}>
            Son gerçek kalibrasyon: {new Date(data.last_genuine_calibration).toLocaleDateString('tr-TR')}
          </Typography>
        )}
      </Alert>

      {/* Komutlar */}
      <Card variant="outlined" sx={{ borderRadius: 2, mt: 2, bgcolor: '#1a1a2e' }}>
        <CardContent>
          <Typography variant="caption" color="grey.400" fontWeight={700} display="block" mb={1}>
            Manuel Çalıştırma Komutları
          </Typography>
          {[
            'python scripts\\irt_calibration_runner.py --dry-run',
            'python scripts\\irt_calibration_runner.py --min-responses 50 --limit 100',
            'python scripts\\irt_calibration_runner.py --subject MATEMATIK',
          ].map((cmd, i) => (
            <Typography key={i} variant="caption" component="div"
              sx={{ fontFamily: 'monospace', color: '#7dd3fc', mb: 0.5 }}>
              $ {cmd}
            </Typography>
          ))}
        </CardContent>
      </Card>
    </Box>
  );
}
