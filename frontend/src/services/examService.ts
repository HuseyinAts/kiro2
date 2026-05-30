/**
 * ÖSYM Uyumlu Sınav Servisi
 * Backend ÖSYM sınav API'leri ile entegrasyon
 */

import { apiClient } from './apiClient';

// Enum'lar - Backend ile uyumlu
export enum ExamType {
  TYT = 'TYT',
  AYT = 'AYT',
  YDT = 'YDT',
  LGS = 'LGS'
}

export enum ExamStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  ABANDONED = 'abandoned',
  EXPIRED = 'expired'
}

export enum QuestionDifficulty {
  VERY_EASY = 'VERY_EASY',
  EASY = 'EASY',
  MEDIUM = 'MEDIUM',
  HARD = 'HARD',
  VERY_HARD = 'VERY_HARD'
}

// Legacy aliases for compatibility
export type SinavTipi = ExamType
export const SinavTipi = ExamType;

export type SinavDurumu = ExamStatus
export const SinavDurumu = ExamStatus;

export type ZorlukSeviyesi = QuestionDifficulty
export const ZorlukSeviyesi = QuestionDifficulty;

// Note: ExamType, ExamStatus, QuestionDifficulty are already exported above

// Request/Response tipleri - Backend API ile uyumlu
export interface CreateExamRequest {
  exam_type: ExamType
  custom_config?: Record<string, any>
}

export interface SaveAnswerRequest {
  question_id: string
  selected_answer?: string
  response_time?: number
}

export interface FlagQuestionRequest {
  question_id: string
  flagged: boolean
}

export interface NavigateQuestionRequest {
  question_index: number
}

/**
 * Sınav oturumu bilgileri
 * Backend'den dönen sınav session verisi
 */
export interface ExamSessionResponse {
  session_id: string
  student_id: string
  exam_type: string
  status: string
  total_questions: number
  duration_minutes: number
  current_question_index: number
  /** Sınav başlangıç zamanı (ISO 8601 format: "2024-06-15T09:00:00Z") */
  started_at?: string
  /** Sınav bitiş zamanı (ISO 8601 format: "2024-06-15T11:30:00Z") */
  completed_at?: string
}

export interface QuestionResponse {
  id: string
  question_id?: string  // Alias for id (compatibility)
  question_text: string
  content?: string  // Alias for question_text (compatibility)
  question_image_url?: string
  image_alt_text?: string
  image_width?: number
  image_height?: number
  option_a: string
  option_b: string
  option_c: string
  option_d: string
  option_e?: string
  options?: string[]  // Array format of options (compatibility)
  subject_area: string
  topic: string
  konu: string
  alt_konu?: string
  difficulty: string
  zorluk_seviyesi: string
  question_order: number
}

export interface PerformanceResponse {
  total_questions: number
  answered_questions: number
  correct_answers: number
  wrong_answers: number
  empty_answers: number
  net_score: number
  net_sayisi: number
  raw_score: number
  percentile?: number
  estimated_ability: number
  confidence_level: number
  konu_performanslari: Array<{
    konu: string
    dogru_sayisi: number
    toplam_soru: number
    basari_yuzdesi: number
  }>
  calisma_onerileri: string[]
}

export interface SubjectPerformanceResponse {
  subject: string
  total_questions: number
  correct_answers: number
  wrong_answers: number
  empty_answers: number
  success_rate: number
  average_response_time: number
  difficulty_level: number
}

export interface RemainingTimeResponse {
  remaining_seconds: number
  remaining_minutes?: number
  formatted_time: string
  warning: boolean
  exam_status: string
}

// Task 69.2: Boş bırakma (Empty answer handling) - REQ-1.6
export interface UnansweredQuestionsResponse {
  session_id: string
  unanswered_question_ids: string[]
  unanswered_count: number
  total_questions: number
}

export interface CompletionStatsResponse {
  session_id: string
  total_questions: number
  answered_questions: number
  unanswered_questions: number
  completion_percentage: number
}

class ExamService {
  /**
   * Yeni ÖSYM sınav oturumu oluştur
   */
  async createExam(request: CreateExamRequest): Promise<ExamSessionResponse> {
    try {
      const response = await apiClient.post('/api/v1/osym-exam/create', request);
      return response.data;
    } catch (error) {
      console.error('Sınav oluşturma hatası:', error);
      throw error;
    }
  }

  /**
   * Beta pratik testi oluştur.
   *
   * Kör 3-solver gate'inden geçmiş (okunabilir + cevap-onaylı) çekirdek
   * sorulardan karışık, kısa bir pratik testi kurar. Standart ÖSYM
   * dağılımını zorlamaz.
   */
  async createBetaPractice(numQuestions = 20): Promise<ExamSessionResponse> {
    try {
      const response = await apiClient.post(
        `/api/v1/osym-exam/beta-practice?num_questions=${numQuestions}`,
      );
      return response.data;
    } catch (error) {
      console.error('Beta pratik oluşturma hatası:', error);
      throw error;
    }
  }

