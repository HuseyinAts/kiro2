import {
  Bell,
  Send,
  Plus,
  Check,
  AlertCircle,
  Info,
  CheckCircle,
  X,
} from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

interface Notification {
  bildirim_id: string;
  baslik: string;
  mesaj: string;
  tip: string;
  olusturma_tarihi: string;
  okundu: boolean;
}

interface NotificationData {
  bildirimler: Notification[];
  toplam: number;
  okunmamis: number;
}

interface NewNotification {
  baslik: string;
  mesaj: string;
  tip: string;
}

const TeacherNotifications: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newNotification, setNewNotification] = useState<NewNotification>({
    baslik: '',
    mesaj: '',
    tip: 'bilgi',
  });
  const [sendingNotification, setSendingNotification] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch('/api/v1/ogretmen/bildirimler?limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Bildirimler alınamadı');
      }

      const result = await response.json();
      if (result.success) {
        setNotifications(result.data);
      } else {
        throw new Error(result.message || 'Veri alınamadı');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  const sendNotification = async () => {
    if (!newNotification.baslik.trim() || !newNotification.mesaj.trim()) {
      setError('Başlık ve mesaj alanları zorunludur');
      return;
    }

    try {
      setSendingNotification(true);
      setError(null);
      const token = localStorage.getItem('token');

      const response = await fetch('/api/v1/ogretmen/bildirim', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newNotification),
      });

      if (!response.ok) {
        throw new Error('Bildirim gönderilemedi');
      }

      const result = await response.json();
      if (result.success) {
        // Formu temizle
        setNewNotification({
          baslik: '',
          mesaj: '',
          tip: 'bilgi',
        });
        setShowCreateForm(false);

        // Bildirimleri yenile
        await fetchNotifications();
      } else {
        throw new Error(result.message || 'Bildirim gönderilemedi');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bildirim gönderme hatası');
    } finally {
      setSendingNotification(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      const token = localStorage.getItem('token');

      const response = await fetch(`/api/v1/ogretmen/bildirim/${notificationId}/okundu`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // Bildirimi okundu olarak işaretle
        setNotifications(prev => {
          if (!prev) {return prev;}

          return {
            ...prev,
            bildirimler: prev.bildirimler.map(bildirim =>
              bildirim.bildirim_id === notificationId
                ? { ...bildirim, okundu: true }
                : bildirim,
            ),
            okunmamis: Math.max(0, prev.okunmamis - 1),
          };
        });
      }
    } catch (err) {
      console.error('Bildirim okundu işaretleme hatası:', err);
    }
  };

  const getNotificationIcon = (tip: string) => {
    switch (tip) {
      case 'basari':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'uyari':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />;
      case 'hata':
        return <X className="h-5 w-5 text-red-600" />;
      default:
        return <Info className="h-5 w-5 text-blue-600" />;
    }
  };

  const getNotificationColor = (tip: string) => {
    switch (tip) {
      case 'basari':
        return 'border-green-200 bg-green-50';
      case 'uyari':
        return 'border-yellow-200 bg-yellow-50';
      case 'hata':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getNotificationBadgeColor = (tip: string) => {
    switch (tip) {
      case 'basari':
        return 'bg-green-100 text-green-800';
      case 'uyari':
        return 'bg-yellow-100 text-yellow-800';
      case 'hata':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Bildirimler</h1>
          <p className="text-gray-600 mt-1">
            Bildirim yönetimi ve geçmiş
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Bildirim
        </Button>
      </div>

      {error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Bildirim Oluşturma Formu */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Send className="h-5 w-5 mr-2" />
              Yeni Bildirim Oluştur
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="notification-title">Başlık</Label>
              <Input
                id="notification-title"
                placeholder="Bildirim başlığı..."
                value={newNotification.baslik}
                onChange={(e) => setNewNotification(prev => ({
                  ...prev,
                  baslik: e.target.value,
                }))}
              />
            </div>

            <div>
              <Label htmlFor="notification-type">Bildirim Türü</Label>
              <Select
                value={newNotification.tip}
                onValueChange={(value) => setNewNotification(prev => ({
                  ...prev,
                  tip: value,
                }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bilgi">Bilgi</SelectItem>
                  <SelectItem value="basari">Başarı</SelectItem>
                  <SelectItem value="uyari">Uyarı</SelectItem>
                  <SelectItem value="hata">Hata</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="notification-message">Mesaj</Label>
              <Textarea
                id="notification-message"
                placeholder="Bildirim mesajı..."
                rows={4}
                value={newNotification.mesaj}
                onChange={(e) => setNewNotification(prev => ({
                  ...prev,
                  mesaj: e.target.value,
                }))}
              />
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={sendNotification}
                disabled={sendingNotification}
              >
                {sendingNotification ? 'Gönderiliyor...' : 'Bildirim Gönder'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowCreateForm(false)}
              >
                İptal
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bildirim İstatistikleri */}
      {notifications && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Bell className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Toplam Bildirim</p>
                  <p className="text-2xl font-bold">{notifications.toplam}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <AlertCircle className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Okunmamış</p>
                  <p className="text-2xl font-bold">{notifications.okunmamis}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Okunmuş</p>
                  <p className="text-2xl font-bold">{notifications.toplam - notifications.okunmamis}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Bildirim Listesi */}
      <Card>
        <CardHeader>
          <CardTitle>Bildirim Geçmişi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {notifications && notifications.bildirimler.length > 0 ? (
              notifications.bildirimler.map((bildirim) => (
                <div
                  key={bildirim.bildirim_id}
                  className={`p-4 border rounded-lg ${getNotificationColor(bildirim.tip)} ${!bildirim.okundu ? 'border-l-4 border-l-blue-500' : ''}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      {getNotificationIcon(bildirim.tip)}

                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h3 className={`font-semibold ${!bildirim.okundu ? 'text-gray-900' : 'text-gray-700'}`}>
                            {bildirim.baslik}
                          </h3>
                          <Badge className={getNotificationBadgeColor(bildirim.tip)}>
                            {bildirim.tip}
                          </Badge>
                          {!bildirim.okundu && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          )}
                        </div>

                        <p className={`text-sm ${!bildirim.okundu ? 'text-gray-800' : 'text-gray-600'}`}>
                          {bildirim.mesaj}
                        </p>

                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(bildirim.olusturma_tarihi).toLocaleString('tr-TR')}
                        </p>
                      </div>
                    </div>

                    {!bildirim.okundu && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => markAsRead(bildirim.bildirim_id)}
                      >
                        <Check className="h-4 w-4 mr-1" />
                        Okundu
                      </Button>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Henüz bildirim bulunmuyor</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherNotifications;