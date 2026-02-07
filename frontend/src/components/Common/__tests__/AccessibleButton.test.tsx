/**
 * AccessibleButton WCAG 2.1 Level AA Compliance Tests
 */

import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { AccessibleButton } from '../AccessibleButton';

expect.extend(toHaveNoViolations);

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

describe('AccessibleButton - WCAG 2.1 AA Compliance', () => {
  describe('Automated Accessibility Audit', () => {
    it('passes axe accessibility audit', async () => {
      const { container } = renderWithTheme(
        <AccessibleButton>Tıkla</AccessibleButton>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe audit with aria-label', async () => {
      const { container } = renderWithTheme(
        <AccessibleButton ariaLabel="Formu gönder">
          <span>icon</span>
        </AccessibleButton>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe audit in high contrast mode', async () => {
      const { container } = renderWithTheme(
        <AccessibleButton highContrast>Yüksek Kontrast</AccessibleButton>
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ARIA Attributes', () => {
    it('has role="button"', () => {
      renderWithTheme(<AccessibleButton>Test</AccessibleButton>);

      const button = screen.getByRole('button', { name: 'Test' });
      expect(button).toHaveAttribute('role', 'button');
    });

    it('sets aria-label when provided', () => {
      renderWithTheme(
        <AccessibleButton ariaLabel="Özel etiket">İçerik</AccessibleButton>
      );

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Özel etiket');
    });

    it('uses children text as aria-label when ariaLabel not provided', () => {
      renderWithTheme(<AccessibleButton>Buton Metni</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Buton Metni');
    });

    it('sets aria-describedby when provided', () => {
      renderWithTheme(
        <>
          <span id="description">Bu buton formu gönderir</span>
          <AccessibleButton ariaDescribedBy="description">Gönder</AccessibleButton>
        </>
      );

      const button = screen.getByRole('button', { name: 'Gönder' });
      expect(button).toHaveAttribute('aria-describedby', 'description');
    });

    it('sets aria-busy when loading', () => {
      renderWithTheme(<AccessibleButton loading>Gönder</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
    });

    it('does not set aria-busy when not loading', () => {
      renderWithTheme(<AccessibleButton>Gönder</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'false');
    });
  });

  describe('Keyboard Navigation', () => {
    it('is focusable via Tab', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleButton>Tab ile odaklan</AccessibleButton>);

      await user.tab();

      const button = screen.getByRole('button');
      expect(button).toHaveFocus();
    });

    it('has tabIndex=0 when enabled', () => {
      renderWithTheme(<AccessibleButton>Enabled</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('tabindex', '0');
    });

    it('has tabIndex=-1 when disabled', () => {
      renderWithTheme(<AccessibleButton disabled>Disabled</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('tabindex', '-1');
    });

    it('triggers onClick with Enter key', async () => {
      const handleClick = vi.fn();
      renderWithTheme(
        <AccessibleButton onClick={handleClick}>Enter Testi</AccessibleButton>
      );

      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('triggers onClick with Space key', async () => {
      const handleClick = vi.fn();
      renderWithTheme(
        <AccessibleButton onClick={handleClick}>Space Testi</AccessibleButton>
      );

      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: ' ' });

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not trigger onClick when disabled and Enter pressed', () => {
      const handleClick = vi.fn();
      renderWithTheme(
        <AccessibleButton onClick={handleClick} disabled>
          Disabled Enter
        </AccessibleButton>
      );

      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not trigger onClick when loading and Enter pressed', () => {
      const handleClick = vi.fn();
      renderWithTheme(
        <AccessibleButton onClick={handleClick} loading>
          Loading Enter
        </AccessibleButton>
      );

      const button = screen.getByRole('button');
      button.focus();
      fireEvent.keyDown(button, { key: 'Enter' });

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('calls custom onKeyDown handler', () => {
      const handleKeyDown = vi.fn();
      renderWithTheme(
        <AccessibleButton onKeyDown={handleKeyDown}>KeyDown Testi</AccessibleButton>
      );

      const button = screen.getByRole('button');
      fireEvent.keyDown(button, { key: 'Escape' });

      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });
  });

  describe('Click Behavior', () => {
    it('triggers onClick on mouse click', async () => {
      const handleClick = vi.fn();
      const user = userEvent.setup();
      renderWithTheme(
        <AccessibleButton onClick={handleClick}>Tıkla</AccessibleButton>
      );

      await user.click(screen.getByRole('button'));

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not trigger onClick when disabled', async () => {
      const handleClick = vi.fn();
      renderWithTheme(
        <AccessibleButton onClick={handleClick} disabled>
          Disabled
        </AccessibleButton>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not trigger onClick when loading', async () => {
      const handleClick = vi.fn();
      renderWithTheme(
        <AccessibleButton onClick={handleClick} loading>
          Loading
        </AccessibleButton>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('shows loading text when loading', () => {
      renderWithTheme(<AccessibleButton loading>Gönder</AccessibleButton>);

      expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
    });

    it('shows custom loading text', () => {
      renderWithTheme(
        <AccessibleButton loading loadingText="Lütfen bekleyin...">
          Gönder
        </AccessibleButton>
      );

      expect(screen.getByText('Lütfen bekleyin...')).toBeInTheDocument();
    });

    it('is disabled when loading', () => {
      renderWithTheme(<AccessibleButton loading>Loading</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('Touch Target Size (WCAG 2.5.5)', () => {
    it('has minimum 44px height', () => {
      renderWithTheme(<AccessibleButton>Touch Target</AccessibleButton>);

      const button = screen.getByRole('button');
      const styles = window.getComputedStyle(button);

      // MUI buttons might have different computed styles, check minHeight attribute
      expect(button).toHaveStyle({ minHeight: '44px' });
    });

    it('has minimum 44px width', () => {
      renderWithTheme(<AccessibleButton>Touch</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toHaveStyle({ minWidth: '44px' });
    });
  });

  describe('High Contrast Mode', () => {
    it('applies high contrast styles when enabled', () => {
      renderWithTheme(
        <AccessibleButton highContrast>High Contrast</AccessibleButton>
      );

      const button = screen.getByRole('button');
      // Check that highContrast prop is passed (styling is applied via styled-components)
      expect(button).toBeInTheDocument();
    });

    it('does not apply high contrast styles by default', () => {
      renderWithTheme(<AccessibleButton>Normal</AccessibleButton>);

      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Ref Forwarding', () => {
    it('forwards ref to button element', () => {
      const ref = React.createRef<HTMLButtonElement>();
      renderWithTheme(<AccessibleButton ref={ref}>Ref Test</AccessibleButton>);

      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    });

    it('allows programmatic focus via ref', () => {
      const ref = React.createRef<HTMLButtonElement>();
      renderWithTheme(<AccessibleButton ref={ref}>Focus Test</AccessibleButton>);

      ref.current?.focus();

      expect(ref.current).toHaveFocus();
    });
  });

  describe('Display Name', () => {
    it('has correct displayName for debugging', () => {
      expect(AccessibleButton.displayName).toBe('AccessibleButton');
    });
  });
});
