/**
 * DailyQuestPage -- /daily-quests
 * 3 gunluk gorev + bonus odul sistemi
 */
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress,
  LinearProgress, Stack, Typography,
} from '@mui/material';
import {
  CheckCircle, RadioButtonUnchecked, EmojiEvents, CardGiftcard,
  GpsFixed, Replay, SportsEsports, LocalFireDepartment, Explore, Quiz,
} from '@mui/icons-material';
import { apiRequest } from '../utils/apiHelpers';

interface Quest {
  id: number;
  quest_type: string;
  title: string;
  description: string | null;
  target_value: number;
  current_value: number;
  xp_reward: number;
  completed: boolean;
  completed_at: string | null;
  bonus_claimed: boolean;
}

interface QuestData {
  quests: Quest[];
  completed_count: number;
  total_count: number;
  all_completed: boolean;
  bonus_available: boolean;
  bonus_xp: number;
}

const QUEST_ICON: Record<string, React.ReactNode> = {
  cat_session: <GpsFixed fontSize="small" />,
  fsrs_review: <Replay fontSize="small" />,
  duel: <SportsEsports fontSize="small" />,
  streak_check: <LocalFireDepartment fontSize="small" />,
  realm_quest: <Explore fontSize="small" />,
  solve_10: <Quiz fontSize="small" />,
};

const QUEST_ROUTE: Record<string, string> = {
  cat_session: '/cat',
  fsrs_review: '/fsrs-review',
  duel: '/duel',
  streak_check: '/dashboard',
  realm_quest: '/realms',
  solve_10: '/cat',
};

export default function DailyQuestPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<QuestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [claiming, setClaiming] = useState(false);

  const fetchQuests = useCallback(async () => {
    try {
      const res = await apiRequest<{ success: boolean; data: QuestData }>('/api/v1/daily-quests/today');
      setData(res.data ?? res as unknown as QuestData);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchQuests(); }, [fetchQuests]);

  const claimBonus = async () => {
    setClaiming(true);
    try {
      await apiRequest('/api/v1/daily-quests/claim-bonus', { method: 'POST' });
      await fetchQuests();
    } catch (e) {
      setError(String(e));
    } finally {
      setClaiming(false);
    }
  };

  if (loading) return (
    <Box textAlign="center" py={8}>
      <CircularProgress size={52} />
      <Typography mt={2} color="text.secondary">Gorevler yukleniyor...</Typography>
    </Box>
  );

  if (error) return (
    <Box maxWidth={520} mx="auto" mt={4}>
      <Alert severity="error">{error}</Alert>
    </Box>
  );

  if (!data) return null;

  const progress = (data.completed_count / data.total_count) * 100;

  return (
    <Box maxWidth={600} mx="auto" py={3}>
      {/* Header */}
      <Stack direction="row" spacing={2} alignItems="center" mb={1}>
        <EmojiEvents color="primary" sx={{ fontSize: 36 }} />
        <Box flex={1}>
          <Typography variant="h5" fontWeight={800}>Gunluk Gorevler</Typography>
          <Typography variant="body2" color="text.secondary">
            3 gorevi tamamla, bonus XP kazan!
          </Typography>
        </Box>
        <Chip
          label={`${data.completed_count}/${data.total_count}`}
          color={data.all_completed ? 'success' : 'primary'}
          variant="filled"
        />
      </Stack>

      {/* Progress */}
      <LinearProgress
        variant="determinate" value={progress}
        color={data.all_completed ? 'success' : 'primary'}
        sx={{ height: 8, borderRadius: 4, mb: 3 }}
      />

      {/* Quest Cards */}
      <Stack spacing={2} mb={3}>
        {data.quests.map(q => (
          <Card
            key={q.id}
            variant="outlined"
            sx={{
              borderRadius: 2,
              borderColor: q.completed ? 'success.main' : 'divider',
              opacity: q.completed ? 0.85 : 1,
            }}
          >
            <CardContent sx={{ py: 2, px: 2.5, '&:last-child': { pb: 2 } }}>
              <Stack direction="row" spacing={2} alignItems="center">
                {/* Status icon */}
                <Box sx={{ color: q.completed ? 'success.main' : 'text.disabled' }}>
                  {q.completed ? <CheckCircle /> : <RadioButtonUnchecked />}
                </Box>

                {/* Quest info */}
                <Box flex={1}>
                  <Stack direction="row" spacing={1} alignItems="center" mb={0.5}>
                    {QUEST_ICON[q.quest_type] ?? <GpsFixed fontSize="small" />}
                    <Typography variant="subtitle2" fontWeight={700}>
                      {q.title}
                    </Typography>
                  </Stack>
                  {q.description && (
                    <Typography variant="caption" color="text.secondary" display="block" mb={0.5}>
                      {q.description}
                    </Typography>
                  )}

                  {/* Mini progress */}
                  {q.target_value > 1 && (
                    <Box>
                      <LinearProgress
                        variant="determinate"
                        value={Math.round((q.current_value / q.target_value) * 100)}
                        sx={{ height: 4, borderRadius: 2, mb: 0.5 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {q.current_value}/{q.target_value}
                      </Typography>
                    </Box>
                  )}
                </Box>

                {/* XP badge + action */}
                <Stack alignItems="flex-end" spacing={0.5}>
                  <Chip
                    size="small"
                    label={`+${q.xp_reward} XP`}
                    color={q.completed ? 'success' : 'default'}
                    variant={q.completed ? 'filled' : 'outlined'}
                  />
                  {!q.completed && (
                    <Button
                      size="small" variant="text"
                      onClick={() => navigate(QUEST_ROUTE[q.quest_type] ?? '/dashboard')}
                    >
                      Basla
                    </Button>
                  )}
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {/* Bonus Card */}
      <Card
        sx={{
          borderRadius: 3,
          background: data.bonus_available
            ? 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)'
            : data.all_completed
              ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
              : undefined,
          border: data.bonus_available ? 'none' : '1px solid',
          borderColor: 'divider',
        }}
      >
        <CardContent sx={{ textAlign: 'center', py: 3 }}>
          <CardGiftcard sx={{ fontSize: 40, mb: 1, color: data.bonus_available ? '#fff' : 'text.disabled' }} />
          {data.bonus_available ? (
            <>
              <Typography variant="h6" fontWeight={800} color="#fff" mb={1}>
                Bonus Hazir!
              </Typography>
              <Button
                variant="contained"
                sx={{ bgcolor: '#fff', color: '#f59e0b', fontWeight: 700, '&:hover': { bgcolor: '#fef3c7' } }}
                onClick={claimBonus}
                disabled={claiming}
              >
                +{data.bonus_xp} XP Al
              </Button>
            </>
          ) : data.all_completed ? (
            <>
              <Typography variant="h6" fontWeight={800} color="#fff" mb={0.5}>
                Tebrikler!
              </Typography>
              <Typography variant="body2" color="rgba(255,255,255,0.8)">
                Bugunku tum gorevler ve bonus tamamlandi.
              </Typography>
            </>
          ) : (
            <>
              <Typography variant="subtitle2" color="text.secondary" mb={0.5}>
                Gunluk Bonus
              </Typography>
              <Typography variant="body2" color="text.disabled">
                Tum gorevleri tamamlayinca +{data.bonus_xp} XP bonus kazan
              </Typography>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
