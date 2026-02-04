/**
 * Analytics Service
 * Advanced analytics ve reporting servisleri
 */

import { apiClient } from './apiClient';

// Analytics veri tipleri
export interface StudentAnalytics {
  student_id: string;
  period: {
    start_date: string;
    end_date: string;
  };
  basic_metrics: {
    total_events: number;
    aggregations: any;
  };
  performance_metrics: {
    total_study_time_hours: number;
    total_questions_solved: number;
    correct_answers: number;
    accuracy_rate: number;
    average_session_duration_minutes: number;
    improvement_trend: string;
    weak_subjects: string[];
    strong_subjects: string[];
    study_consistency_score: number;
  };
  learning_style: {
    vark_profile: {
      visual: number;
      auditory: number;
      reading: number;
      kinesthetic: number;
    };
    felder_silverman_profile: {
      active_reflective: number;
      sensing_intuitive: number;
      visual_verbal: number;
      sequential_global: number;
    };
    hybrid_code: string;
    confidence_level: number;
    recommendations: string[];
  };
  exam_performance: {
    total_exams: number;
    average_score: number;
    best_score: number;
    worst_score: number;
    improvement_rate: number;
    exam_types: Record<string, { count: number; average: number }>;
    time_management: {
      average_completion_rate: number;
      time_per_question_seconds: number;
    };
  };
  subject_analysis: {
    subjects: Record<string, {
      accuracy_rate: number;
      questions_solved: number;
      time_spent_hours: number;
      improvement_trend: string;
      weak_topics: string[];
      strong_topics: string[];
    }>;
  };
  detailed_analysis?: {
    study_patterns: {
      preferred_study_hours: string[];
      most_active_days: string[];
      session_frequency: string;
      break_patterns: string;
    };
    motivation_analysis: {
      motivation_score: number;
      engagement_level: string;
      challenge_preference: string;
      feedback_responsiveness: number;
    };
    revolutionary_features_usage: Record<string, {
      usage_rate: number;
      effectiveness?: number;
      retention_improvement?: number;
      comprehension_improvement?: number;
      learning_efficiency?: number;
    }>;
  };
}

export interface ClassAnalytics {
  class_id: string;
  period: {
    start_date: string;
    end_date: string;
  };
  student_count: number;
  class_metrics: {
    average_study_time_hours: number;
    total_questions_solved: number;
    class_accuracy_rate: number;
    active_students_percentage: number;
    improvement_rate: number;
    engagement_score: number;
  };
  performance_distribution: {
    score_distribution: Record<string, number>;
    performance_levels: Record<string, number>;
  };
  subject_analysis: {
    subject_averages: Record<string, number>;
    challenging_topics: string[];
    strong_topics: string[];
  };
  learning_style_distribution: {
    vark_distribution: Record<string, number>;
    felder_silverman_distribution: Record<string, number>;
    hybrid_profiles: Record<string, number>;
  };
  student_details?: Array<{
    student_id: string;
    name: string;
    analytics: any;
  }>;
}

export interface AdminAnalytics {
  period: {
    start_date: string;
    end_date: string;
  };
  system_metrics: {
    total_active_users: number;
    total_sessions: number;
    average_session_duration_minutes: number;
    total_questions_solved: number;
    system_uptime_percentage: number;
    api_response_time_ms: number;
    error_rate_percentage: number;
  };
  user_statistics: {
    total_users: number;
    new_registrations: number;
    active_users: number;
    user_types: Record<string, number>;
    retention_rate: number;
    churn_rate: number;
  };
  exam_statistics: {
    total_exams_taken: number;
    exam_types: Record<string, number>;
    average_scores: Record<string, number>;
    completion_rates: Record<string, number>;
  };
  content_usage: {
    total_content_views: number;
    content_types: Record<string, number>;
    popular_subjects: Record<string, number>;
    engagement_metrics: {
      average_view_duration_minutes: number;
      bounce_rate: number;
      completion_rate: number;
    };
  };
  performance_metrics: {
    api_metrics: {
      average_response_time_ms: number;
      p95_response_time_ms: number;
      p99_response_time_ms: number;
      error_rate_percentage: number;
      throughput_requests_per_second: number;
    };
    database_metrics: {
      query_performance_ms: number;
      connection_pool_usage: number;
      slow_queries_count: number;
    };
    cache_metrics: {
      hit_rate_percentage: number;
      miss_rate_percentage: number;
      eviction_rate: number;
    };
  };
  revolutionary_features: Record<string, {
    total_users: number;
    usage_sessions?: number;
    effectiveness_score?: number;
    user_satisfaction: number;
    cards_reviewed?: number;
    retention_improvement?: number;
    texts_simplified?: number;
    comprehension_improvement?: number;
    coordination_events?: number;
    learning_efficiency_improvement?: number;
    profiles_generated?: number;
    accuracy_rate?: number;
    personalization_effectiveness?: number;
    assessments_completed?: number;
    cultural_adaptation_score?: number;
    learning_optimization?: number;
    questions_analyzed?: number;
    difficulty_accuracy?: number;
    osym_standard_improvement?: number;
  }>;
}

export interface ExportRequest {
  format: 'pdf' | 'excel' | 'csv';
  data_type: 'student' | 'class' | 'admin';
  filters: Record<string, any>;
}

export interface ExportResponse {
  success: boolean;
  data: {
    pdf_content?: string;
    excel_content?: string;
    csv_content?: string;
    filename: string;
  };
  message: string;
}

class AnalyticsService {
  private baseUrl = '/api/v1/analytics';

