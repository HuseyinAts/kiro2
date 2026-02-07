import {
  Bell,
  BellRing,
  CheckCircle,
  Clock,
  Award,
  TrendingUp,
  AlertCircle,
  Filter,
} from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { LoadingSpinner } from '@/components/Common/LoadingStates';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { parentService } from '@/services/parentService';

interface ParentNotification {
  id: number;
  child_id: number;
  child_name: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

export const ParentNotifications: React.FC = () => {
  const [notifications, setNotifications] = useState<ParentNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [markingAsRead, setMarkingAsRead] = useState<number | null>(null);

  useEffect(() => {
    loadNotifications();
  }, [filter]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await parentService.getNotifications(filter === 'unread');
      setNotifications(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Bildirimler yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: number) => {
    try {
      setMarkingAsRead(notificationId);
      await parentService.markNotificationAsRead(notificationId);

      // Update local state
      setNotifications(prev =>
        prev.map(notification =>
          notification.id === notificationId
            ? { ...notification, is_read: true, read_at: new Date().toISOString() }
            : notification,
        ),
      );
    } catch (err: any) {
      setError(err.message || 'Bildirim güncellenirken hata oluştu');
    } finally {
      setMarkingAsRead(null);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'performance':
        return <TrendingUp className="h-4 w-4 text-blue-600" />;
      case 'exam':
        return <Clock className="h-4 w-4 text-orange-600" />;
      case 'achievement':
        return <Award className="h-4 w-4 text-yellow-600" />;
      case 'approval':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      default:
        return <Bell className="h-4 w-4 text-gray-600" />;
    }
  };

  const getNotificationTypeText = (type: string) => {
    switch (type) {
      case 'performance':
        return 'Performans';
      case 'exam':
        return 'Sınav';
      case 'achievement':
        return 'Başarı';
      case 'approval':
        return 'Onay';
      case 'reminder':
        return 'Hatırlatma';
      default:
        return 'Bildirim';
    }
  };

  const getNotificationTypeBadge = (type: string) => {
    switch (type) {
      case 'performance':
        return 'bg-blue-100 text-blue-800';
      case 'exam':
        return 'bg-orange-100 text-orange-800';
      case 'achievement':
        return 'bg-yellow-100 text-yellow-800';
      case 'approval':
        return 'bg-green-100 text-green-800';
      case 'reminder':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Bell className="h-6 w-6" />
            Bildirimler
            {unreadCount > 0 && (
              <Badge className="bg-red-500 text-white">
                {unreadCount} yeni
              </Badge>
            )}
          </h2>
          <p className="text-gray-600">Çocuklarınızla ilgili güncellemeler</p>
        </div>
        <Button onClick={loadNotifications} variant="outline">
          Yenile
        </Button>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Filter Buttons */}
      <div className="flex gap-2">
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          onClick={() => setFilter('all')}
          className="flex items-center gap-2"
        >
          <Filter className="h-4 w-4" />
          Tümü ({notifications.length})
        </Button>
        <Button
          variant={filter === 'unread' ? 'default' : 'outline'}
          onClick={() => setFilter('unread')}
          className="flex items-center gap-2"
        >
          <BellRing className="h-4 w-4" />
          Okunmamış ({unreadCount})
        </Button>
      </div>

      {/* Notifications List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            {filter === 'all' ? 'Tüm Bildirimler' : 'Okunmamış Bildirimler'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {notifications.length === 0 ? (
            <div className="text-center py-8">
              <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">
                {filter === 'unread' ? 'Okunmamış bildirim bulunmamaktadır' : 'Henüz bildirim bulunmamaktadır'}
              </p>
              <p className="text-sm text-gray-400">
                Çocuklarınızın aktiviteleri hakkında bildirimler burada görünecektir
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`border rounded-lg p-4 transition-colors ${
                    !notification.is_read
                      ? 'bg-blue-50 border-blue-200 shadow-sm'
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-start gap-3">
                      {getNotificationIcon(notification.notification_type)}
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-900">
                            {notification.title}
                          </h3>
                          {!notification.is_read && (
                            <Badge className="bg-blue-500 text-white text-xs">
                              Yeni
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {notification.message}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <Badge className={getNotificationTypeBadge(notification.notification_type)}>
                        {getNotificationTypeText(notification.notification_type)}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {notification.child_name}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="text-xs text-gray-500">
                      <p>
                        Gönderilme: {new Date(notification.created_at).toLocaleString('tr-TR')}
                      </p>
                      {notification.read_at && (
                        <p>
                          Okunma: {new Date(notification.read_at).toLocaleString('tr-TR')}
                        </p>
                      )}
                    </div>

                    {!notification.is_read && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleMarkAsRead(notification.id)}
                        disabled={markingAsRead === notification.id}
                        className="flex items-center gap-2"
                      >
                        {markingAsRead === notification.id ? (
                          <LoadingSpinner size="sm" />
                        ) : (
                          <CheckCircle className="h-3 w-3" />
                        )}
                        Okundu İşaretle
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Bildirim Türleri</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• <strong>Performans:</strong> Çocuğunuzun başarı durumu değişiklikleri</li>
                <li>• <strong>Sınav:</strong> Sınav sonuçları ve değerlendirmeler</li>
                <li>• <strong>Başarı:</strong> Özel başarılar ve ödüller</li>
                <li>• <strong>Onay:</strong> Veli ilişkisi onay durumları</li>
                <li>• <strong>Hatırlatma:</strong> Önemli tarih ve etkinlikler</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};