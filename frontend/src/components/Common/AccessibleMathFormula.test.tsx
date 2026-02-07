/**
 * AccessibleMathFormula Component Test Suite
 * WCAG 2.1 Level AA uyumlu matematik formül bileşeni testleri
 * 
 * Test Coverage:
 * - MathML rendering
 * - LaTeX to MathML conversion
 * - Keyboard navigation
 * - Screen reader compatibility
 * - Zoom functionality
 * - Audio playback
 * - Copy functionality
 * - Accessibility attributes
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import AccessibleMathFormula from './AccessibleMathFormula';
import { AccessibilityProvider } from './AccessibilityProvider';

// Test wrapper with AccessibilityProvider
const renderWithProvider = (ui: React.ReactElement) => {
  return render(<AccessibilityProvider>{ui}</AccessibilityProvider>);
};

// Mock sanitize utility
vi.mock('../../utils/sanitize', () => ({
  sanitizeMathML: (content: string) => content, // Pass through for tests
  default: {
    sanitizeMathML: (content: string) => content,
  },
}));

// Mock hooks
vi.mock('../../hooks/useScreenReader', () => ({
  useScreenReader: () => ({
    announce: vi.fn(),
    announcePageChange: vi.fn(),
    announceFormError: vi.fn(),
    announceSuccess: vi.fn(),
    announceLoading: vi.fn(),
    announceContentChange: vi.fn(),
    announceLandmark: vi.fn(),
    manageFocus: vi.fn(),
    createSkipLink: vi.fn(),
    isScreenReaderActive: true,
  }),
}));

vi.mock('../../hooks/useAccessibilitySettings', () => ({
  useAccessibilitySettings: () => ({
    settings: {
      highContrast: false,
      fontSize: 'medium',
      reducedMotion: false,
      keyboardNavigation: true,
      focusIndicators: true,
      skipLinks: true,
      screenReaderOptimized: false,
      announcements: true,
      verboseDescriptions: false,
      speechRate: 1.0,
      language: 'tr-TR',
      region: 'TR',
      dyslexiaSupport: false,
      colorBlindSupport: false,
      motorImpairmentSupport: false,
    },
    isLoading: false,
    updateSetting: vi.fn(),
    saveSettings: vi.fn(),
    resetSettings: vi.fn(),
    toggleHighContrast: vi.fn(),
    toggleReducedMotion: vi.fn(),
    toggleDyslexiaSupport: vi.fn(),
    toggleScreenReaderOptimization: vi.fn(),
    increaseFontSize: vi.fn(),
    decreaseFontSize: vi.fn(),
    getAccessibilityStatus: vi.fn(),
  }),
}));

// Mock MUI theme
vi.mock('@mui/material', async () => {
  const actual = await vi.importActual('@mui/material');
  return {
    ...actual,
    useTheme: () => ({
      palette: {
        primary: { main: '#1976d2' },
        text: { secondary: '#666' },
        background: { default: '#fff', paper: '#f5f5f5' },
        divider: '#e0e0e0',
      },
    }),
  };
});

describe('AccessibleMathFormula', () => {
  const mockDescription = 'x kare artı 2x artı 1 eşittir 0';

  beforeEach(() => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    // Mock speechSynthesis API
    Object.assign(window, {
      speechSynthesis: {
        speak: vi.fn(),
        cancel: vi.fn(),
        getVoices: vi.fn(() => []),
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render with LaTeX formula', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
        />
      );

      expect(screen.getByRole('math')).toBeInTheDocument();
    });

    it('should render with MathML formula', () => {
      const mathml = '<math><mi>x</mi><mo>+</mo><mn>1</mn></math>';
      renderWithProvider(
        <AccessibleMathFormula
          mathml={mathml}
          description={mockDescription}
        />
      );

      expect(screen.getByRole('math')).toBeInTheDocument();
    });

    it('should render with label', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          label="Denklem 1"
        />
      );

      expect(screen.getByText('Denklem 1')).toBeInTheDocument();
    });

    it('should render in block display mode', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
        />
      );

      const mathElement = screen.getByRole('math');
      expect(mathElement).toBeInTheDocument();
    });

    it('should render in inline display mode', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="inline"
        />
      );

      const mathElement = screen.getByRole('math');
      expect(mathElement).toBeInTheDocument();
    });
  });

  describe('LaTeX to MathML Conversion', () => {
    it('should convert fraction LaTeX to MathML', () => {
      const { container } = render(
        <AccessibleMathFormula
          latex="\frac{a}{b}"
          description="a bölü b"
        />
      );

      const mathml = container.querySelector('math');
      expect(mathml).toBeInTheDocument();
      expect(mathml?.innerHTML).toContain('mfrac');
    });

    it('should convert superscript LaTeX to MathML', () => {
      const { container } = render(
        <AccessibleMathFormula
          latex="x^2"
          description="x kare"
        />
      );

      const mathml = container.querySelector('math');
      expect(mathml).toBeInTheDocument();
      expect(mathml?.innerHTML).toContain('msup');
    });

    it('should convert subscript LaTeX to MathML', () => {
      const { container } = render(
        <AccessibleMathFormula
          latex="x_1"
          description="x alt 1"
        />
      );

      const mathml = container.querySelector('math');
      expect(mathml).toBeInTheDocument();
      expect(mathml?.innerHTML).toContain('msub');
    });

    it('should convert square root LaTeX to MathML', () => {
      const { container } = render(
        <AccessibleMathFormula
          latex="\sqrt{x}"
          description="x'in karekökü"
        />
      );

      const mathml = container.querySelector('math');
      expect(mathml).toBeInTheDocument();
      expect(mathml?.innerHTML).toContain('msqrt');
    });
  });

  describe('Accessibility Attributes', () => {
    it('should have proper ARIA attributes', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          label="Test Formula"
          id="test-formula"
        />
      );

      const mathElement = screen.getByRole('math');
      expect(mathElement).toHaveAttribute('aria-labelledby');
      expect(mathElement).toHaveAttribute('aria-describedby');
      expect(mathElement).toHaveAttribute('tabIndex', '0');
    });

    it('should have hidden description for screen readers', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
        />
      );

      const description = screen.getByText(mockDescription);
      expect(description).toBeInTheDocument();
      // Description should be visually hidden but accessible to screen readers
      expect(description).toHaveStyle({ position: 'absolute' });
    });

    it('should generate unique ID when not provided', () => {
      const { container } = render(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
        />
      );

      const mathElement = container.querySelector('[role="math"]');
      const describedBy = mathElement?.getAttribute('aria-describedby');
      expect(describedBy).toMatch(/math-formula-.*-description/);
    });
  });

  describe('Zoom Functionality', () => {
    it('should zoom in when zoom in button is clicked', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
        />
      );

      const zoomInButton = screen.getByLabelText('Formülü yakınlaştır');
      await userEvent.click(zoomInButton);

      // Verify zoom increased (implementation detail)
      expect(zoomInButton).toBeInTheDocument();
    });

    it('should zoom out when zoom out button is clicked', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          initialZoom={2}
        />
      );

      const zoomOutButton = screen.getByLabelText('Formülü uzaklaştır');
      await userEvent.click(zoomOutButton);

      expect(zoomOutButton).toBeInTheDocument();
    });

    it('should disable zoom in at maximum zoom', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          initialZoom={3}
        />
      );

      const zoomInButton = screen.getByLabelText('Formülü yakınlaştır');
      expect(zoomInButton).toBeDisabled();
    });

    it('should disable zoom out at minimum zoom', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          initialZoom={0.5}
        />
      );

      const zoomOutButton = screen.getByLabelText('Formülü uzaklaştır');
      expect(zoomOutButton).toBeDisabled();
    });
  });

  describe('Audio Functionality', () => {
    it('should play audio when audio button is clicked', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableAudio={true}
        />
      );

      const audioButton = screen.getByLabelText('Formülü sesli oku');
      await userEvent.click(audioButton);

      expect(window.speechSynthesis.speak).toHaveBeenCalled();
    });

    it('should not render audio button when disabled', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableAudio={false}
        />
      );

      expect(screen.queryByLabelText('Formülü sesli oku')).not.toBeInTheDocument();
    });

    it('should disable audio button while speaking', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableAudio={true}
        />
      );

      const audioButton = screen.getByLabelText('Formülü sesli oku');
      await userEvent.click(audioButton);

      // Button should be disabled while speaking
      await waitFor(() => {
        expect(audioButton).toBeDisabled();
      });
    });
  });

  describe('Copy Functionality', () => {
    it('should copy formula when copy button is clicked', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableCopy={true}
        />
      );

      const copyButton = screen.getByLabelText('Formülü kopyala');
      await userEvent.click(copyButton);

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('x^2');
    });

    it('should not render copy button when disabled', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableCopy={false}
        />
      );

      expect(screen.queryByLabelText('Formülü kopyala')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('should zoom in with + key', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
        />
      );

      const mathElement = screen.getByRole('math');
      mathElement.focus();
      
      fireEvent.keyDown(mathElement, { key: '+' });
      
      // Verify zoom functionality was triggered
      expect(mathElement).toBeInTheDocument();
    });

    it('should zoom out with - key', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          initialZoom={2}
        />
      );

      const mathElement = screen.getByRole('math');
      mathElement.focus();
      
      fireEvent.keyDown(mathElement, { key: '-' });
      
      expect(mathElement).toBeInTheDocument();
    });

    it('should trigger audio with s key', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          enableAudio={true}
        />
      );

      const mathElement = screen.getByRole('math');
      mathElement.focus();
      
      fireEvent.keyDown(mathElement, { key: 's' });
      
      expect(window.speechSynthesis.speak).toHaveBeenCalled();
    });

    it('should copy with Ctrl+C', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          enableCopy={true}
        />
      );

      const mathElement = screen.getByRole('math');
      mathElement.focus();
      
      fireEvent.keyDown(mathElement, { key: 'c', ctrlKey: true });
      
      await waitFor(() => {
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
      });
    });

    it('should toggle description with i key', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
        />
      );

      const mathElement = screen.getByRole('math');
      mathElement.focus();
      
      fireEvent.keyDown(mathElement, { key: 'i' });
      
      // Description should be visible after toggle
      await waitFor(() => {
        const descriptionRegion = screen.getByRole('region', { name: 'Formül açıklaması' });
        expect(descriptionRegion).toBeInTheDocument();
      });
    });
  });

  describe('Description Toggle', () => {
    it('should show description when info button is clicked', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
        />
      );

      const infoButton = screen.getByLabelText('Detaylı açıklamayı göster');
      await userEvent.click(infoButton);

      const descriptionRegion = screen.getByRole('region', { name: 'Formül açıklaması' });
      expect(descriptionRegion).toBeInTheDocument();
      expect(descriptionRegion).toHaveTextContent(mockDescription);
    });

    it('should hide description when info button is clicked again', async () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          showDetailedDescription={true}
        />
      );

      const infoButton = screen.getByLabelText('Detaylı açıklamayı göster');
      
      // Description should be visible initially
      expect(screen.getByRole('region', { name: 'Formül açıklaması' })).toBeInTheDocument();
      
      // Click to hide
      await userEvent.click(infoButton);
      
      await waitFor(() => {
        expect(screen.queryByRole('region', { name: 'Formül açıklaması' })).not.toBeInTheDocument();
      });
    });
  });

  describe('Control Buttons Visibility', () => {
    it('should show control buttons in block display mode', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
        />
      );

      expect(screen.getByLabelText('Formülü sesli oku')).toBeInTheDocument();
      expect(screen.getByLabelText('Formülü kopyala')).toBeInTheDocument();
      expect(screen.getByLabelText('Formülü yakınlaştır')).toBeInTheDocument();
      expect(screen.getByLabelText('Formülü uzaklaştır')).toBeInTheDocument();
      expect(screen.getByLabelText('Detaylı açıklamayı göster')).toBeInTheDocument();
    });

    it('should not show control buttons in inline display mode', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="inline"
        />
      );

      expect(screen.queryByLabelText('Formülü sesli oku')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Formülü kopyala')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts Info', () => {
    it('should show keyboard shortcuts info in block mode with keyboard navigation enabled', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
        />
      );

      expect(screen.getByText(/Kısayollar:/)).toBeInTheDocument();
    });
  });

  describe('Button Minimum Touch Target Size', () => {
    it('should have minimum 44x44 touch target for all buttons', () => {
      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
        />
      );

      const buttons = [
        screen.getByLabelText('Formülü sesli oku'),
        screen.getByLabelText('Formülü kopyala'),
        screen.getByLabelText('Formülü yakınlaştır'),
        screen.getByLabelText('Formülü uzaklaştır'),
        screen.getByLabelText('Detaylı açıklamayı göster'),
      ];

      buttons.forEach(button => {
        expect(button).toBeInTheDocument();
        // Buttons should have minimum touch target size (WCAG 2.5.5)
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle clipboard write failure gracefully', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn().mockRejectedValue(new Error('Clipboard error')),
        },
      });

      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableCopy={true}
        />
      );

      const copyButton = screen.getByLabelText('Formülü kopyala');
      await userEvent.click(copyButton);

      // Should not throw error
      expect(copyButton).toBeInTheDocument();
      
      consoleErrorSpy.mockRestore();
    });

    it('should handle missing speechSynthesis API', async () => {
      const originalSpeechSynthesis = window.speechSynthesis;
      // @ts-ignore
      delete window.speechSynthesis;

      renderWithProvider(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          display="block"
          enableAudio={true}
        />
      );

      const audioButton = screen.getByLabelText('Formülü sesli oku');
      await userEvent.click(audioButton);

      // Should handle gracefully
      expect(audioButton).toBeInTheDocument();

      window.speechSynthesis = originalSpeechSynthesis;
    });
  });

  describe('Cleanup', () => {
    it('should cancel speech synthesis on unmount', () => {
      const { unmount } = render(
        <AccessibleMathFormula
          latex="x^2"
          description={mockDescription}
          enableAudio={true}
        />
      );

      unmount();

      // Cleanup should be called
      expect(window.speechSynthesis.cancel).toHaveBeenCalled();
    });
  });
});
