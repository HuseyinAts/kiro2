/**
 * LeaguePanel — Lig Sistemi (Duolingo XP ligleri modeli)
 *
 * Lig kademeleri: Bronz → Gümüş → Altın → Elmas → Şampiyon
 * Haftalık döngü, XP bazlı sıralama.
 *
 * SDT özerklik (g=0.638) + gamifikasyon (g=0.654)
 * Anti-pattern: ZPD doğru cevap 2x XP, kolay 1x → speed-running önleme
 */

import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Typography,
  Avatar,
  Chip,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  EmojiEvents,
  TrendingUp,
  TrendingDown,
  Person,
  Star,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';

interface LeagueTier {
  id: string;
  name: string;
  minXP: number;
  maxXP: number;
  color: string;
  icon: string;
}

const LEAGUE_TIERS: LeagueTier[] = [
  { id: 'bronze', name: 'Bronz', minXP: 0, maxXP: 499, color: '#cd7f32', icon: '🥉' },
  { id: 'silver', name: 'Gümüş', minXP: 500, maxXP: 1499, color: '#c0c0c0', icon: '🥈' },
  { id: 'gold', name: 'Altın', minXP: 1500, maxXP: 3499, color: '#ffd700', icon: '🥇' },
  { id: 'diamond', name: 'Elmas', minXP: 3500, maxXP: 7999, color: '#b9f2ff', icon: '💎' },
  { id: 'champion', name: 'Şampiyon', minXP: 8000, maxXP: Infinity, color: '#8b5cf6', icon: '👑' },
];

interface LeaderboardEntry {
  rank: number;
  name: string;
  xp: number;
  isCurrentUser: boolean;
  trend: 'up' | 'down' | 'same';
}

interface LeaguePanelProps {
  /** Current user's weekly XP */
  weeklyXP?: number;
  /** Compact mode for header badge */
  compact?: boolean;
}

function getCurrentTier(xp: number): LeagueTier {
  for (let i = LEAGUE_TIERS.length - 1; i >= 0; i--) {
    if (xp >= LEAGUE_TIERS[i].minXP) return LEAGUE_TIERS[i];
  }
  return LEAGUE_TIERS[0];
}

function getNextTier(xp: number): LeagueTier | null {
  const idx = LEAGUE_TIERS.findIndex(t => xp >= t.minXP && xp <= t.maxXP);
  return idx < LEAGUE_TIERS.length - 1 ? LEAGUE_TIERS[idx + 1] : null;
}

// Generate mock leaderboard for demo
function generateMockLeaderboard(userXP: number): LeaderboardEntry[] {
  const names = [
    'Ahmet Y.', 'Elif K.', 'Mehmet S.', 'Zeynep D.', 'Can T.',
    'Ayşe B.', 'Emre H.', 'Fatma C.', 'Burak A.', 'Selin M.',
  ];

  const entries: LeaderboardEntry[] = names.map((name, i) => ({
    rank: i + 1,
    name,
    xp: Math.max(0, userXP + Math.round((Math.random() - 0.5) * 200)),
    isCurrentUser: false,
    trend: (['up', 'down', 'same'] as const)[Math.floor(Math.random() * 3)],
  }));

  // Insert current user
  entries.push({
    rank: 0,
    name: 'Sen',
    xp: userXP,
    isCurrentUser: true,
    trend: 'up',
  });

  // Sort by XP desc and assign ranks
  entries.sort((a, b) => b.xp - a.xp);
  entries.forEach((e, i) => { e.rank = i + 1; });

  return entries;
}

