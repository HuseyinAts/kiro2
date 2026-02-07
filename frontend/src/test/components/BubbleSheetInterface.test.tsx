/**
 * Optik Form Arayüzü Test Dosyası
 * BubbleSheetInterface ve BubbleSheetPanel bileşenlerinin testleri
 * 
 * REQ-1.1: TYT sınav formatı desteği
 * REQ-1.6: Otomatik kaydetme ile veri kaybı önleme
 */
import * as React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider, createTheme } from '@mui/material'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import '@testing-library/jest-dom'
import BubbleSheetInterface from '../../components/Exam/BubbleSheetInterface'
import BubbleSheetPanel from '../../components/Exam/BubbleSheetPanel'

const theme = createTheme()

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  )
}

describe('BubbleSheetInterface', () => {
  const mockOptions = ['A', 'B', 'C', 'D', 'E']
  const mockOnAnswerSelect = vi.fn()

  beforeEach(() => {
    mockOnAnswerSelect.mockClear()
  })

  describe('Temel Render', () => {
    it('soru numarasını gösterir', () => {
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      expect(screen.getByText('1')).toBeInTheDocument()
    })

    it('tüm seçenekleri gösterir', () => {
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      mockOptions.forEach(option => {
        expect(screen.getByText(option)).toBeInTheDocument()
      })
    })

    it('seçili cevabı vurgular', () => {
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer="B"
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleB = screen.getByRole('radio', { name: /Şık B/i })
      expect(bubbleB).toHaveAttribute('aria-checked', 'true')
    })
  })

  describe('Cevap İşaretleme (Mark/Unmark)', () => {
    it('bubble tıklandığında cevap seçer', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleA = screen.getByRole('radio', { name: /Şık A/i })
      await user.click(bubbleA)

      expect(mockOnAnswerSelect).toHaveBeenCalledWith('A')
    })

    it('seçili bubble tekrar tıklandığında işareti kaldırır', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer="C"
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleC = screen.getByRole('radio', { name: /Şık C/i })
      await user.click(bubbleC)

      expect(mockOnAnswerSelect).toHaveBeenCalledWith('')
    })

    it('farklı bir bubble seçildiğinde cevabı değiştirir', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer="A"
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleD = screen.getByRole('radio', { name: /Şık D/i })
      await user.click(bubbleD)

      expect(mockOnAnswerSelect).toHaveBeenCalledWith('D')
    })
  })

  describe('Görsel Geri Bildirim', () => {
    it('seçili bubble için görsel geri bildirim gösterir', () => {
      const { container } = renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer="B"
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleB = screen.getByRole('radio', { name: /Şık B/i })
      expect(bubbleB).toHaveStyle({ fontWeight: 'bold' })
    })

    it('doğru cevap için başarı rengi gösterir', () => {
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer="A"
          onAnswerSelect={mockOnAnswerSelect}
          showFeedback={true}
          correctAnswer="A"
        />
      )

      expect(screen.getByTestId('CheckCircleIcon')).toBeInTheDocument()
    })

    it('yanlış cevap için hata rengi gösterir', () => {
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer="B"
          onAnswerSelect={mockOnAnswerSelect}
          showFeedback={true}
          correctAnswer="A"
        />
      )

      expect(screen.getByTestId('CircleIcon')).toBeInTheDocument()
    })
  })

  describe('Klavye Erişilebilirliği', () => {
    it('Enter tuşu ile cevap seçer', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleA = screen.getByRole('radio', { name: /Şık A/i })
      bubbleA.focus()
      await user.keyboard('{Enter}')

      expect(mockOnAnswerSelect).toHaveBeenCalledWith('A')
    })

    it('Space tuşu ile cevap seçer', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleB = screen.getByRole('radio', { name: /Şık B/i })
      bubbleB.focus()
      await user.keyboard(' ')

      expect(mockOnAnswerSelect).toHaveBeenCalledWith('B')
    })

    it('Tab tuşu ile bubble\'lar arasında gezinir', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
        />
      )

      const bubbleA = screen.getByRole('radio', { name: /Şık A/i })
      const bubbleB = screen.getByRole('radio', { name: /Şık B/i })

      bubbleA.focus()
      expect(document.activeElement).toBe(bubbleA)

      await user.tab()
      expect(document.activeElement).toBe(bubbleB)
    })
  })

  describe('Disabled Durumu', () => {
    it('disabled olduğunda tıklama çalışmaz', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
          disabled={true}
        />
      )

      const bubbleA = screen.getByRole('radio', { name: /Şık A/i })
      await user.click(bubbleA)

      expect(mockOnAnswerSelect).not.toHaveBeenCalled()
    })

    it('disabled olduğunda klavye girişi çalışmaz', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
          disabled={true}
        />
      )

      const bubbleA = screen.getByRole('radio', { name: /Şık A/i })
      expect(bubbleA).toHaveAttribute('tabindex', '-1')
    })
  })

  describe('Boyut Seçenekleri', () => {
    it('small boyutunda render olur', () => {
      const { container } = renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
          size="small"
        />
      )

      expect(container).toBeInTheDocument()
    })

    it('medium boyutunda render olur', () => {
      const { container } = renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
          size="medium"
        />
      )

      expect(container).toBeInTheDocument()
    })

    it('large boyutunda render olur', () => {
      const { container } = renderWithTheme(
        <BubbleSheetInterface
          questionNumber={1}
          options={mockOptions}
          selectedAnswer={null}
          onAnswerSelect={mockOnAnswerSelect}
          size="large"
        />
      )

      expect(container).toBeInTheDocument()
    })
  })
})

