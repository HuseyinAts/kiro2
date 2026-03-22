/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * MSW (Mock Service Worker) Handlers
 * 
 * API endpoint'leri için mock handler'lar
 */

import { http, HttpResponse } from 'msw'

// Mock data
const mockUser = {
  id: '1',
  username: 'test-student',
  email: 'test@example.com',
  role: 'student',
  firstName: 'Test',
  lastName: 'Student',
  isActive: true,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z'
}

const mockExam = {
  id: '1',
  title: 'TYT Matematik Denemesi',
  type: 'TYT',
  subject: 'Matematik',
  duration: 165,
  questionCount: 40,
  status: 'active',
  createdAt: '2024-01-01T00:00:00Z'
}

const mockQuestions = [
  {
    id: '1',
    text: 'x + 2 = 5 ise x kaçtır?',
    options: ['1', '2', '3', '4'],
    correctAnswer: 2,
    subject: 'Matematik',
    difficulty: 'easy',
    explanation: 'x + 2 = 5 denkleminde x = 3 olur.'
  },
  {
    id: '2',
    text: 'Türkiye\'nin başkenti neresidir?',
    options: ['İstanbul', 'Ankara', 'İzmir', 'Bursa'],
    correctAnswer: 1,
    subject: 'Tarih',
    difficulty: 'easy',
    explanation: 'Türkiye\'nin başkenti Ankara\'dır.'
  }
]

const mockExamResults = {
  id: '1',
  examId: '1',
  userId: '1',
  score: 85,
  correctAnswers: 34,
  totalQuestions: 40,
  timeSpent: 120,
  completedAt: '2024-01-01T12:00:00Z',
  subjectScores: {
    'Matematik': { correct: 15, total: 20, percentage: 75 },
    'Geometri': { correct: 12, total: 15, percentage: 80 },
    'Fonksiyonlar': { correct: 7, total: 5, percentage: 140 }
  }
}

const mockLearningStyle = {
  id: '1',
  userId: '1',
  varkProfile: {
    visual: 0.8,
    auditory: 0.3,
    reading: 0.6,
    kinesthetic: 0.4
  },
  felderProfile: {
    activeReflective: 0.7,
    sensingIntuitive: 0.5,
    visualVerbal: 0.8,
    sequentialGlobal: 0.6
  },
  hybridCode: 'V-A-V-S',
  confidenceLevel: 0.85,
  recommendations: [
    'Görsel materyaller kullanın',
    'Diyagramlar ve şemalar tercih edin',
    'Aktif öğrenme yöntemlerini deneyin'
  ]
}

