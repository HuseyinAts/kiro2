/**
 * Visual Timer Component Tests
 * 
 * WCAG 2.1 Level AA compliance tests for VisualTimer component
 * Requirements: REQ-9.1 - REQ-9.5, REQ-52.6 - REQ-52.10
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import VisualTimer from '../VisualTimer';

expect.extend(toHaveNoViolations);

// Mock fetch
global.fetch = vi.fn();

const mockTimerData = {
  session_id: 'test-session-123',
  remaining_seconds: 1500, // 25 minutes
  total_seconds: 1500,
  progress_percentage: 100,
  time_display: '25:00',
  is_active: true,
  session_type: 'work' as const,
  color_scheme: {
    primary: '#e53e3e',
    secondary: '#fc8181',
    background: '#fff5f5'
  }
};

describe('VisualTimer - WCAG 2.1 Level AA Compliance', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockTimerData
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('1.1.1 Non-text Content', () => {
    it('should have descriptive aria-label for timer role', async () => {
      render(<VisualTimer sessionId="test-123" />);
      
      await waitFor(() => {
        const timer = screen.getByRole('timer');
        expect(timer).toHaveAttribute('aria-label', 'Çalışma zamanlayıcısı');
      });
    });

    it('should have aria-label for progress ring', async () => {
      render(<VisualTimer sessionId="test-123" />);
      
      await waitFor(() => {
        const progressRing = screen.getByRole('img');
        expect(progressRing).toHaveAttribute('aria-label', expect.stringContaining('İlerleme'));
      });
    });
  });

  describe('Automated Accessibility Testing', () => {
    it('should have no WCAG violations (axe-core)', async () => {
      const { container } = render(<VisualTimer sessionId="test-123" />);
      
      await waitFor(() => {
        expect(screen.getByRole('timer')).toBeInTheDocument();
      });
      
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
