/**
 * kiro MathText sarmalayıcısı — sözleşmesi: inline'ı ZORLAR.
 *
 * Paylaşılan bileşen block modda <div>/<p> üretir; kiro'da soru gövdesi zaten
 * <p> içinde (AdaptifTestPage.tsx:180) → iç içe <p> geçersiz HTML olurdu.
 * Bu tuzağı testler yakalayamaz çünkü src/test/setup.ts console.error'ı
 * susturuyor (React'in validateDOMNesting uyarısı yutulur). Tek koruma:
 * sarmalayıcının `inline` prop'unu HİÇ dışarı açmaması + bu testler.
 */

import { render, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { MathText } from './MathText';

describe('kiro/ui MathText', () => {
  it('LaTeX içeren metni KaTeX ile render eder', async () => {
    const { container } = render(<MathText>{'$\\frac{2}{7}$ oranı'}</MathText>);
    await waitFor(() => expect(container.querySelector('.katex')).not.toBeNull(), { timeout: 4000 });
  });

  it('blok öğe ÜRETMEZ — <p> içine güvenle konur', async () => {
    const { container } = render(<MathText>{'$x_1 + x_2 = 5$'}</MathText>);
    await waitFor(() => expect(container.querySelector('.katex')).not.toBeNull(), { timeout: 4000 });
    expect(container.querySelector('p')).toBeNull();
    expect(container.querySelector('div')).toBeNull();
  });

  it('LaTeX yokken de blok öğe üretmez (düz metin yolu)', () => {
    const { container } = render(<MathText>{'Rakamları toplamı kaçtır?'}</MathText>);
    expect(container.querySelector('p')).toBeNull();
    expect(container.querySelector('div')).toBeNull();
    expect(container.textContent).toContain('Rakamları toplamı kaçtır?');
  });

  it('k-math sınıfını taşır (stil kancası)', () => {
    const { container } = render(<MathText>{'test'}</MathText>);
    expect(container.querySelector('.k-math')).not.toBeNull();
  });
});
