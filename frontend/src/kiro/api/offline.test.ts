import { afterEach, describe, expect, it } from 'vitest';

import { configureKiroApi, getCevrimdisiDurum } from './api-client';

afterEach(() => {
  configureKiroApi({ mode: 'mock' });
});

// ===========================================================================
// F4-S2 · getCevrimdisiDurum kok-neden fix: kiro '/offline/durum' cagiriyordu,
// backend'de boyle bir yol YOK (gercek yol '/offline/sync-status', backend
// SyncStatusResponse: last_sync_at, pending_results_count, offline_package_
// version — kiro SyncStatus: sonEsitleme, kuyruk, paketler ile ne yol ne alan
// adi ORTUSUYORDU). 'kuyruk' (senkron-olmamis ogeler CIHAZ-yerel) ve 'paketler'
// (adlandirilmis plan/tekrar/soru/video) kavramlari backend'de HIC YOK — uydurma
// YAPILMAZ, dürüst bos liste doner (ekran EmptyState ile zarif gosterir).
// ===========================================================================
describe('F4-S2 · getCevrimdisiDurum (live sözleşme)', () => {
  it('doğru yola gider (/offline/sync-status) ve last_sync_at → saat etiketine çevrilir; kuyruk/paketler dürüst boş', async () => {
    const calls: string[] = [];
    const fetchImpl = (async (url: string | URL) => {
      calls.push(String(url));
      return {
        ok: true, status: 200,
        json: async () => ({
          last_sync_at: '2026-07-25T14:32:00+00:00',
          pending_results_count: 50,
          offline_package_version: '1.0',
        }),
      };
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    const s = await getCevrimdisiDurum();

    expect(calls[0]).toContain('/offline/sync-status');
    expect(calls.some((c) => c.includes('/offline/durum'))).toBe(false);
    expect(s.kuyruk).toEqual([]);
    expect(s.paketler).toEqual([]);
    expect(s.sonEsitleme).toMatch(/^\d{2}:\d{2}$/); // saat:dakika etiketi, ham ISO DEĞİL
  });

  it('last_sync_at yoksa (hiç eşitlenmemiş) kaygı-duyarlı fallback döner', async () => {
    const fetchImpl = (async () => ({
      ok: true, status: 200,
      json: async () => ({ last_sync_at: null, pending_results_count: 0, offline_package_version: '1.0' }),
    })) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    const s = await getCevrimdisiDurum();

    expect(s.sonEsitleme).toBe('Henüz eşitlenmedi');
  });
});
