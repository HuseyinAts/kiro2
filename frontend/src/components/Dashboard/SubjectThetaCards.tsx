/**
 * SubjectThetaCards — Dashboard seviye kartları
 * GET /api/v1/estimate/thetas  →  her ders için theta + seviye
 */
import { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Chip, CircularProgress,
  Grid, LinearProgress, Stack, Typography,
} from '@mui/material';
import { TrendingUp } from '@mui/icons-material';
import { apiRequest } from '../../utils/apiHelpers';

interface DersTheta {
  ders_kodu: string;
  ders_adi:  string;
  theta:     number;
  se:        number;
  seviye:    string;
}

const SEVİYE_RENK: Record<string, 'error' | 'warning' | 'info' | 'success' | 'primary'> = {
  'Temel':       'error',
  'Orta-Temel':  'warning',
  'Orta':        'info',
  'Orta-İleri':  'primary',
  'İleri':       'success',
};

// θ [-3, +3] → [0, 100]
function thetaToPercent(theta: number) {
  return Math.min(100, Math.max(0, ((theta + 3) / 6) * 100));
}

export default function SubjectThetaCards() {
  const [data,    setData]    = useState<DersTheta[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<DersTheta[]>('/api/v1/estimate/thetas')
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {return <CircularProgress size={28} />;}
  if (!data.length) {return (
    <Typography variant="body2" color="text.secondary">
      Henüz tamamlanmış ders testi yok. CAT veya Seviye Tespiti yap.
    </Typography>
  );}

  return (
    <Box>
      <Stack direction="row" spacing={1} alignItems="center" mb={2}>
        <TrendingUp color="primary" />
        <Typography variant="subtitle1" fontWeight={700}>Ders Seviyelerin</Typography>
      </Stack>
      <Grid container spacing={1.5}>
        {data.map(d => {
          const pct   = thetaToPercent(d.theta);
          const renk  = SEVİYE_RENK[d.seviye] ?? 'info';
          return (
            <Grid item xs={12} sm={6} md={4} key={d.ders_kodu}>
              <Card variant="outlined" sx={{ borderRadius: 2 }}>
                <CardContent sx={{ py: 1.5, px: 2, '&:last-child': { pb: 1.5 } }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" fontWeight={600}>{d.ders_adi}</Typography>
                    <Chip size="small" label={d.seviye} color={renk} />
                  </Stack>
                  <LinearProgress
                    variant="determinate" value={pct} color={renk}
                    sx={{ mt: 1, mb: 0.5, height: 5, borderRadius: 3 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    θ = {d.theta.toFixed(2)} · SE = {d.se.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
}
