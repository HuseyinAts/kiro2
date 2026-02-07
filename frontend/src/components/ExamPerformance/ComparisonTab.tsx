/**
 * Comparison Tab Component
 * Displays national comparison and ranking information
 */

import { Users } from 'lucide-react';
import * as React from 'react';

import type { ComparisonTabProps } from './types';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { examPerformanceService } from '@/services/examPerformanceService';

const ComparisonTab: React.FC<ComparisonTabProps> = ({
  studentScore,
  nationalAverage,
  percentile,
  rankingInfo,
}) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="h-5 w-5" />
          Performans Karsilastirmasi
        </CardTitle>
        <CardDescription>
          Puaninizin ulusal ortalamalarla karsilastirmasi
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Sizin Puaniniz</span>
            <span className="text-lg font-bold text-blue-600">
              {examPerformanceService.formatScore(studentScore)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Ulusal Ortalama</span>
            <span className="text-lg font-bold text-gray-600">
              {examPerformanceService.formatScore(nationalAverage)}
            </span>
          </div>

          <div className="relative">
            <Progress value={percentile} className="h-3" />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>%{rankingInfo.better_than_percent}</strong> ogrenciden daha
              iyi performans gosterdiniz
            </p>
            <p className="text-xs text-blue-600 mt-1">
              Tahmini siralama: {rankingInfo.estimated_rank.toLocaleString()} /{' '}
              {rankingInfo.total_participants.toLocaleString()}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ComparisonTab;
