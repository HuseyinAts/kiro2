/**
 * Öğretmen paneli servisleri
 */

const API_BASE_URL = '/api/v1/ogretmen';

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

interface DashboardStats {
  toplam_ogrenci: number;
  aktif_sinavlar: number;
  ortalama_basari: number;
  son_guncelleme: string;
}

interface StudentSummary {
  ogrenci_id: string;
  ad_soyad: string;
  email: string;
  sinif_seviyesi: number;
  okul_adi?: string;
  hedef_sinav?: string;
  son_giris?: string;
  performans: {
    ortalama_net: number;
    toplam_sinav: number;
    gelisim_trendi: string;
    son_sinav_tarihi?: string;
  };
  aktif: boolean;
}

interface TeacherProfile {
  ogretmen_id: string;
  okul_adi: string;
  brans: string;
  deneyim_yili?: number;
}

interface Notification {
  bildirim_id: string;
  baslik: string;
  mesaj: string;
  tip: string;
  olusturma_tarihi: string;
  okundu: boolean;
}

interface DashboardData {
  ogretmen_profili: TeacherProfile;
  genel_istatistikler: DashboardStats;
  ogrenci_listesi: StudentSummary[];
  son_bildirimler: Notification[];
}

interface StudentListData {
  ogrenciler: StudentSummary[];
  sayfalama: {
    mevcut_sayfa: number;
    sayfa_basina: number;
    toplam_ogrenci: number;
    toplam_sayfa: number;
  };
}

interface StudentDetailPerformance {
  ogrenci_bilgileri: {
    ad_soyad: string;
    email: string;
    sinif_seviyesi: number;
    hedef_sinav?: string;
    hedef_universiteler: string[];
  };
  genel_istatistikler: {
    toplam_sinav: number;
    ortalama_net: number;
    en_yuksek_net: number;
    gelisim_trendi: string;
  };
  sinav_gecmisi: Array<{
    sinav_id: string;
    sinav_tipi: string;
    tarih: string;
    net_sayisi: number;
    ham_puan: number;
    dogru: number;
    yanlis: number;
    bos: number;
  }>;
  net_trendi: Array<{
    tarih: string;
    net: number;
  }>;
  konu_performanslari: Record<string, number>;
  zayif_konular: string[];
  guclu_konular: string[];
  oneriler: string[];
}

interface ClassReport {
  rapor_id: string;
  ogretmen_id: string;
  olusturma_tarihi: string;
  rapor_donemi: {
    baslangic: string;
    bitis: string;
  };
  sinif_istatistikleri: {
    toplam_ogrenci: number;
    aktif_ogrenci: number;
    ortalama_net: number;
    en_yuksek_net: number;
    en_dusuk_net: number;
    standart_sapma: number;
  };
  konu_performanslari: Record<string, number>;
  en_zayif_konu: [string, number];
  en_guclu_konu: [string, number];
  ogrenci_sayisi: number;
  sinav_sayisi: number;
  oneriler: string[];
}

interface ReportParams {
  baslangic_tarihi?: string;
  bitis_tarihi?: string;
  sinav_tipi?: string;
}

interface NewNotification {
  baslik: string;
  mesaj: string;
  tip: string;
}

interface NotificationData {
  bildirimler: Notification[];
  toplam: number;
  okunmamis: number;
}

class TeacherService {
  private getRequestInit(): RequestInit {
    return {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const result: ApiResponse<T> = await response.json();

    if (!result.success) {
      throw new Error(result.message || 'İşlem başarısız');
    }

    return result.data;
  }

  /**
   * Öğretmen dashboard verilerini getir
   */
  async getDashboardData(): Promise<DashboardData> {
    const response = await fetch(`${API_BASE_URL}/dashboard`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<DashboardData>(response);
  }

  /**
   * Öğrenci listesini getir
   */
  async getStudentList(page: number = 1, limit: number = 20): Promise<StudentListData> {
    const response = await fetch(`${API_BASE_URL}/ogrenciler?sayfa=${page}&limit=${limit}`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<StudentListData>(response);
  }

  /**
   * Öğrenci detay performansını getir
   */
  async getStudentDetailPerformance(studentId: string): Promise<StudentDetailPerformance> {
    const response = await fetch(`${API_BASE_URL}/ogrenci/${studentId}/performans`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<StudentDetailPerformance>(response);
  }

  /**
   * Sınıf raporu oluştur
   */
  async createClassReport(params: ReportParams): Promise<ClassReport> {
    const response = await fetch(`${API_BASE_URL}/rapor/sinif`, {
      method: 'POST',
      ...this.getRequestInit(),
      body: JSON.stringify(params),
    });

    return this.handleResponse<ClassReport>(response);
  }

  /**
   * Kaydedilmiş raporları getir
   */
  async getSavedReports(limit: number = 10): Promise<{ raporlar: ClassReport[]; toplam_rapor: number }> {
    const response = await fetch(`${API_BASE_URL}/raporlar?limit=${limit}`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<{ raporlar: ClassReport[]; toplam_rapor: number }>(response);
  }

  /**
   * Belirli bir raporu getir
   */
  async getReportDetail(reportId: string): Promise<ClassReport> {
    const response = await fetch(`${API_BASE_URL}/rapor/${reportId}`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<ClassReport>(response);
  }

  /**
   * Bildirim gönder
   */
  async sendNotification(notification: NewNotification): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/bildirim`, {
      method: 'POST',
      ...this.getRequestInit(),
      body: JSON.stringify(notification),
    });

    await this.handleResponse<void>(response);
  }

  /**
   * Bildirimleri getir
   */
  async getNotifications(limit: number = 20): Promise<NotificationData> {
    const response = await fetch(`${API_BASE_URL}/bildirimler?limit=${limit}`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<NotificationData>(response);
  }

  /**
   * Bildirimi okundu olarak işaretle
   */
  async markNotificationAsRead(notificationId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/bildirim/${notificationId}/okundu`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
    });

    await this.handleResponse<void>(response);
  }

  /**
   * Öğretmen istatistiklerini getir
   */
  async getTeacherStats(days: number = 30): Promise<{
    genel_ozet: DashboardStats;
    donem_bilgisi: {
      baslangic_tarihi: string;
      gun_sayisi: number;
    };
    ogrenci_aktivitesi: {
      toplam_ogrenci: number;
      aktif_ogrenci: number;
    };
    son_guncelleme: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/istatistikler?gun_sayisi=${days}`, {
      method: 'GET',
      ...this.getRequestInit(),
    });

    return this.handleResponse<{
      genel_ozet: DashboardStats;
      donem_bilgisi: {
        baslangic_tarihi: string;
        gun_sayisi: number;
      };
      ogrenci_aktivitesi: {
        toplam_ogrenci: number;
        aktif_ogrenci: number;
      };
      son_guncelleme: string;
    }>(response);
  }
}

// Singleton instance
export const teacherService = new TeacherService();

// Export types
export type {
  DashboardData,
  StudentListData,
  StudentDetailPerformance,
  ClassReport,
  ReportParams,
  NewNotification,
  NotificationData,
  TeacherProfile,
  StudentSummary,
  Notification,
};