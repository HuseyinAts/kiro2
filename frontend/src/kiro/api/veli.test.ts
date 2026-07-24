import { afterEach, describe, expect, it } from 'vitest';

import { configureKiroApi, getVeliDashboard } from './api-client';

afterEach(() => {
  configureKiroApi({ mode: 'mock' });
});

// ===========================================================================
// F4-S2 · mapVeliCocuk kok-neden fix: backend ParentChildRelationResponse
// {id:int (relation-id), child_id:str (GERCEK ogrenci id), child_name:str, ...}
// döner (backend/models/parent.py:92-105) — pick() ONCEDEN 'id'/'ad' ariyordu,
// backend'in gercekte gonderdigi 'child_id'/'child_name' hic denenmiyordu.
// Sonuc: ad HER ZAMAN bos + relation-id (orn. "1") ogrenci id'si sanilip
// SONRAKI /parent/children/{id}/performance cagrisina YANLIS id gidiyordu.
// ===========================================================================
describe('F4-S2 · getVeliDashboard/mapVeliCocuk (live sözleşme)', () => {
  it('child_name → ad, child_id → id (relation-id DEĞİL) doğru okunur; performans çağrısı DOĞRU id ile gider', async () => {
    const calls: string[] = [];
    const fetchImpl = (async (url: string | URL) => {
      const u = String(url);
      calls.push(u);
      if (u.endsWith('/parent/dashboard')) {
        return { ok: true, status: 200, json: async () => ({}) };
      }
      if (u.endsWith('/parent/children')) {
        return {
          ok: true, status: 200,
          json: async () => ([
            {
              id: 1, // relation-id — ÖĞRENCİ id'si DEĞİL, mapVeliCocuk bunu SEÇMEMELİ
              parent_id: 'p1',
              child_id: 'child-uuid-123', // GERÇEK öğrenci id — mapVeliCocuk BUNU seçmeli
              child_name: 'Ali Veli',
              child_email: 'ali@eposta.com',
              relation_type: 'parent',
              approved: true,
            },
          ]),
        };
      }
      if (u.includes('/parent/children/child-uuid-123/performance')) {
        return { ok: true, status: 200, json: async () => ({}) };
      }
      throw new Error('beklenmeyen çağrı: ' + u);
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    const d = await getVeliDashboard();

    expect(d.cocuklar).toHaveLength(1);
    expect(d.cocuklar[0]!.ad).toBe('Ali Veli'); // child_name doğru okundu
    expect(d.cocuklar[0]!.id).toBe('child-uuid-123'); // child_id doğru okundu (relation-id '1' DEĞİL)
    expect(d.aktifCocukId).toBe('child-uuid-123');
    // Regresyon kanıtı: performans ucu yanlış id (relation-id '1') İLE ÇAĞRILMADI.
    expect(calls.some((c) => c.includes('/parent/children/1/performance'))).toBe(false);
    expect(calls.some((c) => c.includes('/parent/children/child-uuid-123/performance'))).toBe(true);
  });
});
