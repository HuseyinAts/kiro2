import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';

import { SideNav } from './SideNav';
import { KiroThemeProvider } from './theme';

expect.extend(toHaveNoViolations);

// SideNav çalışma yüzeyi = paper (bileşen temayı okumaz ama kanon sarma paper).
const paper = (ui: React.ReactNode) => render(<KiroThemeProvider theme="paper">{ui}</KiroThemeProvider>);

describe('SideNav', () => {
  it('öğrenci navında bölüm öğeleri link olarak render edilir', () => {
    paper(<SideNav role="ogrenci" activeId="panel" userName="Zeynep Kaya" userSub="TYT · 12. Sınıf" />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Panel' })).toBeInTheDocument();
    // Ödevlerim öğrenci navında zorunlu (ödev döngüsü ürün sözü)
    expect(screen.getByRole('link', { name: 'Ödevlerim' })).toBeInTheDocument();
  });

  it('aktif öğe aria-current="page" ile işaretlenir', () => {
    paper(<SideNav role="ogrenci" activeId="solve" userName="Zeynep Kaya" userSub="TYT" />);
    const aktif = screen.getByRole('link', { name: 'Soru Çözme' });
    expect(aktif).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: 'Panel' })).not.toHaveAttribute('aria-current');
  });

  it('veli navı Çocuklarım öğesini gösterir', () => {
    paper(<SideNav role="veli" activeId="overview" userName="Ali Kaya" userSub="Veli" />);
    expect(screen.getByRole('link', { name: 'Çocuklarım' })).toBeInTheDocument();
  });

  it('öğretmen navı Sınıflarım öğesini gösterir', () => {
    paper(<SideNav role="ogretmen" activeId="panel" userName="Ayşe Demir" userSub="Matematik" />);
    expect(screen.getByRole('link', { name: 'Sınıflarım' })).toBeInTheDocument();
  });

  it('renderLink verilince özel eleman render edilir ve tıklanır', async () => {
    const onNav = vi.fn();
    paper(
      <SideNav
        role="ogrenci"
        activeId="panel"
        userName="Zeynep Kaya"
        userSub="TYT"
        renderLink={(item, children, props) => (
          <button type="button" {...props} onClick={() => onNav(item.id)}>
            {children}
          </button>
        )}
      />
    );
    await userEvent.click(screen.getByRole('button', { name: 'Haftalık Plan' }));
    expect(onNav).toHaveBeenCalledWith('plan');
  });

  it('collapsed modda görünür etiket gizlenir, erişilebilir isim korunur', () => {
    paper(<SideNav role="ogrenci" activeId="panel" collapsed userName="Zeynep Kaya" userSub="TYT" />);
    // aria-label üstünden erişilebilir isim durur
    expect(screen.getByRole('link', { name: 'Panel' })).toBeInTheDocument();
    // görünür metin düğümü render edilmez
    expect(screen.queryByText('Haftalık Plan')).not.toBeInTheDocument();
  });

  it('onAssistant düğmesi tıklanınca çağrılır', async () => {
    const onAssistant = vi.fn();
    paper(<SideNav role="ogrenci" activeId="panel" userName="Zeynep Kaya" userSub="TYT" onAssistant={onAssistant} />);
    await userEvent.click(screen.getByRole('button', { name: 'KIRO Asistan' }));
    expect(onAssistant).toHaveBeenCalledTimes(1);
  });

  it('showSettings ile Ayarlar öğesi eklenir', () => {
    paper(<SideNav role="ogretmen" activeId="panel" showSettings userName="Ayşe Demir" userSub="Matematik" />);
    expect(screen.getByRole('link', { name: 'Ayarlar' })).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok (paper)', async () => {
    const { container } = paper(
      <SideNav role="ogrenci" activeId="panel" userName="Zeynep Kaya" userSub="TYT · 12. Sınıf" onAssistant={() => {}} />
    );
    expect(await axe(container)).toHaveNoViolations();
  });

  it('axe: collapsed veli navı ihlal yok', async () => {
    const { container } = paper(
      <SideNav role="veli" activeId="overview" collapsed showSettings userName="Ali Kaya" userSub="Veli" />
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
