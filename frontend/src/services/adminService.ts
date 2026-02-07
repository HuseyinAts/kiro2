/**
 * Admin Panel Servisi
 * Admin API endpoint'leri ile entegrasyon
 */

import { apiHelpers } from '../utils/apiHelpers';

// Admin API tipleri
export interface AdminUser {
  kullanici_id: string
  email: string
  ad_soyad: string
  telefon?: string
  rol: 'ogrenci' | 'ogretmen' | 'veli' | 'admin'
  aktif: boolean
  kayit_tarihi: string
  son_giris: string | null
  profil?: any
}

export interface CreateUserRequest {
  email: string
  ad_soyad: string
  sifre: string
  rol: 'ogrenci' | 'ogretmen' | 'veli' | 'admin'
  profil_bilgileri?: any
}

export interface UpdateUserRequest {
  ad_soyad?: string
  aktif?: boolean
  profil_bilgileri?: any
}

export interface DashboardStats {
  toplam_kullanici: number
  aktif_kullanici: number
  toplam_ogrenci: number
  toplam_ogretmen: number
  toplam_veli: number
  toplam_admin: number
  bugun_kayit: number
  bu_hafta_kayit: number
  bu_ay_kayit: number
  aktif_sinav_sayisi: number
  tamamlanan_sinav_sayisi: number
  ortalama_basari_orani: number
  sistem_durumu: 'healthy' | 'warning' | 'error'
  son_guncelleme: string
}

export interface ContentQuestion {
  soru_id: string
  soru_metni: string
  secenekler: string[]
  dogru_cevap: string
  konu: string
  alt_konu?: string
  zorluk_seviyesi: 'KOLAY' | 'ORTA' | 'ZOR'
  sinav_tipi: 'TYT' | 'AYT' | 'YDT'
  olusturma_tarihi: string
  durum: 'aktif' | 'pasif' | 'inceleme'
  onay_durumu: 'bekliyor' | 'onaylandi' | 'reddedildi'
  olusturan: string
}

export interface CreateQuestionRequest {
  soru_metni: string
  secenekler: string[]
  dogru_cevap: string
  konu: string
  alt_konu?: string
  zorluk_seviyesi: 'KOLAY' | 'ORTA' | 'ZOR'
  sinav_tipi: 'TYT' | 'AYT' | 'YDT'
}

export interface EducationalContent {
  icerik_id: string
  baslik: string
  aciklama: string
  icerik_tipi: 'video' | 'makale' | 'interaktif' | 'dokuman'
  konu: string
  zorluk_seviyesi: 'KOLAY' | 'ORTA' | 'ZOR'
  seviye?: string
  url?: string
  dosya_yolu?: string
  etiketler: string[]
  olusturma_tarihi: string
  durum: 'aktif' | 'pasif' | 'inceleme'
  goruntulenme_sayisi: number
  begeni_sayisi: number
  onay_durumu: 'bekliyor' | 'onaylandi' | 'reddedildi'
  olusturan: string
}

export interface CreateContentRequest {
  baslik: string
  aciklama: string
  icerik_tipi: 'video' | 'makale' | 'interaktif' | 'dokuman'
  konu: string
  zorluk_seviyesi: 'KOLAY' | 'ORTA' | 'ZOR'
  url?: string
  etiketler: string[]
}

export interface UserListParams {
  rol?: 'ogrenci' | 'ogretmen' | 'veli' | 'admin'
  aktif?: boolean
  sayfa?: number
  sayfa_boyutu?: number
  arama?: string
}

export interface QuestionListParams {
  konu?: string
  zorluk_seviyesi?: 'KOLAY' | 'ORTA' | 'ZOR'
  sinav_tipi?: 'TYT' | 'AYT' | 'YDT'
  durum?: 'aktif' | 'pasif' | 'inceleme'
  sayfa?: number
  sayfa_boyutu?: number
  arama?: string
}

export interface ContentListParams {
  icerik_tipi?: 'video' | 'makale' | 'interaktif' | 'dokuman'
  konu?: string
  zorluk_seviyesi?: 'KOLAY' | 'ORTA' | 'ZOR'
  durum?: 'aktif' | 'pasif' | 'inceleme'
  sayfa?: number
  sayfa_boyutu?: number
  arama?: string
}

class AdminService {
  private baseURL = '/api/v1/admin';

  // ==================== KULLANICI YÖNETİMİ ====================

  /**
   * Tüm kullanıcıları listele
   */
  async getUsers(params: UserListParams = {}): Promise<AdminUser[]> {
    const response = await apiHelpers.get(`${this.baseURL}/users`, params);
    return response.data;
  }

