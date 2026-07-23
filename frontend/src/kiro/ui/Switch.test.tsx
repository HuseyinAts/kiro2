import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { Switch } from './Switch';
import { resetAyar } from '../lib/ayarStore';

expect.extend(toHaveNoViolations);

// Switch → useReducedMotion → ayarStore (calmMode) aboneliği taşır; test izolasyonu.
beforeEach(() => resetAyar());
afterEach(() => resetAyar());

describe('Switch', () => {
  it('role=switch taşır ve checked durumunu aria-checked ile yansıtır', () => {
    render(<Switch checked ariaLabel="Bildirimler" onChange={() => {}} />);
    const el = screen.getByRole('switch', { name: 'Bildirimler' });
    expect(el).toHaveAttribute('aria-checked', 'true');
  });

  it('KAPALI track WCAG 1.4.11 için görünür nötr sınır taşır (dolgudan farklı)', () => {
    const { container } = render(<Switch checked={false} ariaLabel="Sakin mod" onChange={() => {}} />);
    const track = container.querySelector('span[aria-hidden]') as HTMLElement;
    expect(track).not.toBeNull();
    // 1.5px solid sınır — beyaz kartta 3.63:1 (#8F8577)
    expect(track.style.borderStyle).toBe('solid');
    expect(track.style.borderWidth).toBe('1.5px');
    // sınır rengi dolgudan farklı → sınır GÖRÜNÜR (beyaz kart üstünde ayırt edilir)
    expect(track.style.borderColor).not.toBe('');
    expect(track.style.borderColor).not.toBe(track.style.backgroundColor);
  });

  it('AÇIK track sınırı dolguyla aynı renk (görünmez dikiş; coralCtaBg zaten ≥3:1)', () => {
    const { container } = render(<Switch checked ariaLabel="Sakin mod" onChange={() => {}} />);
    const track = container.querySelector('span[aria-hidden]') as HTMLElement;
    expect(track.style.borderStyle).toBe('solid');
    expect(track.style.borderColor).toBe(track.style.backgroundColor);
  });

  it('ariaDescribedby verilince kök switch elementine aria-describedby iletilir', () => {
    render(
      <Switch checked={false} ariaLabel="Sakin mod" ariaDescribedby="sakin-aciklama" onChange={() => {}} />
    );
    expect(screen.getByRole('switch')).toHaveAttribute('aria-describedby', 'sakin-aciklama');
  });

  it('ariaDescribedby verilmezse aria-describedby özniteliği yazılmaz (additive sözleşme)', () => {
    render(<Switch checked={false} ariaLabel="Sakin mod" onChange={() => {}} />);
    expect(screen.getByRole('switch')).not.toHaveAttribute('aria-describedby');
  });

  it('label verilince erişilebilir ad içerikten türetilir', () => {
    render(<Switch checked={false} label="FSRS hatırlatması" onChange={() => {}} />);
    expect(screen.getByRole('switch', { name: 'FSRS hatırlatması' })).toHaveAttribute(
      'aria-checked',
      'false'
    );
  });

  it('tıklanınca onChange ters değerle çağrılır', async () => {
    const onChange = vi.fn();
    render(<Switch checked={false} ariaLabel="Bildirimler" onChange={onChange} />);
    await userEvent.click(screen.getByRole('switch'));
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('Space tuşu toggle eder', () => {
    const onChange = vi.fn();
    render(<Switch checked={false} ariaLabel="Bildirimler" onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole('switch'), { key: ' ' });
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('Enter tuşu toggle eder', () => {
    const onChange = vi.fn();
    render(<Switch checked ariaLabel="Bildirimler" onChange={onChange} />);
    fireEvent.keyDown(screen.getByRole('switch'), { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it('disabled iken tık ve klavye no-op', async () => {
    const onChange = vi.fn();
    render(<Switch checked={false} disabled ariaLabel="Bildirimler" onChange={onChange} />);
    const el = screen.getByRole('switch');
    await userEvent.click(el);
    fireEvent.keyDown(el, { key: ' ' });
    fireEvent.keyDown(el, { key: 'Enter' });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('axe: etiketli anahtar ihlal yok', async () => {
    const { container } = render(
      <Switch checked label="Zayıf konu uyarısı" onChange={() => {}} />
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: ariaLabel ile ihlal yok', async () => {
    const { container } = render(
      <Switch checked={false} ariaLabel="Sakin mod" onChange={() => {}} />
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
