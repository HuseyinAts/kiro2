/**
 * Student Analytics Dashboard
 * Öğrenci performans analizi ve raporlama bileşeni
 */

import {
  Clock,
  Target,
  BookOpen,
  Download,
  BarChart3,
  Activity,
} from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

import { analyticsService, StudentAnalytics, ExportRequest } from '../../services/analyticsService';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';

interface StudentAnalyticsDashboardProps {
  studentId: string;
  className?: string;
}

const StudentAnalyticsDashboard: React.FC<StudentAnalyticsDashboardProps> = ({
  studentId,
  className = '',
}) => {
  const [analytics, setAnalytics] = useState<StudentAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState(30); // Son 30 gün
  const [includeDetailed, setIncludeDetailed] = useState(false);
  const [exporting, setExporting] = useState(false);

  // Analytics verilerini yükle
  useEffect(() => {
    loadAnalytics();
  }, [studentId, dateRange, includeDetailed]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const { startDate, endDate } = analyticsService.formatDateRange(dateRange);
      const data = await analyticsService.getStudentAnalytics(
        studentId,
        startDate,
        endDate,
        includeDetailed,
      );

      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analytics yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  // Export işlemi
  const handleExport = async (format: 'pdf' | 'excel' | 'csv') => {
    try {
      setExporting(true);

      const { startDate, endDate } = analyticsService.formatDateRange(dateRange);
      const exportRequest: ExportRequest = {
        format,
        data_type: 'student',
        filters: {
          student_id: studentId,
          start_date: startDate,
          end_date: endDate,
          include_detailed: includeDetailed,
        },
      };

      let response;
      if (format === 'pdf') {
        response = await analyticsService.exportToPdf(exportRequest);
        analyticsService.downloadExportFile(
          response.data.pdf_content!,
          response.data.filename,
          'pdf',
        );
      } else if (format === 'excel') {
        response = await analyticsService.exportToExcel(exportRequest);
        analyticsService.downloadExportFile(
          response.data.excel_content!,
          response.data.filename,
          'excel',
        );
      } else {
        response = await analyticsService.exportToCsv(exportRequest);
        analyticsService.downloadExportFile(
          response.data.csv_content!,
          response.data.filename,
          'csv',
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export işlemi başarısız');
    } finally {
      setExporting(false);
    }
  };

  // Konu performans verilerini hazırla
  const prepareSubjectData = () => {
    if (!analytics?.subject_analysis?.subjects) {return [];}

    return Object.entries(analytics.subject_analysis.subjects).map(([subject, data]) => ({
      subject,
      accuracy: Math.round(data.accuracy_rate * 100),
      questions: data.questions_solved,
      hours: data.time_spent_hours,
      trend: data.improvement_trend,
    }));
  };

  // Öğrenme stili radar chart verisi
  const prepareLearningStyleData = () => {
    if (!analytics?.learning_style) {return [];}

    const vark = analytics.learning_style.vark_profile;
    const felder = analytics.learning_style.felder_silverman_profile;

    return [
      { style: 'Görsel', value: Math.round(vark.visual * 100) },
      { style: 'İşitsel', value: Math.round(vark.auditory * 100) },
      { style: 'Okuma', value: Math.round(vark.reading * 100) },
      { style: 'Kinestetik', value: Math.round(vark.kinesthetic * 100) },
      { style: 'Aktif', value: Math.round(felder.active_reflective * 100) },
      { style: 'Görsel/Sözel', value: Math.round(felder.visual_verbal * 100) },
    ];
  };

  // Sınav performans trend verisi
  const prepareExamTrendData = () => {
    if (!analytics?.exam_performance) {return [];}

    // Mock trend data - gerçek implementasyonda API'den gelecek
    return [
      { exam: 'Deneme 1', score: 65, date: '2024-01-15' },
      { exam: 'Deneme 2', score: 72, date: '2024-01-22' },
      { exam: 'Deneme 3', score: 68, date: '2024-01-29' },
      { exam: 'Deneme 4', score: 78, date: '2024-02-05' },
      { exam: 'Deneme 5', score: 82, date: '2024-02-12' },
    ];
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Analytics yükleniyor...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-4 ${className}`}>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <p className="text-red-600">Hata: {error}</p>
            <Button onClick={loadAnalytics} className="mt-2" variant="outline">
              Tekrar Dene
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className={`p-4 ${className}`}>
        <Card>
          <CardContent className="p-4">
            <p className="text-gray-600">Analytics verisi bulunamadı.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const subjectData = prepareSubjectData();
  const learningStyleData = prepareLearningStyleData();
  const examTrendData = prepareExamTrendData();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Öğrenci Analytics</h2>
          <p className="text-gray-600">
            Öğrenci ID: {analytics.student_id} |
            Dönem: {new Date(analytics.period.start_date).toLocaleDateString('tr-TR')} -
            {new Date(analytics.period.end_date).toLocaleDateString('tr-TR')}
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {/* Tarih aralığı seçici */}
          <select
            aria-label="Tarih aralığı"
            value={dateRange}
            onChange={(e) => setDateRange(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value={7}>Son 7 gün</option>
            <option value={30}>Son 30 gün</option>
            <option value={90}>Son 3 ay</option>
            <option value={365}>Son 1 yıl</option>
          </select>

          {/* Detaylı analiz toggle */}
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={includeDetailed}
              onChange={(e) => setIncludeDetailed(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Detaylı Analiz</span>
          </label>

          {/* Export butonları */}
          <div className="flex space-x-1">
            <Button
              onClick={() => handleExport('pdf')}
              disabled={exporting}
              variant="outline"
              size="sm"
            >
              <Download className="w-4 h-4 mr-1" />
              PDF
            </Button>
            <Button
              onClick={() => handleExport('excel')}
              disabled={exporting}
              variant="outline"
              size="sm"
            >
              <Download className="w-4 h-4 mr-1" />
              Excel
            </Button>
            <Button
              onClick={() => handleExport('csv')}
              disabled={exporting}
              variant="outline"
              size="sm"
            >
              <Download className="w-4 h-4 mr-1" />
              CSV
            </Button>
          </div>
        </div>
      </div>

      {/* Özet Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Toplam Çalışma</p>
                <p className="text-2xl font-bold">
                  {analytics.performance_metrics.total_study_time_hours}h
                </p>
              </div>
              <Clock className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Çözülen Soru</p>
                <p className="text-2xl font-bold">
                  {analytics.performance_metrics.total_questions_solved.toLocaleString()}
                </p>
              </div>
              <BookOpen className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Doğruluk Oranı</p>
                <p className="text-2xl font-bold">
                  %{Math.round(analytics.performance_metrics.accuracy_rate * 100)}
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Gelişim Trendi</p>
                <div className="flex items-center">
                  <span className="text-2xl">
                    {analyticsService.getTrendIcon(analytics.performance_metrics.improvement_trend)}
                  </span>
                  <span className="ml-2 font-bold">
                    {analytics.performance_metrics.improvement_trend === 'increasing' ? 'Artış' :
                     analytics.performance_metrics.improvement_trend === 'decreasing' ? 'Azalış' : 'Stabil'}
                  </span>
                </div>
              </div>
              <Activity className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ana İçerik - Tabs */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="performance">Performans</TabsTrigger>
          <TabsTrigger value="subjects">Konular</TabsTrigger>
          <TabsTrigger value="learning-style">Öğrenme Stili</TabsTrigger>
          <TabsTrigger value="exams">Sınavlar</TabsTrigger>
        </TabsList>

        {/* Performans Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Konu Performansı */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Konu Performansı
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={subjectData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="subject" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="accuracy" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Güçlü ve Zayıf Konular */}
            <Card>
              <CardHeader>
                <CardTitle>Güçlü ve Zayıf Konular</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold text-green-600 mb-2">Güçlü Konular</h4>
                  <div className="flex flex-wrap gap-2">
                    {analytics.performance_metrics.strong_subjects.map((subject, index) => (
                      <Badge key={index} variant="secondary" className="bg-green-100 text-green-800">
                        {subject}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-red-600 mb-2">Zayıf Konular</h4>
                  <div className="flex flex-wrap gap-2">
                    {analytics.performance_metrics.weak_subjects.map((subject, index) => (
                      <Badge key={index} variant="secondary" className="bg-red-100 text-red-800">
                        {subject}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Konular Tab */}
        <TabsContent value="subjects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Detaylı Konu Analizi</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Konu</th>
                      <th className="text-left p-2">Doğruluk</th>
                      <th className="text-left p-2">Soru Sayısı</th>
                      <th className="text-left p-2">Süre (saat)</th>
                      <th className="text-left p-2">Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subjectData.map((subject, index) => (
                      <tr key={index} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-medium">{subject.subject}</td>
                        <td className="p-2">
                          <span className={analyticsService.getPerformanceColor(subject.accuracy, 'percentage')}>
                            %{subject.accuracy}
                          </span>
                        </td>
                        <td className="p-2">{subject.questions}</td>
                        <td className="p-2">{subject.hours}</td>
                        <td className="p-2">
                          <span className="text-lg">
                            {analyticsService.getTrendIcon(subject.trend)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Öğrenme Stili Tab */}
        <TabsContent value="learning-style" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Öğrenme Stili Radar */}
            <Card>
              <CardHeader>
                <CardTitle>Öğrenme Stili Profili</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={learningStyleData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="style" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Öğrenme Stili"
                      dataKey="value"
                      stroke="#3B82F6"
                      fill="#3B82F6"
                      fillOpacity={0.3}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Öğrenme Stili Detayları */}
            <Card>
              <CardHeader>
                <CardTitle>Hibrit Profil Detayları</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="font-semibold">Hibrit Kod:
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded">
                      {analytics.learning_style.hybrid_code}
                    </span>
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    Güven Seviyesi: %{Math.round(analytics.learning_style.confidence_level * 100)}
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Öneriler</h4>
                  <ul className="space-y-1">
                    {analytics.learning_style.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-gray-700 flex items-start">
                        <span className="text-blue-600 mr-2">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Sınavlar Tab */}
        <TabsContent value="exams" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Sınav Trend Grafiği */}
            <Card>
              <CardHeader>
                <CardTitle>Sınav Performans Trendi</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={examTrendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="exam" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Sınav İstatistikleri */}
            <Card>
              <CardHeader>
                <CardTitle>Sınav İstatistikleri</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Toplam Sınav</p>
                    <p className="text-xl font-bold">{analytics.exam_performance.total_exams}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Ortalama Puan</p>
                    <p className="text-xl font-bold">{analytics.exam_performance.average_score}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">En Yüksek</p>
                    <p className="text-xl font-bold text-green-600">{analytics.exam_performance.best_score}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">En Düşük</p>
                    <p className="text-xl font-bold text-red-600">{analytics.exam_performance.worst_score}</p>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">Sınav Türleri</h4>
                  {Object.entries(analytics.exam_performance.exam_types).map(([type, data]) => (
                    <div key={type} className="flex justify-between items-center py-1">
                      <span>{type}</span>
                      <span className="text-sm text-gray-600">
                        {data.count} sınav, ort: {data.average}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Detaylı Analiz (eğer aktifse) */}
      {includeDetailed && analytics.detailed_analysis && (
        <Card>
          <CardHeader>
            <CardTitle>Detaylı Analiz</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Çalışma Kalıpları */}
            <div>
              <h4 className="font-semibold mb-2">Çalışma Kalıpları</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p><strong>Tercih Edilen Saatler:</strong></p>
                  <p className="text-gray-600">
                    {analytics.detailed_analysis.study_patterns.preferred_study_hours.join(', ')}
                  </p>
                </div>
                <div>
                  <p><strong>En Aktif Günler:</strong></p>
                  <p className="text-gray-600">
                    {analytics.detailed_analysis.study_patterns.most_active_days.join(', ')}
                  </p>
                </div>
              </div>
            </div>

            {/* Devrimsel Özellik Kullanımı */}
            <div>
              <h4 className="font-semibold mb-2">Devrimsel Özellik Kullanımı</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(analytics.detailed_analysis.revolutionary_features_usage).map(([feature, data]) => (
                  <div key={feature} className="p-3 border rounded">
                    <p className="font-medium">{feature.replace(/_/g, ' ').toUpperCase()}</p>
                    <p className="text-sm text-gray-600">
                      Kullanım: %{Math.round(data.usage_rate * 100)}
                    </p>
                    {data.effectiveness && (
                      <p className="text-sm text-gray-600">
                        Etkinlik: %{Math.round(data.effectiveness * 100)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StudentAnalyticsDashboard;