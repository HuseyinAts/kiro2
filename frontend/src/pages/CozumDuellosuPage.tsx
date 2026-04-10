/**
 * CozumDuellosuPage -- /cozum-duellosu
 * Cozum Duellosu (Solution Duel) — F2
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
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import {
  EmojiEvents,
  HowToVote,
  Send,
} from '@mui/icons-material';
import type { DuelInfo, DuelSubmission } from '../services/socialService';
import { cozumDuellosu } from '../services/socialService';

const SUBJECTS = [
  'matematik', 'fizik', 'kimya', 'biyoloji',
  'turkce', 'tarih', 'cografya', 'geometri',
];

export default function CozumDuellosuPage() {
  const [activeDuels, setActiveDuels] = useState<{ id: string; subject_area: string; voting_ends_at: string | null }[]>([]);
  const [selectedDuel, setSelectedDuel] = useState<DuelInfo | null>(null);
  const [submissions, setSubmissions] = useState<DuelSubmission[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [subject, setSubject] = useState('MATEMATIK');
  const [solutionText, setSolutionText] = useState('');

  const fetchActive = useCallback(async () => {
    try {
      setLoading(true);
      const res = await cozumDuellosu.listActive({ limit: 20 });
      setActiveDuels(res.data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchActive(); }, [fetchActive]);

  const handleCreate = async () => {
    setActing(true);
    setError('');
    try {
      const res = await cozumDuellosu.create({
        question_bank_id: 'auto',
        subject_area: subject.toUpperCase(),
      });
      setMessage(res.message);
      if (res.data.matched) {
        const detail = await cozumDuellosu.getDuel(res.data.duel_id);
        setSelectedDuel(detail.data.duel);
        setSubmissions(detail.data.submissions);
      }
      fetchActive();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  const handleViewDuel = async (duelId: string) => {
    setActing(true);
    try {
      const res = await cozumDuellosu.getDuel(duelId);
      setSelectedDuel(res.data.duel);
      setSubmissions(res.data.submissions);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedDuel || !solutionText.trim()) return;
    setActing(true);
    try {
      const res = await cozumDuellosu.submit(selectedDuel.id, { body: solutionText });
      setMessage(res.message);
      setSolutionText('');
      const detail = await cozumDuellosu.getDuel(selectedDuel.id);
      setSelectedDuel(detail.data.duel);
      setSubmissions(detail.data.submissions);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  const handleVote = async (submissionId: string) => {
    if (!selectedDuel) return;
    setActing(true);
    try {
      const res = await cozumDuellosu.vote(selectedDuel.id, submissionId);
      setMessage(res.message);
      const detail = await cozumDuellosu.getDuel(selectedDuel.id);
      setSubmissions(detail.data.submissions);
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
          <EmojiEvents sx={{ fontSize: 40, color: 'warning.main' }} />
          <Box>
            <Typography variant="h4" fontWeight={700}>Cozum Duellosu</Typography>
            <Typography variant="body2" color="text.secondary">
              Ayni soruyu coz, topluluk oylasin. En iyi cozum kazanir!
            </Typography>
          </Box>
        </Stack>

        {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
        {message && <Alert severity="success" onClose={() => setMessage('')}>{message}</Alert>}

        {/* Create duel */}
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Yeni Duello
            </Typography>
            <Stack direction="row" spacing={2} alignItems="center">
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Konu</InputLabel>
                <Select value={subject} label="Konu" onChange={e => setSubject(e.target.value)}>
                  {SUBJECTS.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                color="warning"
                onClick={handleCreate}
                disabled={acting}
                startIcon={acting ? <CircularProgress size={20} /> : <EmojiEvents />}
              >
                Duello Baslat
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Selected duel detail */}
        {selectedDuel && (
          <Card sx={{ borderLeft: '4px solid #ed6c02' }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6" fontWeight={600}>
                    Duello: {selectedDuel.subject_area}
                  </Typography>
                  <Chip
                    label={selectedDuel.status}
                    color={selectedDuel.status === 'voting' ? 'warning' : selectedDuel.status === 'active' ? 'success' : 'default'}
                    size="small"
                  />
                </Stack>

                {/* Submissions */}
                {submissions.length > 0 ? (
                  <Stack spacing={1}>
                    <Typography variant="subtitle2">Cozumler:</Typography>
                    {submissions.map(s => (
                      <Card key={s.id} variant="outlined" sx={{ p: 1.5 }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="body2">{s.body}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {s.vote_count} oy
                            </Typography>
                          </Box>
                          {selectedDuel.status === 'voting' && (
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<HowToVote />}
                              onClick={() => handleVote(s.id)}
                              disabled={acting}
                            >
                              Oy Ver
                            </Button>
                          )}
                        </Stack>
                      </Card>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Henuz cozum gonderilmedi.
                  </Typography>
                )}

                {/* Submit solution */}
                {selectedDuel.status === 'active' && (
                  <Stack direction="row" spacing={1}>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      placeholder="Cozumunuzu yazin..."
                      value={solutionText}
                      onChange={e => setSolutionText(e.target.value)}
                    />
                    <Button
                      variant="contained"
                      onClick={handleSubmit}
                      disabled={acting || !solutionText.trim()}
                      sx={{ minWidth: 100 }}
                      startIcon={<Send />}
                    >
                      Gonder
                    </Button>
                  </Stack>
                )}
              </Stack>
            </CardContent>
          </Card>
        )}

        {/* Active duels list */}
        <Typography variant="h6" fontWeight={600}>
          Oylama Bekleyen Duellolar ({activeDuels.length})
        </Typography>
        {activeDuels.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" py={2}>
            Oylama bekleyen duello yok.
          </Typography>
        ) : (
          <Stack spacing={1}>
            {activeDuels.map(d => (
              <Card key={d.id} variant="outlined" sx={{ cursor: 'pointer' }} onClick={() => handleViewDuel(d.id)}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip label={d.subject_area} size="small" color="warning" />
                      <Typography variant="body2">
                        {d.voting_ends_at ? `Oylama: ${new Date(d.voting_ends_at).toLocaleDateString('tr-TR')}` : ''}
                      </Typography>
                    </Stack>
                    <Button size="small" variant="text">Goruntule</Button>
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
