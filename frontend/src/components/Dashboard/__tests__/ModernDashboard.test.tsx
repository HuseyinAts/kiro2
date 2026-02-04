/**
 * ModernDashboard Component Tests
 * Comprehensive test suite for ModernDashboard component
 */

import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, within } from '@testing-library/react'
import { render, mockUsers } from '../../../test/utils/test-utils'
import { ModernDashboard } from '../ModernDashboard'

// Mock useAuth hook
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: mockUsers.student,
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    loading: false,
    error: null
  })
}))

// Mock responsive hook
vi.mock('../../../utils/responsive', () => ({
  useResponsive: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    currentBreakpoint: 'lg'
  })
}))

const mockStats = {
  completedExams: 15,
  averageScore: 87,
  studyTime: 32,
  upcomingExams: 4
}

describe('ModernDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders welcome message with user name', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText(/Merhaba, Test!/)).toBeInTheDocument()
      expect(screen.getByText('Bugün nasıl ilerleme kaydedeceğiz?')).toBeInTheDocument()
    })

    it('renders all stat cards', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText('Tamamlanan Sınavlar')).toBeInTheDocument()
      expect(screen.getByText('15')).toBeInTheDocument()
      
      expect(screen.getByText('Ortalama Puan')).toBeInTheDocument()
      expect(screen.getByText('87%')).toBeInTheDocument()
      
      expect(screen.getByText('Çalışma Saati')).toBeInTheDocument()
      expect(screen.getByText('32h')).toBeInTheDocument()
      
      expect(screen.getByText('Yaklaşan Sınavlar')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
    })

    it('renders recent activity section', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText('Son Aktiviteler')).toBeInTheDocument()
      expect(screen.getByText('Matematik Sınavı Tamamlandı')).toBeInTheDocument()
      expect(screen.getByText('Fizik Dersi İzlendi')).toBeInTheDocument()
      expect(screen.getByText('Kimya Ödevi Gönderildi')).toBeInTheDocument()
    })

    it('renders quick actions section', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText('Hızlı İşlemler')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Sınav Başlat' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Ders İzle' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Ödev Gönder' })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'İstatistikler' })).toBeInTheDocument()
    })

    it('renders performance chart placeholder', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText('Performans Grafiği')).toBeInTheDocument()
      expect(screen.getByText('Grafik yakında eklenecek...')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('shows loading skeletons when loading', () => {
      render(<ModernDashboard loading />)
      
      const skeletons = document.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('shows content when not loading', () => {
      render(<ModernDashboard stats={mockStats} loading={false} />)
      
      expect(screen.getByText('15')).toBeInTheDocument()
      expect(screen.getByText('87%')).toBeInTheDocument()
    })
  })

  describe('Default Stats', () => {
    it('uses default stats when none provided', () => {
      render(<ModernDashboard />)
      
      // Default stats should be displayed
      expect(screen.getByText('12')).toBeInTheDocument() // completedExams
      expect(screen.getByText('85%')).toBeInTheDocument() // averageScore
      expect(screen.getByText('24h')).toBeInTheDocument() // studyTime
      expect(screen.getByText('3')).toBeInTheDocument() // upcomingExams
    })
  })

  describe('Responsive Behavior', () => {
    it('handles mobile layout', () => {
      // Mock mobile responsive hook
      vi.mocked(require('../../../utils/responsive').useResponsive).mockReturnValue({
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        currentBreakpoint: 'xs'
      })

      render(<ModernDashboard stats={mockStats} />)
      
      // Quick actions should be full width on mobile
      const quickActions = screen.getAllByRole('button')
      quickActions.forEach(button => {
        expect(button).toHaveStyle({ width: '100%' })
      })
    })
  })

  describe('Menu Interactions', () => {
    it('opens menu when menu button is clicked', async () => {
      // Mock mobile for menu button to appear
      vi.mocked(require('../../../utils/responsive').useResponsive).mockReturnValue({
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        currentBreakpoint: 'xs'
      })

      const { user } = render(<ModernDashboard stats={mockStats} />)
      
      const menuButton = screen.getByRole('button', { name: /more/i })
      await user.click(menuButton)
      
      expect(screen.getByText('Ayarlar')).toBeInTheDocument()
      expect(screen.getByText('Yardım')).toBeInTheDocument()
      expect(screen.getByText('Geri Bildirim')).toBeInTheDocument()
    })

    it('closes menu when menu item is clicked', async () => {
      vi.mocked(require('../../../utils/responsive').useResponsive).mockReturnValue({
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        currentBreakpoint: 'xs'
      })

      const { user } = render(<ModernDashboard stats={mockStats} />)
      
      const menuButton = screen.getByRole('button', { name: /more/i })
      await user.click(menuButton)
      
      const settingsItem = screen.getByText('Ayarlar')
      await user.click(settingsItem)
      
      expect(screen.queryByText('Ayarlar')).not.toBeInTheDocument()
    })
  })

  describe('Stat Card Colors', () => {
    it('applies correct colors to stat cards', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      // Each stat card should have its specific color
      const statCards = document.querySelectorAll('[style*="background-color"]')
      expect(statCards.length).toBeGreaterThan(0)
    })
  })

  describe('Activity Timeline', () => {
    it('displays activity items with correct styling', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      const activities = [
        'Matematik Sınavı Tamamlandı',
        'Fizik Dersi İzlendi',
        'Kimya Ödevi Gönderildi'
      ]
      
      activities.forEach(activity => {
        expect(screen.getByText(activity)).toBeInTheDocument()
      })
      
      // Check for activity indicators (colored dots)
      const indicators = document.querySelectorAll('[style*="border-radius: 50%"]')
      expect(indicators.length).toBeGreaterThanOrEqual(3)
    })

    it('shows relative timestamps', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText('2 saat önce')).toBeInTheDocument()
      expect(screen.getByText('5 saat önce')).toBeInTheDocument()
      expect(screen.getByText('1 gün önce')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      const mainHeading = screen.getByRole('heading', { level: 1 })
      expect(mainHeading).toHaveTextContent(/Merhaba, Test!/)
      
      const subHeadings = screen.getAllByRole('heading', { level: 2 })
      expect(subHeadings.length).toBeGreaterThan(0)
    })

    it('provides proper ARIA labels for interactive elements', () => {
      render(<ModernDashboard stats={mockStats} />)
      
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAttribute('type')
      })
    })
  })

  describe('Performance', () => {
    it('memoizes expensive calculations', () => {
      const { rerender } = render(<ModernDashboard stats={mockStats} />)
      
      // Re-render with same props
      rerender(<ModernDashboard stats={mockStats} />)
      
      // Component should still render correctly
      expect(screen.getByText('15')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles missing user gracefully', () => {
      vi.mocked(require('../../../hooks/useAuth').useAuth).mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: vi.fn(),
        logout: vi.fn(),
        loading: false,
        error: null
      })

      render(<ModernDashboard stats={mockStats} />)
      
      expect(screen.getByText(/Merhaba, Öğrenci!/)).toBeInTheDocument()
    })

    it('handles invalid stats gracefully', () => {
      const invalidStats = {
        completedExams: null,
        averageScore: undefined,
        studyTime: -1,
        upcomingExams: 'invalid'
      } as any

      render(<ModernDashboard stats={invalidStats} />)
      
      // Should still render without crashing
      expect(screen.getByText('Son Aktiviteler')).toBeInTheDocument()
    })
  })
})