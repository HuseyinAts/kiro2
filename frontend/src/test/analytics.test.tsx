/**
 * Analytics Components Test
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { analyticsService } from '../services/analyticsService';
import { StudentAnalyticsDashboard, TeacherClassAnalytics, AdminSystemAnalytics } from '../components/Analytics';

// Mock the analytics service
vi.mock('../services/analyticsService', () => ({
  analyticsService: {
    getStudentAnalytics: vi.fn(),
    getClassAnalytics: vi.fn(),
    getAdminAnalytics: vi.fn(),
    formatDateRange: vi.fn(),
    getPerformanceColor: vi.fn(),
    getTrendIcon: vi.fn(),
    getLearningStyleColor: vi.fn(),
    exportToPdf: vi.fn(),
    exportToExcel: vi.fn(),
    exportToCsv: vi.fn(),
    downloadExportFile: vi.fn()
  }
}));

// Mock data
const mockStudentAnalytics = {
  student_id: 'test_student',
  period: {
    start_date: '2024-01-01T00:00:00Z',
    end_date: '2024-01-31T00:00:00Z'
  },
  basic_metrics: {
    total_events: 100,
    aggregations: {}
  },
  performance_metrics: {
    total_study_time_hours: 45.5,
    total_questions_solved: 1247,
    correct_answers: 892,
    accuracy_rate: 0.715,
    average_session_duration_minutes: 28.3,
    improvement_trend: 'increasing',
    weak_subjects: ['Matematik', 'Fizik'],
    strong_subjects: ['Türkçe', 'Tarih'],
    study_consistency_score: 0.82
  },
  learning_style: {
    vark_profile: {
      visual: 0.7,
      auditory: 0.3,
      reading: 0.6,
      kinesthetic: 0.4
    },
    felder_silverman_profile: {
      active_reflective: 0.6,
      sensing_intuitive: 0.4,
      visual_verbal: 0.8,
      sequential_global: 0.5
    },
    hybrid_code: 'V-A-S-S',
    confidence_level: 0.85,
    recommendations: ['Görsel materyaller kullanın']
  },
  exam_performance: {
    total_exams: 12,
    average_score: 78.5,
    best_score: 92,
    worst_score: 65,
    improvement_rate: 0.15,
    exam_types: {
      TYT: { count: 8, average: 76.2 }
    },
    time_management: {
      average_completion_rate: 0.89,
      time_per_question_seconds: 45.2
    }
  },
  subject_analysis: {
    subjects: {
      Matematik: {
        accuracy_rate: 0.68,
        questions_solved: 245,
        time_spent_hours: 12.5,
        improvement_trend: 'stable',
        weak_topics: ['Türev'],
        strong_topics: ['Fonksiyonlar']
      }
    }
  }
};

const mockClassAnalytics = {
  class_id: 'test_class',
  period: {
    start_date: '2024-01-01T00:00:00Z',
    end_date: '2024-01-31T00:00:00Z'
  },
  student_count: 30,
  class_metrics: {
    average_study_time_hours: 38.2,
    total_questions_solved: 5847,
    class_accuracy_rate: 0.742,
    active_students_percentage: 0.89,
    improvement_rate: 0.12,
    engagement_score: 0.78
  },
  performance_distribution: {
    score_distribution: {
      '90-100': 2,
      '80-89': 8
    },
    performance_levels: {
      excellent: 2,
      good: 8
    }
  },
  subject_analysis: {
    subject_averages: {
      Matematik: 72.5,
      Türkçe: 78.9
    },
    challenging_topics: ['Matematik - Türev'],
    strong_topics: ['Türkçe - Anlam Bilgisi']
  },
  learning_style_distribution: {
    vark_distribution: {
      visual: 0.45,
      auditory: 0.25
    },
    felder_silverman_distribution: {
      active: 0.60,
      reflective: 0.40
    },
    hybrid_profiles: {
      'V-A-S-S': 8
    }
  }
};

const mockAdminAnalytics = {
  period: {
    start_date: '2024-01-01T00:00:00Z',
    end_date: '2024-01-31T00:00:00Z'
  },
  system_metrics: {
    total_active_users: 15247,
    total_sessions: 89456,
    average_session_duration_minutes: 32.5,
    total_questions_solved: 1247896,
    system_uptime_percentage: 99.7,
    api_response_time_ms: 145,
    error_rate_percentage: 0.3
  },
  user_statistics: {
    total_users: 25847,
    new_registrations: 1247,
    active_users: 15896,
    user_types: {
      students: 22456,
      teachers: 2847
    },
    retention_rate: 0.78,
    churn_rate: 0.05
  },
  exam_statistics: {
    total_exams_taken: 45896,
    exam_types: {
      TYT: 28456,
      AYT: 12847
    },
    average_scores: {
      TYT: 76.8,
      AYT: 72.3
    },
    completion_rates: {
      TYT: 0.89,
      AYT: 0.85
    }
  },
  content_usage: {
    total_content_views: 189456,
    content_types: {
      videos: 78456,
      articles: 56789
    },
    popular_subjects: {
      Matematik: 45896,
      Türkçe: 38745
    },
    engagement_metrics: {
      average_view_duration_minutes: 8.5,
      bounce_rate: 0.25,
      completion_rate: 0.68
    }
  },
  performance_metrics: {
    api_metrics: {
      average_response_time_ms: 145,
      p95_response_time_ms: 289,
      p99_response_time_ms: 456,
      error_rate_percentage: 0.3,
      throughput_requests_per_second: 1247
    },
    database_metrics: {
      query_performance_ms: 23,
      connection_pool_usage: 0.65,
      slow_queries_count: 12
    },
    cache_metrics: {
      hit_rate_percentage: 89.5,
      miss_rate_percentage: 10.5,
      eviction_rate: 0.02
    }
  },
  revolutionary_features: {
    bionic_reading: {
      total_users: 8456,
      usage_sessions: 45896,
      effectiveness_score: 0.78,
      user_satisfaction: 0.85
    }
  }
};

describe('Analytics Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(analyticsService.formatDateRange).mockReturnValue({
      startDate: '2024-01-01T00:00:00Z',
      endDate: '2024-01-31T00:00:00Z'
    });
    
    vi.mocked(analyticsService.getPerformanceColor).mockReturnValue('text-green-600');
    vi.mocked(analyticsService.getTrendIcon).mockReturnValue('📈');
    vi.mocked(analyticsService.getLearningStyleColor).mockReturnValue('bg-blue-100 text-blue-800');
  });

  describe('StudentAnalyticsDashboard', () => {
    it('renders student analytics dashboard', async () => {
      vi.mocked(analyticsService.getStudentAnalytics).mockResolvedValue(mockStudentAnalytics);

      render(<StudentAnalyticsDashboard studentId="test_student" />);

      // Loading state
      expect(screen.getByText('Analytics yükleniyor...')).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Öğrenci Analytics')).toBeInTheDocument();
      });

      // Check if analytics service was called
      expect(analyticsService.getStudentAnalytics).toHaveBeenCalledWith(
        'test_student',
        '2024-01-01T00:00:00Z',
        '2024-01-31T00:00:00Z',
        false
      );

      // Check if performance metrics are displayed
      expect(screen.getByText('45.5h')).toBeInTheDocument(); // Study time
      expect(screen.getByText('1,247')).toBeInTheDocument(); // Questions solved
    });

    it('handles error state', async () => {
      vi.mocked(analyticsService.getStudentAnalytics).mockRejectedValue(
        new Error('Analytics yüklenemedi')
      );

      render(<StudentAnalyticsDashboard studentId="test_student" />);

      await waitFor(() => {
        expect(screen.getByText('Hata: Analytics yüklenemedi')).toBeInTheDocument();
      });
    });
  });

  describe('TeacherClassAnalytics', () => {
    it('renders teacher class analytics', async () => {
      vi.mocked(analyticsService.getClassAnalytics).mockResolvedValue(mockClassAnalytics);

      render(<TeacherClassAnalytics classId="test_class" />);

      // Loading state
      expect(screen.getByText('Sınıf analytics yükleniyor...')).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Sınıf Analytics')).toBeInTheDocument();
      });

      // Check if analytics service was called
      expect(analyticsService.getClassAnalytics).toHaveBeenCalledWith(
        'test_class',
        '2024-01-01T00:00:00Z',
        '2024-01-31T00:00:00Z',
        true
      );

      // Check if class metrics are displayed
      expect(screen.getByText('38.2h')).toBeInTheDocument(); // Average study time
      expect(screen.getByText('5,847')).toBeInTheDocument(); // Total questions
    });
  });

  describe('AdminSystemAnalytics', () => {
    it('renders admin system analytics', async () => {
      vi.mocked(analyticsService.getAdminAnalytics).mockResolvedValue(mockAdminAnalytics);

      render(<AdminSystemAnalytics />);

      // Loading state
      expect(screen.getByText('Sistem analytics yükleniyor...')).toBeInTheDocument();

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Sistem Analytics')).toBeInTheDocument();
      });

      // Check if analytics service was called
      expect(analyticsService.getAdminAnalytics).toHaveBeenCalledWith(
        '2024-01-01T00:00:00Z',
        '2024-01-31T00:00:00Z'
      );

      // Check if system metrics are displayed
      expect(screen.getByText('25,847')).toBeInTheDocument(); // Total users
      expect(screen.getByText('15,896')).toBeInTheDocument(); // Active users
    });
  });

  describe('Export Functionality', () => {
    it('handles PDF export', async () => {
      vi.mocked(analyticsService.getStudentAnalytics).mockResolvedValue(mockStudentAnalytics);
      vi.mocked(analyticsService.exportToPdf).mockResolvedValue({
        success: true,
        data: {
          pdf_content: 'mock_pdf_content',
          filename: 'analytics_student_20240101.pdf'
        },
        message: 'PDF export başarılı'
      });

      render(<StudentAnalyticsDashboard studentId="test_student" />);

      await waitFor(() => {
        expect(screen.getByText('Öğrenci Analytics')).toBeInTheDocument();
      });

      // Find and click PDF export button
      const pdfButton = screen.getByText('PDF');
      pdfButton.click();

      await waitFor(() => {
        expect(analyticsService.exportToPdf).toHaveBeenCalled();
      });
    });
  });
});