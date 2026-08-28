/**
 * Test Suite: BadgeEarned Component
 * #415 (A11y/WCAG) — modal modda focus-trap regresyon testi.
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import { BadgeEarned } from '../BadgeEarned';

const badge = { name: 'İlk Adım', icon: '🏅', category: 'quiz', description: 'İlk sınavını tamamladın' };

describe('BadgeEarned', () => {
  it('modal modda: Tab tuşu odağı kart içinde tutar (arka plana kaçmaz)', async () => {
    const user = userEvent.setup();
    render(
      <>
        <button>Arka plan butonu</button>
        <BadgeEarned badge={badge} mode="modal" onClose={vi.fn()} autoCloseMs={999999} />
      </>,
    );

    const kapatBtn = screen.getByRole('button', { name: 'Harika!' });
    kapatBtn.focus();
    expect(kapatBtn).toHaveFocus();

    await user.tab();

    expect(screen.getByRole('button', { name: 'Arka plan butonu' })).not.toHaveFocus();
  });

  it('modal modda: dialog role + aria-modal + rozet adıyla aria-label taşır', () => {
    render(<BadgeEarned badge={badge} mode="modal" onClose={vi.fn()} autoCloseMs={999999} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-label', 'İlk Adım rozeti kazanıldı');
  });
});
