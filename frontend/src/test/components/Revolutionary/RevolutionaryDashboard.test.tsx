/**
 * Teknofest 2025 Eğitim Eylemci Platformu
 * RevolutionaryDashboard Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render, createMockUser } from '../../utils/test-utils'
import { server, addHandler } from '../../mocks/server'
import { http, HttpResponse } from 'msw'
import RevolutionaryDashboard from '../../../components/Revolutionary/RevolutionaryDashboard'

const mockRevolutionaryData = {
  learningStyle: {
    varkProfile: {
      visual: 0.8,
      auditory: 0.3,
      reading: 0.6,
      kinesthetic: 0.4
    },
    felderProfile: {
      activeReflective: 0.7,
      sensingIntuitive: 0.5,
      visualVerbal: 0.8,
      sequentialGlobal: 0.6
    },
    hybridCode: 'V-A-V-S',
    confidenceLevel: 0.85
  },
  fsrsSchedule: {
    cards: [
      {
        id: '1',
        content: 'Matematik - Türev Kuralları',
        nextReview: '2024-01-02T10:00:00Z',
        interval: 1,
        easeFactor: 2.5,
        repetitions: 1
      }
    ],
    schedule: {
      today: 5,
      tomorrow: 3,
      thisWeek: 15
    }
  },
  multiAgentStatus: {
    agents: [
      { name: 'LearningPathAgent', status: 'active', lastUpdate: '2024-01-01T12:00:00Z' },
      { name: 'StudyBuddyAgent', status: 'active', lastUpdate: '2024-01-01T12:00:00Z' },
      { name: 'AccessibilityAgent', status: 'active', lastUpdate: '2024-01-01T12:00:00Z' }
    ],
    coordination: {
      activeConnections: 3,
      messagesSent: 150,
      messagesReceived: 148
    }
  }
}

describe('RevolutionaryDashboard', () => {
  const defaultProps = {
    userId: 'test-user-id'
  }

  beforeEach(() => {
    vi.clearAllMocks()
    server.resetHandlers()
    
    // Mock successful API responses
    addHandler(
      http.get('/api/v1/learning-style/:userId', () => {
        return HttpResponse.json({
          success: true,
          data: mockRevolutionaryData.learningStyle,
          message: 'Öğrenme stili alındı'
        })
      })
    )
    
    addHandler(
      http.get('/api/v1/revolutionary-features/fsrs/:userId', () => {
        return HttpResponse.json({
          success: true,
          data: mockRevolutionaryData.fsrsSchedule,
          message: 'FSRS verileri alındı'
        })
      })
    )
    
    addHandler(
      http.get('/api/v1/revolutionary-features/multi-agent/status', () => {
        return HttpResponse.json({
          success: true,
          data: mockRevolutionaryData.multiAgentStatus,
          message: 'Multi-agent durumu alındı'
        })
      })
    )
  })

  it('renders revolutionary dashboard correctly', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    expect(screen.getByText(/devrimsel özellikler/i)).toBeInTheDocument()
    expect(screen.getByText(/öğrenme stili profili/i)).toBeInTheDocument()
    expect(screen.getByText(/fsrs tekrar sistemi/i)).toBeInTheDocument()
    expect(screen.getByText(/multi-agent koordinasyon/i)).toBeInTheDocument()
  })

  it('displays loading state initially', () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    expect(screen.getByText(/yükleniyor/i)).toBeInTheDocument()
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('displays learning style profile correctly', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('V-A-V-S')).toBeInTheDocument()
      expect(screen.getByText(/görsel: 80%/i)).toBeInTheDocument()
      expect(screen.getByText(/işitsel: 30%/i)).toBeInTheDocument()
      expect(screen.getByText(/güven seviyesi: 85%/i)).toBeInTheDocument()
    })
  })

  it('displays FSRS schedule correctly', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/bugün: 5 kart/i)).toBeInTheDocument()
      expect(screen.getByText(/yarın: 3 kart/i)).toBeInTheDocument()
      expect(screen.getByText(/bu hafta: 15 kart/i)).toBeInTheDocument()
      expect(screen.getByText('Matematik - Türev Kuralları')).toBeInTheDocument()
    })
  })

  it('displays multi-agent status correctly', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('LearningPathAgent')).toBeInTheDocument()
      expect(screen.getByText('StudyBuddyAgent')).toBeInTheDocument()
      expect(screen.getByText('AccessibilityAgent')).toBeInTheDocument()
      expect(screen.getByText(/aktif bağlantılar: 3/i)).toBeInTheDocument()
      expect(screen.getByText(/gönderilen mesajlar: 150/i)).toBeInTheDocument()
    })
  })

  it('shows error state when API calls fail', async () => {
    // Mock API error
    addHandler(
      http.get('/api/v1/learning-style/:userId', () => {
        return HttpResponse.json(
          {
            success: false,
            message: 'Veri alınamadı',
            error: 'Server Error'
          },
          { status: 500 }
        )
      })
    )

    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/veri yüklenirken hata oluştu/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /tekrar dene/i })).toBeInTheDocument()
    })
  })

  it('retries data loading when retry button is clicked', async () => {
    const user = userEvent.setup()
    
    // Mock initial error then success
    let callCount = 0
    addHandler(
      http.get('/api/v1/learning-style/:userId', () => {
        callCount++
        if (callCount === 1) {
          return HttpResponse.json(
            { success: false, message: 'Server Error' },
            { status: 500 }
          )
        }
        return HttpResponse.json({
          success: true,
          data: mockRevolutionaryData.learningStyle
        })
      })
    )

    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/veri yüklenirken hata oluştu/i)).toBeInTheDocument()
    })
    
    const retryButton = screen.getByRole('button', { name: /tekrar dene/i })
    await user.click(retryButton)
    
    await waitFor(() => {
      expect(screen.getByText('V-A-V-S')).toBeInTheDocument()
    })
  })

  it('refreshes data when refresh button is clicked', async () => {
    const user = userEvent.setup()
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('V-A-V-S')).toBeInTheDocument()
    })
    
    const refreshButton = screen.getByRole('button', { name: /yenile/i })
    await user.click(refreshButton)
    
    expect(screen.getByText(/yükleniyor/i)).toBeInTheDocument()
  })

  it('opens learning style details modal', async () => {
    const user = userEvent.setup()
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('V-A-V-S')).toBeInTheDocument()
    })
    
    const detailsButton = screen.getByRole('button', { name: /detayları gör/i })
    await user.click(detailsButton)
    
    expect(screen.getByText(/öğrenme stili detayları/i)).toBeInTheDocument()
    expect(screen.getByText(/vark profili/i)).toBeInTheDocument()
    expect(screen.getByText(/felder-silverman profili/i)).toBeInTheDocument()
  })

  it('opens FSRS card details', async () => {
    const user = userEvent.setup()
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Matematik - Türev Kuralları')).toBeInTheDocument()
    })
    
    const cardButton = screen.getByText('Matematik - Türev Kuralları')
    await user.click(cardButton)
    
    expect(screen.getByText(/kart detayları/i)).toBeInTheDocument()
    expect(screen.getByText(/sonraki tekrar/i)).toBeInTheDocument()
    expect(screen.getByText(/zorluk faktörü/i)).toBeInTheDocument()
  })

  it('shows agent status indicators correctly', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      const activeIndicators = screen.getAllByText(/aktif/i)
      expect(activeIndicators).toHaveLength(3) // 3 active agents
      
      // Check for status indicators (green dots, etc.)
      const statusIndicators = screen.getAllByTestId('agent-status-indicator')
      expect(statusIndicators).toHaveLength(3)
      statusIndicators.forEach(indicator => {
        expect(indicator).toHaveClass('status-active')
      })
    })
  })

  it('handles real-time updates for agent status', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/aktif bağlantılar: 3/i)).toBeInTheDocument()
    })
    
    // Simulate real-time update
    const updatedStatus = {
      ...mockRevolutionaryData.multiAgentStatus,
      coordination: {
        activeConnections: 4,
        messagesSent: 155,
        messagesReceived: 153
      }
    }
    
    addHandler(
      http.get('/api/v1/revolutionary-features/multi-agent/status', () => {
        return HttpResponse.json({
          success: true,
          data: updatedStatus
        })
      })
    )
    
    // Trigger refresh (this would normally be done via WebSocket)
    const refreshButton = screen.getByRole('button', { name: /yenile/i })
    await userEvent.setup().click(refreshButton)
    
    await waitFor(() => {
      expect(screen.getByText(/aktif bağlantılar: 4/i)).toBeInTheDocument()
      expect(screen.getByText(/gönderilen mesajlar: 155/i)).toBeInTheDocument()
    })
  })

  it('supports keyboard navigation', async () => {
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('V-A-V-S')).toBeInTheDocument()
    })
    
    // Tab through interactive elements
    const detailsButton = screen.getByRole('button', { name: /detayları gör/i })
    detailsButton.focus()
    expect(detailsButton).toHaveFocus()
    
    fireEvent.keyDown(detailsButton, { key: 'Tab' })
    const refreshButton = screen.getByRole('button', { name: /yenile/i })
    expect(refreshButton).toHaveFocus()
  })

  it('displays tooltips for complex features', async () => {
    const user = userEvent.setup()
    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('V-A-V-S')).toBeInTheDocument()
    })
    
    const helpIcon = screen.getByRole('button', { name: /yardım/i })
    await user.hover(helpIcon)
    
    await waitFor(() => {
      expect(screen.getByText(/hibrit öğrenme stili kodu/i)).toBeInTheDocument()
    })
  })

  it('handles empty data states gracefully', async () => {
    // Mock empty responses
    addHandler(
      http.get('/api/v1/revolutionary-features/fsrs/:userId', () => {
        return HttpResponse.json({
          success: true,
          data: {
            cards: [],
            schedule: { today: 0, tomorrow: 0, thisWeek: 0 }
          }
        })
      })
    )

    render(<RevolutionaryDashboard {...defaultProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/henüz kart bulunmuyor/i)).toBeInTheDocument()
      expect(screen.getByText(/bugün: 0 kart/i)).toBeInTheDocument()
    })
  })
})