import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MathText } from './MathText';

function katexVarMi(container: HTMLElement): boolean {
  return container.querySelector('.katex') !== null;
}

function gorunenMetin(container: HTMLElement): string {
  const kopya = container.cloneNode(true) as HTMLElement;
  kopya.querySelectorAll('annotation, .katex-mathml').forEach((n) => n.remove());
  return kopya.textContent ?? '';
}

describe('MathText — üretim havuzundaki gerçek soru metinleri', () => {
  it('inline $...$ formülünü KaTeX ile render eder', async () => {
    const { container } = render(
      <MathText>
        {'$2x^2 - 4x + 6 = 0$ denkleminin kökleri $x_1$ ve $x_2$\u2019dir.'}
      </MathText>,
    );
    await waitFor(() => expect(katexVarMi(container)).toBe(true));
    expect(gorunenMetin(container)).not.toContain('$2x^2');
  });

  it('\\frac ve \\sqrt komutlarını render eder', async () => {
    const { container } = render(
      <MathText>
        {'Pozitif iki sayının birbirine oranı $\\frac{2}{7}$\u2019dir.'}
      </MathText>,
    );
    await waitFor(() => expect(katexVarMi(container)).toBe(true));
  });

  it('kök-derece, \\left(...\\right) ve Yunan harflerini render eder', async () => {
    const { container } = render(
      <MathText>
        {'$\\theta \\in \\left( \\frac{\\pi}{24}, \\frac{\\pi}{12} \\right)$ olmak üzere'}
      </MathText>,
    );
    await waitFor(() => expect(katexVarMi(container)).toBe(true));
  });

  it('$ delimiter OLMADAN ham \\frac gelirse auto-wrap ile render eder', async () => {
    const { container } = render(<MathText inline>{'\\frac{26}{33}'}</MathText>);
    await waitFor(() => expect(katexVarMi(container)).toBe(true));
  });
});
