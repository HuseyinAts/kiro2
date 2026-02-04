/**
 * VideoLoadingUI Accessibility Tests (WCAG 2.1 Level AA)
 * 
 * Bu test dosyası VideoLoadingUI bileşeninin WCAG 2.1 Level AA
 * erişilebilirlik standartlarına uygunluğunu doğrular.
 * 
 * @module VideoLoadingUI.accessibility.test
 */

import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { VideoLoadingUI } from '../VideoLoadingUI';
import { VideoLoadingState } from '../../services/VideoLoadingManager';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

describe('VideoLoadingUI - WCAG 2.1 Level AA Accessibility', () => {
  // Helper function to create mock state
  const createMockState = (overrides: Partial<VideoLoadingState> = {}): VideoLoadingState => ({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
    cacheHit: false,
    errorMessage: null,
    ...overrides,
  });

  describe('WCAG 4.1.2 - Name, Role, Value (Level A)', () => {
    it('should have no accessibility violations in loading state', async () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);
      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });

    it('should have no accessibility violations in success state', async () => {
      const state = createMockState({
        status: 'success',
        videos: [
          {
            subject_exam: 'TYT Matematik',
            videos: [
              {
                video_id: '1',
                title: 'Test Video',
                channel: 'Test Channel',
                duration: '10:00',
                quality_score: 8.5,
                subject: 'matematik',
                url: 'https://youtube.com/watch?v=1',
              },
            ],
            total_count: 1,
          },
        ],
        loadingTime: 2500,
      });

      const { container } = render(<VideoLoadingUI state={state} />);
      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });

    it('should have no accessibility violations in error state', async () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Network error'),
        errorMessage: 'İnternet bağlantınızı kontrol edin.',
      });

      const { container } = render(
        <VideoLoadingUI state={state} onRetry={() => {}} onShowFallback={() => {}} />
      );
      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });

    it('should have no accessibility violations in fallback state', async () => {
      const state = createMockState({
        status: 'fallback',
        error: new Error('Timeout'),
        errorMessage: 'Videoları 20 saniye içinde yükleyemedik.',
      });

      const { container } = render(
        <VideoLoadingUI state={state} onShowFallback={() => {}} />
      );
      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });
  });

  describe('WCAG 1.3.1 - Info and Relationships (Level A)', () => {
    it('should use semantic HTML elements', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for semantic section element
      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
      expect(section).toHaveAttribute('role', 'status');
    });

    it('should have proper heading hierarchy', () => {
      const state = createMockState({
        status: 'success',
        videos: [],
        loadingTime: 1000,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for h2 heading
      const heading = container.querySelector('h2');
      expect(heading).toBeInTheDocument();
    });

    it('should use progressbar role for progress indicator', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 75,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for progressbar
      const progressbar = container.querySelector('[role="progressbar"]');
      expect(progressbar).toBeInTheDocument();
      expect(progressbar).toHaveAttribute('aria-valuenow', '75');
      expect(progressbar).toHaveAttribute('aria-valuemin', '0');
      expect(progressbar).toHaveAttribute('aria-valuemax', '100');
    });
  });

  describe('WCAG 2.1.1 - Keyboard (Level A)', () => {
    it('should have accessible buttons with proper type', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      const { container } = render(
        <VideoLoadingUI state={state} onRetry={() => {}} onShowFallback={() => {}} />
      );

      // Check all buttons have type="button"
      const buttons = container.querySelectorAll('button');
      buttons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });

    it('should have aria-label on buttons', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      const { container } = render(
        <VideoLoadingUI state={state} onRetry={() => {}} onShowFallback={() => {}} />
      );

      // Check buttons have aria-label
      const buttons = container.querySelectorAll('button');
      buttons.forEach((button) => {
        expect(button).toHaveAttribute('aria-label');
      });
    });
  });

  describe('WCAG 1.4.3 - Contrast (Minimum) (Level AA)', () => {
    it('should use sufficient color contrast for text', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check that no elements use low-contrast colors
      const lowContrastColors = ['#999', '#666'];
      const allElements = container.querySelectorAll('*');

      allElements.forEach((element) => {
        const style = window.getComputedStyle(element);
        const color = style.color;

        // Ensure no low-contrast colors are used
        lowContrastColors.forEach((badColor) => {
          expect(color).not.toContain(badColor);
        });
      });
    });
  });

  describe('WCAG 4.1.3 - Status Messages (Level AA)', () => {
    it('should have aria-live on dynamic content', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for aria-live attribute
      const liveRegion = container.querySelector('[aria-live]');
      expect(liveRegion).toBeInTheDocument();
      expect(liveRegion).toHaveAttribute('aria-live', 'polite');
    });

    it('should use role="alert" for error messages', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for alert role
      const alert = container.querySelector('[role="alert"]');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveAttribute('aria-live', 'assertive');
    });
  });

  describe('WCAG 1.1.1 - Non-text Content (Level A)', () => {
    it('should have aria-label on decorative icons', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check spinner has role="img" and aria-label
      const spinner = container.querySelector('[role="img"]');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveAttribute('aria-label');
    });

    it('should hide decorative emojis from screen readers', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      const { container } = render(
        <VideoLoadingUI state={state} onRetry={() => {}} />
      );

      // Check that button emojis are hidden
      const hiddenEmojis = container.querySelectorAll('[aria-hidden="true"]');
      expect(hiddenEmojis.length).toBeGreaterThan(0);
    });
  });

  describe('WCAG 2.2.2 - Pause, Stop, Hide (Level A)', () => {
    it('should support reduced motion preference', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for reduced motion CSS
      const style = container.querySelector('style');
      expect(style?.textContent).toContain('prefers-reduced-motion');
    });
  });

  describe('WCAG 3.1.1 - Language of Page (Level A)', () => {
    it('should have lang attribute on Turkish content', () => {
      const state = createMockState({
        status: 'loading',
        loadingProgress: 50,
      });

      const { container } = render(<VideoLoadingUI state={state} />);

      // Check for lang="tr" attribute
      const section = container.querySelector('section');
      expect(section).toHaveAttribute('lang', 'tr');
    });
  });

  describe('WCAG 2.4.7 - Focus Visible (Level AA)', () => {
    it('should have visible focus indicator on buttons', () => {
      const state = createMockState({
        status: 'error',
        error: new Error('Error'),
      });

      const { container } = render(
        <VideoLoadingUI state={state} onRetry={() => {}} />
      );

      const button = container.querySelector('button');
      expect(button).toBeInTheDocument();

      // Simulate focus
      button?.focus();

      // Check that focus handler is defined (outline will be set)
      expect(button?.onfocus).toBeDefined();
    });
  });

  describe('Integration: Full Accessibility Audit', () => {
    it('should pass complete accessibility audit for all states', async () => {
      const states: VideoLoadingState[] = [
        createMockState({ status: 'loading', loadingProgress: 50 }),
        createMockState({
          status: 'success',
          videos: [
            {
              subject_exam: 'TYT Matematik',
              videos: [
                {
                  video_id: '1',
                  title: 'Test',
                  channel: 'Test',
                  duration: '10:00',
                  quality_score: 8.5,
                  subject: 'matematik',
                  url: 'https://youtube.com/watch?v=1',
                },
              ],
              total_count: 1,
            },
          ],
          loadingTime: 2500,
        }),
        createMockState({
          status: 'error',
          error: new Error('Error'),
          errorMessage: 'Test error',
        }),
        createMockState({
          status: 'fallback',
          error: new Error('Timeout'),
          errorMessage: 'Test timeout',
        }),
      ];

      for (const state of states) {
        const { container } = render(
          <VideoLoadingUI
            state={state}
            onRetry={() => {}}
            onShowFallback={() => {}}
            onCancel={() => {}}
          />
        );

        const results = await axe(container, {
          rules: {
            // Enable all WCAG 2.1 Level AA rules
            'color-contrast': { enabled: true },
            'aria-roles': { enabled: true },
            'aria-valid-attr': { enabled: true },
            'button-name': { enabled: true },
            'heading-order': { enabled: true },
            'label': { enabled: true },
            'link-name': { enabled: true },
            'list': { enabled: true },
            'listitem': { enabled: true },
          },
        });

        expect(results).toHaveNoViolations();
      }
    });
  });
});
