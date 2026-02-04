import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  BookOpen, 
  Award, 
  Calendar,
  BarChart3,
  Target,
  AlertCircle,
  Download
} from 'lucide-react';
import { parentService } from '@/services/parentService';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';

interface ChildPerformance {
  child_id: number;
  child_name: string;
  total_study_time: number;
  exams_taken: number;
  average_score: number;
  last_exam_date?: string;
  last_exam_score?: number;
  weak_subjects: string[];
  strong_subjects: string[];
  recent_achievements: string[];
}

interface WeeklyReport {
  child_id: number;
  child_name: string;
  week_start: string;
  week_end: string;
  total_study_time: number;
  exams_taken: number;
  average_score: number;
  subjects_studied: string[];
  achievements: string[];
  performance_trend: string;
  recommendations: string[];
}

export const ChildPerformanceView: React.FC = () => {
  const { childId } = useParams<{ childId: string }>();
  const [performance, setPerformance] = useState<ChildPerformance | null>(null);
  const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'weekly'>('overview');

  useEffect(() => {
    if (childId) {
      loadPerformanceData();
    }
  }, [childId]);

  const loadPerformanceData = async () => {
    if (!childId) return;

    try {
      setLoading(true);
      const [performanceData, reportData] = await Promise.all([
        parentService.getChildPerformance(parseInt(childId)),
        parentService.getWeeklyReport(parseInt(childId))
      ]);
      
      setPerformance(performanceData);
      setWeeklyReport(reportData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Performans verileri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const formatStudyTime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}s ${mins}dk`;
  };

  const getPerformanceColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceBadge = (score: number): string => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'declining':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <BarChart3 className="h-4 w-4 text-blue-600" />;
    }
  };

  const getTrendText = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'Gelişiyor';
      case 'declining':
        return 'Düşüş';
      default:
        return 'Stabil';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!performance) {
    return (
      <Alert className="m-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Performans verileri bulunamadı</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{performance.child_name}</h1>
          <p className="text-gray-600">Performans Detayları</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadPerformanceData} variant="outline">
            Yenile
          </Button>
          <Button className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Rapor İndir
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Genel Bakış
          </button>
          <button
            onClick={() => setActiveTab('weekly')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'weekly'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Haftalık Rapor
          </button>
        </nav>
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Performance Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Ortalama Başarı</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getPerformanceColor(performance.average_score)}`}>
                  {performance.average_score.toFixed(1)}%
                </div>
                <Badge className={getPerformanceBadge(performance.average_score)}>
                  {performance.average_score >= 80 ? 'Mükemmel' : 
                   performance.average_score >= 60 ? 'İyi' : 'Geliştirilmeli'}
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Toplam Çalışma</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatStudyTime(performance.total_study_time)}</div>
                <p className="text-xs text-muted-foreground">Son 30 gün</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Çözülen Sınav</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{performance.exams_taken}</div>
                <p className="text-xs text-muted-foreground">Son 30 gün</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Son Sınav</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {performance.last_exam_date ? (
                  <>
                    <div className={`text-2xl font-bold ${getPerformanceColor(performance.last_exam_score || 0)}`}>
                      {performance.last_exam_score?.toFixed(1)}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {new Date(performance.last_exam_date).toLocaleDateString('tr-TR')}
                    </p>
                  </>
                ) : (
                  <div className="text-sm text-gray-500">Henüz sınav yok</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Subject Analysis */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-600">
                  <TrendingDown className="h-5 w-5" />
                  Geliştirilmesi Gereken Konular
                </CardTitle>
              </CardHeader>
              <CardContent>
                {performance.weak_subjects.length === 0 ? (
                  <p className="text-gray-500">Zayıf konu bulunmamaktadır</p>
                ) : (
                  <div className="space-y-2">
                    {performance.weak_subjects.map((subject, index) => (
                      <Badge key={index} className="bg-red-100 text-red-800 mr-2">
                        {subject}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <TrendingUp className="h-5 w-5" />
                  Güçlü Konular
                </CardTitle>
              </CardHeader>
              <CardContent>
                {performance.strong_subjects.length === 0 ? (
                  <p className="text-gray-500">Güçlü konu bulunmamaktadır</p>
                ) : (
                  <div className="space-y-2">
                    {performance.strong_subjects.map((subject, index) => (
                      <Badge key={index} className="bg-green-100 text-green-800 mr-2">
                        {subject}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Achievements */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5 text-yellow-500" />
                Son Başarılar
              </CardTitle>
            </CardHeader>
            <CardContent>
              {performance.recent_achievements.length === 0 ? (
                <p className="text-gray-500">Henüz başarı kaydı bulunmamaktadır</p>
              ) : (
                <div className="space-y-2">
                  {performance.recent_achievements.map((achievement, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 bg-yellow-50 rounded-lg">
                      <Award className="h-4 w-4 text-yellow-600" />
                      <span className="text-yellow-800">{achievement}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {activeTab === 'weekly' && weeklyReport && (
        <>
          {/* Weekly Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Bu Haftanın Özeti
                <Badge variant="outline">
                  {new Date(weeklyReport.week_start).toLocaleDateString('tr-TR')} - 
                  {new Date(weeklyReport.week_end).toLocaleDateString('tr-TR')}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {formatStudyTime(weeklyReport.total_study_time)}
                  </div>
                  <p className="text-sm text-gray-600">Çalışma Süresi</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {weeklyReport.exams_taken}
                  </div>
                  <p className="text-sm text-gray-600">Sınav Sayısı</p>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getPerformanceColor(weeklyReport.average_score)}`}>
                    {weeklyReport.average_score.toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600">Ortalama</p>
                </div>
                <div className="text-center flex flex-col items-center">
                  {getTrendIcon(weeklyReport.performance_trend)}
                  <p className="text-sm text-gray-600 mt-1">
                    {getTrendText(weeklyReport.performance_trend)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Subjects and Achievements */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Çalışılan Konular</CardTitle>
              </CardHeader>
              <CardContent>
                {weeklyReport.subjects_studied.length === 0 ? (
                  <p className="text-gray-500">Bu hafta konu çalışılmamış</p>
                ) : (
                  <div className="space-y-2">
                    {weeklyReport.subjects_studied.map((subject, index) => (
                      <Badge key={index} variant="outline" className="mr-2">
                        {subject}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Bu Haftanın Başarıları</CardTitle>
              </CardHeader>
              <CardContent>
                {weeklyReport.achievements.length === 0 ? (
                  <p className="text-gray-500">Bu hafta özel başarı kaydedilmemiş</p>
                ) : (
                  <div className="space-y-2">
                    {weeklyReport.achievements.map((achievement, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-green-50 rounded-lg">
                        <Award className="h-4 w-4 text-green-600" />
                        <span className="text-green-800">{achievement}</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Öneriler
              </CardTitle>
            </CardHeader>
            <CardContent>
              {weeklyReport.recommendations.length === 0 ? (
                <p className="text-gray-500">Bu hafta için özel öneri bulunmamaktadır</p>
              ) : (
                <div className="space-y-3">
                  {weeklyReport.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
                      <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5" />
                      <span className="text-blue-800">{recommendation}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};