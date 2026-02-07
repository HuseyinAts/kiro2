/**
 * Exam Performance Dashboard Type Definitions
 * Re-exported from examPerformanceService for component usage
 */

// Re-export all types from service
export type {
  DetailedPerformanceAnalysis,
  SubjectWeakness,
  StudyRecommendation,
  PerformanceComparison,
  TimeAnalysis,
  ImprovementTrends,
  NextExamPrediction,
} from '@/services/examPerformanceService';

// Local component prop types
export interface ExamPerformanceDashboardProps {
  examSessionId: string;
  onClose?: () => void;
}

export interface PerformanceMetricsProps {
  netScore: number;
  rawScore: number;
  accuracyRate: number;
  correctAnswers: number;
  totalQuestions: number;
  averageResponseTime: number;
  percentile?: number;
}

export interface SubjectAnalysisProps {
  subjectPerformances: Array<{
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
}

export interface WeaknessAnalysisProps {
  weaknesses: Array<{
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
  }>;
}

export interface TrendChartProps {
  trend: 'improving' | 'stable' | 'declining' | 'insufficient_data';
  improvementRate: number;
  consistency: number;
  recentScores: number[];
  predictedScore: number;
}

export interface ComparisonTabProps {
  studentScore: number;
  nationalAverage: number;
  percentile: number;
  rankingInfo: {
    estimated_rank: number;
    total_participants: number;
    better_than_percent: number;
  };
}

export interface TimeAnalysisTabProps {
  timeAnalysis: {
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
  };
}

export interface RecommendationsTabProps {
  recommendations: Array<{
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
  }>;
}
