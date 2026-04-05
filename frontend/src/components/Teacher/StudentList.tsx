import {
  Search,
  Filter,
  Eye,
  TrendingUp,
  TrendingDown,
  Minus,
  Users,
  BookOpen,
  Calendar,
  Mail,
} from 'lucide-react';
import * as React from 'react';
import {  useState, useEffect, memo, useCallback  } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

interface StudentPerformance {
  ortalama_net: number;
  toplam_sinav: number;
  gelisim_trendi: string;
  son_sinav_tarihi?: string;
}

interface Student {
  ogrenci_id: string;
  ad_soyad: string;
  email: string;
  sinif_seviyesi: number;
  okul_adi?: string;
  hedef_sinav?: string;
  son_giris?: string;
  performans: StudentPerformance;
  aktif: boolean;
}

interface PaginationInfo {
  mevcut_sayfa: number;
  sayfa_basina: number;
  toplam_ogrenci: number;
  toplam_sayfa: number;
}

interface StudentListData {
  ogrenciler: Student[];
  sayfalama: PaginationInfo;
}

// Memoized helper functions for performance
const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'artan':
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    case 'azalan':
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    default:
      return <Minus className="h-4 w-4 text-gray-500" />;
  }
};

const getTrendText = (trend: string) => {
  switch (trend) {
    case 'artan':
      return 'Yükseliş';
    case 'azalan':
      return 'Düşüş';
    default:
      return 'Sabit';
  }
};

const getPerformanceColor = (net: number) => {
  if (net >= 60) {return 'bg-green-100 text-green-800';}
  if (net >= 40) {return 'bg-yellow-100 text-yellow-800';}
  return 'bg-red-100 text-red-800';
};

// Memoized Student List Item component for performance optimization
interface StudentListItemProps {
  student: Student;
  onViewDetails: (studentId: string) => void;
}

