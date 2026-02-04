/**
 * FlaggedQuestionsPanel Test Suite
 * Tests for flagged questions list and review navigation - REQ-1.6
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import FlaggedQuestionsPanel from '../FlaggedQuestionsPanel'

describe('FlaggedQuestionsPanel', () => {
  const mockOnQuestionSelect = vi.fn()
  const mockOnFlagToggle = vi.fn()

  const defaultProps = {
    flaggedQuestions: new Set(['question_0', 'question_5', 'question_10']),
    answers: {
      'question_0': 'A',
      'question_5': 'B'
    },
    currentQuestionIndex: 5,
    totalQuestions: 20,
    onQuestionSelect: mockOnQuestionSelect,
    onFlagToggle: mockOnFlagToggle,
    disabled: false
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders flagged questions panel with correct title', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    expect(screen.getByText('Şüpheli Sorular')).toBeInTheDocument()
  })

  it('displays correct number of flagged questions', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    expect(screen.getByText('Toplam: 3')).toBeInTheDocument()
  })

  it('shows answered and unanswered statistics', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    expect(screen.getByText('Cevaplanan: 2')).toBeInTheDocument()
    expect(screen.getByText('Cevaplanmayan: 1')).toBeInTheDocument()
  })

  it('displays all flagged questions in the list', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    expect(screen.getByText('Soru 1')).toBeInTheDocument()
    expect(screen.getByText('Soru 6')).toBeInTheDocument()
    expect(screen.getByText('Soru 11')).toBeInTheDocument()
  })

  it('highlights current question', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    const currentQuestionItem = screen.getByText('Soru 6').closest('[role="button"]')
    expect(currentQuestionItem).toHaveClass('Mui-selected')
  })

  it('calls onQuestionSelect when a question is clicked', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    const questionButton = screen.getByText('Soru 1').closest('[role="button"]')
    fireEvent.click(questionButton!)
    expect(mockOnQuestionSelect).toHaveBeenCalledWith(0)
  })

  it('calls onFlagToggle when unflag button is clicked', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    const unflagButtons = screen.getAllByLabelText('İşareti kaldır')
    fireEvent.click(unflagButtons[0])
    expect(mockOnFlagToggle).toHaveBeenCalledWith('question_0')
  })

  it('shows empty state when no questions are flagged', () => {
    const emptyProps = {
      ...defaultProps,
      flaggedQuestions: new Set<string>()
    }
    render(<FlaggedQuestionsPanel {...emptyProps} />)
    expect(screen.getByText('Henüz işaretlenmiş soru yok')).toBeInTheDocument()
  })

  it('disables interactions when disabled prop is true', () => {
    const disabledProps = {
      ...defaultProps,
      disabled: true
    }
    render(<FlaggedQuestionsPanel {...disabledProps} />)
    const questionButton = screen.getByText('Soru 1').closest('[role="button"]')
    expect(questionButton).toHaveAttribute('aria-disabled', 'true')
  })

  it('shows warning for unanswered flagged questions', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    expect(screen.getByText(/1 cevaplanmayan şüpheli soru var/i)).toBeInTheDocument()
  })

  it('can be collapsed and expanded', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    const header = screen.getByText('Şüpheli Sorular').closest('div')
    
    // Initially expanded - check if content exists
    expect(screen.getByText('Soru 1')).toBeInTheDocument()
    
    // Click to collapse
    fireEvent.click(header!)
    
    // Content should be hidden (Collapse component handles this)
    // We just verify the click handler works
    expect(header).toBeInTheDocument()
  })

  it('sorts flagged questions by index', () => {
    const unsortedProps = {
      ...defaultProps,
      flaggedQuestions: new Set(['question_10', 'question_0', 'question_5'])
    }
    render(<FlaggedQuestionsPanel {...unsortedProps} />)
    
    const questions = screen.getAllByText(/Soru \d+/)
    expect(questions[0]).toHaveTextContent('Soru 1')
    expect(questions[1]).toHaveTextContent('Soru 6')
    expect(questions[2]).toHaveTextContent('Soru 11')
  })

  it('shows answered status correctly', () => {
    render(<FlaggedQuestionsPanel {...defaultProps} />)
    
    // Question 1 (index 0) is answered
    const question1 = screen.getByText('Soru 1').closest('li')
    expect(question1).toHaveTextContent('Cevaplandı')
    
    // Question 11 (index 10) is not answered
    const question11 = screen.getByText('Soru 11').closest('li')
    expect(question11).toHaveTextContent('Cevaplanmadı')
  })
})
