// ============================================================================
// SPRINT11 · AI Sohbet + Sokratik AI — çift-kollu streaming sözleşmesi (mock kolu).
// streamSohbet mock kolu setTimeout scripted token akışı üretir → fake-timer ile
// deterministik doğrulanır. Sunucu-otorite: yanıt server-sim'den (istemci cevap
// UYDURMAZ); socratic cevabı VERMEZ (kiro-data.sokratik yönlendirici sorular).
// ============================================================================
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  configureKiroApi, getSohbet, postSohbetMesaj, streamSohbet,
  type MockData,
} from './api-client';
import type { SohbetMesaj } from '../types';
import kiroData from './kiro-data.json';

const D = kiroData as unknown as MockData;

function useMock(): void {
  configureKiroApi({ mode: 'mock', mockData: D });
}

afterEach(() => {
  vi.useRealTimers();
});

describe('SPRINT11 · getSohbet / postSohbetMesaj (mock)', () => {
  it('getSohbet direct: açılış oturumu (AI, SEN dili) döner', async () => {
    useMock();
    const o = await getSohbet();
    expect(o.id).toBe('oturum-1');
    expect(o.mesajlar.length).toBeGreaterThan(0);
    expect(o.mesajlar[0]!.rol).toBe('ai');
    // Absence-dili yok (kanon)
    expect(o.mesajlar[0]!.metin).not.toMatch(/eksik/i);
  });

  it('getSohbet socratic: açılış cevabı VERMEZ, "Sokratik" etiketli', async () => {
    useMock();
    const o = await getSohbet('socratic');
    expect(o.mesajlar[0]!.tag).toBe('Sokratik');
    expect(o.mesajlar[0]!.metin).toBe(D.sokratik.acilis);
  });

  it('postSohbetMesaj socratic: AI yanıtı yönlendirici (cevabı vermez) + tag', async () => {
    useMock();
    const m = await postSohbetMesaj({ metin: 'Türev nedir?', teaching: 'socratic' });
    expect(m.rol).toBe('ai');
    expect(m.tag).toBe('Sokratik');
    // Yönlendirici soru içerir — sonucu söylemez
    expect(m.metin).toContain(D.sokratik.adimlar[0]!);
  });

  it('postSohbetMesaj direct: yöntemi anlatan AI yanıtı (tag yok)', async () => {
    useMock();
    const m = await postSohbetMesaj({ metin: 'x', teaching: 'direct' });
    expect(m.rol).toBe('ai');
    expect(m.tag).toBeUndefined();
    expect(m.metin.length).toBeGreaterThan(0);
  });
});

describe('SPRINT11 · streamSohbet mock kolu (setTimeout scripted token akışı)', () => {
  it('onConnected → onToken×N → onFinished; token birleşimi tam metni kurar', () => {
    vi.useFakeTimers();
    useMock();
    const tokens: string[] = [];
    let connectedId = '';
    let finished: SohbetMesaj | undefined;
    const unsub = streamSohbet(
      { oturumId: 'oturum-1', metin: 'Türev nedir?', teaching: 'socratic' },
      {
        onConnected: (id) => { connectedId = id; },
        onToken: (t) => tokens.push(t),
        onFinished: (m) => { finished = m; },
      },
    );
    vi.runAllTimers();
    expect(connectedId).toBe('oturum-1');
    expect(tokens.length).toBeGreaterThan(0);
    expect(finished).toBeDefined();
    // Reconstruction: token akışı finished.metin'i birebir kurar
    expect(tokens.join('')).toBe(finished!.metin);
    // socratic → yönlendirici (cevabı vermez) + tag
    expect(finished!.rol).toBe('ai');
    expect(finished!.tag).toBe('Sokratik');
    expect(finished!.metin).toContain(D.sokratik.adimlar[0]!);
    unsub();
  });

  it('unsubscribe token akışını durdurur (timer temizlenir)', () => {
    vi.useFakeTimers();
    useMock();
    const tokens: string[] = [];
    let finished: SohbetMesaj | undefined;
    let connectedId = '';
    const unsub = streamSohbet(
      { metin: 'x', teaching: 'direct' },
      {
        onConnected: (id) => { connectedId = id; },
        onToken: (t) => tokens.push(t),
        onFinished: (m) => { finished = m; },
      },
    );
    unsub(); // hemen iptal — hiçbir timer çalışmamalı
    vi.runAllTimers();
    expect(connectedId).toBe('');
    expect(tokens).toHaveLength(0);
    expect(finished).toBeUndefined();
  });

  it('direct ve socratic farklı metin üretir; direct sonuç UYDURMAZ (yöntem verir)', () => {
    vi.useFakeTimers();
    useMock();
    const grab = (teaching: 'direct' | 'socratic'): string => {
      let m = '';
      streamSohbet({ metin: 'x', teaching }, { onFinished: (msg) => { m = msg.metin; } });
      vi.runAllTimers();
      return m;
    };
    const direct = grab('direct');
    const socratic = grab('socratic');
    expect(direct).not.toBe(socratic);
    expect(socratic).toContain(D.sokratik.adimlar[0]!);
    expect(direct).not.toContain(D.sokratik.adimlar[0]!);
  });
});

