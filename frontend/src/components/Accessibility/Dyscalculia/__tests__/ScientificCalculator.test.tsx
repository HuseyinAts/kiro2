/**
 * Scientific Calculator Tests
 * WCAG 2.1 Level AA Compliance Testing
 */

import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import ScientificCalculator from '../ScientificCalculator';

expect.extend(toHaveNoViolations);

describe('ScientificCalculator', () => {
  describe('WCAG 2.1 Level AA Compliance', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<ScientificCalculator />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper ARIA labels for all buttons', () => {
      render(<ScientificCalculator />);
      
      // Sayı tuşları
      expect(screen.getByLabelText('0')).toBeInTheDocument();
      expect(screen.getByLabelText('1')).toBeInTheDocument();
      expect(screen.getByLabelText('9')).toBeInTheDocument();
      
      // İşlem tuşları
      expect(screen.getByLabelText('Toplama')).toBeInTheDocument();
      expect(screen.getByLabelText('Çıkarma')).toBeInTheDocument();
      expect(screen.getByLabelText('Çarpma')).toBeInTheDocument();
      expect(screen.getByLabelText('Bölme')).toBeInTheDocument();
      
      // Bilimsel fonksiyonlar
      expect(screen.getByLabelText('Sinüs')).toBeInTheDocument();
      expect(screen.getByLabelText('Kosinüs')).toBeInTheDocument();
      expect(screen.getByLabelText('Karekök')).toBeInTheDocument();
      expect(screen.getByLabelText('Logaritma taban 10')).toBeInTheDocument();
    });

    it('should have role="application" for calculator', () => {
      render(<ScientificCalculator />);
      const calculator = screen.getByRole('application', { name: 'Bilimsel Hesap Makinesi' });
      expect(calculator).toBeInTheDocument();
    });

    it('should have aria-live region for display updates', () => {
      render(<ScientificCalculator />);
      const display = screen.getByRole('application').querySelector('[aria-live="polite"]');
      expect(display).toBeInTheDocument();
      expect(display).toHaveAttribute('aria-atomic', 'true');
    });

    it('should support keyboard navigation', async () => {
      render(<ScientificCalculator />);
      const user = userEvent.setup();
      
      // Tab navigation
      await user.tab();
      expect(document.activeElement).toHaveAttribute('aria-label');
      
      // Multiple tabs
      await user.tab();
      await user.tab();
      expect(document.activeElement).toHaveAttribute('aria-label');
    });

    it('should have visible focus indicators', async () => {
      render(<ScientificCalculator />);
      const button = screen.getByLabelText('1');
      
      button.focus();
      
      const styles = window.getComputedStyle(button);
      expect(styles.outline).toBeTruthy();
    });
  });

  describe('Basic Arithmetic Operations', () => {
    it('should display initial value of 0', () => {
      render(<ScientificCalculator />);
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('0');
    });

    it('should handle number input', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('1'));
      fireEvent.click(screen.getByLabelText('2'));
      fireEvent.click(screen.getByLabelText('3'));
      
      expect(screen.getByText('123')).toBeInTheDocument();
    });

    it('should perform addition', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Toplama'));
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('8');
    });

    it('should perform subtraction', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('9'));
      fireEvent.click(screen.getByLabelText('Çıkarma'));
      fireEvent.click(screen.getByLabelText('4'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('5');
    });

    it('should perform multiplication', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('6'));
      fireEvent.click(screen.getByLabelText('Çarpma'));
      fireEvent.click(screen.getByLabelText('7'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('should perform division', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('8'));
      fireEvent.click(screen.getByLabelText('Bölme'));
      fireEvent.click(screen.getByLabelText('2'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('4');
    });

    it('should handle decimal numbers', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Ondalık nokta'));
      fireEvent.click(screen.getByLabelText('1'));
      fireEvent.click(screen.getByLabelText('4'));
      
      expect(screen.getByText('3.14')).toBeInTheDocument();
    });

    it('should clear display', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Temizle'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('0');
    });

    it('should handle backspace', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('1'));
      fireEvent.click(screen.getByLabelText('2'));
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Sil'));
      
      expect(screen.getByText('12')).toBeInTheDocument();
    });
  });

  describe('Scientific Functions', () => {
    it('should calculate square root', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('9'));
      fireEvent.click(screen.getByLabelText('Karekök'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('3');
    });

    it('should calculate square', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Kare'));
      
      expect(screen.getByText('25')).toBeInTheDocument();
    });

    it('should calculate cube', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Küp'));
      
      expect(screen.getByText('27')).toBeInTheDocument();
    });

    it('should insert Pi constant', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('Pi sayısı'));
      
      const display = screen.getByText(/3\.14/);
      expect(display).toBeInTheDocument();
    });

    it('should insert Euler constant', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('Euler sayısı'));
      
      const display = screen.getByText(/2\.71/);
      expect(display).toBeInTheDocument();
    });

    it('should calculate sine in degree mode', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('9'));
      fireEvent.click(screen.getByLabelText('0'));
      fireEvent.click(screen.getByLabelText('Sinüs'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display?.textContent).toMatch(/1/);
    });

    it('should toggle between degree and radian mode', () => {
      render(<ScientificCalculator />);
      
      const modeButton = screen.getByLabelText(/Açı modu/);
      expect(modeButton).toHaveTextContent('DEG');
      
      fireEvent.click(modeButton);
      expect(modeButton).toHaveTextContent('RAD');
      
      fireEvent.click(modeButton);
      expect(modeButton).toHaveTextContent('DEG');
    });
  });

  describe('Memory Operations', () => {
    it('should store value in memory', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Belleğe kaydet'));
      
      expect(screen.getByText(/M: 5/)).toBeInTheDocument();
    });

    it('should recall value from memory', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('7'));
      fireEvent.click(screen.getByLabelText('Belleğe kaydet'));
      fireEvent.click(screen.getByLabelText('Temizle'));
      fireEvent.click(screen.getByLabelText('Bellekten getir'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('7');
    });

    it('should clear memory', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Belleğe kaydet'));
      fireEvent.click(screen.getByLabelText('Belleği temizle'));
      
      expect(screen.queryByText(/M: /)).not.toBeInTheDocument();
    });

    it('should add to memory', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Belleğe kaydet'));
      fireEvent.click(screen.getByLabelText('Temizle'));
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Belleğe ekle'));
      
      expect(screen.getByText(/M: 8/)).toBeInTheDocument();
    });
  });

  describe('History Management', () => {
    it('should toggle history panel', () => {
      render(<ScientificCalculator />);
      
      const historyButton = screen.getByLabelText('Geçmişi göster/gizle');
      fireEvent.click(historyButton);
      
      expect(screen.getByRole('region', { name: 'İşlem geçmişi' })).toBeInTheDocument();
    });

    it('should add calculation to history', () => {
      render(<ScientificCalculator />);
      
      // Perform calculation
      fireEvent.click(screen.getByLabelText('5'));
      fireEvent.click(screen.getByLabelText('Toplama'));
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      // Open history
      fireEvent.click(screen.getByLabelText('Geçmişi göster/gizle'));
      
      expect(screen.getByText(/5 \+ 3/)).toBeInTheDocument();
      expect(screen.getByText(/= 8/)).toBeInTheDocument();
    });

    it('should clear history', () => {
      render(<ScientificCalculator />);
      
      // Perform calculation
      fireEvent.click(screen.getByLabelText('2'));
      fireEvent.click(screen.getByLabelText('Çarpma'));
      fireEvent.click(screen.getByLabelText('3'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      // Open history and clear
      fireEvent.click(screen.getByLabelText('Geçmişi göster/gizle'));
      fireEvent.click(screen.getByLabelText('Geçmişi temizle'));
      
      expect(screen.getByText('Henüz işlem yapılmadı')).toBeInTheDocument();
    });
  });

  describe('Keyboard Support', () => {
    it('should handle number keys', () => {
      render(<ScientificCalculator />);
      
      fireEvent.keyDown(window, { key: '5' });
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('5');
    });

    it('should handle operator keys', () => {
      render(<ScientificCalculator />);
      
      fireEvent.keyDown(window, { key: '5' });
      fireEvent.keyDown(window, { key: '+' });
      fireEvent.keyDown(window, { key: '3' });
      fireEvent.keyDown(window, { key: 'Enter' });
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('8');
    });

    it('should handle Escape key for clear', () => {
      render(<ScientificCalculator />);
      
      fireEvent.keyDown(window, { key: '5' });
      fireEvent.keyDown(window, { key: 'Escape' });
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('0');
    });

    it('should handle Backspace key', () => {
      render(<ScientificCalculator />);
      
      fireEvent.keyDown(window, { key: '1' });
      fireEvent.keyDown(window, { key: '2' });
      fireEvent.keyDown(window, { key: 'Backspace' });
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('1');
    });
  });

  describe('Error Handling', () => {
    it('should display error for invalid operations', () => {
      render(<ScientificCalculator />);
      
      fireEvent.click(screen.getByLabelText('0'));
      fireEvent.click(screen.getByLabelText('Bölme'));
      fireEvent.click(screen.getByLabelText('0'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      // 0/0 = NaN or Infinity
      expect(display?.textContent).toMatch(/NaN|Infinity|Error/);
    });

    it('should recover from error state', () => {
      render(<ScientificCalculator />);
      
      // Cause error
      fireEvent.click(screen.getByLabelText('0'));
      fireEvent.click(screen.getByLabelText('Bölme'));
      fireEvent.click(screen.getByLabelText('0'));
      fireEvent.click(screen.getByLabelText('Eşittir'));
      
      // Clear and continue
      fireEvent.click(screen.getByLabelText('Temizle'));
      fireEvent.click(screen.getByLabelText('5'));
      
      const display = screen.getByRole('application').querySelector('.main-display');
      expect(display).toHaveTextContent('5');
    });
  });

  describe('Responsive Design', () => {
    it('should render on mobile viewport', () => {
      global.innerWidth = 375;
      global.innerHeight = 667;
      
      render(<ScientificCalculator />);
      
      expect(screen.getByRole('application')).toBeInTheDocument();
    });
  });

  describe('Turkish Language Support', () => {
    it('should display Turkish labels', () => {
      render(<ScientificCalculator />);
      
      expect(screen.getByText('Bilimsel Hesap Makinesi')).toBeInTheDocument();
      expect(screen.getByLabelText('Karekök')).toBeInTheDocument();
      expect(screen.getByLabelText('Sinüs')).toBeInTheDocument();
    });

    it('should show Turkish keyboard shortcuts', () => {
      render(<ScientificCalculator />);
      
      const shortcuts = screen.getByText('⌨️ Klavye Kısayolları');
      expect(shortcuts).toBeInTheDocument();
    });
  });
});
