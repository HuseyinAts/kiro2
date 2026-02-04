/**
 * Sınav Performans Analizi Servisi
 * Türkiye Üniversite Sınavları Hazırlık Platformu
 * 
 * Bu servis sınav performans analizi API'si ile iletişim kurar:
 * - Detaylı performans analizi
 * - Konu bazlı zayıflık tespiti
 * - Çalışma önerileri
 * - Ulusal ortalamalarla karşılaştırma
 */

import { apiClient } from './apiClient';

// Type definitions
export interface SubjectWeakness {
  subject: string;
  topic: string;
  weakness_level: 'critical' | 'moderate' | 'minor';
  success_rate: number;
  total_questions: number;
  correct_answers: number;
  wrong_answers: number;
  empty_answers: number;
  average_response_time: number;
  difficulty_distribution: Record<string, number>;
  improvement_potential: number;
}

export interface StudyRecommendation {
  subject: string;
  topic: string;
  priority: 'urgent' | 'high' | 'medium' | 'low';
  recommended_study_hours: number;
  recommended_resources: Array<{
    type: string;
    title: string;
    source: string;
    duration_minutes?: number;
    question_count?: number;
    reading_time?: number;
    difficulty: string;
    url: string;
  }>;
  practice_question_count: number;
  difficulty_focus: 'easy' | 'medium' | 'hard';
  explanation: string;
}

export interface PerformanceComparison {
  student_score: number;
  class_average?: number;
  school_average?: number;
  national_average: number;
  percentile: number;
  ranking_info: {
    estimated_rank: number;
    total_participants: number;
    better_than_percent: number;
  };
}

export interface TimeAnalysis {
  total_duration_seconds: number;
  total_duration_minutes: number;
  exam_duration_minutes: number;
  time_utilization_percent: number;
  average_time_per_question: number;
  time_by_subject: Record<string, {
    average_time: number;
    question_count: number;
  }>;
  speed_analysis: {
    too_fast: number;
    optimal: number;
    too_slow: number;
  };
}

export interface ImprovementTrends {
  trend: 'improving' | 'stable' | 'declining' | 'insufficient_data';
  improvement_rate: number;
  consistency: number;
  recent_scores: number[];
  score_variance: number;
}

export interface NextExamPrediction {
  predicted_score: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  target_score: number;
  weeks_to_target?: number;
  probability_of_improvement: number;
}

export interface DetailedPerformanceAnalysis {
  exam_session_id: string;
  student_id: string;
  exam_type: string;
  overall_performance: {
    total_questions: number;
    correct_answers: number;
    wrong_answers: number;
    empty_answers: number;
    net_score: number;
    raw_score: number;
    answer_rate: number;
    accuracy_rate: number;
    average_response_time: number;
    estimated_ability: number;
    confidence_level: number;
  };
  subject_performances: Array<{
    subject: string;
    topic: string;
    total_questions: number;
    correct_answers: number;
    wrong_answers: number;
    empty_answers: number;
    success_rate: number;
    net_score: number;
    average_response_time: number;
    average_difficulty: number;
    difficulty_distribution: Record<string, number>;
  }>;
  weaknesses: SubjectWeakness[];
  study_recommendations: StudyRecommendation[];
  performance_comparison?: PerformanceComparison;
  time_analysis: TimeAnalysis;
  improvement_trends: ImprovementTrends;
  next_exam_prediction: NextExamPrediction;
}

class ExamPerformanceService {
  private baseUrl = '/api/v1/exam-performance';

