/**
 * QuizInterface — Bug Fix Tests
 *
 * Fix 2: onExit called with submitted=true from results screen
 * Fix 4: "Tekrar Dene" resets internal state instead of window.location.reload()
 *        + onRetry prop support
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QuizInterface } from '../QuizInterface'
import type { QuizConfig } from '../QuizInterface'

// Mock canvas-confetti (used on passing quiz)
vi.mock('canvas-confetti', () => ({ default: vi.fn() }))

// Mock framer-motion to avoid animation issues in test
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    span: ({ children, ...props }: any) => <span {...props}>{children}</span>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

// Mock react-syntax-highlighter
vi.mock('react-syntax-highlighter', () => ({
  Prism: ({ children }: any) => <pre>{children}</pre>,
}))
vi.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
  vscDarkPlus: {},
}))

// Mock sub-components
vi.mock('../ErrorTypeSelector', () => ({
  ErrorTypeSelector: () => null,
}))
vi.mock('../MnemonicHint', () => ({
  MnemonicHint: () => null,
}))

const makeConfig = (overrides?: Partial<QuizConfig>): QuizConfig => ({
  title: 'Test Quiz',
  description: 'Test quiz description',
  questions: [
    {
      id: 'q1',
      type: 'multiple-choice',
      question: '2+2 kactir?',
      options: ['3', '4', '5', '6'],
      correctAnswer: '4',
      difficulty: 'easy',
      points: 10,
    },
    {
      id: 'q2',
      type: 'multiple-choice',
      question: '3+3 kactir?',
      options: ['5', '6', '7', '8'],
      correctAnswer: '6',
      difficulty: 'easy',
      points: 10,
    },
  ],
  passingScore: 50,
  ...overrides,
})

/** Helper: answer both questions and submit */
const answerAndSubmit = () => {
  // Answer question 1
  fireEvent.click(screen.getByLabelText('4'))
  // Navigate to question 2
  fireEvent.click(screen.getByRole('button', { name: /sonraki/i }))
  // Answer question 2
  fireEvent.click(screen.getByLabelText('6'))
  // Submit (last question shows "Gönder")
  fireEvent.click(screen.getByRole('button', { name: /gönder/i }))
}

describe('QuizInterface — Bug Fix Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Fix 2: onExit with submitted flag from results screen', () => {
    it('calls onExit(true) when clicking exit on results screen', async () => {
      const onExit = vi.fn()
      const onSubmit = vi.fn()
      render(<QuizInterface config={makeConfig()} onExit={onExit} onSubmit={onSubmit} />)

      answerAndSubmit()

      await waitFor(() => expect(onSubmit).toHaveBeenCalled())

      // Results screen should have "Çıkış" button
      const exitBtn = screen.getByRole('button', { name: /çıkış/i })
      fireEvent.click(exitBtn)

      expect(onExit).toHaveBeenCalledWith(true)
    })
  })

  describe('Fix 4: Tekrar Dene', () => {
    it('calls onRetry callback when provided', async () => {
      const onRetry = vi.fn()
      const onSubmit = vi.fn()
      render(<QuizInterface config={makeConfig()} onRetry={onRetry} onSubmit={onSubmit} />)

      answerAndSubmit()

      await waitFor(() => expect(onSubmit).toHaveBeenCalled())

      // Click "Tekrar Dene"
      const retryBtn = screen.getByRole('button', { name: /tekrar dene/i })
      fireEvent.click(retryBtn)

      expect(onRetry).toHaveBeenCalledTimes(1)
    })

    it('resets internal state when no onRetry (shows first question again)', async () => {
      const onSubmit = vi.fn()
      render(<QuizInterface config={makeConfig()} onSubmit={onSubmit} />)

      answerAndSubmit()

      await waitFor(() => expect(onSubmit).toHaveBeenCalled())

      // Click "Tekrar Dene" (no onRetry prop → internal reset)
      const retryBtn = screen.getByRole('button', { name: /tekrar dene/i })
      fireEvent.click(retryBtn)

      // Should show first question heading again (not results)
      await waitFor(() => {
        // Use heading role to be specific (not the "Soru 1 / 2" chip)
        expect(screen.getByRole('heading', { name: /2\+2 kactir/i })).toBeInTheDocument()
      })

      // Results should no longer be visible
      expect(screen.queryByText(/tekrar dene/i)).not.toBeInTheDocument()
    })
  })
})
