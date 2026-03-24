/**
 * PomodoroPage -- /pomodoro
 * Birlikte calisma odalari — 25/5 pomodoro
 */
import { useEffect, useState, useCallback, useRef } from 'react';
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
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import {
  Timer,
  PlayArrow,
  Pause,
  Stop,
  EmojiEvents,
  People,
} from '@mui/icons-material';
import type { PomodoroRoom, PomodoroParticipant } from '../services/socialService';
import { pomodoro } from '../services/socialService';

const SUBJECTS = [
  'matematik', 'fizik', 'kimya', 'biyoloji',
  'turkce', 'tarih', 'cografya', 'geometri',
];

export default function PomodoroPage() {
  const [roomId, setRoomId] = useState<string | null>(null);
  const [room, setRoom] = useState<PomodoroRoom | null>(null);
  const [participants, setParticipants] = useState<PomodoroParticipant[]>([]);
  const [subject, setSubject] = useState('matematik');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [timer, setTimer] = useState(0); // seconds remaining
  const [isWork, setIsWork] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchRoom = useCallback(async () => {
    if (!roomId) return;
    try {
      const res = await pomodoro.getRoom(roomId);
      setRoom(res.data.room);
      setParticipants(res.data.participants);
    } catch (e: any) {
      setError(e.message);
    }
  }, [roomId]);

  useEffect(() => {
    if (roomId) {
      fetchRoom();
      const interval = setInterval(fetchRoom, 10000); // poll every 10s
      return () => clearInterval(interval);
    }
  }, [roomId, fetchRoom]);

  // Timer countdown
  useEffect(() => {
    if (timer > 0) {
      timerRef.current = setInterval(() => {
        setTimer(prev => {
          if (prev <= 1) {
            if (timerRef.current) clearInterval(timerRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }
  }, [timer > 0]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleJoin = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await pomodoro.join({ subject_area: subject });
      setRoomId(res.data.room_id);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const startWork = async () => {
    if (!roomId) return;
    await pomodoro.updateStatus(roomId, 'working');
    setIsWork(true);
    setTimer((room?.work_minutes || 25) * 60);
    fetchRoom();
  };

  const startBreak = async () => {
    if (!roomId) return;
    await pomodoro.updateStatus(roomId, 'on_break');
    setIsWork(false);
    setTimer((room?.break_minutes || 5) * 60);
    fetchRoom();
  };

  const completeRound = async () => {
    if (!roomId) return;
    try {
      await pomodoro.completeRound(roomId);
      setError('');
      fetchRoom();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const leaveRoom = async () => {
    if (!roomId) return;
    await pomodoro.updateStatus(roomId, 'left');
    setRoomId(null);
    setRoom(null);
    setParticipants([]);
    setTimer(0);
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  };

  // Not in a room — show join UI
  if (!roomId) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Stack spacing={3} alignItems="center">
          <Timer sx={{ fontSize: 60, color: 'error.main' }} />
          <Typography variant="h4" fontWeight={700}>Pomodoro Odalari</Typography>
          <Typography color="text.secondary" textAlign="center">
            Konu sec, odaya katil, birlikte calis. 25dk odak + 5dk mola.
          </Typography>

          {error && <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>}

          <FormControl fullWidth>
            <InputLabel>Konu</InputLabel>
            <Select value={subject} label="Konu" onChange={e => setSubject(e.target.value)}>
              {SUBJECTS.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
            </Select>
          </FormControl>

          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={handleJoin}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
          >
            Odaya Katil
          </Button>
        </Stack>
      </Container>
    );
  }

  // In a room
  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Stack spacing={3} alignItems="center">
        {error && <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert>}

        {/* Timer display */}
        <Box sx={{ position: 'relative', display: 'inline-flex' }}>
          <CircularProgress
            variant="determinate"
            value={timer > 0 ? (timer / ((isWork ? (room?.work_minutes || 25) : (room?.break_minutes || 5)) * 60)) * 100 : 0}
            size={200}
            thickness={4}
            color={isWork ? 'error' : 'success'}
          />
          <Box sx={{
            top: 0, left: 0, bottom: 0, right: 0,
            position: 'absolute', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column',
          }}>
            <Typography variant="h2" fontWeight={700}>
              {formatTime(timer)}
            </Typography>
            <Chip
              label={isWork ? 'Calisma' : 'Mola'}
              color={isWork ? 'error' : 'success'}
              size="small"
            />
          </Box>
        </Box>

        {/* Room info */}
        <Card sx={{ width: '100%' }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between">
              <Typography variant="subtitle2">
                {room?.subject_area} — Tur {room?.current_round}/{room?.total_rounds}
              </Typography>
              <Stack direction="row" spacing={0.5} alignItems="center">
                <People fontSize="small" />
                <Typography variant="body2">{participants.length}</Typography>
              </Stack>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={((room?.current_round || 0) / (room?.total_rounds || 4)) * 100}
              sx={{ mt: 1 }}
            />
          </CardContent>
        </Card>

        {/* Participants */}
        <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="center">
          {participants.map((p, i) => (
            <Chip
              key={i}
              label={`Ogrenci ${i + 1}`}
              color={p.status === 'working' ? 'error' : p.status === 'on_break' ? 'success' : 'default'}
              variant={p.status === 'left' ? 'outlined' : 'filled'}
              size="small"
            />
          ))}
        </Stack>

        {/* Controls */}
        <Stack direction="row" spacing={2}>
          <Button
            variant="contained"
            color="error"
            startIcon={<PlayArrow />}
            onClick={startWork}
            disabled={timer > 0}
          >
            Calis
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={<Pause />}
            onClick={startBreak}
            disabled={timer > 0}
          >
            Mola
          </Button>
          <Button
            variant="outlined"
            startIcon={<EmojiEvents />}
            onClick={completeRound}
            disabled={timer > 0}
          >
            Tur Bitti
          </Button>
        </Stack>

        <Button
          variant="text"
          color="error"
          startIcon={<Stop />}
          onClick={leaveRoom}
        >
          Odadan Cik
        </Button>
      </Stack>
    </Container>
  );
}
