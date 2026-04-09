/**
 * FSRS (Free Spaced Repetition Scheduler) API Servisi
 * Teknofest 2025 - Eğitim Eylemci Projesi
 */

import config from '../config';
import {
  FSRSCard,
  FSRSSchedule,
  ApiResponse,
  FSRSGrade,
} from '../types/revolutionary';

const API_BASE_URL = config.api.baseURL;

export interface CreateFlashcardRequest {
  subject: string;
  topic: string;
  content: string;
  answer: string;
}

export interface ReviewFlashcardRequest {
  card_id: string;
  grade: FSRSGrade;
  response_time_ms: number;
}

export interface StudyRecommendations {
  recommended_cards: number;
  optimal_study_time: number;
  difficulty_adjustment: string;
  cultural_advice: string;
  period_advice: string;
  total_cards: number;
  new_cards: number;
  learning_cards: number;
  review_cards: number;
  student_context: {
    group_study_preference: boolean;
    family_pressure_level: number;
    exam_anxiety_level: number;
    study_consistency: number;
  };
}

/**
 * Backend /api/v1/fsrs/stats -> StatsResponse (schemas/fsrs_schemas.py)
 * Alan adlari backend ile tam eslesir — eski nested {profile,...} yapisi kaldirildi.
 */
export interface StudentStatistics {
  total_cards:    number;   // Toplam FSRS karti
  new_count:      number;   // Yeni kartlar (state=0)
  learning_count: number;   // Ogrenme asamasindaki kartlar
  review_count:   number;   // Tekrar asamasindaki kartlar
  due_now:        number;   // Simdi vadesi gelmis kartlar
  avg_stability:  number;   // Ortalama stabilite
  total_lapses:   number;   // Toplam hata sayisi
}

export interface StudySessionSummary {
  session_id: string;
  duration_minutes: number;
  cards_reviewed: number;
  cards_learned: number;
  average_grade: number;
  success_rate: number;
}

class FSRSService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_BASE_URL}/api/v1/fsrs`;
  }

  /** Yeni flashcard oluştur (endpoint henüz yok — 404 fallback) */
  async createFlashcard(
    studentId: string,
    request: CreateFlashcardRequest,
  ): Promise<ApiResponse<FSRSCard | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/flashcards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ student_id: studentId, ...request }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: data.success, data: data.data, message: data.message };
    } catch (error) {
      console.error('Create flashcard error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Flashcard oluşturma hatası' };
    }
  }

  /**
   * Flashcard incelemesi yap
   * Backend: POST /api/v1/fsrs/review → ReviewResponse (question_id, new_stability, ...)
   * Backend {success,data} wrapper dönmez — direkt ReviewResponse döner
   */
  async reviewFlashcard(
    _studentId: string,
    request: ReviewFlashcardRequest,
  ): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          question_id: request.card_id,
          is_correct: request.grade >= 3,
          response_ms: request.response_time_ms,
        }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      // Backend ReviewResponse döndürür ({question_id, new_stability, ...}), {success,data} değil
      return { success: true, data: data, message: 'OK' };
    } catch (error) {
      console.error('Review flashcard error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Flashcard inceleme hatası' };
    }
  }

  /**
   * Vadesi gelen kartları getir
   * Backend: GET /api/v1/fsrs/due → list[DueItemResponse] (düz JSON array, wrapper yok)
   * DueItemResponse: question_id, stem, options, subject_id,
   *   stability, difficulty, due_date, retrievability, urgency_score, state, reps, lapses
   */
  async getDueCards(
    _studentId: string,
    limit: number = 20,
  ): Promise<ApiResponse<FSRSCard[] | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/due?limit=${limit}`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      // Backend düz array döndürür — {success,data} wrapper değil
      const items: any[] = await response.json();
      return {
        success: Array.isArray(items),
        data: Array.isArray(items) ? items : [],
        message: 'OK',
      };
    } catch (error) {
      console.error('Get due cards error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Vadesi gelen kartları getirme hatası' };
    }
  }

  /**
   * Çalışma önerilerini getir
   * Backend: endpoint yok → 404, fallback mock kullanılır (FSRSScheduler'da)
   */
  async getStudyRecommendations(
    _studentId: string,
  ): Promise<ApiResponse<StudyRecommendations | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/recommendations`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: data.success, data: data.data, message: data.message };
    } catch (error) {
      console.error('Get study recommendations error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Çalışma önerileri getirme hatası' };
    }
  }

  /**
   * Öğrenci istatistiklerini getir
   * Backend: GET /api/v1/fsrs/stats → StatsResponse (düz obje, wrapper yok)
   * Alanlar: total_cards, new_count, learning_count, review_count, due_now, avg_stability, total_lapses
   */
  async getStudentStatistics(
    _studentId: string,
  ): Promise<ApiResponse<StudentStatistics | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/stats`, {
        method: 'GET',
        credentials: 'include',
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      // Backend StatsResponse döndürür ({total_cards, due_now, ...}), {success,data} değil
      const data = await response.json();
      return { success: true, data: data, message: 'OK' };
    } catch (error) {
      console.error('Get student statistics error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Öğrenci istatistikleri getirme hatası' };
    }
  }

  /** Çalışma oturumu başlat (endpoint henüz yok) */
  async startStudySession(_studentId: string, sessionType: string = 'regular'): Promise<ApiResponse<string | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/study-sessions/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ session_type: sessionType }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: data.success, data: data.data, message: data.message };
    } catch (error) {
      console.error('Start study session error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Çalışma oturumu başlatma hatası' };
    }
  }

  /** Çalışma oturumunu sonlandır (endpoint henüz yok) */
  async endStudySession(sessionId: string): Promise<ApiResponse<StudySessionSummary | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/study-sessions/${sessionId}/end`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: data.success, data: data.data, message: data.message };
    } catch (error) {
      console.error('End study session error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Çalışma oturumu sonlandırma hatası' };
    }
  }

  /** Kart zamanlamasını hesapla (endpoint henüz yok) */
  async calculateSchedule(_studentId: string, cardId: string, grade: FSRSGrade): Promise<ApiResponse<FSRSSchedule | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/schedule`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ card_id: cardId, grade }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: data.success, data: data.data, message: data.message };
    } catch (error) {
      console.error('Calculate schedule error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'Zamanlama hesaplama hatası' };
    }
  }

  /** Sistem sağlık kontrolü */
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, { method: 'GET', credentials: 'include' });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      return { success: data.status === 'healthy', data, message: data.status };
    } catch (error) {
      console.error('FSRS health check error:', error);
      return { success: false, data: null, message: error instanceof Error ? error.message : 'FSRS sağlık kontrolü hatası' };
    }
  }
}

const fsrsService = new FSRSService();
export default fsrsService;
