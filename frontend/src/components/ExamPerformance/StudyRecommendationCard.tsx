/**
 * Çalışma Önerisi Kartı Bileşeni
 * Türkiye Üniversite Sınavları Hazırlık Platformu
 *
 * Bu bileşen tek bir çalışma önerisini görselleştirir:
 * - Öncelik seviyesi ve renk kodlaması
 * - Önerilen çalışma süresi ve soru sayısı
 * - Kaynak önerileri
 * - Zorluk odağı
 */

import {
  Clock,
  Target,
  BookOpen,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Play,
  FileText,
  HelpCircle,
  BarChart3,
} from 'lucide-react';
import * as React from 'react';
import {  useState  } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  StudyRecommendation,
  examPerformanceService,
} from '@/services/examPerformanceService';

interface StudyRecommendationCardProps {
  recommendation: StudyRecommendation;
  showResources?: boolean;
  onStartStudy?: () => void;
}

const StudyRecommendationCard: React.FC<StudyRecommendationCardProps> = ({
  recommendation,
  showResources = true,
  onStartStudy,
}) => {
  const [showAllResources, setShowAllResources] = useState(false);

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '🚨';
      case 'high':
        return '⚡';
      case 'medium':
        return '📚';
      case 'low':
        return '💡';
      default:
        return '📖';
    }
  };

  const getDifficultyIcon = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return '🟢';
      case 'medium':
        return '🟡';
      case 'hard':
        return '🔴';
      default:
        return '⚪';
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'Kolay';
      case 'medium':
        return 'Orta';
      case 'hard':
        return 'Zor';
      default:
        return 'Bilinmeyen';
    }
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'video':
        return <Play className="h-4 w-4" />;
      case 'article':
        return <FileText className="h-4 w-4" />;
      case 'practice':
        return <Target className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const getResourceTypeLabel = (type: string) => {
    switch (type) {
      case 'video':
        return 'Video';
      case 'article':
        return 'Makale';
      case 'practice':
        return 'Pratik';
      default:
        return 'Kaynak';
    }
  };

  const visibleResources = showAllResources
    ? recommendation.recommended_resources
    : recommendation.recommended_resources.slice(0, 2);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">
              {getPriorityIcon(recommendation.priority)}
            </span>
            <CardTitle className="text-lg">{recommendation.topic}</CardTitle>
          </div>
          <Badge
            style={{
              backgroundColor: examPerformanceService.getPriorityColor(recommendation.priority),
              color: 'white',
            }}
          >
            {examPerformanceService.getPriorityLabel(recommendation.priority)} Öncelik
          </Badge>
        </div>
        <CardDescription>
          {recommendation.subject}
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Çalışma Metrikleri */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <Clock className="h-5 w-5 mx-auto mb-2 text-blue-600" />
            <p className="text-xs text-muted-foreground">Önerilen Süre</p>
            <p className="text-lg font-bold text-blue-600">
              {recommendation.recommended_study_hours} saat
            </p>
          </div>

          <div className="text-center p-3 bg-green-50 rounded-lg">
            <Target className="h-5 w-5 mx-auto mb-2 text-green-600" />
            <p className="text-xs text-muted-foreground">Soru Sayısı</p>
            <p className="text-lg font-bold text-green-600">
              {recommendation.practice_question_count}
            </p>
          </div>

          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <BarChart3 className="h-5 w-5 mx-auto mb-2 text-orange-600" />
            <p className="text-xs text-muted-foreground">Zorluk Odağı</p>
            <p className="text-lg font-bold text-orange-600">
              {getDifficultyIcon(recommendation.difficulty_focus)} {getDifficultyLabel(recommendation.difficulty_focus)}
            </p>
          </div>
        </div>

        {/* Açıklama */}
        <div className="mb-4">
          <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
            <HelpCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-gray-700">
              {recommendation.explanation}
            </p>
          </div>
        </div>

        {/* Kaynak Önerileri */}
        {showResources && recommendation.recommended_resources.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <BookOpen className="h-4 w-4" />
                Önerilen Kaynaklar
              </h4>
              {recommendation.recommended_resources.length > 2 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllResources(!showAllResources)}
                  className="text-xs"
                >
                  {showAllResources ? (
                    <>
                      <ChevronUp className="h-3 w-3 mr-1" />
                      Daha Az
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-3 w-3 mr-1" />
                      Tümünü Gör ({recommendation.recommended_resources.length})
                    </>
                  )}
                </Button>
              )}
            </div>

            <div className="space-y-2">
              {visibleResources.map((resource, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
                      {getResourceIcon(resource.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{resource.title}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{resource.source}</span>
                        <span>•</span>
                        <span>{getResourceTypeLabel(resource.type)}</span>
                        {resource.duration_minutes && (
                          <>
                            <span>•</span>
                            <span>{resource.duration_minutes} dk</span>
                          </>
                        )}
                        {resource.question_count && (
                          <>
                            <span>•</span>
                            <span>{resource.question_count} soru</span>
                          </>
                        )}
                        {resource.reading_time && (
                          <>
                            <span>•</span>
                            <span>{resource.reading_time} dk okuma</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Aç
                    </a>
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Aksiyon Butonu */}
        {onStartStudy && (
          <div className="pt-4 border-t">
            <Button
              onClick={onStartStudy}
              className="w-full"
              style={{
                backgroundColor: examPerformanceService.getPriorityColor(recommendation.priority),
              }}
            >
              <Play className="h-4 w-4 mr-2" />
              Çalışmaya Başla
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default StudyRecommendationCard;