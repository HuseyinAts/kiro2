/**
 * Gelişmiş Sınav Zamanlayıcısı
 * Görsel ve etkileşimli timer bileşeni
 */
import {
  Timer,
  Warning,
  Pause,
  PlayArrow,
  Visibility,
  VisibilityOff,
  Schedule,
  Alarm,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  Chip,
  LinearProgress,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import * as React from 'react';
import {  useState, useEffect, useRef, useMemo  } from 'react';

interface WarningThresholds {
  halfway?: number // Yarı süre uyarısı (saniye)
  final?: number   // Son uyarı (saniye)
  critical?: number // Kritik uyarı (saniye)
}

interface ExamTimerProps {
  totalTimeSeconds: number
  remainingTimeSeconds: number
  onTimeUpdate?: (remainingTime: number) => void
  onTimeWarning?: (warningType: 'halfway' | 'final' | 'critical') => void
  onTimeUp?: () => void
  paused?: boolean
  onPauseToggle?: () => void
  showProgress?: boolean
  warningThresholds?: WarningThresholds
}

// Default warning thresholds factory - prevents object recreation
const getDefaultThresholds = (totalTime: number): WarningThresholds => ({
  halfway: Math.floor(totalTime / 2),
  final: 300, // 5 dakika
  critical: 60, // 1 dakika
});

/**
 * Süreyi formatla - pure function, defined outside component
 */
const formatTime = (seconds: number): { hours: number; minutes: number; secs: number; formatted: string } => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  let formatted = '';
  if (hours > 0) {
    formatted = `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    formatted = `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  return { hours, minutes, secs, formatted };
};

export const ExamTimer: React.FC<ExamTimerProps> = ({
  totalTimeSeconds,
  remainingTimeSeconds,
  onTimeUpdate,
  onTimeWarning,
  onTimeUp,
  paused = false,
  onPauseToggle,
  showProgress = true,
  warningThresholds,
}) => {
  // Memoized warning thresholds to prevent object recreation
  const thresholds = useMemo(
    () => warningThresholds || getDefaultThresholds(totalTimeSeconds),
    [warningThresholds, totalTimeSeconds],
  );
  const [localTime, setLocalTime] = useState(remainingTimeSeconds);
  const [isVisible, setIsVisible] = useState(true);
  const [showWarningDialog, setShowWarningDialog] = useState(false);
  const [warningMessage, setWarningMessage] = useState('');
  const [warningType, setWarningType] = useState<'info' | 'warning' | 'error'>('info');
  const [hasShownWarnings, setHasShownWarnings] = useState({
    halfway: false,
    final: false,
    critical: false,
  });

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  /**
   * Ses efektleri için audio element oluştur
   */
  useEffect(() => {
    // Basit beep sesi oluştur
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

    const createBeep = (frequency: number, duration: number) => {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + duration);
    };

    audioRef.current = {
      play: () => createBeep(800, 0.2),
    } as any;

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  /**
   * Timer'ı başlat/durdur
   */
  useEffect(() => {
    if (!paused && localTime > 0) {
      timerRef.current = setInterval(() => {
        setLocalTime(prev => {
          const newTime = prev - 1;

          // Parent component'e bildir
          if (onTimeUpdate) {
            onTimeUpdate(newTime);
          }

          // Uyarıları kontrol et
          checkWarnings(newTime);

          // Süre bitti
          if (newTime <= 0) {
            if (onTimeUp) {
              onTimeUp();
            }
            return 0;
          }

          return newTime;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [paused, localTime, onTimeUpdate, onTimeUp]);

  /**
   * Prop'tan gelen süre değişikliklerini takip et
   */
  useEffect(() => {
    setLocalTime(remainingTimeSeconds);
  }, [remainingTimeSeconds]);

  /**
   * Uyarıları kontrol et
   */
  const checkWarnings = (timeLeft: number) => {
    if (thresholds.critical && timeLeft === thresholds.critical && !hasShownWarnings.critical) {
      showWarning('Dikkat! Sadece 1 dakikanız kaldı!', 'error', 'critical');
      setHasShownWarnings(prev => ({ ...prev, critical: true }));
      playWarningSound();
    } else if (thresholds.final && timeLeft === thresholds.final && !hasShownWarnings.final) {
      showWarning('Uyarı! 5 dakikanız kaldı. Lütfen cevaplarınızı kontrol edin.', 'warning', 'final');
      setHasShownWarnings(prev => ({ ...prev, final: true }));
      playWarningSound();
    } else if (thresholds.halfway && timeLeft === thresholds.halfway && !hasShownWarnings.halfway) {
      showWarning('Bilgi: Sınav sürenizin yarısı geçti.', 'info', 'halfway');
      setHasShownWarnings(prev => ({ ...prev, halfway: true }));
    }
  };

  /**
   * Uyarı göster
   */
  const showWarning = (message: string, type: 'info' | 'warning' | 'error', warningTypeKey: 'halfway' | 'final' | 'critical') => {
    setWarningMessage(message);
    setWarningType(type);
    setShowWarningDialog(true);

    if (onTimeWarning) {
      onTimeWarning(warningTypeKey);
    }
  };

  /**
   * Uyarı sesi çal
   */
  const playWarningSound = () => {
    if (audioRef.current && audioRef.current.play) {
      try {
        audioRef.current.play();
      } catch (error) {
      }
    }
  };

  /**
   * Süre durumunu belirle - memoized
   */
  const timeStatus = useMemo(() => {
    const percentage = (localTime / totalTimeSeconds) * 100;

    if (percentage <= 5) {return { color: 'error', status: 'critical' };}
    if (percentage <= 15) {return { color: 'warning', status: 'warning' };}
    if (percentage <= 50) {return { color: 'info', status: 'normal' };}
    return { color: 'success', status: 'good' };
  }, [localTime, totalTimeSeconds]);

  // Memoized values to prevent recalculation on each render
  const timeInfo = useMemo(() => formatTime(localTime), [localTime]);
  const progressPercentage = useMemo(
    () => (localTime / totalTimeSeconds) * 100,
    [localTime, totalTimeSeconds],
  );

  return (
    <>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
          >
            <Paper
              elevation={3}
              sx={{
                p: 2,
                bgcolor: timeStatus.status === 'critical' ? 'error.50' : 'background.paper',
                border: timeStatus.status === 'critical' ? 2 : 0,
                borderColor: 'error.main',
                animation: timeStatus.status === 'critical' ? 'pulse 1s infinite' : 'none',
                '@keyframes pulse': {
                  '0%': { boxShadow: '0 0 0 0 rgba(244, 67, 54, 0.7)' },
                  '70%': { boxShadow: '0 0 0 10px rgba(244, 67, 54, 0)' },
                  '100%': { boxShadow: '0 0 0 0 rgba(244, 67, 54, 0)' },
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Timer color={timeStatus.color as any} />
                  <Typography variant="h6" color={`${timeStatus.color}.main`}>
                    Kalan Süre
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  {onPauseToggle && (
                    <Tooltip title={paused ? 'Devam Et' : 'Duraklat'}>
                      <IconButton onClick={onPauseToggle} size="small">
                        {paused ? <PlayArrow /> : <Pause />}
                      </IconButton>
                    </Tooltip>
                  )}

                  <Tooltip title={isVisible ? 'Gizle' : 'Göster'}>
                    <IconButton onClick={() => setIsVisible(!isVisible)} size="small">
                      {isVisible ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <motion.div
                  animate={timeStatus.status === 'critical' ? { scale: [1, 1.05, 1] } : {}}
                  transition={{ duration: 1, repeat: timeStatus.status === 'critical' ? Infinity : 0 }}
                >
                  <Typography
                    variant="h3"
                    color={`${timeStatus.color}.main`}
                    fontFamily="monospace"
                    fontWeight="bold"
                  >
                    {timeInfo.formatted}
                  </Typography>
                </motion.div>

                {paused && (
                  <Chip
                    label="DURAKLATILDI"
                    color="warning"
                    size="small"
                    icon={<Pause />}
                    sx={{ mt: 1 }}
                  />
                )}
              </Box>

              {showProgress && (
                <Box sx={{ mb: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={progressPercentage}
                    color={timeStatus.color as any}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 4,
                        transition: 'transform 1s linear',
                      },
                    }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                    <Typography variant="caption" color="textSecondary">
                      Geçen: {formatTime(totalTimeSeconds - localTime).formatted}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      %{progressPercentage.toFixed(1)} kaldı
                    </Typography>
                  </Box>
                </Box>
              )}

              {/* Durum göstergeleri */}
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                {timeStatus.status === 'critical' && (
                  <Chip
                    label="KRİTİK SÜRE!"
                    color="error"
                    size="small"
                    icon={<Alarm />}
                  />
                )}
                {timeStatus.status === 'warning' && (
                  <Chip
                    label="DİKKAT!"
                    color="warning"
                    size="small"
                    icon={<Warning />}
                  />
                )}
                {timeInfo.hours > 0 && (
                  <Chip
                    label={`${timeInfo.hours} saat`}
                    variant="outlined"
                    size="small"
                    icon={<Schedule />}
                  />
                )}
              </Box>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Minimized view */}
      {!isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Chip
            icon={<Timer />}
            label={timeInfo.formatted}
            color={timeStatus.color as any}
            onClick={() => setIsVisible(true)}
            sx={{
              cursor: 'pointer',
              fontSize: '1rem',
              height: 40,
              animation: timeStatus.status === 'critical' ? 'pulse 1s infinite' : 'none',
            }}
          />
        </motion.div>
      )}

      {/* Uyarı Dialog */}
      <Dialog
        open={showWarningDialog}
        onClose={() => setShowWarningDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {warningType === 'error' && <Alarm color="error" />}
          {warningType === 'warning' && <Warning color="warning" />}
          {warningType === 'info' && <Timer color="info" />}
          Süre Uyarısı
        </DialogTitle>

        <DialogContent>
          <Alert severity={warningType} sx={{ mb: 2 }}>
            {warningMessage}
          </Alert>

          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h4" color={`${timeStatus.color}.main`} fontFamily="monospace">
              {timeInfo.formatted}
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Kalan süre
            </Typography>
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setShowWarningDialog(false)} variant="contained">
            Tamam
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ExamTimer;