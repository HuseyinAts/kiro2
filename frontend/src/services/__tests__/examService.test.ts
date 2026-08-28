/**
 * ÖSYM Uyumlu Sınav Servisi Test Dosyası
 * examService.ts için kapsamlı unit testler
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest'
import {
  examService,
  ExamType,
  ExamStatus,
  QuestionDifficulty,
  CreateExamRequest,
  SaveAnswerRequest,
  FlagQuestionRequest,
  NavigateQuestionRequest,
  ExamSessionResponse,
  QuestionResponse,
  PerformanceResponse,
  SubjectPerformanceResponse,
  RemainingTimeResponse,
  WebSocketMessage
} from '../examService'
import { apiClient } from '../apiClient'

// Mock apiClient
vi.mock('../apiClient', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock WebSocket
const mockWebSocket = {
  close: vi.fn(),
  send: vi.fn(),
  onopen: null as any,
  onmessage: null as any,
  onclose: null as any,
  onerror: null as any,
  readyState: WebSocket.OPEN
}

// @ts-ignore
global.WebSocket = vi.fn(() => mockWebSocket)

describe('ExamService', () => {
  const mockApiClient = apiClient as {
    post: Mock
    get: Mock
    put: Mock
    delete: Mock
  }

  beforeEach(() => {
    vi.clearAllMocks()
    // WebSocket bağlantısını temizle
    examService.disconnectWebSocket()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Enum Değerleri', () => {
    it('ExamType enum değerlerini doğru döndürmeli', () => {
      expect(ExamType.TYT).toBe('TYT')
      expect(ExamType.AYT).toBe('AYT')
      expect(ExamType.YDT).toBe('YDT')
    })

    it('ExamStatus enum değerlerini doğru döndürmeli', () => {
      expect(ExamStatus.NOT_STARTED).toBe('not_started')
      expect(ExamStatus.IN_PROGRESS).toBe('in_progress')
      expect(ExamStatus.COMPLETED).toBe('completed')
      expect(ExamStatus.ABANDONED).toBe('abandoned')
      expect(ExamStatus.EXPIRED).toBe('expired')
    })

    it('QuestionDifficulty enum değerlerini doğru döndürmeli', () => {
      expect(QuestionDifficulty.EASY).toBe('EASY')
      expect(QuestionDifficulty.MEDIUM).toBe('MEDIUM')
      expect(QuestionDifficulty.HARD).toBe('HARD')
    })
  })

  describe('createExam', () => {
    it('başarılı sınav oluşturma', async () => {
      const mockRequest: CreateExamRequest = {
        exam_type: ExamType.TYT,
        custom_config: { difficulty: 'medium' }
      }

      const mockResponse: ExamSessionResponse = {
        session_id: 'test-session-123',
        student_id: 'student-456',
        exam_type: 'TYT',
        status: 'not_started',
        total_questions: 120,
        duration_minutes: 165,
        current_question_index: 0
      }

      mockApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await examService.createExam(mockRequest)

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/osym-exam/create', mockRequest)
      expect(result).toEqual(mockResponse)
    })

    it('sınav oluşturma hatası durumunda hata fırlatmalı', async () => {
      const mockRequest: CreateExamRequest = {
        exam_type: ExamType.TYT
      }

      const mockError = new Error('API Hatası')
      mockApiClient.post.mockRejectedValue(mockError)

      await expect(examService.createExam(mockRequest)).rejects.toThrow('API Hatası')
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/osym-exam/create', mockRequest)
    })
  })

  describe('startExam', () => {
    it('başarılı sınav başlatma', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: ExamSessionResponse = {
        session_id: sessionId,
        student_id: 'student-456',
        exam_type: 'TYT',
        status: 'in_progress',
        total_questions: 120,
        duration_minutes: 165,
        current_question_index: 0,
        started_at: '2024-01-01T10:00:00Z'
      }

      mockApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await examService.startExam(sessionId)

      expect(mockApiClient.post).toHaveBeenCalledWith(`/api/v1/osym-exam/${sessionId}/start`)
      expect(result).toEqual(mockResponse)
      expect(result.status).toBe('in_progress')
    })
  })

  describe('getExamSession', () => {
    it('sınav oturum bilgilerini başarıyla getirmeli', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: ExamSessionResponse = {
        session_id: sessionId,
        student_id: 'student-456',
        exam_type: 'TYT',
        status: 'in_progress',
        total_questions: 120,
        duration_minutes: 165,
        current_question_index: 5
      }

      mockApiClient.get.mockResolvedValue({ data: mockResponse })

      const result = await examService.getExamSession(sessionId)

      expect(mockApiClient.get).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/osym-exam/${sessionId}/session`),
        expect.any(Object),
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getCurrentQuestion', () => {
    it('mevcut soruyu başarıyla getirmeli', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: QuestionResponse = {
        id: 'question-1',
        question_text: 'Test sorusu?',
        option_a: 'A şıkkı',
        option_b: 'B şıkkı',
        option_c: 'C şıkkı',
        option_d: 'D şıkkı',
        subject_area: 'matematik',
        topic: 'cebir',
        difficulty: 'MEDIUM',
        question_order: 1
      }

      mockApiClient.get.mockResolvedValue({ data: mockResponse })

      const result = await examService.getCurrentQuestion(sessionId)

      expect(mockApiClient.get).toHaveBeenCalledWith(`/api/v1/osym-exam/${sessionId}/current-question`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('saveAnswer', () => {
    it('cevabı başarıyla kaydetmeli', async () => {
      const sessionId = 'test-session-123'
      const mockRequest: SaveAnswerRequest = {
        question_id: 'question-1',
        selected_answer: 'A',
        response_time: 30000
      }

      mockApiClient.post.mockResolvedValue({ data: {} })

      await examService.saveAnswer(sessionId, mockRequest)

      expect(mockApiClient.post).toHaveBeenCalledWith(
        `/api/v1/osym-exam/${sessionId}/save-answer`,
        mockRequest
      )
    })
  })

  describe('navigateToQuestion', () => {
    it('belirli soruya başarıyla gitmeli', async () => {
      const sessionId = 'test-session-123'
      const mockRequest: NavigateQuestionRequest = {
        question_index: 5
      }

      const mockResponse: QuestionResponse = {
        id: 'question-6',
        question_text: '6. soru?',
        option_a: 'A şıkkı',
        option_b: 'B şıkkı',
        option_c: 'C şıkkı',
        option_d: 'D şıkkı',
        subject_area: 'turkce',
        topic: 'dil bilgisi',
        difficulty: 'EASY',
        question_order: 6
      }

      mockApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await examService.navigateToQuestion(sessionId, mockRequest)

      expect(mockApiClient.post).toHaveBeenCalledWith(
        `/api/v1/osym-exam/${sessionId}/navigate`,
        mockRequest
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('flagQuestion', () => {
    it('soruyu başarıyla işaretlemeli', async () => {
      const sessionId = 'test-session-123'
      const mockRequest: FlagQuestionRequest = {
        question_id: 'question-1',
        flagged: true
      }

      mockApiClient.post.mockResolvedValue({ data: {} })

      await examService.flagQuestion(sessionId, mockRequest)

      expect(mockApiClient.post).toHaveBeenCalledWith(
        `/api/v1/osym-exam/${sessionId}/flag-question`,
        mockRequest
      )
    })
  })

  describe('getRemainingTime', () => {
    it('kalan süreyi başarıyla getirmeli', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: RemainingTimeResponse = {
        remaining_seconds: 3600,
        remaining_minutes: 60,
        formatted_time: '01:00:00',
        warning: false,
        exam_status: 'in_progress'
      }

      mockApiClient.get.mockResolvedValue({ data: mockResponse })

      const result = await examService.getRemainingTime(sessionId)

      expect(mockApiClient.get).toHaveBeenCalledWith(`/api/v1/osym-exam/${sessionId}/remaining-time`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('completeExam', () => {
    it('sınavı başarıyla tamamlamalı', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: PerformanceResponse = {
        total_questions: 120,
        answered_questions: 115,
        correct_answers: 85,
        wrong_answers: 30,
        empty_answers: 5,
        net_score: 55,
        raw_score: 85,
        percentile: 75,
        estimated_ability: 0.5,
        confidence_level: 0.8
      }

      mockApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await examService.completeExam(sessionId)

      expect(mockApiClient.post).toHaveBeenCalledWith(`/api/v1/osym-exam/${sessionId}/complete`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getPerformanceAnalysis', () => {
    it('performans analizini başarıyla getirmeli', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: PerformanceResponse = {
        total_questions: 120,
        answered_questions: 120,
        correct_answers: 90,
        wrong_answers: 30,
        empty_answers: 0,
        net_score: 60,
        raw_score: 90,
        percentile: 80,
        estimated_ability: 0.6,
        confidence_level: 0.85
      }

      mockApiClient.get.mockResolvedValue({ data: mockResponse })

      const result = await examService.getPerformanceAnalysis(sessionId)

      expect(mockApiClient.get).toHaveBeenCalledWith(`/api/v1/osym-exam/${sessionId}/performance`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSubjectPerformance', () => {
    it('konu bazlı performansı başarıyla getirmeli', async () => {
      const sessionId = 'test-session-123'
      const mockResponse: SubjectPerformanceResponse[] = [
        {
          subject: 'matematik',
          total_questions: 40,
          correct_answers: 30,
          wrong_answers: 8,
          empty_answers: 2,
          success_rate: 0.75,
          average_response_time: 45.5,
          difficulty_level: 2.3
        },
        {
          subject: 'turkce',
          total_questions: 40,
          correct_answers: 35,
          wrong_answers: 5,
          empty_answers: 0,
          success_rate: 0.875,
          average_response_time: 38.2,
          difficulty_level: 1.8
        }
      ]

      mockApiClient.get.mockResolvedValue({ data: mockResponse })

      const result = await examService.getSubjectPerformance(sessionId)

      expect(mockApiClient.get).toHaveBeenCalledWith(`/api/v1/osym-exam/${sessionId}/subject-performance`)
      expect(result).toEqual(mockResponse)
      expect(result).toHaveLength(2)
    })
  })

  describe('Navigation Helper Methods', () => {
    it('nextQuestion - sonraki soruya geçmeli', async () => {
      const sessionId = 'test-session-123'
      const currentIndex = 5
      const mockResponse: QuestionResponse = {
        id: 'question-7',
        question_text: '7. soru?',
        option_a: 'A şıkkı',
        option_b: 'B şıkkı',
        option_c: 'C şıkkı',
        option_d: 'D şıkkı',
        subject_area: 'matematik',
        topic: 'geometri',
        difficulty: 'HARD',
        question_order: 7
      }

      mockApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await examService.nextQuestion(sessionId, currentIndex)

      expect(mockApiClient.post).toHaveBeenCalledWith(
        `/api/v1/osym-exam/${sessionId}/navigate`,
        { question_index: 6 }
      )
      expect(result).toEqual(mockResponse)
    })

    it('previousQuestion - önceki soruya dönmeli', async () => {
      const sessionId = 'test-session-123'
      const currentIndex = 5
      const mockResponse: QuestionResponse = {
        id: 'question-5',
        question_text: '5. soru?',
        option_a: 'A şıkkı',
        option_b: 'B şıkkı',
        option_c: 'C şıkkı',
        option_d: 'D şıkkı',
        subject_area: 'fen',
        topic: 'fizik',
        difficulty: 'MEDIUM',
        question_order: 5
      }

      mockApiClient.post.mockResolvedValue({ data: mockResponse })

      const result = await examService.previousQuestion(sessionId, currentIndex)

      expect(mockApiClient.post).toHaveBeenCalledWith(
        `/api/v1/osym-exam/${sessionId}/navigate`,
        { question_index: 4 }
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('WebSocket İşlemleri', () => {
    beforeEach(() => {
      // Mock window.location
      Object.defineProperty(window, 'location', {
        value: {
          protocol: 'http:',
          host: 'localhost:3000'
        },
        writable: true
      })
    })

    it('WebSocket bağlantısını kurmalı ve kapatmalı (stub)', () => {
      const sinavId = 'test-sinav-123'
      expect(() => examService.connectWebSocket(sinavId)).not.toThrow()
      expect(() => examService.disconnectWebSocket()).not.toThrow()
    })

    it('WebSocket mesaj handler eklemeli ve kaldırmalı', () => {
      const mockHandler = vi.fn()

      const cleanup = examService.onWebSocketMessage(mockHandler)

      expect(typeof cleanup).toBe('function')
      expect(() => cleanup()).not.toThrow()
    })
  })

  describe('Utility Methods', () => {
    it('getExamTypeDescription - sınav türü açıklamasını döndürmeli', () => {
      expect(examService.getExamTypeDescription(ExamType.TYT)).toBe('Temel Yeterlilik Testi (TYT)')
      expect(examService.getExamTypeDescription(ExamType.AYT)).toBe('Alan Yeterlilik Testi (AYT)')
      expect(examService.getExamTypeDescription(ExamType.YDT)).toBe('Yabancı Dil Testi (YDT)')
    })

    it('getExamDuration - sınav süre bilgilerini döndürmeli', () => {
      expect(examService.getExamDuration(ExamType.TYT)).toEqual(expect.objectContaining({ minutes: 165, questionCount: 120 }))
      expect(examService.getExamDuration(ExamType.AYT)).toEqual(expect.objectContaining({ minutes: 210, questionCount: 160 }))
      expect(examService.getExamDuration(ExamType.YDT)).toEqual(expect.objectContaining({ minutes: 180, questionCount: 80 }))
    })

    it('isExamActive - sınav aktif durumunu kontrol etmeli', () => {
      const activeSession: ExamSessionResponse = {
        session_id: 'test',
        student_id: 'student',
        exam_type: 'TYT',
        status: 'in_progress',
        total_questions: 120,
        duration_minutes: 165,
        current_question_index: 10
      }

      const inactiveSession: ExamSessionResponse = {
        ...activeSession,
        status: 'completed'
      }

      expect(examService.isExamActive(activeSession)).toBe(true)
      expect(examService.isExamActive(inactiveSession)).toBe(false)
    })

    it('isExamCompleted - sınav tamamlanma durumunu kontrol etmeli', () => {
      const completedSession: ExamSessionResponse = {
        session_id: 'test',
        student_id: 'student',
        exam_type: 'TYT',
        status: 'completed',
        total_questions: 120,
        duration_minutes: 165,
        current_question_index: 120
      }

      const activeSession: ExamSessionResponse = {
        ...completedSession,
        status: 'in_progress'
      }

      expect(examService.isExamCompleted(completedSession)).toBe(true)
      expect(examService.isExamCompleted(activeSession)).toBe(false)
    })

    it('getExamProgress - sınav ilerlemesi yüzdesini hesaplamalı', () => {
      const session: ExamSessionResponse = {
        session_id: 'test',
        student_id: 'student',
        exam_type: 'TYT',
        status: 'in_progress',
        total_questions: 120,
        duration_minutes: 165,
        current_question_index: 59 // 60. soru (0-indexed)
      }

      const progress = examService.getExamProgress(session)
      expect(progress).toBe(50) // 60/120 * 100 = 50%
    })

    it('getExamProgress - sıfır soru durumunda 0 döndürmeli', () => {
      const session: ExamSessionResponse = {
        session_id: 'test',
        student_id: 'student',
        exam_type: 'TYT',
        status: 'not_started',
        total_questions: 0,
        duration_minutes: 165,
        current_question_index: 0
      }

      const progress = examService.getExamProgress(session)
      expect(progress).toBe(0)
    })
  })

  describe('Error Handling', () => {
    it('API hatalarını yakalayıp yeniden fırlatmalı', async () => {
      const sessionId = 'test-session-123'
      const mockError = new Error('Network Error')

      mockApiClient.get.mockRejectedValue(mockError)

      await expect(examService.getExamSession(sessionId)).rejects.toThrow('Network Error')
    })
  })

  describe('Legacy Compatibility', () => {
    it('legacy enum alias\'larının çalışması', () => {
      // Bu testler legacy uyumluluğu kontrol eder
      expect(ExamType.TYT).toBe('TYT')
      expect(ExamStatus.IN_PROGRESS).toBe('in_progress')
      expect(QuestionDifficulty.MEDIUM).toBe('MEDIUM')
    })
  })
})
