/**
 * TYT Deneme Sınavı Servisi
 *
 * Backend karşılığı: `backend/api/v1/exams.py` (prefix `/api/v1/exams`).
 *
 * NOT: Bu servis, `examService.ts`'in konuştuğu `/api/v1/osym-exam/*` API'sinden
 * AYRI bir uç kümesidir. İkisi farklı router, farklı response şekli döndürür —
 * bu yüzden kasıtlı olarak ayrı dosyada tutulur. `examService`'e karıştırmak
 * `getExamSession` / `submitExam` ad çatışması üretir.
 */

import { apiClient } from './apiClient';

/** Sınav oluşturma yanıtı — POST /generate-mock */
export interface GenerateMockExamResponse {
  status: string
  exam_session_id: string
  total_questions: number
}

/** Tek soru — GET /{session_id} içindeki `questions` elemanı */
export interface ExamQuestionData {
  id: string
  order: number
  text: string
  options: { letter: string; text: string }[]
  /** TUR | SOS | MAT | FEN — soru sırasından türetilir */
  branch: string
  /** Öğrencinin daha önce kaydettiği cevap (resume için) */
  selected_answer?: string
}

/** Oturum + sıralı sorular — GET /{session_id} */
export interface MockExamSessionResponse {
  id: string
  exam_name: string
  exam_type: string
  total_questions: number
  duration_minutes: number
  status: string
  questions: ExamQuestionData[]
}

/** Branş bazlı doğru/yanlış/boş/net kırılımı */
export interface BranchStat {
  correct: number
  wrong: number
  empty: number
  net: number
}

/** Sınav sonucu — POST /{session_id}/submit */
export interface ExamSubmitResult {
  status: string
  session_id: string
  total_correct: number
  total_wrong: number
  total_empty: number
  raw_score: number
  /** Anahtarlar: TUR, SOS, MAT, FEN */
  branch_breakdown: Record<string, BranchStat>
  xp_earned: number
  coins_earned: number
}

/** Cevap kaydetme yanıtı — POST /{session_id}/answer */
export interface SaveExamAnswerResponse {
  status: string
  question_id: string
  selected_answer?: string
}

const BASE = '/api/v1/exams';

class MockExamService {
  /**
   * 120 soruluk TYT deneme sınavı üret (Bell Curve ile branş bazlı seçim)
   */
  async generateMockExam(
    studentId: string,
    organizationId?: string,
  ): Promise<GenerateMockExamResponse> {
    try {
      const response = await apiClient.post(`${BASE}/generate-mock`, {
        student_id: studentId,
        ...(organizationId ? { organization_id: organizationId } : {}),
      });
      return response.data;
    } catch (error) {
      console.error('Deneme sınavı oluşturma hatası:', error);
      throw error;
    }
  }

  /**
   * Sınav oturumunu sıralı sorular + kaydedilmiş cevaplarla getir
   *
   * @param bionicReading Sunucu tarafında bionic-reading dönüşümü uygula
   */
  async getExamSession(
    sessionId: string,
    bionicReading = false,
  ): Promise<MockExamSessionResponse> {
    try {
      const response = await apiClient.get(
        `${BASE}/${sessionId}?bionic_reading=${bionicReading}`,
      );
      return response.data;
    } catch (error) {
      console.error('Deneme sınavı oturumu getirme hatası:', error);
      throw error;
    }
  }

  /**
   * Tek bir sorunun cevabını kaydet/güncelle (gerçek zamanlı)
   *
   * @param responseTimeSeconds Bu soruya harcanan süre; sunucuda toplanır
   */
  async saveExamAnswer(
    sessionId: string,
    questionId: string,
    selectedAnswer: string | null,
    responseTimeSeconds = 0,
  ): Promise<SaveExamAnswerResponse> {
    try {
      const response = await apiClient.post(`${BASE}/${sessionId}/answer`, {
        question_id: questionId,
        selected_answer: selectedAnswer,
        response_time_seconds: responseTimeSeconds,
      });
      return response.data;
    } catch (error) {
      console.error('Deneme sınavı cevap kaydetme hatası:', error);
      throw error;
    }
  }

  /**
   * Sınavı bitir; net/branş kırılımı + XP/coin kazancını döndürür
   */
  async submitExam(sessionId: string, timeSpentSeconds = 0): Promise<ExamSubmitResult> {
    try {
      const response = await apiClient.post(`${BASE}/${sessionId}/submit`, {
        time_spent_seconds: timeSpentSeconds,
      });
      return response.data;
    } catch (error) {
      console.error('Deneme sınavı bitirme hatası:', error);
      throw error;
    }
  }
}

export const mockExamService = new MockExamService();
export default mockExamService;
