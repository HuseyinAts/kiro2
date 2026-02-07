/**
 * Performance Metrics Component
 * Displays the 4 main metric cards for exam performance
 */

import {
  Clock,
  Target,
  CheckCircle,
  Award,
} from 'lucide-react';
import * as React from 'react';

import type { PerformanceMetricsProps } from './types';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { examPerformanceService } from '@/services/examPerformanceService';

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  netScore,
  rawScore,
  accuracyRate,
  correctAnswers,
  totalQuestions,
  averageResponseTime,
  percentile,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Net Puan Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Net Puan</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-blue-600">
            {examPerformanceService.formatScore(netScore)}
          </div>
          <p className="text-xs text-muted-foreground">
            Ham Puan: {examPerformanceService.formatScore(rawScore)}%
          </p>
        </CardContent>
      </Card>

      {/* Dogruluk Orani Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Dogruluk Orani</CardTitle>
          <CheckCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            %{accuracyRate.toFixed(1)}
          </div>
          <p className="text-xs text-muted-foreground">
            {correctAnswers}/{totalQuestions} dogru
          </p>
        </CardContent>
      </Card>

      {/* Ortalama Sure Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Ortalama Sure</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">
            {examPerformanceService.formatTime(averageResponseTime)}
          </div>
          <p className="text-xs text-muted-foreground">
            Soru basina ortalama
          </p>
        </CardContent>
      </Card>

      {/* Yuzdelik Dilim Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Yuzdelik Dilim</CardTitle>
          <Award className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-purple-600">
            {percentile !== undefined
              ? examPerformanceService.formatPercentile(percentile)
              : 'N/A'}
          </div>
          <p className="text-xs text-muted-foreground">
            Ulusal siralama
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default PerformanceMetrics;
