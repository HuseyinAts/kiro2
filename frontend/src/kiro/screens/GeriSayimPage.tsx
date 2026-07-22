// kanon-allow: kutlama
// ============================================================================
// KIRO2 — Sınav Geri Sayım (SPRINT7 §A · KIRO2 Sinav Geri Sayim.dc.html · DUSK)
// Ufuk-batımı göğü (Bugün'den farklı radyal) + güneş glow (sunGlow 6s) + 5 yıldız.
// İKİ VARYANT (ürünün kalbi): 'kaygi-notr' (B · VARSAYILAN — sayı yok, "Bugüne bak")
// vs 'geri-sayim' (A · dev gün sayısı). Prop korunur (Ayarlar toggle + PostHog A/B, S8).
// Tek kaynak: /me.persona → gunKalan/haftaKalan util (SPRINT6 açık-nokta #3 çözümü).
// Dev sayı aria-live DEĞİL (oturumda değişmez); B'de countdown/sıralama SR'de de yok.
// Ambient gökyüzü hareketi (>600ms) MEŞRU → kanon-allow: kutlama. Tümü RM-guard'lı.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getMe } from '../api/api-client';
import type { MockData } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { gunKalan, haftaKalan } from '../lib/gunSayaci';
import type { Persona } from '../types';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText, useReducedMotion, Skeleton, ErrorState } from '../ui';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

// Ufuk-batımı göğü — Bugün hub'ından bilinçli olarak FARKLI (SPRINT7 §A).
const SKY =
  'radial-gradient(135% 108% at 50% 122%, #FFB07A 0%, #FF7E6B 10%, #C2506F 30%, #5B2F66 58%, #1A0F26 100%)';
const ACCENT = '#FF8A5B';

// Serif "gündoğumu kaldı" varsayılan birim (A) + varsayılan mantra (prop'suz sabit).
const BIRIM = 'gündoğumu';
const MANTRA = 'Uzak görünen şafak, her sabah biraz daha yakın.';

// Dekoratif gece yıldızları (aria-hidden; tw reduced'ta kapalı) — DC birebir konumlar.
const YILDIZLAR = [
  { top: 60, left: '14%', size: 3, dur: '4s', delay: '0s' },
  { top: 110, left: '82%', size: 2, dur: '5s', delay: '0.6s' },
  { top: 150, left: '32%', size: 2, dur: '4.5s', delay: '1.1s' },
  { top: 80, left: '60%', size: 2.5, dur: '5.5s', delay: '0.3s' },
  { top: 180, left: '72%', size: 2, dur: '4.2s', delay: '1.6s' },
];

// @keyframes BİREBİR (DC) — güneş nabzı + yıldız titreşimi. JS'te `reduced` ile kapanır.
const KEYFRAMES = `
@keyframes gsSunGlow { 0%,100% { opacity:0.85; transform:translateX(-50%) scale(1); } 50% { opacity:1; transform:translateX(-50%) scale(1.05); } }
@keyframes gsTw { 0%,100% { opacity:0.25; } 50% { opacity:0.9; } }
`;

function useMedia(query: string): boolean {
  const [esles, setEsles] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia(query);
    const on = () => setEsles(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return esles;
}

/** Sınav günü (kısa) — "20 Haziran 2027". */
function fmtTarih(iso: string): string {
  const d = new Date(iso + 'T00:00:00');
  return new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }).format(d);
}
/** Bugün (uzun) — "22 Temmuz 2026 Çarşamba" (B eyebrow). */
function fmtUzun(d: Date): string {
  return new Intl.DateTimeFormat('tr-TR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(d);
}
const trBin = (n: number): string => n.toLocaleString('tr-TR');

// Cam chip (3'lü şerit) — DC birebir.
function Chip({ deger, etiket }: { deger: React.ReactNode; etiket: string }): React.ReactElement {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        minWidth: 104,
        padding: '15px 18px',
        borderRadius: 16,
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(255,240,230,0.13)',
        backdropFilter: 'blur(6px)',
        boxSizing: 'border-box',
      }}
    >
      <span style={{ ...numText, fontSize: 26, fontWeight: 800, color: '#FFF6EC', lineHeight: 1 }}>{deger}</span>
      <span style={{ fontSize: 12, color: 'rgba(251,239,230,0.62)', fontWeight: 600, marginTop: 5 }}>{etiket}</span>
    </div>
  );
}