  /**
   * Kullanıcı detaylarını getir
   */
  async getUser(userId: string): Promise<AdminUser> {
    const response = await apiHelpers.get(`${this.baseURL}/users/${userId}`);
    return response.data;
  }

  /**
   * Yeni kullanıcı oluştur
   */
  async createUser(userData: CreateUserRequest): Promise<AdminUser> {
    const response = await apiHelpers.post(`${this.baseURL}/users`, userData);
    return response.data;
  }

  /**
   * Kullanıcı bilgilerini güncelle
   */
  async updateUser(userId: string, userData: UpdateUserRequest): Promise<AdminUser> {
    const response = await apiHelpers.put(`${this.baseURL}/users/${userId}`, userData);
    return response.data;
  }

  /**
   * Kullanıcıyı sil
   */
  async deleteUser(userId: string): Promise<void> {
    await apiHelpers.delete(`${this.baseURL}/users/${userId}`);
  }

  /**
   * Kullanıcı durumunu değiştir (aktif/pasif)
   */
  async toggleUserStatus(userId: string, aktif: boolean): Promise<AdminUser> {
    const response = await apiHelpers.patch(`${this.baseURL}/users/${userId}/status`, { aktif });
    return response.data;
  }

  /**
   * Kullanıcı şifresini sıfırla
   */
  async resetUserPassword(userId: string): Promise<{ yeni_sifre: string }> {
    const response = await apiHelpers.post(`${this.baseURL}/users/${userId}/reset-password`);
    return response.data;
  }

  // ==================== DASHBOARD İSTATİSTİKLERİ ====================