export const handlers = [
  // Auth endpoints
  http.post('/api/v1/auth/login', () => {
    return HttpResponse.json({
      success: true,
      data: {
        user: mockUser,
        token: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token'
      },
      message: 'Giriş başarılı'
    })
  }),

  http.post('/api/v1/auth/register', () => {
    return HttpResponse.json({
      success: true,
      data: {
        user: mockUser,
        token: 'mock-jwt-token',
        refreshToken: 'mock-refresh-token'
      },
      message: 'Kayıt başarılı'
    })
  }),

  http.post('/api/v1/auth/refresh', () => {
    return HttpResponse.json({
      success: true,
      data: {
        token: 'new-mock-jwt-token',
        refreshToken: 'new-mock-refresh-token'
      },
      message: 'Token yenilendi'
    })
  }),

  http.get('/api/v1/auth/me', () => {
    return HttpResponse.json({
      success: true,
      data: mockUser,
      message: 'Kullanıcı bilgileri alındı'
    })
  }),

  // Exam endpoints (matches backend: /api/v1/osym-exam/*)
  http.get('/api/v1/osym-exam/my-exams', () => {
    return HttpResponse.json({
      success: true,
      data: [mockExam],
      message: 'Sınavlar listelendi'
    })
  }),

  http.get('/api/v1/osym-exam/exam-configs', () => {
    return HttpResponse.json({
      success: true,
      data: { TYT: mockExam, AYT: mockExam },
      message: 'Sınav konfigürasyonları alındı'
    })
  }),

  http.post('/api/v1/osym-exam/create', () => {
    return HttpResponse.json({
      success: true,
      data: {
        session_id: 'mock-session-id',
        exam_type: 'TYT',
        status: 'not_started',
        questions: mockQuestions,
        total_questions: mockQuestions.length,
        duration_minutes: 165,
        created_at: new Date().toISOString()
      },
      message: 'Sınav oluşturuldu'
    })
  }),

  http.post('/api/v1/osym-exam/:sessionId/start', ({ params }) => {
    return HttpResponse.json({
      success: true,
      data: {
        session_id: params.sessionId,
        status: 'in_progress',
        start_time: new Date().toISOString(),
        duration_minutes: 165
      },
      message: 'Sınav başlatıldı'
    })
  }),

  http.post('/api/v1/osym-exam/:sessionId/save-answer', () => {
    return HttpResponse.json({
      success: true,
      message: 'Cevap kaydedildi',
      auto_saved: true
    })
  }),

  http.post('/api/v1/osym-exam/:sessionId/complete', () => {
    return HttpResponse.json({
      success: true,
      data: mockExamResults,
      message: 'Sınav tamamlandı'
    })
  }),

  http.post('/api/v1/osym-exam/:sessionId/navigate', () => {
    return HttpResponse.json({
      success: true,
      data: mockQuestions[0],
      message: 'Soruya gidildi'
    })
  }),

  http.get('/api/v1/osym-exam/:sessionId/remaining-time', () => {
    return HttpResponse.json({
      success: true,
      data: { remaining_seconds: 9900 },
      message: 'Kalan süre alındı'
    })
  }),

  // Learning Style endpoints
  http.get('/api/v1/learning-style/:userId', ({ params }) => {
    return HttpResponse.json({
      success: true,
      data: { ...mockLearningStyle, userId: params.userId },
      message: 'Öğrenme stili alındı'
    })
  }),

  http.post('/api/v1/learning-style/detect', () => {
    return HttpResponse.json({
      success: true,
      data: mockLearningStyle,
      message: 'Öğrenme stili tespit edildi'
    })
  }),

  // Revolutionary Features endpoints
  http.get('/api/v1/revolutionary-features/fsrs/:userId', ({ params }) => {
    return HttpResponse.json({
      success: true,
      data: {
        userId: params.userId,
        cards: [
          {
            id: '1',
            content: 'Matematik - Türev Kuralları',
            nextReview: '2024-01-02T10:00:00Z',
            interval: 1,
            easeFactor: 2.5,
            repetitions: 1
          }
        ],
        schedule: {
          today: 5,
          tomorrow: 3,
          thisWeek: 15
        }
      },
      message: 'FSRS verileri alındı'
    })
  }),

  http.post('/api/v1/revolutionary-features/bionic-reading', () => {
    return HttpResponse.json({
      success: true,
      data: {
        originalText: 'Bu bir örnek metindir.',
        bionicText: '**Bu** **bir** **ör**nek **me**tindir.'
      },
      message: 'Bionic Reading uygulandı'
    })
  }),

  http.get('/api/v1/revolutionary-features/multi-agent/status', () => {
    return HttpResponse.json({
      success: true,
      data: {
        agents: [
          { name: 'LearningPathAgent', status: 'active', lastUpdate: '2024-01-01T12:00:00Z' },
          { name: 'StudyBuddyAgent', status: 'active', lastUpdate: '2024-01-01T12:00:00Z' },
          { name: 'AccessibilityAgent', status: 'active', lastUpdate: '2024-01-01T12:00:00Z' }
        ],
        coordination: {
          activeConnections: 3,
          messagesSent: 150,
          messagesReceived: 148
        }
      },
      message: 'Multi-agent durumu alındı'
    })
  }),

  // Admin endpoints
  http.get('/api/v1/admin/users', () => {
    return HttpResponse.json({
      success: true,
      data: [mockUser],
      message: 'Kullanıcılar listelendi'
    })
  }),

  http.get('/api/v1/admin/dashboard/stats', () => {
    return HttpResponse.json({
      success: true,
      data: {
        totalUsers: 1250,
        activeUsers: 890,
        totalExams: 45,
        completedExams: 2340,
        averageScore: 78.5
      },
      message: 'Dashboard istatistikleri alındı'
    })
  }),

  // Teacher endpoints
  http.get('/api/v1/teacher/students', () => {
    return HttpResponse.json({
      success: true,
      data: [mockUser],
      message: 'Öğrenciler listelendi'
    })
  }),

  http.get('/api/v1/teacher/class-report', () => {
    return HttpResponse.json({
      success: true,
      data: {
        classId: '1',
        className: '12-A',
        studentCount: 25,
        averageScore: 82.3,
        subjectPerformance: {
          'Matematik': 78.5,
          'Fizik': 85.2,
          'Kimya': 80.1
        }
      },
      message: 'Sınıf raporu alındı'
    })
  }),

  // Chat endpoints
  http.post('/api/v1/chat/message', () => {
    return HttpResponse.json({
      success: true,
      data: {
        id: 'msg-1',
        content: 'Bu soruyu çözmek için önce denklemi düzenlememiz gerekiyor.',
        timestamp: new Date().toISOString(),
        sender: 'ai'
      },
      message: 'Mesaj gönderildi'
    })
  }),

  // Error scenarios
  http.get('/api/v1/error/500', () => {
    return HttpResponse.json(
      {
        success: false,
        message: 'Sunucu hatası',
        error: 'Internal Server Error'
      },
      { status: 500 }
    )
  }),

  http.get('/api/v1/error/404', () => {
    return HttpResponse.json(
      {
        success: false,
        message: 'Kaynak bulunamadı',
        error: 'Not Found'
      },
      { status: 404 }
    )
  }),

  http.get('/api/v1/error/401', () => {
    return HttpResponse.json(
      {
        success: false,
        message: 'Yetkisiz erişim',
        error: 'Unauthorized'
      },
      { status: 401 }
    )
  })
]