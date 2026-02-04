/**
 * Admin System Analytics
 * Sistem geneli analytics ve raporlama bileşeni
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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { 
  Users, 
  Activity, 
  Server, 
  Database,
  Clock,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Download,
  RefreshCw,
  Monitor,
  Zap,
  Globe,
  BookOpen,
  Award,
  Target
} from 'lucide-react';
import { analyticsService, AdminAnalytics, ExportRequest } from '../../services/analyticsService';

interface AdminSystemAnalyticsProps {
  className?: string;
}

const AdminSystemAnalytics: React.FC<AdminSystemAnalyticsProps> = ({
  className = ''
}) => {
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState(30);
  const [exporting, setExporting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Analytics verilerini yükle
  useEffect(() => {
    loadAnalytics();
  }, [dateRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const { startDate, endDate } = analyticsService.formatDateRange(dateRange);
      const data = await analyticsService.getAdminAnalytics(startDate, endDate);

      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Admin analytics yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  // Refresh işlemi
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
    setRefreshing(false);
  };

  // Export işlemi
  const handleExport = async (format: 'pdf' | 'excel' | 'csv') => {
    try {
      setExporting(true);

      const { startDate, endDate } = analyticsService.formatDateRange(dateRange);
      const exportRequest: ExportRequest = {
        format,
        data_type: 'admin',
        filters: {
          start_date: startDate,
          end_date: endDate
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

  // Kullanıcı türü dağılım verilerini hazırla
  const prepareUserTypeData = () => {
    if (!analytics?.user_statistics?.user_types) return [];

    return Object.entries(analytics.user_statistics.user_types).map(([type, count]) => ({
      type: type.charAt(0).toUpperCase() + type.slice(1),
      count,
      percentage: Math.round((count / analytics.user_statistics.total_users) * 100)
    }));
  };

  // Sınav türü dağılım verilerini hazırla
  const prepareExamTypeData = () => {
    if (!analytics?.exam_statistics?.exam_types) return [];

    return Object.entries(analytics.exam_statistics.exam_types).map(([type, count]) => ({
      type,
      count,
      average: analytics.exam_statistics.average_scores[type] || 0
    }));
  };

  // İçerik kullanım verilerini hazırla
  const prepareContentUsageData = () => {
    if (!analytics?.content_usage?.content_types) return [];

    return Object.entries(analytics.content_usage.content_types).map(([type, views]) => ({
      type: type.charAt(0).toUpperCase() + type.slice(1),
      views,
      percentage: Math.round((views / analytics.content_usage.total_content_views) * 100)
    }));
  };

  // Devrimsel özellik kullanım verilerini hazırla
  const prepareRevolutionaryFeaturesData = () => {
    if (!analytics?.revolutionary_features) return [];

    return Object.entries(analytics.revolutionary_features).map(([feature, data]) => ({
      feature: feature.replace(/_/g, ' ').toUpperCase(),
      users: data.total_users,
      satisfaction: Math.round(data.user_satisfaction * 100),
      effectiveness: data.effectiveness_score ? Math.round(data.effectiveness_score * 100) : null
    }));
  };

  // Sistem sağlık durumu
  const getSystemHealthStatus = () => {
    if (!analytics) return 'unknown';

    const uptime = analytics.system_metrics.system_uptime_percentage;
    const responseTime = analytics.performance_metrics.api_metrics.average_response_time_ms;
    const errorRate = analytics.performance_metrics.api_metrics.error_rate_percentage;

    if (uptime >= 99.5 && responseTime <= 200 && errorRate <= 0.5) {
      return 'excellent';
    } else if (uptime >= 99.0 && responseTime <= 500 && errorRate <= 1.0) {
      return 'good';
    } else if (uptime >= 98.0 && responseTime <= 1000 && errorRate <= 2.0) {
      return 'warning';
    } else {
      return 'critical';
    }
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Sistem analytics yükleniyor...</span>
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
            <p className="text-gray-600">Admin analytics verisi bulunamadı.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const userTypeData = prepareUserTypeData();
  const examTypeData = prepareExamTypeData();
  const contentUsageData = prepareContentUsageData();
  const revolutionaryFeaturesData = prepareRevolutionaryFeaturesData();
  const systemHealth = getSystemHealthStatus();

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Sistem Analytics</h2>
          <p className="text-gray-600">
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

          {/* Refresh butonu */}
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            Yenile
          </Button>

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

      {/* Sistem Sağlık Durumu */}
      <Card className={`border-2 ${
        systemHealth === 'excellent' ? 'border-green-200 bg-green-50' :
        systemHealth === 'good' ? 'border-blue-200 bg-blue-50' :
        systemHealth === 'warning' ? 'border-yellow-200 bg-yellow-50' :
        'border-red-200 bg-red-50'
      }`}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {systemHealth === 'excellent' ? (
                <CheckCircle className="w-8 h-8 text-green-600" />
              ) : systemHealth === 'good' ? (
                <CheckCircle className="w-8 h-8 text-blue-600" />
              ) : systemHealth === 'warning' ? (
                <AlertCircle className="w-8 h-8 text-yellow-600" />
              ) : (
                <AlertCircle className="w-8 h-8 text-red-600" />
              )}
              <div>
                <h3 className="text-lg font-bold">Sistem Sağlık Durumu</h3>
                <p className={`text-sm ${
                  systemHealth === 'excellent' ? 'text-green-600' :
                  systemHealth === 'good' ? 'text-blue-600' :
                  systemHealth === 'warning' ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {systemHealth === 'excellent' ? 'Mükemmel' :
                   systemHealth === 'good' ? 'İyi' :
                   systemHealth === 'warning' ? 'Dikkat' : 'Kritik'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Uptime</p>
              <p className="text-xl font-bold">
                %{analytics.system_metrics.system_uptime_percentage}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Özet Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Toplam Kullanıcı</p>
                <p className="text-2xl font-bold">
                  {analytics.user_statistics.total_users.toLocaleString()}
                </p>
                <p className="text-xs text-green-600">
                  +{analytics.user_statistics.new_registrations} yeni
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Aktif Kullanıcı</p>
                <p className="text-2xl font-bold">
                  {analytics.user_statistics.active_users.toLocaleString()}
                </p>
                <p className="text-xs text-gray-600">
                  %{Math.round((analytics.user_statistics.active_users / analytics.user_statistics.total_users) * 100)} oran
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Toplam Sınav</p>
                <p className="text-2xl font-bold">
                  {analytics.exam_statistics.total_exams_taken.toLocaleString()}
                </p>
              </div>
              <BookOpen className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">API Yanıt Süresi</p>
                <p className="text-2xl font-bold">
                  {analytics.performance_metrics.api_metrics.average_response_time_ms}ms
                </p>
              </div>
              <Zap className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ana İçerik - Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
          <TabsTrigger value="users">Kullanıcılar</TabsTrigger>
          <TabsTrigger value="content">İçerik</TabsTrigger>
          <TabsTrigger value="performance">Performans</TabsTrigger>
          <TabsTrigger value="revolutionary">Devrimsel</TabsTrigger>
        </TabsList>

        {/* Genel Bakış Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Kullanıcı Türü Dağılımı */}
            <Card>
              <CardHeader>
                <CardTitle>Kullanıcı Türü Dağılımı</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={userTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ type, percentage }) => `${type}: %${percentage}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {userTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Sınav Türü Performansı */}
            <Card>
              <CardHeader>
                <CardTitle>Sınav Türü Performansı</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={examTypeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="average" fill="#3B82F6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Sistem Metrikleri */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Server className="w-5 h-5 mr-2" />
                  Sistem Metrikleri
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Toplam Oturum</span>
                  <span className="font-medium">{analytics.system_metrics.total_sessions.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Ort. Oturum Süresi</span>
                  <span className="font-medium">{analytics.system_metrics.average_session_duration_minutes}dk</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Toplam Soru</span>
                  <span className="font-medium">{analytics.system_metrics.total_questions_solved.toLocaleString()}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="w-5 h-5 mr-2" />
                  Veritabanı
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Sorgu Performansı</span>
                  <span className="font-medium">{analytics.performance_metrics.database_metrics.query_performance_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Bağlantı Havuzu</span>
                  <span className="font-medium">%{Math.round(analytics.performance_metrics.database_metrics.connection_pool_usage * 100)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Yavaş Sorgular</span>
                  <span className="font-medium">{analytics.performance_metrics.database_metrics.slow_queries_count}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Monitor className="w-5 h-5 mr-2" />
                  Cache Metrikleri
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Hit Rate</span>
                  <span className="font-medium text-green-600">%{analytics.performance_metrics.cache_metrics.hit_rate_percentage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Miss Rate</span>
                  <span className="font-medium text-red-600">%{analytics.performance_metrics.cache_metrics.miss_rate_percentage}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Eviction Rate</span>
                  <span className="font-medium">%{Math.round(analytics.performance_metrics.cache_metrics.eviction_rate * 100)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Kullanıcılar Tab */}
        <TabsContent value="users" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Kullanıcı İstatistikleri</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 border rounded">
                      <p className="text-2xl font-bold text-green-600">
                        %{Math.round(analytics.user_statistics.retention_rate * 100)}
                      </p>
                      <p className="text-sm text-gray-600">Retention Rate</p>
                    </div>
                    <div className="text-center p-4 border rounded">
                      <p className="text-2xl font-bold text-red-600">
                        %{Math.round(analytics.user_statistics.churn_rate * 100)}
                      </p>
                      <p className="text-sm text-gray-600">Churn Rate</p>
                    </div>
                  </div>
                  
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={userTypeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="type" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3B82F6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Kullanıcı Detayları</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {userTypeData.map((user, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="font-medium">{user.type}</p>
                        <p className="text-sm text-gray-600">{user.count.toLocaleString()} kullanıcı</p>
                      </div>
                      <Badge variant="secondary">
                        %{user.percentage}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* İçerik Tab */}
        <TabsContent value="content" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>İçerik Kullanımı</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={contentUsageData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="views" fill="#10B981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Engagement Metrikleri</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-3">
                  <div className="p-3 border rounded">
                    <p className="text-sm text-gray-600">Ortalama Görüntüleme Süresi</p>
                    <p className="text-xl font-bold">
                      {analytics.content_usage.engagement_metrics.average_view_duration_minutes} dakika
                    </p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-sm text-gray-600">Bounce Rate</p>
                    <p className="text-xl font-bold text-red-600">
                      %{Math.round(analytics.content_usage.engagement_metrics.bounce_rate * 100)}
                    </p>
                  </div>
                  <div className="p-3 border rounded">
                    <p className="text-sm text-gray-600">Completion Rate</p>
                    <p className="text-xl font-bold text-green-600">
                      %{Math.round(analytics.content_usage.engagement_metrics.completion_rate * 100)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Performans Tab */}
        <TabsContent value="performance" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>API Performansı</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Ortalama Yanıt</span>
                  <span className={`font-bold ${analyticsService.getPerformanceColor(analytics.performance_metrics.api_metrics.average_response_time_ms, 'time')}`}>
                    {analytics.performance_metrics.api_metrics.average_response_time_ms}ms
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">P95 Yanıt</span>
                  <span className={`font-bold ${analyticsService.getPerformanceColor(analytics.performance_metrics.api_metrics.p95_response_time_ms, 'time')}`}>
                    {analytics.performance_metrics.api_metrics.p95_response_time_ms}ms
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">P99 Yanıt</span>
                  <span className={`font-bold ${analyticsService.getPerformanceColor(analytics.performance_metrics.api_metrics.p99_response_time_ms, 'time')}`}>
                    {analytics.performance_metrics.api_metrics.p99_response_time_ms}ms
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Hata Oranı</span>
                  <span className={`font-bold ${analytics.performance_metrics.api_metrics.error_rate_percentage <= 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                    %{analytics.performance_metrics.api_metrics.error_rate_percentage}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Throughput</span>
                  <span className="font-bold">
                    {analytics.performance_metrics.api_metrics.throughput_requests_per_second} req/s
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Veritabanı Performansı</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Sorgu Performansı</span>
                  <span className={`font-bold ${analyticsService.getPerformanceColor(analytics.performance_metrics.database_metrics.query_performance_ms, 'time')}`}>
                    {analytics.performance_metrics.database_metrics.query_performance_ms}ms
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Bağlantı Havuzu</span>
                  <span className={`font-bold ${analyticsService.getPerformanceColor(analytics.performance_metrics.database_metrics.connection_pool_usage * 100, 'percentage')}`}>
                    %{Math.round(analytics.performance_metrics.database_metrics.connection_pool_usage * 100)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Yavaş Sorgular</span>
                  <span className={`font-bold ${analytics.performance_metrics.database_metrics.slow_queries_count <= 10 ? 'text-green-600' : 'text-red-600'}`}>
                    {analytics.performance_metrics.database_metrics.slow_queries_count}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cache Performansı</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Hit Rate</span>
                  <span className={`font-bold ${analyticsService.getPerformanceColor(analytics.performance_metrics.cache_metrics.hit_rate_percentage, 'percentage')}`}>
                    %{analytics.performance_metrics.cache_metrics.hit_rate_percentage}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Miss Rate</span>
                  <span className="font-bold text-red-600">
                    %{analytics.performance_metrics.cache_metrics.miss_rate_percentage}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Eviction Rate</span>
                  <span className="font-bold">
                    %{Math.round(analytics.performance_metrics.cache_metrics.eviction_rate * 100)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Devrimsel Özellikler Tab */}
        <TabsContent value="revolutionary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Award className="w-5 h-5 mr-2" />
                Devrimsel Özellik Kullanımı
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {revolutionaryFeaturesData.map((feature, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <h4 className="font-semibold text-sm mb-2">{feature.feature}</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-600">Kullanıcı</span>
                        <span className="text-sm font-medium">{feature.users.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-xs text-gray-600">Memnuniyet</span>
                        <span className={`text-sm font-medium ${analyticsService.getPerformanceColor(feature.satisfaction, 'percentage')}`}>
                          %{feature.satisfaction}
                        </span>
                      </div>
                      {feature.effectiveness && (
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-600">Etkinlik</span>
                          <span className={`text-sm font-medium ${analyticsService.getPerformanceColor(feature.effectiveness, 'percentage')}`}>
                            %{feature.effectiveness}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminSystemAnalytics;