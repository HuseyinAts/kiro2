import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { Callout } from './Callout';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

// bespoke svg — kanon: emoji/lucide YOK
const Icon = () => (
  <svg aria-hidden width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round">
    <circle cx="12" cy="12" r="9" />
  </svg>
);

describe('Callout', () => {
  it('dawn (varsayılan) children metnini render eder', () => {
    paper(<Callout>Bugünkü tekrarların seni bekliyor.</Callout>);
    expect(screen.getByText('Bugünkü tekrarların seni bekliyor.')).toBeInTheDocument();
  });

  it('success tonu metni render eder', () => {
    paper(<Callout tone="success">Tüm konular tamamlandı.</Callout>);
    expect(screen.getByText('Tüm konular tamamlandı.')).toBeInTheDocument();
  });

  it('attention tonu (amber) metni render eder', () => {
    paper(<Callout tone="attention">Sınavına üç gün kaldı.</Callout>);
    expect(screen.getByText('Sınavına üç gün kaldı.')).toBeInTheDocument();
  });

  it('icon verilince ikon ve metin birlikte görünür', () => {
    const { container } = paper(<Callout icon={<Icon />}>İpucu metni.</Callout>);
    expect(screen.getByText('İpucu metni.')).toBeInTheDocument();
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('KANON: bekliyor dili geçerli, absence-dili yok', () => {
    paper(<Callout tone="attention">Planın seni bekliyor.</Callout>);
    expect(screen.getByText('Planın seni bekliyor.')).toBeInTheDocument();
    expect(screen.queryByText(/eksik/i)).not.toBeInTheDocument();
  });

  it('axe: dawn ihlal yok', async () => {
    const { container } = paper(<Callout>Bugünkü tekrarların seni bekliyor.</Callout>);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: attention (amber) ihlal yok', async () => {
    const { container } = paper(<Callout tone="attention">Sınavına üç gün kaldı.</Callout>);
    expect(await axe(container)).toHaveNoViolations();
  });
});
