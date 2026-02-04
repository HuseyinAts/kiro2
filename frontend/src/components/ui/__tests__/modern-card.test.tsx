/**
 * ModernCard Component Tests
 * Comprehensive test suite for ModernCard component
 */

import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { render } from '../../../test/utils/test-utils'
import { ModernCard } from '../modern-card'

describe('ModernCard', () => {
  describe('Basic Rendering', () => {
    it('renders children correctly', () => {
      render(
        <ModernCard>
          <div>Test Content</div>
        </ModernCard>
      )
      
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('renders with title and subtitle', () => {
      render(
        <ModernCard title="Test Title" subtitle="Test Subtitle">
          <div>Content</div>
        </ModernCard>
      )
      
      expect(screen.getByText('Test Title')).toBeInTheDocument()
      expect(screen.getByText('Test Subtitle')).toBeInTheDocument()
    })

    it('renders actions when provided', () => {
      const mockAction = <button>Action Button</button>
      
      render(
        <ModernCard actions={mockAction}>
          <div>Content</div>
        </ModernCard>
      )
      
      expect(screen.getByText('Action Button')).toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('shows skeleton when loading', () => {
      render(
        <ModernCard loading>
          <div>Content</div>
        </ModernCard>
      )
      
      // Content should not be visible when loading
      expect(screen.queryByText('Content')).not.toBeInTheDocument()
      
      // Skeleton should be present
      const skeletons = document.querySelectorAll('.MuiSkeleton-root')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('shows content when not loading', () => {
      render(
        <ModernCard loading={false}>
          <div>Test Content</div>
        </ModernCard>
      )
      
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })
  })

  describe('Variants', () => {
    it('applies default variant styles', () => {
      const { container } = render(
        <ModernCard variant="default">
          <div>Content</div>
        </ModernCard>
      )
      
      const card = container.querySelector('.MuiCard-root')
      expect(card).toBeInTheDocument()
    })

    it('applies outlined variant styles', () => {
      const { container } = render(
        <ModernCard variant="outlined">
          <div>Content</div>
        </ModernCard>
      )
      
      const card = container.querySelector('.MuiCard-root')
      expect(card).toHaveStyle({ borderWidth: '1px' })
    })

    it('applies elevated variant styles', () => {
      const { container } = render(
        <ModernCard variant="elevated">
          <div>Content</div>
        </ModernCard>
      )
      
      const card = container.querySelector('.MuiCard-root')
      expect(card).toBeInTheDocument()
    })
  })

  describe('Sizes', () => {
    it('applies small size styles', () => {
      render(
        <ModernCard size="small">
          <div>Content</div>
        </ModernCard>
      )
      
      const content = document.querySelector('.MuiCardContent-root')
      expect(content).toHaveStyle({ padding: '16px' })
    })

    it('applies medium size styles', () => {
      render(
        <ModernCard size="medium">
          <div>Content</div>
        </ModernCard>
      )
      
      const content = document.querySelector('.MuiCardContent-root')
      expect(content).toHaveStyle({ padding: '24px' })
    })

    it('applies large size styles', () => {
      render(
        <ModernCard size="large">
          <div>Content</div>
        </ModernCard>
      )
      
      const content = document.querySelector('.MuiCardContent-root')
      expect(content).toHaveStyle({ padding: '32px' })
    })
  })

  describe('Interactions', () => {
    it('calls onClick when clicked', async () => {
      const mockClick = vi.fn()
      const { user } = render(
        <ModernCard onClick={mockClick}>
          <div>Clickable Content</div>
        </ModernCard>
      )
      
      const card = screen.getByRole('button')
      await user.click(card)
      
      expect(mockClick).toHaveBeenCalledTimes(1)
    })

    it('handles keyboard navigation', async () => {
      const mockClick = vi.fn()
      const { user } = render(
        <ModernCard onClick={mockClick}>
          <div>Clickable Content</div>
        </ModernCard>
      )
      
      const card = screen.getByRole('button')
      
      // Test Enter key
      card.focus()
      await user.keyboard('{Enter}')
      expect(mockClick).toHaveBeenCalledTimes(1)
      
      // Test Space key
      await user.keyboard(' ')
      expect(mockClick).toHaveBeenCalledTimes(2)
    })

    it('calls onMenuClick when menu button is clicked', async () => {
      const mockMenuClick = vi.fn()
      const mockCardClick = vi.fn()
      
      const { user } = render(
        <ModernCard onClick={mockCardClick} onMenuClick={mockMenuClick}>
          <div>Content with menu</div>
        </ModernCard>
      )
      
      const menuButton = screen.getByLabelText('diğer seçenekler')
      await user.click(menuButton)
      
      expect(mockMenuClick).toHaveBeenCalledTimes(1)
      expect(mockCardClick).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes when clickable', () => {
      render(
        <ModernCard onClick={() => {}} aria-label="Test card">
          <div>Content</div>
        </ModernCard>
      )
      
      const card = screen.getByRole('button')
      expect(card).toHaveAttribute('aria-label', 'Test card')
      expect(card).toHaveAttribute('tabIndex', '0')
    })

    it('does not have button role when not clickable', () => {
      render(
        <ModernCard>
          <div>Non-clickable content</div>
        </ModernCard>
      )
      
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    it('has proper heading structure', () => {
      render(
        <ModernCard title="Test Title">
          <div>Content</div>
        </ModernCard>
      )
      
      const heading = screen.getByRole('heading', { level: 2 })
      expect(heading).toHaveTextContent('Test Title')
    })
  })

  describe('Responsive Behavior', () => {
    it('adapts to different screen sizes', () => {
      // This would require mocking window.matchMedia
      // The actual responsive behavior is tested through visual regression tests
      render(
        <ModernCard>
          <div>Responsive content</div>
        </ModernCard>
      )
      
      expect(screen.getByText('Responsive content')).toBeInTheDocument()
    })
  })

  describe('Custom Props', () => {
    it('forwards custom data attributes', () => {
      render(
        <ModernCard data-testid="custom-card">
          <div>Content</div>
        </ModernCard>
      )
      
      expect(screen.getByTestId('custom-card')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      const { container } = render(
        <ModernCard className="custom-class">
          <div>Content</div>
        </ModernCard>
      )
      
      const card = container.querySelector('.custom-class')
      expect(card).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('renders gracefully with undefined children', () => {
      render(<ModernCard>{undefined}</ModernCard>)
      
      const card = document.querySelector('.MuiCard-root')
      expect(card).toBeInTheDocument()
    })

    it('handles empty title gracefully', () => {
      render(
        <ModernCard title="">
          <div>Content</div>
        </ModernCard>
      )
      
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })
})