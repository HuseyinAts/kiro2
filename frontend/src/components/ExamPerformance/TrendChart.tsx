/**
 * Trend Chart Component
 * Displays improvement trend visualization over recent exams
 */

import { Activity } from 'lucide-react';
import * as React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import type { TrendChartProps } from './types';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { examPerformanceService } from '@/services/examPerformanceService';

const TrendChart: React.FC<TrendChartProps> = ({
  trend,
  improvementRate,
  consistency,
  recentScores,
  predictedScore,
}) => {
  const getTrendBadgeVariant = () => {
    if (trend === 'improving') {return 'default';}
    if (trend === 'stable') {return 'secondary';}
    return 'destructive';
  };

  const chartData = recentScores.map((score, index) => ({
    exam: `Sinav ${index + 1}`,
    score: score,
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Gelisim Trendi
          <Badge variant={getTrendBadgeVariant()}>
            {examPerformanceService.getTrendIcon(trend)}{' '}
            {examPerformanceService.getTrendLabel(trend)}
          </Badge>
        </CardTitle>
        <CardDescription>
          Son sinavlarinizdaki performans degisimi
        </CardDescription>
      </CardHeader>
      <CardContent>
        {recentScores.length > 1 ? (
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="exam" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-muted-foreground">Gelisim Orani</p>
                <p className="text-lg font-bold text-blue-600">
                  {improvementRate > 0 ? '+' : ''}
                  {improvementRate.toFixed(1)} puan
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Tutarlilik</p>
                <p className="text-lg font-bold text-green-600">
                  %{consistency.toFixed(1)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Sonraki Tahmin</p>
                <p className="text-lg font-bold text-purple-600">
                  {examPerformanceService.formatScore(predictedScore)}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Trend analizi icin daha fazla sinav verisi gerekiyor</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TrendChart;
