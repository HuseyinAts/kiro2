import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { Input } from './Input';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('Input', () => {
  it('ariaLabel erişilebilir isim sağlar', () => {
    paper(<Input value="" onChange={() => undefined} ariaLabel="Ad Soyad" />);
    expect(screen.getByRole('textbox', { name: 'Ad Soyad' })).toBeInTheDocument();
  });

  it('placeholder metnini gösterir', () => {
    paper(<Input value="" onChange={() => undefined} ariaLabel="Ad Soyad" placeholder="Adınızı yazın" />);
    expect(screen.getByPlaceholderText('Adınızı yazın')).toBeInTheDocument();
  });

  it('mevcut value input değerine yansır', () => {
    paper(<Input value="Ayşe" onChange={() => undefined} ariaLabel="Ad Soyad" />);
    expect(screen.getByRole('textbox', { name: 'Ad Soyad' })).toHaveValue('Ayşe');
  });

  it('yazınca onChange yeni değerle tetiklenir', async () => {
    const onChange = vi.fn();
    paper(<Input value="" onChange={onChange} ariaLabel="Ad Soyad" />);
    await userEvent.type(screen.getByRole('textbox', { name: 'Ad Soyad' }), 'A');
    expect(onChange).toHaveBeenCalledWith('A');
  });

  it('axe: ariaLabel ile erişilebilirlik ihlali yok', async () => {
    const { container } = paper(
      <Input value="" onChange={() => undefined} ariaLabel="Ad Soyad" placeholder="Adınızı yazın" />
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
