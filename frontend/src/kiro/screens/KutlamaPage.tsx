// kanon-allow: kutlama
// ============================================================================
// KIRO2 — Kutlama (SPRINT6 · KIRO2 Kutlama.dc.html · TEMA = DUSK)
// Tören sahnesi: gerçek başarı anında (günlük hedef / seviye / seri / boss).
// Sunucu-otoriter: tür/xp/seri URL paramından; persona (getMe) fallback;
// {konu} = en zayıf mat konu (getTopics). İçerik salt-okur — hesap yapmaz.
// Konfeti ConfettiDawn (reuse) — reduced-motion'da kendi içinde kapanır.
// Ambient tören hareketi (cglow/ctwinkle >600ms) MEŞRU → kanon-allow: kutlama.
// ============================================================================
import * as React from 'react';

import { getMe, getTopics, seviyeBilgiFrom } from '../api/api-client';
import type { MockData } from '../api/api-client';
import type { Persona } from '../types';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText, serifText } from '../ui/theme';
import { ConfettiDawn, useReducedMotion } from '../ui/ConfettiDawn';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

type KutlamaTur = 'gunluk' | 'seviye' | 'seri' | 'boss';
const TURLER: readonly KutlamaTur[] = ['gunluk', 'seviye', 'seri', 'boss'];

// Tür ikon path'leri (bespoke · stroke #2A1018 koyu mürekkep)
const IKON: Record<KutlamaTur, string> = {
  gunluk: 'M20 6 9 17l-5-5',
  seviye: 'M12 2l2.9 6.26 6.9.7-5.13 4.64L18 21l-6-3.5L6 21l1.33-7.4L2.2 8.96l6.9-.7L12 2Z',
  seri: 'M12 2c1.4 3.4 4.4 4.6 4.4 8.2a4.4 4.4 0 0 1-8.8.2c0-1.6.6-2.8 1.3-3.6.2 1.2 1 1.9 1.8 1.9C10.2 6.6 11 4.2 12 2Z',
  boss: 'M12 3 5 6v5c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6l-7-3ZM9 12l2 2 4-4',
};

interface Palet { accent: string; accent2: string; glow: string }
const PALET: Record<KutlamaTur, Palet> = {
  gunluk: { accent: '#FF8A5B', accent2: '#FF5E7E', glow: 'rgba(255,110,120,0.45)' },
  seviye: { accent: '#FFD98C', accent2: '#FF9E7D', glow: 'rgba(255,200,130,0.5)' },
  seri: { accent: '#FF9E7D', accent2: '#F5B84E', glow: 'rgba(255,150,90,0.45)' },
  boss: { accent: '#C9A8E0', accent2: '#8B5CF6', glow: 'rgba(167,123,255,0.5)' }, // mor — kanon-allow boss
};

interface Odul { deger: string; etiket: string; sayi?: boolean }
interface Icerik {
  eyebrow: string;
  baslik: string;
  alt: string;
  oduller: Odul[];
  mantra: string;
  cta: string;
}

interface Degerler {
  bugunDk: number;
  xp: string;
  seviye: number;
  seri: number;
  rekorKalan: number;
  konu: string;
}

