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

export interface StudentStatistics {
  profile: {
    total_cards: number;
    total_reviews: number;
    average_retention: number;
    study_streak_days: number;
    last_study_date: string | null;
    cards_due_today: number;
    cards_learned_today: number;
    study_time_today_minutes: number;
    target_retention: number;
    group_study_preference: boolean;
    family_pressure_level: number;
    exam_anxiety_level: number;
    study_consistency: number;
  };
  subject_statistics: Array<{
    subject: string;
    total_cards: number;
    cards_mastered: number;
    cards_learning: number;
    cards_difficult: number;
    average_difficulty: number;
    average_stability: number;
    success_rate: number;
    total_study_time_minutes: number;
    last_studied: string | null;
  }>;
  recent_performance: {
    total_reviews: number;
    average_grade: number;
    recent_success_rate: number;
    recent_reviews_count: number;
  };
  recent_sessions: Array<{
    id: string;
    session_start: string;
    session_end: string | null;
    duration_minutes: number;
    cards_reviewed: number;
    cards_learned: number;
    average_grade: number;
    session_type: string;
  }>;
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

  /**
   * Yeni flashcard oluştur
   */
  async createFlashcard(
    studentId: string,
    request: CreateFlashcardRequest,
  ): Promise<ApiResponse<FSRSCard | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/cards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          student_id: studentId,
          ...request,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Create flashcard error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Flashcard oluşturma hatası',
      };
    }
  }

  /**
   * Flashcard incelemesi yap
   */
  async reviewFlashcard(
    studentId: string,
    request: ReviewFlashcardRequest,
  ): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/cards/${request.card_id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          student_id: studentId,
          grade: request.grade,
          response_time_ms: request.response_time_ms,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Review flashcard error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Flashcard inceleme hatası',
      };
    }
  }

  /**
   * Vadesi gelen kartları getir
   */
  async getDueCards(
    studentId: string,
    limit: number = 20,
  ): Promise<ApiResponse<FSRSCard[] | null>> {
    try {
      const response = await fetch(
        `${this.baseUrl}/cards/due?student_id=${studentId}&limit=${limit}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data || [],
        message: data.message,
      };
    } catch (error) {
      console.error('Get due cards error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Vadesi gelen kartları getirme hatası',
      };
    }
  }

  /**
   * Çalışma önerilerini getir
   */
  async getStudyRecommendations(
    studentId: string,
  ): Promise<ApiResponse<StudyRecommendations | null>> {
    try {
      const response = await fetch(
        `${this.baseUrl}/recommendations?student_id=${studentId}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get study recommendations error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Çalışma önerileri getirme hatası',
      };
    }
  }

  /**
   * Öğrenci istatistiklerini getir
   */
  async getStudentStatistics(
    studentId: string,
  ): Promise<ApiResponse<StudentStatistics | null>> {
    try {
      const response = await fetch(
        `${this.baseUrl}/statistics?student_id=${studentId}`,
        {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Get student statistics error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Öğrenci istatistikleri getirme hatası',
      };
    }
  }

  /**
   * Çalışma oturumu başlat
   */
  async startStudySession(
    studentId: string,
    sessionType: string = 'regular',
  ): Promise<ApiResponse<string | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          student_id: studentId,
          session_type: sessionType,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Start study session error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Çalışma oturumu başlatma hatası',
      };
    }
  }

  /**
   * Çalışma oturumunu sonlandır
   */
  async endStudySession(sessionId: string): Promise<ApiResponse<StudySessionSummary | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/end`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('End study session error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Çalışma oturumu sonlandırma hatası',
      };
    }
  }

  /**
   * Kart zamanlamasını hesapla (preview)
   */
  async calculateSchedule(
    studentId: string,
    cardId: string,
    grade: FSRSGrade,
  ): Promise<ApiResponse<FSRSSchedule | null>> {
    try {
      const response = await fetch(`${this.baseUrl}/cards/${cardId}/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          student_id: studentId,
          grade: grade,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.success,
        data: data.data,
        message: data.message,
      };
    } catch (error) {
      console.error('Calculate schedule error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'Zamanlama hesaplama hatası',
      };
    }
  }

  /**
   * Sistem sağlık kontrolü
   */
  async healthCheck(): Promise<ApiResponse<any>> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: data.status === 'healthy',
        data: data,
        message: data.status === 'healthy' ? 'FSRS sistemi sağlıklı' : 'FSRS sistemi sağlıksız',
      };
    } catch (error) {
      console.error('FSRS health check error:', error);
      return {
        success: false,
        data: null,
        message: error instanceof Error ? error.message : 'FSRS sağlık kontrolü hatası',
      };
    }
  }
}

// Singleton instance
const fsrsService = new FSRSService();

export default fsrsService;