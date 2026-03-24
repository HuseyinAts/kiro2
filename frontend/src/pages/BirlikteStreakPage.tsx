/**
 * BirlikteStreakPage -- /birlikte-streak
 * Streak ortakligi — birlikte gunluk gorev
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
  Stack,
  Typography,
} from '@mui/material';
import {
  LocalFireDepartment,
  CheckCircle,
  RadioButtonUnchecked,
  Handshake,
  EmojiEvents,
} from '@mui/icons-material';
import type { StreakStatus } from '../services/socialService';
import { streak } from '../services/socialService';

export default function BirlikteStreakPage() {
  const [status, setStatus] = useState<StreakStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [acting, setActing] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const res = await streak.getStatus();
      setStatus(res.data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleRequest = async () => {
    setActing(true);
    try {
      await streak.request();
      fetchStatus();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActing(false);
    }
  };

  const handleComplete = async () => {
    setActing(true);
    try {
      await streak.completeToday();
      setError('');
      fetchStatus();
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

  // No active streak
  if (!status) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Stack spacing={3} alignItems="center">
          <LocalFireDepartment sx={{ fontSize: 60, color: 'warning.main' }} />
          <Typography variant="h4" fontWeight={700}>Birlikte Streak</Typography>
          <Typography color="text.secondary" textAlign="center">
            Bir ortakla birlikte gunluk gorev tamamla. Streak ne kadar uzun olursa o kadar cok XP!
          </Typography>
          <Card sx={{ width: '100%', p: 2, bgcolor: 'grey.50' }}>
            <Stack spacing={1}>
              <Typography variant="body2">7 gun = +30 bonus XP</Typography>
              <Typography variant="body2">30 gun = +100 bonus XP</Typography>
            </Stack>
          </Card>
          {error && <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>}
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleRequest}
            disabled={acting}
            startIcon={acting ? <CircularProgress size={20} /> : <Handshake />}
          >
            Ortak Bul
          </Button>
        </Stack>
      </Container>
    );
  }

  // Active streak
  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Stack spacing={3} alignItems="center">
        {error && <Alert severity="error" sx={{ width: '100%' }} onClose={() => setError('')}>{error}</Alert>}

        {/* Streak flame */}
        <Box sx={{ position: 'relative' }}>
          <LocalFireDepartment sx={{ fontSize: 80, color: status.current_streak > 0 ? 'warning.main' : 'grey.400' }} />
          <Typography
            variant="h3"
            fontWeight={700}
            sx={{ position: 'absolute', bottom: -10, left: '50%', transform: 'translateX(-50%)' }}
          >
            {status.current_streak}
          </Typography>
        </Box>

        <Typography variant="h5" fontWeight={700}>
          {status.current_streak} Gun Streak
        </Typography>
        <Typography variant="body2" color="text.secondary">
          En yuksek: {status.max_streak} gun | Toplam: {status.total_xp} XP
        </Typography>

        {/* Today's status */}
        <Card sx={{ width: '100%' }}>
          <CardContent>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Bugunku Durum
            </Typography>
            <Stack spacing={1}>
              <Stack direction="row" spacing={1} alignItems="center">
                {status.my_today
                  ? <CheckCircle color="success" />
                  : <RadioButtonUnchecked color="disabled" />
                }
                <Typography>
                  Sen: {status.my_today ? 'Tamamlandi!' : 'Henuz tamamlanmadi'}
                </Typography>
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                {status.partner_today
                  ? <CheckCircle color="success" />
                  : <RadioButtonUnchecked color="disabled" />
                }
                <Typography>
                  Ortak: {status.partner_today ? 'Tamamladi!' : 'Henuz tamamlamadi'}
                </Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>

        {/* Milestones */}
        <Stack direction="row" spacing={2}>
          <Chip
            icon={<EmojiEvents />}
            label="7 gun"
            color={status.current_streak >= 7 ? 'success' : 'default'}
            variant={status.current_streak >= 7 ? 'filled' : 'outlined'}
          />
          <Chip
            icon={<EmojiEvents />}
            label="30 gun"
            color={status.current_streak >= 30 ? 'success' : 'default'}
            variant={status.current_streak >= 30 ? 'filled' : 'outlined'}
          />
        </Stack>

        {/* Complete button */}
        {!status.my_today && (
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleComplete}
            disabled={acting}
            startIcon={acting ? <CircularProgress size={20} /> : <CheckCircle />}
            color="warning"
          >
            Bugunku Gorevi Tamamla
          </Button>
        )}
      </Stack>
    </Container>
  );
}
