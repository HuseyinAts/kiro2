/**
 * ExamInterface Component Tests
 * Comprehensive test suite for exam interface functionality
 */

import * as React from 'react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../../../test/utils/test-utils'
import { ExamInterface, ExamQuestion, ExamAnswer } from '../ExamInterface'

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>
  },
  AnimatePresence: ({ children }: any) => <>{children}</>
}))

// Mock BubbleSheetInterface
vi.mock('../BubbleSheetInterface', () => ({
  default: ({ questionNumber, options, selectedAnswer, onAnswerSelect, disabled }: any) => (
    <div data-testid="bubble-sheet">
      <span data-testid="question-number">{questionNumber}</span>
      {options.map((option: string, index: number) => (
        <button
          key={index}
          data-testid={`option-${option}`}
          onClick={() => onAnswerSelect(option)}
          disabled={disabled}
          aria-pressed={selectedAnswer === option}
        >
          {option}
        </button>
      ))}
    </div>
  )
}))

// Mock MUI theme
vi.mock('@mui/material/styles', async () => {
  const actual = await vi.importActual('@mui/material/styles')
  return {
    ...actual,
    useTheme: () => ({
      palette: {
        primary: { main: '#1976d2' },
        success: { main: '#4caf50' },
        warning: { main: '#ff9800' },
        error: { main: '#f44336' },
        info: { main: '#2196f3' },
        grey: { 400: '#bdbdbd' },
        text: { primary: '#000', secondary: '#666' }
      },
      shadows: ['none', '0 1px 3px rgba(0,0,0,0.12)']
    }),
    alpha: (color: string, value: number) => color
  }
})

