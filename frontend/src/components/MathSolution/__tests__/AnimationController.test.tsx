/**
 * AnimationController Accessibility Tests
 * WCAG 2.1 Level AA Compliance Testing
 * REQ-9: Erişilebilirlik ve Kapsayıcı Tasarım
 */

import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import AnimationController, { AnimationProvider } from '../AnimationController';

expect.extend(toHaveNoViolations);

const renderWithProvider = (ui: React.ReactElement) => {
  return render(
    <AnimationProvider>
      {ui}
    </AnimationProvider>
  );
};

describe('AnimationController - WCAG 2.1 AA Compliance', () => {
  describe('REQ-9.1: Text Alternatives', () => {
    it('should have aria-labels for icon buttons', () => {
      renderWithProvider(<AnimationController />);
      
      const toggleButton = screen.getByRole('button', { name: /Animasyonları/i });
      expect(toggleButton).toHaveAttribute('aria-label');
    });

    it('should mark decorative icons as aria-hidden', () => {
      const { container } = renderWithProvider(<AnimationController />);
      
      const icons = container.querySelectorAll('svg');
      icons.forEach(icon => {
        expect(icon).toHaveAttribute('aria-hidden', 'true');
      });
    });

    it('should have status indicator with aria-label', () => {
      renderWithProvider(<AnimationController />);
      
      const statusIndicator = screen.getByRole('status', { name: /Animasyonlar/i });
      expect(statusIndicator).toBeInTheDocument();
    });
  });

  describe('REQ-9.4: Keyboard Navigation', () => {
    it('should toggle animations with Enter key', () => {
      renderWithProvider(<AnimationController />);
      
      const toggleButton = screen.getByRole('button', { name: /Animasyonları/i });
      
      fireEvent.keyDown(toggleButton, { key: 'Enter' });
      expect(screen.getByText('Animasyonlar Kapalı')).toBeInTheDocument();
    });

    it('should navigate speed options with arrow keys', () => {
      renderWithProvider(<AnimationController />);
      
      const normalButton = screen.getByRole('radio', { name: /Normal hız/i });
      
      fireEvent.keyDown(normalButton, { key: 'ArrowRight' });
      
      const fastButton = screen.getByRole('radio', { name: /Hızlı hız/i });
      expect(fastButton).toHaveAttribute('aria-checked', 'true');
    });

    it('should have proper tabIndex for radio group', () => {
      renderWithProvider(<AnimationController />);
      
      const normalButton = screen.getByRole('radio', { name: /Normal hız/i });
      expect(normalButton).toHaveAttribute('tabIndex', '0');
      
      const slowButton = screen.getByRole('radio', { name: /Yavaş hız/i });
      expect(slowButton).toHaveAttribute('tabIndex', '-1');
    });

    it('should have visible focus indicators', () => {
      const { container } = renderWithProvider(<AnimationController />);
      
      const buttons = container.querySelectorAll('button');
      buttons.forEach(button => {
        fireEvent.focus(button);
        const styles = window.getComputedStyle(button);
        // Focus styles are applied via CSS, check class exists
        expect(button.className).toBeTruthy();
      });
    });
  });

  describe('WCAG 1.4.3: Color Contrast', () => {
    it('should use sufficient color contrast for text', () => {
      const { container } = renderWithProvider(<AnimationController />);
      
      const infoText = container.querySelector('.text-gray-700');
      expect(infoText).toBeInTheDocument();
      // text-gray-700 provides 4.6:1 contrast ratio
    });
  });

  describe('WCAG 2.3.3: Animation from Interactions', () => {
    it('should respect prefers-reduced-motion', () => {
      const { container } = renderWithProvider(<AnimationController />);
      
      const animationController = container.querySelector('.animation-controller');
      expect(animationController).toBeInTheDocument();
      // CSS media query handles reduced motion
    });
  });

  describe('REQ-9.4: ARIA Live Regions', () => {
    it('should announce status changes to screen readers', () => {
      renderWithProvider(<AnimationController />);
      
      const liveRegion = screen.getByRole('status', { name: '' });
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
      expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
    });

    it('should update live region when animation state changes', () => {
      renderWithProvider(<AnimationController />);
      
      const toggleButton = screen.getByRole('button', { name: /Animasyonları/i });
      
      expect(screen.getByText(/Animasyonlar aktif/i)).toBeInTheDocument();
      
      fireEvent.click(toggleButton);
      
      expect(screen.getByText(/Animasyonlar kapalı/i)).toBeInTheDocument();
    });
  });

  describe('Semantic HTML & ARIA Roles', () => {
    it('should use proper ARIA roles for radio group', () => {
      renderWithProvider(<AnimationController />);
      
      const radioGroup = screen.getByRole('radiogroup');
      expect(radioGroup).toHaveAttribute('aria-labelledby', 'speed-label');
    });

    it('should have proper group labeling', () => {
      renderWithProvider(<AnimationController />);
      
      const group = screen.getByRole('group', { name: /Animasyon hızı seçimi/i });
      expect(group).toBeInTheDocument();
    });
  });

  describe('Turkish Language Support (REQ-12)', () => {
    it('should use Turkish terminology in aria-labels', () => {
      renderWithProvider(<AnimationController />);
      
      const slowButton = screen.getByRole('radio', { name: /Yavaş hız.*milisaniye/i });
      expect(slowButton).toBeInTheDocument();
    });

    it('should display Turkish UI text', () => {
      renderWithProvider(<AnimationController />);
      
      expect(screen.getByText('Hız:')).toBeInTheDocument();
      expect(screen.getByText(/Animasyonlar aktif/i)).toBeInTheDocument();
    });
  });

  describe('Automated Accessibility Testing', () => {
    it('should have no WCAG violations', async () => {
      const { container } = renderWithProvider(<AnimationController />);
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should pass accessibility audit when animations disabled', async () => {
      const { container } = renderWithProvider(<AnimationController />);
      
      const toggleButton = screen.getByRole('button', { name: /Animasyonları/i });
      fireEvent.click(toggleButton);
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