  /**
   * Öğrenci analytics verilerini getir
   */
  async getStudentAnalytics(
    studentId: string,
    startDate?: string,
    endDate?: string,
    includeDetailed: boolean = false
  ): Promise<StudentAnalytics> {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (includeDetailed) params.append('include_detailed', 'true');

      const response = await apiClient.get<{
        success: boolean;
        data: StudentAnalytics;
        message: string;
      }>(`${this.baseUrl}/student/${studentId}?${params.toString()}`);

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Öğrenci analytics alınamadı');
      }
    } catch (error) {
      console.error('Student analytics error:', error);
      throw error;
    }
  }

  /**
   * Sınıf analytics verilerini getir
   */
  async getClassAnalytics(
    classId: string,
    startDate?: string,
    endDate?: string,
    includeStudents: boolean = true
  ): Promise<ClassAnalytics> {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (includeStudents) params.append('include_students', 'true');

      const response = await apiClient.get<{
        success: boolean;
        data: ClassAnalytics;
        message: string;
      }>(`${this.baseUrl}/class/${classId}?${params.toString()}`);

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Sınıf analytics alınamadı');
      }
    } catch (error) {
      console.error('Class analytics error:', error);
      throw error;
    }
  }

  /**
   * Admin dashboard analytics verilerini getir
   */
  async getAdminAnalytics(
    startDate?: string,
    endDate?: string
  ): Promise<AdminAnalytics> {
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await apiClient.get<{
        success: boolean;
        data: AdminAnalytics;
        message: string;
      }>(`${this.baseUrl}/admin/dashboard?${params.toString()}`);

      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || 'Admin analytics alınamadı');
      }
    } catch (error) {
      console.error('Admin analytics error:', error);
      throw error;
    }
  }

  /**
   * Analytics verilerini PDF olarak export et
   */
  async exportToPdf(request: ExportRequest): Promise<ExportResponse> {
    try {
      const response = await apiClient.post<ExportResponse>(
        `${this.baseUrl}/export/pdf`,
        request
      );

      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.message || 'PDF export başarısız');
      }
    } catch (error) {
      console.error('PDF export error:', error);
      throw error;
    }
  }

  /**
   * Analytics verilerini Excel olarak export et
   */
  async exportToExcel(request: ExportRequest): Promise<ExportResponse> {
    try {
      const response = await apiClient.post<ExportResponse>(
        `${this.baseUrl}/export/excel`,
        request
      );

      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.message || 'Excel export başarısız');
      }
    } catch (error) {
      console.error('Excel export error:', error);
      throw error;
    }
  }

  /**
   * Analytics verilerini CSV olarak export et
   */
  async exportToCsv(request: ExportRequest): Promise<ExportResponse> {
    try {
      const response = await apiClient.post<ExportResponse>(
        `${this.baseUrl}/export/csv`,
        request
      );

      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.message || 'CSV export başarısız');
      }
    } catch (error) {
      console.error('CSV export error:', error);
      throw error;
    }
  }

  /**
   * Export dosyasını indir
   */
  downloadExportFile(content: string, filename: string, format: 'pdf' | 'excel' | 'csv') {
    try {
      let blob: Blob;

      if (format === 'pdf') {
        // Hex string'i binary'ye çevir
        const binaryString = content.match(/.{1,2}/g)?.map(byte => 
          String.fromCharCode(parseInt(byte, 16))
        ).join('') || '';
        blob = new Blob([binaryString], { type: 'application/pdf' });
      } else if (format === 'excel') {
        // Hex string'i binary'ye çevir
        const binaryString = content.match(/.{1,2}/g)?.map(byte => 
          String.fromCharCode(parseInt(byte, 16))
        ).join('') || '';
        blob = new Blob([binaryString], { 
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
      } else {
        // CSV
        blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
      }

      // Dosyayı indir
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }

  /**
   * Tarih aralığı formatla
   */
  formatDateRange(days: number = 30): { startDate: string; endDate: string } {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    return {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString()
    };
  }

  /**
   * Performans metriklerini renklendir
   */
  getPerformanceColor(value: number, type: 'percentage' | 'score' | 'time'): string {
    if (type === 'percentage') {
      if (value >= 80) return 'text-green-600';
      if (value >= 60) return 'text-yellow-600';
      return 'text-red-600';
    } else if (type === 'score') {
      if (value >= 80) return 'text-green-600';
      if (value >= 60) return 'text-yellow-600';
      return 'text-red-600';
    } else if (type === 'time') {
      if (value <= 200) return 'text-green-600';
      if (value <= 500) return 'text-yellow-600';
      return 'text-red-600';
    }
    return 'text-gray-600';
  }

  /**
   * Trend ikonunu getir
   */
  getTrendIcon(trend: string): string {
    switch (trend) {
      case 'increasing':
        return '📈';
      case 'decreasing':
        return '📉';
      case 'stable':
        return '➡️';
      default:
        return '📊';
    }
  }

  /**
   * Öğrenme stili rengini getir
   */
  getLearningStyleColor(style: string): string {
    const colors: Record<string, string> = {
      'visual': 'bg-blue-100 text-blue-800',
      'auditory': 'bg-green-100 text-green-800',
      'reading': 'bg-purple-100 text-purple-800',
      'kinesthetic': 'bg-orange-100 text-orange-800',
      'active': 'bg-red-100 text-red-800',
      'reflective': 'bg-indigo-100 text-indigo-800',
      'sensing': 'bg-yellow-100 text-yellow-800',
      'intuitive': 'bg-pink-100 text-pink-800',
      'sequential': 'bg-teal-100 text-teal-800',
      'global': 'bg-gray-100 text-gray-800'
    };
    return colors[style.toLowerCase()] || 'bg-gray-100 text-gray-800';
  }
}

export const analyticsService = new AnalyticsService();
export default analyticsService;