/**
 * ColorCoding Component Tests
 * 
 * Task 86.4: Değişken/sabit renkleri testleri
 * Requirements: REQ-51.76-51.80
 * 
 * @author Kiro AI
 * @date 2025-10-24
 */

import * as React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ColorCoding from './ColorCoding';

describe('ColorCoding Component - Task 86.4: Değişken/Sabit Renkleri', () => {
  describe('REQ-51.76: Variable Highlighting', () => {
    it('değişkenleri doğru renk ile vurgular', () => {
      const { container } = render(<ColorCoding expression="x + y - z" />);
      
      const tokens = container.querySelectorAll('[data-type="variable"]');
      expect(tokens).toHaveLength(3);
      
      // Varsayılan cyan renk kontrolü
      tokens.forEach(token => {
        expect(token).toHaveStyle({ color: '#06b6d4' });
      });
    });

    it('birden fazla değişkeni ayırt eder', () => {
      const { container } = render(<ColorCoding expression="a + b + c" />);
      
      const variables = container.querySelectorAll('[data-type="variable"]');
      expect(variables).toHaveLength(3);
      expect(variables[0].textContent).toBe('a');
      expect(variables[1].textContent).toBe('b');
      expect(variables[2].textContent).toBe('c');
    });

    it('büyük harf değişkenleri de tanır', () => {
      const { container } = render(<ColorCoding expression="X + Y" />);
      
      const variables = container.querySelectorAll('[data-type="variable"]');
      expect(variables).toHaveLength(2);
      expect(variables[0].textContent).toBe('X');
      expect(variables[1].textContent).toBe('Y');
    });
  });

  describe('REQ-51.77: Constant Identification', () => {
    it('π sabitini tanır ve doğru renk ile gösterir', () => {
      const { container } = render(<ColorCoding expression="π + 1" />);
      
      const constants = container.querySelectorAll('[data-type="constant"]');
      expect(constants).toHaveLength(1);
      expect(constants[0].textContent).toBe('π');
      expect(constants[0]).toHaveStyle({ color: '#84cc16' }); // Lime
    });

    it('e sabitini tanır', () => {
      const { container } = render(<ColorCoding expression="e + 1" />);
      
      const constants = container.querySelectorAll('[data-type="constant"]');
      expect(constants).toHaveLength(1);
      expect(constants[0].textContent).toBe('e');
      expect(constants[0]).toHaveStyle({ color: '#84cc16' });
    });

    it('sabitleri değişkenlerden ayırt eder', () => {
      const { container } = render(<ColorCoding expression="π + x" />);
      
      const constants = container.querySelectorAll('[data-type="constant"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      
      expect(constants).toHaveLength(1);
      expect(variables).toHaveLength(1);
      expect(constants[0].textContent).toBe('π');
      expect(variables[0].textContent).toBe('x');
    });
  });

  describe('REQ-51.78: Coefficient Distinction', () => {
    it('katsayıları doğru renk ile gösterir', () => {
      const { container } = render(<ColorCoding expression="2x + 3y" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      expect(coefficients).toHaveLength(2);
      
      // Orange renk kontrolü
      coefficients.forEach(coef => {
        expect(coef).toHaveStyle({ color: '#f97316' });
      });
    });

    it('katsayı ve değişkeni ayrı token olarak işler', () => {
      const { container } = render(<ColorCoding expression="5x" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      
      expect(coefficients).toHaveLength(1);
      expect(variables).toHaveLength(1);
      expect(coefficients[0].textContent).toBe('5');
      expect(variables[0].textContent).toBe('x');
    });

    it('ondalık katsayıları işler', () => {
      const { container } = render(<ColorCoding expression="2.5x + 3.14y" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      expect(coefficients).toHaveLength(2);
      expect(coefficients[0].textContent).toBe('2.5');
      expect(coefficients[1].textContent).toBe('3.14');
    });

    it('katsayısız değişkenleri doğru işler', () => {
      const { container } = render(<ColorCoding expression="x + 2y" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      
      expect(coefficients).toHaveLength(1); // Sadece 2
      expect(variables).toHaveLength(2); // x ve y
    });
  });

  describe('REQ-51.79: Karmaşık İfadeler', () => {
    it('değişken, sabit ve katsayıları birlikte işler', () => {
      const { container } = render(<ColorCoding expression="2x + π - 3y + e" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      const constants = container.querySelectorAll('[data-type="constant"]');
      
      expect(coefficients).toHaveLength(2); // 2, 3
      expect(variables).toHaveLength(2); // x, y
      expect(constants.length).toBeGreaterThanOrEqual(1); // π ve/veya e
    });

    it('parantezli ifadelerde doğru çalışır', () => {
      const { container } = render(<ColorCoding expression="(2x + 3) * (y - π)" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      const constants = container.querySelectorAll('[data-type="constant"]');
      
      expect(coefficients).toHaveLength(1); // 2
      expect(variables).toHaveLength(2); // x, y
      expect(constants).toHaveLength(1); // π
    });

    it('çoklu katsayılı ifadeleri işler', () => {
      const { container } = render(<ColorCoding expression="10x + 20y + 30z" />);
      
      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      expect(coefficients).toHaveLength(3);
      expect(coefficients[0].textContent).toBe('10');
      expect(coefficients[1].textContent).toBe('20');
      expect(coefficients[2].textContent).toBe('30');
    });
  });

  describe('REQ-51.80: Renk Şemaları', () => {
    it('özel renk ayarlarını uygular', () => {
      const customSettings = {
        variableColor: '#ff0000',
        constantColor: '#00ff00',
        coefficientColor: '#0000ff',
      };

      const { container } = render(
        <ColorCoding expression="2x + π" settings={customSettings} />
      );

      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      const constants = container.querySelectorAll('[data-type="constant"]');

      expect(coefficients.length).toBeGreaterThan(0);
      expect(variables.length).toBeGreaterThan(0);
      expect(constants.length).toBeGreaterThan(0);
      
      expect(coefficients[0]).toHaveStyle({ color: '#0000ff' });
      expect(variables[0]).toHaveStyle({ color: '#ff0000' });
      expect(constants[0]).toHaveStyle({ color: '#00ff00' });
    });

    it('yüksek kontrast modunda doğru renkleri kullanır', () => {
      const { container } = render(
        <ColorCoding expression="x + π" settings={{ highContrast: true }} />
      );

      const variables = container.querySelectorAll('[data-type="variable"]');
      const constants = container.querySelectorAll('[data-type="constant"]');

      expect(variables.length).toBeGreaterThan(0);
      expect(constants.length).toBeGreaterThan(0);
      
      // Yüksek kontrast renkleri
      expect(variables[0]).toHaveStyle({ color: '#00ffff' });
      expect(constants[0]).toHaveStyle({ color: '#ffff00' });
    });

    it('renk körlüğü dostu modda uygun renkleri kullanır', () => {
      const { container } = render(
        <ColorCoding 
          expression="2x + π" 
          settings={{ colorScheme: 'colorblind-friendly' }} 
        />
      );

      const coefficients = container.querySelectorAll('[data-type="coefficient"]');
      const variables = container.querySelectorAll('[data-type="variable"]');
      const constants = container.querySelectorAll('[data-type="constant"]');

      expect(coefficients.length).toBeGreaterThan(0);
      expect(variables.length).toBeGreaterThan(0);
      expect(constants.length).toBeGreaterThan(0);
      
      expect(coefficients[0]).toHaveStyle({ color: '#f0e442' });
      expect(variables[0]).toHaveStyle({ color: '#56b4e9' });
      expect(constants[0]).toHaveStyle({ color: '#009e73' });
    });
  });

  describe('Erişilebilirlik', () => {
    it('ARIA etiketleri içerir', () => {
      render(<ColorCoding expression="2x + π" />);
      
      const mathElement = screen.getByRole('math');
      expect(mathElement).toBeInTheDocument();
      expect(mathElement).toHaveAttribute('aria-label');
    });

    it('özel ARIA etiketi kullanır', () => {
      const customLabel = 'İki x artı pi';
      render(<ColorCoding expression="2x + π" aria-label={customLabel} />);
      
      const mathElement = screen.getByRole('math');
      expect(mathElement).toHaveAttribute('aria-label', customLabel);
    });

    it('renk açıklaması gösterir', () => {
      render(<ColorCoding expression="x" settings={{ showLegend: true }} />);
      
      const legend = screen.getByRole('region', { name: /renk açıklaması/i });
      expect(legend).toBeInTheDocument();
      expect(screen.getAllByText(/değişkenler/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/sabitler/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/katsayılar/i).length).toBeGreaterThan(0);
    });

    it('renk açıklamasını gizleyebilir', () => {
      render(<ColorCoding expression="x" settings={{ showLegend: false }} />);
      
      const legend = screen.queryByRole('region', { name: /renk açıklaması/i });
      expect(legend).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('boş ifadeyi işler', () => {
      const { container } = render(<ColorCoding expression="" />);
      const tokens = container.querySelectorAll('.color-coding__token');
      expect(tokens).toHaveLength(0);
    });

    it('sadece boşluk içeren ifadeyi işler', () => {
      const { container } = render(<ColorCoding expression="   " />);
      const tokens = container.querySelectorAll('.color-coding__token');
      expect(tokens).toHaveLength(0);
    });

    it('özel karakterleri işler', () => {
      const { container } = render(<ColorCoding expression="x² + y³" />);
      const variables = container.querySelectorAll('[data-type="variable"]');
      expect(variables).toHaveLength(2);
    });

    it('özel karakterleri text olarak işler', () => {
      const { container } = render(<ColorCoding expression="α + β + γ" />);
      // Yunanca harfler şu an için desteklenmiyor, text olarak işlenir
      const tokens = container.querySelectorAll('.color-coding__token');
      expect(tokens.length).toBeGreaterThan(0);
    });
  });
});