export function GeriSayimPage(
  { varyant = 'kaygi-notr' }: { varyant?: 'kaygi-notr' | 'geri-sayim' } = {},
): React.ReactElement {
  const notr = varyant === 'kaygi-notr';
  const reduced = useReducedMotion();
  const dar = useMedia('(max-width: 480px)');
  const px = dar ? 20 : 34;

  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const baslikRef = React.useRef<HTMLHeadingElement>(null);

  // Tek kaynak: getMe() → persona (yksTarihi, seri, seriRekor, hedef üçlüsü, gunlukHedefDk).
  React.useEffect(() => {
    let alive = true;
    setPersona(null);
    setHata(false);
    Promise.all([getMe()])
      .then(([p]) => { if (alive) setPersona(p); })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // Başlığa programatik odak (ekran okuyucu girişi) — veri geldiğinde.
  React.useEffect(() => {
    if (persona) baslikRef.current?.focus();
  }, [persona]);

  return (
    <KiroThemeProvider theme="dusk">
      <div
        className="k-dusk"
        style={{
          minHeight: '100vh',
          background: SKY,
          color: color.dusk.textWarm,
          fontFamily: font.sans,
          position: 'relative',
          overflowX: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxSizing: 'border-box',
        }}
      >
        <style>{KEYFRAMES}</style>

        {/* Güneş glow (dekoratif) — sunGlow reduced'ta durur, merkez korunur */}
        <div
          aria-hidden
          style={{
            position: 'absolute',
            left: '50%',
            bottom: -190,
            width: 660,
            height: 660,
            borderRadius: '50%',
            transform: 'translateX(-50%)',
            background: 'radial-gradient(circle, rgba(255,216,164,0.9), rgba(255,150,110,0.22) 46%, transparent 70%)',
            pointerEvents: 'none',
            zIndex: 0,
            animation: reduced ? undefined : 'gsSunGlow 6s ease-in-out infinite',
          }}
        />
        {/* Yıldızlar (dekoratif) */}
        {YILDIZLAR.map((y, i) => (
          <div
            key={i}
            aria-hidden
            style={{
              position: 'absolute',
              top: y.top,
              left: y.left,
              width: y.size,
              height: y.size,
              borderRadius: '50%',
              background: '#fff',
              zIndex: 1,
              animation: reduced ? undefined : `gsTw ${y.dur} ease-in-out ${y.delay} infinite`,
            }}
          />
        ))}

        {/* Üst bar */}
        <header style={{ position: 'relative', zIndex: 2, display: 'flex', alignItems: 'center', gap: 14, padding: `22px ${px}px` }}>
          <a
            href="/bugun"
            style={{ display: 'flex', alignItems: 'center', gap: 11, minHeight: 44, textDecoration: 'none', color: 'inherit' }}
          >
            <div
              style={{
                width: 38,
                height: 38,
                flexShrink: 0,
                borderRadius: 11,
                background: 'rgba(255,255,255,0.14)',
                backdropFilter: 'blur(6px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M12 3 3 8l9 5 9-5-9-5Z" />
                <path d="M3 16l9 5 9-5" />
                <path d="M3 12l9 5 9-5" />
              </svg>
            </div>
            <div style={{ lineHeight: 1.1 }}>
              <div style={{ fontWeight: 800, fontSize: 15, letterSpacing: '-0.01em' }}>
                KIRO<span style={{ color: '#FFC59B' }}>2</span>
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'rgba(251,239,230,0.6)' }}>Sınava Geri Sayım</div>
            </div>
          </a>
          <div style={{ flex: 1 }} />
          {persona ? (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                height: 36,
                padding: '0 13px',
                borderRadius: 999,
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,240,230,0.16)',
                backdropFilter: 'blur(6px)',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFB570" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" />
              </svg>
              <span style={{ ...numText, fontWeight: 800, fontSize: 14, color: '#FFD9B8' }}>{persona.seri}</span>
              <span style={{ fontSize: 12, color: 'rgba(251,239,230,0.6)', fontWeight: 600 }}>gün</span>
            </div>
          ) : null}
        </header>

        {/* Ana içerik */}
        <main
          className="rpadc"
          style={{
            position: 'relative',
            zIndex: 2,
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: `14px ${px}px 64px`,
            maxWidth: 840,
            width: '100%',
            margin: '0 auto',
            boxSizing: 'border-box',
          }}
        >
          {hata ? (
            <div style={{ width: '100%', maxWidth: 440, boxSizing: 'border-box' }}>
              <ErrorState
                serifTitle="Geri sayım şu an gelmedi — senlik bir şey değil."
                body="Bağlantı bir soluklandı, ilerlemen güvende. Hazır olduğunda tekrar dene."
                onRetry={() => setYeniden((n) => n + 1)}
                retryLabel="Yeniden dene"
              />
            </div>
          ) : persona === null ? (
            <div
              aria-busy="true"
              aria-label="Geri sayım hazırlanıyor"
              style={{ width: '100%', maxWidth: 440, display: 'flex', flexDirection: 'column', gap: 18, alignItems: 'center', boxSizing: 'border-box' }}
            >
              <Skeleton shape="bar" width="55%" delayMs={0} />
              <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
            </div>
          ) : (
            (() => {
              const tarih = fmtTarih(persona.yksTarihi);
              const gun = gunKalan(persona.yksTarihi);
              const hafta = haftaKalan(persona.yksTarihi);
              const hedefSira = trBin(persona.hedefSiralama);
              const guncelSira = trBin(persona.guncelSiralama);
              const gunlukDk = persona.gunlukHedefDk;

              return (
                <>
                  {notr ? (
                    // ===== B · KAYGI-NÖTR (varsayılan) — sayı/sıralama HİÇ geçmez =====
                    <>
                      <div style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.16em', color: ACCENT, textTransform: 'uppercase', marginBottom: 16 }}>
                        BUGÜN · {fmtUzun(new Date())}
                      </div>
                      <h1
                        ref={baslikRef}
                        tabIndex={-1}
                        style={{
                          margin: 0,
                          fontFamily: font.serif,
                          fontStyle: 'italic',
                          fontWeight: 400,
                          fontSize: 'clamp(38px, 7vw, 66px)',
                          lineHeight: 1.05,
                          letterSpacing: '-0.01em',
                          color: '#FFF6EC',
                          textShadow: '0 8px 40px rgba(255,150,110,0.3)',
                          maxWidth: 660,
                          outline: 'none',
                        }}
                      >
                        Bugüne bak.
                        <br />
                        Gün saymaya gerek yok.
                      </h1>
                      <p style={{ fontSize: 18, color: 'rgba(251,239,230,0.82)', maxWidth: 540, margin: '24px 0 0', lineHeight: 1.6 }}>
                        Sınav uzak bir tehdit değil — ufuktaki sabit bir gün. Sen bugüne odaklan; yarıştığın tek kişi dünkü sen.
                      </p>

                      {/* Sınav günü: sayaç değil, sabit bir ufuk */}
                      <div
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 9,
                          marginTop: 24,
                          height: 40,
                          padding: '0 18px',
                          borderRadius: 999,
                          background: 'rgba(255,255,255,0.07)',
                          border: '1px solid rgba(255,240,230,0.16)',
                          backdropFilter: 'blur(6px)',
                        }}
                      >
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#FFB570" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                          <circle cx="12" cy="12" r="4" />
                          <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6 17 7M7 17l-1.4 1.4" />
                        </svg>
                        <span style={{ fontSize: 13.5, fontWeight: 700, color: '#FFD9B8' }}>YKS ufku · {tarih}</span>
                      </div>

                      <div className="rchips" style={{ display: 'flex', gap: 12, marginTop: 30, flexWrap: 'wrap', justifyContent: 'center' }}>
                        <Chip deger={persona.seri} etiket="günlük seri" />
                        <Chip deger={persona.seriRekor} etiket="en uzun seri" />
                        <Chip deger={gunlukDk} etiket="dk · günlük ritim" />
                      </div>
                    </>
                  ) : (
                    // ===== A · GERİ SAYIM (geleneksel) — dev gün sayısı =====
                    <>
                      <div style={{ fontSize: 13, fontWeight: 800, letterSpacing: '0.16em', color: ACCENT, textTransform: 'uppercase', marginBottom: 10 }}>
                        YKS · {tarih}
                      </div>
                      {/* Dev sayı — aria-live DEĞİL (her gün değişir, oturumda değişmez) */}
                      <div
                        style={{
                          ...numText,
                          fontWeight: 800,
                          fontSize: 'clamp(100px, 19vw, 176px)',
                          lineHeight: 0.86,
                          letterSpacing: '-0.03em',
                          color: '#FFF6EC',
                          textShadow: '0 8px 40px rgba(255,150,110,0.35)',
                        }}
                      >
                        {gun}
                      </div>
                      <h1
                        ref={baslikRef}
                        tabIndex={-1}
                        style={{
                          margin: '8px 0 0',
                          fontFamily: font.serif,
                          fontStyle: 'italic',
                          fontWeight: 400,
                          fontSize: 'clamp(28px, 5vw, 36px)',
                          color: '#FFC59B',
                          outline: 'none',
                        }}
                      >
                        {BIRIM} kaldı
                      </h1>
                      <p style={{ fontSize: 18, color: 'rgba(251,239,230,0.8)', maxWidth: 520, margin: '22px 0 0', lineHeight: 1.6 }}>
                        Sınav senin şafağın. Her {BIRIM} bir tuğla — acelesi yok, sen vs dün.
                      </p>

                      <div className="rchips" style={{ display: 'flex', gap: 12, marginTop: 34, flexWrap: 'wrap', justifyContent: 'center' }}>
                        <Chip deger={hafta} etiket="hafta" />
                        <Chip deger={persona.seri} etiket="günlük seri" />
                        <Chip deger={gunlukDk} etiket="dk / gün" />
                      </div>
                    </>
                  )}

                  {/* Hedef kartı (ortak) */}
                  <div
                    style={{
                      marginTop: 22,
                      width: '100%',
                      maxWidth: 440,
                      padding: '20px 24px',
                      borderRadius: 18,
                      background: 'rgba(255,255,255,0.055)',
                      border: '1px solid rgba(255,240,230,0.13)',
                      backdropFilter: 'blur(6px)',
                      textAlign: 'left',
                      boxSizing: 'border-box',
                    }}
                  >
                    <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.1em', color: 'rgba(251,239,230,0.5)', textTransform: 'uppercase', marginBottom: 7 }}>
                      Hedef
                    </div>
                    <div style={{ fontSize: 19, fontWeight: 800, color: '#FFF6EC', letterSpacing: '-0.01em' }}>{persona.hedefBolum}</div>
                    <div style={{ ...numText, fontSize: 13.5, color: 'rgba(251,239,230,0.72)', marginTop: 3 }}>
                      {persona.hedefUni} · ilk {hedefSira}
                    </div>
                    {notr ? (
                      <div style={{ fontSize: 12.5, color: 'rgba(251,239,230,0.55)', marginTop: 10, lineHeight: 1.5 }}>
                        Acele yok — istikrar sıralamadan güçlü. Her gün bir adım yeter.
                      </div>
                    ) : (
                      <div style={{ ...numText, fontSize: 12.5, color: 'rgba(251,239,230,0.55)', marginTop: 10, lineHeight: 1.5 }}>
                        Son denemede {guncelSira}. sıradaydın — her tuğla seni yaklaştırıyor.
                      </div>
                    )}
                  </div>

                  {/* Mantra (serif italik) */}
                  <p style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 21, color: '#FFD9B8', margin: '28px 0 0', maxWidth: 520, lineHeight: 1.4 }}>
                    “{MANTRA}”
                  </p>

                  {/* CTA → Soru Çözme (dusk coral dolgu + koyu mürekkep) */}
                  <a
                    href="/soru-cozme"
                    style={{
                      marginTop: 26,
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 10,
                      height: 54,
                      minHeight: 44,
                      padding: '0 30px',
                      border: 'none',
                      borderRadius: 15,
                      background: ACCENT,
                      color: '#241018',
                      fontFamily: font.sans,
                      fontSize: 15.5,
                      fontWeight: 800,
                      textDecoration: 'none',
                      boxShadow: '0 12px 30px -10px rgba(255,138,91,0.6)',
                      boxSizing: 'border-box',
                    }}
                  >
                    Bugünün tuğlasını koy
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                      <path d="m9 6 6 6-6 6" />
                    </svg>
                  </a>
                </>
              );
            })()
          )}
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default GeriSayimPage;
