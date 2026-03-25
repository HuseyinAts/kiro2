/**
 * YKSEstimatePage — YKS Puan Tahmini
 * GET /api/v1/estimate/full  →  tüm puan türleri
 */
import { useEffect, useState } from 'react';
import {
  Alert, Box, Card, CardContent, Chip, CircularProgress,
  Divider, Grid, LinearProgress, Stack, Typography,
} from '@mui/material';
import { EmojiEvents, School, TrendingUp, WarningAmber } from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

interface PuanTahmini {
  puan_turu:        string;
  puan:             number;
  alt_sinir:        number;
  ust_sinir:        number;
  tahmini_siralama: number;
  siralama_alt:     number;
  siralama_ust:     number;
  yuzdelik:         number;
  guvenilik:        string;
}

interface FullEstimate {
  tyt: PuanTahmini | null;
  say: PuanTahmini | null;
  ea:  PuanTahmini | null;
  soz: PuanTahmini | null;
  dil: PuanTahmini | null;
}

const GUVENILIK_RENK: Record<string, 'success' | 'warning' | 'error'> = {
  'yüksek': 'success', 'orta': 'warning', 'düşük': 'error',
};
const PUAN_TURU_AD: Record<string, string> = {
  TYT: 'TYT', SAY: 'SAY (Sayısal)', EA: 'EA (Eşit Ağırlık)',
  'SÖZ': 'SÖZ (Sözel)', 'DİL': 'DİL (Yabancı)',
};
function puanRenk(p: number) {
  return p >= 400 ? '#2e7d32' : p >= 300 ? '#1565c0' : p >= 200 ? '#e65100' : '#b71c1c';
}

function PuanKart({ tahmin: t }: { tahmin: PuanTahmini }) {
  const renk = GUVENILIK_RENK[t.guvenilik] ?? 'warning';
  const bar  = Math.min(100, Math.max(0, ((t.puan - 100) / 400) * 100));
  return (
    <Card variant="outlined" sx={{ borderRadius: 3, height: '100%' }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1.5}>
          <Typography variant="subtitle1" fontWeight={700}>
            {PUAN_TURU_AD[t.puan_turu] ?? t.puan_turu}
          </Typography>
          <Chip size="small" label={t.guvenilik} color={renk}
            icon={t.guvenilik === 'düşük' ? <WarningAmber fontSize="small" /> : undefined} />
        </Stack>

        <Typography variant="h3" fontWeight={800} sx={{ color: puanRenk(t.puan), lineHeight: 1 }}>
          {t.puan.toFixed(0)}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t.alt_sinir.toFixed(0)} – {t.ust_sinir.toFixed(0)} puan aralığı
        </Typography>

        <LinearProgress variant="determinate" value={bar}
          sx={{ mt: 1.5, mb: 1.5, height: 8, borderRadius: 4 }} color={renk} />

        <Divider sx={{ mb: 1.5 }} />

        <Stack spacing={0.5}>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">Tahmini sıralama</Typography>
            <Typography variant="body2" fontWeight={600}>
              {t.tahmini_siralama.toLocaleString('tr-TR')}
            </Typography>
          </Stack>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="body2" color="text.secondary">Yüzdelik</Typography>
            <Typography variant="body2" fontWeight={600}>%{t.yuzdelik.toFixed(1)}</Typography>
          </Stack>
          <Stack direction="row" justifyContent="space-between">
            <Typography variant="caption" color="text.secondary">Sıralama aralığı</Typography>
            <Typography variant="caption" color="text.secondary">
              {t.siralama_alt.toLocaleString('tr-TR')} – {t.siralama_ust.toLocaleString('tr-TR')}
            </Typography>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

export default function YKSEstimatePage() {
  const [data,    setData]    = useState<FullEstimate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    apiRequest<FullEstimate>('/api/v1/estimate/full')
      .then(setData)
      .catch((e: any) => {
        const msg = String(e?.message ?? e);
        setError(msg.includes('404') || msg.includes('CAT')
          ? 'Henüz tamamlanmış CAT oturumu yok. Önce Adaptif Test veya Seviye Tespiti tamamla.'
          : msg);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <Box textAlign="center" py={8}>
      <CircularProgress size={52} />
      <Typography mt={2} color="text.secondary">Puan tahmini hesaplanıyor...</Typography>
    </Box>
  );

  if (error || !data) return (
    <Box maxWidth={640} mx="auto" mt={4}>
      <Alert severity="info" icon={<School />} sx={{ borderRadius: 2 }}>
        <Typography variant="subtitle2" fontWeight={700} mb={0.5}>Henüz Tahmin Yapılamıyor</Typography>
        <Typography variant="body2">{error ?? 'Tamamlanmış CAT oturumu bulunamadı.'}</Typography>
        <Typography variant="body2" mt={1}>
          👉 <strong>/assessment</strong> veya <strong>/cat</strong> sayfasından bir test tamamla.
        </Typography>
      </Alert>
    </Box>
  );

  const puanlar = [data.tyt, data.say, data.ea, data.soz, data.dil].filter(Boolean) as PuanTahmini[];
  const enYuksek = puanlar.length ? puanlar.reduce((a, b) => a.puan > b.puan ? a : b) : null;

  return (
    <Box>
      {/* Başlık */}
      <Stack direction="row" spacing={2} alignItems="center" mb={3}>
        <EmojiEvents sx={{ fontSize: 40, color: 'primary.main' }} />
        <Box>
          <Typography variant="h5" fontWeight={700}>YKS Puan Tahmini</Typography>
          <Typography variant="body2" color="text.secondary">
            CAT oturumlarındaki θ değerlerinden IRT ile hesaplanmıştır
          </Typography>
        </Box>
      </Stack>

      {/* En yüksek puan özeti */}
      {enYuksek && (
        <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1565c0 0%, #0d47a1 100%)', color: '#fff', borderRadius: 3 }}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="center">
              <TrendingUp sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>En yüksek puan tahmini</Typography>
                <Typography variant="h4" fontWeight={800}>
                  {enYuksek.puan.toFixed(0)} — {PUAN_TURU_AD[enYuksek.puan_turu] ?? enYuksek.puan_turu}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.85 }}>
                  Sıralama: {enYuksek.tahmini_siralama.toLocaleString('tr-TR')} · %{enYuksek.yuzdelik.toFixed(1)} yüzdelik
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      )}

      {/* Düşük güvenilirlik uyarısı */}
      {puanlar.some(p => p.guvenilik === 'düşük') && (
        <Alert severity="warning" sx={{ mb: 3, borderRadius: 2 }}>
          Güvenilirlik artırmak için Türkçe, Matematik, Fen gibi ek dersleri de tamamla.
        </Alert>
      )}

      {/* Puan kartları */}
      <Grid container spacing={2}>
        {puanlar.map(p => (
          <Grid item xs={12} sm={6} md={4} key={p.puan_turu}>
            <PuanKart tahmin={p} />
          </Grid>
        ))}
      </Grid>

      <Typography variant="caption" color="text.secondary" display="block" mt={3} textAlign="center">
        * Tahminler IRT θ ve ÖSYM 2024 istatistiklerine dayanır. Gerçek sınav farklılık gösterebilir.
      </Typography>
    </Box>
  );
}
