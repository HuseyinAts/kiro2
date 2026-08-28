import { afterEach, describe, expect, it } from 'vitest';

import { configureKiroApi, getKvkkNotice, giveConsent } from './api-client';

afterEach(() => {
  configureKiroApi({ mode: 'mock' });
});

// ===========================================================================
// F4-S2 · giveConsent kok-neden fix: backend ConsentGiveRequest 3 zorunlu alan
// ister (purpose:DataProcessingPurpose enum, consent_text:str, privacy_policy_
// version:str — backend/api/kvkk_consent_api.py:36-41). Eski kod tek bir
// serbest-metin `purpose` string'i gonderiyordu (consent_text/privacy_policy_
// version HIC yok, purpose degeri enum'a UYMUYOR) — HER ZAMAN 422 verirdi.
// ===========================================================================
describe('F4-S2 · giveConsent/getKvkkNotice (live sözleşme)', () => {
  it('giveConsent live: 3 zorunlu alanı (purpose=account_management, consent_text, privacy_policy_version) doğru gönderir', async () => {
    let govde: Record<string, unknown> | null = null;
    const fetchImpl = (async (_url: string | URL, init?: RequestInit) => {
      govde = JSON.parse(String(init?.body)) as Record<string, unknown>;
      return { ok: true, status: 200, json: async () => ({ success: true, consent_id: 'c1' }) };
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    await giveConsent({ consentText: 'KVKK aydınlatma metni v3', policyVersion: 'v3' });

    expect(govde).toEqual({
      purpose: 'account_management',
      consent_text: 'KVKK aydınlatma metni v3',
      privacy_policy_version: 'v3',
    });
  });

  it('getKvkkNotice live: backend text alanını da okur (consent_text kaynağı)', async () => {
    const fetchImpl = (async () => ({
      ok: true, status: 200,
      json: async () => ({ version: 'v4', effective_date: '2026-01-01', text: 'Aydınlatma metni.' }),
    })) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    const n = await getKvkkNotice();

    expect(n).toEqual({ version: 'v4', text: 'Aydınlatma metni.' });
  });
});
