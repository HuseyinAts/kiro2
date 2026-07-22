import { render, screen, within, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect } from 'vitest';

import { FSRSPage } from './FSRSPage';

expect.extend(toHaveNoViolations);

describe('FSRSPage', () => {
  it('sayfa: hero + eğri + istatistik + hafıza gücü + 7 gün yükü', async () => {
    render(<FSRSPage />);
    expect(await screen.findByText('Bugün tekrar edilecek')).toBeInTheDocument();
    expect(screen.getByText('Tekrar · Hafıza Motoru')).toBeInTheDocument();
    expect(screen.getByText('Unutma eğrisi')).toBeInTheDocument();
    expect(screen.getByText('Tutma oranı')).toBeInTheDocument();
    expect(screen.getByText('Konuya göre hafıza gücü')).toBeInTheDocument();
    expect(screen.getByText(/Önümüzdeki 7 gün/)).toBeInTheDocument();
  });

  it('overlay: Tekrara başla → SORU → Cevabı göster → 4 derece butonu', async () => {
    render(<FSRSPage />);
    await screen.findByText('Bugün tekrar edilecek');
    await userEvent.click(screen.getByRole('button', { name: 'Tekrara başla' }));
    const dialog = await screen.findByRole('dialog', { name: 'Tekrar oturumu' });
    expect(within(dialog).getByText('SORU')).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole('button', { name: /Cevabı göster/ }));
    expect(within(dialog).getByText('CEVAP')).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Tekrar/ })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Zor/ })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /İyi/ })).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: /Kolay/ })).toBeInTheDocument();
  });

  it('overlay: demoOverlay açık + Esc kapatır (aria-modal)', async () => {
    render(<FSRSPage demoOverlay />);
    const dialog = await screen.findByRole('dialog', { name: 'Tekrar oturumu' });
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    fireEvent.keyDown(dialog, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('axe: sayfa temiz', async () => {
    const { container } = render(<FSRSPage />);
    await screen.findByText('Bugün tekrar edilecek');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
