/**
 * Sınav Performans Analizi Dashboard
 * Türkiye Üniversite Sınavları Hazırlık Platformu
 * 
 * Bu bileşen sınav performansının detaylı analizini görselleştirir:
 * - Genel performans metrikleri
 * - Konu bazlı zayıflık analizi
 * - Çalışma önerileri
 * - Ulusal ortalamalarla karşılaştırma
 * - Gelişim trendi
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  BookOpen,
  AlertTriangle,
  CheckCircle,
  XCircle,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Award,
  Calendar,
  Users,
} from 'lucide-react';

import {
  examPerformanceService,
  DetailedPerformanceAnalysis,
  SubjectWeakness,
  StudyRecommendation,
} from '@/services/examPerformanceService';

interface ExamPerformanceDashboardProps {
  examSessionId: string;
  onClose?: () => void;
}

const ExamPerformanceDashboard: React.FC<ExamPerformanceDashboardProps> = ({
  examSessionId,
  onClose,
}) => {
  const [analysis, setAnalysis] = useState<DetailedPerformanceAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadPerformanceAnalysis();
  }, [examSessionId]);

  const loadPerformanceAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const analysisData = await examPerformanceService.getDetailedAnalysis(
        examSessionId,
        true
      );
      
      setAnalysis(analysisData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Performans analizi yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Performans analizi yüklenirken hata oluştu: {error}
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadPerformanceAnalysis}
            className="ml-2"
          >
            Tekrar Dene
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!analysis) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Performans analizi verisi bulunamadı.
        </AlertDescription>
      </Alert>
    );
  }

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Genel Performans Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Puan</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {examPerformanceService.formatScore(analysis.overall_performance.net_score)}
            </div>
            <p className="text-xs text-muted-foreground">
              Ham Puan: {examPerformanceService.formatScore(analysis.overall_performance.raw_score)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Doğruluk Oranı</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              %{analysis.overall_performance.accuracy_rate.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              {analysis.overall_performance.correct_answers}/{analysis.overall_performance.total_questions} doğru
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ortalama Süre</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {examPerformanceService.formatTime(analysis.overall_performance.average_response_time)}
            </div>
            <p className="text-xs text-muted-foreground">
              Soru başına ortalama
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Yüzdelik Dilim</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {analysis.performance_comparison ? 
                examPerformanceService.formatPercentile(analysis.performance_comparison.percentile) : 
                'N/A'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              Ulusal sıralama
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performans Karşılaştırması */}
      {analysis.performance_comparison && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Performans Karşılaştırması
            </CardTitle>
            <CardDescription>
              Puanınızın ulusal ortalamalarla karşılaştırması
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Sizin Puanınız</span>
                <span className="text-lg font-bold text-blue-600">
                  {examPerformanceService.formatScore(analysis.performance_comparison.student_score)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Ulusal Ortalama</span>
                <span className="text-lg font-bold text-gray-600">
                  {examPerformanceService.formatScore(analysis.performance_comparison.national_average)}
                </span>
              </div>

              <div className="relative">
                <Progress 
                  value={analysis.performance_comparison.percentile} 
                  className="h-3"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>%{analysis.performance_comparison.ranking_info.better_than_percent}</strong> öğrenciden daha iyi performans gösterdiniz
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Tahmini sıralama: {analysis.performance_comparison.ranking_info.estimated_rank.toLocaleString()} / {analysis.performance_comparison.ranking_info.total_participants.toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Gelişim Trendi */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Gelişim Trendi
            <Badge variant={analysis.improvement_trends.trend === 'improving' ? 'default' : 
                          analysis.improvement_trends.trend === 'stable' ? 'secondary' : 'destructive'}>
              {examPerformanceService.getTrendIcon(analysis.improvement_trends.trend)} {examPerformanceService.getTrendLabel(analysis.improvement_trends.trend)}
            </Badge>
          </CardTitle>
          <CardDescription>
            Son sınavlarınızdaki performans değişimi
          </CardDescription>
        </CardHeader>
        <CardContent>
          {analysis.improvement_trends.recent_scores.length > 1 ? (
            <div className="space-y-4">
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={analysis.improvement_trends.recent_scores.map((score, index) => ({
                  exam: `Sınav ${index + 1}`,
                  score: score
                }))}>
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
                  <p className="text-sm text-muted-foreground">Gelişim Oranı</p>
                  <p className="text-lg font-bold text-blue-600">
                    {analysis.improvement_trends.improvement_rate > 0 ? '+' : ''}
                    {analysis.improvement_trends.improvement_rate.toFixed(1)} puan
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Tutarlılık</p>
                  <p className="text-lg font-bold text-green-600">
                    %{analysis.improvement_trends.consistency.toFixed(1)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Sonraki Tahmin</p>
                  <p className="text-lg font-bold text-purple-600">
                    {examPerformanceService.formatScore(analysis.next_exam_prediction.predicted_score)}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Trend analizi için daha fazla sınav verisi gerekiyor</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );

  const renderSubjectAnalysisTab = () => (
    <div className="space-y-6">
      {/* Konu Performansları */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Konu Bazlı Performans
          </CardTitle>
          <CardDescription>
            Her konudaki başarı oranınız ve detaylı analiz
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analysis.subject_performances}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="topic" 
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value: number) => [`%${value.toFixed(1)}`, 'Başarı Oranı']}
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

      {/* Konu Detayları */}
      <div className="grid gap-4">
        {analysis.subject_performances.map((subject, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{subject.topic}</CardTitle>
                <Badge variant={subject.success_rate >= 75 ? 'default' : 
                              subject.success_rate >= 60 ? 'secondary' : 
                              subject.success_rate >= 40 ? 'outline' : 'destructive'}>
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
                  <p className="text-sm text-muted-foreground">Doğru</p>
                  <p className="text-lg font-bold text-green-600">{subject.correct_answers}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Yanlış</p>
                  <p className="text-lg font-bold text-red-600">{subject.wrong_answers}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">Boş</p>
                  <p className="text-lg font-bold text-gray-600">{subject.empty_answers}</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Net Puan:</span>
                  <span className="font-medium">{subject.net_score.toFixed(1)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Ortalama Süre:</span>
                  <span className="font-medium">
                    {examPerformanceService.formatTime(subject.average_response_time)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Ortalama Zorluk:</span>
                  <span className="font-medium">{subject.average_difficulty.toFixed(2)}</span>
                </div>
              </div>

              <Progress value={subject.success_rate} className="mt-4" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderWeaknessesTab = () => (
    <div className="space-y-6">
      {analysis.weaknesses.length > 0 ? (
        <>
          {/* Zayıflık Özeti */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Zayıflık Analizi Özeti
              </CardTitle>
              <CardDescription>
                Geliştirilmesi gereken alanlar ve öncelik sıralaması
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {['critical', 'moderate', 'minor'].map(level => {
                  const count = analysis.weaknesses.filter(w => w.weakness_level === level).length;
                  return (
                    <div key={level} className="text-center p-4 rounded-lg border">
                      <div 
                        className="text-2xl font-bold mb-2"
                        style={{ color: examPerformanceService.getWeaknessLevelColor(level) }}
                      >
                        {count}
                      </div>
                      <p className="text-sm font-medium">
                        {examPerformanceService.getWeaknessLevelLabel(level)} Zayıflık
                      </p>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Zayıflık Detayları */}
          <div className="space-y-4">
            {analysis.weaknesses.map((weakness, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{weakness.topic}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge 
                        style={{ 
                          backgroundColor: examPerformanceService.getWeaknessLevelColor(weakness.weakness_level),
                          color: 'white'
                        }}
                      >
                        {examPerformanceService.getWeaknessLevelLabel(weakness.weakness_level)}
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
                      <p className="text-sm text-muted-foreground">Başarı Oranı</p>
                      <p className="text-lg font-bold text-red-600">
                        %{weakness.success_rate.toFixed(1)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Doğru</p>
                      <p className="text-lg font-bold">{weakness.correct_answers}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Yanlış</p>
                      <p className="text-lg font-bold">{weakness.wrong_answers}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground">Boş</p>
                      <p className="text-lg font-bold">{weakness.empty_answers}</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Ortalama Cevaplama Süresi:</span>
                      <span className="font-medium">
                        {examPerformanceService.formatTime(weakness.average_response_time)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Gelişim Potansiyeli:</span>
                      <span className="font-medium">
                        %{(weakness.improvement_potential * 100).toFixed(0)}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4">
                    <p className="text-sm font-medium mb-2">Zorluk Dağılımı:</p>
                    <div className="flex gap-2">
                      {Object.entries(weakness.difficulty_distribution).map(([difficulty, count]) => (
                        <Badge key={difficulty} variant="outline">
                          {difficulty}: {count}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="text-center py-8">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
            <h3 className="text-lg font-medium mb-2">Harika! Zayıflık Tespit Edilmedi</h3>
            <p className="text-muted-foreground">
              Tüm konularda %75 ve üzeri başarı gösterdiniz. Mevcut performansınızı koruyun.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderRecommendationsTab = () => (
    <div className="space-y-6">
      {analysis.study_recommendations.length > 0 ? (
        <>
          {/* Öneri Özeti */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Çalışma Önerileri Özeti
              </CardTitle>
              <CardDescription>
                Kişiselleştirilmiş çalışma planı ve kaynak önerileri
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {['urgent', 'high', 'medium', 'low'].map(priority => {
                  const count = analysis.study_recommendations.filter(r => r.priority === priority).length;
                  return (
                    <div key={priority} className="text-center p-4 rounded-lg border">
                      <div 
                        className="text-2xl font-bold mb-2"
                        style={{ color: examPerformanceService.getPriorityColor(priority) }}
                      >
                        {count}
                      </div>
                      <p className="text-sm font-medium">
                        {examPerformanceService.getPriorityLabel(priority)} Öncelik
                      </p>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Öneri Detayları */}
          <div className="space-y-4">
            {analysis.study_recommendations.map((recommendation, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{recommendation.topic}</CardTitle>
                    <Badge 
                      style={{ 
                        backgroundColor: examPerformanceService.getPriorityColor(recommendation.priority),
                        color: 'white'
                      }}
                    >
                      {examPerformanceService.getPriorityLabel(recommendation.priority)} Öncelik
                    </Badge>
                  </div>
                  <CardDescription>{recommendation.subject}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <Clock className="h-6 w-6 mx-auto mb-2 text-blue-600" />
                      <p className="text-sm text-muted-foreground">Önerilen Süre</p>
                      <p className="text-lg font-bold text-blue-600">
                        {recommendation.recommended_study_hours} saat
                      </p>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <Target className="h-6 w-6 mx-auto mb-2 text-green-600" />
                      <p className="text-sm text-muted-foreground">Soru Sayısı</p>
                      <p className="text-lg font-bold text-green-600">
                        {recommendation.practice_question_count}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-lg">
                      <BarChart3 className="h-6 w-6 mx-auto mb-2 text-orange-600" />
                      <p className="text-sm text-muted-foreground">Zorluk Odağı</p>
                      <p className="text-lg font-bold text-orange-600 capitalize">
                        {recommendation.difficulty_focus}
                      </p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-sm font-medium mb-2">Açıklama:</p>
                    <p className="text-sm text-muted-foreground bg-gray-50 p-3 rounded-lg">
                      {recommendation.explanation}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-3">Önerilen Kaynaklar:</p>
                    <div className="space-y-2">
                      {recommendation.recommended_resources.map((resource, resourceIndex) => (
                        <div key={resourceIndex} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium">{resource.title}</p>
                            <p className="text-sm text-muted-foreground">
                              {resource.source} • {resource.type}
                              {resource.duration_minutes && ` • ${resource.duration_minutes} dk`}
                              {resource.question_count && ` • ${resource.question_count} soru`}
                              {resource.reading_time && ` • ${resource.reading_time} dk okuma`}
                            </p>
                          </div>
                          <Button variant="outline" size="sm" asChild>
                            <a href={resource.url} target="_blank" rel="noopener noreferrer">
                              Aç
                            </a>
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="text-center py-8">
            <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
            <h3 className="text-lg font-medium mb-2">Mükemmel Performans!</h3>
            <p className="text-muted-foreground">
              Şu anda özel çalışma önerisi bulunmuyor. Mevcut seviyenizi korumaya odaklanın.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderTimeAnalysisTab = () => (
    <div className="space-y-6">
      {/* Zaman Kullanım Özeti */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Zaman Kullanım Analizi
          </CardTitle>
          <CardDescription>
            Sınav süresini nasıl kullandığınızın detaylı analizi
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Toplam Süre</p>
              <p className="text-2xl font-bold text-blue-600">
                {examPerformanceService.formatTime(analysis.time_analysis.total_duration_seconds)}
              </p>
              <p className="text-xs text-muted-foreground">
                {analysis.time_analysis.total_duration_minutes.toFixed(0)} dakika
              </p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Süre Kullanımı</p>
              <p className="text-2xl font-bold text-green-600">
                %{analysis.time_analysis.time_utilization_percent.toFixed(1)}
              </p>
              <p className="text-xs text-muted-foreground">
                {analysis.time_analysis.exam_duration_minutes} dakikadan
              </p>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-muted-foreground">Soru Başına</p>
              <p className="text-2xl font-bold text-orange-600">
                {examPerformanceService.formatTime(analysis.time_analysis.average_time_per_question)}
              </p>
              <p className="text-xs text-muted-foreground">
                Ortalama süre
              </p>
            </div>
          </div>

          <Progress 
            value={analysis.time_analysis.time_utilization_percent} 
            className="mb-4"
          />
          
          <div className="text-center text-sm text-muted-foreground">
            Sınav süresinin %{analysis.time_analysis.time_utilization_percent.toFixed(1)}'ini kullandınız
          </div>
        </CardContent>
      </Card>

      {/* Konu Bazlı Zaman Analizi */}
      <Card>
        <CardHeader>
          <CardTitle>Konu Bazlı Zaman Dağılımı</CardTitle>
          <CardDescription>
            Her konuda harcadığınız ortalama süre
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(analysis.time_analysis.time_by_subject).map(([subject, data]) => ({
              subject,
              time: data.average_time,
              count: data.question_count
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="subject" />
              <YAxis />
              <Tooltip 
                formatter={(value: number) => [examPerformanceService.formatTime(value), 'Ortalama Süre']}
              />
              <Bar dataKey="time" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Hız Analizi */}
      <Card>
        <CardHeader>
          <CardTitle>Cevaplama Hızı Analizi</CardTitle>
          <CardDescription>
            Sorulara verdiğiniz cevapların hız dağılımı
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-red-600 mb-2">
                {analysis.time_analysis.speed_analysis.too_fast}
              </div>
              <p className="text-sm font-medium">Çok Hızlı</p>
              <p className="text-xs text-muted-foreground">&lt; 30 saniye</p>
            </div>
            <div className="text-center p-4 border rounded-lg bg-green-50">
              <div className="text-2xl font-bold text-green-600 mb-2">
                {analysis.time_analysis.speed_analysis.optimal}
              </div>
              <p className="text-sm font-medium">Optimal</p>
              <p className="text-xs text-muted-foreground">30-120 saniye</p>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-orange-600 mb-2">
                {analysis.time_analysis.speed_analysis.too_slow}
              </div>
              <p className="text-sm font-medium">Çok Yavaş</p>
              <p className="text-xs text-muted-foreground">&gt; 120 saniye</p>
            </div>
          </div>

          <div className="mt-6">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Çok Hızlı', value: analysis.time_analysis.speed_analysis.too_fast, fill: '#ef4444' },
                    { name: 'Optimal', value: analysis.time_analysis.speed_analysis.optimal, fill: '#22c55e' },
                    { name: 'Çok Yavaş', value: analysis.time_analysis.speed_analysis.too_slow, fill: '#f59e0b' }
                  ]}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, percent }) => `${name} %${(percent * 100).toFixed(0)}`}
                />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Sınav Performans Analizi
          </h1>
          <p className="text-gray-600 mt-1">
            {analysis.exam_type.toUpperCase()} Sınavı • Detaylı Analiz ve Öneriler
          </p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Kapat
          </Button>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
          <TabsTrigger value="subjects">Konu Analizi</TabsTrigger>
          <TabsTrigger value="weaknesses">Zayıflıklar</TabsTrigger>
          <TabsTrigger value="recommendations">Öneriler</TabsTrigger>
          <TabsTrigger value="time">Zaman Analizi</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverviewTab()}
        </TabsContent>

        <TabsContent value="subjects" className="mt-6">
          {renderSubjectAnalysisTab()}
        </TabsContent>

        <TabsContent value="weaknesses" className="mt-6">
          {renderWeaknessesTab()}
        </TabsContent>

        <TabsContent value="recommendations" className="mt-6">
          {renderRecommendationsTab()}
        </TabsContent>

        <TabsContent value="time" className="mt-6">
          {renderTimeAnalysisTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExamPerformanceDashboard;