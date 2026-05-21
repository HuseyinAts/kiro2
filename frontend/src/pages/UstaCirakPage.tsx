/**
 * UstaCirakPage -- /usta-cirak
 * Mentor-Mentee sistemi
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
  Typography,
} from '@mui/material';
import {
  School,
  PersonAdd,
} from '@mui/icons-material';
import type { MentorPairInfo } from '../services/socialService';
import { ustaCirak } from '../services/socialService';

const SUBJECTS = [
  'matematik', 'fizik', 'kimya', 'biyoloji',
  'turkce', 'tarih', 'cografya', 'geometri',
];

export default function UstaCirakPage() {
  const [pairs, setPairs] = useState<MentorPairInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [acting, setActing] = useState(false);
  const [subject, setSubject] = useState('matematik');
  const [role, setRole] = useState<'mentor' | 'mentee'>('mentee');
  // S179 fix (B-P0-44): expose end-session UI so XP can finally be awarded.
  // Pre-fix the only way to leave a session was to reload — duration
  // never reached the backend and XPTransaction was never written.
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionStartedAt, setSessionStartedAt] = useState<number | null>(null);
  const [sessionElapsed, setSessionElapsed] = useState(0);

  // Tick the on-screen timer when a session is active.
  useEffect(() => {
    if (!sessionStartedAt) {
      return;
    }
    const t = window.setInterval(() => {
      setSessionElapsed(Math.floor((Date.now() - sessionStartedAt) / 1000));
    }, 1000);
    return () => window.clearInterval(t);
  }, [sessionStartedAt]);

  const fetchPairs = useCallback(async () => {
    try {
      setLoading(true);
      const res = await ustaCirak.getPairs();
      setPairs(res.data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPairs(); }, [fetchPairs]);

  const handleRequest = async () => {
    setActing(true);
    try {
      const res = await ustaCirak.requestMatch({ subject_area: subject, role });
      if (res.data.matched) {
        fetchPairs();
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActing(false);
    }
  };

  const handleStartSession = async (pairId: string) => {
    setActing(true);
    try {
      const res = await ustaCirak.startSession(pairId);
      const sessionId = res?.data?.session_id ?? null;
      if (sessionId) {
        setActiveSessionId(sessionId);
        setSessionStartedAt(Date.now());
        setSessionElapsed(0);
      }
      fetchPairs();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Oturum baslatilamadi');
    } finally {
      setActing(false);
    }
  };

  // S179 fix (B-P0-44): close the loop so XP is actually awarded.
  const handleEndSession = async () => {
    if (!activeSessionId) {
      return;
    }
    setActing(true);
    try {
      const res = await ustaCirak.endSession(activeSessionId);
      const minutes = res?.data?.duration_minutes ?? 0;
      const mentorXp = res?.data?.mentor_xp ?? 0;
      const menteeXp = res?.data?.mentee_xp ?? 0;
      setError('');
      // Toast-style flash via the existing Alert region — simplest path.
      window.alert(
        `Oturum tamamlandi. Sure: ${minutes} dk. ` +
          `Usta XP: ${mentorXp}, Cirak XP: ${menteeXp}.`,
      );
      setActiveSessionId(null);
      setSessionStartedAt(null);
      setSessionElapsed(0);
      fetchPairs();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Oturum kapatilamadi');
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
          <School sx={{ fontSize: 40, color: 'secondary.main' }} />
          <Box>
            <Typography variant="h4" fontWeight={700}>Usta-Cirak</Typography>
            <Typography variant="body2" color="text.secondary">
              Konunda iyiysen cirak al, ogreniyorsan usta bul.
            </Typography>
          </Box>
        </Stack>

        {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}

        {/* S179 fix (B-P0-44): Active session banner with timer + end-session
            button. Pre-fix `startSession` ran but the UI gave the student no
            way to call `endSession`, so XP was never awarded. */}
        {activeSessionId && (
          <Card sx={{ borderLeft: '4px solid #2e7d32' }}>
            <CardContent>
              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
                <Box>
                  <Typography variant="subtitle1" fontWeight={700}>
                    Aktif oturum
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sure: {Math.floor(sessionElapsed / 60)} dk {sessionElapsed % 60} sn
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleEndSession}
                  disabled={acting}
                  aria-label="Oturumu sonlandir ve XP kazan"
                >
                  Oturumu Sonlandir
                </Button>
              </Stack>
            </CardContent>
          </Card>
        )}

        {/* Match request */}
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Yeni Eslestirme
            </Typography>
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <FormControl sx={{ minWidth: 150 }}>
                <InputLabel>Konu</InputLabel>
                <Select value={subject} label="Konu" onChange={e => setSubject(e.target.value)}>
                  {SUBJECTS.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                </Select>
              </FormControl>
              <FormControl sx={{ minWidth: 120 }}>
                <InputLabel>Rol</InputLabel>
                <Select value={role} label="Rol" onChange={e => setRole(e.target.value as 'mentor' | 'mentee')}>
                  <MenuItem value="mentor">Usta</MenuItem>
                  <MenuItem value="mentee">Cirak</MenuItem>
                </Select>
              </FormControl>
              <Button
                variant="contained"
                color="secondary"
                onClick={handleRequest}
                disabled={acting}
                startIcon={acting ? <CircularProgress size={20} /> : <PersonAdd />}
              >
                Esles
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Active pairs */}
        <Typography variant="h6" fontWeight={600}>
          Aktif Eslesmelerim ({pairs.length})
        </Typography>

        {pairs.length === 0 ? (
          <Typography color="text.secondary" textAlign="center" py={2}>
            Henuz eslestirmeniz yok.
          </Typography>
        ) : (
          <Stack spacing={2}>
            {pairs.map(p => (
              <Card key={p.id} sx={{
                borderLeft: `4px solid ${p.my_role === 'mentor' ? '#9c27b0' : '#1976d2'}`,
              }}>
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Chip
                          label={p.my_role === 'mentor' ? 'Usta' : 'Cirak'}
                          color={p.my_role === 'mentor' ? 'secondary' : 'primary'}
                          size="small"
                        />
                        <Typography variant="subtitle1" fontWeight={600}>
                          {p.subject_area}
                        </Typography>
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {p.session_count} oturum tamamlandi
                      </Typography>
                    </Box>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleStartSession(p.id)}
                      disabled={acting}
                    >
                      Oturum Baslat
                    </Button>
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
