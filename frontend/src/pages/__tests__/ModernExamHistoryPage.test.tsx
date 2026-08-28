/**
 * ModernExamHistoryPage — S200 audit fixes
 *
 * Findings fixed:
 * 1. Backend GET /api/v1/osym-exam/my-exams returns a bare JSON array, but the
 *    page read data.exams — real successful responses always rendered an empty list.
 * 2. On any fetch failure the page silently substituted 3 hardcoded fake exam
 *    records, indistinguishable from real history.
 * 3. ExamSessionResponse (the real backend shape) has no subject/score/
 *    correct_count/wrong_count/empty_count fields — the page required them.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import { ModernExamHistoryPage } from '../ModernExamHistoryPage'

const renderPage = () =>
  render(
    <MemoryRouter initialEntries={['/exam/history']}>
      <ModernExamHistoryPage />
    </MemoryRouter>,
  )

const mockExam = (overrides: Record<string, unknown> = {}) => ({
  session_id: 'sess-1',
  student_id: 'stu-1',
  exam_type: 'TYT',
  status: 'completed',
  total_questions: 40,
  duration_minutes: 165,
  current_question_index: 40,
  started_at: '2026-07-01T10:00:00Z',
  completed_at: '2026-07-01T12:30:00Z',
  ...overrides,
})

describe('ModernExamHistoryPage — API contract fix (S200 audit)', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders exams from a bare array response (not response.exams)', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => [mockExam(), mockExam({ session_id: 'sess-2', exam_type: 'AYT' })],
    })

    renderPage()

    await waitFor(() => expect(screen.getAllByText('TYT').length + screen.getAllByText('AYT').length).toBe(2))
  })

  it('shows a real error state on fetch failure instead of fabricated exam data', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({ ok: false })

    renderPage()

    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
    expect(screen.queryByText(/TYT Deneme Sınavı/i)).not.toBeInTheDocument()
  })

  it('does not require subject/score/correct_count fields that the real backend never sends', async () => {
    // Real ExamSessionResponse shape has no subject/score/correct_count/wrong_count/empty_count —
    // rendering must not throw/crash when those keys are simply absent.
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => [mockExam({ status: 'in_progress', completed_at: null, total_questions: 77 })],
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('TYT')).toBeInTheDocument())
    // total_questions renders in both the aggregate card and the item row when there's
    // only one exam — assert it appears at least once rather than pinning an exact count.
    expect(screen.getAllByText('77').length).toBeGreaterThan(0)
    expect(screen.getByText('Devam Ediyor')).toBeInTheDocument() // status label, not a fabricated score
  })
})