  /**
   * Detaylı performans analizi getir
   */
  async getDetailedAnalysis(
    examSessionId: string,
    includeComparisons: boolean = true
  ): Promise<DetailedPerformanceAnalysis> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/${examSessionId}/detailed-analysis`,
        {
          params: { include_comparisons: includeComparisons }
        }
      );

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Performans analizi alınamadı');
      }
    } catch (error: any) {
      console.error('Detaylı performans analizi hatası:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Performans analizi sırasında bir hata oluştu'
      );
    }
  }

  /**
   * Konu bazlı zayıflık analizi getir
   */
  async getSubjectWeaknesses(examSessionId: string): Promise<SubjectWeakness[]> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/${examSessionId}/weaknesses`
      );

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Zayıflık analizi alınamadı');
      }
    } catch (error: any) {
      console.error('Zayıflık analizi hatası:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Zayıflık analizi sırasında bir hata oluştu'
      );
    }
  }

  /**
   * Çalışma önerileri getir
   */
  async getStudyRecommendations(examSessionId: string): Promise<StudyRecommendation[]> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/${examSessionId}/study-recommendations`
      );

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Çalışma önerileri alınamadı');
      }
    } catch (error: any) {
      console.error('Çalışma önerileri hatası:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Çalışma önerileri sırasında bir hata oluştu'
      );
    }
  }

  /**
   * Performans karşılaştırması getir
   */
  async getPerformanceComparison(examSessionId: string): Promise<PerformanceComparison> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/${examSessionId}/performance-comparison`
      );

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Performans karşılaştırması alınamadı');
      }
    } catch (error: any) {
      console.error('Performans karşılaştırması hatası:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Performans karşılaştırması sırasında bir hata oluştu'
      );
    }
  }

  /**
   * Öğrenci gelişim trendi getir
   */
  async getImprovementTrends(
    studentId: string,
    examType: 'TYT' | 'AYT' | 'YDT'
  ): Promise<ImprovementTrends> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/student/${studentId}/improvement-trends`,
        {
          params: { exam_type: examType }
        }
      );

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Gelişim trendi alınamadı');
      }
    } catch (error: any) {
      console.error('Gelişim trendi hatası:', error);
      throw new Error(
        error.response?.data?.detail || 
        error.message || 
        'Gelişim trendi sırasında bir hata oluştu'
      );
    }
  }

  /**
   * Zayıflık seviyesi rengini getir
   */
  getWeaknessLevelColor(level: string): string {
    switch (level) {
      case 'critical':
        return '#ef4444'; // red-500
      case 'moderate':
        return '#f59e0b'; // amber-500
      case 'minor':
        return '#eab308'; // yellow-500
      default:
        return '#6b7280'; // gray-500
    }
  }

  /**
   * Zayıflık seviyesi etiketini getir
   */
  getWeaknessLevelLabel(level: string): string {
    switch (level) {
      case 'critical':
        return 'Kritik';
      case 'moderate':
        return 'Orta';
      case 'minor':
        return 'Hafif';
      default:
        return 'Bilinmeyen';
    }
  }

  /**
   * Öncelik seviyesi rengini getir
   */
  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'urgent':
        return '#dc2626'; // red-600
      case 'high':
        return '#ea580c'; // orange-600
      case 'medium':
        return '#ca8a04'; // yellow-600
      case 'low':
        return '#16a34a'; // green-600
      default:
        return '#6b7280'; // gray-500
    }
  }

  /**
   * Öncelik seviyesi etiketini getir
   */
  getPriorityLabel(priority: string): string {
    switch (priority) {
      case 'urgent':
        return 'Acil';
      case 'high':
        return 'Yüksek';
      case 'medium':
        return 'Orta';
      case 'low':
        return 'Düşük';
      default:
        return 'Bilinmeyen';
    }
  }

  /**
   * Trend yönü ikonunu getir
   */
  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'improving':
        return '📈';
      case 'stable':
        return '➡️';
      case 'declining':
        return '📉';
      case 'insufficient_data':
        return '❓';
      default:
        return '❓';
    }
  }

  /**
   * Trend yönü etiketini getir
   */
  getTrendLabel(trend: string): string {
    switch (trend) {
      case 'improving':
        return 'Gelişen';
      case 'stable':
        return 'Durağan';
      case 'declining':
        return 'Gerileyen';
      case 'insufficient_data':
        return 'Yetersiz Veri';
      default:
        return 'Bilinmeyen';
    }
  }

  /**
   * Süreyi formatla (saniye -> dakika:saniye)
   */
  formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  /**
   * Yüzdelik dilimi formatla
   */
  formatPercentile(percentile: number): string {
    return `%${percentile.toFixed(1)}`;
  }

  /**
   * Puanı formatla
   */
  formatScore(score: number): string {
    return score.toFixed(1);
  }
}

// Singleton instance
export const examPerformanceService = new ExamPerformanceService();