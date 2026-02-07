/**
 * Subject Analysis Component
 * Displays subject-based performance chart and detailed breakdown
 */

import { BarChart3 } from 'lucide-react';
import * as React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import type { SubjectAnalysisProps } from './types';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { examPerformanceService } from '@/services/examPerformanceService';

const SubjectAnalysis: React.FC<SubjectAnalysisProps> = ({
  subjectPerformances,
}) => {
  const getSuccessRateBadgeVariant = (rate: number) => {
    if (rate >= 75) {return 'default';}
    if (rate >= 60) {return 'secondary';}
    if (rate >= 40) {return 'outline';}
    return 'destructive';
  };

  return (
    <div className="space-y-6">
      {/* Konu Performanslari Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Konu Bazli Performans
          </CardTitle>
          <CardDescription>
            Her konudaki basari oraniniz ve detayli analiz
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={subjectPerformances}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="topic"
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis domain={[0, 100]} />
              <Tooltip
                formatter={(value: number) => [`%${value.toFixed(1)}`, 'Basari Orani']}
              />
              <Bar
                dataKey="success_rate"
                fill="#3b82f6"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Konu Detaylari */}
      <div className="grid gap-4">
        {subjectPerformances.map((subject, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{subject.topic}</CardTitle>
                <Badge variant={getSuccessRateBadgeVariant(subject.success_rate)}>
                  %{subject.success_rate.toFixed(1)}
                </Badge>
              </div>
              <CardDescription>{subject.subject}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Toplam</p>
                  <p className="text-lg font-bold">{subject.total_questions}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Dogru</p>
                  <p className="text-lg font-bold text-green-600">
                    {subject.correct_answers}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Yanlis</p>
                  <p className="text-lg font-bold text-red-600">
                    {subject.wrong_answers}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Bos</p>
                  <p className="text-lg font-bold text-gray-600">
                    {subject.empty_answers}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Net Puan:</span>
                  <span className="font-medium">{subject.net_score.toFixed(1)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Ortalama Sure:</span>
                  <span className="font-medium">
                    {examPerformanceService.formatTime(subject.average_response_time)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Ortalama Zorluk:</span>
                  <span className="font-medium">
                    {subject.average_difficulty.toFixed(2)}
                  </span>
                </div>
              </div>

              <Progress value={subject.success_rate} className="mt-4" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default SubjectAnalysis;
