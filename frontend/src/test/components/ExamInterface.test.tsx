/**
 * ExamInterface Component Tests
 * 
 * Tests for Task 69: Sınav Arayüzü
 * - 69.1: İşaretleme sistemi
 * - 69.2: Boş bırakma
 * - 69.3: Şüpheli işaretleme
 * - 69.4: Soru navigasyonu
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider, createTheme } from '@mui/material'
import ExamInterface, { ExamQuestion, ExamAnswer } from '../../components/Exam/ExamInterface'
import { vi } from 'vitest';

const theme = createTheme()

const mockQuestions: ExamQuestion[] = [
  {
    id: 'q1',
    number: 1,
    content: 'Test sorusu 1',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Matematik',
    topic: 'Cebir'
  },
  {
    id: 'q2',
    number: 2,
    content: 'Test sorusu 2',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Türkçe',
    topic: 'Dil Bilgisi'
  },
  {
    id: 'q3',
    number: 3,
    content: 'Test sorusu 3',
    options: ['A', 'B', 'C', 'D', 'E'],
    subject: 'Fen',
    topic: 'Fizik'
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

const renderComponent = (props = {}) => {
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

  return render(
    <ThemeProvider theme={theme}>
      <ExamInterface {...defaultProps} {...props} />
    </ThemeProvider>
  )
}

describe('ExamInterface Component', () => {
  describe('Task 69.1: İşaretleme Sistemi', () => {
    it('should display current question number and content', () => {
      renderComponent()
      expect(screen.getByText('Soru 1')).toBeInTheDocument()
      expect(screen.getByText('Test sorusu 1')).toBeInTheDocument()
    })

    it('should show selected answer', () => {
      renderComponent()
      // Cevap A seçili olmalı
      const bubbles = screen.getAllByRole('radio')
      const selectedBubble = bubbles.find(b => b.getAttribute('aria-checked') === 'true')
      expect(selectedBubble).toBeDefined()
    })

    it('should call onAnswerChange when answer is selected', async () => {
      const onAnswerChange = vi.fn()
      renderComponent({ onAnswerChange, currentQuestionIndex: 1, answers: {} })

      const bubbles = screen.getAllByRole('radio')
      const optionB = bubbles[1] // B şıkkı
      
      fireEvent.click(optionB)
      
      expect(onAnswerChange).toHaveBeenCalledWith('q2', 'B')
    })

    it('should show visual confirmation after answer selection', async () => {
      const { rerender } = renderComponent({ currentQuestionIndex: 1, answers: {} })

      // Cevap seç
      const bubbles = screen.getAllByRole('radio')
      fireEvent.click(bubbles[0])

      // Cevabı güncelle
      const newAnswers = {
        ...mockAnswers,
        q2: {
          questionId: 'q2',
          answer: 'A',
          flaggedForReview: false,
          timestamp: new Date()
        }
      }

      rerender(
        <ThemeProvider theme={theme}>
          <ExamInterface
            questions={mockQuestions}
            answers={newAnswers}
            currentQuestionIndex={1}
            onAnswerChange={vi.fn()}
            onFlagToggle={vi.fn()}
            onQuestionNavigate={vi.fn()}
          />
        </ThemeProvider>
      )

      await waitFor(() => {
        expect(screen.getByText(/Cevabınız kaydedildi/i)).toBeInTheDocument()
      })
    })

    it('should allow changing answer', async () => {
      const onAnswerChange = vi.fn()
      renderComponent({ onAnswerChange })

      const bubbles = screen.getAllByRole('radio')
      const optionC = bubbles[2] // C şıkkı
      
      fireEvent.click(optionC)
      
      expect(onAnswerChange).toHaveBeenCalledWith('q1', 'C')
    })

    it('should support keyboard shortcuts for answer selection', async () => {
      const onAnswerChange = vi.fn()
      renderComponent({ onAnswerChange, currentQuestionIndex: 1, answers: {} })

      // A tuşuna bas
      fireEvent.keyDown(window, { key: 'a' })
      expect(onAnswerChange).toHaveBeenCalledWith('q2', 'A')

      // B tuşuna bas
      fireEvent.keyDown(window, { key: 'b' })
      expect(onAnswerChange).toHaveBeenCalledWith('q2', 'B')
    })
  })

  describe('Task 69.2: Boş Bırakma', () => {
    it('should track unanswered questions', () => {
      renderComponent({ answers: {} })
      
      // Navigasyon panelinde boş soru sayısı gösterilmeli
      expect(screen.getByText(/3 Boş/i)).toBeInTheDocument()
    })

    it('should show empty status icon for unanswered question', () => {
      renderComponent({ currentQuestionIndex: 1, answers: {} })
      
      // Boş soru ikonu gösterilmeli
      const emptyIcons = screen.getAllByTestId('RadioButtonUncheckedIcon')
      expect(emptyIcons.length).toBeGreaterThan(0)
    })

    it('should calculate completion percentage', () => {
      const answers = {
        q1: { questionId: 'q1', answer: 'A', flaggedForReview: false, timestamp: new Date() },
        q2: { questionId: 'q2', answer: 'B', flaggedForReview: false, timestamp: new Date() }
      }
      renderComponent({ answers })
      
      // 2/3 cevaplandı
      expect(screen.getByText(/2 Cevaplandı/i)).toBeInTheDocument()
      expect(screen.getByText(/1 Boş/i)).toBeInTheDocument()
    })

    it('should show answered status icon for answered question', () => {
      renderComponent()
      
      // Cevaplı soru ikonu gösterilmeli
      const checkIcons = screen.getAllByTestId('CheckCircleIcon')
      expect(checkIcons.length).toBeGreaterThan(0)
    })
  })

  describe('Task 69.3: Şüpheli İşaretleme', () => {
    it('should display flag button', () => {
      renderComponent()
      
      const flagButton = screen.getByRole('button', { name: /İnceleme için işaretle/i })
      expect(flagButton).toBeInTheDocument()
    })

    it('should call onFlagToggle when flag button is clicked', () => {
      const onFlagToggle = vi.fn()
      renderComponent({ onFlagToggle })

      const flagButton = screen.getByRole('button', { name: /İnceleme için işaretle/i })
      fireEvent.click(flagButton)

      expect(onFlagToggle).toHaveBeenCalledWith('q1')
    })

    it('should show flagged status', () => {
      const answers = {
        q1: {
          questionId: 'q1',
          answer: 'A',
          flaggedForReview: true,
          timestamp: new Date()
        }
      }
      renderComponent({ answers })

      expect(screen.getByRole('button', { name: /İnceleme işaretini kaldır/i })).toBeInTheDocument()
    })

    it('should track flagged questions count', () => {
      const answers = {
        q1: { questionId: 'q1', answer: 'A', flaggedForReview: true, timestamp: new Date() },
        q2: { questionId: 'q2', answer: 'B', flaggedForReview: true, timestamp: new Date() }
      }
      renderComponent({ answers })

      expect(screen.getByText(/2 İşaretli/i)).toBeInTheDocument()
    })

    it('should support keyboard shortcut F for flagging', () => {
      const onFlagToggle = vi.fn()
      renderComponent({ onFlagToggle })

      fireEvent.keyDown(window, { key: 'f' })
      expect(onFlagToggle).toHaveBeenCalledWith('q1')

      fireEvent.keyDown(window, { key: 'F' })
      expect(onFlagToggle).toHaveBeenCalledTimes(2)
    })

    it('should show flag icon in navigation panel for flagged questions', () => {
      const answers = {
        q1: { questionId: 'q1', answer: 'A', flaggedForReview: true, timestamp: new Date() }
      }
      renderComponent({ answers })

      const flagIcons = screen.getAllByTestId('FlagIcon')
      expect(flagIcons.length).toBeGreaterThan(0)
    })
  })

  describe('Task 69.4: Soru Navigasyonu', () => {
    it('should display question navigation buttons', () => {
      renderComponent()

      expect(screen.getByRole('button', { name: /Önceki Soru/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Sonraki Soru/i })).toBeInTheDocument()
    })

    it('should disable previous button on first question', () => {
      renderComponent({ currentQuestionIndex: 0 })

      const prevButton = screen.getByRole('button', { name: /Önceki Soru/i })
      expect(prevButton).toBeDisabled()
    })

    it('should disable next button on last question', () => {
      renderComponent({ currentQuestionIndex: 2 })

      const nextButton = screen.getByRole('button', { name: /Sonraki Soru/i })
      expect(nextButton).toBeDisabled()
    })

    it('should call onQuestionNavigate when next button is clicked', () => {
      const onQuestionNavigate = vi.fn()
      renderComponent({ onQuestionNavigate, currentQuestionIndex: 0 })

      const nextButton = screen.getByRole('button', { name: /Sonraki Soru/i })
      fireEvent.click(nextButton)

      expect(onQuestionNavigate).toHaveBeenCalledWith(1)
    })

    it('should call onQuestionNavigate when previous button is clicked', () => {
      const onQuestionNavigate = vi.fn()
      renderComponent({ onQuestionNavigate, currentQuestionIndex: 1 })

      const prevButton = screen.getByRole('button', { name: /Önceki Soru/i })
      fireEvent.click(prevButton)

      expect(onQuestionNavigate).toHaveBeenCalledWith(0)
    })

    it('should support keyboard shortcuts for navigation', () => {
      const onQuestionNavigate = vi.fn()
      renderComponent({ onQuestionNavigate, currentQuestionIndex: 1 })

      // Sol ok: Önceki
      fireEvent.keyDown(window, { key: 'ArrowLeft' })
      expect(onQuestionNavigate).toHaveBeenCalledWith(0)

      // Sağ ok: Sonraki
      fireEvent.keyDown(window, { key: 'ArrowRight' })
      expect(onQuestionNavigate).toHaveBeenCalledWith(2)
    })

    it('should display question number grid in navigation panel', () => {
      renderComponent()

      // Tüm soru numaraları gösterilmeli
      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
    })

    it('should allow jumping to specific question from grid', () => {
      const onQuestionNavigate = vi.fn()
      renderComponent({ onQuestionNavigate, currentQuestionIndex: 0 })

      // Soru 3'e tıkla
      const question3 = screen.getByText('3')
      fireEvent.click(question3)

      expect(onQuestionNavigate).toHaveBeenCalledWith(2)
    })

    it('should highlight current question in navigation grid', () => {
      renderComponent({ currentQuestionIndex: 1 })

      // Aktif soru vurgulanmalı (mavi renk)
      const question2Box = screen.getByText('2').closest('div')
      expect(question2Box).toHaveStyle({ fontWeight: 'bold' })
    })

    it('should show question progress indicator', () => {
      renderComponent({ currentQuestionIndex: 1 })

      expect(screen.getByText('2 / 3')).toBeInTheDocument()
    })

    it('should display keyboard shortcuts info', () => {
      renderComponent()

      expect(screen.getByText(/Kısayollar:/i)).toBeInTheDocument()
      expect(screen.getByText(/Gezinme/i)).toBeInTheDocument()
      expect(screen.getByText(/Cevap/i)).toBeInTheDocument()
      expect(screen.getByText(/İşaretle/i)).toBeInTheDocument()
    })
  })

  describe('Disabled State', () => {
    it('should disable all interactions when disabled', () => {
      const onAnswerChange = vi.fn()
      const onFlagToggle = vi.fn()
      const onQuestionNavigate = vi.fn()

      renderComponent({
        disabled: true,
        onAnswerChange,
        onFlagToggle,
        onQuestionNavigate
      })

      // Cevap seçme devre dışı
      const bubbles = screen.getAllByRole('radio')
      fireEvent.click(bubbles[0])
      expect(onAnswerChange).not.toHaveBeenCalled()

      // İşaretleme devre dışı
      const flagButton = screen.getByRole('button', { name: /İnceleme için işaretle/i })
      expect(flagButton).toBeDisabled()

      // Navigasyon devre dışı
      const nextButton = screen.getByRole('button', { name: /Sonraki Soru/i })
      expect(nextButton).toBeDisabled()
    })
  })

  describe('Subject and Topic Display', () => {
    it('should display question subject and topic', () => {
      renderComponent()

      expect(screen.getByText('Matematik')).toBeInTheDocument()
      expect(screen.getByText('Cebir')).toBeInTheDocument()
    })
  })

  describe('Navigation Panel Toggle', () => {
    it('should hide navigation panel when showNavigationPanel is false', () => {
      renderComponent({ showNavigationPanel: false })

      expect(screen.queryByText('Soru Haritası')).not.toBeInTheDocument()
    })

    it('should show navigation panel when showNavigationPanel is true', () => {
      renderComponent({ showNavigationPanel: true })

      expect(screen.getByText('Soru Haritası')).toBeInTheDocument()
    })
  })

  describe('Statistics Display', () => {
    it('should display correct statistics', () => {
      const answers = {
        q1: { questionId: 'q1', answer: 'A', flaggedForReview: false, timestamp: new Date() },
        q2: { questionId: 'q2', answer: 'B', flaggedForReview: true, timestamp: new Date() }
      }
      renderComponent({ answers })

      expect(screen.getByText(/2 Cevaplandı/i)).toBeInTheDocument()
      expect(screen.getByText(/1 Boş/i)).toBeInTheDocument()
      expect(screen.getByText(/1 İşaretli/i)).toBeInTheDocument()
    })
  })
})
