import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect } from 'vitest';

import { Avatar, AVATAR_PAL } from './Avatar';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);
const dusk = (ui: React.ReactNode) => render(<KiroThemeProvider theme="dusk">{ui}</KiroThemeProvider>);

describe('Avatar', () => {
  it('initials metnini render eder', () => {
    paper(<Avatar initials="AK" />);
    expect(screen.getByText('AK')).toBeInTheDocument();
  });

  it('size değerini width/height (px) olarak uygular', () => {
    paper(<Avatar initials="SM" size={70} />);
    expect(screen.getByText('SM')).toHaveStyle({ width: '70px', height: '70px' });
  });

  it('varsayılan boyut 38px', () => {
    paper(<Avatar initials="DF" />);
    expect(screen.getByText('DF')).toHaveStyle({ width: '38px', height: '38px' });
  });

  it('bg rengini arka plan olarak uygular', () => {
    paper(<Avatar initials="BG" bg={AVATAR_PAL[2]} />);
    expect(screen.getByText('BG')).toHaveStyle({ backgroundColor: AVATAR_PAL[2] });
  });

  it('ring podyum halkasını (solid kenar) ekler; ringsiz avatarda eklenmez', () => {
    paper(
      <>
        <Avatar initials="R1" ring={AVATAR_PAL[5]} />
        <Avatar initials="R2" />
      </>
    );
    const ringli = (screen.getByText('R1').getAttribute('style') ?? '').toLowerCase();
    const ringsiz = (screen.getByText('R2').getAttribute('style') ?? '').toLowerCase();
    expect(ringli).toContain('solid');
    expect(ringsiz).not.toContain('solid');
  });

  it('axe: paper yüzeyde ihlal yok', async () => {
    const { container } = paper(<Avatar initials="AX" />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: dusk yüzeyde podyum ringli avatar ihlal yok', async () => {
    const { container } = dusk(<Avatar initials="DK" size={70} ring={AVATAR_PAL[5]} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
