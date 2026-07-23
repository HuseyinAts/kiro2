import { render } from '@testing-library/react';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { ROL_LANDING, roleLanding, AuthGate } from './routeGuard';

describe('routeGuard', () => {
  it('roleLanding 3 rol için doğru landing döner', () => {
    expect(roleLanding('ogrenci')).toBe('/panel');
    expect(roleLanding('veli')).toBe('/veli');
    expect(roleLanding('ogretmen')).toBe('/ogretmen');
  });

  it('ROL_LANDING tek kanon eşlemesi', () => {
    expect(ROL_LANDING).toEqual({ ogrenci: '/panel', veli: '/veli', ogretmen: '/ogretmen' });
  });

  it('AuthGate rol null → /giris yönlendirir (kimlik yok)', () => {
    const onRedirect = vi.fn();
    render(React.createElement(AuthGate, { rol: null, onRedirect }));
    expect(onRedirect).toHaveBeenCalledWith('/giris');
  });

  it('AuthGate rol var → rolün landing\'ine yönlendirir', () => {
    const onRedirect = vi.fn();
    render(React.createElement(AuthGate, { rol: 'ogretmen', onRedirect }));
    expect(onRedirect).toHaveBeenCalledWith('/ogretmen');
  });

  it('AuthGate children render eder', () => {
    const onRedirect = vi.fn();
    const { getByText } = render(
      React.createElement(
        AuthGate,
        { rol: 'ogrenci', onRedirect },
        React.createElement('span', null, 'içerik'),
      ),
    );
    expect(getByText('içerik')).toBeInTheDocument();
  });
});