  /**
   * Dashboard istatistiklerini getir
   */
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiHelpers.get(`${this.baseURL}/dashboard/stats`);
    return response.data;
  }

  /**
   * Kullanıcı kayıt trendlerini getir
   */
  async getUserRegistrationTrends(days = 30): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/dashboard/user-trends`, { days });
    return response.data;
  }

  /**
   * Sınav istatistiklerini getir
   */
  async getExamStatistics(): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/dashboard/exam-stats`);
    return response.data;
  }

  /**
   * Sistem sağlık durumunu getir
   */
  async getSystemHealth(): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/dashboard/system-health`);
    return response.data;
  }

  // ==================== İÇERİK YÖNETİMİ - SORULAR ====================

  /**
   * Soruları listele
   */
  async getQuestions(params: QuestionListParams = {}): Promise<ContentQuestion[]> {
    const response = await apiHelpers.get(`${this.baseURL}/content/questions`, params);
    return response.data;
  }

  /**
   * Soru detaylarını getir
   */
  async getQuestion(questionId: string): Promise<ContentQuestion> {
    const response = await apiHelpers.get(`${this.baseURL}/content/questions/${questionId}`);
    return response.data;
  }

  /**
   * Yeni soru oluştur
   */
  async createQuestion(questionData: CreateQuestionRequest): Promise<ContentQuestion> {
    const response = await apiHelpers.post(`${this.baseURL}/content/questions`, questionData);
    return response.data;
  }

  /**
   * Soru güncelle
   */
  async updateQuestion(questionId: string, questionData: Partial<CreateQuestionRequest>): Promise<ContentQuestion> {
    const response = await apiHelpers.put(`${this.baseURL}/content/questions/${questionId}`, questionData);
    return response.data;
  }

  /**
   * Soru sil
   */
  async deleteQuestion(questionId: string): Promise<void> {
    await apiHelpers.delete(`${this.baseURL}/content/questions/${questionId}`);
  }

  /**
   * Soru durumunu değiştir
   */
  async updateQuestionStatus(questionId: string, durum: 'aktif' | 'pasif' | 'inceleme'): Promise<ContentQuestion> {
    const response = await apiHelpers.patch(`${this.baseURL}/content/questions/${questionId}/status`, { durum });
    return response.data;
  }

  /**
   * Toplu soru yükleme
   */
  async bulkUploadQuestions(file: File, onProgress?: (progress: number) => void): Promise<any> {
    const response = await apiHelpers.uploadFile(`${this.baseURL}/content/questions/bulk-upload`, file, onProgress);
    return response.data;
  }

  /**
   * Soru konularını getir
   */
  async getQuestionSubjects(): Promise<string[]> {
    const response = await apiHelpers.get(`${this.baseURL}/content/questions/subjects`);
    return response.data;
  }

  // ==================== İÇERİK YÖNETİMİ - EĞİTİM MATERYALLERİ ====================

  /**
   * Eğitim içeriklerini listele
   */
  async getEducationalContent(params: ContentListParams = {}): Promise<EducationalContent[]> {
    const response = await apiHelpers.get(`${this.baseURL}/content/educational`, params);
    return response.data;
  }

  /**
   * Eğitim içeriği detaylarını getir
   */
  async getEducationalContentDetail(contentId: string): Promise<EducationalContent> {
    const response = await apiHelpers.get(`${this.baseURL}/content/educational/${contentId}`);
    return response.data;
  }

  /**
   * Yeni eğitim içeriği oluştur
   */
  async createEducationalContent(contentData: CreateContentRequest): Promise<EducationalContent> {
    const response = await apiHelpers.post(`${this.baseURL}/content/educational`, contentData);
    return response.data;
  }

  /**
   * Eğitim içeriğini güncelle
   */
  async updateEducationalContent(contentId: string, contentData: Partial<CreateContentRequest>): Promise<EducationalContent> {
    const response = await apiHelpers.put(`${this.baseURL}/content/educational/${contentId}`, contentData);
    return response.data;
  }

  /**
   * Eğitim içeriğini sil
   */
  async deleteEducationalContent(contentId: string): Promise<void> {
    await apiHelpers.delete(`${this.baseURL}/content/educational/${contentId}`);
  }

  /**
   * İçerik durumunu değiştir
   */
  async updateContentStatus(contentId: string, durum: 'aktif' | 'pasif' | 'inceleme'): Promise<EducationalContent> {
    const response = await apiHelpers.patch(`${this.baseURL}/content/educational/${contentId}/status`, { durum });
    return response.data;
  }

  /**
   * İçerik dosyası yükle
   */
  async uploadContentFile(contentId: string, file: File, onProgress?: (progress: number) => void): Promise<any> {
    const response = await apiHelpers.uploadFile(`${this.baseURL}/content/educational/${contentId}/upload`, file, onProgress);
    return response.data;
  }

  // ==================== RAPORLAMA ====================

  /**
   * Kullanıcı aktivite raporu
   */
  async getUserActivityReport(startDate: string, endDate: string): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/reports/user-activity`, {
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  }

  /**
   * Sınav performans raporu
   */
  async getExamPerformanceReport(startDate: string, endDate: string): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/reports/exam-performance`, {
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  }

  /**
   * İçerik kullanım raporu
   */
  async getContentUsageReport(startDate: string, endDate: string): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/reports/content-usage`, {
      start_date: startDate,
      end_date: endDate,
    });
    return response.data;
  }

  // ==================== SİSTEM YÖNETİMİ ====================

  /**
   * Sistem ayarlarını getir
   */
  async getSystemSettings(): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/system/settings`);
    return response.data;
  }

  /**
   * Sistem ayarlarını güncelle
   */
  async updateSystemSettings(settings: any): Promise<any> {
    const response = await apiHelpers.put(`${this.baseURL}/system/settings`, settings);
    return response.data;
  }

  /**
   * Sistem loglarını getir
   */
  async getSystemLogs(level = 'INFO', limit = 100): Promise<any> {
    const response = await apiHelpers.get(`${this.baseURL}/system/logs`, { level, limit });
    return response.data;
  }

  /**
   * Cache temizle
   */
  async clearCache(): Promise<any> {
    const response = await apiHelpers.post(`${this.baseURL}/system/clear-cache`);
    return response.data;
  }

  // ==================== YARDIMCI METODLAR ====================

  /**
   * Rol açıklamasını getir
   */
  getRoleDescription(rol: string): string {
    switch (rol) {
      case 'ogrenci':
        return 'Öğrenci';
      case 'ogretmen':
        return 'Öğretmen';
      case 'veli':
        return 'Veli';
      case 'admin':
        return 'Yönetici';
      default:
        return 'Bilinmeyen';
    }
  }

  /**
   * Durum açıklamasını getir
   */
  getStatusDescription(durum: string): string {
    switch (durum) {
      case 'aktif':
        return 'Aktif';
      case 'pasif':
        return 'Pasif';
      case 'inceleme':
        return 'İncelemede';
      default:
        return 'Bilinmeyen';
    }
  }

  /**
   * Zorluk seviyesi açıklamasını getir
   */
  getDifficultyDescription(zorluk: string): string {
    switch (zorluk) {
      case 'KOLAY':
        return 'Kolay';
      case 'ORTA':
        return 'Orta';
      case 'ZOR':
        return 'Zor';
      default:
        return 'Bilinmeyen';
    }
  }

  /**
   * İçerik tipi açıklamasını getir
   */
  getContentTypeDescription(tip: string): string {
    switch (tip) {
      case 'video':
        return 'Video';
      case 'makale':
        return 'Makale';
      case 'interaktif':
        return 'İnteraktif';
      case 'dokuman':
        return 'Doküman';
      default:
        return 'Bilinmeyen';
    }
  }
}

export const adminService = new AdminService();
export default adminService;