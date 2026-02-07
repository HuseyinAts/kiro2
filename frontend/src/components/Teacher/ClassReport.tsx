import {
  FileText,
  Download,
  BarChart3,
  TrendingUp,
  Users,
  Target,
  BookOpen,
  AlertCircle,
  CheckCircle,
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

interface ReportParams {
  baslangic_tarihi?: string;
  bitis_tarihi?: string;
  sinav_tipi?: string;
}

interface ClassStats {
  toplam_ogrenci: number;
  aktif_ogrenci: number;
  ortalama_net: number;
  en_yuksek_net: number;
  en_dusuk_net: number;
  standart_sapma: number;
}

interface ClassReport {
  rapor_id: string;
  ogretmen_id: string;
  olusturma_tarihi: string;
  rapor_donemi: {
    baslangic: string;
    bitis: string;
  };
  sinif_istatistikleri: ClassStats;
  konu_performanslari: Record<string, number>;
  en_zayif_konu: [string, number];
  en_guclu_konu: [string, number];
  ogrenci_sayisi: number;
  sinav_sayisi: number;
  oneriler: string[];
}

interface SavedReport {
  rapor_id: string;
  olusturma_tarihi: string;
  rapor_donemi: {
    baslangic: string;
    bitis: string;
  };
  sinif_istatistikleri: ClassStats;
}

const ClassReport: React.FC = () => {
  const [reportParams, setReportParams] = useState<ReportParams>({
    baslangic_tarihi: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    bitis_tarihi: new Date().toISOString().split('T')[0],
    sinav_tipi: '',
  });

  const [currentReport, setCurrentReport] = useState<ClassReport | null>(null);
  const [savedReports, setSavedReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportsLoading, setReportsLoading] = useState(true);

  useEffect(() => {
    fetchSavedReports();
  }, []);

  const fetchSavedReports = async () => {
    try {
      setReportsLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch('/api/v1/ogretmen/raporlar?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Raporlar alınamadı');
      }

      const result = await response.json();
      if (result.success) {
        setSavedReports(result.data.raporlar || []);
      }
    } catch (err) {
      console.error('Raporlar yüklenirken hata:', err);
    } finally {
      setReportsLoading(false);
    }
  };

  const generateReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('token');

      const response = await fetch('/api/v1/ogretmen/rapor/sinif', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportParams),
      });

      if (!response.ok) {
        throw new Error('Rapor oluşturulamadı');
      }

      const result = await response.json();
      if (result.success) {
        setCurrentReport(result.data);
        await fetchSavedReports(); // Yeni rapor listesini güncelle
      } else {
        throw new Error(result.message || 'Rapor oluşturulamadı');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  const loadSavedReport = async (reportId: string) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch(`/api/v1/ogretmen/rapor/${reportId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Rapor yüklenemedi');
      }

      const result = await response.json();
      if (result.success) {
        setCurrentReport(result.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rapor yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceColor = (percentage: number) => {
    if (percentage >= 70) {return 'text-green-600 bg-green-50';}
    if (percentage >= 50) {return 'text-yellow-600 bg-yellow-50';}
    return 'text-red-600 bg-red-50';
  };

  const getPerformanceIcon = (percentage: number) => {
    if (percentage >= 70) {return <CheckCircle className="h-4 w-4 text-green-600" />;}
    if (percentage >= 50) {return <AlertCircle className="h-4 w-4 text-yellow-600" />;}
    return <AlertCircle className="h-4 w-4 text-red-600" />;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Sınıf Raporu</h1>
          <p className="text-gray-600 mt-1">
            Sınıf geneli performans analizi ve raporlama
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rapor Oluşturma Paneli */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                Yeni Rapor Oluştur
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="start-date">Başlangıç Tarihi</Label>
                <Input
                  id="start-date"
                  type="date"
                  value={reportParams.baslangic_tarihi}
                  onChange={(e) => setReportParams(prev => ({
                    ...prev,
                    baslangic_tarihi: e.target.value,
                  }))}
                />
              </div>

              <div>
                <Label htmlFor="end-date">Bitiş Tarihi</Label>
                <Input
                  id="end-date"
                  type="date"
                  value={reportParams.bitis_tarihi}
                  onChange={(e) => setReportParams(prev => ({
                    ...prev,
                    bitis_tarihi: e.target.value,
                  }))}
                />
              </div>

              <div>
                <Label htmlFor="exam-type">Sınav Türü (Opsiyonel)</Label>
                <Select
                  value={reportParams.sinav_tipi || ''}
                  onValueChange={(value) => setReportParams(prev => ({
                    ...prev,
                    sinav_tipi: value,
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Tüm sınavlar" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Tüm sınavlar</SelectItem>
                    <SelectItem value="TYT">TYT</SelectItem>
                    <SelectItem value="AYT">AYT</SelectItem>
                    <SelectItem value="YDT">YDT</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button
                onClick={generateReport}
                disabled={loading}
                className="w-full"
              >
                {loading ? 'Rapor Oluşturuluyor...' : 'Rapor Oluştur'}
              </Button>

              {error && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Kaydedilmiş Raporlar */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Kaydedilmiş Raporlar</CardTitle>
            </CardHeader>
            <CardContent>
              {reportsLoading ? (
                <div className="text-center py-4">Yükleniyor...</div>
              ) : savedReports.length > 0 ? (
                <div className="space-y-2">
                  {savedReports.map((report) => (
                    <div
                      key={report.rapor_id}
                      className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => loadSavedReport(report.rapor_id)}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium">
                            {new Date(report.olusturma_tarihi).toLocaleDateString('tr-TR')}
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(report.rapor_donemi.baslangic).toLocaleDateString('tr-TR')} -
                            {new Date(report.rapor_donemi.bitis).toLocaleDateString('tr-TR')}
                          </p>
                        </div>
                        <Badge variant="outline">
                          {report.sinif_istatistikleri.ortalama_net.toFixed(1)} net
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">
                  Henüz rapor bulunmuyor
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Rapor İçeriği */}
        <div className="lg:col-span-2">
          {currentReport ? (
            <div className="space-y-6">
              {/* Rapor Başlığı */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>Sınıf Performans Raporu</CardTitle>
                      <p className="text-gray-600 mt-1">
                        {new Date(currentReport.rapor_donemi.baslangic).toLocaleDateString('tr-TR')} -
                        {new Date(currentReport.rapor_donemi.bitis).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        PDF İndir
                      </Button>
                    </div>
                  </div>
                </CardHeader>
              </Card>

              {/* Genel İstatistikler */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center">
                      <Users className="h-8 w-8 text-blue-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Toplam Öğrenci</p>
                        <p className="text-2xl font-bold">{currentReport.sinif_istatistikleri.toplam_ogrenci}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center">
                      <BarChart3 className="h-8 w-8 text-green-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Ortalama Net</p>
                        <p className="text-2xl font-bold">{currentReport.sinif_istatistikleri.ortalama_net.toFixed(1)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center">
                      <TrendingUp className="h-8 w-8 text-purple-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">En Yüksek Net</p>
                        <p className="text-2xl font-bold">{currentReport.sinif_istatistikleri.en_yuksek_net.toFixed(1)}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <div className="flex items-center">
                      <BookOpen className="h-8 w-8 text-orange-600" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Toplam Sınav</p>
                        <p className="text-2xl font-bold">{currentReport.sinav_sayisi}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Konu Performansları */}
              <Card>
                <CardHeader>
                  <CardTitle>Konu Bazlı Performans</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(currentReport.konu_performanslari).map(([konu, yuzde]) => (
                      <div key={konu} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          {getPerformanceIcon(yuzde)}
                          <span className="font-medium">{konu}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${yuzde >= 70 ? 'bg-green-500' : yuzde >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                              style={{ width: `${Math.min(100, yuzde)}%` }}
                            ></div>
                          </div>
                          <Badge className={getPerformanceColor(yuzde)}>
                            {yuzde.toFixed(1)}%
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* En İyi ve En Zayıf Konular */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-green-600">En Güçlü Konu</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-lg">{currentReport.en_guclu_konu[0]}</p>
                        <p className="text-sm text-gray-600">Sınıf başarısı</p>
                      </div>
                      <Badge className="bg-green-100 text-green-800">
                        {currentReport.en_guclu_konu[1].toFixed(1)}%
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-red-600">En Zayıf Konu</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-lg">{currentReport.en_zayif_konu[0]}</p>
                        <p className="text-sm text-gray-600">Gelişim gerekli</p>
                      </div>
                      <Badge className="bg-red-100 text-red-800">
                        {currentReport.en_zayif_konu[1].toFixed(1)}%
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Öneriler */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Target className="h-5 w-5 mr-2" />
                    Öneriler
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {currentReport.oneriler.map((oneri, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-gray-700">{oneri}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Rapor Seçin</h3>
                  <p className="text-gray-600">
                    Yeni bir rapor oluşturun veya kaydedilmiş raporlardan birini seçin
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClassReport;