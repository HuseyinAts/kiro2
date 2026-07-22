// ============================================================================
// KIRO2 — Bilgi Atomları (SPRINT5 · KIRO Bilgi Atomlari.dc.html · Grup 4/C)
// Tema = PAPER. SideNav YOK — tek sütun değer-önerisi makalesi (max 820px).
// Anlatı: motor "konuda zayıfsın" demez, tam başarısız ATOMU gösterir.
// Sunucu-otoriter: enZayif atom yanıttan gelir (markEnZayif) — istemci min-hesabı YOK.
// Rota: /atomlar?konu= · drill-down hedefi (Öğrenme Yolu + Panel).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getTopics, getTopicAtoms } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import type { AtomKirilim, Topic } from '../types';
import { color, font, shadow } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { MasteryBadge } from '../ui/MasteryBadge';
import { Skeleton } from '../ui/Skeleton';
import { useReducedMotion } from '../ui/ConfettiDawn';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const VARSAYILAN_KONU = 'Türev';

function ilkKonu(): string {
  try {
    return new URLSearchParams(window.location.search).get('konu') || VARSAYILAN_KONU;
  } catch {
    return VARSAYILAN_KONU;
  }
}

const Im = {
  chevron: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C4BBAE" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="m9 6 6 6-6 6" /></svg>
  ),
  alert: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9A5D0D" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="12" cy="12" r="9" /><path d="M12 8v4M12 16h.01" /></svg>
  ),
  check: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#1FB683" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden><polyline points="20 6 9 17 4 12" /></svg>
  ),
  play: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5Z" /></svg>
  ),
};

export function BilgiAtomlariPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const [sel, setSel] = React.useState<string>(ilkKonu);
  const [topics, setTopics] = React.useState<Topic[] | null>(null);
  const [kir, setKir] = React.useState<AtomKirilim | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  // Veri çekme (PanelPage deseni): topics (chip listesi) + seçili konunun atom kırılımı.
  // Promise.all → topics çözülünce kir de kesin çözülmüştür (obje = içerik, null = boş).
  React.useEffect(() => {
    let alive = true;
    setTopics(null);
    setKir(null);
    setHata(false);
    Promise.all([getTopics(), getTopicAtoms(sel)])
      .then(([ts, k]) => { if (alive) { setTopics(ts); setKir(k); } })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [sel, yeniden]);

  const secKonu = React.useCallback((konu: string) => {
    setSel(konu);
    try {
      const u = new URL(window.location.href);
      u.searchParams.set('konu', konu);
      window.history.replaceState(null, '', u.toString());
    } catch {
      // jsdom / SSR — URL güncellemesi yoksa sessizce geç (state zaten değişti).
    }
  }, []);

  const zayifKonular = (topics ?? []).filter((t) => t.durum === 'zayif' || t.durum === 'gelisiyor');
  // enZayif SUNUCUDAN gelir (markEnZayif) — istemci min-hesabı YAPMAZ.
  const zayifAtom = kir?.atomlar.find((a) => a.enZayif) ?? kir?.atomlar[0];
  const atomAd = zayifAtom?.ad ?? '';
  const digerCount = kir ? Math.max(0, kir.atomlar.length - 1) : 0;
  const kavramHeader = kir ? kir.kavram.toLocaleUpperCase('tr-TR') + ' · ATOMLAR' : '';
  const bosMu = !kir || kir.atomlar.length === 0 || !zayifAtom;

  return (
    <KiroThemeProvider theme="paper">
      <style>{
        '@keyframes kiroPulseA{0%,100%{box-shadow:0 0 0 0 rgba(199,122,30,0.4)}50%{box-shadow:0 0 0 8px rgba(199,122,30,0)}}' +
        '@media (prefers-reduced-motion: reduce){.kiro-atom-pulse{animation:none!important}}'
      }</style>
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary }}>
        <main style={{ maxWidth: 820, margin: '0 auto', padding: '34px 30px 70px', boxSizing: 'border-box' }}>

          {/* Başlık — statik anlatı (veri gerektirmez) */}
          <header style={{ marginBottom: 20 }}>
            <span style={{ display: 'inline-block', fontSize: 11, fontWeight: 800, letterSpacing: '0.14em', color: '#E0593F', textTransform: 'uppercase' }}>Konu Değil · Tam Adım</span>
            <h1 style={{ margin: '11px 0 6px', fontFamily: font.serif, fontSize: 38, lineHeight: 1.06, fontWeight: 400 }}>Bilgi Atomları</h1>
            <p style={{ margin: 0, fontSize: 15, color: color.ink.muted, maxWidth: 600, lineHeight: 1.6 }}>
              Motor "Türev'de zayıfsın" demez — konuyu ince atomlara böler ve <strong style={{ color: color.ink.primary }}>tam başarısız adımı</strong> gösterir. Böylece <span style={numText}>12</span> soru boşa değil, doğru yere gider.
            </p>
          </header>

          {/* 3-durum merdiveni: error → loading → empty → içerik */}
          {hata ? (
            <ErrorState serifTitle="Atomların şu an gelmedi." onRetry={() => setYeniden((n) => n + 1)} />
          ) : topics === null ? (
            <div aria-busy="true" aria-label="Atomlar yükleniyor">
              <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 22 }}>
                <Skeleton shape="card" delayMs={0} />
              </div>
            </div>
          ) : bosMu ? (
            <EmptyState
              serifTitle="Bu konunun atom kırılımı hazırlanıyor."
              body="Motor bu konuyu ince adımlara ayırınca burada göreceksin. Şimdilik başka bir odak konu seçebilirsin."
            />
          ) : (
            <>
              {/* Odak konu chip'leri — radiogroup (spec §C a11y) */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 14 }}>
                <span style={{ fontSize: 11.5, fontWeight: 700, color: color.ink.muted, marginRight: 2 }}>Odak konu:</span>
                <div role="radiogroup" aria-label="Odak konu" style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  {zayifKonular.map((t) => {
                    const aktif = t.ad === sel;
                    return (
                      <button
                        key={t.ders + '·' + t.ad}
                        type="button"
                        role="radio"
                        aria-checked={aktif}
                        onClick={() => secKonu(t.ad)}
                        style={{
                          display: 'inline-flex', alignItems: 'center', minHeight: 44, padding: '0 15px',
                          borderRadius: 999, cursor: 'pointer', fontFamily: font.sans, fontSize: 12.5,
                          ...(aktif
                            ? { background: '#E0593F', color: '#fff', fontWeight: 700, border: 'none', boxShadow: '0 3px 0 #B8472E' }
                            : { background: '#fff', color: color.ink.muted, fontWeight: 600, border: `1px solid ${color.paper.border}` }),
                        }}
                      >
                        {t.ad}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Breadcrumb: konu → kavram → zayıf atom (amber vurgu) */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap', background: '#FFFFFF', border: '1px solid #ECE6DD', borderRadius: 14, padding: '14px 18px', marginBottom: 16 }}>
                <span style={{ fontSize: 13.5, fontWeight: 700, color: color.ink.muted }}>{kir!.konu}</span>
                {Im.chevron}
                <span style={{ fontSize: 13.5, fontWeight: 700, color: color.ink.muted }}>{kir!.kavram}</span>
                {Im.chevron}
                <span style={{ fontSize: 13.5, fontWeight: 800, color: '#9A5D0D', background: 'rgba(199,122,30,0.12)', padding: '3px 10px', borderRadius: 8 }}>{atomAd}</span>
              </div>

              {/* Atom listesi */}
              <div style={{ background: '#FFFFFF', border: '1px solid #ECE6DD', borderRadius: 16, padding: 20, marginBottom: 16 }}>
                <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: '0.1em', color: color.ink.muted, marginBottom: 14 }}>{kavramHeader}</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {kir!.atomlar.map((a) => {
                    const weak = !!a.enZayif;
                    return (
                      <div
                        key={a.ad}
                        className={weak ? 'kiro-atom-pulse' : undefined}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 13, padding: '12px 14px', borderRadius: 12,
                          background: weak ? 'rgba(199,122,30,0.07)' : '#FBF7F1',
                          border: `1px solid ${weak ? 'rgba(199,122,30,0.35)' : '#ECE6DD'}`,
                          animation: weak && !reduced ? 'kiroPulseA 2s ease-out infinite' : undefined,
                        }}
                      >
                        <span aria-hidden style={{ width: 26, height: 26, flexShrink: 0, borderRadius: 8, background: weak ? 'rgba(199,122,30,0.14)' : 'rgba(31,182,131,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {weak ? Im.alert : Im.check}
                        </span>
                        <span style={{ flex: 1, minWidth: 0, fontSize: 13.5, fontWeight: 700, color: color.ink.primary }}>{a.ad}</span>
                        <MasteryBadge pct={a.hakimiyet} trend={weak ? 'down' : 'up'} />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* İçgörü kutusu — özel gradyan (amber dolgu kanonu; DC birebir) */}
              <div style={{ background: 'linear-gradient(150deg,#FFF3EE,#FFFFFF)', border: '1px solid #F2D9CE', borderLeft: '3px solid #C77A1E', borderRadius: 14, padding: '18px 20px', marginBottom: 16 }}>
                <p style={{ margin: 0, fontSize: 14.5, color: color.ink.primary, lineHeight: 1.6 }}>
                  <strong>Sorun {kir!.konu} değil</strong> — sadece <strong style={{ color: '#9A5D0D' }}>{atomAd} adımında</strong> zayıfsın. Motor bugünkü <span style={numText}>12</span> soruyu tam bu atoma ayırdı; diğer <span style={numText}>{digerCount}</span> atomun sağlam, onlarla vakit harcamıyoruz.
                </p>
              </div>

              {/* CTA — ported rota /soru-cozme (gerçek çapa) + coral AA (#C2452B dolgu + beyaz) */}
              <a
                href="/soru-cozme"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 9, minHeight: 48, padding: '0 24px',
                  borderRadius: 13, background: color.dawn.coralCtaBg, color: '#fff',
                  fontFamily: font.sans, fontSize: 14.5, fontWeight: 800, textDecoration: 'none', boxShadow: shadow.coralCta,
                }}
              >
                <span>{atomAd} atomunu çöz (<span style={numText}>12</span> soru)</span>
                {Im.play}
              </a>
            </>
          )}
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default BilgiAtomlariPage;
