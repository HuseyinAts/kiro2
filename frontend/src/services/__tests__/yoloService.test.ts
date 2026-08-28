/**
 * yoloService — S200 audit fix
 *
 * baseUrl was built as `${API_BASE_URL}/yolo`, but the backend router is
 * mounted at prefix "/api/v1/yolo" (backend/api/yolo_detection_api.py:53).
 * Every AI-detection call missed the backend entirely (404) in both dev and
 * prod, since nginx only proxies /api/* paths.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { yoloService } from '../yoloService'

describe('yoloService — /api/v1/yolo prefix (S200 audit fix)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('healthCheck calls the correctly prefixed backend path', async () => {
    ;(axios.get as any).mockResolvedValueOnce({ data: { status: 'healthy' } })

    await yoloService.healthCheck()

    expect(axios.get).toHaveBeenCalledWith(expect.stringMatching(/\/api\/v1\/yolo\/health$/))
  })

  it('detectQuestions posts to the correctly prefixed detect endpoint', async () => {
    ;(axios.post as any).mockResolvedValueOnce({
      data: { total_detections: 0, questions_count: 0, detections: [], questions: [] },
    })
    const file = new File(['x'], 'p.jpg', { type: 'image/jpeg' })

    await yoloService.detectQuestions(file)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/yolo\/detect$/),
      expect.anything(),
      expect.anything(),
    )
  })
})
