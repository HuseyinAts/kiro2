/**
 * Zayıflık Kartı Bileşeni
 * Türkiye Üniversite Sınavları Hazırlık Platformu
 * 
 * Bu bileşen tek bir zayıflığı görselleştirir:
 * - Zayıflık seviyesi ve renk kodlaması
 * - Performans metrikleri
 * - Gelişim potansiyeli
 * - Zorluk dağılımı
 */

import React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, TrendingUp, Clock, Target } from 'lucide-react';

import {
  SubjectWeakness,
  examPerformanceService,
} from '@/services/examPerformanceService';

interface WeaknessCardProps {
  weakness: SubjectWeakness;
  showDetails?: boolean;
  onViewDetails?: () => void;
}

const WeaknessCard: React.FC<WeaknessCardProps> = ({
  weakness,
  showDetails = true,
  onViewDetails,
}) => {
  const getWeaknessIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'moderate':
        return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'minor':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getWeaknessDescription = (level: string) => {
    switch (level) {
      case 'critical':
        return 'Acil müdahale gerekiyor. Bu konuya öncelik verin.';
      case 'moderate':
        return 'Orta seviye zayıflık. Düzenli çalışma ile geliştirilebilir.';
      case 'minor':
        return 'Hafif zayıflık. Biraz daha pratik yaparak güçlendirebilirsiniz.';
      default:
        return 'Zayıflık seviyesi belirlenemedi.';
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getWeaknessIcon(weakness.weakness_level)}
            <CardTitle className="text-lg">{weakness.topic}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge 
              style={{ 
                backgroundColor: examPerformanceService.getWeaknessLevelColor(weakness.weakness_level),
                color: 'white'
              }}
            >
              {examPerformanceService.getWeaknessLevelLabel(weakness.weakness_level)}
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              %{(weakness.improvement_potential * 100).toFixed(0)}
            </Badge>
          </div>
        </div>
        <CardDescription>
          {weakness.subject} • {getWeaknessDescription(weakness.weakness_level)}
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Başarı Oranı */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Başarı Oranı</span>
            <span className="text-lg font-bold text-red-600">
              %{weakness.success_rate.toFixed(1)}
            </span>
          </div>
          <Progress 
            value={weakness.success_rate} 
            className="h-2"
            style={{
              '--progress-background': examPerformanceService.getWeaknessLevelColor(weakness.weakness_level)
            } as React.CSSProperties}
          />
        </div>

        {/* Performans Metrikleri */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="text-center p-2 bg-gray-50 rounded">
            <p className="text-xs text-muted-foreground">Toplam</p>
            <p className="text-sm font-bold">{weakness.total_questions}</p>
          </div>
          <div className="text-center p-2 bg-green-50 rounded">
            <p className="text-xs text-muted-foreground">Doğru</p>
            <p className="text-sm font-bold text-green-600">{weakness.correct_answers}</p>
          </div>
          <div className="text-center p-2 bg-red-50 rounded">
            <p className="text-xs text-muted-foreground">Yanlış</p>
            <p className="text-sm font-bold text-red-600">{weakness.wrong_answers}</p>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <p className="text-xs text-muted-foreground">Boş</p>
            <p className="text-sm font-bold text-gray-600">{weakness.empty_answers}</p>
          </div>
        </div>

        {showDetails && (
          <>
            {/* Ek Bilgiler */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3 text-muted-foreground" />
                  <span>Ortalama Süre:</span>
                </div>
                <span className="font-medium">
                  {examPerformanceService.formatTime(weakness.average_response_time)}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-1">
                  <Target className="h-3 w-3 text-muted-foreground" />
                  <span>Gelişim Potansiyeli:</span>
                </div>
                <span className="font-medium text-blue-600">
                  %{(weakness.improvement_potential * 100).toFixed(0)}
                </span>
              </div>
            </div>

            {/* Zorluk Dağılımı */}
            <div>
              <p className="text-sm font-medium mb-2">Zorluk Dağılımı:</p>
              <div className="flex flex-wrap gap-1">
                {Object.entries(weakness.difficulty_distribution).map(([difficulty, count]) => (
                  <Badge key={difficulty} variant="outline" className="text-xs">
                    {difficulty === 'easy' ? 'Kolay' : 
                     difficulty === 'medium' ? 'Orta' : 
                     difficulty === 'hard' ? 'Zor' : difficulty}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Aksiyon Butonu */}
        {onViewDetails && (
          <div className="mt-4 pt-4 border-t">
            <button
              onClick={onViewDetails}
              className="w-full text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Detaylı Analiz ve Öneriler →
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WeaknessCard;