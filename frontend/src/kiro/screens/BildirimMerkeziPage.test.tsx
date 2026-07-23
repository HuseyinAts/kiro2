import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { describe, it, expect, vi } from 'vitest';

import * as apiClient from '../api/api-client';
import { BildirimMerkeziPage } from './BildirimMerkeziPage';

expect.extend(toHaveNoViolations);

// NOT: vi.restoreAllMocks() KULLANMA — setup.ts'in global matchMedia vi.fn'ini
// bozar (mockRestore implementation'ı siler → mq.matches undefined). Spy'lar
// mockRejectedValueOnce ile tek çağrıdan sonra kendiliğinden orijinale döner.

describe('BildirimMerkeziPage', () => {
  it('SideNav + başlık render eder', () => {
    render(<BildirimMerkeziPage />);
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('Bildirimler')).toBeInTheDocument();
  });

  it('mock bildirimleri gruplu render eder (Bugün + Bu hafta)', async () => {
    render(<BildirimMerkeziPage />);
    expect(await screen.findByText('3 kartın bugün tekrar zamanında')).toBeInTheDocument();
    expect(screen.getByText('Bugün')).toBeInTheDocument();
    expect(screen.getByText('Bu hafta')).toBeInTheDocument();
    expect(screen.getByText('Mert seni düelloya çağırdı')).toBeInTheDocument();
    expect(screen.getByText('Yeni rozet: Kararlı Başlangıç')).toBeInTheDocument();
  });

  it('okunmamış pili sunucu sayısını gösterir (3 yeni)', async () => {
    render(<BildirimMerkeziPage />);
    await screen.findByText('3 kartın bugün tekrar zamanında');
    expect(screen.getByText('3 yeni')).toBeInTheDocument();
  });

  it('KANON: zayıf-konu bildirimi kaygı-duyarlı kopya taşır (yasak absence-dili yok)', async () => {
    render(<BildirimMerkeziPage />);
    expect(await screen.findByText('Limit konusuna biraz daha zaman ayıralım')).toBeInTheDocument();
    expect(screen.queryByText(/\beksik\b/i)).not.toBeInTheDocument();
  });

  it('tek bildirimi okundu işaretleyince sayaç optimistik düşer (3 → 2)', async () => {
    render(<BildirimMerkeziPage />);
    const satir = await screen.findByRole('button', { name: /3 kartın bugün tekrar zamanında/ });
    expect(screen.getByText('3 yeni')).toBeInTheDocument();
    fireEvent.click(satir);
    expect(await screen.findByText('2 yeni')).toBeInTheDocument();
  });

  it('"Tümünü okundu işaretle" pili gizler (okunmamış 0)', async () => {
    render(<BildirimMerkeziPage />);
    await screen.findByText('3 kartın bugün tekrar zamanında');
    fireEvent.click(screen.getByRole('button', { name: /Tümünü okundu işaretle/ }));
    await waitFor(() => expect(screen.queryByText('3 yeni')).not.toBeInTheDocument());
    // Liste durur, sayaç sıfır: hiçbir "N yeni" pili kalmaz
    expect(screen.queryByText(/\d+ yeni/)).not.toBeInTheDocument();
    expect(screen.getByText('3 kartın bugün tekrar zamanında')).toBeInTheDocument();
  });

  it('"Bildirimleri temizle" boş-durumu açar (serif "Her şey sakin.")', async () => {
    render(<BildirimMerkeziPage />);
    await screen.findByText('3 kartın bugün tekrar zamanında');
    fireEvent.click(screen.getByRole('button', { name: 'Bildirimleri temizle' }));
    expect(await screen.findByText('Her şey sakin.')).toBeInTheDocument();
    expect(screen.queryByText('3 kartın bugün tekrar zamanında')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Panele dön' })).toBeInTheDocument();
  });

  it('yükleme dalı: veri gelmeden aria-busy iskeleti gösterir', async () => {
    render(<BildirimMerkeziPage />);
    // İlk render'da (mikrotask boşalmadan) gruplar=null → iskelet dalı
    expect(screen.getByLabelText('Bildirimler yükleniyor')).toHaveAttribute('aria-busy', 'true');
    // Veri gelince iskelet kalkar (akışı boşalt → act uyarısı yok)
    await screen.findByText('3 kartın bugün tekrar zamanında');
    expect(screen.queryByLabelText('Bildirimler yükleniyor')).not.toBeInTheDocument();
  });

  it('getBildirimler reddi ErrorState açar; retry sonrası liste döner', async () => {
    const spy = vi
      .spyOn(apiClient, 'getBildirimler')
      .mockRejectedValueOnce(new Error('baglanti'));
    render(<BildirimMerkeziPage />);
    // Birincil veri reddi → sakin hata (ErrorState serif başlığı)
    expect(await screen.findByText('Bildirimlerin şu an gelmedi.')).toBeInTheDocument();
    expect(screen.queryByText('3 kartın bugün tekrar zamanında')).not.toBeInTheDocument();
    // Retry: sonraki çağrı gerçek mock'a düşer → liste render olur
    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }));
    expect(await screen.findByText('3 kartın bugün tekrar zamanında')).toBeInTheDocument();
    expect(screen.queryByText('Bildirimlerin şu an gelmedi.')).not.toBeInTheDocument();
    expect(spy).toHaveBeenCalled();
  });

  it('persona (getMe) reddi TÜM ekranı düşürmez; nav "Öğrenci"e düşer, liste render olur', async () => {
    vi.spyOn(apiClient, 'getMe').mockRejectedValueOnce(new Error('persona'));
    render(<BildirimMerkeziPage />);
    // Birincil veri geldiği için liste render olur; hata durumu tetiklenmez
    expect(await screen.findByText('3 kartın bugün tekrar zamanında')).toBeInTheDocument();
    expect(screen.queryByText('Bildirimlerin şu an gelmedi.')).not.toBeInTheDocument();
    // Nav fallback
    expect(screen.getByText('Öğrenci')).toBeInTheDocument();
  });

  it('axe: erişilebilirlik ihlali yok', async () => {
    const { container } = render(<BildirimMerkeziPage />);
    await screen.findByText('3 kartın bugün tekrar zamanında');
    expect(await axe(container)).toHaveNoViolations();
  }, 20000);
});