export function LeaguePanel({ weeklyXP = 0, compact = false }: LeaguePanelProps) {
  const [xp, setXp] = useState(weeklyXP);

  useEffect(() => { setXp(weeklyXP); }, [weeklyXP]);

  const tier = useMemo(() => getCurrentTier(xp), [xp]);
  const nextTier = useMemo(() => getNextTier(xp), [xp]);
  const leaderboard = useMemo(() => generateMockLeaderboard(xp), [xp]);

  const progressToNext = nextTier
    ? Math.round(((xp - tier.minXP) / (nextTier.minXP - tier.minXP)) * 100)
    : 100;

  // Compact badge for header
  if (compact) {
    return (
      <Chip
        label={`${tier.icon} ${tier.name}`}
        size="small"
        sx={{
          fontWeight: 700,
          fontSize: 11,
          bgcolor: `${tier.color}20`,
          color: tier.id === 'diamond' || tier.id === 'silver' ? '#334155' : tier.color,
          borderColor: tier.color,
          borderWidth: 1,
          borderStyle: 'solid',
        }}
      />
    );
  }

  // Hafta sonu bilgisi
  const now = new Date();
  const daysUntilReset = (8 - now.getDay()) % 7 || 7;

  return (
    <GlassCard glassIntensity="light">
      {/* Tier header */}
      <Box sx={{ textAlign: 'center', mb: 2 }}>
        <Typography variant="h4" sx={{ mb: 0.5 }}>{tier.icon}</Typography>
        <Typography variant="h6" fontWeight={800} sx={{ color: tier.color === '#c0c0c0' || tier.color === '#b9f2ff' ? '#334155' : tier.color }}>
          {tier.name} Ligi
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {xp} XP · Reset: {daysUntilReset} gün
        </Typography>
      </Box>

      {/* Progress to next tier */}
      {nextTier && (
        <Box sx={{ mb: 2.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" fontWeight={600}>{tier.icon} {tier.name}</Typography>
            <Typography variant="caption" fontWeight={600}>{nextTier.icon} {nextTier.name}</Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progressToNext}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: 'rgba(0,0,0,0.06)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                bgcolor: tier.color === '#c0c0c0' ? '#94a3b8' : tier.color,
              },
            }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, display: 'block', textAlign: 'right' }}>
            {nextTier.minXP - xp} XP kaldı
          </Typography>
        </Box>
      )}

      <Divider sx={{ my: 1.5 }} />

      {/* Leaderboard */}
      <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <EmojiEvents sx={{ fontSize: 18, color: '#f59e0b' }} />
        Haftalık Sıralama
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
        {leaderboard.slice(0, 10).map(entry => (
          <Box
            key={entry.rank}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              p: 1,
              borderRadius: 1.5,
              bgcolor: entry.isCurrentUser ? '#6366f108' : 'transparent',
              borderWidth: entry.isCurrentUser ? 1.5 : 0,
              borderStyle: 'solid',
              borderColor: entry.isCurrentUser ? '#6366f1' : 'transparent',
            }}
          >
            <Typography
              variant="caption"
              fontWeight={800}
              sx={{
                width: 24,
                textAlign: 'center',
                color: entry.rank <= 3 ? '#f59e0b' : '#94a3b8',
              }}
            >
              {entry.rank <= 3 ? ['🥇', '🥈', '🥉'][entry.rank - 1] : entry.rank}
            </Typography>

            <Avatar sx={{
              width: 28,
              height: 28,
              bgcolor: entry.isCurrentUser ? '#6366f1' : '#e2e8f0',
              fontSize: 14,
            }}>
              {entry.isCurrentUser ? <Person sx={{ fontSize: 16 }} /> : <Star sx={{ fontSize: 14, color: '#94a3b8' }} />}
            </Avatar>

            <Typography variant="body2" fontWeight={entry.isCurrentUser ? 700 : 400} sx={{ flex: 1 }}>
              {entry.name}
            </Typography>

            {entry.trend === 'up' && <TrendingUp sx={{ fontSize: 14, color: '#22c55e' }} />}
            {entry.trend === 'down' && <TrendingDown sx={{ fontSize: 14, color: '#ef4444' }} />}

            <Typography variant="caption" fontWeight={700} color="text.secondary">
              {entry.xp}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Promotion/demotion zone */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
        <Chip
          icon={<TrendingUp sx={{ fontSize: 14 }} />}
          label="Üst 3 → Yükselme"
          size="small"
          sx={{ fontSize: 10, fontWeight: 600, bgcolor: '#22c55e10', color: '#22c55e' }}
        />
        <Chip
          icon={<TrendingDown sx={{ fontSize: 14 }} />}
          label="Alt 3 → Düşme"
          size="small"
          sx={{ fontSize: 10, fontWeight: 600, bgcolor: '#ef444410', color: '#ef4444' }}
        />
      </Box>
    </GlassCard>
  );
}

export default LeaguePanel;
