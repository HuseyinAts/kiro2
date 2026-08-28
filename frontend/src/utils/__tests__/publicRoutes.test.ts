import { describe, expect, it } from 'vitest';
import { PUBLIC_ROUTES, girisYonlendirmesiGerekli } from '../publicRoutes';

describe('girisYonlendirmesiGerekli', () => {
  it('anonim kullanicinin ait oldugu rotalarda yonlendirme YAPILMAZ', () => {
    for (const yol of [
      '/login',
      '/register',
      '/eposta-dogrula',
      '/veli-onay',
      '/hesap-kurtarma',
      '/forgot-password',
      '/unauthorized',
      '/404',
      '/error',
    ]) {
      expect(girisYonlendirmesiGerekli(yol), yol).toBe(false);
    }
  });

  it('korumali rotalarda yonlendirme YAPILIR', () => {
    for (const yol of [
      '/dashboard',
      '/exam/123/results',
      '/parent/dashboard',
      '/teacher/classes',
    ]) {
      expect(girisYonlendirmesiGerekli(yol), yol).toBe(true);
    }
  });

  it('KORUMALI hedefe Navigate eden yollar muaf DEGIL', () => {
    // App.tsx: '/' ve '*' -> Navigate; '/veli-takip' -> /parent/dashboard.
    // Bunlari muaf saymak catch-all'i muaf yapardi -> kusuru GENISLETIRDI.
    // Spec'in "App.tsx listeden turetsin" onerisi tam bu yuzden reddedildi.
    for (const yol of ['/', '/veli-takip', '/parent-new']) {
      expect(girisYonlendirmesiGerekli(yol), yol).toBe(true);
    }
  });

  it('sondaki egik cizgi ve query/hash kirletmez', () => {
    expect(girisYonlendirmesiGerekli('/eposta-dogrula/')).toBe(false);
    expect(girisYonlendirmesiGerekli('/eposta-dogrula?token=abc')).toBe(false);
    expect(girisYonlendirmesiGerekli('/eposta-dogrula#x')).toBe(false);
  });

  it('buyuk/kucuk harf bypass uretmez', () => {
    // React Router v6 eslesmesi varsayilan olarak buyuk/kucuk harf DUYARSIZ
    // (matchPath caseSensitive: false). Liste duyarli olsaydi /LOGIN sayfasi
    // acilir ama muaf sayilmaz -> sonsuz sicrama.
    expect(girisYonlendirmesiGerekli('/LOGIN')).toBe(false);
    expect(girisYonlendirmesiGerekli('/Eposta-Dogrula')).toBe(false);
  });

  it('bos/bozuk girdi CAGIRANI COKERTMEZ', () => {
    expect(girisYonlendirmesiGerekli('')).toBe(true);
    expect(girisYonlendirmesiGerekli(null)).toBe(true);
    expect(girisYonlendirmesiGerekli(undefined)).toBe(true);
  });

  it('KORLESME GUVENCESI: liste bosalirsa testler bos kume uzerinde gecmez', () => {
    // Bu assert olmadan ustteki "muaf" testi bos listeyle de gecerdi
    // (girisYonlendirmesiGerekli her zaman true doner, ama dongu 0 kez doner).
    expect(PUBLIC_ROUTES.length).toBeGreaterThanOrEqual(9);
  });
});
