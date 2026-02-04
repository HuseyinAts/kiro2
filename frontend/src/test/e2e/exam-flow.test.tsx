/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * End-to-End Exam Flow Tests
 * 
 * Bu dosya sınav akışının tamamını test eder:
 * 1. Kullanıcı girişi
 * 2. Sınav seçimi
 * 3. Sınav başlatma
 * 4. Soru çözme
 * 5. Sınav tamamlama
 * 6. Sonuçları görüntüleme
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render, createMockUser, createMockExam, createMockQuestion } from '../utils/test-utils'
import { server, addHandler } from '../mocks/server'
import { http, HttpResponse } from 'msw'
import App from '../../app'

// Mock navigation
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    BrowserRouter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
  }
})

const mockUser = createMockUser({
  role: 'student',
  firstName: 'Test',
  lastName: 'Student'
})

const mockExam = createMockExam({
  id: 'exam-1',
  title: 'TYT Matematik Denemesi',
  type: 'TYT',
  subject: 'Matematik',
  duration: 165,
  questionCount: 3 // Reduced for testing
})

const mockQuestions = [
  createMockQuestion({
    id: 'q1',
    text: 'x + 2 = 5 ise x kaçtır?',
    options: ['1', '2', '3', '4'],
    correctAnswer: 2,
    subject: 'Matematik'
  }),
  createMockQuestion({
    id: 'q2',
    text: '2 × 3 = ?',
    options: ['4', '5', '6', '7'],
    correctAnswer: 2,
    subject: 'Matematik'
  }),
  createMockQuestion({
    id: 'q3',
    text: '10 ÷ 2 = ?',
    options: ['3', '4', '5', '6'],
    correctAnswer: 2,
    subject: 'Matematik'
  })
]

const mockExamResult = {
  id: 'result-1',
  examId: 'exam-1',
  userId: mockUser.id,
  score: 85,
  correctAnswers: 2,
  totalQuestions: 3,
  timeSpent: 120,
  completedAt: '2024-01-01T12:00:00Z',
  subjectScores: {
    'Matematik': { correct: 2, total: 3, percentage: 67 }
  },
  detailedResults: [
    { questionId: 'q1', selectedAnswer: 2, correctAnswer: 2, isCorrect: true, timeSpent: 30 },
    { questionId: 'q2', selectedAnswer: 2, correctAnswer: 2, isCorrect: true, timeSpent: 45 },
    { questionId: 'q3', selectedAnswer: 1, correctAnswer: 2, isCorrect: false, timeSpent: 45 }
  ]
}