function icerikOlustur(tur: KutlamaTur, d: Degerler): Icerik {
  switch (tur) {
    case 'gunluk':
      return {
        eyebrow: 'GÜNLÜK HEDEF',
        baslik: 'Bugünkü tuğlanı koydun.',
        alt: `${d.bugunDk} dakika çalıştın — şafağa bir tuğla daha yakınsın. Yarın da buradayız.`,
        oduller: [{ deger: '+40', etiket: 'XP · bugünkü kazanç', sayi: true }],
        mantra: 'Büyük duvarlar tek tuğlayla yükselir.',
        cta: 'Devam et',
      };
    case 'seviye':
      return {
        eyebrow: 'SEVİYE ATLADIN',
        baslik: `Seviye ${d.seviye}!`,
        alt: `Toplam ${d.xp} XP topladın. Her seviye, dünkü senden bir adım ileride.`,
        oduller: [
          { deger: '+120', etiket: 'XP · seviye ödülü', sayi: true },
          { deger: `Seviye ${d.seviye}`, etiket: 'yeni rütbe', sayi: true },
        ],
        mantra: 'Kıyasladığın tek kişi, dünkü sensin.',
        cta: 'Yoluna devam et',
      };
    case 'seri':
      return {
        eyebrow: 'SERİ KİLOMETRE TAŞI',
        baslik: `${d.seri} günlük seri!`,
        alt: `Rekoruna ${d.rekorKalan} gün kaldı. İstikrar, hızdan daha güçlüdür — sakin devam.`,
        oduller: [{ deger: `${d.seri}`, etiket: 'gün üst üste', sayi: true }],
        mantra: 'Her gün küçük bir söz, kendine tutulmuş.',
        cta: 'Seriyi sürdür',
      };
    case 'boss':
      return {
        eyebrow: 'BOSS ZAFERİ',
        baslik: 'Ejderha yenildi!',
        alt: `${d.konu} ejderhasını alt ettin — en zayıf konun artık senin gücün oluyor.`,
        oduller: [
          { deger: '+120', etiket: 'XP · boss ödülü', sayi: true },
          { deger: d.konu, etiket: 'ustalık rozeti' },
        ],
        mantra: 'Korktuğun konu, en çok büyüdüğün yerdir.',
        cta: 'Zaferi kutla',
      };
  }
}

const KEYFRAMES = `
@keyframes kcpop { 0% { transform: scale(0.7); opacity: 0; } 60% { transform: scale(1.06); } 100% { transform: scale(1); opacity: 1; } }
@keyframes kcglow { 0%, 100% { opacity: 0.85; transform: scale(1); } 50% { opacity: 1; transform: scale(1.07); } }
@keyframes kcup { from { transform: translateY(14px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
@keyframes kctwinkle { 0%, 100% { opacity: 0.25; } 50% { opacity: 0.9; } }
`;

// DC birebir: 4 küçük yuvarlak nokta (üst bölge) — yıldız-glifi/altın DEĞİL
const YILDIZLAR = [
  { top: '8%', left: '16%', boy: 2, renk: '#fff', sure: '4s', gecikme: '0s' },
  { top: '14%', left: '78%', boy: 2.4, renk: '#FFE8C9', sure: '5.5s', gecikme: '0.6s' },
  { top: '22%', left: '40%', boy: 1.6, renk: '#fff', sure: '4.8s', gecikme: '1.2s' },
  { top: '10%', left: '62%', boy: 1.8, renk: '#fff', sure: '5s', gecikme: '0.9s' },
];

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

const OkSvg = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2A1018" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M5 12h14M13 6l6 6-6 6" /></svg>
);