// ===========================================================================
// F4-S1b · live sözleşme: {success,sessions} zarf-çöz + student_id (backend
// ChatMessageRequest zorunlu alanı) — canlı curl ile doğrulanmış backend şekilleri.
// ===========================================================================
describe('F4-S1b · getSohbet/postSohbetMesaj/streamSohbet (live sözleşme)', () => {
  afterEach(() => {
    configureKiroApi({ mode: 'mock', mockData: D });
  });

  it('getSohbet live: {success,sessions} zarfını çözer, en güncel oturumun (sessions[0]) mesajlarını AYRI uçtan çeker', async () => {
    const calls: string[] = [];
    const fetchImpl = (async (url: string | URL) => {
      const u = String(url);
      calls.push(u);
      if (u.endsWith('/enhanced-chat/sessions')) {
        return {
          ok: true, status: 200,
          json: async () => ({
            success: true,
            sessions: [
              { id: 'yeni-oturum', title: 'Türev', message_count: 2 },
              { id: 'eski-oturum', title: 'Limit', message_count: 1 },
            ],
          }),
        };
      }
      if (u.includes('/enhanced-chat/sessions/yeni-oturum/messages')) {
        return {
          ok: true, status: 200,
          json: async () => ({
            success: true,
            session_id: 'yeni-oturum',
            messages: [
              { id: 'm1', role: 'user', content: 'Türev nedir?' },
              { id: 'm2', role: 'agent', content: 'Birlikte bakalım...' },
            ],
          }),
        };
      }
      throw new Error('beklenmeyen çağrı: ' + u);
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    const o = await getSohbet('direct');

    expect(o.id).toBe('yeni-oturum'); // sessions[0] — backend updated_at DESC (en güncel)
    expect(o.baslik).toBe('Türev');
    expect(o.mesajlar).toHaveLength(2);
    expect(o.mesajlar[0]!.rol).toBe('ben'); // backend 'user' → kiro 'ben'
    expect(o.mesajlar[0]!.metin).toBe('Türev nedir?');
    expect(o.mesajlar[1]!.rol).toBe('ai'); // backend 'agent' → kiro 'ai'
    expect(calls).toHaveLength(2); // /sessions + /sessions/{id}/messages
  });

  it('getSohbet live: oturum yoksa (boş sessions) mesaj ucu ÇAĞRILMAZ, boş oturum döner', async () => {
    const calls: string[] = [];
    const fetchImpl = (async (url: string | URL) => {
      calls.push(String(url));
      return { ok: true, status: 200, json: async () => ({ success: true, sessions: [] }) };
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    const o = await getSohbet('direct');

    expect(o.mesajlar).toHaveLength(0);
    expect(calls).toHaveLength(1); // sadece /sessions
  });

  it('postSohbetMesaj live: student_id gövdeye geçer (backend ChatMessageRequest zorunlu alanı)', async () => {
    let govde: Record<string, unknown> | null = null;
    const fetchImpl = (async (_url: string | URL, init?: RequestInit) => {
      govde = JSON.parse(String(init?.body)) as Record<string, unknown>;
      return {
        ok: true, status: 200,
        json: async () => ({ success: true, data: { response_id: 'r1', message: 'yanıt', session_id: 's1' } }),
      };
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    await postSohbetMesaj({ oturumId: 's1', metin: 'merhaba', teaching: 'direct', studentId: 'STU_abc' });

    expect(govde).toMatchObject({
      session_id: 's1', message: 'merhaba', teaching_mode: 'direct', student_id: 'STU_abc',
    });
  });

  it('streamSohbet live: student_id gövdeye geçer', async () => {
    let govde: Record<string, unknown> | null = null;
    const fetchImpl = (async (_url: string | URL, init?: RequestInit) => {
      govde = JSON.parse(String(init?.body)) as Record<string, unknown>;
      return { ok: true, status: 200, body: null }; // gövde-kontrolü yeterli; akış kapsam dışı
    }) as unknown as typeof fetch;
    configureKiroApi({ mode: 'live', baseUrl: 'http://test', fetchImpl });

    await new Promise<void>((resolve) => {
      streamSohbet(
        { oturumId: 's1', metin: 'merhaba', teaching: 'socratic', studentId: 'STU_abc' },
        { onError: () => resolve() },
      );
    });

    expect(govde).toMatchObject({
      session_id: 's1', message: 'merhaba', teaching_mode: 'socratic', student_id: 'STU_abc',
    });
  });
});
