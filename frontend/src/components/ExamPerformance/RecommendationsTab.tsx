/**
 * Recommendations Tab Component
 * Displays personalized study recommendations and resources
 */

import { BookOpen, Clock, Target, BarChart3, CheckCircle } from 'lucide-react';
import * as React from 'react';

import type { RecommendationsTabProps } from './types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { examPerformanceService } from '@/services/examPerformanceService';

const RecommendationsTab: React.FC<RecommendationsTabProps> = ({
  recommendations,
}) => {
  if (recommendations.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
          <h3 className="text-lg font-medium mb-2">Mukemmel Performans!</h3>
          <p className="text-muted-foreground">
            Su anda ozel calisma onerisi bulunmuyor. Mevcut seviyenizi korumaya
            odaklanin.
          </p>
        </CardContent>
      </Card>
    );
  }

  const priorityLevels = ['urgent', 'high', 'medium', 'low'] as const;

  return (
    <div className="space-y-6">
      {/* Oneri Ozeti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Calisma Onerileri Ozeti
          </CardTitle>
          <CardDescription>
            Kisisellestirilmis calisma plani ve kaynak onerileri
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {priorityLevels.map((priority) => {
              const count = recommendations.filter(
                (r) => r.priority === priority,
              ).length;
              return (
                <div key={priority} className="text-center p-4 rounded-lg border">
                  <div
                    className="text-2xl font-bold mb-2"
                    style={{
                      color: examPerformanceService.getPriorityColor(priority),
                    }}
                  >
                    {count}
                  </div>
                  <p className="text-sm font-medium">
                    {examPerformanceService.getPriorityLabel(priority)} Oncelik
                  </p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Oneri Detaylari */}
      <div className="space-y-4">
        {recommendations.map((recommendation, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{recommendation.topic}</CardTitle>
                <Badge
                  style={{
                    backgroundColor: examPerformanceService.getPriorityColor(
                      recommendation.priority,
                    ),
                    color: 'white',
                  }}
                >
                  {examPerformanceService.getPriorityLabel(recommendation.priority)}{' '}
                  Oncelik
                </Badge>
              </div>
              <CardDescription>{recommendation.subject}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <Clock className="h-6 w-6 mx-auto mb-2 text-blue-600" />
                  <p className="text-sm text-muted-foreground">Onerilen Sure</p>
                  <p className="text-lg font-bold text-blue-600">
                    {recommendation.recommended_study_hours} saat
                  </p>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <Target className="h-6 w-6 mx-auto mb-2 text-green-600" />
                  <p className="text-sm text-muted-foreground">Soru Sayisi</p>
                  <p className="text-lg font-bold text-green-600">
                    {recommendation.practice_question_count}
                  </p>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <BarChart3 className="h-6 w-6 mx-auto mb-2 text-orange-600" />
                  <p className="text-sm text-muted-foreground">Zorluk Odagi</p>
                  <p className="text-lg font-bold text-orange-600 capitalize">
                    {recommendation.difficulty_focus}
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <p className="text-sm font-medium mb-2">Aciklama:</p>
                <p className="text-sm text-muted-foreground bg-gray-50 p-3 rounded-lg">
                  {recommendation.explanation}
                </p>
              </div>

              <div>
                <p className="text-sm font-medium mb-3">Onerilen Kaynaklar:</p>
                <div className="space-y-2">
                  {recommendation.recommended_resources.map(
                    (resource, resourceIndex) => (
                      <div
                        key={resourceIndex}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div className="flex-1">
                          <p className="font-medium">{resource.title}</p>
                          <p className="text-sm text-muted-foreground">
                            {resource.source} - {resource.type}
                            {resource.duration_minutes &&
                              ` - ${resource.duration_minutes} dk`}
                            {resource.question_count &&
                              ` - ${resource.question_count} soru`}
                            {resource.reading_time &&
                              ` - ${resource.reading_time} dk okuma`}
                          </p>
                        </div>
                        <Button variant="outline" size="sm" asChild>
                          <a
                            href={resource.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            Ac
                          </a>
                        </Button>
                      </div>
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

export default RecommendationsTab;
