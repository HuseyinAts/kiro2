import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Users, 
  TrendingUp, 
  Bell, 
  Calendar, 
  BookOpen,
  Clock,
  Award,
  AlertCircle
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

interface ParentNotification {
  id: number;
  child_id: number;
  child_name: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
}

interface DashboardData {
  children: ChildPerformance[];
  unread_notifications: number;
  recent_notifications: ParentNotification[];
  weekly_summary: {
    total_children: number;
    active_children: number;
    average_performance: number;
  };
  pending_approvals: any[];
}

export const ParentDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChild, setSelectedChild] = useState<number | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await parentService.getDashboardData();
      setDashboardData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Dashboard verileri yüklenirken hata oluştu');
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

  if (!dashboardData) {
    return (
      <Alert className="m-4">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Dashboard verileri yüklenemedi</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Veli Paneli</h1>
        <Button onClick={loadDashboardData} variant="outline">
          Yenile
        </Button>
      </div>

      {/* Bekleyen Onaylar */}
      {dashboardData.pending_approvals.length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {dashboardData.pending_approvals.length} adet onay bekleyen veli isteğiniz bulunmaktadır.
          </AlertDescription>
        </Alert>
      )}

      {/* Özet Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Toplam Çocuk</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.weekly_summary.total_children}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aktif Çocuk</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.weekly_summary.active_children}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ortalama Başarı</CardTitle>
            <Award className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getPerformanceColor(dashboardData.weekly_summary.average_performance)}`}>
              {dashboardData.weekly_summary.average_performance.toFixed(1)}%
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Okunmamış Bildirim</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.unread_notifications}</div>
          </CardContent>
        </Card>
      </div>

      {/* Çocukların Performansı */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Çocukların Performansı
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dashboardData.children.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              Henüz onaylanmış çocuk bulunmamaktadır.
            </p>
          ) : (
            <div className="space-y-4">
              {dashboardData.children.map((child) => (
                <div
                  key={child.child_id}
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedChild(child.child_id)}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-lg">{child.child_name}</h3>
                      <Badge className={getPerformanceBadge(child.average_score)}>
                        Ortalama: {child.average_score.toFixed(1)}%
                      </Badge>
                    </div>
                    <div className="text-right text-sm text-gray-600">
                      {child.last_exam_date && (
                        <p>Son Sınav: {new Date(child.last_exam_date).toLocaleDateString('tr-TR')}</p>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-blue-500" />
                      <span>Çalışma: {formatStudyTime(child.total_study_time)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-4 w-4 text-green-500" />
                      <span>Sınav: {child.exams_taken}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-red-500" />
                      <span>Zayıf: {child.weak_subjects.join(', ') || 'Yok'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Award className="h-4 w-4 text-yellow-500" />
                      <span>Güçlü: {child.strong_subjects.join(', ') || 'Yok'}</span>
                    </div>
                  </div>

                  {child.recent_achievements.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-sm font-medium text-green-700">Son Başarılar:</p>
                      <ul className="text-sm text-green-600 mt-1">
                        {child.recent_achievements.map((achievement, index) => (
                          <li key={index}>• {achievement}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Son Bildirimler */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Son Bildirimler
          </CardTitle>
        </CardHeader>
        <CardContent>
          {dashboardData.recent_notifications.length === 0 ? (
            <p className="text-gray-500 text-center py-4">
              Henüz bildirim bulunmamaktadır.
            </p>
          ) : (
            <div className="space-y-3">
              {dashboardData.recent_notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`border rounded-lg p-3 ${
                    !notification.is_read ? 'bg-blue-50 border-blue-200' : 'bg-gray-50'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium">{notification.title}</h4>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{notification.child_name}</Badge>
                      {!notification.is_read && (
                        <Badge className="bg-blue-500">Yeni</Badge>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{notification.message}</p>
                  <p className="text-xs text-gray-400">
                    {new Date(notification.created_at).toLocaleString('tr-TR')}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};