/**
 * PhotoAskPage — S200 audit fixes
 *
 * The frontend's interfaces (UploadResult.similar_questions, SolutionResult.solution_text)
 * never matched what backend/api/photo_ask_api.py actually returns
 * (PhotoAskResponse.matched_questions, QuestionSolutionResponse.correct_answer/explanation,
 * ai-solve's bare {solution} — sent as a query param, not a JSON body). Every successful
 * upload crashed on `uploadResult.similar_questions.length`. This file locks in the fix
 * to the real backend contract.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

import PhotoAskPage from '../PhotoAskPage'

function makeFile() {
  return new File(['fake-bytes'], 'soru.jpg', { type: 'image/jpeg' })
}

async function uploadAndWait(fetchMock: any) {
  render(<PhotoAskPage />)
  const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
  fireEvent.change(fileInput, { target: { files: [makeFile()] } })
  const searchButton = await screen.findByRole('button', { name: /Soruyu Ara/i })
  fireEvent.click(searchButton)
  await waitFor(() => expect(fetchMock).toHaveBeenCalled())
}

describe('PhotoAskPage — real backend contract (S200 audit fix)', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders matched_questions (real backend field) without crashing on similar_questions', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'matched',
        ocr_text: 'Bir sayının %20 fazlası...',
        ocr_confidence: 0.92,
        ocr_time_ms: 340,
        matched_questions: [
          {
            id: 'q-1',
            question_text: 'Bir sayının %20 fazlası kaçtır?',
            question_image_url: null,
            exam_type: 'TYT',
            subject_area: 'MATEMATIK',
            source_book: 'Kitap A',
            difficulty: 'orta',
            correct_answer: 'C',
            options: { A: '1', B: '2', C: '3', D: '4', E: '5' },
            explanation: null,
            similarity: 0.91,
          },
        ],
        ai_solution: null,
        total_time_ms: 500,
        message: 'Benzer soru bulundu',
      }),
    })

    await uploadAndWait(global.fetch)

    expect(await screen.findByText('MATEMATIK')).toBeInTheDocument()
    expect(screen.getByText('TYT')).toBeInTheDocument()
  })

  it('shows the AI solution directly when the backend already solved it during upload (status=ai_solved)', async () => {
    ;(global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'ai_solved',
        ocr_text: 'Zor bir soru...',
        ocr_confidence: 0.8,
        ocr_time_ms: 300,
        matched_questions: [],
        ai_solution: { solution: 'Cevap: Bu sorunun çözümü şöyledir...', model: 'qwen3-8b', generated: true, error: null },
        total_time_ms: 1200,
        message: 'AI ile çözüldü',
      }),
    })

    await uploadAndWait(global.fetch)

    expect(await screen.findByText(/Bu sorunun çözümü şöyledir/i)).toBeInTheDocument()
    expect(screen.getByText('AI Üretim')).toBeInTheDocument()
  })

  it('handleViewSolution renders correct_answer/explanation, not solution_text', async () => {
    ;(global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'matched',
          ocr_text: 'soru',
          ocr_confidence: 0.9,
          ocr_time_ms: 100,
          matched_questions: [
            {
              id: 'q-42',
              question_text: 'Test sorusu metni',
              question_image_url: null,
              exam_type: 'AYT',
              subject_area: 'FIZIK',
              source_book: null,
              difficulty: null,
              correct_answer: 'B',
              options: null,
              explanation: null,
              similarity: 0.95,
            },
          ],
          ai_solution: null,
          total_time_ms: 200,
          message: '',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          question_id: 'q-42',
          question_text: 'Test sorusu metni',
          correct_answer: 'B',
          explanation: 'Çünkü B doğru şıktır.',
          options: { A: '1', B: '2', C: '3', D: '4', E: '5' },
        }),
      })

    await uploadAndWait(global.fetch)
    const item = await screen.findByText('Test sorusu metni')
    fireEvent.click(item)

    expect(await screen.findByText(/Çünkü B doğru şıktır/i)).toBeInTheDocument()
    expect(screen.getByText(/Doğru Cevap: B/)).toBeInTheDocument()
    expect(global.fetch).toHaveBeenLastCalledWith(
      '/api/v1/photo-ask/solution/q-42',
      expect.objectContaining({ credentials: 'include' }),
    )
  })

  it('AI-solve sends question_text as a query param (backend reads it as Query, not JSON body)', async () => {
    ;(global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'partial_match',
          ocr_text: 'çözülemeyen soru metni',
          ocr_confidence: 0.5,
          ocr_time_ms: 100,
          matched_questions: [],
          ai_solution: null,
          total_time_ms: 150,
          message: 'Eşleşme bulunamadı',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          question_text: 'çözülemeyen soru metni',
          solution: 'AI çözümü burada',
          model: 'qwen3-8b',
          generated: true,
        }),
      })

    await uploadAndWait(global.fetch)
    const aiButton = await screen.findByRole('button', { name: /AI ile Çöz/i })
    fireEvent.click(aiButton)

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2))
    const [url, options] = (global.fetch as any).mock.calls[1]
    expect(url).toContain('/api/v1/photo-ask/ai-solve?question_text=')
    expect(url).toContain(encodeURIComponent('çözülemeyen soru metni'))
    expect(options).toEqual(expect.objectContaining({ method: 'POST', credentials: 'include' }))
    expect(await screen.findByText('AI çözümü burada')).toBeInTheDocument()
  })
})
