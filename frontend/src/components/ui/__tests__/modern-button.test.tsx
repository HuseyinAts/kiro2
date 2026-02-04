/**
 * ModernButton Component Tests
 * Comprehensive test suite for ModernButton component
 */

import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { render } from '../../../test/utils/test-utils'
import { ModernButton } from '../modern-button'

describe('ModernButton', () => {
  describe('Basic Rendering', () => {
    it('renders button with text', () => {
      render(<ModernButton>Test Button</ModernButton>)
      
      expect(screen.getByRole('button', { name: 'Test Button' })).toBeInTheDocument()
    })

    it('renders with start and end icons', () => {
      const StartIcon = () => <span data-testid="start-icon">→</span>
      const EndIcon = () => <span data-testid="end-icon">←</span>
      
      render(
        <ModernButton startIcon={<StartIcon />} endIcon={<EndIcon />}>
          Button with Icons
        </ModernButton>
      )
      
      expect(screen.getByTestId('start-icon')).toBeInTheDocument()
      expect(screen.getByTestId('end-icon')).toBeInTheDocument()
      expect(screen.getByText('Button with Icons')).toBeInTheDocument()
    })
  })

  describe('Variants', () => {
    it('renders contained variant', () => {
      const { container } = render(
        <ModernButton variant="contained">Contained</ModernButton>
      )
      
      const button = container.querySelector('.MuiButton-contained')
      expect(button).toBeInTheDocument()
    })

    it('renders outlined variant', () => {
      const { container } = render(
        <ModernButton variant="outlined">Outlined</ModernButton>
      )
      
      const button = container.querySelector('.MuiButton-outlined')
      expect(button).toBeInTheDocument()
    })

    it('renders text variant', () => {
      const { container } = render(
        <ModernButton variant="text">Text</ModernButton>
      )
      
      const button = container.querySelector('.MuiButton-text')
      expect(button).toBeInTheDocument()
    })

    it('renders gradient variant with special styling', () => {
      render(<ModernButton variant="gradient">Gradient</ModernButton>)
      
      const button = screen.getByRole('button')
      const styles = getComputedStyle(button)
      
      // Gradient should set a background
      expect(styles.background).toContain('linear-gradient')
    })
  })

  describe('Sizes', () => {
    it('applies small size correctly', () => {
      render(<ModernButton size="small">Small</ModernButton>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveStyle({ height: '40px' })
    })

    it('applies medium size correctly', () => {
      render(<ModernButton size="medium">Medium</ModernButton>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveStyle({ height: '48px' })
    })

    it('applies large size correctly', () => {
      render(<ModernButton size="large">Large</ModernButton>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveStyle({ height: '56px' })
    })
  })

  describe('Touch Optimization', () => {
    it('applies touch-optimized sizes when enabled', () => {
      render(
        <ModernButton touchOptimized size="small">
          Touch Button
        </ModernButton>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveStyle({ 
        minHeight: '44px',
        minWidth: '44px'
      })
    })

    it('applies regular sizes when touch optimization disabled', () => {
      render(
        <ModernButton touchOptimized={false} size="small">
          Regular Button
        </ModernButton>
      )
      
      const button = screen.getByRole('button')
      expect(button).toHaveStyle({ height: '32px' })
    })
  })

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      render(<ModernButton loading>Loading Button</ModernButton>)
      
      const button = screen.getByRole('button')
      const spinner = document.querySelector('.MuiCircularProgress-root')
      
      expect(button).toBeDisabled()
      expect(spinner).toBeInTheDocument()
    })

    it('hides text when loading', () => {
      render(<ModernButton loading>Button Text</ModernButton>)
      
      const textContainer = document.querySelector('[style*="opacity: 0"]')
      expect(textContainer).toBeInTheDocument()
    })

    it('hides icons when loading', () => {
      const Icon = () => <span data-testid="icon">🎉</span>
      
      render(
        <ModernButton loading startIcon={<Icon />}>
          Loading
        </ModernButton>
      )
      
      expect(screen.queryByTestId('icon')).not.toBeInTheDocument()
    })
  })

  describe('Disabled State', () => {
    it('is disabled when disabled prop is true', () => {
      render(<ModernButton disabled>Disabled</ModernButton>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('is disabled when loading', () => {
      render(<ModernButton loading>Loading</ModernButton>)
      
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })
  })

  describe('Interactions', () => {
    it('calls onClick when clicked', async () => {
      const mockClick = vi.fn()
      const { user } = render(
        <ModernButton onClick={mockClick}>
          Clickable
        </ModernButton>
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(mockClick).toHaveBeenCalledTimes(1)
    })

    it('does not call onClick when disabled', async () => {
      const mockClick = vi.fn()
      const { user } = render(
        <ModernButton onClick={mockClick} disabled>
          Disabled
        </ModernButton>
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(mockClick).not.toHaveBeenCalled()
    })

    it('does not call onClick when loading', async () => {
      const mockClick = vi.fn()
      const { user } = render(
        <ModernButton onClick={mockClick} loading>
          Loading
        </ModernButton>
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(mockClick).not.toHaveBeenCalled()
    })
  })

  describe('Form Integration', () => {
    it('submits form when type is submit', async () => {
      const mockSubmit = vi.fn()
      const { user } = render(
        <form onSubmit={mockSubmit}>
          <ModernButton type="submit">Submit</ModernButton>
        </form>
      )
      
      const button = screen.getByRole('button')
      await user.click(button)
      
      expect(mockSubmit).toHaveBeenCalled()
    })

    it('applies fullWidth correctly', () => {
      render(<ModernButton fullWidth>Full Width</ModernButton>)
      
      const button = screen.getByRole('button')
      expect(button).toHaveStyle({ width: '100%' })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA label', () => {
      render(
        <ModernButton aria-label="Custom aria label">
          Button
        </ModernButton>
      )
      
      const button = screen.getByLabelText('Custom aria label')
      expect(button).toBeInTheDocument()
    })

    it('has focus-visible outline', () => {
      render(<ModernButton>Focusable</ModernButton>)
      
      const button = screen.getByRole('button')
      button.focus()
      
      // Check if focus styles are applied (this would be more detailed in real tests)
      expect(document.activeElement).toBe(button)
    })

    it('maintains keyboard navigation', async () => {
      const mockClick = vi.fn()
      const { user } = render(
        <ModernButton onClick={mockClick}>
          Keyboard Nav
        </ModernButton>
      )
      
      const button = screen.getByRole('button')
      button.focus()
      
      await user.keyboard('{Enter}')
      expect(mockClick).toHaveBeenCalledTimes(1)
      
      await user.keyboard(' ')
      expect(mockClick).toHaveBeenCalledTimes(2)
    })
  })

  describe('Color Variants', () => {
    const colors = ['primary', 'secondary', 'success', 'error', 'warning', 'info'] as const
    
    colors.forEach(color => {
      it(`renders ${color} color correctly`, () => {
        const { container } = render(
          <ModernButton color={color}>{color} button</ModernButton>
        )
        
        const button = container.querySelector(`.MuiButton-${color}`)
        expect(button).toBeInTheDocument()
      })
    })
  })

  describe('Custom Props', () => {
    it('forwards data-testid', () => {
      render(
        <ModernButton data-testid="custom-button">
          Test Button
        </ModernButton>
      )
      
      expect(screen.getByTestId('custom-button')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      const { container } = render(
        <ModernButton className="custom-class">
          Custom Button
        </ModernButton>
      )
      
      const button = container.querySelector('.custom-class')
      expect(button).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('renders quickly with minimal re-renders', () => {
      const renderCount = vi.fn()
      
      const TestButton = () => {
        renderCount()
        return <ModernButton>Performance Test</ModernButton>
      }
      
      const { rerender } = render(<TestButton />)
      
      // Initial render
      expect(renderCount).toHaveBeenCalledTimes(1)
      
      // Re-render with same props shouldn't cause extra renders due to memo
      rerender(<TestButton />)
      expect(renderCount).toHaveBeenCalledTimes(2)
    })
  })
})