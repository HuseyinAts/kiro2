/**
 * Dashboard-related React Query hooks — `student-dashboard` API.
 */

import { useQuery } from 'react-query';

import { queryConfig } from '../../config/reactQuery';
import { dashboardService } from '../../services/dashboardService';
import { useAuthStore } from '../../store';
import { queryKeys } from '../useQueryKeys';

/**
 * Query: Get dashboard stats
 */
export const useDashboardStats = () => {
  const userId = useAuthStore((state) => state.user?.id);

  return useQuery(
    queryKeys.dashboard.stats(userId!),
    async () => {
      return dashboardService.getStats(userId!);
    },
    {
      enabled: !!userId,
      ...queryConfig.moderate,
    },
  );
};

/**
 * Query: Recent sınav geçmişi (aktivite özeti)
 */
export const useRecentActivity = () => {
  const userId = useAuthStore((state) => state.user?.id);

  return useQuery(
    queryKeys.dashboard.recent(userId!),
    async () => {
      return dashboardService.getRecentActivity(userId!);
    },
    {
      enabled: !!userId,
      ...queryConfig.moderate,
    },
  );
};

/**
 * Query: Bildirimler
 */
export const useNotifications = () => {
  const userId = useAuthStore((state) => state.user?.id);

  return useQuery(
    queryKeys.dashboard.notifications(userId!),
    async () => {
      return dashboardService.getNotifications(userId!);
    },
    {
      enabled: !!userId,
      ...queryConfig.realtime,
      refetchInterval: 1000 * 60, // Refetch every minute
    },
  );
};
