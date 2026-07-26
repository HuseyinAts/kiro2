/**
 * MathText — GERÇEK üretim verisiyle doğrulama.
 *
 * Örnek dizeler question_bank'tan alındı (MATEMATIK, CAT-uygun havuz,
 * 27 Tem 2026). Havuzun %60.7'si (6,129/10,102) LaTeX içeriyor; bu bileşen
 * o içeriği okunur kılan tek yol. Kırılırsa öğrenci ham "$\frac{2}{7}$" görür.
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { MathText } from './MathText';

/** KaTeX render etti mi? .katex sınıfı KaTeX'in kök çıktısıdır. */
function katexVarMi(container: HTMLElement): boolean {
  return container.querySelector('.katex') !== null;
}

/**
 * Öğrencinin GÖRDÜĞÜ metin.
 *
 * container.textContent kullanılamaz: KaTeX erişilebilirlik için MathML
 * `<annotation encoding="application/x-tex">` içine ORİJİNAL TeX'i gömer, o da
 * textContent'e karışır. Görsel katman `.katex-html` (MathML aria-hidden değil,
 * tersi: .katex-html aria-hidden'dır, MathML ekran okuyucuya gider).
 */
function gorunenMetin(container: HTMLElement): string {
  const kopya = container.cloneNode(true) as HTMLElement;
  kopya.querySelectorAll('annotation, .katex-mathml').forEach((n) => n.remove());
  return kopya.textContent ?? '';
}

describe('MathText — üretim havuzundaki gerçek soru metinleri', () => {
  it('inline $...$ formülünü KaTeX ile render eder', () => {
    const { container } = render(
      <MathText>
        {'$2x^2 - 4x + 6 = 0$ denkleminin kökleri $x_1$ ve $x_2$\u2019dir.'}
      </MathText>,
    );
    expect(katexVarMi(container)).toBe(true);
    // Ham LaTeX ekranda kalmamalı
    expect(gorunenMetin(container)).not.toContain('$2x^2');
  });

  it('\\frac ve \\sqrt komutlarını render eder', () => {
    const { container } = render(
      <MathText>
        {'Pozitif iki sayının birbirine oranı $\\frac{2}{7}$\u2019dir.'}
      </MathText>,
    );
    expect(katexVarMi(container)).toBe(true);
    expect(gorunenMetin(container)).not.toContain('\\frac');
  });

  it('kök-derece, \\left(...\\right) ve Yunan harflerini render eder', () => {
    const { container } = render(
      <MathText>
        {'$\\theta \\in \\left( \\frac{\\pi}{24}, \\frac{\\pi}{12} \\right)$ olmak üzere'}
      </MathText>,
    );
    expect(katexVarMi(container)).toBe(true);
    expect(gorunenMetin(container)).not.toContain('\\theta');
  });

  it('$ delimiter OLMADAN ham \\frac gelirse auto-wrap ile render eder', () => {
    // Şıklarda DB'de bu format var (bkz. MathText bare-LaTeX notu)
    const { container } = render(<MathText inline>{'\\frac{26}{33}'}</MathText>);
    expect(katexVarMi(container)).toBe(true);
  });

  it('LaTeX içermeyen düz Türkçe metni AYNEN gösterir', () => {
    render(<MathText>{'Üç basamaklı sayı için rakamlar toplamı kaçtır?'}</MathText>);
    expect(
      screen.getByText('Üç basamaklı sayı için rakamlar toplamı kaçtır?'),
    ).toBeInTheDocument();
  });

  it('boş metinde çökmez', () => {
    const { container } = render(<MathText>{''}</MathText>);
    expect(container.firstChild).toBeTruthy();
  });

  it('inline modda <p> ÜRETMEZ (iç içe <p> geçersiz HTML olurdu)', () => {
    // AdaptifTestPage soru metnini <p> içinde basıyor; inline mod şart.
    const { container } = render(<MathText inline>{'$x_1$ ve $x_2$'}</MathText>);
    expect(container.querySelector('p')).toBeNull();
  });
});
