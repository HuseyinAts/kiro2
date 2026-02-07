/**
 * ExamPerformance Component Exports
 * Barrel file for exam performance dashboard components
 */

// Main dashboard component
export { default as ExamPerformanceDashboard } from './ExamPerformanceDashboard';
export { default } from './ExamPerformanceDashboard';

// Sub-components
export { default as PerformanceMetrics } from './PerformanceMetrics';
export { default as SubjectAnalysis } from './SubjectAnalysis';
export { default as WeaknessAnalysis } from './WeaknessAnalysis';
export { default as TrendChart } from './TrendChart';
export { default as ComparisonTab } from './ComparisonTab';
export { default as TimeAnalysisTab } from './TimeAnalysisTab';
export { default as RecommendationsTab } from './RecommendationsTab';

// Types
export type {
  ExamPerformanceDashboardProps,
  PerformanceMetricsProps,
  SubjectAnalysisProps,
  WeaknessAnalysisProps,
  TrendChartProps,
  ComparisonTabProps,
  TimeAnalysisTabProps,
  RecommendationsTabProps,
} from './types';

// Re-export service types for convenience
export type {
  DetailedPerformanceAnalysis,
  SubjectWeakness,
  StudyRecommendation,
  PerformanceComparison,
  TimeAnalysis,
  ImprovementTrends,
  NextExamPrediction,
} from '@/services/examPerformanceService';
