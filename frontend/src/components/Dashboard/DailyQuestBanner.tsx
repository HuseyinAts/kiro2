import { memo } from 'react';
import { Box, Container, Typography, Stack, LinearProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { DailyQuestSummary } from './types';

interface DailyQuestBannerProps {
  dailyQuests: DailyQuestSummary | null;
}

export const DailyQuestBanner = memo(({ dailyQuests }: DailyQuestBannerProps) => {
  const navigate = useNavigate();

  if (!dailyQuests) return null;

  return (
    <Container maxWidth="xl" sx={{ mt: 1, position: 'relative', zIndex: 1 }}>
      <Box
        onClick={() => navigate('/daily-quests')}
        sx={{
          background: dailyQuests.all_completed
            ? 'linear-gradient(135deg, var(--k-success) 0%, var(--k-success-2) 100%)'
            : 'linear-gradient(135deg, var(--k-coral) 0%, var(--k-coral-2) 100%)',
          borderRadius: '12px',
          px: 3, py: 1.5,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: '#fff',
          '&:hover': { opacity: 0.9 },
        }}
      >
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Typography fontWeight={700} fontSize={14}>
            {dailyQuests.all_completed ? 'Tum Gorevler Tamam!' : 'Gunluk Gorevler'}
          </Typography>
          <Typography fontSize={13} sx={{ opacity: 0.85 }}>
            {dailyQuests.completed_count}/{dailyQuests.total_count}
          </Typography>
          {dailyQuests.bonus_available && (
            <Typography fontSize={12} sx={{ bgcolor: 'rgba(255,255,255,0.25)', px: 1, borderRadius: 2, fontWeight: 700 }}>
              Bonus Hazir!
            </Typography>
          )}
        </Stack>
        <LinearProgress
          variant="determinate"
          value={(dailyQuests.completed_count / dailyQuests.total_count) * 100}
          sx={{
            width: 120, height: 6, borderRadius: 3, ml: 2,
            bgcolor: 'rgba(255,255,255,0.2)',
            '& .MuiLinearProgress-bar': { bgcolor: '#fff', borderRadius: 3 },
          }}
        />
      </Box>
    </Container>
  );
});

DailyQuestBanner.displayName = 'DailyQuestBanner';
