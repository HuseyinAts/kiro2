/**
 * AccessibleForm WCAG 2.1 Level AA Compliance Tests
 */

import * as React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import AccessibleForm, { FormField } from '../AccessibleForm';

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
  }),
}));

const theme = createTheme();

const renderWithTheme = (component: React.ReactElement) => {
  return render(<ThemeProvider theme={theme}>{component}</ThemeProvider>);
};

const defaultFields: FormField[] = [
  {
    id: 'name',
    name: 'name',
    label: 'İsim',
    type: 'text',
    required: true,
    validation: { required: true },
  },
  {
    id: 'email',
    name: 'email',
    label: 'E-posta',
    type: 'email',
    required: true,
    validation: { required: true, email: true },
  },
];

const defaultProps = {
  fields: defaultFields,
  onSubmit: vi.fn(),
};

describe('AccessibleForm - WCAG 2.1 AA Compliance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Automated Accessibility Audit', () => {
    it('passes axe accessibility audit', async () => {
      const { container } = renderWithTheme(
        <AccessibleForm {...defaultProps} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe audit with title and description', async () => {
      const { container } = renderWithTheme(
        <AccessibleForm
          {...defaultProps}
          title="Kayıt Formu"
          description="Hesap oluşturmak için aşağıdaki alanları doldurun"
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('passes axe audit with password field', async () => {
      const fieldsWithPassword: FormField[] = [
        ...defaultFields,
        {
          id: 'password',
          name: 'password',
          label: 'Şifre',
          type: 'password',
          required: true,
        },
      ];

      const { container } = renderWithTheme(
        <AccessibleForm {...defaultProps} fields={fieldsWithPassword} />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe('ARIA Attributes', () => {
    it('has role="form"', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const form = screen.getByRole('form');
      expect(form).toBeInTheDocument();
    });

    it('has aria-labelledby pointing to title when provided', () => {
      renderWithTheme(
        <AccessibleForm {...defaultProps} title="Test Formu" />
      );

      const form = screen.getByRole('form');
      const labelledbyId = form.getAttribute('aria-labelledby');

      expect(labelledbyId).toBeTruthy();
      const title = document.getElementById(labelledbyId!);
      expect(title).toHaveTextContent('Test Formu');
    });

    it('has aria-describedby pointing to description when provided', () => {
      renderWithTheme(
        <AccessibleForm {...defaultProps} description="Form açıklaması" />
      );

      const form = screen.getByRole('form');
      const describedbyId = form.getAttribute('aria-describedby');

      expect(describedbyId).toBeTruthy();
      const description = document.getElementById(describedbyId!);
      expect(description).toHaveTextContent('Form açıklaması');
    });
  });

  describe('Form Labels', () => {
    it('all inputs have associated labels', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const nameInput = screen.getByLabelText(/İsim/);
      const emailInput = screen.getByLabelText(/E-posta/);

      expect(nameInput).toBeInTheDocument();
      expect(emailInput).toBeInTheDocument();
    });

    it('shows required indicator for required fields', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const nameLabel = screen.getByText('İsim');
      expect(nameLabel.parentElement).toHaveTextContent('*');
    });

    it('shows required indicator message', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      expect(screen.getByText(/işaretli alanlar zorunludur/)).toBeInTheDocument();
    });
  });

  describe('Input Validation', () => {
    it('shows error for empty required field on submit', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      expect(screen.getByText(/İsim alanı zorunludur/)).toBeInTheDocument();
    });

    it('shows error for invalid email format', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const emailInput = screen.getByLabelText(/E-posta/);
      await user.type(emailInput, 'invalid-email');
      fireEvent.blur(emailInput);

      await waitFor(() => {
        expect(screen.getByText(/Geçerli bir e-posta adresi giriniz/)).toBeInTheDocument();
      });
    });

    it('sets aria-invalid on invalid field', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      const nameInput = screen.getByLabelText(/İsim/);
      expect(nameInput).toHaveAttribute('aria-invalid', 'true');
    });

    it('validates minLength', async () => {
      const fieldsWithMinLength: FormField[] = [
        {
          id: 'name',
          name: 'name',
          label: 'İsim',
          type: 'text',
          validation: { minLength: 3 },
        },
      ];

      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm fields={fieldsWithMinLength} onSubmit={vi.fn()} />);

      const input = screen.getByLabelText(/İsim/);
      await user.type(input, 'ab');
      fireEvent.blur(input);

      await waitFor(() => {
        expect(screen.getByText(/en az 3 karakter/)).toBeInTheDocument();
      });
    });

    it('validates maxLength', async () => {
      const fieldsWithMaxLength: FormField[] = [
        {
          id: 'name',
          name: 'name',
          label: 'İsim',
          type: 'text',
          validation: { maxLength: 5 },
        },
      ];

      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm fields={fieldsWithMaxLength} onSubmit={vi.fn()} />);

      const input = screen.getByLabelText(/İsim/);
      await user.type(input, 'abcdefgh');
      fireEvent.blur(input);

      await waitFor(() => {
        expect(screen.getByText(/en fazla 5 karakter/)).toBeInTheDocument();
      });
    });
  });

  describe('Error Summary', () => {
    it('shows error count on form submission', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      expect(screen.getByText(/Form Hataları \(2\)/)).toBeInTheDocument();
    });

    it('error summary has role="alert"', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('clicking error link focuses the field', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      const errorLink = screen.getByRole('button', { name: /İsim: İsim alanı zorunludur/ });
      await user.click(errorLink);

      const nameInput = screen.getByLabelText(/İsim/);
      expect(nameInput).toHaveFocus();
    });
  });

  describe('Password Field', () => {
    it('renders password toggle button', () => {
      const fieldsWithPassword: FormField[] = [
        {
          id: 'password',
          name: 'password',
          label: 'Şifre',
          type: 'password',
        },
      ];

      renderWithTheme(<AccessibleForm fields={fieldsWithPassword} onSubmit={vi.fn()} />);

      expect(screen.getByLabelText('Şifreyi göster')).toBeInTheDocument();
    });

    it('toggles password visibility', async () => {
      const fieldsWithPassword: FormField[] = [
        {
          id: 'password',
          name: 'password',
          label: 'Şifre',
          type: 'password',
        },
      ];

      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm fields={fieldsWithPassword} onSubmit={vi.fn()} />);

      const passwordInput = screen.getByLabelText(/Şifre/) as HTMLInputElement;
      expect(passwordInput.type).toBe('password');

      await user.click(screen.getByLabelText('Şifreyi göster'));

      expect(passwordInput.type).toBe('text');
      expect(screen.getByLabelText('Şifreyi gizle')).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('calls onSubmit with form data when valid', async () => {
      const onSubmit = vi.fn();
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} onSubmit={onSubmit} />);

      await user.type(screen.getByLabelText(/İsim/), 'Test User');
      await user.type(screen.getByLabelText(/E-posta/), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          name: 'Test User',
          email: 'test@example.com',
        });
      });
    });

    it('does not call onSubmit when form is invalid', async () => {
      const onSubmit = vi.fn();
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} onSubmit={onSubmit} />);

      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('shows loading state during submission', async () => {
      const onSubmit = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} onSubmit={onSubmit} />);

      await user.type(screen.getByLabelText(/İsim/), 'Test');
      await user.type(screen.getByLabelText(/E-posta/), 'test@example.com');
      await user.click(screen.getByRole('button', { name: 'Gönder' }));

      expect(screen.getByText('Gönderiliyor...')).toBeInTheDocument();
    });
  });

  describe('Form Reset', () => {
    it('clears form on reset', async () => {
      const user = userEvent.setup();
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const nameInput = screen.getByLabelText(/İsim/) as HTMLInputElement;
      await user.type(nameInput, 'Test');

      expect(nameInput.value).toBe('Test');

      // Mock window.confirm
      vi.spyOn(window, 'confirm').mockReturnValue(true);

      await user.click(screen.getByRole('button', { name: 'Sıfırla' }));

      expect(nameInput.value).toBe('');
    });

    it('reset button is disabled when form is empty', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const resetButton = screen.getByRole('button', { name: 'Sıfırla' });
      expect(resetButton).toBeDisabled();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('shows keyboard shortcut info', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      expect(screen.getByText(/Klavye Kısayolları/)).toBeInTheDocument();
      expect(screen.getByText(/Ctrl\+Enter: Gönder/)).toBeInTheDocument();
    });
  });

  describe('Touch Target Size (WCAG 2.5.5)', () => {
    it('inputs have minimum touch target size', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} />);

      const inputs = screen.getAllByRole('textbox');
      inputs.forEach(input => {
        expect(input.closest('.MuiInputBase-root')).toHaveStyle({ minHeight: '44px' });
      });
    });
  });

  describe('Helper Text', () => {
    it('displays helper text when provided', () => {
      const fieldsWithHelper: FormField[] = [
        {
          id: 'name',
          name: 'name',
          label: 'İsim',
          type: 'text',
          helperText: 'Adınızı ve soyadınızı girin',
        },
      ];

      renderWithTheme(<AccessibleForm fields={fieldsWithHelper} onSubmit={vi.fn()} />);

      expect(screen.getByText('Adınızı ve soyadınızı girin')).toBeInTheDocument();
    });
  });

  describe('Custom Labels', () => {
    it('uses custom submit label', () => {
      renderWithTheme(
        <AccessibleForm {...defaultProps} submitLabel="Kaydet" />
      );

      expect(screen.getByRole('button', { name: 'Kaydet' })).toBeInTheDocument();
    });

    it('uses custom reset label', async () => {
      const user = userEvent.setup();
      renderWithTheme(
        <AccessibleForm {...defaultProps} resetLabel="Temizle" />
      );

      // Type something to enable reset button
      await user.type(screen.getByLabelText(/İsim/), 'Test');

      expect(screen.getByRole('button', { name: 'Temizle' })).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('disables all inputs when disabled prop is true', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} disabled />);

      const inputs = screen.getAllByRole('textbox');
      inputs.forEach(input => {
        expect(input).toBeDisabled();
      });
    });

    it('disables buttons when disabled prop is true', () => {
      renderWithTheme(<AccessibleForm {...defaultProps} disabled />);

      expect(screen.getByRole('button', { name: 'Gönder' })).toBeDisabled();
    });
  });
});
