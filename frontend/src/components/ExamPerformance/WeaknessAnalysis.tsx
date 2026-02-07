/**
 * Weakness Analysis Component
 * Displays weak areas and improvement potential analysis
 */

import { AlertTriangle, CheckCircle } from 'lucide-react';
import * as React from 'react';

import type { WeaknessAnalysisProps } from './types';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { examPerformanceService } from '@/services/examPerformanceService';

const WeaknessAnalysis: React.FC<WeaknessAnalysisProps> = ({ weaknesses }) => {
  if (weaknesses.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
          <h3 className="text-lg font-medium mb-2">Harika! Zayiflik Tespit Edilmedi</h3>
          <p className="text-muted-foreground">
            Tum konularda %75 ve uzeri basari gosterdiniz. Mevcut performansinizi koruyun.
          </p>
        </CardContent>
      </Card>
    );
  }

  const weaknessLevels = ['critical', 'moderate', 'minor'] as const;

  return (
    <div className="space-y-6">
      {/* Zayiflik Ozeti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Zayiflik Analizi Ozeti
          </CardTitle>
          <CardDescription>
            Gelistirilmesi gereken alanlar ve oncelik siralamasi
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {weaknessLevels.map((level) => {
              const count = weaknesses.filter(
                (w) => w.weakness_level === level,
              ).length;
              return (
                <div key={level} className="text-center p-4 rounded-lg border">
                  <div
                    className="text-2xl font-bold mb-2"
                    style={{
                      color: examPerformanceService.getWeaknessLevelColor(level),
                    }}
                  >
                    {count}
                  </div>
                  <p className="text-sm font-medium">
                    {examPerformanceService.getWeaknessLevelLabel(level)} Zayiflik
                  </p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Zayiflik Detaylari */}
      <div className="space-y-4">
        {weaknesses.map((weakness, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{weakness.topic}</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge
                    style={{
                      backgroundColor: examPerformanceService.getWeaknessLevelColor(
                        weakness.weakness_level,
                      ),
                      color: 'white',
                    }}
                  >
                    {examPerformanceService.getWeaknessLevelLabel(
                      weakness.weakness_level,
                    )}
                  </Badge>
                  <Badge variant="outline">
                    Potansiyel: %{(weakness.improvement_potential * 100).toFixed(0)}
                  </Badge>
                </div>
              </div>
              <CardDescription>{weakness.subject}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Basari Orani</p>
                  <p className="text-lg font-bold text-red-600">
                    %{weakness.success_rate.toFixed(1)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Dogru</p>
                  <p className="text-lg font-bold">{weakness.correct_answers}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Yanlis</p>
                  <p className="text-lg font-bold">{weakness.wrong_answers}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Bos</p>
                  <p className="text-lg font-bold">{weakness.empty_answers}</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Ortalama Cevaplama Suresi:</span>
                  <span className="font-medium">
                    {examPerformanceService.formatTime(weakness.average_response_time)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Gelisim Potansiyeli:</span>
                  <span className="font-medium">
                    %{(weakness.improvement_potential * 100).toFixed(0)}
                  </span>
                </div>
              </div>

              <div className="mt-4">
                <p className="text-sm font-medium mb-2">Zorluk Dagilimi:</p>
                <div className="flex gap-2">
                  {Object.entries(weakness.difficulty_distribution).map(
                    ([difficulty, count]) => (
                      <Badge key={difficulty} variant="outline">
                        {difficulty}: {count}
                      </Badge>
                    ),
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default WeaknessAnalysis;
