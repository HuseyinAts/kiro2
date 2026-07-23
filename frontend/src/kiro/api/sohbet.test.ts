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
