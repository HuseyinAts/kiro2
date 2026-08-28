import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { AdaptifTestPage } from './AdaptifTestPage';

expect.extend(toHaveNoViolations);

describe('AdaptifTestPage', () => {
  it('yüklenir: header + motor paneli 3 blok', async () => {
    render(<AdaptifTestPage />);
    expect(await screen.findByText('Yetenek tahmini (θ)')).toBeInTheDocument();
    expect(screen.getByText('Adaptif Yerleştirme Testi')).toBeInTheDocument();
    expect(screen.getByText('CAT · IRT')).toBeInTheDocument();
    expect(screen.getByText('θ Yakınsaması')).toBeInTheDocument();
    expect(screen.getByText('Standart hata (SE)')).toBeInTheDocument();
  });

  it('seçim yokken Cevapla devre dışı; seçince aktif + ilerler', async () => {
    render(<AdaptifTestPage />);
    await screen.findByText('Yetenek tahmini (θ)');
    expect(screen.getByText('0 doğru')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cevapla/ })).toBeDisabled();
    await userEvent.click(within(screen.getByRole('radiogroup')).getAllByRole('radio')[0]!);
    expect(screen.getByRole('button', { name: /Cevapla/ })).toBeEnabled();
    await userEvent.click(screen.getByRole('button', { name: /Cevapla/ }));
    expect(await screen.findByText('1 doğru')).toBeInTheDocument();
  });

  it('klavye: rakam seçer, Enter gönderir (DoD Enter=Cevapla)', async () => {
    render(<AdaptifTestPage />);
    await screen.findByText('Yetenek tahmini (θ)');
    const grp = screen.getByRole('radiogroup');
    within(grp).getAllByRole('radio')[0]!.focus();
    await userEvent.keyboard('1');
    expect(within(grp).getAllByRole('radio')[0]!).toHaveAttribute('aria-checked', 'true');
    await userEvent.keyboard('{Enter}');
    expect(await screen.findByText('1 doğru')).toBeInTheDocument();
  });

  it('"Emin değilim" (secim:null) ilerletir', async () => {
    render(<AdaptifTestPage />);
    await screen.findByText('Yetenek tahmini (θ)');
    await userEvent.click(screen.getByRole('button', { name: 'Emin değilim' }));
    await waitFor(() => expect(screen.queryByText('0 doğru')).not.toBeInTheDocument());
  });

  it('doğru/yanlış geri bildirimi GÖSTERİLMEZ (yerleştirme)', async () => {
    render(<AdaptifTestPage />);
    await screen.findByText('Yetenek tahmini (θ)');
    await userEvent.click(within(screen.getByRole('radiogroup')).getAllByRole('radio')[0]!);
    await userEvent.click(screen.getByRole('button', { name: /Cevapla/ }));
    await screen.findByText('1 doğru');
    expect(screen.queryByText('Doğru cevap')).not.toBeInTheDocument();
    expect(screen.queryByText('Çözüm · adım adım')).not.toBeInTheDocument();
  });

  it('tam akış → Yerleştirme tamamlandı (durdurma sunucuda)', async () => {
    render(<AdaptifTestPage />);
    await screen.findByText('Yetenek tahmini (θ)');
    for (let i = 0; i < 12; i++) {
      const btn = screen.queryByRole('button', { name: 'Emin değilim' });
      if (!btn) break;
      await userEvent.click(btn);
    }
    expect(await screen.findByText('Yerleştirme tamamlandı')).toBeInTheDocument();
  }, 20000);

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<AdaptifTestPage />);
    await screen.findByText('Yetenek tahmini (θ)');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);


  // --- FAZ4 · LaTeX render (üretim havuzunun %60.7'si formül içeriyor) ---

  it('soru metnindeki LaTeX KaTeX ile render edilir, ham kalmaz', async () => {
    const { configureKiroApi } = await import('../api/api-client');
    const ham = (await import('../api/kiro-data.json')).default as Record<string, unknown>;
    const veri = structuredClone(ham) as { catBankMat: { soru: string; secenekler: string[] }[] };
    veri.catBankMat[0]!.soru = '$2x^2 - 4x + 6 = 0$ denkleminin kökleri toplamı kaçtır?';
    const BS = String.fromCharCode(92); // ters bolu — kaynak-kacis belirsizligini eler
    veri.catBankMat[0]!.secenekler = [`$${BS}frac{2}{7}$`, '2', '3', '4'];
    configureKiroApi({ mode: 'mock', mockData: veri as never });

    const { container } = render(<AdaptifTestPage />);
    await screen.findByRole('radiogroup');

    // KaTeX gerçekten çalıştı mı?
    expect(container.querySelector('.katex')).not.toBeNull();
    // Öğrencinin GÖRDÜĞÜ metinde ham delimiter kalmamalı (MathML annotation hariç)
    const kopya = container.cloneNode(true) as HTMLElement;
    kopya.querySelectorAll('annotation, .katex-mathml').forEach((n) => n.remove());
    expect(kopya.textContent).not.toContain('$2x^2');
    expect(kopya.textContent).not.toContain(`${BS}frac`);

    // Geçersiz iç içelik: stem <p> içinde; MathText blok öğe ÜRETMEMELİ
    expect(container.querySelectorAll('p p').length).toBe(0);
    expect(container.querySelectorAll('p div').length).toBe(0);

    configureKiroApi({ mode: 'mock', mockData: ham as never });
  });

  it('LaTeX render edilse de şık radio sözleşmesi bozulmaz', async () => {
    const { configureKiroApi } = await import('../api/api-client');
    const ham = (await import('../api/kiro-data.json')).default as Record<string, unknown>;
    const veri = structuredClone(ham) as { catBankMat: { secenekler: string[] }[] };
    veri.catBankMat[0]!.secenekler = ['$x_1$', '$x_2$', '$x_3$', '$x_4$'];
    configureKiroApi({ mode: 'mock', mockData: veri as never });

    render(<AdaptifTestPage />);
    const grp = await screen.findByRole('radiogroup');
    const radios = within(grp).getAllByRole('radio');
    expect(radios.length).toBeGreaterThan(0);
    // Roving tabindex + aria-checked korunuyor mu
    expect(radios[0]!.getAttribute('aria-checked')).toBe('false');
    await userEvent.click(radios[0]!);
    expect(radios[0]!.getAttribute('aria-checked')).toBe('true');

    configureKiroApi({ mode: 'mock', mockData: ham as never });
  });

});