describe('ExamInterface', () => {
  const mockQuestions: ExamQuestion[] = [
    {
      id: 'q1',
      number: 1,
      content: 'Birinci sorunun icerigi nedir?',
      options: ['A', 'B', 'C', 'D', 'E'],
      subject: 'Matematik',
      topic: 'Denklemler'
    },
    {
      id: 'q2',
      number: 2,
      content: 'Ikinci sorunun icerigi nedir?',
      options: ['A', 'B', 'C', 'D', 'E'],
      subject: 'Matematik',
      topic: 'Fonksiyonlar'
    },
    {
      id: 'q3',
      number: 3,
      content: 'Ucuncu sorunun icerigi nedir?',
      options: ['A', 'B', 'C', 'D', 'E'],
      subject: 'Fizik',
      topic: 'Kuvvet'
    }
  ]

  const mockAnswers: Record<string, ExamAnswer> = {
    q1: {
      questionId: 'q1',
      answer: 'A',
      flaggedForReview: false,
      timestamp: new Date()
    }
  }

  const mockOnAnswerChange = vi.fn()
  const mockOnFlagToggle = vi.fn()
  const mockOnQuestionNavigate = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders current question content', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      expect(screen.getByText('Soru 1')).toBeInTheDocument()
      expect(screen.getByText('Birinci sorunun icerigi nedir?')).toBeInTheDocument()
    })

    it('displays subject and topic chips', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      expect(screen.getByText('Matematik')).toBeInTheDocument()
      expect(screen.getByText('Denklemler')).toBeInTheDocument()
    })

    it('shows navigation panel by default', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          showNavigationPanel={true}
        />
      )

      expect(screen.getByText('Soru Haritası')).toBeInTheDocument()
    })

    it('hides navigation panel when showNavigationPanel is false', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          showNavigationPanel={false}
        />
      )

      expect(screen.queryByText('Soru Haritası')).not.toBeInTheDocument()
    })

    it('displays progress indicator', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      expect(screen.getByText('1 / 3')).toBeInTheDocument()
    })

    it('shows description info', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      expect(screen.getByText(/Aktif soru/)).toBeInTheDocument()
    })
  })

  describe('Answer Selection', () => {
    it('calls onAnswerChange when answer is selected', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={{}}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      const optionB = screen.getByTestId('option-B')
      await user.click(optionB)

      expect(mockOnAnswerChange).toHaveBeenCalledWith('q1', 'B')
    })

    it('does not call onAnswerChange when disabled', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={{}}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          disabled={true}
        />
      )

      const optionB = screen.getByTestId('option-B')
      await user.click(optionB)

      expect(mockOnAnswerChange).not.toHaveBeenCalled()
    })

    it('shows answered status when question has answer', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      // Check for "Cevaplandi" tooltip indicator
      const statusIndicators = screen.getAllByTestId('CheckCircleIcon')
      expect(statusIndicators.length).toBeGreaterThan(0)
    })
  })

  describe('Flag Toggle', () => {
    it('calls onFlagToggle when flag button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      const flagButton = screen.getByRole('button', { name: /İnceleme için işaretle/i })
      await user.click(flagButton)

      expect(mockOnFlagToggle).toHaveBeenCalledWith('q1')
    })

    it('shows flagged status when question is flagged', () => {
      const flaggedAnswers: Record<string, ExamAnswer> = {
        q1: {
          questionId: 'q1',
          answer: 'A',
          flaggedForReview: true,
          timestamp: new Date()
        }
      }

      render(
        <ExamInterface
          questions={mockQuestions}
          answers={flaggedAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      // Flag icon should be filled
      const flagIcons = screen.getAllByTestId('FlagIcon')
      expect(flagIcons.length).toBeGreaterThan(0)
    })

    it('does not call onFlagToggle when disabled', async () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          disabled={true}
        />
      )

      const flagButton = screen.getByRole('button', { name: /İnceleme için işaretle/i })
      expect(flagButton).toBeDisabled()
    })
  })

  describe('Navigation', () => {
    it('navigates to previous question when Previous button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={1}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      const prevButton = screen.getByRole('button', { name: /Önceki Soru/i })
      await user.click(prevButton)

      expect(mockOnQuestionNavigate).toHaveBeenCalledWith(0)
    })

    it('navigates to next question when Next button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      const nextButton = screen.getByRole('button', { name: /Sonraki Soru/i })
      await user.click(nextButton)

      expect(mockOnQuestionNavigate).toHaveBeenCalledWith(1)
    })

    it('disables Previous button on first question', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      const prevButton = screen.getByRole('button', { name: /Önceki Soru/i })
      expect(prevButton).toBeDisabled()
    })

    it('disables Next button on last question', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={2}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      const nextButton = screen.getByRole('button', { name: /Sonraki Soru/i })
      expect(nextButton).toBeDisabled()
    })

    it('disables navigation buttons when disabled prop is true', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={1}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          disabled={true}
        />
      )

      const prevButton = screen.getByRole('button', { name: /Önceki Soru/i })
      const nextButton = screen.getByRole('button', { name: /Sonraki Soru/i })

      expect(prevButton).toBeDisabled()
      expect(nextButton).toBeDisabled()
    })
  })

  describe('Keyboard Shortcuts', () => {
    it('navigates to previous question with ArrowLeft key', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={1}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      await user.keyboard('{ArrowLeft}')

      expect(mockOnQuestionNavigate).toHaveBeenCalledWith(0)
    })

    it('navigates to next question with ArrowRight key', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      await user.keyboard('{ArrowRight}')

      expect(mockOnQuestionNavigate).toHaveBeenCalledWith(1)
    })

    it('toggles flag with F key', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      await user.keyboard('f')

      expect(mockOnFlagToggle).toHaveBeenCalledWith('q1')
    })

    it('selects answer with A-E keys', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={{}}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      await user.keyboard('c')

      expect(mockOnAnswerChange).toHaveBeenCalledWith('q1', 'C')
    })

    it('does not respond to keyboard when disabled', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={{}}
          currentQuestionIndex={1}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          disabled={true}
        />
      )

      await user.keyboard('{ArrowLeft}')
      await user.keyboard('a')
      await user.keyboard('f')

      expect(mockOnQuestionNavigate).not.toHaveBeenCalled()
      expect(mockOnAnswerChange).not.toHaveBeenCalled()
      expect(mockOnFlagToggle).not.toHaveBeenCalled()
    })
  })

  describe('Navigation Panel Statistics', () => {
    it('shows correct answered count', () => {
      const partialAnswers: Record<string, ExamAnswer> = {
        q1: { questionId: 'q1', answer: 'A', flaggedForReview: false, timestamp: new Date() },
        q3: { questionId: 'q3', answer: 'E', flaggedForReview: false, timestamp: new Date() }
      }

      render(
        <ExamInterface
          questions={mockQuestions}
          answers={partialAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          showNavigationPanel={true}
        />
      )

      expect(screen.getByText(/2 Cevaplandı/)).toBeInTheDocument()
      expect(screen.getByText(/1 Boş/)).toBeInTheDocument()
    })

    it('shows correct unanswered count', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          showNavigationPanel={true}
        />
      )

      expect(screen.getByText(/2 Boş/)).toBeInTheDocument()
    })

    it('shows correct flagged count', () => {
      const partialAnswers: Record<string, ExamAnswer> = {
        q1: { questionId: 'q1', answer: 'A', flaggedForReview: true, timestamp: new Date() },
        q2: { questionId: 'q2', answer: 'C', flaggedForReview: true, timestamp: new Date() }
      }

      render(
        <ExamInterface
          questions={mockQuestions}
          answers={partialAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          showNavigationPanel={true}
        />
      )

      expect(screen.getByText(/2 İşaretli/)).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('shows message when no question is found', () => {
      render(
        <ExamInterface
          questions={[]}
          answers={{}}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      expect(screen.getByText('Soru bulunamadı')).toBeInTheDocument()
    })
  })

  describe('Answer Confirmation', () => {
    it('shows confirmation message when answer is saved', async () => {
      vi.useFakeTimers()
      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

      const { rerender } = render(
        <ExamInterface
          questions={mockQuestions}
          answers={{}}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      // Simulate answer selection
      const answersAfterSelect: Record<string, ExamAnswer> = {
        q1: { questionId: 'q1', answer: 'B', flaggedForReview: false, timestamp: new Date() }
      }

      rerender(
        <ExamInterface
          questions={mockQuestions}
          answers={answersAfterSelect}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      await waitFor(() => {
        expect(screen.getByText(/cevabınız kaydedildi/i)).toBeInTheDocument()
      })

      vi.useRealTimers()
    })
  })

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      expect(screen.getByText('Soru 1')).toBeInTheDocument()
    })

    it('provides tooltips for interactive elements', async () => {
      const user = userEvent.setup()
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      // Flag button has tooltip
      const flagButton = screen.getByRole('button', { name: /İnceleme için işaretle/i })
      expect(flagButton).toHaveAttribute('aria-label')
    })

    it('indicates current question in navigation panel', () => {
      render(
        <ExamInterface
          questions={mockQuestions}
          answers={mockAnswers}
          currentQuestionIndex={0}
          onAnswerChange={mockOnAnswerChange}
          onFlagToggle={mockOnFlagToggle}
          onQuestionNavigate={mockOnQuestionNavigate}
          showNavigationPanel={true}
        />
      )

      // Current question should be visually highlighted
      // The first question box should have primary color styling
      const navigationPanel = screen.getByText('Soru Haritası').closest('div')
      expect(navigationPanel).toBeInTheDocument()
    })
  })
})
