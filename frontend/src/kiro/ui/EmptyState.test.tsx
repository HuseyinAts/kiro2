import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { EmptyState } from './EmptyState';
import { KiroThemeProvider, type KiroTheme } from './theme';

expect.extend(toHaveNoViolations);

const withTheme = (theme: KiroTheme, ui: React.ReactNode) =>
  render(<KiroThemeProvider theme={theme}>{ui}</KiroThemeProvider>);

describe('EmptyState', () => {
  it('serif başlığı render eder', () => {
    withTheme('paper', <EmptyState serifTitle="Sıradaki çalışma seni bekliyor" />);
    expect(screen.getByText('Sıradaki çalışma seni bekliyor')).toBeInTheDocument();
  });

  it('gövde metnini verildiğinde gösterir', () => {
    withTheme(
      'paper',
      <EmptyState serifTitle="Pusulan hazır" body="İlk konunu seç, birlikte yön bulalım." />
    );
    expect(screen.getByText('İlk konunu seç, birlikte yön bulalım.')).toBeInTheDocument();
  });

  it('action tıklanınca handler tetiklenir', async () => {
    const onAction = vi.fn();
    withTheme(
      'paper',
      <EmptyState
        serifTitle="Sıradaki çalışma seni bekliyor"
        action={
          <button type="button" onClick={onAction}>
            Konu ekle
          </button>
        }
      />
    );
    await userEvent.click(screen.getByRole('button', { name: 'Konu ekle' }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('KANON: yönlendiren dil kullanır, absence-dili yok', () => {
    withTheme(
      'paper',
      <EmptyState serifTitle="Sıradaki çalışma seni bekliyor" body="İlk adımı at, gerisi akar." />
    );
    expect(screen.getByText('Sıradaki çalışma seni bekliyor')).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('axe: paper yüzey ihlal yok', async () => {
    const { container } = withTheme(
      'paper',
      <EmptyState
        serifTitle="Sıradaki çalışma seni bekliyor"
        body="İlk adımı at, ilerledikçe burası dolacak."
        action={
          <button type="button">Konu ekle</button>
        }
      />
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzey ihlal yok', async () => {
    const { container } = withTheme(
      'dusk',
      <EmptyState serifTitle="Bugünü kutlamayı hak ettin" body="Kaldığın yerden devam et." />
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
