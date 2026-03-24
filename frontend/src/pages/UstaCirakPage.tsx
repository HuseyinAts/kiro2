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
      await ustaCirak.startSession(pairId);
      fetchPairs();
    } catch (e: any) {
      setError(e.message);
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
