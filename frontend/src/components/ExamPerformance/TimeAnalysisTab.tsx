/**
 * Time Analysis Tab Component
 * Displays detailed time usage analysis during exam
 */

import { Clock } from 'lucide-react';
import * as React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
} from 'recharts';

import type { TimeAnalysisTabProps } from './types';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { examPerformanceService } from '@/services/examPerformanceService';

const TimeAnalysisTab: React.FC<TimeAnalysisTabProps> = ({ timeAnalysis }) => {
  const subjectTimeData = Object.entries(timeAnalysis.time_by_subject).map(
    ([subject, data]) => ({
      subject,
      time: data.average_time,
      count: data.question_count,
    }),
  );

  const speedPieData = [
    {
      name: 'Cok Hizli',
      value: timeAnalysis.speed_analysis.too_fast,
      fill: '#ef4444',
    },
    {
      name: 'Optimal',
      value: timeAnalysis.speed_analysis.optimal,
      fill: '#22c55e',
    },
    {
      name: 'Cok Yavas',
      value: timeAnalysis.speed_analysis.too_slow,
      fill: '#f59e0b',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Zaman Kullanim Ozeti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Zaman Kullanim Analizi
          </CardTitle>
          <CardDescription>
            Sinav suresini nasil kullandiginizin detayli analizi
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Toplam Sure</p>
              <p className="text-2xl font-bold text-blue-600">
                {examPerformanceService.formatTime(
                  timeAnalysis.total_duration_seconds,
                )}
              </p>
              <p className="text-xs text-muted-foreground">
                {timeAnalysis.total_duration_minutes.toFixed(0)} dakika
              </p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Sure Kullanimi</p>
              <p className="text-2xl font-bold text-green-600">
                %{timeAnalysis.time_utilization_percent.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">
                {timeAnalysis.exam_duration_minutes} dakikadan
              </p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Soru Basina</p>
              <p className="text-2xl font-bold text-orange-600">
                {examPerformanceService.formatTime(
                  timeAnalysis.average_time_per_question,
                )}
              </p>
              <p className="text-xs text-muted-foreground">Ortalama sure</p>
            </div>
          </div>

          <Progress
            value={timeAnalysis.time_utilization_percent}
            className="mb-4"
          />

          <div className="text-center text-sm text-muted-foreground">
            Sinav suresinin %{timeAnalysis.time_utilization_percent.toFixed(1)}
            {`${"'"}ini kullandiniz`}
          </div>
        </CardContent>
      </Card>

      {/* Konu Bazli Zaman Analizi */}
      <Card>
        <CardHeader>
          <CardTitle>Konu Bazli Zaman Dagilimi</CardTitle>
          <CardDescription>
            Her konuda harcardiginiz ortalama sure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={subjectTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="subject" />
              <YAxis />
              <Tooltip
                formatter={(value: number) => [
                  examPerformanceService.formatTime(value),
                  'Ortalama Sure',
                ]}
              />
              <Bar dataKey="time" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Hiz Analizi */}
      <Card>
        <CardHeader>
          <CardTitle>Cevaplama Hizi Analizi</CardTitle>
          <CardDescription>
            Sorulara verdiginiz cevaplarin hiz dagilimi
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-red-600 mb-2">
                {timeAnalysis.speed_analysis.too_fast}
              </div>
              <p className="text-sm font-medium">Cok Hizli</p>
              <p className="text-xs text-muted-foreground">&lt; 30 saniye</p>
            </div>
            <div className="text-center p-4 border rounded-lg bg-green-50">
              <div className="text-2xl font-bold text-green-600 mb-2">
                {timeAnalysis.speed_analysis.optimal}
              </div>
              <p className="text-sm font-medium">Optimal</p>
              <p className="text-xs text-muted-foreground">30-120 saniye</p>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-orange-600 mb-2">
                {timeAnalysis.speed_analysis.too_slow}
              </div>
              <p className="text-sm font-medium">Cok Yavas</p>
              <p className="text-xs text-muted-foreground">&gt; 120 saniye</p>
            </div>
          </div>

          <div className="mt-6">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={speedPieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} %${(percent * 100).toFixed(0)}`
                  }
                />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TimeAnalysisTab;
