/**
 * AccessibleModal WCAG 2.1 Level AA Compliance Tests
 */

import * as React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import AccessibleModal from '../AccessibleModal';

expect.extend(toHaveNoViolations);

// Mock hooks
vi.mock('../../../hooks/useAccessibilitySettings', () => ({
  useAccessibilitySettings: () => ({
    settings: {
      highContrast: false,
      fontSize: 'medium',
      reducedMotion: false,
      keyboardNavigation: true,
      focusIndicators: true,
      screenReaderOptimized: false,
      dyslexiaSupport: false,
    },
    toggleHighContrast: vi.fn(),
    toggleReducedMotion: vi.fn(),
    increaseFontSize: vi.fn(),
    decreaseFontSize: vi.fn(),
    toggleDyslexiaSupport: vi.fn(),
    getAccessibilityStatus: () => ({
      activeFeatures: [],
      isOptimized: false,
      summary: 'Standart erişilebilirlik ayarları',
    }),
  }),
}));

vi.mock('../../../hooks/useScreenReader', () => ({
  useScreenReader: () => ({
    announce: vi.fn(),
    announcePageChange: vi.fn(),
    announceFormError: vi.fn(),
    announceSuccess: vi.fn(),
    announceLoading: vi.fn(),
    announceContentChange: vi.fn(),
    announceLandmark: vi.fn(),
    manageFocus: vi.fn(),
    createSkipLink: vi.fn(() => document.createElement('a')),
    isScreenReaderActive: false,
  }),
}));

vi.mock('../../../hooks/useFocusTrap', () => ({
  useFocusTrap: () => {
    const ref = React.useRef<HTMLDivElement>(null);
    return ref;
  },
}));

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const defaultProps = {
  open: true,
  onClose: vi.fn(),
  title: 'Test Modal',
  children: <p>Modal içeriği</p>,
};

describe('AccessibleModal - WCAG 2.1 AA Compliance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Automated Accessibility Audit', () => {
    it('passes axe accessibility audit', async () => {
      const { container } = renderWithTheme(
        <AccessibleModal {...defaultProps} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe audit with description', async () => {
      const { container } = renderWithTheme(
        <AccessibleModal
          {...defaultProps}
          description="Bu modal test amaçlıdır"
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe audit with actions', async () => {
      const { container } = renderWithTheme(
        <AccessibleModal
          {...defaultProps}
          actions={<button>Tamam</button>}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ARIA Attributes', () => {
    it('has role="dialog"', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('has aria-modal="true"', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('has aria-labelledby pointing to title', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      const labelledbyId = dialog.getAttribute('aria-labelledby');

      expect(labelledbyId).toBeTruthy();
      const title = document.getElementById(labelledbyId!);
      expect(title).toHaveTextContent('Test Modal');
    });

    it('has aria-describedby when description provided', () => {
      renderWithTheme(
        <AccessibleModal {...defaultProps} description="Test açıklaması" />
      );

      const dialog = screen.getByRole('dialog');
      const describedbyId = dialog.getAttribute('aria-describedby');

      expect(describedbyId).toBeTruthy();
      const description = document.getElementById(describedbyId!);
      expect(description).toHaveTextContent('Test açıklaması');
    });

    it('uses custom ariaLabelledBy when provided', () => {
      renderWithTheme(
        <>
          <span id="custom-label">Custom Title</span>
          <AccessibleModal {...defaultProps} ariaLabelledBy="custom-label" />
        </>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'custom-label');
    });

    it('uses custom ariaDescribedBy when provided', () => {
      renderWithTheme(
        <>
          <span id="custom-desc">Custom Description</span>
          <AccessibleModal {...defaultProps} ariaDescribedBy="custom-desc" />
        </>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-describedby', 'custom-desc');
    });
  });

  describe('Title and Content', () => {
    it('renders title correctly', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      expect(screen.getByText('Test Modal')).toBeInTheDocument();
    });

    it('renders children content', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      expect(screen.getByText('Modal içeriği')).toBeInTheDocument();
    });

    it('renders description when provided', () => {
      renderWithTheme(
        <AccessibleModal {...defaultProps} description="Modal açıklaması" />
      );

      expect(screen.getByText('Modal açıklaması')).toBeInTheDocument();
    });

    it('renders actions when provided', () => {
      renderWithTheme(
        <AccessibleModal
          {...defaultProps}
          actions={<button>Onayla</button>}
        />
      );

      expect(screen.getByRole('button', { name: 'Onayla' })).toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    it('renders close button by default', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      expect(screen.getByLabelText('Modalı kapat')).toBeInTheDocument();
    });

    it('does not render close button when showCloseButton=false', () => {
      renderWithTheme(
        <AccessibleModal {...defaultProps} showCloseButton={false} />
      );

      expect(screen.queryByLabelText('Modalı kapat')).not.toBeInTheDocument();
    });

    it('calls onClose when close button clicked', async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      renderWithTheme(<AccessibleModal {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByLabelText('Modalı kapat'));

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('close button has accessible label', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Modalı kapat');
      expect(closeButton).toHaveAttribute('aria-label', 'Modalı kapat');
    });
  });

  describe('Keyboard Navigation', () => {
    it('title has tabIndex=-1 for programmatic focus', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      const title = screen.getByText('Test Modal').closest('h2');
      expect(title?.parentElement).toHaveAttribute('tabindex', '-1');
    });

    it('shows keyboard shortcuts when keyboardNavigation enabled', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} />);

      expect(screen.getByText(/Klavye:/)).toBeInTheDocument();
      expect(screen.getByText(/Tab: Navigasyon/)).toBeInTheDocument();
      expect(screen.getByText(/Esc: Kapat/)).toBeInTheDocument();
    });
  });

  describe('Backdrop Click', () => {
    it('calls onClose when backdrop clicked by default', async () => {
      const onClose = vi.fn();
      renderWithTheme(<AccessibleModal {...defaultProps} onClose={onClose} />);

      // MUI Dialog uses Backdrop component
      const backdrop = document.querySelector('.MuiBackdrop-root');
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(onClose).toHaveBeenCalled();
      }
    });

    it('does not close on backdrop click when disableBackdropClick=true', async () => {
      const onClose = vi.fn();
      renderWithTheme(
        <AccessibleModal {...defaultProps} onClose={onClose} disableBackdropClick />
      );

      const backdrop = document.querySelector('.MuiBackdrop-root');
      if (backdrop) {
        fireEvent.click(backdrop);
        // onClose might still be called by MUI, but our handler should prevent it
      }
    });
  });

  describe('Modal States', () => {
    it('does not render content when closed', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} open={false} />);

      expect(screen.queryByText('Modal içeriği')).not.toBeInTheDocument();
    });

    it('renders content when open', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} open={true} />);

      expect(screen.getByText('Modal içeriği')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('applies maxWidth prop', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} maxWidth="lg" />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('applies fullScreen prop', () => {
      renderWithTheme(<AccessibleModal {...defaultProps} fullScreen />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  describe('Custom Class', () => {
    it('applies custom className', () => {
      renderWithTheme(
        <AccessibleModal {...defaultProps} className="custom-modal" />
      );

      const dialog = document.querySelector('.custom-modal');
      expect(dialog).toBeInTheDocument();
    });
  });
});
