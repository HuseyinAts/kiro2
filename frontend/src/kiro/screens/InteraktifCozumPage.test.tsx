import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { InteraktifCozumPage, hesaplaParabol } from './InteraktifCozumPage';

expect.extend(toHaveNoViolations);

describe('hesaplaParabol (istemci-matematik — deterministik)', () => {
  it('varsayılan (1, -2, -1): tepe (1, -2), yukarı, orta, iki kök', () => {
    const m = hesaplaParabol(1, -2, -1);
    expect(m.hasVertex).toBe(true);
    expect(m.vertexX).toBe('1');
    expect(m.vertexY).toBe('-2');
    expect(m.up).toBe(true);
    expect(m.dirText).toBe('yukarı');
    expect(m.widthText).toBe('orta');
    expect(m.diskriminant).toBe(8); // b²-4ac = 4 + 4
    expect(m.kokler).toHaveLength(2);
    expect(m.insight).toMatch(/c değeri parabolü/);
    expect(m.curve.length).toBeGreaterThan(0);
    expect(m.denklemLabel).toContain('y = 1x² − 2x − 1');
  });

  it('a = 0 → doğru: tepe yok, diskriminant yok, doğru (a=0)', () => {
    const m = hesaplaParabol(0, 2, 1);
    expect(m.hasVertex).toBe(false);
    expect(m.vertexX).toBe('—');
    expect(m.tepeX).toBeNull();
    expect(m.diskriminant).toBeNull();
    expect(m.kokler).toHaveLength(0);
    expect(m.widthText).toBe('doğru (a=0)');
    expect(m.insight).toMatch(/^a = 0 olunca x² kaybolur/);
    expect(m.denklemLabel).toContain('grafik bir doğru');
  });

  it('|a| büyük → dar + daralır', () => {
    const m = hesaplaParabol(1.5, 0, 0);
    expect(m.widthText).toBe('dar');
    expect(m.insight).toMatch(/kollar birbirine yaklaşır/);
  });

  it('|a| küçük → geniş + yayvanlaşır', () => {
    const m = hesaplaParabol(0.5, 0, 0);
    expect(m.widthText).toBe('geniş');
    expect(m.insight).toMatch(/kollar açılır/);
  });

  it('a negatif → aşağı bakar (maksimum)', () => {
    const m = hesaplaParabol(-1, 0, 3);
    expect(m.up).toBe(false);
    expect(m.dirText).toBe('aşağı');
    expect(m.insight).toMatch(/parabol aşağı bakar/);
    expect(m.vertexX).toBe('0');
    expect(m.vertexY).toBe('3');
  });

  it('diskriminant < 0 → gerçek kök yok', () => {
    const m = hesaplaParabol(1, 0, 1);
    expect(m.diskriminant).toBe(-4);
    expect(m.kokler).toHaveLength(0);
    expect(m.denklemLabel).toContain('Gerçek kök yok');
  });

  it('diskriminant = 0 → tek (çakışık) kök', () => {
    const m = hesaplaParabol(1, -2, 1);
    expect(m.diskriminant).toBe(0);
    expect(m.kokler).toHaveLength(1);
    expect(m.denklemLabel).toContain('Tek (çakışık) kök');
  });
});

describe('InteraktifCozumPage', () => {
  it('sayfa: başlık + keşif alt-metni + soru + kategori + 3 kaydırıcı + içgörü kartları', () => {
    render(<InteraktifCozumPage />);
    expect(screen.getByRole('heading', { name: 'İnteraktif Çözüm' })).toBeInTheDocument();
    expect(screen.getByText('Okuma değil — kaydırarak keşfet')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Katsayılar parabolü nasıl değiştirir?' })).toBeInTheDocument();
    expect(screen.getByText('AYT MATEMATİK · PARABOL')).toBeInTheDocument();
    expect(screen.getByText('Aktif öğrenme')).toBeInTheDocument();
    expect(screen.getByText('Şu an')).toBeInTheDocument();
    expect(screen.getByText('KEŞFET')).toBeInTheDocument();
    expect(screen.getByText('Mini görev')).toBeInTheDocument();
    // 3 kaydırıcı — aria-label + native slider rolü
    expect(screen.getByRole('slider', { name: 'a katsayısı — açılım' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'b katsayısı — konum' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'c katsayısı — yükseklik' })).toBeInTheDocument();
  });

  it('SVG role=img güncel denklemi taşır (aria-label)', () => {
    render(<InteraktifCozumPage />);
    const grafik = screen.getByRole('img', { name: /Denklem: y = 1x² − 2x − 1/ });
    expect(grafik).toBeInTheDocument();
    expect(grafik.getAttribute('aria-label')).toContain('Tepe noktası (1, -2)');
  });

  it('kaydırıcı: a negatif olunca içgörü + yön canlı güncellenir', () => {
    render(<InteraktifCozumPage />);
    expect(screen.getByText('yukarı')).toBeInTheDocument();
    fireEvent.change(screen.getByRole('slider', { name: 'a katsayısı — açılım' }), { target: { value: '-1' } });
    expect(screen.getByText('aşağı')).toBeInTheDocument();
    expect(screen.getByText(/parabol aşağı bakar/)).toBeInTheDocument();
  });

  it('mini görev: yanlış durumda nazik yönlendirme, hedefte başarı', async () => {
    render(<InteraktifCozumPage />);
    const kontrol = screen.getByRole('button', { name: 'Kontrol et' });

    // Varsayılan (tepe 1,-2) → henüz değil
    await userEvent.click(kontrol);
    expect(screen.getByText(/Henüz değil/)).toBeInTheDocument();

    // Hedef: a<0, b=0, c=3 → tepe (0,3)
    fireEvent.change(screen.getByRole('slider', { name: 'a katsayısı — açılım' }), { target: { value: '-1' } });
    fireEvent.change(screen.getByRole('slider', { name: 'b katsayısı — konum' }), { target: { value: '0' } });
    fireEvent.change(screen.getByRole('slider', { name: 'c katsayısı — yükseklik' }), { target: { value: '3' } });
    await userEvent.click(kontrol);
    expect(screen.getByText(/Tam isabet/)).toBeInTheDocument();
  });

  it('axe: sayfa temiz', async () => {
    const { container } = render(<InteraktifCozumPage />);
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
