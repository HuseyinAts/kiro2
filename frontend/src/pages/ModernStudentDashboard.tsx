/**
 * Modern Student Dashboard
 * Beautiful, functional dashboard with glassmorphism and modern design
 * REFACTORED: Split into micro-components with React.memo to prevent re-renders
 */

import * as React from 'react';
import { Box, Container } from '@mui/material';
import { useQuery } from 'react-query';
import SubjectThetaCards from '@/components/Dashboard/SubjectThetaCards';
import { ThemeSelector } from '@/kiro/components/ThemeSelector';
import { StaggerContainer } from '@/components/Animations/PageTransition';
import { apiRequest } from '@/utils/apiHelpers';

// Dashboard Micro-components
import { DashboardHeader } from '@/components/Dashboard/DashboardHeader';
import { GamificationBar } from '@/components/Dashboard/GamificationBar';
import { DailyQuestBanner } from '@/components/Dashboard/DailyQuestBanner';
import { StatsOverview } from '@/components/Dashboard/StatsOverview';
import { QuickActions } from '@/components/Dashboard/QuickActions';
import { RecentActivity } from '@/components/Dashboard/RecentActivity';
import { DashboardStats, GamificationProfile, DailyQuestSummary, RecentExam } from '@/components/Dashboard/types';

const DEFAULT_GAMIFICATION: GamificationProfile = {
  total_xp: 0,
  current_level: 1,
  xp_for_next_level: 500,
  streak: 0,
  streak_active_today: false,
  total_badges: 0,
  leaderboard_rank: null,
};

const DEFAULT_STATS: DashboardStats = {
  tamamlanan_dersler: 0,
  toplam_dersler: 0,
  tamamlanan_sinavlar: 0,
  ortalama_puan: 0,
  toplam_calisma_suresi: 0,
  haftalik_ilerleme: 0,
  gunluk_seri: 0,
  toplam_puan: 0,
  seviye: 1,
  deneyim: 0,
};

export const ModernStudentDashboard: React.FC = () => {
  // Use TanStack Query for optimal caching and state management (2026 Standard)
  const { data: statsData, isLoading: loadingStats } = useQuery({
    queryKey: ['student-dashboard-stats'],
    queryFn: async () => {
      const data = await apiRequest<DashboardStats>('/api/v1/student-dashboard/istatistikler');
      return data || DEFAULT_STATS;
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: examsData, isLoading: loadingExams } = useQuery({
    queryKey: ['student-dashboard-exams'],
    queryFn: async () => {
      const data = await apiRequest<RecentExam[]>('/api/v1/student-dashboard/sinav-gecmisi?limit=3');
      return Array.isArray(data) ? data : [];
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: gamificationData } = useQuery({
    queryKey: ['student-dashboard-gamification'],
    queryFn: async () => {
      const res = await apiRequest<{ success: boolean; data: Partial<GamificationProfile> }>('/api/v1/gamification/profile');
      return { ...DEFAULT_GAMIFICATION, ...(res.data ?? res) };
    },
    staleTime: 5 * 60 * 1000,
  });

  const { data: questsData } = useQuery({
    queryKey: ['student-dashboard-quests'],
    queryFn: async () => {
      const res = await apiRequest<{ success: boolean; data: DailyQuestSummary }>('/api/v1/daily-quests/today');
      return res.data ?? res;
    },
    staleTime: 5 * 60 * 1000,
  });

  const loading = loadingStats || loadingExams;
  const stats = statsData ?? DEFAULT_STATS;
  const recentExams = examsData ?? [];
  const gamification = gamificationData ?? DEFAULT_GAMIFICATION;
  const dailyQuests = (questsData && 'completed_count' in (questsData as any)) ? (questsData as DailyQuestSummary) : null;

  return (
    <Box sx={{ minHeight: '100vh', background: 'var(--k-bg)', color: 'var(--k-text)', pb: 8 }}>
      <Box sx={{ position: 'fixed', top: 32, right: 32, zIndex: 9999 }}>
        <ThemeSelector />
      </Box>
      <DashboardHeader stats={stats} loading={loading} />
      <GamificationBar gamification={gamification} />
      
      <Container maxWidth="xl">
        <DailyQuestBanner dailyQuests={dailyQuests} />
        <Box sx={{ mt: 6 }}>
          <StaggerContainer>
            <StatsOverview stats={stats} loading={loading} />
            <QuickActions />
            <RecentActivity recentExams={recentExams} loading={loading} />
          </StaggerContainer>
        </Box>

        <Box mt={4}>
          <SubjectThetaCards />
        </Box>
      </Container>
    </Box>
  );
};

export default ModernStudentDashboard;
