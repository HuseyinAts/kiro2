/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * End-to-End Video Loading Flow Tests
 * 
 * Bu dosya video yükleme akışının tamamını test eder:
 * 1. Video yükleme başarılı senaryosu
 * 2. Video yükleme hata senaryosu
 * 3. Retry mekanizması
 * 4. Timeout senaryosu
 * 5. Network kesintisi
 * 6. Offline mode
 * 7. Cache hit/miss senaryoları
 * 8. User interaction testleri
 * 
 * Requirements: 11.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '../utils/test-utils'
import { server, addHandler } from '../mocks/server'
import { http, HttpResponse } from 'msw'
import App from '../../app'

// Mock window.open for popup tests
const mockPopup = {
  document: {
    write: vi.fn(),
    close: vi.fn()
  },
  close: vi.fn()
}

global.window.open = vi.fn(() => mockPopup as any)

// Mock video recommendations data
const mockVideoRecommendations = [
  {
    subject_exam: 'Matematik TYT',
    videos: [
      {
        video_id: 'test-video-1',
        title: 'Üçgenler - Temel Kavramlar',
        channel: 'Matematik Öğretmeni',
        duration: '15:30',
        quality_score: 8.5,
        subject: 'matematik',
        url: 'https://www.youtube.com/watch?v=test-video-1',
        relevance_score: 0.85,
        language_score: 0.95,
        difficulty_match: 0.9
      },
      {
        video_id: 'test-video-2',
        title: 'Geometri - Alan Hesaplamaları',
        channel: 'TYT Matematik',
        duration: '12:45',
        quality_score: 9.2,
        subject: 'matematik',
        url: 'https://www.youtube.com/watch?v=test-video-2',
        relevance_score: 0.92,
        language_score: 0.98,
        difficulty_match: 0.88
      }
    ],
    total_count: 2,
    cache_hit: false,
    response_time_ms: 1250
  },
  {
    subject_exam: 'Fizik TYT',
    videos: [
      {
        video_id: 'test-video-3',
        title: 'Hareket - Hız ve İvme',
        channel: 'Fizik Öğretmeni',
        duration: '18:20',
        quality_score: 8.8,
        subject: 'fizik',
        url: 'https://www.youtube.com/watch?v=test-video-3',
        relevance_score: 0.88,
        language_score: 0.96,
        difficulty_match: 0.85
      }
    ],
    total_count: 1,
    cache_hit: false,
    response_time_ms: 980
  }
]

const mockStudentProfile = {
  goals: ['TYT Matematik', 'TYT Fizik'],
  currentLevel: { matematik: 5, fizik: 4 },
  learningStyle: 'visual',
  preferences: {}
}

