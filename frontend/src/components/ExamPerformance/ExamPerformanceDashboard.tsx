/**
 * Sinav Performans Analizi Dashboard - Orchestrator Component
 * Turkiye Universite Sinavlari Hazirlik Platformu
 *
 * Bu bilesen sinav performansinin detayli analizini orkestre eder:
 * - Genel performans metrikleri
 * - Konu bazli zayiflik analizi
 * - Calisma onerileri
 * - Ulusal ortalamalarla karsilastirma
 * - Gelisim trendi
 *
 * REFACTORED: 2025-01-25
 * Original: 878 lines -> Current: ~200 lines
 * Components extracted:
 * - PerformanceMetrics.tsx (metric cards)
 * - SubjectAnalysis.tsx (subject chart)
 * - WeaknessAnalysis.tsx (weakness cards)
 * - TrendChart.tsx (trend visualization)
 * - ComparisonTab.tsx (national comparison)
 * - TimeAnalysisTab.tsx (time usage)
 * - RecommendationsTab.tsx (study recommendations)
 */

import { AlertTriangle } from 'lucide-react';
import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';

import ComparisonTab from './ComparisonTab';
import PerformanceMetrics from './PerformanceMetrics';
import RecommendationsTab from './RecommendationsTab';
import SubjectAnalysis from './SubjectAnalysis';
import TimeAnalysisTab from './TimeAnalysisTab';
import TrendChart from './TrendChart';
import type { ExamPerformanceDashboardProps } from './types';
import WeaknessAnalysis from './WeaknessAnalysis';
import {
  examPerformanceService,
  DetailedPerformanceAnalysis,
} from '@/services/examPerformanceService';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

const ExamPerformanceDashboard: React.FC<ExamPerformanceDashboardProps> = ({
  examSessionId,
  onClose,
}) => {
  const [analysis, setAnalysis] = useState<DetailedPerformanceAnalysis | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const loadPerformanceAnalysis = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const analysisData = await examPerformanceService.getDetailedAnalysis(
        examSessionId,
        true,
      );

      setAnalysis(analysisData);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Bilinmeyen hata';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [examSessionId]);

  useEffect(() => {
    loadPerformanceAnalysis();
  }, [loadPerformanceAnalysis]);

  // Loading State
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Performans analizi yukleniyor...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Performans analizi yuklenirken hata olustu: {error}
          <Button
            variant="outline"
            size="sm"
            onClick={loadPerformanceAnalysis}
            className="ml-2"
          >
            Tekrar Dene
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  // No Data State
  if (!analysis) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Performans analizi verisi bulunamadi.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Sinav Performans Analizi
          </h1>
          <p className="text-gray-600 mt-1">
            {analysis.exam_type.toUpperCase()} Sinavi - Detayli Analiz ve Oneriler
          </p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Kapat
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Genel Bakis</TabsTrigger>
          <TabsTrigger value="subjects">Konu Analizi</TabsTrigger>
          <TabsTrigger value="weaknesses">Zayifliklar</TabsTrigger>
          <TabsTrigger value="recommendations">Oneriler</TabsTrigger>
          <TabsTrigger value="time">Zaman Analizi</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="space-y-6">
            <PerformanceMetrics
              netScore={analysis.overall_performance.net_score}
              rawScore={analysis.overall_performance.raw_score}
              accuracyRate={analysis.overall_performance.accuracy_rate}
              correctAnswers={analysis.overall_performance.correct_answers}
              totalQuestions={analysis.overall_performance.total_questions}
              averageResponseTime={
                analysis.overall_performance.average_response_time
              }
              percentile={analysis.performance_comparison?.percentile}
            />

            {analysis.performance_comparison && (
              <ComparisonTab
                studentScore={analysis.performance_comparison.student_score}
                nationalAverage={analysis.performance_comparison.national_average}
                percentile={analysis.performance_comparison.percentile}
                rankingInfo={analysis.performance_comparison.ranking_info}
              />
            )}

            <TrendChart
              trend={analysis.improvement_trends.trend}
              improvementRate={analysis.improvement_trends.improvement_rate}
              consistency={analysis.improvement_trends.consistency}
              recentScores={analysis.improvement_trends.recent_scores}
              predictedScore={analysis.next_exam_prediction.predicted_score}
            />
          </div>
        </TabsContent>

        {/* Subject Analysis Tab */}
        <TabsContent value="subjects" className="mt-6">
          <SubjectAnalysis
            subjectPerformances={analysis.subject_performances}
          />
        </TabsContent>

        {/* Weaknesses Tab */}
        <TabsContent value="weaknesses" className="mt-6">
          <WeaknessAnalysis weaknesses={analysis.weaknesses} />
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="mt-6">
          <RecommendationsTab recommendations={analysis.study_recommendations} />
        </TabsContent>

        {/* Time Analysis Tab */}
        <TabsContent value="time" className="mt-6">
          <TimeAnalysisTab timeAnalysis={analysis.time_analysis} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExamPerformanceDashboard;