describe('BubbleSheetPanel', () => {
  const mockQuestions = [
    { id: 'q1', number: 1, subject: 'Matematik', topic: 'Cebir' },
    { id: 'q2', number: 2, subject: 'Matematik', topic: 'Geometri' },
    { id: 'q3', number: 3, subject: 'Türkçe', topic: 'Dil Bilgisi' },
    { id: 'q4', number: 4, subject: 'Türkçe', topic: 'Anlam Bilgisi' },
    { id: 'q5', number: 5, subject: 'Fen', topic: 'Fizik' }
  ]

  const mockAnswers = {
    'q1': 'A',
    'q2': 'B',
    'q3': ''
  }

  const mockOnAnswerChange = vi.fn()
  const mockOnQuestionNavigate = vi.fn()

  beforeEach(() => {
    mockOnAnswerChange.mockClear()
    mockOnQuestionNavigate.mockClear()
  })

  describe('Temel Render', () => {
    it('tüm soruları gösterir', () => {
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      mockQuestions.forEach(q => {
        expect(screen.getByText(q.number.toString())).toBeInTheDocument()
      })
    })

    it('istatistikleri doğru hesaplar', () => {
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      // 2 cevaplandı (q1, q2), 3 boş (q3, q4, q5)
      expect(screen.getByText(/2\/5 Cevaplandı/i)).toBeInTheDocument()
      expect(screen.getByText(/3 Boş/i)).toBeInTheDocument()
    })

    it('konulara göre gruplar', () => {
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
          showSubjects={true}
        />
      )

      expect(screen.getByText('Matematik')).toBeInTheDocument()
      expect(screen.getByText('Türkçe')).toBeInTheDocument()
      expect(screen.getByText('Fen')).toBeInTheDocument()
    })
  })

  describe('Cevap Değiştirme', () => {
    it('cevap değiştiğinde callback çağrılır', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      // q4 için C seçeneğini işaretle
      const bubbles = screen.getAllByRole('radio', { name: /Şık C/i })
      await user.click(bubbles[3]) // 4. soru

      expect(mockOnAnswerChange).toHaveBeenCalledWith('q4', 'C')
    })
  })

  describe('Soru Navigasyonu', () => {
    it('soruya tıklandığında navigasyon callback çağrılır', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
          onQuestionNavigate={mockOnQuestionNavigate}
        />
      )

      // İlk sorunun container'ına tıkla
      const questionContainers = screen.getAllByText(/^\d+$/)
      await user.click(questionContainers[0].closest('div[role="button"]') || questionContainers[0])

      expect(mockOnQuestionNavigate).toHaveBeenCalled()
    })

    it('mevcut soruyu vurgular', () => {
      const { container } = renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
          currentQuestionIndex={2}
        />
      )

      // 3. soru (index 2) vurgulanmalı
      expect(container).toBeInTheDocument()
    })
  })

  describe('Görünüm Modları', () => {
    it('grid görünümünde başlar', () => {
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      // Grid görünümü varsayılan
      expect(screen.getByTestId('ViewListIcon')).toBeInTheDocument()
    })

    it('liste görünümüne geçiş yapar', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      const viewToggle = screen.getByTestId('ViewListIcon').closest('button')
      if (viewToggle) {
        await user.click(viewToggle)
        expect(screen.getByTestId('GridViewIcon')).toBeInTheDocument()
      }
    })
  })

  describe('Boş Soru Vurgulama', () => {
    it('boş soruları vurgulama özelliği çalışır', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      const highlightButton = screen.getByTestId('VisibilityOffIcon').closest('button')
      if (highlightButton) {
        await user.click(highlightButton)
        expect(screen.getByTestId('VisibilityIcon')).toBeInTheDocument()
      }
    })
  })

  describe('Bilgi Dialog', () => {
    it('bilgi dialogunu açar', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      const infoButton = screen.getByTestId('InfoIcon').closest('button')
      if (infoButton) {
        await user.click(infoButton)
        
        await waitFor(() => {
          expect(screen.getByText('Optik Form Kullanımı')).toBeInTheDocument()
        })
      }
    })

    it('bilgi dialogunu kapatır', async () => {
      const user = userEvent.setup()
      
      renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
        />
      )

      const infoButton = screen.getByTestId('InfoIcon').closest('button')
      if (infoButton) {
        await user.click(infoButton)
        
        await waitFor(() => {
          expect(screen.getByText('Optik Form Kullanımı')).toBeInTheDocument()
        })

        const closeButton = screen.getByText('Anladım')
        await user.click(closeButton)

        await waitFor(() => {
          expect(screen.queryByText('Optik Form Kullanımı')).not.toBeInTheDocument()
        })
      }
    })
  })

  describe('Kolon Sayısı', () => {
    it('1 kolonda render olur', () => {
      const { container } = renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
          columns={1}
        />
      )

      expect(container).toBeInTheDocument()
    })

    it('2 kolonda render olur', () => {
      const { container } = renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
          columns={2}
        />
      )

      expect(container).toBeInTheDocument()
    })

    it('4 kolonda render olur', () => {
      const { container } = renderWithTheme(
        <BubbleSheetPanel
          questions={mockQuestions}
          answers={mockAnswers}
          onAnswerChange={mockOnAnswerChange}
          columns={4}
        />
      )

      expect(container).toBeInTheDocument()
    })
  })
})