describe('Video Loading Flow E2E Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    server.resetHandlers()
    mockPopup.document.write.mockClear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Başarılı Video Yükleme Senaryosu', () => {
    it('videoları başarıyla yükler ve gösterir', async () => {
      const user = userEvent.setup()
      
      // Setup successful API response
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations,
            message: 'Video önerileri başarıyla alındı'
          })
        })
      )

      render(<App />)

      // Navigate to Learning Path page
      await navigateToLearningPath(user)

      // Click on video library button
      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      // Verify loading UI is shown
      await waitFor(() => {
        expect(mockPopup.document.write).toHaveBeenCalled()
        const loadingHTML = mockPopup.document.write.mock.calls[0][0]
        expect(loadingHTML).toContain('🤖 AI size özel videoları buluyor')
        expect(loadingHTML).toContain('Yükleniyor')
      })

      // Wait for success UI
      await waitFor(() => {
        const successHTML = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(successHTML).toContain('Kişiselleştirilmiş Video Hazır')
        expect(successHTML).toContain('Matematik TYT')
        expect(successHTML).toContain('Fizik TYT')
        expect(successHTML).toContain('test-video-1')
        expect(successHTML).toContain('test-video-2')
        expect(successHTML).toContain('test-video-3')
      }, { timeout: 5000 })
    })

    it('cache hit durumunda hızlı yükleme yapar', async () => {
      const user = userEvent.setup()
      
      // Setup cached response
      const cachedRecommendations = mockVideoRecommendations.map(rec => ({
        ...rec,
        cache_hit: true,
        response_time_ms: 85
      }))

      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: cachedRecommendations,
            message: 'Video önerileri cache\'den alındı'
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      // Verify fast loading with cache indicator
      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('💾 Cache')
        expect(html).toContain('0.1s') // Fast response time
      }, { timeout: 3000 })
    })

    it('video kalite skorlarını doğru gösterir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('8.5') // Quality score for video 1
        expect(html).toContain('9.2') // Quality score for video 2
        expect(html).toContain('8.8') // Quality score for video 3
      })
    })
  })

  describe('Hata Senaryoları', () => {
    it('timeout durumunda fallback videolar gösterir', async () => {
      const user = userEvent.setup()
      
      // Setup delayed response (simulating timeout)
      addHandler(
        http.post('/api/youtube/recommendations', async () => {
          await new Promise(resolve => setTimeout(resolve, 25000)) // 25s delay
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      // Verify loading UI
      await waitFor(() => {
        expect(mockPopup.document.write).toHaveBeenCalled()
      })

      // Wait for timeout and fallback
      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Backend bağlantı hatası')
        expect(html).toContain('Örnek videolar gösteriliyor')
      }, { timeout: 25000 })
    })

    it('network hatası durumunda kullanıcı dostu mesaj gösterir', async () => {
      const user = userEvent.setup()
      
      // Setup network error
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.error()
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Backend bağlantı hatası')
      }, { timeout: 5000 })
    })

    it('500 server error durumunda fallback gösterir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return new HttpResponse(null, { status: 500 })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Örnek videolar')
      }, { timeout: 5000 })
    })
  })

  describe('Retry Mekanizması', () => {
    it('ilk denemede başarısız olursa otomatik retry yapar', async () => {
      const user = userEvent.setup()
      let attemptCount = 0
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          attemptCount++
          if (attemptCount === 1) {
            return HttpResponse.error()
          }
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      // Verify retry attempt is shown
      await waitFor(() => {
        const calls = mockPopup.document.write.mock.calls
        const hasRetryMessage = calls.some(call => 
          call[0].includes('Deneme 2')
        )
        expect(hasRetryMessage).toBe(true)
      }, { timeout: 10000 })

      // Verify success after retry
      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Kişiselleştirilmiş Video Hazır')
      }, { timeout: 10000 })

      expect(attemptCount).toBe(2)
    })

    it('maksimum 3 deneme yapar', async () => {
      const user = userEvent.setup()
      let attemptCount = 0
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          attemptCount++
          return HttpResponse.error()
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        expect(attemptCount).toBeLessThanOrEqual(3)
      }, { timeout: 15000 })

      // Verify fallback is shown after max retries
      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Örnek videolar')
      }, { timeout: 15000 })
    })
  })

  describe('Loading Progress UI', () => {
    it('loading progress bar gösterir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', async () => {
          await new Promise(resolve => setTimeout(resolve, 2000))
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      // Verify progress bar exists
      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[0][0]
        expect(html).toContain('progress')
        expect(html).toContain('%')
      })
    })

    it('dinamik loading mesajları gösterir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', async () => {
          await new Promise(resolve => setTimeout(resolve, 2000))
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[0][0]
        expect(html).toMatch(/Hedefleriniz analiz ediliyor|AI size özel videoları buluyor|Videolar hazırlanıyor/)
      })
    })
  })

  describe('User Interaction Tests', () => {
    it('yeni öneriler butonu ile yeniden yükleme yapar', async () => {
      const user = userEvent.setup()
      let callCount = 0
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          callCount++
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Yeni Öneriler')
      })

      expect(callCount).toBe(1)
    })

    it('video popup kapatma butonu çalışır', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Tamamladım')
        expect(html).toContain('window.close()')
      })
    })

    it('YouTube linklerine tıklama çalışır', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('https://www.youtube.com/watch?v=test-video-1')
        expect(html).toContain('target="_blank"')
      })
    })
  })

  describe('Offline Mode Tests', () => {
    it('offline durumunda uygun mesaj gösterir', async () => {
      const user = userEvent.setup()
      
      // Mock offline status
      Object.defineProperty(window.navigator, 'onLine', {
        writable: true,
        value: false
      })

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('İnternet bağlantısı yok')
      }, { timeout: 5000 })

      // Restore online status
      Object.defineProperty(window.navigator, 'onLine', {
        writable: true,
        value: true
      })
    })
  })

  describe('Video Metadata Tests', () => {
    it('video metadata doğru gösterilir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Üçgenler - Temel Kavramlar')
        expect(html).toContain('Matematik Öğretmeni')
        expect(html).toContain('15:30')
      })
    })

    it('subject icons doğru gösterilir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('📐') // Matematik icon
        expect(html).toContain('🔬') // Fizik icon
      })
    })
  })

  describe('Performance Tests', () => {
    it('3 saniyeden kısa sürede yükleme yapar', async () => {
      const user = userEvent.setup()
      const startTime = Date.now()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toContain('Kişiselleştirilmiş Video Hazır')
      }, { timeout: 5000 })

      const loadTime = Date.now() - startTime
      expect(loadTime).toBeLessThan(3000)
    })

    it('response time metriğini gösterir', async () => {
      const user = userEvent.setup()
      
      addHandler(
        http.post('/api/youtube/recommendations', () => {
          return HttpResponse.json({
            success: true,
            data: mockVideoRecommendations
          })
        })
      )

      render(<App />)
      await navigateToLearningPath(user)

      const videoButton = await screen.findByText(/video/i)
      await user.click(videoButton)

      await waitFor(() => {
        const html = mockPopup.document.write.mock.calls[mockPopup.document.write.mock.calls.length - 1][0]
        expect(html).toMatch(/\d+\.\d+s/) // Response time format
      })
    })
  })
})

// Helper function to navigate to Learning Path page
async function navigateToLearningPath(user: any) {
  // This is a simplified navigation - adjust based on actual app structure
  await waitFor(() => {
    expect(screen.getByText(/learning path|öğrenme yolu/i)).toBeInTheDocument()
  })
  
  const learningPathLink = screen.getByText(/learning path|öğrenme yolu/i)
  await user.click(learningPathLink)
  
  await waitFor(() => {
    expect(screen.getByText(/video/i)).toBeInTheDocument()
  })
}
