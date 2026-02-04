/**
 * Teacher Class Analytics
 * Öğretmen sınıf analizi ve raporlama bileşeni
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
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
  Cell,
  LineChart,
  Line,
  ScatterChart,
  Scatter
} from 'recharts';
import { 
  Users, 
  TrendingUp, 
  Award, 
  BookOpen,
  Download,
  Search,
  Filter,
  Eye,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { analyticsService, ClassAnalytics, ExportRequest } from '../../services/analyticsService';

interface TeacherClassAnalyticsProps {
  classId: string;
  className?: string;
}

const TeacherClassAnalytics: React.FC<TeacherClassAnalyticsProps> = ({
  classId,
  className = ''
}) => {
  const [analytics, setAnalytics] = useState<ClassAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState(30);
  const [includeStudents, setIncludeStudents] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<string | null>(null);

  // Analytics verilerini yükle
  useEffect(() => {
    loadAnalytics();
  }, [classId, dateRange, includeStudents]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const { startDate, endDate } = analyticsService.formatDateRange(dateRange);
      const data = await analyticsService.getClassAnalytics(
        classId,
        startDate,
        endDate,
        includeStudents
      );

      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sınıf analytics yüklenirken hata oluştu');
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
        data_type: 'class',
        filters: {
          class_id: classId,
          start_date: startDate,
          end_date: endDate,
          include_students: includeStudents
        }
      };

      let response;
      if (format === 'pdf') {
        response = await analyticsService.exportToPdf(exportRequest);
        analyticsService.downloadExportFile(
          response.data.pdf_content!,
          response.data.filename,
          'pdf'
        );
      } else if (format === 'excel') {
        response = await analyticsService.exportToExcel(exportRequest);
        analyticsService.downloadExportFile(
          response.data.excel_content!,
          response.data.filename,
          'excel'
        );
      } else {
        response = await analyticsService.exportToCsv(exportRequest);
        analyticsService.downloadExportFile(
          response.data.csv_content!,
          response.data.filename,
          'csv'
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export işlemi başarısız');
    } finally {
      setExporting(false);
    }
  };

  // Performans dağılım verilerini hazırla
  const preparePerformanceDistribution = () => {
    if (!analytics?.performance_distribution?.score_distribution) return [];

    return Object.entries(analytics.performance_distribution.score_distribution).map(([range, count]) => ({
      range,
      count,
      percentage: Math.round((count / analytics.student_count) * 100)
    }));
  };

  // Konu performans verilerini hazırla
  const prepareSubjectData = () => {
    if (!analytics?.subject_analysis?.subject_averages) return [];

    return Object.entries(analytics.subject_analysis.subject_averages).map(([subject, average]) => ({
      subject,
      average: Math.round(average),
      color: average >= 80 ? '#10B981' : average >= 60 ? '#F59E0B' : '#EF4444'
    }));
  };

  // Öğrenme stili dağılım verilerini hazırla
  const prepareLearningStyleDistribution = () => {
    if (!analytics?.learning_style_distribution?.vark_distribution) return [];

    return Object.entries(analytics.learning_style_distribution.vark_distribution).map(([style, percentage]) => ({
      style: style.charAt(0).toUpperCase() + style.slice(1),
      value: Math.round(percentage * 100),
      color: analyticsService.getLearningStyleColor(style).split(' ')[0].replace('bg-', '#')
    }));
  };

  // Öğrenci listesini filtrele
  const filteredStudents = analytics?.student_details?.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Sınıf analytics yükleniyor...</span>
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
            <p className="text-gray-600">Sınıf analytics verisi bulunamadı.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const performanceData = preparePerformanceDistribution();
  const subjectData = prepareSubjectData();
  const learningStyleData = prepareLearningStyleDistribution();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Sınıf Analytics</h2>
          <p className="text-gray-600">
            Sınıf ID: {analytics.class_id} | 
            Öğrenci Sayısı: {analytics.student_count} |
            Dönem: {new Date(analytics.period.start_date).toLocaleDateString('tr-TR')} - 
            {new Date(analytics.period.end_date).toLocaleDateString('tr-TR')}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Tarih aralığı seçici */}
          <select
            value={dateRange}
            onChange={(e) => setDateRange(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value={7}>Son 7 gün</option>
            <option value={30}>Son 30 gün</option>
            <option value={90}>Son 3 ay</option>
            <option value={365}>Son 1 yıl</option>
          </select>

          {/* Öğrenci detayları toggle */}
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={includeStudents}
              onChange={(e) => setIncludeStudents(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm">Öğrenci Detayları</span>
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
          </div>
        </div>
      </div>

      {/* Özet Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Ortalama Çalışma</p>
                <p className="text-2xl font-bold">
                  {analytics.class_metrics.average_study_time_hours}h
                </p>
              </div>
              <BookOpen className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Toplam Soru</p>
                <p className="text-2xl font-bold">
                  {analytics.class_metrics.total_questions_solved.toLocaleString()}
                </p>
              </div>
              <Award className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Sınıf Doğruluğu</p>
                <p className="text-2xl font-bold">
                  %{Math.round(analytics.class_metrics.class_accuracy_rate * 100)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Aktif Öğrenci</p>
                <p className="text-2xl font-bold">
                  %{Math.round(analytics.class_metrics.active_students_percentage * 100)}
                </p>
              </div>
              <Users className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ana İçerik - Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
          <TabsTrigger value="performance">Performans</TabsTrigger>
          <TabsTrigger value="subjects">Konular</TabsTrigger>
          <TabsTrigger value="students">Öğrenciler</TabsTrigger>
        </TabsList>

        {/* Genel Bakış Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Performans Dağılımı */}
            <Card>
              <CardHeader>
                <CardTitle>Performans Dağılımı</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={performanceData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ range, percentage }) => `${range}: %${percentage}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {performanceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Öğrenme Stili Dağılımı */}
            <Card>
              <CardHeader>
                <CardTitle>Öğrenme Stili Dağılımı</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={learningStyleData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="style" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Zorlayıcı ve Güçlü Konular */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-red-600">
                  <AlertTriangle className="w-5 h-5 mr-2" />
                  Zorlayıcı Konular
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.subject_analysis.challenging_topics.map((topic, index) => (
                    <div key={index} className="p-2 bg-red-50 border border-red-200 rounded">
                      <p className="text-sm text-red-800">{topic}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center text-green-600">
                  <CheckCircle className="w-5 h-5 mr-2" />
                  Güçlü Konular
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.subject_analysis.strong_topics.map((topic, index) => (
                    <div key={index} className="p-2 bg-green-50 border border-green-200 rounded">
                      <p className="text-sm text-green-800">{topic}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Performans Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performans Seviyeleri</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                {Object.entries(analytics.performance_distribution.performance_levels).map(([level, count]) => (
                  <div key={level} className="text-center p-4 border rounded">
                    <p className="text-2xl font-bold">{count}</p>
                    <p className="text-sm text-gray-600 capitalize">{level.replace('_', ' ')}</p>
                  </div>
                ))}
              </div>

              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Konular Tab */}
        <TabsContent value="subjects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Konu Ortalamaları</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={subjectData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis dataKey="subject" type="category" width={100} />
                  <Tooltip />
                  <Bar dataKey="average" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Öğrenciler Tab */}
        <TabsContent value="students" className="space-y-4">
          {includeStudents && analytics.student_details ? (
            <>
              {/* Öğrenci Arama */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <Search className="w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Öğrenci ara..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                    />
                    <Button variant="outline" size="sm">
                      <Filter className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Öğrenci Listesi */}
              <Card>
                <CardHeader>
                  <CardTitle>Öğrenci Detayları ({filteredStudents.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Öğrenci</th>
                          <th className="text-left p-2">Toplam Etkinlik</th>
                          <th className="text-left p-2">Son Aktivite</th>
                          <th className="text-left p-2">Durum</th>
                          <th className="text-left p-2">İşlemler</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredStudents.map((student, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="p-2">
                              <div>
                                <p className="font-medium">{student.name}</p>
                                <p className="text-sm text-gray-600">ID: {student.student_id}</p>
                              </div>
                            </td>
                            <td className="p-2">
                              <p className="text-sm">
                                {student.analytics?.total_events || 0} etkinlik
                              </p>
                            </td>
                            <td className="p-2">
                              <p className="text-sm text-gray-600">
                                {new Date().toLocaleDateString('tr-TR')}
                              </p>
                            </td>
                            <td className="p-2">
                              <Badge 
                                variant="secondary" 
                                className={
                                  (student.analytics?.total_events || 0) > 50 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-yellow-100 text-yellow-800'
                                }
                              >
                                {(student.analytics?.total_events || 0) > 50 ? 'Aktif' : 'Orta'}
                              </Badge>
                            </td>
                            <td className="p-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setSelectedStudent(student.student_id)}
                              >
                                <Eye className="w-4 h-4 mr-1" />
                                Detay
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="p-4">
                <p className="text-gray-600">
                  Öğrenci detaylarını görmek için "Öğrenci Detayları" seçeneğini aktifleştirin.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Seçili Öğrenci Modal (basit implementasyon) */}
      {selectedStudent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Öğrenci Detayları</h3>
            <p className="text-gray-600 mb-4">
              Öğrenci ID: {selectedStudent}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Detaylı öğrenci analytics için StudentAnalyticsDashboard bileşeni kullanılabilir.
            </p>
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => setSelectedStudent(null)}
              >
                Kapat
              </Button>
              <Button onClick={() => setSelectedStudent(null)}>
                Detaylı Analiz
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeacherClassAnalytics;