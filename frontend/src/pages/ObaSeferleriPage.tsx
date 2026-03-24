/**
 * ObaSeferleriPage -- /oba-seferleri
 * Oba Seferleri (Team Challenges) — F3
 */
import { useEffect, useState, useCallback } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import {
  Groups,
  Add,
} from '@mui/icons-material';
import type { ObaChallengeInfo, ObaContributor } from '../services/socialService';
import { obaSeferleri } from '../services/socialService';

// Demo oba ID - gercek uygulamada kullanicinin obasindan gelecek
const DEMO_OBA_ID = 'demo-oba';

export default function ObaSeferleriPage() {
  const [challenge, setChallenge] = useState<ObaChallengeInfo | null>(null);
  const [contributors, setContributors] = useState<ObaContributor[]>([]);
  const [history, setHistory] = useState<{ id: string; title: string; completed: boolean; start_date: string; end_date: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [activeRes, historyRes] = await Promise.all([
        obaSeferleri.getActive(DEMO_OBA_ID),
        obaSeferleri.getHistory(DEMO_OBA_ID, 10),
      ]);
      if (activeRes.data) {
        setChallenge(activeRes.data.challenge);
        setContributors(activeRes.data.contributors);
      } else {
        setChallenge(null);
        setContributors([]);
      }
      setHistory(historyRes.data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleContribute = async (amount: number) => {
    if (!challenge) return;
    setActing(true);
    setError('');
    try {
      const res = await obaSeferleri.contribute(challenge.id, amount);
      setMessage(res.message);
      // Refresh
      const activeRes = await obaSeferleri.getActive(DEMO_OBA_ID);
      if (activeRes.data) {
        setChallenge(activeRes.data.challenge);
        setContributors(activeRes.data.contributors);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="sm" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Stack spacing={3}>
        {/* Header */}
        <Stack direction="row" spacing={2} alignItems="center">
          <Groups sx={{ fontSize: 40, color: 'success.main' }} />
          <Box>
            <Typography variant="h4" fontWeight={700}>Oba Seferleri</Typography>
            <Typography variant="body2" color="text.secondary">
              Haftalik takim gorevi — birlikte hedefe ulasin, bonus XP kazanin!
            </Typography>
          </Box>
        </Stack>

        {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
        {message && <Alert severity="success" onClose={() => setMessage('')}>{message}</Alert>}

        {/* Active challenge */}
        {challenge ? (
          <Card sx={{ borderLeft: '4px solid #2e7d32' }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6" fontWeight={600}>{challenge.title}</Typography>
                  <Chip
                    label={challenge.completed ? 'Tamamlandi' : 'Aktif'}
                    color={challenge.completed ? 'success' : 'primary'}
                    size="small"
                  />
                </Stack>
                {challenge.description && (
                  <Typography variant="body2" color="text.secondary">
                    {challenge.description}
                  </Typography>
                )}

                {/* Progress */}
                <Box>
                  <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                    <Typography variant="body2">
                      {challenge.current_value} / {challenge.target_value}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      %{challenge.progress_pct}
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(challenge.progress_pct, 100)}
                    sx={{ height: 10, borderRadius: 1 }}
                    color={challenge.completed ? 'success' : 'primary'}
                  />
                </Box>

                <Typography variant="body2" color="text.secondary">
                  Bonus: +{challenge.bonus_xp_per_member} XP / uye | {challenge.start_date} - {challenge.end_date}
                </Typography>

                {/* Contribute buttons */}
                {!challenge.completed && (
                  <Stack direction="row" spacing={1}>
                    {[1, 5, 10].map(n => (
                      <Button
                        key={n}
                        variant="outlined"
                        size="small"
                        startIcon={<Add />}
                        onClick={() => handleContribute(n)}
                        disabled={acting}
                      >
                        +{n} Katki
                      </Button>
                    ))}
                  </Stack>
                )}

                {/* Contributors */}
                {contributors.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Katkilar:
                    </Typography>
                    <Stack spacing={0.5}>
                      {contributors.map((c, i) => (
                        <Stack key={c.student_id} direction="row" justifyContent="space-between" alignItems="center">
                          <Typography variant="body2">
                            #{i + 1} {c.student_id.slice(0, 8)}...
                          </Typography>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography variant="body2">{c.contribution}</Typography>
                            <Chip label={`%${(c.ratio * 100).toFixed(0)}`} size="small" variant="outlined" />
                          </Stack>
                        </Stack>
                      ))}
                    </Stack>
                  </Box>
                )}
              </Stack>
            </CardContent>
          </Card>
        ) : (
          <Card sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">
              Bu hafta aktif gorev yok. Yeni gorev yakinda atanacak!
            </Typography>
          </Card>
        )}

        {/* History */}
        <Typography variant="h6" fontWeight={600}>
          Gecmis Gorevler ({history.length})
        </Typography>
        {history.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" py={2}>
            Henuz gecmis gorev yok.
          </Typography>
        ) : (
          <Stack spacing={1}>
            {history.map(h => (
              <Card key={h.id} variant="outlined">
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="subtitle2">{h.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {h.start_date} - {h.end_date}
                      </Typography>
                    </Box>
                    <Chip
                      label={h.completed ? 'Basarili' : 'Bitmedi'}
                      color={h.completed ? 'success' : 'default'}
                      size="small"
                    />
                  </Stack>
                </CardContent>
              </Card>
            ))}
          </Stack>
        )}
      </Stack>
    </Container>
  );
}