describe('Complete Exam Flow E2E Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    server.resetHandlers()
    
    // Setup default API responses
    setupDefaultAPIResponses()
  })

  const setupDefaultAPIResponses = () => {
    // Auth responses
    addHandler(
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
      })
    )

    addHandler(
      http.get('/api/v1/auth/me', () => {
        return HttpResponse.json({
          success: true,
          data: mockUser,
          message: 'Kullanıcı bilgileri alındı'
        })
      })
    )

    // Exam list
    addHandler(
      http.get('/api/v1/exams', () => {
        return HttpResponse.json({
          success: true,
          data: [mockExam],
          message: 'Sınavlar listelendi'
        })
      })
    )

    // Exam start
    addHandler(
      http.post('/api/v1/exams/:examId/start', () => {
        return HttpResponse.json({
          success: true,
          data: {
            sessionId: 'session-1',
            examId: mockExam.id,
            questions: mockQuestions,
            startTime: new Date().toISOString(),
            duration: mockExam.duration
          },
          message: 'Sınav başlatıldı'
        })
      })
    )

    // Answer submission
    addHandler(
      http.post('/api/v1/exams/sessions/:sessionId/answer', () => {
        return HttpResponse.json({
          success: true,
          data: { saved: true },
          message: 'Cevap kaydedildi'
        })
      })
    )

    // Exam completion
    addHandler(
      http.post('/api/v1/exams/sessions/:sessionId/submit', () => {
        return HttpResponse.json({
          success: true,
          data: mockExamResult,
          message: 'Sınav tamamlandı'
        })
      })
    )

    // Exam results
    addHandler(
      http.get('/api/v1/exams/results/:resultId', () => {
        return HttpResponse.json({
          success: true,
          data: mockExamResult,
          message: 'Sınav sonuçları alındı'
        })
      })
    )
  }

  it('completes full exam flow successfully', async () => {
    const user = userEvent.setup()
    
    // Render the app
    render(<App />)

    // Step 1: User Login
    await waitFor(() => {
      expect(screen.getByText(/giriş yap/i)).toBeInTheDocument()
    })

    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const loginButton = screen.getByRole('button', { name: /giriş yap/i })

    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(loginButton)

    // Step 2: Navigate to Exams
    await waitFor(() => {
      expect(screen.getByText(/hoş geldiniz/i)).toBeInTheDocument()
    })

    const examsLink = screen.getByRole('link', { name: /sınavlar/i })
    await user.click(examsLink)

    // Step 3: Select Exam
    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Denemesi')).toBeInTheDocument()
    })

    const startExamButton = screen.getByRole('button', { name: /sınava başla/i })
    await user.click(startExamButton)

    // Step 4: Confirm Exam Start
    await waitFor(() => {
      expect(screen.getByText(/sınava başlamak istediğinizden emin misiniz/i)).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: /evet, başla/i })
    await user.click(confirmButton)

    // Step 5: Answer Questions
    await waitFor(() => {
      expect(screen.getByText('x + 2 = 5 ise x kaçtır?')).toBeInTheDocument()
      expect(screen.getByText(/soru 1 \/ 3/i)).toBeInTheDocument()
    })

    // Answer Question 1
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)

    // Answer Question 2
    await waitFor(() => {
      expect(screen.getByText('2 × 3 = ?')).toBeInTheDocument()
      expect(screen.getByText(/soru 2 \/ 3/i)).toBeInTheDocument()
    })

    const option6 = screen.getByLabelText('6')
    await user.click(option6)
    await user.click(nextButton)

    // Answer Question 3
    await waitFor(() => {
      expect(screen.getByText('10 ÷ 2 = ?')).toBeInTheDocument()
      expect(screen.getByText(/soru 3 \/ 3/i)).toBeInTheDocument()
    })

    const option4 = screen.getByLabelText('4')
    await user.click(option4)

    // Step 6: Complete Exam
    const completeButton = screen.getByRole('button', { name: /sınavı tamamla/i })
    await user.click(completeButton)

    // Confirm completion
    await waitFor(() => {
      expect(screen.getByText(/sınavı tamamlamak istediğinizden emin misiniz/i)).toBeInTheDocument()
    })

    const confirmCompleteButton = screen.getByRole('button', { name: /evet, tamamla/i })
    await user.click(confirmCompleteButton)

    // Step 7: View Results
    await waitFor(() => {
      expect(screen.getByText(/sınav tamamlandı/i)).toBeInTheDocument()
      expect(screen.getByText(/puanınız: 85/i)).toBeInTheDocument()
      expect(screen.getByText(/doğru cevap: 2 \/ 3/i)).toBeInTheDocument()
    })

    // Check detailed results
    expect(screen.getByText(/matematik: %67/i)).toBeInTheDocument()
    
    // View detailed analysis
    const detailsButton = screen.getByRole('button', { name: /detaylı analiz/i })
    await user.click(detailsButton)

    await waitFor(() => {
      expect(screen.getByText(/soru bazlı analiz/i)).toBeInTheDocument()
      expect(screen.getByText(/doğru/i)).toBeInTheDocument() // For correct answers
      expect(screen.getByText(/yanlış/i)).toBeInTheDocument() // For incorrect answers
    })
  })

  it('handles exam timeout scenario', async () => {
    const user = userEvent.setup()
    
    // Mock exam with very short duration
    const shortExam = { ...mockExam, duration: 1 } // 1 minute
    
    addHandler(
      http.get('/api/v1/exams', () => {
        return HttpResponse.json({
          success: true,
          data: [shortExam]
        })
      })
    )

    addHandler(
      http.post('/api/v1/exams/:examId/start', () => {
        return HttpResponse.json({
          success: true,
          data: {
            sessionId: 'session-1',
            examId: shortExam.id,
            questions: mockQuestions,
            startTime: new Date().toISOString(),
            duration: 1,
            remainingTime: 60 // 60 seconds
          }
        })
      })
    )

    render(<App />)

    // Login and start exam
    await loginAndStartExam(user)

    // Wait for timeout warning
    await waitFor(() => {
      expect(screen.getByText(/süre azalıyor/i)).toBeInTheDocument()
    }, { timeout: 5000 })

    // Wait for auto-submit
    await waitFor(() => {
      expect(screen.getByText(/süre doldu/i)).toBeInTheDocument()
      expect(screen.getByText(/sınav otomatik olarak tamamlandı/i)).toBeInTheDocument()
    }, { timeout: 10000 })
  })

  it('handles network interruption during exam', async () => {
    const user = userEvent.setup()
    
    render(<App />)
    await loginAndStartExam(user)

    // Answer first question
    const option3 = screen.getByLabelText('3')
    await user.click(option3)

    // Mock network error for answer submission
    addHandler(
      http.post('/api/v1/exams/sessions/:sessionId/answer', () => {
        return HttpResponse.error()
      })
    )

    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/bağlantı hatası/i)).toBeInTheDocument()
      expect(screen.getByText(/cevabınız kaydedilemedi/i)).toBeInTheDocument()
    })

    // Should show retry option
    const retryButton = screen.getByRole('button', { name: /tekrar dene/i })
    expect(retryButton).toBeInTheDocument()

    // Fix network and retry
    addHandler(
      http.post('/api/v1/exams/sessions/:sessionId/answer', () => {
        return HttpResponse.json({
          success: true,
          data: { saved: true }
        })
      })
    )

    await user.click(retryButton)

    await waitFor(() => {
      expect(screen.getByText('2 × 3 = ?')).toBeInTheDocument() // Should proceed to next question
    })
  })

  it('handles exam resume after browser refresh', async () => {
    const user = userEvent.setup()
    
    // Mock ongoing session
    addHandler(
      http.get('/api/v1/exams/sessions/current', () => {
        return HttpResponse.json({
          success: true,
          data: {
            sessionId: 'session-1',
            examId: mockExam.id,
            currentQuestionIndex: 1,
            answers: [{ questionId: 'q1', selectedAnswer: 2 }],
            remainingTime: 7200, // 2 hours
            status: 'active'
          }
        })
      })
    )

    render(<App />)
    
    // Should detect ongoing session and show resume option
    await waitFor(() => {
      expect(screen.getByText(/devam eden sınavınız var/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sınava devam et/i })).toBeInTheDocument()
    })

    const resumeButton = screen.getByRole('button', { name: /sınava devam et/i })
    await user.click(resumeButton)

    // Should resume from question 2
    await waitFor(() => {
      expect(screen.getByText('2 × 3 = ?')).toBeInTheDocument()
      expect(screen.getByText(/soru 2 \/ 3/i)).toBeInTheDocument()
    })
  })

  it('handles accessibility features during exam', async () => {
    const user = userEvent.setup()
    
    render(<App />)
    await loginAndStartExam(user)

    // Test keyboard navigation
    const option1 = screen.getByLabelText('1')
    const option2 = screen.getByLabelText('2')
    
    // Use arrow keys to navigate options
    option1.focus()
    fireEvent.keyDown(option1, { key: 'ArrowDown' })
    expect(option2).toHaveFocus()

    // Use space to select
    fireEvent.keyDown(option2, { key: ' ' })
    expect(option2).toBeChecked()

    // Test screen reader announcements
    expect(screen.getByRole('status')).toHaveTextContent(/soru 1 \/ 3/i)
    
    // Test high contrast mode
    const highContrastButton = screen.getByRole('button', { name: /yüksek kontrast/i })
    await user.click(highContrastButton)
    
    expect(document.body).toHaveClass('high-contrast')
  })

  // Helper function for common login and exam start flow
  const loginAndStartExam = async (user: any) => {
    // Login
    await waitFor(() => {
      expect(screen.getByText(/giriş yap/i)).toBeInTheDocument()
    })

    const usernameInput = screen.getByLabelText(/kullanıcı adı/i)
    const passwordInput = screen.getByLabelText(/şifre/i)
    const loginButton = screen.getByRole('button', { name: /giriş yap/i })

    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'SecurePass123!')
    await user.click(loginButton)

    // Navigate to exams
    await waitFor(() => {
      expect(screen.getByText(/hoş geldiniz/i)).toBeInTheDocument()
    })

    const examsLink = screen.getByRole('link', { name: /sınavlar/i })
    await user.click(examsLink)

    // Start exam
    await waitFor(() => {
      expect(screen.getByText('TYT Matematik Denemesi')).toBeInTheDocument()
    })

    const startExamButton = screen.getByRole('button', { name: /sınava başla/i })
    await user.click(startExamButton)

    const confirmButton = screen.getByRole('button', { name: /evet, başla/i })
    await user.click(confirmButton)

    // Wait for exam interface
    await waitFor(() => {
      expect(screen.getByText('x + 2 = 5 ise x kaçtır?')).toBeInTheDocument()
    })
  }
})