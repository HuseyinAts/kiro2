/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * ExamInterface Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render, createMockExam, createMockQuestion } from '../../utils/test-utils'
import { server, addHandler } from '../../mocks/server'
import { http, HttpResponse } from 'msw'
import ExamInterface from '../../../components/Exam/ExamInterface'

// Mock timer
vi.mock('react', async () => {
  const actual = await vi.importActual('react')
  return {
    ...actual,
    useEffect: vi.fn((fn, deps) => {
      if (deps && deps.length === 0) {
        fn()
      }
    })
  }
})

const mockExam = createMockExam({
  title: 'TYT Matematik Denemesi',
  duration: 165,
  questionCount: 40
})

const mockQuestions = [
  createMockQuestion({
    id: '1',
    text: 'x + 2 = 5 ise x kaçtır?',
    options: ['1', '2', '3', '4'],
    correctAnswer: 2
  }),
  createMockQuestion({
    id: '2',
    text: 'Türkiye\'nin başkenti neresidir?',
    options: ['İstanbul', 'Ankara', 'İzmir', 'Bursa'],
    correctAnswer: 1
  })
]

describe('ExamInterface', () => {
  const defaultProps = {
    exam: mockExam,
    questions: mockQuestions,
    onSubmitAnswer: vi.fn(),
    onCompleteExam: vi.fn(),
    sessionId: 'test-session-id'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    server.resetHandlers()
  })

  it('renders exam interface correctly', () => {
    render(<ExamInterface {...defaultProps} />)
    
    expect(screen.getByText('TYT Matematik Denemesi')).toBeInTheDocument()
    expect(screen.getByText(/soru 1 \/ 2/i)).toBeInTheDocument()
    expect(screen.getByText('x + 2 = 5 ise x kaçtır?')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('displays timer correctly', () => {
    render(<ExamInterface {...defaultProps} />)
    
    // Timer should show remaining time
    expect(screen.getByText(/kalan süre/i)).toBeInTheDocument()
    expect(screen.getByText(/165:00/)).toBeInTheDocument()
  })

  it('allows selecting an answer', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    expect(option3).toBeChecked()
  })

  it('submits answer when next button is clicked', async () => {
    const user = userEvent.setup()
    const mockSubmitAnswer = vi.fn()
    
    render(<ExamInterface {...defaultProps} onSubmitAnswer={mockSubmitAnswer} />)
    
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    expect(mockSubmitAnswer).toHaveBeenCalledWith({
      questionId: '1',
      selectedAnswer: 2,
      timeSpent: expect.any(Number)
    })
  })

  it('navigates to next question after submitting answer', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    // First question
    expect(screen.getByText('x + 2 = 5 ise x kaçtır?')).toBeInTheDocument()
    
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    // Should show second question
    await waitFor(() => {
      expect(screen.getByText('Türkiye\'nin başkenti neresidir?')).toBeInTheDocument()
      expect(screen.getByText(/soru 2 \/ 2/i)).toBeInTheDocument()
    })
  })

  it('navigates to previous question', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    // Go to second question first
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    // Now go back
    const prevButton = screen.getByRole('button', { name: /önceki/i })
    await user.click(prevButton)
    
    await waitFor(() => {
      expect(screen.getByText('x + 2 = 5 ise x kaçtır?')).toBeInTheDocument()
      expect(screen.getByText(/soru 1 \/ 2/i)).toBeInTheDocument()
    })
  })

  it('shows complete exam button on last question', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    // Navigate to last question
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    // Should show complete exam button
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sınavı tamamla/i })).toBeInTheDocument()
    })
  })

  it('completes exam when complete button is clicked', async () => {
    const user = userEvent.setup()
    const mockCompleteExam = vi.fn()
    
    render(<ExamInterface {...defaultProps} onCompleteExam={mockCompleteExam} />)
    
    // Navigate to last question
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    // Answer last question
    const option2 = screen.getByLabelText('Ankara')
    await user.click(option2)
    
    const completeButton = screen.getByRole('button', { name: /sınavı tamamla/i })
    await user.click(completeButton)
    
    expect(mockCompleteExam).toHaveBeenCalled()
  })

  it('shows confirmation dialog before completing exam', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    // Navigate to last question
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    const completeButton = screen.getByRole('button', { name: /sınavı tamamla/i })
    await user.click(completeButton)
    
    expect(screen.getByText(/sınavı tamamlamak istediğinizden emin misiniz/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /evet, tamamla/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iptal/i })).toBeInTheDocument()
  })

  it('marks questions for review', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    const markButton = screen.getByRole('button', { name: /işaretle/i })
    await user.click(markButton)
    
    expect(markButton).toHaveClass('marked') // Assuming marked class is applied
  })

  it('shows question navigation panel', () => {
    render(<ExamInterface {...defaultProps} />)
    
    expect(screen.getByText(/soru navigasyonu/i)).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('allows direct navigation to questions via navigation panel', async () => {
    const user = userEvent.setup()
    render(<ExamInterface {...defaultProps} />)
    
    const question2Button = screen.getByRole('button', { name: '2' })
    await user.click(question2Button)
    
    await waitFor(() => {
      expect(screen.getByText('Türkiye\'nin başkenti neresidir?')).toBeInTheDocument()
      expect(screen.getByText(/soru 2 \/ 2/i)).toBeInTheDocument()
    })
  })

  it('shows warning when time is running low', () => {
    const propsWithLowTime = {
      ...defaultProps,
      remainingTime: 300 // 5 minutes
    }
    
    render(<ExamInterface {...propsWithLowTime} />)
    
    expect(screen.getByText(/süre azalıyor/i)).toBeInTheDocument()
  })

  it('auto-submits exam when time runs out', async () => {
    const mockCompleteExam = vi.fn()
    const propsWithNoTime = {
      ...defaultProps,
      remainingTime: 0,
      onCompleteExam: mockCompleteExam
    }
    
    render(<ExamInterface {...propsWithNoTime} />)
    
    await waitFor(() => {
      expect(mockCompleteExam).toHaveBeenCalled()
    })
  })

  it('saves answers automatically', async () => {
    const user = userEvent.setup()
    const mockSubmitAnswer = vi.fn()
    
    render(<ExamInterface {...defaultProps} onSubmitAnswer={mockSubmitAnswer} />)
    
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    // Auto-save should trigger after a delay
    await waitFor(() => {
      expect(mockSubmitAnswer).toHaveBeenCalled()
    }, { timeout: 3000 })
  })

  it('handles keyboard shortcuts', async () => {
    render(<ExamInterface {...defaultProps} />)
    
    // Test number key shortcuts for options
    fireEvent.keyDown(document, { key: '3' })
    
    const option3 = screen.getByLabelText('3')
    expect(option3).toBeChecked()
  })

  it('shows progress indicator', () => {
    render(<ExamInterface {...defaultProps} />)
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
    expect(screen.getByText(/50%/)).toBeInTheDocument() // 1 of 2 questions
  })

  it('handles network errors gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock network error for answer submission
    addHandler(
      http.post('/api/v1/exams/sessions/:sessionId/answer', () => {
        return HttpResponse.error()
      })
    )
    
    render(<ExamInterface {...defaultProps} />)
    
    const option3 = screen.getByLabelText('3')
    await user.click(option3)
    
    const nextButton = screen.getByRole('button', { name: /sonraki/i })
    await user.click(nextButton)
    
    await waitFor(() => {
      expect(screen.getByText(/cevap kaydedilemedi/i)).toBeInTheDocument()
    })
  })

  it('supports accessibility features', () => {
    render(<ExamInterface {...defaultProps} />)
    
    // Check ARIA labels
    expect(screen.getByRole('main')).toHaveAttribute('aria-label', 'Sınav Arayüzü')
    expect(screen.getByRole('timer')).toHaveAttribute('aria-live', 'polite')
    
    // Check keyboard navigation
    const firstOption = screen.getByLabelText('1')
    expect(firstOption).toHaveAttribute('tabindex', '0')
  })
})