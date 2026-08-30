import * as React from 'react';
import { useQuery } from 'react-query';
import { Brain, TrendingUp, RefreshCw, Sparkles } from 'lucide-react';
import { apiRequest } from '../../utils/apiHelpers';

interface GrowthMindsetData {
  type: 'improvement' | 'resilience' | 'habit' | 'neutral';
  title: string;
  message: string;
}

const GrowthMindsetCard: React.FC = () => {
  // 29 Agu 2026 (SS10.11 zinciri): eskiden localStorage.getItem('token') +
  // manuel `Authorization: Bearer` header kullaniyordu -- bu depo
  // apiClient.ts'de belgelendigi gibi ("No more localStorage token storage -
  // XSS attack surface eliminated.") httpOnly cookie tabanli auth'a
  // gecileli beri bu desen kullanilmiyor. Sayfadaki diger tum kartlarla
  // (SubjectThetaCards, StatsOverview, ...) ayni desene -- useQuery +
  // apiRequest (credentials: 'include') -- geciyoruz.
  const { data, isLoading: loading, isError } = useQuery<GrowthMindsetData>({
    queryKey: ['student-dashboard-growth-mindset'],
    queryFn: () => apiRequest<GrowthMindsetData>('/api/v1/student-dashboard/growth-mindset'),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  if (loading) {
    return (
      <div className="bg-white/50 animate-pulse rounded-xl p-6 h-32 flex items-center justify-center border border-gray-100 shadow-sm">
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (isError || !data) {
    return null; // Silent fail, don't show the card if it errors out
  }

  const getIcon = () => {
    switch (data.type) {
      case 'improvement':
        return <TrendingUp className="w-8 h-8 text-green-500" />;
      case 'resilience':
        return <RefreshCw className="w-8 h-8 text-blue-500" />;
      case 'habit':
        return <Sparkles className="w-8 h-8 text-yellow-500" />;
      default:
        return <Brain className="w-8 h-8 text-purple-500" />;
    }
  };

  const getTheme = () => {
    switch (data.type) {
      case 'improvement':
        return 'bg-green-50 border-green-100 text-green-900';
      case 'resilience':
        return 'bg-blue-50 border-blue-100 text-blue-900';
      case 'habit':
        return 'bg-yellow-50 border-yellow-100 text-yellow-900';
      default:
        return 'bg-purple-50 border-purple-100 text-purple-900';
    }
  };

  return (
    <div className={`rounded-xl p-6 flex items-start space-x-4 border shadow-sm transition-all duration-300 hover:shadow-md ${getTheme()}`}>
      <div className="p-2 bg-white rounded-lg shadow-sm">
        {getIcon()}
      </div>
      <div>
        <h3 className="font-semibold text-lg mb-1 tracking-tight">{data.title}</h3>
        <p className="opacity-90 leading-relaxed font-medium">
          {data.message}
        </p>
      </div>
    </div>
  );
};

export default GrowthMindsetCard;
