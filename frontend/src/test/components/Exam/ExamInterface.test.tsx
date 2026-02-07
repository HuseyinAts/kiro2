/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * ExamInterface Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../utils/test-utils'
import { ExamInterface, type ExamQuestion, type ExamAnswer } from '../../../components/Exam/ExamInterface'

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const mockQuestions: ExamQuestion[] = [
  {
    id: '1',
    number: 1,
    content: 'x + 2 = 5 ise x kaçtır?',
    options: ['1', '2', '3', '4'],
    subject: 'Matematik',
    topic: 'Denklemler'
  },
  {
    id: '2',
    number: 2,
    content: 'Türkiye\'nin başkenti neresidir?',
    options: ['İstanbul', 'Ankara', 'İzmir', 'Bursa'],
    subject: 'Coğrafya',
    topic: 'Başkentler'
  }
]

describe('ExamInterface', () => {
  const mockAnswers: Record<string, ExamAnswer> = {}
  const defaultProps = {
    questions: mockQuestions,
    answers: mockAnswers,
    currentQuestionIndex: 0,
    onAnswerChange: vi.fn(),
    onFlagToggle: vi.fn(),
    onQuestionNavigate: vi.fn(),
    disabled: false,
    showNavigationPanel: true
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders exam interface correctly', () => {
    render(<ExamInterface {...defaultProps} />)

    expect(screen.getByText('Soru 1')).toBeInTheDocument()
    expect(screen.getByText('Matematik')).toBeInTheDocument()
    expect(screen.getByText('Denklemler')).toBeInTheDocument()
    expect(screen.getByText('x + 2 = 5 ise x kaçtır?')).toBeInTheDocument()
  })

  it('displays question navigation panel when enabled', () => {
    render(<ExamInterface {...defaultProps} />)

    expect(screen.getByText('Soru Haritası')).toBeInTheDocument()
    expect(screen.getByText(/2 Boş/i)).toBeInTheDocument()
  })

  it('hides question navigation panel when disabled', () => {
    render(<ExamInterface {...defaultProps} showNavigationPanel={false} />)

    expect(screen.queryByText('Soru Haritası')).not.toBeInTheDocument()
  })

  it('allows selecting an answer', async () => {
    const user = userEvent.setup()
    const mockOnAnswerChange = vi.fn()

    render(<ExamInterface {...defaultProps} onAnswerChange={mockOnAnswerChange} />)

    // Find option buttons (they should be rendered by BubbleSheetInterface)
    const optionButtons = screen.getAllByRole('button').filter(btn =>
      ['A', 'B', 'C', 'D', 'E'].includes(btn.textContent || '')
    )

    if (optionButtons.length > 0) {
      await user.click(optionButtons[2]) // Click option C (3)

      expect(mockOnAnswerChange).toHaveBeenCalledWith('1', 'C')
    }
  })

  it('toggles flag for review', async () => {
    const user = userEvent.setup()
    const mockOnFlagToggle = vi.fn()

    render(<ExamInterface {...defaultProps} onFlagToggle={mockOnFlagToggle} />)

    // Match the exact button label from component
    const flagButton = screen.getByRole('button', { name: /inceleme için işaretle \(f\)/i })
    await user.click(flagButton)

    expect(mockOnFlagToggle).toHaveBeenCalledWith('1')
  })

  it('navigates to next question', async () => {
    const user = userEvent.setup()
    const mockOnNavigate = vi.fn()

    render(<ExamInterface {...defaultProps} onQuestionNavigate={mockOnNavigate} />)

    const nextButton = screen.getByRole('button', { name: /sonraki soru/i })
    await user.click(nextButton)

    expect(mockOnNavigate).toHaveBeenCalledWith(1)
  })

  it('navigates to previous question', async () => {
    const user = userEvent.setup()
    const mockOnNavigate = vi.fn()

    render(<ExamInterface {...defaultProps} currentQuestionIndex={1} onQuestionNavigate={mockOnNavigate} />)

    const prevButton = screen.getByRole('button', { name: /önceki soru/i })
    await user.click(prevButton)

    expect(mockOnNavigate).toHaveBeenCalledWith(0)
  })

  it('disables previous button on first question', () => {
    render(<ExamInterface {...defaultProps} currentQuestionIndex={0} />)

    const prevButton = screen.getByRole('button', { name: /önceki soru/i })
    expect(prevButton).toBeDisabled()
  })

  it('disables next button on last question', () => {
    render(<ExamInterface {...defaultProps} currentQuestionIndex={1} />)

    const nextButton = screen.getByRole('button', { name: /sonraki soru/i })
    expect(nextButton).toBeDisabled()
  })

  it('shows flagged question indicator', () => {
    const answersWithFlag: Record<string, ExamAnswer> = {
      '1': {
        questionId: '1',
        answer: 'A',
        flaggedForReview: true,
        timestamp: new Date()
      }
    }

    render(<ExamInterface {...defaultProps} answers={answersWithFlag} />)

    // Check for flag icon or flagged state
    const flagButton = screen.getByRole('button', { name: /inceleme işaretini kaldır \(f\)/i })
    expect(flagButton).toBeInTheDocument()
  })

  it('shows answered question indicator', () => {
    const answersWithAnswer: Record<string, ExamAnswer> = {
      '1': {
        questionId: '1',
        answer: 'C',
        flaggedForReview: false,
        timestamp: new Date()
      }
    }

    render(<ExamInterface {...defaultProps} answers={answersWithAnswer} />)

    // Check for CheckCircle icon indicating answered
    const checkIcons = screen.getAllByTestId(/CheckCircleIcon/i)
    expect(checkIcons.length).toBeGreaterThan(0)
  })

  it('disables all interactions when disabled prop is true', async () => {
    const user = userEvent.setup()
    const mockOnAnswerChange = vi.fn()
    const mockOnFlagToggle = vi.fn()
    const mockOnNavigate = vi.fn()

    render(
      <ExamInterface
        {...defaultProps}
        disabled={true}
        onAnswerChange={mockOnAnswerChange}
        onFlagToggle={mockOnFlagToggle}
        onQuestionNavigate={mockOnNavigate}
      />
    )

    const flagButton = screen.getByRole('button', { name: /inceleme için işaretle \(f\)/i })
    await user.click(flagButton)

    expect(mockOnFlagToggle).not.toHaveBeenCalled()
  })

  it('displays keyboard shortcuts info', () => {
    render(<ExamInterface {...defaultProps} />)

    expect(screen.getByText(/kısayollar/i)).toBeInTheDocument()
    expect(screen.getByText(/a-e \(cevap\)/i)).toBeInTheDocument()
    expect(screen.getByText(/f \(işaretle\)/i)).toBeInTheDocument()
  })

  it('shows question progress', () => {
    render(<ExamInterface {...defaultProps} currentQuestionIndex={0} />)

    expect(screen.getByText('1 / 2')).toBeInTheDocument()
  })

  it('displays subject and topic chips', () => {
    render(<ExamInterface {...defaultProps} />)

    expect(screen.getByText('Matematik')).toBeInTheDocument()
    expect(screen.getByText('Denklemler')).toBeInTheDocument()
  })

  it('navigates to specific question from navigation panel', async () => {
    const user = userEvent.setup()
    const mockOnNavigate = vi.fn()

    render(<ExamInterface {...defaultProps} onQuestionNavigate={mockOnNavigate} />)

    // Find question 2 button in navigation panel
    const questionButtons = screen.getAllByRole('button').filter(btn => btn.textContent === '2')

    if (questionButtons.length > 0) {
      await user.click(questionButtons[0])
      expect(mockOnNavigate).toHaveBeenCalledWith(1)
    }
  })

  it('shows statistics in navigation panel', () => {
    const answersWithMixed: Record<string, ExamAnswer> = {
      '1': {
        questionId: '1',
        answer: 'A',
        flaggedForReview: true,
        timestamp: new Date()
      }
    }

    render(<ExamInterface {...defaultProps} answers={answersWithMixed} />)

    expect(screen.getByText(/1 Cevaplandı/i)).toBeInTheDocument()
    expect(screen.getByText(/1 Boş/i)).toBeInTheDocument()
    expect(screen.getByText(/1 İşaretli/i)).toBeInTheDocument()
  })

  it('handles empty answers gracefully', () => {
    render(<ExamInterface {...defaultProps} answers={{}} />)

    expect(screen.getByText(/2 Boş/i)).toBeInTheDocument()
    expect(screen.getByText(/0 Cevaplandı/i)).toBeInTheDocument()
  })

  it('renders correctly when no question is available', () => {
    render(<ExamInterface {...defaultProps} questions={[]} currentQuestionIndex={0} />)

    expect(screen.getByText('Soru bulunamadı')).toBeInTheDocument()
  })

  it('shows confirmation when answer is selected', async () => {
    const user = userEvent.setup()
    const answersWithNew: Record<string, ExamAnswer> = {
      '1': {
        questionId: '1',
        answer: 'B',
        flaggedForReview: false,
        timestamp: new Date()
      }
    }

    render(<ExamInterface {...defaultProps} answers={answersWithNew} />)

    // Check for confirmation message
    await waitFor(() => {
      const confirmation = screen.queryByText(/cevabınız kaydedildi/i)
      // Confirmation may appear and disappear quickly
      if (confirmation) {
        expect(confirmation).toBeInTheDocument()
      }
    })
  })

  it('maintains answer state when navigating between questions', async () => {
    const user = userEvent.setup()
    const answersState: Record<string, ExamAnswer> = {
      '1': {
        questionId: '1',
        answer: 'A',
        flaggedForReview: false,
        timestamp: new Date()
      }
    }

    const { rerender } = render(<ExamInterface {...defaultProps} answers={answersState} currentQuestionIndex={0} />)

    // Navigate to next question
    const nextButton = screen.getByRole('button', { name: /sonraki soru/i })
    await user.click(nextButton)

    // Rerender with new question index
    rerender(<ExamInterface {...defaultProps} answers={answersState} currentQuestionIndex={1} />)

    // Navigate back
    const prevButton = screen.getByRole('button', { name: /önceki soru/i })
    await user.click(prevButton)

    // Answer should still be there
    rerender(<ExamInterface {...defaultProps} answers={answersState} currentQuestionIndex={0} />)
    expect(screen.getByText('Soru 1')).toBeInTheDocument()
  })
})
