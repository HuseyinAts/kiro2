/**
 * Gamification Hooks - Task 91
 * Oyunlaştırma sistemi için React hooks
 *
 * Hooks:
 * - usePoints: Puan yönetimi
 * - useLevel: Seviye ve XP yönetimi
 * - useBadges: Rozet koleksiyonu yönetimi
 * - useLeaderboard: Liderlik tablosu yönetimi
 */
import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api/v1/gamification';
const api = axios.create({ withCredentials: true });

// ============================================================================
// Types
// ============================================================================

export interface Badge {
  badge_id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  points: number;
  earned_at?: string;
  auto_awarded?: boolean;
}

export interface BadgeProgress extends Badge {
  progress_percentage: number;
  criteria: Record<string, number>;
}

export interface LevelProgress {
  current_level: number;
  total_xp: number;
  xp_in_current_level: number;
  xp_needed_for_next: number;
  progress_percentage: number;
  next_level: number;
  next_milestone: number | null;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  score: number;
  level?: number;
  avatar_url?: string;
}

export interface UserRank {
  rank: number;
  score: number;
  total_users: number;
  percentile: number;
}

export interface GamificationStats {
  points: number;
  level: number;
  total_xp: number;
  level_progress: LevelProgress;
  total_badges: number;
  badges_by_rarity: Record<string, number>;
  leaderboard_rank: UserRank | null;
  recent_achievements: Badge[];
}

// ============================================================================
// usePoints Hook
// ============================================================================

export function usePoints() {
  const [points, setPoints] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPoints = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`${API_BASE}/points`);
      setPoints(response?.data?.total_points ?? 0);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const awardPoints = useCallback(async (amount: number, reason: string, metadata?: Record<string, unknown>) => {
    try {
      setLoading(true);
      const response = await api.post(`${API_BASE}/points/award`, {
        points: amount,
        reason,
        metadata,
      });
      setPoints(response?.data?.total_points ?? 0);
      setError(null);
      return response?.data;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getHistory = useCallback(async (limit = 50) => {
    try {
      setLoading(true);
      const response = await api.get(`${API_BASE}/points/history`, {
        params: { limit },
      });
      setError(null);
      return response.data;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPoints();
  }, [fetchPoints]);

  return {
    points,
    loading,
    error,
    refresh: fetchPoints,
    awardPoints,
    getHistory,
  };
}

// ============================================================================
// useLevel Hook
// ============================================================================

export function useLevel() {
  const [levelProgress, setLevelProgress] = useState<LevelProgress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLevelProgress = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`${API_BASE}/level/progress`);
      setLevelProgress(response.data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const getLevelLeaderboard = useCallback(async (limit = 100) => {
    try {
      const response = await api.get(`${API_BASE}/level/leaderboard`, {
        params: { limit },
      });
      return response.data as LeaderboardEntry[];
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      return [];
    }
  }, []);

  const getMilestones = useCallback(async () => {
    try {
      const response = await api.get(`${API_BASE}/level/milestones`);
      return response.data as number[];
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      return [];
    }
  }, []);

  useEffect(() => {
    fetchLevelProgress();
  }, [fetchLevelProgress]);

  return {
    levelProgress,
    loading,
    error,
    refresh: fetchLevelProgress,
    getLevelLeaderboard,
    getMilestones,
  };
}

// ============================================================================
// useBadges Hook
// ============================================================================

export function useBadges() {
  const [allBadges, setAllBadges] = useState<Badge[]>([]);
  const [earnedBadges, setEarnedBadges] = useState<Badge[]>([]);
  const [badgeProgress, setBadgeProgress] = useState<BadgeProgress[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAllBadges = useCallback(async () => {
    try {
      const response = await api.get(`${API_BASE}/badges`);
      setAllBadges(response.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  const fetchEarnedBadges = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`${API_BASE}/badges/earned`);
      setEarnedBadges(response.data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchBadgeProgress = useCallback(async () => {
    try {
      const response = await api.get(`${API_BASE}/badges/progress`);
      setBadgeProgress(response.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  const awardBadge = useCallback(async (badgeId: string) => {
    try {
      setLoading(true);
      const response = await api.post(`${API_BASE}/badges/${badgeId}/award`);
      await fetchEarnedBadges(); // Refresh earned badges
      setError(null);
      return response.data;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchEarnedBadges]);

  useEffect(() => {
    fetchAllBadges();
    fetchEarnedBadges();
    fetchBadgeProgress();
  }, [fetchAllBadges, fetchEarnedBadges, fetchBadgeProgress]);

  return {
    allBadges,
    earnedBadges,
    badgeProgress,
    loading,
    error,
    refresh: fetchEarnedBadges,
    awardBadge,
  };
}

// ============================================================================
// useLeaderboard Hook
// ============================================================================

export function useLeaderboard(type: 'global' | 'weekly' | 'monthly' = 'global') {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLeaderboard = useCallback(async (limit = 100, offset = 0) => {
    try {
      setLoading(true);
      const endpoint = `${API_BASE}/leaderboard/${type}`;
      const response = await api.get(endpoint, {
        params: { limit, offset },
      });
      setLeaderboard(response.data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [type]);

  const getNearbyUsers = useCallback(async (rangeSize = 5) => {
    try {
      const response = await api.get(`${API_BASE}/leaderboard/nearby`, {
        params: { range_size: rangeSize },
      });
      return response.data;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      return { user: null, above: [], below: [] };
    }
  }, []);

  const syncLeaderboard = useCallback(async () => {
    try {
      setLoading(true);
      await api.post(`${API_BASE}/leaderboard/sync`);
      await fetchLeaderboard();
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchLeaderboard]);

  useEffect(() => {
    fetchLeaderboard();
  }, [fetchLeaderboard]);

  return {
    leaderboard,
    loading,
    error,
    refresh: fetchLeaderboard,
    getNearbyUsers,
    syncLeaderboard,
  };
}

// ============================================================================
// useGamificationStats Hook
// ============================================================================

export function useGamificationStats() {
  const [stats, setStats] = useState<GamificationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get(`${API_BASE}/stats`);
      setStats(response.data);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats,
    loading,
    error,
    refresh: fetchStats,
  };
}

// ============================================================================
// Combined Hook
// ============================================================================

export function useGamification() {
  const points = usePoints();
  const level = useLevel();
  const badges = useBadges();
  const leaderboard = useLeaderboard();
  const stats = useGamificationStats();

  return {
    points,
    level,
    badges,
    leaderboard,
    stats,
  };
}
