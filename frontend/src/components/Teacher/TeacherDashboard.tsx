import {
  Users,
  BookOpen,
  TrendingUp,
  Bell,
  Calendar,
  BarChart3,
  FileText,
  Settings,
} from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect  } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface DashboardStats {
  toplam_ogrenci: number;
  aktif_sinavlar: number;
  ortalama_basari: number;
  son_guncelleme: string;
}

interface StudentSummary {
  ogrenci_id: string;
  ad_soyad: string;
  sinif_seviyesi: number;
  performans: {
    ortalama_net: number;
    toplam_sinav: number;
    gelisim_trendi: string;
  };
  aktif: boolean;
}

interface Notification {
  bildirim_id: string;
  baslik: string;
  mesaj: string;
  tip: string;
  olusturma_tarihi: string;
  okundu: boolean;
}

interface TeacherProfile {
  ogretmen_id: string;
  okul_adi: string;
  brans: string;
  deneyim_yili?: number;
}

interface DashboardData {
  ogretmen_profili: TeacherProfile;
  genel_istatistikler: DashboardStats;
  ogrenci_listesi: StudentSummary[];
  son_bildirimler: Notification[];
}

const TeacherDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch('/api/v1/ogretmen/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Dashboard verisi alınamadı');
      }

      const result = await response.json();
      if (result.success) {
        setDashboardData(result.data);
      } else {
        throw new Error(result.message || 'Veri alınamadı');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'artan':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'azalan':
        return <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />;
      default:
        return <TrendingUp className="h-4 w-4 text-gray-500" />;
    }
  };

  const getNotificationColor = (tip: string) => {
    switch (tip) {
      case 'basari':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'uyari':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'hata':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <AlertDescription>
          Hata: {error}
          <Button
            onClick={fetchDashboardData}
            className="ml-4"
            size="sm"
          >
            Tekrar Dene
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert className="m-4">
        <AlertDescription>Dashboard verisi bulunamadı</AlertDescription>
      </Alert>
    );
  }

  const { ogretmen_profili, genel_istatistikler, ogrenci_listesi, son_bildirimler } = dashboardData;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Öğretmen Paneli</h1>
          <p className="text-gray-600 mt-1">
            {ogretmen_profili.okul_adi} - {ogretmen_profili.brans}
            {ogretmen_profili.deneyim_yili && ` (${ogretmen_profili.deneyim_yili} yıl deneyim)`}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Settings className="h-4 w-4 mr-2" />
            Ayarlar
          </Button>
          <Button size="sm">
            <FileText className="h-4 w-4 mr-2" />
            Rapor Oluştur
          </Button>
        </div>
      </div>

      {/* İstatistik Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Toplam Öğrenci</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{genel_istatistikler.toplam_ogrenci}</div>
            <p className="text-xs text-muted-foreground">
              Sorumlu olduğunuz öğrenci sayısı
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aktif Sınavlar</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{genel_istatistikler.aktif_sinavlar}</div>
            <p className="text-xs text-muted-foreground">
              Devam eden sınav sayısı
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Ortalama Başarı</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{genel_istatistikler.ortalama_basari.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">
              Sınıf ortalaması (net)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Son Güncelleme</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold">
              {new Date(genel_istatistikler.son_guncelleme).toLocaleDateString('tr-TR')}
            </div>
            <p className="text-xs text-muted-foreground">
              {new Date(genel_istatistikler.son_guncelleme).toLocaleTimeString('tr-TR')}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Öğrenci Listesi Özeti */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Öğrenci Performans Özeti
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {ogrenci_listesi.length > 0 ? (
                ogrenci_listesi.map((ogrenci) => (
                  <div key={ogrenci.ogrenci_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${ogrenci.aktif ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                      <div>
                        <p className="font-medium">{ogrenci.ad_soyad}</p>
                        <p className="text-sm text-gray-600">{ogrenci.sinif_seviyesi}. Sınıf</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">
                        {ogrenci.performans.ortalama_net.toFixed(1)} net
                      </Badge>
                      {getTrendIcon(ogrenci.performans.gelisim_trendi)}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">Henüz öğrenci bulunmuyor</p>
              )}

              {ogrenci_listesi.length > 0 && (
                <Button variant="outline" className="w-full mt-4">
                  Tüm Öğrencileri Görüntüle
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Son Bildirimler */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="h-5 w-5 mr-2" />
              Son Bildirimler
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {son_bildirimler.length > 0 ? (
                son_bildirimler.map((bildirim) => (
                  <div
                    key={bildirim.bildirim_id}
                    className={`p-3 rounded-lg border ${getNotificationColor(bildirim.tip)} ${!bildirim.okundu ? 'font-medium' : ''}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="text-sm font-medium">{bildirim.baslik}</p>
                        <p className="text-xs mt-1">{bildirim.mesaj}</p>
                      </div>
                      {!bildirim.okundu && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full ml-2 mt-1"></div>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      {new Date(bildirim.olusturma_tarihi).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">Henüz bildirim bulunmuyor</p>
              )}

              {son_bildirimler.length > 0 && (
                <Button variant="outline" className="w-full mt-4">
                  Tüm Bildirimleri Görüntüle
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Hızlı Eylemler */}
      <Card>
        <CardHeader>
          <CardTitle>Hızlı Eylemler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="h-20 flex flex-col items-center justify-center space-y-2">
              <FileText className="h-6 w-6" />
              <span>Sınıf Raporu Oluştur</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Users className="h-6 w-6" />
              <span>Öğrenci Ekle</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Bell className="h-6 w-6" />
              <span>Bildirim Gönder</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherDashboard;