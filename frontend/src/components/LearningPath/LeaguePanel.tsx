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
  CircularProgress,
} from '@mui/material';
import {
  EmojiEvents,
  TrendingUp,
  TrendingDown,
  Person,
  Star,
} from '@mui/icons-material';
import { GlassCard } from '../ui/GlassCard';
import { apiRequest } from '../../utils/apiHelpers';

interface LeagueTier {
  id: string;
  name: string;
  /** Backend tier key (uppercase) */
  apiKey: string;
  minXP: number;
  maxXP: number;
  color: string;
  icon: string;
}

const LEAGUE_TIERS: LeagueTier[] = [
  { id: 'bronze',   name: 'Bronz',    apiKey: 'BRONZE',   minXP: 0,    maxXP: 499,      color: '#cd7f32', icon: '🥉' },
  { id: 'silver',   name: 'Gümüş',    apiKey: 'SILVER',   minXP: 500,  maxXP: 1499,     color: '#c0c0c0', icon: '🥈' },
  { id: 'gold',     name: 'Altın',    apiKey: 'GOLD',     minXP: 1500, maxXP: 3499,     color: '#ffd700', icon: '🥇' },
  { id: 'diamond',  name: 'Elmas',    apiKey: 'PLATINUM', minXP: 3500, maxXP: 7999,     color: '#b9f2ff', icon: '💎' },
  { id: 'champion', name: 'Şampiyon', apiKey: 'CHAMPION', minXP: 8000, maxXP: Infinity, color: '#8b5cf6', icon: '👑' },
];

// ---------------------------------------------------------------------------
// API response types (matches league_api.py)
// ---------------------------------------------------------------------------

interface APIStandingsEntry {
  student_id: string;
  display_name: string;
  xp: number;
  rank: number;
  is_self: boolean;
}

interface APIStandingsResponse {
  tier: string;
  rank: number;
  weekly_xp: number;
  total_in_tier: number;
  week_start: string;
  standings: APIStandingsEntry[];
}

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

interface LeaderboardEntry {
  rank: number;
  name: string;
  xp: number;
  isCurrentUser: boolean;
  trend: 'up' | 'down' | 'same';
}

interface LeaguePanelProps {
  /** Current user's weekly XP (overridden by API data when available) */
  weeklyXP?: number;
  /** Compact mode for header badge */
  compact?: boolean;
}

// ---------------------------------------------------------------------------
// Helper: map API tier key → LeagueTier object
// ---------------------------------------------------------------------------

function getTierByApiKey(apiKey: string): LeagueTier {
  const upper = apiKey.toUpperCase();
  return LEAGUE_TIERS.find(t => t.apiKey === upper) ?? LEAGUE_TIERS[0];
}

function getTierByXP(xp: number): LeagueTier {
  for (let i = LEAGUE_TIERS.length - 1; i >= 0; i--) {
    if (xp >= LEAGUE_TIERS[i].minXP) return LEAGUE_TIERS[i];
  }
  return LEAGUE_TIERS[0];
}

function getNextTier(tier: LeagueTier): LeagueTier | null {
  const idx = LEAGUE_TIERS.findIndex(t => t.id === tier.id);
  return idx >= 0 && idx < LEAGUE_TIERS.length - 1 ? LEAGUE_TIERS[idx + 1] : null;
}

// ---------------------------------------------------------------------------
// Map API standings → LeaderboardEntry[]
// ---------------------------------------------------------------------------

