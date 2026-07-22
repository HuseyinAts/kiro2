import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { Button } from './Button';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('Button', () => {
  it('tıklanınca onClick tetiklenir', async () => {
    const onClick = vi.fn();
    paper(<Button onClick={onClick}>Devam et</Button>);
    await userEvent.click(screen.getByRole('button', { name: 'Devam et' }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('disabled iken onClick tetiklenmez', async () => {
    const onClick = vi.fn();
    paper(
      <Button disabled onClick={onClick}>
        Devam et
      </Button>
    );
    await userEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('ikon-yalnız buton aria-label ile erişilebilir isim taşır', () => {
    paper(<Button variant="ghost" ariaLabel="Kapat" icon={<svg aria-hidden width="14" height="14" />} />);
    expect(screen.getByRole('button', { name: 'Kapat' })).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = paper(<Button>Devam et</Button>);
    expect(await axe(container)).toHaveNoViolations();
  });
});
