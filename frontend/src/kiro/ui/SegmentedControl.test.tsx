import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { SegmentedControl } from './SegmentedControl';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('SegmentedControl', () => {
  it('pill: bir seçeneğe tıklanınca onChange doğru key ile çağrılır', async () => {
    const onChange = vi.fn();
    paper(
      <SegmentedControl
        options={[
          { key: 'aylik', label: 'Aylık' },
          { key: 'yillik', label: 'Yıllık' },
        ]}
        value="aylik"
        onChange={onChange}
      />
    );
    await userEvent.click(screen.getByRole('radio', { name: 'Yıllık' }));
    expect(onChange).toHaveBeenCalledWith('yillik');
  });

  it('scale: seçeneğe tıklanınca onChange doğru key ile çağrılır', async () => {
    const onChange = vi.fn();
    paper(
      <SegmentedControl
        variant="scale"
        ariaContext="Bu konuyu ne kadar iyi biliyorsun"
        options={[
          { key: '1', label: '1' },
          { key: '2', label: '2' },
          { key: '3', label: '3' },
          { key: '4', label: '4' },
        ]}
        value="1"
        onChange={onChange}
      />
    );
    await userEvent.click(screen.getByRole('radio', { name: 'Bu konuyu ne kadar iyi biliyorsun — 3' }));
    expect(onChange).toHaveBeenCalledWith('3');
  });

  it('seçili seçenek aria-checked=true, diğerleri false taşır', () => {
    paper(
      <SegmentedControl
        options={[
          { key: 'aylik', label: 'Aylık' },
          { key: 'yillik', label: 'Yıllık' },
        ]}
        value="aylik"
        onChange={() => {}}
      />
    );
    expect(screen.getByRole('radio', { name: 'Aylık' })).toHaveAttribute('aria-checked', 'true');
    expect(screen.getByRole('radio', { name: 'Yıllık' })).toHaveAttribute('aria-checked', 'false');
  });

  it('pill: rozet içeriği render edilir', () => {
    paper(
      <SegmentedControl
        options={[
          { key: 'aylik', label: 'Aylık' },
          { key: 'yillik', label: 'Yıllık', badge: <span>2 ay bedava</span> },
        ]}
        value="aylik"
        onChange={() => {}}
      />
    );
    expect(screen.getByText('2 ay bedava')).toBeInTheDocument();
  });

  it('axe: pill (adlandırılmış grup) ihlal yok', async () => {
    const { container } = paper(
      <SegmentedControl
        ariaContext="Fatura dönemi"
        options={[
          { key: 'aylik', label: 'Aylık' },
          { key: 'yillik', label: 'Yıllık' },
        ]}
        value="aylik"
        onChange={() => {}}
      />
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: scale ölçeği ihlal yok', async () => {
    const { container } = paper(
      <SegmentedControl
        variant="scale"
        ariaContext="Bu konuyu ne kadar iyi biliyorsun"
        options={[
          { key: '1', label: '1' },
          { key: '2', label: '2' },
          { key: '3', label: '3' },
          { key: '4', label: '4' },
        ]}
        value="2"
        onChange={() => {}}
      />
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