const StudentListItem = memo(function StudentListItem({ student, onViewDetails }: StudentListItemProps) {
  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`w-4 h-4 rounded-full ${student.aktif ? 'bg-green-500' : 'bg-gray-400'}`}></div>

          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-lg">{student.ad_soyad}</h3>
              <Badge variant="outline">{student.sinif_seviyesi}. Sınıf</Badge>
              {student.hedef_sinav && (
                <Badge variant="secondary">{student.hedef_sinav}</Badge>
              )}
            </div>

            <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
              <div className="flex items-center">
                <Mail className="h-4 w-4 mr-1" />
                {student.email}
              </div>
              {student.okul_adi && (
                <div>{student.okul_adi}</div>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {/* Performans Bilgileri */}
          <div className="text-right">
            <div className="flex items-center space-x-2">
              <Badge className={getPerformanceColor(student.performans.ortalama_net)}>
                {student.performans.ortalama_net.toFixed(1)} net
              </Badge>
              <div className="flex items-center space-x-1">
                {getTrendIcon(student.performans.gelisim_trendi)}
                <span className="text-xs text-gray-500">
                  {getTrendText(student.performans.gelisim_trendi)}
                </span>
              </div>
            </div>

            <div className="text-xs text-gray-500 mt-1">
              {student.performans.toplam_sinav} sınav
              {student.performans.son_sinav_tarihi && (
                <span className="ml-2">
                  Son: {new Date(student.performans.son_sinav_tarihi).toLocaleDateString('tr-TR')}
                </span>
              )}
            </div>
          </div>

          {/* Eylemler */}
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewDetails(student.ogrenci_id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              Detay
            </Button>
          </div>
        </div>
      </div>

      {/* Son Giriş Bilgisi */}
      {student.son_giris && (
        <div className="mt-2 text-xs text-gray-500">
          Son giriş: {new Date(student.son_giris).toLocaleString('tr-TR')}
        </div>
      )}
    </div>
  );
});

const StudentList: React.FC = () => {
  const [studentData, setStudentData] = useState<StudentListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [_selectedStudent, _setSelectedStudent] = useState<Student | null>(null);

  useEffect(() => {
    fetchStudentList();
  }, [currentPage]);

  const fetchStudentList = async () => {
    try {
      setLoading(true);

      const response = await fetch(`/api/v1/ogretmen/ogrenciler?sayfa=${currentPage}&limit=20`, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Öğrenci listesi alınamadı');
      }

      const result = await response.json();
      if (result.success) {
        setStudentData(result.data);
      } else {
        throw new Error(result.message || 'Veri alınamadı');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bilinmeyen hata');
    } finally {
      setLoading(false);
    }
  };

  // Memoized callback to prevent unnecessary re-renders of StudentListItem
  const viewStudentDetails = useCallback(async (studentId: string) => {
    try {
      const response = await fetch(`/api/v1/ogretmen/ogrenci/${studentId}/performans`, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Öğrenci detayları alınamadı');
      }

      const result = await response.json();
      if (result.success) {
        // Detay sayfasına yönlendir veya modal aç
        // Bu kısımda detay modal'ı açılabilir
      }
    } catch (err) {
      console.error('Öğrenci detay hatası:', err);
    }
  }, []);

  const filteredStudents = studentData?.ogrenciler.filter(student =>
    student.ad_soyad.toLowerCase().includes(searchTerm.toLowerCase()) ||
    student.email.toLowerCase().includes(searchTerm.toLowerCase()),
  ) || [];

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
            onClick={fetchStudentList}
            className="ml-4"
            size="sm"
          >
            Tekrar Dene
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Öğrenci Listesi</h1>
          <p className="text-gray-600 mt-1">
            Sorumlu olduğunuz öğrencilerin performans takibi
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            Filtrele
          </Button>
          <Button size="sm">
            <Users className="h-4 w-4 mr-2" />
            Öğrenci Ekle
          </Button>
        </div>
      </div>

      {/* Arama ve Filtreler */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Öğrenci adı veya e-posta ile ara..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* İstatistik Özeti */}
      {studentData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Toplam Öğrenci</p>
                  <p className="text-2xl font-bold">{studentData.sayfalama.toplam_ogrenci}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <BookOpen className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Aktif Öğrenci</p>
                  <p className="text-2xl font-bold">
                    {filteredStudents.filter(s => s.aktif).length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Ortalama Net</p>
                  <p className="text-2xl font-bold">
                    {filteredStudents.length > 0
                      ? (filteredStudents.reduce((sum, s) => sum + s.performans.ortalama_net, 0) / filteredStudents.length).toFixed(1)
                      : '0.0'
                    }
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Calendar className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Bu Ay Sınav</p>
                  <p className="text-2xl font-bold">
                    {filteredStudents.reduce((sum, s) => sum + s.performans.toplam_sinav, 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Öğrenci Listesi */}
      <Card>
        <CardHeader>
          <CardTitle>Öğrenci Performans Listesi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredStudents.length > 0 ? (
              filteredStudents.map((student) => (
                <StudentListItem
                  key={student.ogrenci_id}
                  student={student}
                  onViewDetails={viewStudentDetails}
                />
              ))
            ) : (
              <div className="text-center py-8">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">
                  {searchTerm ? 'Arama kriterlerine uygun öğrenci bulunamadı' : 'Henüz öğrenci bulunmuyor'}
                </p>
              </div>
            )}
          </div>

          {/* Sayfalama */}
          {studentData && studentData.sayfalama.toplam_sayfa > 1 && (
            <div className="flex justify-center items-center space-x-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                Önceki
              </Button>

              <span className="text-sm text-gray-600">
                Sayfa {studentData.sayfalama.mevcut_sayfa} / {studentData.sayfalama.toplam_sayfa}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(studentData.sayfalama.toplam_sayfa, prev + 1))}
                disabled={currentPage === studentData.sayfalama.toplam_sayfa}
              >
                Sonraki
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentList;