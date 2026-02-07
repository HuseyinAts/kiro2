import { apiClient } from './apiClient';

// Type-safe axios error handler
function getAxiosErrorMessage(error: unknown, defaultMessage: string): string {
  const axiosError = error as { response?: { data?: { detail?: string } }; message?: string };
  return axiosError.response?.data?.detail || axiosError.message || defaultMessage;
}

export interface ChildRelationCreate {
  child_email: string;
  relation_type: string;
}

/**
 * Veli-çocuk ilişkisi
 */
export interface ChildRelation {
  id: number;
  parent_id: number;
  child_id: number;
  child_name: string;
  child_email: string;
  relation_type: string;
  approved: boolean;
  /** İlişki oluşturulma zamanı (ISO 8601: "2024-06-15T14:30:00Z") */
  created_at: string;
  /** Onaylanma zamanı (ISO 8601: "2024-06-16T09:15:00Z") */
  approved_at?: string;
}

/**
 * Çocuğun performans özeti
 */
export interface ChildPerformance {
  child_id: number;
  child_name: string;
  total_study_time: number;
  exams_taken: number;
  average_score: number;
  /** Son sınav tarihi (ISO 8601: "2024-06-15T09:00:00Z") */
  last_exam_date?: string;
  last_exam_score?: number;
  weak_subjects: string[];
  strong_subjects: string[];
  recent_achievements: string[];
}

/**
 * Haftalık performans raporu
 */
export interface WeeklyReport {
  child_id: number;
  child_name: string;
  /** Hafta başlangıcı (ISO 8601: "2024-06-10T00:00:00Z") */
  week_start: string;
  /** Hafta bitişi (ISO 8601: "2024-06-16T23:59:59Z") */
  week_end: string;
  total_study_time: number;
  exams_taken: number;
  average_score: number;
  subjects_studied: string[];
  achievements: string[];
  performance_trend: string;
  recommendations: string[];
}

/**
 * Veli bildirimi
 */
export interface ParentNotification {
  id: number;
  child_id: number;
  child_name: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  /** Bildirim oluşturulma zamanı (ISO 8601: "2024-06-15T10:30:00Z") */
  created_at: string;
  /** Okunma zamanı (ISO 8601: "2024-06-15T11:00:00Z") */
  read_at?: string;
}

export interface ParentDashboardData {
  children: ChildPerformance[];
  unread_notifications: number;
  recent_notifications: ParentNotification[];
  weekly_summary: {
    total_children: number;
    active_children: number;
    average_performance: number;
  };
  pending_approvals: ChildRelation[];
}

class ParentService {
  private baseUrl = '/api/v1/parent';

  /**
   * Veli-çocuk ilişkisi oluştur
   */
  async createChildRelation(data: ChildRelationCreate): Promise<ChildRelation> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/children`, data);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Çocuk ilişkisi oluşturulurken hata oluştu'));
    }
  }

  /**
   * Velinin çocuklarını getir
   */
  async getChildren(): Promise<ChildRelation[]> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/children`);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Çocuk listesi alınırken hata oluştu'));
    }
  }

  /**
   * Çocuğun performans verilerini getir
   */
  async getChildPerformance(childId: number): Promise<ChildPerformance> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/children/${childId}/performance`);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Performans verileri alınırken hata oluştu'));
    }
  }

  /**
   * Çocuğun haftalık raporunu getir
   */
  async getWeeklyReport(childId: number): Promise<WeeklyReport> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/children/${childId}/weekly-report`);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Haftalık rapor alınırken hata oluştu'));
    }
  }

  /**
   * Veli bildirimlerini getir
   */
  async getNotifications(unreadOnly: boolean = false): Promise<ParentNotification[]> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/notifications`, {
        params: { unread_only: unreadOnly },
      });
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Bildirimler alınırken hata oluştu'));
    }
  }

  /**
   * Bildirimi okundu olarak işaretle
   */
  async markNotificationAsRead(notificationId: number): Promise<void> {
    try {
      await apiClient.put(`${this.baseUrl}/notifications/${notificationId}/read`);
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Bildirim güncellenirken hata oluştu'));
    }
  }

  /**
   * Veli dashboard verilerini getir
   */
  async getDashboardData(): Promise<ParentDashboardData> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/dashboard`);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Dashboard verileri alınırken hata oluştu'));
    }
  }

  /**
   * Veli ilişkisini onayla/reddet (Öğrenci tarafından kullanılır)
   */
  async approveParentRelation(relationId: number, approved: boolean): Promise<void> {
    try {
      await apiClient.put(`${this.baseUrl}/approval/${relationId}`, null, {
        params: { approved },
      });
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Onay işlemi sırasında hata oluştu'));
    }
  }

  /**
   * Haftalık raporu PDF olarak indir
   */
  async downloadWeeklyReport(childId: number): Promise<Blob> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/children/${childId}/weekly-report/pdf`,
        { responseType: 'blob' },
      );
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Rapor indirilirken hata oluştu'));
    }
  }

  /**
   * Performans raporunu PDF olarak indir
   */
  async downloadPerformanceReport(childId: number): Promise<Blob> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/children/${childId}/performance/pdf`,
        { responseType: 'blob' },
      );
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Rapor indirilirken hata oluştu'));
    }
  }

  /**
   * Çocuk için bildirim oluştur (Sistem tarafından kullanılır)
   */
  async createNotification(data: {
    child_id: number;
    title: string;
    message: string;
    notification_type: string;
  }): Promise<ParentNotification> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/notifications`, data);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Bildirim oluşturulurken hata oluştu'));
    }
  }

  /**
   * Toplu bildirim gönder (Admin tarafından kullanılır)
   */
  async sendBulkNotification(data: {
    child_ids: number[];
    title: string;
    message: string;
    notification_type: string;
  }): Promise<void> {
    try {
      await apiClient.post(`${this.baseUrl}/notifications/bulk`, data);
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Toplu bildirim gönderilirken hata oluştu'));
    }
  }

  /**
   * Veli onay durumunu kontrol et
   */
  async checkApprovalStatus(childId: number): Promise<{
    approved: boolean;
    pending: boolean;
    relation_id?: number;
  }> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/children/${childId}/approval-status`);
      return response.data;
    } catch (error: unknown) {
      throw new Error(getAxiosErrorMessage(error, 'Onay durumu kontrol edilirken hata oluştu'));
    }
  }
}

export const parentService = new ParentService();