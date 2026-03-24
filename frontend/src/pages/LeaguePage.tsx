/**
 * LeaguePage — /league
 * Haftalık lig sıralaması. GET /api/v1/leagues/current
 */
import { useEffect, useState } from 'react';
import {
  Avatar, Box, Card, CardContent, Chip, CircularProgress,
  Divider, LinearProgress, Stack, Table, TableBody,
  TableCell, TableHead, TableRow, Typography, Alert,
} from '@mui/material';
import { EmojiEvents, TrendingUp } from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

interface StandingsEntry {
  student_id:   string;
  display_name: string;
  xp:           number;
  rank:         number;
  is_self:      boolean;
}

interface LeagueData {
  tier:          string;
  rank:          number;
  weekly_xp:     number;
  total_in_tier: number;
  week_start:    string;
  standings:     StandingsEntry[];
}

const TIER_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  BRONZE:   { label: 'Bronz',   color: '#cd7f32', icon: '🥉' },
  SILVER:   { label: 'Gümüş',   color: '#c0c0c0', icon: '🥈' },
  GOLD:     { label: 'Altın',   color: '#ffd700', icon: '🥇' },
  PLATINUM: { label: 'Platin',  color: '#00bcd4', icon: '💎' },
  DIAMOND:  { label: 'Elmas',   color: '#9c27b0', icon: '♦️' },
  MASTER:   { label: 'Master',  color: '#f44336', icon: '👑' },
};

function rankMedal(rank: number) {
  if (rank === 1) return '🥇';
  if (rank === 2) return '🥈';
  if (rank === 3) return '🥉';
  return `#${rank}`;
}

export default function LeaguePage() {
  const [data,    setData]    = useState<LeagueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    apiRequest<LeagueData>('/api/v1/leagues/current')
      .then(setData)
      .catch(e => setError(String(e?.message ?? e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Box textAlign="center" py={8}><CircularProgress /></Box>;
  if (error || !data) return (
    <Box maxWidth={520} mx="auto" mt={4}>
      <Alert severity="error">{error ?? 'Lig verisi alınamadı'}</Alert>
    </Box>
  );

  const tier   = TIER_CONFIG[data.tier] ?? { label: data.tier, color: '#888', icon: '🏅' };
  const maxXP  = Math.max(...data.standings.map(s => s.xp), 1);
  const weekOf = new Date(data.week_start).toLocaleDateString('tr-TR', { day:'numeric', month:'long' });

  return (
    <Box maxWidth={720} mx="auto" py={3}>
      {/* Tier başlık kartı */}
      <Card sx={{ mb: 3, borderRadius: 3, background: `linear-gradient(135deg, ${tier.color}22 0%, ${tier.color}11 100%)`, border: `1px solid ${tier.color}44` }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center">
            <Typography fontSize={52}>{tier.icon}</Typography>
            <Box flex={1}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="h5" fontWeight={800}>{tier.label} Ligi</Typography>
                <Chip size="small" label={`${data.total_in_tier} oyuncu`} variant="outlined" />
              </Stack>
              <Typography variant="body2" color="text.secondary">{weekOf} haftası</Typography>
            </Box>
            <Box textAlign="right">
              <Typography variant="h4" fontWeight={800} color={tier.color}>#{data.rank}</Typography>
              <Typography variant="caption" color="text.secondary">Sıralaman</Typography>
            </Box>
          </Stack>
          <Stack direction="row" spacing={3} mt={2}>
            <Box>
              <Typography variant="h6" fontWeight={700}>{data.weekly_xp}</Typography>
              <Typography variant="caption" color="text.secondary">Bu hafta XP</Typography>
            </Box>
            <Box>
              <Typography variant="h6" fontWeight={700}>{data.rank} / {data.total_in_tier}</Typography>
              <Typography variant="caption" color="text.secondary">Sıralama</Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* Liderlik tablosu */}
      <Card variant="outlined" sx={{ borderRadius: 3 }}>
        <CardContent sx={{ pb: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center" mb={2}>
            <EmojiEvents color="primary" />
            <Typography variant="subtitle1" fontWeight={700}>Haftalık Sıralama</Typography>
          </Stack>
        </CardContent>
        <Divider />
        <Table size="small">
          <TableHead>
            <TableRow sx={{ '& th': { fontWeight: 700, fontSize: '0.75rem', color: 'text.secondary' } }}>
              <TableCell>Sıra</TableCell>
              <TableCell>Öğrenci</TableCell>
              <TableCell align="right">XP</TableCell>
              <TableCell sx={{ width: 140 }}>İlerleme</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.standings.map(s => (
              <TableRow key={s.student_id}
                sx={{ bgcolor: s.is_self ? 'primary.50' : 'transparent',
                      '&:hover': { bgcolor: s.is_self ? 'primary.100' : 'action.hover' } }}>
                <TableCell>
                  <Typography variant="body2" fontWeight={700} fontSize={s.rank <= 3 ? 18 : 14}>
                    {rankMedal(s.rank)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Avatar sx={{ width: 28, height: 28, fontSize: 12, bgcolor: tier.color }}>
                      {s.display_name[0]?.toUpperCase()}
                    </Avatar>
                    <Typography variant="body2" fontWeight={s.is_self ? 700 : 400}>
                      {s.display_name}{s.is_self && ' (sen)'}
                    </Typography>
                  </Stack>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2" fontWeight={700} color={s.is_self ? 'primary.main' : 'text.primary'}>
                    {s.xp.toLocaleString('tr-TR')}
                  </Typography>
                </TableCell>
                <TableCell>
                  <LinearProgress variant="determinate"
                    value={Math.round((s.xp / maxXP) * 100)}
                    sx={{ height: 6, borderRadius: 3,
                      '& .MuiLinearProgress-bar': { bgcolor: s.is_self ? 'primary.main' : tier.color } }} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* XP kazan ipucu */}
        <Box p={2} bgcolor="action.hover" sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <TrendingUp fontSize="small" color="success" />
            <Typography variant="caption" color="text.secondary">
              CAT tamamla → 10 XP · Placement bitir → 20 XP · Duel kazan → 30 XP · Günlük giriş → 5 XP
            </Typography>
          </Stack>
        </Box>
      </Card>
    </Box>
  );
}