  /**
   * ÖSYM sınavını başlat
   */
  async startExam(sessionId: string): Promise<ExamSessionResponse> {
    try {
      const response = await apiClient.post(`/api/v1/osym-exam/${sessionId}/start`);
      return response.data;
    } catch (error) {
      console.error('Sınav başlatma hatası:', error);
      throw error;
    }
  }

  /**
   * Sınav oturum bilgilerini getir
   */
  async getExamSession(sessionId: string): Promise<ExamSessionResponse> {
    try {
      // Cache-bust: response interceptor uzun max-age cache header set ediyor;
      // /start ve diğer state mutation'lar sonrası stale read olmasın diye
      // her çağrıda timestamp ekle + Cache-Control: no-cache header gönder.
      const response = await apiClient.get(
        `/api/v1/osym-exam/${sessionId}/session?_t=${Date.now()}`,
        { headers: { 'Cache-Control': 'no-cache' } },
      );
      return response.data;
    } catch (error) {
      console.error('Sınav oturum bilgisi getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Mevcut soruyu getir
   */
  async getCurrentQuestion(sessionId: string): Promise<QuestionResponse> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/current-question`);
      return response.data;
    } catch (error) {
      console.error('Mevcut soru getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Cevap kaydet
   */
  async saveAnswer(sessionId: string, request: SaveAnswerRequest): Promise<void> {
    try {
      await apiClient.post(`/api/v1/osym-exam/${sessionId}/save-answer`, request);
    } catch (error) {
      console.error('Cevap kaydetme hatası:', error);
      throw error;
    }
  }

  /**
   * Belirli bir soruya git (navigasyon)
   */
  async navigateToQuestion(sessionId: string, request: NavigateQuestionRequest): Promise<QuestionResponse> {
    try {
      const response = await apiClient.post(`/api/v1/osym-exam/${sessionId}/navigate`, request);
      return response.data;
    } catch (error) {
      console.error('Soru navigasyon hatası:', error);
      throw error;
    }
  }

  /**
   * Soru işaretleme
   */
  async flagQuestion(sessionId: string, request: FlagQuestionRequest): Promise<void> {
    try {
      await apiClient.post(`/api/v1/osym-exam/${sessionId}/flag-question`, request);
    } catch (error) {
      console.error('Soru işaretleme hatası:', error);
      throw error;
    }
  }

  /**
   * Kalan süreyi getir
   */
  async getRemainingTime(sessionId: string): Promise<RemainingTimeResponse> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/remaining-time`);
      return response.data;
    } catch (error) {
      console.error('Kalan süre getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınavı tamamla
   */
  async completeExam(sessionId: string): Promise<PerformanceResponse> {
    try {
      const response = await apiClient.post(`/api/v1/osym-exam/${sessionId}/complete`);
      return response.data;
    } catch (error) {
      console.error('Sınav tamamlama hatası:', error);
      throw error;
    }
  }

  /**
   * Performans analizi getir
   */
  async getPerformanceAnalysis(sessionId: string): Promise<PerformanceResponse> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/performance`);
      return response.data;
    } catch (error) {
      console.error('Performans analizi getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Konu bazlı performans getir
   */
  async getSubjectPerformance(sessionId: string): Promise<SubjectPerformanceResponse[]> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/subject-performance`);
      return response.data;
    } catch (error) {
      console.error('Konu performansı getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Kullanıcının tüm sınavlarını listele
   */
  async getMyExams(): Promise<ExamSessionResponse[]> {
    try {
      const response = await apiClient.get('/api/v1/osym-exam/my-exams');
      return response.data;
    } catch (error) {
      console.error('Sınavlarım listesi getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınav konfigürasyonlarını getir
   */
  async getExamConfigs(): Promise<Record<string, any>> {
    try {
      const response = await apiClient.get('/api/v1/osym-exam/exam-configs');
      return response.data;
    } catch (error) {
      console.error('Sınav konfigürasyonları getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Sonraki soruya geç (navigasyon ile)
   */
  async nextQuestion(sessionId: string, currentIndex: number): Promise<QuestionResponse> {
    return this.navigateToQuestion(sessionId, { question_index: currentIndex + 1 });
  }

  /**
   * Önceki soruya dön (navigasyon ile)
   */
  async previousQuestion(sessionId: string, currentIndex: number): Promise<QuestionResponse> {
    return this.navigateToQuestion(sessionId, { question_index: currentIndex - 1 });
  }

  /**
   * Sınav türü açıklamasını getir
   */
  getExamTypeDescription(examType: ExamType): string {
    switch (examType) {
      case ExamType.TYT:
        return 'Temel Yeterlilik Testi (TYT)';
      case ExamType.AYT:
        return 'Alan Yeterlilik Testi (AYT)';
      case ExamType.YDT:
        return 'Yabancı Dil Testi (YDT)';
      case ExamType.LGS:
        return 'Liselere Geçiş Sınavı (LGS)';
      default:
        return 'Bilinmeyen Sınav Türü';
    }
  }

  /**
   * Sınav süresi bilgilerini getir
   * Returns both camelCase and snake_case variants for compatibility
   */
  getExamDuration(examType: ExamType): {
    minutes: number
    questionCount: number
    // Alias properties for component compatibility
    duration_minutes: number
    total_questions: number
    difficulty_distribution?: { easy: number; medium: number; hard: number }
  } {
    let base: { minutes: number; questionCount: number };
    let difficultyDist: { easy: number; medium: number; hard: number } | undefined;

    switch (examType) {
      case ExamType.TYT:
        base = { minutes: 165, questionCount: 120 };
        difficultyDist = { easy: 40, medium: 50, hard: 30 };
        break;
      case ExamType.AYT:
        base = { minutes: 210, questionCount: 160 };
        difficultyDist = { easy: 50, medium: 70, hard: 40 };
        break;
      case ExamType.YDT:
        base = { minutes: 180, questionCount: 80 };
        difficultyDist = { easy: 25, medium: 35, hard: 20 };
        break;
      case ExamType.LGS:
        base = { minutes: 135, questionCount: 90 };
        difficultyDist = { easy: 30, medium: 40, hard: 20 };
        break;
      default:
        base = { minutes: 0, questionCount: 0 };
    }

    return {
      ...base,
      duration_minutes: base.minutes,
      total_questions: base.questionCount,
      difficulty_distribution: difficultyDist,
    };
  }

  /**
   * Sınav durumu kontrolü
   */
  isExamActive(session: ExamSessionResponse): boolean {
    return session.status === ExamStatus.IN_PROGRESS;
  }

  /**
   * Sınav tamamlandı mı kontrolü
   */
  isExamCompleted(session: ExamSessionResponse): boolean {
    return session.status === ExamStatus.COMPLETED;
  }

  /**
   * Sınav ilerlemesi yüzdesini hesapla
   */
  getExamProgress(session: ExamSessionResponse): number {
    const current = session.current_question_index + 1;
    const total = session.total_questions;
    return total > 0 ? (current / total) * 100 : 0;
  }

  /**
   * Sınav sonucunu getir
   */
  async getExamResult(sessionId: string): Promise<PerformanceResponse> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/performance`);
      return response.data;
    } catch (error) {
      console.error('Sınav sonucu getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınavı bitir (complete exam ile aynı)
   */
  async finishExam(sessionId: string): Promise<PerformanceResponse> {
    return this.completeExam(sessionId);
  }

  /**
   * Cevaplanmamış soruları getir - Task 69.2 (REQ-1.6)
   */
  async getUnansweredQuestions(sessionId: string): Promise<UnansweredQuestionsResponse> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/unanswered-questions`);
      return response.data;
    } catch (error) {
      console.error('Cevaplanmamış sorular getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Tamamlanma istatistiklerini getir - Task 69.2 (REQ-1.6)
   */
  async getCompletionStats(sessionId: string): Promise<CompletionStatsResponse> {
    try {
      const response = await apiClient.get(`/api/v1/osym-exam/${sessionId}/completion-stats`);
      return response.data;
    } catch (error) {
      console.error('Tamamlanma istatistikleri getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınav tamamlanma yüzdesini hesapla (local helper)
   */
  calculateCompletionPercentage(answeredCount: number, totalCount: number): number {
    if (totalCount === 0) {return 0;}
    return Math.round((answeredCount / totalCount) * 100 * 100) / 100;
  }

  /**
   * Boş soru sayısını hesapla (local helper)
   */
  calculateEmptyAnswers(totalQuestions: number, answeredQuestions: number): number {
    return Math.max(0, totalQuestions - answeredQuestions);
  }

  // ============================================
  // Alias methods for examStore compatibility
  // ============================================

  /**
   * Sınav oturum bilgilerini getir (getExamSession alias)
   */
  async getSessionInfo(sessionId: string): Promise<ExamSessionResponse> {
    return this.getExamSession(sessionId);
  }

  /**
   * Belirli bir soruyu getir (navigateToQuestion alias)
   */
  async getQuestion(sessionId: string, questionIndex: number): Promise<QuestionResponse> {
    return this.navigateToQuestion(sessionId, { question_index: questionIndex });
  }

  /**
   * Performans analizi getir (getPerformanceAnalysis alias)
   */
  async getPerformance(sessionId: string): Promise<PerformanceResponse> {
    return this.getPerformanceAnalysis(sessionId);
  }

  /**
   * Sınavı duraklat
   */
  async pauseExam(sessionId: string): Promise<ExamSessionResponse> {
    try {
      const response = await apiClient.post(`/api/v1/osym-exam/${sessionId}/pause`);
      return response.data;
    } catch (error) {
      console.error('Sınav duraklatma hatası:', error);
      throw error;
    }
  }

  /**
   * Sınavı terk et
   */
  async abandonExam(sessionId: string): Promise<ExamSessionResponse> {
    try {
      const response = await apiClient.post(`/api/v1/osym-exam/${sessionId}/abandon`);
      return response.data;
    } catch (error) {
      console.error('Sınav terk etme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınavı gönder (completeExam alias)
   */
  async submitExam(sessionId: string): Promise<PerformanceResponse> {
    return this.completeExam(sessionId);
  }

  /**
   * Cevap gönder (saveAnswer alias with different signature)
   */
  async submitAnswer(sessionId: string, questionId: string, answer: string): Promise<void> {
    return this.saveAnswer(sessionId, {
      question_id: questionId,
      selected_answer: answer,
    });
  }

  // ============================================
  // WebSocket methods (stub implementations)
  // ============================================

  /**
   * WebSocket bağlantısı kur
   */
  connectWebSocket(_sessionId: string): void {
    // No-op: /ws/exam/* endpoint not implemented; exam uses polling
  }

  /**
   * WebSocket bağlantısını kapat
   */
  disconnectWebSocket(): void {
    // No-op: no active WebSocket connection
  }

  /**
   * WebSocket mesaj handler'ı ayarla
   * Returns unsubscribe function for cleanup
   */
  onWebSocketMessage(_handler: (message: WebSocketMessage) => void): () => void {
    return () => { /* no-op: no WebSocket connection */ };
  }

  /**
   * Öğrenci istatistiklerini getir
   */
  async getStudentStats(): Promise<Record<string, unknown>> {
    try {
      const response = await apiClient.get('/api/v1/student-dashboard/istatistikler');
      return response.data;
    } catch (error) {
      console.error('Öğrenci istatistikleri getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınav oturumu oluştur (createExam alias)
   */
  async createExamSession(examType: ExamType): Promise<ExamSessionResponse> {
    return this.createExam({ exam_type: examType });
  }

  /**
   * Sınav geçmişini getir - useExamQueries için
   */
  async getExamHistory(params?: { limit?: number; offset?: number }): Promise<ExamSessionResponse[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.limit) {queryParams.append('limit', params.limit.toString());}
      if (params?.offset) {queryParams.append('offset', params.offset.toString());}

      const url = `/api/v1/sinav/history${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await apiClient.get(url);
      return response.data.sessions || response.data || [];
    } catch (error) {
      console.error('Sınav geçmişi getirme hatası:', error);
      return [];
    }
  }

  /**
   * Tüm sınav sonuçlarını getir - useExamQueries için (alias for multiple results)
   */
  async getExamResults(sessionIds?: string[]): Promise<PerformanceResponse[]> {
    try {
      if (sessionIds && sessionIds.length > 0) {
        const results = await Promise.all(
          sessionIds.map(id => this.getExamResult(id).catch(() => null)),
        );
        return results.filter((r): r is PerformanceResponse => r !== null);
      }

      // Get latest results if no specific IDs provided
      const response = await apiClient.get('/api/v1/sinav/results');
      return response.data.results || response.data || [];
    } catch (error) {
      console.error('Sınav sonuçları getirme hatası:', error);
      return [];
    }
  }

  // ─── F8: Error Taxonomy ─────────────────────────────────────

  /**
   * Yanlış cevaba hata tipi ata (F8 Error Taxonomy)
   * @param examSessionId Sınav oturum ID'si
   * @param questionId Soru ID'si
   * @param errorType concept | procedural | careless | knowledge_gap
   */
  async updateErrorType(
    examSessionId: string,
    questionId: string,
    errorType: string,
  ): Promise<{ success: boolean; message: string; error_type?: string }> {
    const response = await apiClient.patch(
      `/api/v1/exam-answer-tracking/${examSessionId}/answers/${questionId}/error-type`,
      { error_type: errorType },
    );
    return response.data;
  }
}

// WebSocket message type for real-time exam updates
export interface WebSocketMessage {
  type: string
  remaining_time?: number
  message?: string
  [key: string]: unknown
}

// Singleton instance
export const examService = new ExamService();
export default examService;
