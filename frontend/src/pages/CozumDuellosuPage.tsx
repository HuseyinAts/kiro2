/**
 * CozumDuellosuPage -- /cozum-duellosu
 * Cozum Duellosu (Solution Duel) — F2
 * Refactored to August 2026 Ultra Premium aesthetic
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
  Psychology,
  AddModerator,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import type { DuelInfo, DuelSubmission } from '../services/socialService';
import { cozumDuellosu } from '../services/socialService';
import { GlassCard } from '../components/ui/GlassCard';
import modernColors from '../theme/modern-colors';
import { useSensoryFeedback } from '../hooks/useSensoryFeedback';

const SUBJECTS = [
  'matematik', 'fizik', 'kimya', 'biyoloji',
  'turkce', 'tarih', 'cografya', 'geometri',
];

const MotionBox = motion(Box);
const MotionCard = motion(Card);

export default function CozumDuellosuPage() {
  const { playSuccess, playHover, playClick, playError } = useSensoryFeedback();
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
      playSuccess();
      setMessage(res.message);
      if (res.data.matched) {
        const detail = await cozumDuellosu.getDuel(res.data.duel_id);
        setSelectedDuel(detail.data.duel);
        setSubmissions(detail.data.submissions);
      }
      fetchActive();
    } catch (e: unknown) {
      playError();
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  const handleViewDuel = async (duelId: string) => {
    setActing(true);
    try {
      const res = await cozumDuellosu.getDuel(duelId);
      playClick();
      setSelectedDuel(res.data.duel);
      setSubmissions(res.data.submissions);
      // Auto-scroll to selected duel slightly delayed for render
      setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100);
    } catch (e: unknown) {
      playError();
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  const handleSubmit = async () => {
    if (!selectedDuel || !solutionText.trim()) {return;}
    setActing(true);
    try {
      const res = await cozumDuellosu.submit(selectedDuel.id, { body: solutionText });
      playSuccess();
      setMessage(res.message);
      setSolutionText('');
      const detail = await cozumDuellosu.getDuel(selectedDuel.id);
      setSelectedDuel(detail.data.duel);
      setSubmissions(detail.data.submissions);
    } catch (e: unknown) {
      playError();
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  const handleVote = async (submissionId: string) => {
    if (!selectedDuel) {return;}
    setActing(true);
    try {
      const res = await cozumDuellosu.vote(selectedDuel.id, submissionId);
      playSuccess();
      setMessage(res.message);
      const detail = await cozumDuellosu.getDuel(selectedDuel.id);
      setSubmissions(detail.data.submissions);
    } catch (e: unknown) {
      playError();
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setActing(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="sm" sx={{ py: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
        <CircularProgress size={60} thickness={4} sx={{ color: modernColors.primary[500] }} />
        <Typography variant="h6" fontWeight={600} color="text.secondary">
          Düellolar Yükleniyor...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 4, md: 8 } }}>
      <Stack spacing={4}>
        {/* Header Section */}
        <MotionBox
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, type: 'spring' }}
        >
          <GlassCard sx={{ p: { xs: 3, md: 5 }, background: modernColors.gradients.sunset, color: 'white', position: 'relative', overflow: 'hidden' }}>
            {/* Background elements */}
            <Box sx={{ position: 'absolute', top: -50, right: -50, width: 250, height: 250, background: 'var(--k-surface)', borderRadius: '50%', filter: 'blur(40px)' }} />
            
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={3} alignItems="center">
              <Box sx={{ p: 2, borderRadius: '50%', background: 'var(--k-surface)', backdropFilter: 'blur(10px)' }}>
                <EmojiEvents sx={{ fontSize: 56, color: 'var(--k-surface)' }} />
              </Box>
              <Box textAlign={{ xs: 'center', md: 'left' }} zIndex={1}>
                <Typography variant="h3" fontWeight={800} letterSpacing={-1}>Çözüm Düellosu</Typography>
                <Typography variant="h6" fontWeight={400} sx={{ opacity: 0.9, mt: 1 }}>
                  Aynı soruyu çöz, topluluk oylasın. En iyi çözüm kazansın!
                </Typography>
              </Box>
            </Stack>
          </GlassCard>
        </MotionBox>

        <AnimatePresence>
          {error && (
            <MotionBox initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
              <Alert severity="error" onClose={() => setError('')} sx={{ borderRadius: 3, mb: 2 }}>{error}</Alert>
            </MotionBox>
          )}
          {message && (
            <MotionBox initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
              <Alert severity="success" onClose={() => setMessage('')} sx={{ borderRadius: 3, mb: 2 }}>{message}</Alert>
            </MotionBox>
          )}
        </AnimatePresence>

        <Stack direction={{ xs: 'column', lg: 'row' }} spacing={4} alignItems="flex-start">
          
          {/* Main Area: Create and Detail */}
          <Stack spacing={4} flex={2} width="100%">
            
            {/* Create Duel */}
            <MotionBox initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
              <GlassCard sx={{ p: 4 }}>
                <Typography variant="h5" fontWeight={700} gutterBottom sx={{ color: modernColors.primary[800], display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AddModerator sx={{ color: 'var(--k-coral)' }} /> Yeni Düello Başlat
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={3}>
                  Kendi becerini göstermek istediğin dersi seç ve rastgele bir soru üzerinde rakiplerini bekle.
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="center">
                  <FormControl fullWidth sx={{ maxWidth: 300 }}>
                    <InputLabel>Ders</InputLabel>
                    <Select value={subject} label="Ders" onChange={e => setSubject(e.target.value)} sx={{ borderRadius: 3 }}>
                      {SUBJECTS.map(s => <MenuItem key={s} value={s} sx={{ textTransform: 'capitalize' }}>{s}</MenuItem>)}
                    </Select>
                  </FormControl>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => { playClick(); handleCreate(); }}
                    onMouseEnter={playHover}
                    disabled={acting}
                    startIcon={acting ? <CircularProgress size={20} color="inherit" /> : <EmojiEvents />}
                    sx={{
                      borderRadius: 3,
                      px: 4,
                      py: 1.5,
                      background: modernColors.gradients.ocean,
                      boxShadow: '0 8px 16px var(--k-surface)',
                      fontWeight: 700,
                      '&:hover': { background: modernColors.gradients.ocean, filter: 'brightness(1.1)' }
                    }}
                  >
                    Meydan Oku
                  </Button>
                </Stack>
              </GlassCard>
            </MotionBox>

            {/* Selected Duel Detail */}
            <AnimatePresence mode="wait">
              {selectedDuel && (
                <MotionBox
                  key={selectedDuel.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ type: 'spring', damping: 25 }}
                >
                  <GlassCard sx={{ p: 4, borderLeft: `6px solid ${modernColors.primary[500]}` }}>
                    <Stack spacing={4}>
                      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems="center" gap={2}>
                        <Box>
                          <Typography variant="h5" fontWeight={800} color="text.primary">
                            <span style={{ textTransform: 'capitalize', color: modernColors.primary[600] }}>{selectedDuel.subject_area}</span> Düellosu
                          </Typography>
                          <Typography variant="caption" color="text.secondary">ID: {selectedDuel.id.substring(0,8)}...</Typography>
                        </Box>
                        <Chip
                          label={selectedDuel.status.toUpperCase()}
                          color={selectedDuel.status === 'voting' ? 'warning' : selectedDuel.status === 'active' ? 'success' : 'default'}
                          sx={{ fontWeight: 800, px: 2, py: 2.5, borderRadius: 2, fontSize: '1rem' }}
                        />
                      </Stack>

                      {/* Submissions List */}
                      <Box>
                        <Typography variant="h6" fontWeight={700} mb={2} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Psychology color="action" /> Çözümler
                        </Typography>
                        {submissions.length > 0 ? (
                          <Stack spacing={2}>
                            {submissions.map((s, index) => (
                              <MotionCard 
                                key={s.id} 
                                initial={{ opacity: 0, y: 10 }} 
                                animate={{ opacity: 1, y: 0 }} 
                                transition={{ delay: index * 0.1 }}
                                elevation={0} 
                                sx={{ p: 3, borderRadius: 3, border: '1px solid', borderColor: 'divider', background: 'var(--k-surface)' }}
                              >
                                <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems="flex-start" gap={2}>
                                  <Box sx={{ flex: 1 }}>
                                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{s.body}</Typography>
                                    <Box mt={2}>
                                      <Chip size="small" label={`${s.vote_count} Oy`} sx={{ background: modernColors.primary[50], color: modernColors.primary[700], fontWeight: 700 }} />
                                    </Box>
                                  </Box>
                                  {selectedDuel.status === 'voting' && (
                                    <Button
                                      variant="outlined"
                                      startIcon={<HowToVote />}
                                      onClick={() => handleVote(s.id)}
                                      disabled={acting}
                                      sx={{ borderRadius: 2, fontWeight: 700 }}
                                    >
                                      Buna Oy Ver
                                    </Button>
                                  )}
                                </Stack>
                              </MotionCard>
                            ))}
                          </Stack>
                        ) : (
                          <Box sx={{ textAlign: 'center', py: 4, background: 'var(--k-surface)', borderRadius: 3 }}>
                            <Typography variant="body1" color="text.secondary" fontWeight={500}>
                              Henüz kimse çözüm göndermedi. İlk çözen sen ol!
                            </Typography>
                          </Box>
                        )}
                      </Box>

                      {/* Submit solution */}
                      {selectedDuel.status === 'active' && (
                        <Box sx={{ mt: 2, p: 3, borderRadius: 4, background: modernColors.primary[50] }}>
                          <Typography variant="subtitle1" fontWeight={700} sx={{ color: 'var(--k-coral)' }} gutterBottom>Çözümünü Gönder</Typography>
                          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="flex-start">
                            <TextField
                              fullWidth
                              multiline
                              rows={3}
                              placeholder="Adım adım çözümünü buraya yaz..."
                              value={solutionText}
                              onChange={e => setSolutionText(e.target.value)}
                              sx={{ background: 'var(--k-surface)', borderRadius: 2 }}
                            />
                            <Button
                              variant="contained"
                              size="large"
                              onClick={handleSubmit}
                              disabled={acting || !solutionText.trim()}
                              sx={{ minWidth: 140, height: '100%', py: { sm: 4 }, borderRadius: 2, fontWeight: 800 }}
                              endIcon={<Send />}
                            >
                              GÖNDER
                            </Button>
                          </Stack>
                        </Box>
                      )}
                    </Stack>
                  </GlassCard>
                </MotionBox>
              )}
            </AnimatePresence>
          </Stack>

          {/* Sidebar: Active Duels List */}
          <Stack spacing={3} flex={1} width="100%">
            <Typography variant="h5" fontWeight={800} color="text.primary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              Oylama Bekleyenler 
              <Chip label={activeDuels.length} sx={{ bgcolor: 'var(--k-coral)', color: 'var(--k-surface)', fontWeight: 800 }} size="small" />
            </Typography>
            
            {activeDuels.length === 0 ? (
              <GlassCard sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary" fontWeight={500}>
                  Şu an oylama bekleyen aktif düello bulunmuyor.
                </Typography>
              </GlassCard>
            ) : (
              <Stack spacing={2}>
                {activeDuels.map((d, index) => (
                  <MotionBox 
                    key={d.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card 
                      variant="outlined" 
                      onClick={() => handleViewDuel(d.id)}
                      sx={{ 
                        cursor: 'pointer', 
                        borderRadius: 3, 
                        border: '1px solid transparent',
                        transition: 'all 0.2s',
                        background: selectedDuel?.id === d.id ? 'var(--k-surface)' : 'transparent',
                        borderColor: selectedDuel?.id === d.id ? modernColors.primary[200] : 'divider',
                        '&:hover': {
                          transform: 'translateY(-2px)',
                          boxShadow: '0 8px 24px rgba(0,0,0,0.06)',
                          borderColor: modernColors.primary[300]
                        }
                      }}
                    >
                      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
                        <Stack spacing={1}>
                          <Stack direction="row" justifyContent="space-between" alignItems="center">
                            <Typography variant="subtitle1" fontWeight={700} sx={{ textTransform: 'capitalize' }}>
                              {d.subject_area}
                            </Typography>
                            <Button size="small" variant={selectedDuel?.id === d.id ? 'contained' : 'outlined'} sx={{ borderRadius: 2 }}>
                              Katıl
                            </Button>
                          </Stack>
                          <Typography variant="caption" color="text.secondary" fontWeight={500}>
                            {d.voting_ends_at ? `Son Oylama: ${new Date(d.voting_ends_at).toLocaleDateString('tr-TR')}` : 'Oylama açık'}
                          </Typography>
                        </Stack>
                      </CardContent>
                    </Card>
                  </MotionBox>
                ))}
              </Stack>
            )}
          </Stack>
        </Stack>
      </Stack>
    </Container>
  );
}
