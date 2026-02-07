/**
 * Performans Karşılaştırma Grafiği Bileşeni
 * Türkiye Üniversite Sınavları Hazırlık Platformu
 *
 * Bu bileşen öğrenci performansını ulusal ortalamalarla karşılaştırır:
 * - Radar chart ile çok boyutlu karşılaştırma
 * - Bar chart ile basit karşılaştırma
 * - Yüzdelik dilim gösterimi
 * - Sıralama bilgileri
 */

import {
  TrendingUp,
  TrendingDown,
  Award,
  Target,
  BarChart3,
} from 'lucide-react';
import * as React from 'react';
import {  useState  } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Cell,
} from 'recharts';

import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  PerformanceComparison,
  examPerformanceService,
} from '@/services/examPerformanceService';

interface PerformanceComparisonChartProps {
  comparison: PerformanceComparison;
  subjectPerformances?: Array<{
    subject: string;
    topic: string;
    success_rate: number;
  }>;
  examType: string;
}

const PerformanceComparisonChart: React.FC<PerformanceComparisonChartProps> = ({
  comparison,
  subjectPerformances = [],
  examType,
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  // Ulusal ortalama veriler (ornek)
  const nationalAverages: Record<string, Record<string, number>> = {
    TYT: {
      TURKCE: 65.2,
      MATEMATIK: 58.7,
      FEN: 62.1,
      SOSYAL: 67.8,
    },
    AYT: {
      MATEMATIK: 55.3,
      FIZIK: 52.1,
      KIMYA: 59.4,
      BIYOLOJI: 61.2,
      EDEBIYAT: 68.9,
      TARIH: 64.7,
      COGRAFYA: 66.1,
      FELSEFE: 63.2,
    },
    YDT: {
      INGILIZCE: 48.7,
    },
  };

  // Genel karşılaştırma verisi
  const overallComparisonData = [
    {
      category: 'Sizin Puanınız',
      score: comparison.student_score,
      fill: '#3b82f6',
    },
    {
      category: 'Ulusal Ortalama',
      score: comparison.national_average,
      fill: '#6b7280',
    },
    ...(comparison.class_average ? [{
      category: 'Sınıf Ortalaması',
      score: comparison.class_average,
      fill: '#10b981',
    }] : []),
    ...(comparison.school_average ? [{
      category: 'Okul Ortalaması',
      score: comparison.school_average,
      fill: '#f59e0b',
    }] : []),
  ];

  // Konu bazli karsilastirma verisi
  const subjectComparisonData = subjectPerformances.map(subject => {
    const nationalAvg = nationalAverages[examType]?.[subject.subject] || 60;
    return {
      subject: subject.topic,
      student: subject.success_rate,
      national: nationalAvg,
      difference: subject.success_rate - nationalAvg,
    };
  });

  // Radar chart verisi
  const radarData = subjectPerformances.slice(0, 6).map(subject => {
    const nationalAvg = nationalAverages[examType]?.[subject.subject] || 60;
    return {
      subject: subject.topic.length > 10 ? subject.topic.substring(0, 10) + '...' : subject.topic,
      student: subject.success_rate,
      national: nationalAvg,
    };
  });

  // Yüzdelik dilim rengi
  const getPercentileColor = (percentile: number) => {
    if (percentile >= 90) {return '#22c55e';} // green
    if (percentile >= 75) {return '#3b82f6';} // blue
    if (percentile >= 50) {return '#f59e0b';} // orange
    if (percentile >= 25) {return '#ef4444';} // red
    return '#6b7280'; // gray
  };

  // Yüzdelik dilim etiketi
  const getPercentileLabel = (percentile: number) => {
    if (percentile >= 90) {return 'Mükemmel';}
    if (percentile >= 75) {return 'Çok İyi';}
    if (percentile >= 50) {return 'İyi';}
    if (percentile >= 25) {return 'Orta';}
    return 'Geliştirilmeli';
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Genel Karşılaştırma */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Genel Performans Karşılaştırması
          </CardTitle>
          <CardDescription>
            Puanınızın farklı gruplarla karşılaştırması
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={overallComparisonData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis domain={[0, 100]} />
              <Tooltip
                formatter={(value: number) => [`${value.toFixed(1)} puan`, 'Puan']}
              />
              <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                {overallComparisonData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Yüzdelik Dilim */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Yüzdelik Dilim Analizi
          </CardTitle>
          <CardDescription>
            Ulusal sıralamadaki konumunuz
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center mb-6">
            <div
              className="text-4xl font-bold mb-2"
              style={{ color: getPercentileColor(comparison.percentile) }}
            >
              {examPerformanceService.formatPercentile(comparison.percentile)}
            </div>
            <Badge
              style={{
                backgroundColor: getPercentileColor(comparison.percentile),
                color: 'white',
              }}
            >
              {getPercentileLabel(comparison.percentile)}
            </Badge>
          </div>

          <div className="relative mb-6">
            <Progress
              value={comparison.percentile}
              className="h-4"
              style={{
                '--progress-background': getPercentileColor(comparison.percentile),
              } as React.CSSProperties}
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span>0%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Daha İyi Performans</p>
              <p className="text-2xl font-bold text-blue-600">
                %{comparison.ranking_info.better_than_percent.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">öğrenciden daha iyi</p>
            </div>

            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Tahmini Sıralama</p>
              <p className="text-2xl font-bold text-green-600">
                {comparison.ranking_info.estimated_rank.toLocaleString()}
              </p>
              <p className="text-xs text-muted-foreground">
                / {comparison.ranking_info.total_participants.toLocaleString()}
              </p>
            </div>

            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Puan Farkı</p>
              <p className="text-2xl font-bold text-orange-600">
                {comparison.student_score > comparison.national_average ? '+' : ''}
                {(comparison.student_score - comparison.national_average).toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">ulusal ortalamadan</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderSubjectComparisonTab = () => (
    <div className="space-y-6">
      {/* Konu Bazlı Karşılaştırma */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Konu Bazlı Performans Karşılaştırması
          </CardTitle>
          <CardDescription>
            Her konudaki performansınızın ulusal ortalamalarla karşılaştırması
          </CardDescription>
        </CardHeader>
        <CardContent>
          {subjectComparisonData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={subjectComparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="subject"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis domain={[0, 100]} />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `${value.toFixed(1)}%`,
                    name === 'student' ? 'Sizin Puanınız' : 'Ulusal Ortalama',
                  ]}
                />
                <Bar dataKey="student" fill="#3b82f6" name="student" />
                <Bar dataKey="national" fill="#6b7280" name="national" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Konu bazlı karşılaştırma için veri bulunamadı</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Konu Detayları */}
      {subjectComparisonData.length > 0 && (
        <div className="grid gap-4">
          {subjectComparisonData.map((subject, index) => (
            <Card key={index}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium">{subject.subject}</h4>
                  <div className="flex items-center gap-2">
                    {subject.difference > 0 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-500" />
                    )}
                    <Badge variant={subject.difference > 0 ? 'default' : 'destructive'}>
                      {subject.difference > 0 ? '+' : ''}{subject.difference.toFixed(1)} puan
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-muted-foreground">Sizin Puanınız</p>
                    <p className="text-lg font-bold text-blue-600">
                      %{subject.student.toFixed(1)}
                    </p>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-sm text-muted-foreground">Ulusal Ortalama</p>
                    <p className="text-lg font-bold text-gray-600">
                      %{subject.national.toFixed(1)}
                    </p>
                  </div>
                </div>

                <Progress
                  value={(subject.student / subject.national) * 50}
                  className="h-2"
                />
                <div className="text-center text-xs text-muted-foreground mt-1">
                  Ulusal ortalamaya göre performans
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderRadarTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Çok Boyutlu Performans Analizi
          </CardTitle>
          <CardDescription>
            Radar grafiği ile tüm konulardaki performansınızın görsel analizi
          </CardDescription>
        </CardHeader>
        <CardContent>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  tick={false}
                />
                <Radar
                  name="Sizin Performansınız"
                  dataKey="student"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                <Radar
                  name="Ulusal Ortalama"
                  dataKey="national"
                  stroke="#6b7280"
                  fill="#6b7280"
                  fillOpacity={0.1}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Radar analizi için yeterli veri bulunamadı</p>
            </div>
          )}

          {radarData.length > 0 && (
            <div className="mt-6 flex justify-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500 rounded"></div>
                <span className="text-sm">Sizin Performansınız</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-gray-500 rounded"></div>
                <span className="text-sm">Ulusal Ortalama</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
          <TabsTrigger value="subjects">Konu Karşılaştırması</TabsTrigger>
          <TabsTrigger value="radar">Radar Analizi</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          {renderOverviewTab()}
        </TabsContent>

        <TabsContent value="subjects">
          {renderSubjectComparisonTab()}
        </TabsContent>

        <TabsContent value="radar">
          {renderRadarTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PerformanceComparisonChart;