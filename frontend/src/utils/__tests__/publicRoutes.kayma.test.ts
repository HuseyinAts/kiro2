import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { PUBLIC_ROUTES } from '../publicRoutes';

/**
 * KAYMA BEKCISI — PUBLIC_ROUTES <-> App.tsx
 *
 * Liste KURATORLU (bkz. publicRoutes.ts): App.tsx'te ProtectedRoute icermeyen
 * 14 rota var ama yalnizca 9'u anlamsal olarak public. Bu yuzden "listeyi
 * App.tsx'ten TURET" denklemi kurulamaz -- turetme '*' catch-all'i muaf yapar
 * ve kusuru GENISLETIRDI.
 *
 * Kurulabilen uc invaryant var. INVARYANT 1 TEHLIKELI YONU tam olarak yakalar:
 * korumali bir rotanin yanlislikla muaf listesine girmesi.
 *
 * BILINEN BOSLUK (gizlenmedi): App.tsx'e YENI bir public sayfa eklenip listeye
 * yazilmazsa kullanicilar o sayfadan sicratilir ve hicbir test dusmez. Bu
 * anlamsal bir karardir, yapisal olarak civilenemez.
 */

const KOK = resolve(__dirname, '../../..');
const APP = readFileSync(resolve(KOK, 'src/App.tsx'), 'utf-8');

/** <Route ...> bloklarini ayristir: her '<Route' basindan kapanisa kadar. */
function rotaBloklari(): { yol: string; korumali: boolean }[] {
  const satirlar = APP.split('\n');
  const cikti: { yol: string; korumali: boolean }[] = [];
  for (let i = 0; i < satirlar.length; i++) {
    if (!satirlar[i].includes('<Route')) {
      continue;
    }
    let j = i;
    const blok: string[] = [satirlar[i]];
    while (j < satirlar.length - 1 && !/\/>\s*$|<\/Route>/.test(satirlar[j])) {
      j += 1;
      blok.push(satirlar[j]);
    }
    const metin = blok.join('\n');
    const m = metin.match(/path="([^"]+)"/);
    if (m) {
      cikti.push({ yol: m[1], korumali: metin.includes('ProtectedRoute') });
    }
    i = j;
  }
  return cikti;
}

describe('publicRoutes <-> App.tsx kaymasi', () => {
  it('KORLESME GUVENCESI: ayristirici gercekten rota buluyor', () => {
    // Bu assert olmadan asagidaki testler BOS KUME uzerinde gecer ve hicbir sey
    // korumaz. Bu depoda tam bu sinif hata yasandi (S238 XPASS, S246 parents[2],
    // S248 yanlis bundle yolu). 23 Agu olcumu: 82 blok / 67 korumali / 14 public.
    const bloklar = rotaBloklari();
    expect(bloklar.length).toBeGreaterThanOrEqual(60);
    expect(bloklar.filter((b) => b.korumali).length).toBeGreaterThanOrEqual(50);
    expect(bloklar.filter((b) => !b.korumali).length).toBeGreaterThanOrEqual(9);
  });

  it('INVARYANT 1 (tehlikeli yon): muaf listesindeki hicbir rota ProtectedRoute DEGIL', () => {
    const korumali = new Set(rotaBloklari().filter((b) => b.korumali).map((b) => b.yol));
    const ihlal = PUBLIC_ROUTES.filter((y) => korumali.has(y));
    expect(ihlal, `Korumali rota muaf listesinde: ${ihlal.join(', ')}`).toEqual([]);
  });

  it('INVARYANT 2: muaf listesindeki her rota App.tsx"te GERCEKTEN var', () => {
    const tumYollar = new Set(rotaBloklari().map((b) => b.yol));
    const kayip = PUBLIC_ROUTES.filter((y) => !tumYollar.has(y));
    expect(kayip, `App.tsx"te olmayan rota muaf listesinde: ${kayip.join(', ')}`).toEqual([]);
  });

  it('INVARYANT 3: dort cagri yerinin DORDU de yardimciyi kullaniyor', () => {
    // Kopyala-yapistir geri gelmesin: cagri yerlerinden biri tekrar
    // `pathname !== '/login'` yazarsa bu test duser.
    const dosyalar = [
      'src/utils/apiHelpers.ts',
      'src/services/apiClient.ts',
      'src/kiro/api/api-client.ts',
      'src/services/learningStyleService.ts',
    ];
    for (const d of dosyalar) {
      const metin = readFileSync(resolve(KOK, d), 'utf-8');
      expect(metin, `${d} yardimciyi kullanmiyor`).toContain('girisYonlendirmesiGerekli');
      expect(metin, `${d} eski deseni hala tasiyor`).not.toContain("pathname !== '/login'");
    }
  });
});
