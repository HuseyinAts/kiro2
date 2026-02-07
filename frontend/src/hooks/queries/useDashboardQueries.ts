/**
 * Dashboard-related React Query Hooks (EXAMPLE)
 *
 * Provides React Query hooks for dashboard data
 * NOTE: This is an example pattern. Uncomment and implement when dashboardService exists.
 */

import { useQuery } from 'react-query';

// import { dashboardService } from '../../services/dashboardService'
import { queryConfig } from '../../config/reactQuery';
import { useAuthStore } from '../../store';
import { queryKeys } from '../useQueryKeys';

/**
 * Query: Get dashboard stats (EXAMPLE)
 * TODO: Uncomment when dashboardService is implemented
 */
export const useDashboardStats = () => {
  const userId = useAuthStore((state) => state.user?.id);

  return useQuery(
    queryKeys.dashboard.stats(userId!),
    async () => {
      // const stats = await dashboardService.getStats(userId!)
      // return stats

      // Placeholder
      return {
        tamamlanan_dersler: 0,
        toplam_dersler: 0,
        tamamlanan_sinavlar: 0,
        ortalama_puan: 0,
      };
    },
    {
      enabled: !!userId,
      ...queryConfig.moderate,
    },
  );
};

/**
 * Query: Get recent activity (EXAMPLE)
 * TODO: Uncomment when dashboardService is implemented
 */
export const useRecentActivity = () => {
  const userId = useAuthStore((state) => state.user?.id);

  return useQuery(
    queryKeys.dashboard.recent(userId!),
    async () => {
      // const activity = await dashboardService.getRecentActivity(userId!)
      // return activity

      // Placeholder
      return [];
    },
    {
      enabled: !!userId,
      ...queryConfig.moderate,
    },
  );
};

/**
 * Query: Get notifications (EXAMPLE)
 * TODO: Uncomment when dashboardService is implemented
 */
export const useNotifications = () => {
  const userId = useAuthStore((state) => state.user?.id);

  return useQuery(
    queryKeys.dashboard.notifications(userId!),
    async () => {
      // const notifications = await dashboardService.getNotifications(userId!)
      // return notifications

      // Placeholder
      return [];
    },
    {
      enabled: !!userId,
      ...queryConfig.realtime,
      refetchInterval: 1000 * 60, // Refetch every minute
    },
  );
};