export function KutlamaPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const darEkran = useMedia('(max-width: 560px)');

  // URL paramları (mount'ta tek okuma): type / xp / seri
  const [{ tur, urlXp, urlSeri }] = React.useState(() => {
    const p = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '');
    const t = p.get('type');
    return {
      tur: (t && (TURLER as readonly string[]).includes(t) ? t : 'gunluk') as KutlamaTur,
      urlXp: p.get('xp'),
      urlSeri: p.get('seri'),
    };
  });

  const [data, setData] = React.useState<{ persona: Persona; konu: string } | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const baslikRef = React.useRef<HTMLHeadingElement>(null);

  React.useEffect(() => {
    let alive = true;
    setData(null);
    setHata(false);
    Promise.all([getMe(), getTopics('mat')])
      .then(([persona, topics]) => {
        if (!alive) return;
        const zayif = topics.length
          ? topics.reduce((a, b) => (b.hakimiyet < a.hakimiyet ? b : a), topics[0]!)
          : null;
        setData({ persona, konu: zayif?.ad ?? 'Türev' });
      })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // Başlığa programatik odak (tören açıldığında SR ekranı duyurur)
  React.useEffect(() => {
    if (data) baslikRef.current?.focus();
  }, [data]);

  const p = PALET[tur];

  // cup girişleri — sıralı 0.15s kademeli (reduced'da kapalı)
  const cup = (i: number): React.CSSProperties =>
    reduced ? {} : { animation: `kcup 0.5s cubic-bezier(0.33,0,0.2,1) ${(i * 0.15).toFixed(2)}s both` };

  return (
    <KiroThemeProvider theme="dusk">
      <div
        className="k-dusk"
        style={{
          minHeight: '100vh',
          background: 'radial-gradient(120% 80% at 50% -10%, #3E1F4E, #241640 30%, #16101F 60%, #110C18)',
          color: color.dusk.text,
          fontFamily: font.sans,
          position: 'relative',
          overflowX: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '48px 20px',
          boxSizing: 'border-box',
        }}
      >
        {!reduced && <style>{KEYFRAMES}</style>}

        {/* Yıldızlar (dekoratif) */}
        <div aria-hidden style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 1, overflow: 'hidden' }}>
          {YILDIZLAR.map((y, i) => (
            <div
              key={i}
              style={{
                position: 'absolute',
                top: y.top,
                left: y.left,
                width: y.boy,
                height: y.boy,
                borderRadius: '50%',
                background: y.renk,
                animation: reduced ? undefined : `kctwinkle ${y.sure} ease-in-out ${y.gecikme} infinite`,
              }}
            />
          ))}
        </div>

        {hata ? (
          <div style={{ position: 'relative', zIndex: 3, width: '100%', maxWidth: 480, boxSizing: 'border-box' }}>
            <ErrorState
              serifTitle="Kutlama şu an gelmedi — senlik bir şey değil."
              body="Bağlantı bir soluklandı, kazanımın güvende. Hazır olduğunda tekrar dene."
              onRetry={() => setYeniden((n) => n + 1)}
              retryLabel="Yeniden dene"
            />
          </div>
        ) : data === null ? (
          <div aria-busy="true" aria-label="Kutlama hazırlanıyor" style={{ position: 'relative', zIndex: 3, width: '100%', maxWidth: 420, boxSizing: 'border-box' }}>
            <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
          </div>
        ) : (
          (() => {
            const per = data.persona;
            const gecerliXp = urlXp != null && urlXp !== '' && !Number.isNaN(Number(urlXp));
            const xpNum = gecerliXp ? Number(urlXp) : per.xp;
            const seri = urlSeri != null && urlSeri !== '' && !Number.isNaN(Number(urlSeri)) ? Number(urlSeri) : per.seri;
            // Seviye kutlamasında URL xp'sinden yeniden türet (DC birebir; başlık↔xp tutarlı)
            const seviyeNo = tur === 'seviye' && gecerliXp
              ? seviyeBilgiFrom((kiroData as unknown as MockData).seviyeEsik, xpNum).seviye
              : per.seviye;
            const deg: Degerler = {
              bugunDk: per.bugunCozulenDk,
              xp: xpNum.toLocaleString('tr-TR'),
              seviye: seviyeNo,
              seri,
              rekorKalan: Math.max(0, per.seriRekor - seri),
              konu: data.konu,
            };
            const ic = icerikOlustur(tur, deg);

            return (
              <>
                {/* Konfeti — yalnız gerçek başarı anında (bu ekran zaten kutlama) */}
                <ConfettiDawn count={20} zIndex={2} />

                <div
                  role="status"
                  style={{
                    position: 'relative',
                    zIndex: 3,
                    width: '100%',
                    maxWidth: 560,
                    boxSizing: 'border-box',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                  }}
                >
                  {/* Merkez rozet + halo */}
                  <div aria-hidden style={{ position: 'relative', width: 132, height: 132, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 26 }}>
                    <div
                      style={{
                        position: 'absolute',
                        inset: -30,
                        borderRadius: '50%',
                        background: `radial-gradient(circle, ${p.glow}, transparent 68%)`,
                        animation: reduced ? undefined : 'kcglow 3.4s ease-in-out infinite',
                      }}
                    />
                    <div
                      style={{
                        position: 'relative',
                        width: 104,
                        height: 104,
                        borderRadius: 32,
                        background: `linear-gradient(140deg, ${p.accent}, ${p.accent2})`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: `0 18px 50px -12px ${p.glow}`,
                        animation: reduced ? undefined : 'kcpop 0.6s cubic-bezier(0.33,0,0.2,1) both',
                      }}
                    >
                      <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#2A1018" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                        <path d={IKON[tur]} />
                      </svg>
                    </div>
                  </div>

                  {/* Eyebrow */}
                  <div style={{ ...cup(0), fontSize: 12.5, fontWeight: 800, letterSpacing: '0.18em', color: p.accent, marginBottom: 14 }}>
                    {ic.eyebrow}
                  </div>

                  {/* Başlık (serif, programatik odak) */}
                  <h1
                    ref={baslikRef}
                    tabIndex={-1}
                    style={{
                      ...cup(1),
                      margin: 0,
                      fontFamily: font.serif,
                      fontSize: darEkran ? 40 : 58,
                      lineHeight: 1.05,
                      fontWeight: 400,
                      color: '#FFF6EC',
                      outline: 'none',
                    }}
                  >
                    {ic.baslik}
                  </h1>

                  {/* Alt açıklama */}
                  <p style={{ ...cup(2), margin: '16px 0 0', maxWidth: 460, fontSize: 15.5, lineHeight: 1.6, color: 'rgba(236,228,240,0.82)' }}>
                    {ic.alt}
                  </p>

                  {/* Ödül chip'leri */}
                  <div style={{ ...cup(3), display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center', marginTop: 26 }}>
                    {ic.oduller.map((o, i) => {
                      const bonus = i > 0;
                      return (
                        <div
                          key={o.etiket}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 10,
                            padding: '12px 18px',
                            borderRadius: 14,
                            background: 'rgba(255,255,255,0.06)',
                            border: '1px solid rgba(255,255,255,0.12)',
                            boxSizing: 'border-box',
                          }}
                        >
                          <span style={{ ...(o.sayi ? numText : undefined), fontSize: 22, fontWeight: 800, color: bonus ? color.dawn.gold : p.accent }}>
                            {o.deger}
                          </span>
                          <span style={{ fontSize: 12.5, fontWeight: 600, color: 'rgba(236,228,240,0.7)', textAlign: 'left', lineHeight: 1.3 }}>{o.etiket}</span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Mantra (serif italik) */}
                  <p style={{ ...cup(4), ...serifText, margin: '28px 0 0', fontSize: 18, lineHeight: 1.4, color: p.accent }}>
                    “{ic.mantra}”
                  </p>

                  {/* CTA (koyu mürekkep · tüm türler → Bugün) */}
                  <a
                    href="/bugun"
                    style={{
                      ...cup(5),
                      marginTop: 30,
                      height: 52,
                      minHeight: 44,
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 8,
                      padding: '0 30px',
                      borderRadius: 15,
                      background: `linear-gradient(110deg, ${p.accent}, ${p.accent2})`,
                      color: '#2A1018',
                      fontFamily: font.sans,
                      fontSize: 15.5,
                      fontWeight: 800,
                      textDecoration: 'none',
                      boxShadow: `0 12px 32px -10px ${p.glow}`,
                      boxSizing: 'border-box',
                    }}
                  >
                    {ic.cta}
                    {OkSvg}
                  </a>
                </div>
              </>
            );
          })()
        )}
      </div>
    </KiroThemeProvider>
  );
}

export default KutlamaPage;