function mapStandings(standings: APIStandingsEntry[]): LeaderboardEntry[] {
  return standings.map(entry => ({
    rank: entry.rank,
    name: entry.is_self ? 'Sen' : entry.display_name,
    xp: entry.xp,
    isCurrentUser: entry.is_self,
    trend: 'same' as const,
  }));
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function LeaguePanel({ weeklyXP = 0, compact = false }: LeaguePanelProps) {
  const [xp, setXp] = useState(weeklyXP);
  const [tier, setTier] = useState<LeagueTier>(getTierByXP(weeklyXP));
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notInLeague, setNotInLeague] = useState(false);

  // Prop sync (only before API data arrives)
  useEffect(() => {
    if (loading) {
      setXp(weeklyXP);
      setTier(getTierByXP(weeklyXP));
    }
  }, [weeklyXP, loading]);

  // Fetch real league standings from API
  useEffect(() => {
    let cancelled = false;

    async function fetchStandings() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiRequest<APIStandingsResponse>('/api/v1/leagues/current');
        if (cancelled) return;

        const apiTier = getTierByApiKey(data.tier);
        setXp(data.weekly_xp);
        setTier(apiTier);

        if (data.standings && data.standings.length > 0) {
          setLeaderboard(mapStandings(data.standings));
          setNotInLeague(false);
        } else {
          // User exists in a league but tier has no other members yet
          setLeaderboard([]);
          setNotInLeague(false);
        }
      } catch {
        if (cancelled) return;
        // API unavailable — show empty state, keep prop XP
        setError('Lig verisi alınamadı');
        setNotInLeague(true);
        setLeaderboard([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchStandings();
    return () => { cancelled = true; };
  }, []);

  const nextTier = useMemo(() => getNextTier(tier), [tier]);

  const progressToNext = useMemo(() => {
    if (!nextTier) return 100;
    const range = nextTier.minXP - tier.minXP;
    if (range <= 0) return 100;
    return Math.min(100, Math.round(((xp - tier.minXP) / range) * 100));
  }, [xp, tier, nextTier]);

  // Compact badge for header — show tier from API or prop
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
        <Typography
          variant="h6"
          fontWeight={800}
          sx={{
            color: tier.id === 'silver' || tier.id === 'diamond'
              ? '#334155'
              : tier.color,
          }}
        >
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
                bgcolor: tier.id === 'silver' ? '#94a3b8' : tier.color,
              },
            }}
          />
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mt: 0.25, display: 'block', textAlign: 'right' }}
          >
            {Math.max(0, nextTier.minXP - xp)} XP kaldı
          </Typography>
        </Box>
      )}

      <Divider sx={{ my: 1.5 }} />

      {/* Leaderboard */}
      <Typography
        variant="subtitle2"
        fontWeight={700}
        sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.5 }}
      >
        <EmojiEvents sx={{ fontSize: 18, color: '#f59e0b' }} />
        Haftalık Sıralama
      </Typography>

      {/* Loading state */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
          <CircularProgress size={28} />
        </Box>
      )}

      {/* Error / not-in-league state */}
      {!loading && (error || notInLeague) && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {error ?? 'Henüz bir ligde değilsiniz.'}
          </Typography>
          <Typography variant="caption" color="text.disabled" sx={{ mt: 0.5, display: 'block' }}>
            İlk quiz'i tamamladığınızda Bronz Lig'e katılırsınız.
          </Typography>
        </Box>
      )}

      {/* Empty standings (in league, but no other members yet) */}
      {!loading && !error && !notInLeague && leaderboard.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Bu haftanın sıralaması henüz oluşmadı.
          </Typography>
        </Box>
      )}

      {/* Leaderboard entries */}
      {!loading && leaderboard.length > 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
          {leaderboard.slice(0, 10).map(entry => (
            <Box
              key={`${entry.rank}-${entry.name}`}
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

              <Avatar
                sx={{
                  width: 28,
                  height: 28,
                  bgcolor: entry.isCurrentUser ? '#6366f1' : '#e2e8f0',
                  fontSize: 14,
                }}
              >
                {entry.isCurrentUser
                  ? <Person sx={{ fontSize: 16 }} />
                  : <Star sx={{ fontSize: 14, color: '#94a3b8' }} />}
              </Avatar>

              <Typography
                variant="body2"
                fontWeight={entry.isCurrentUser ? 700 : 400}
                sx={{ flex: 1 }}
              >
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
      )}

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
