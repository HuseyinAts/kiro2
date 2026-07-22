// ============================================================================
// KIRO2 — Onboarding / misafir yerleştirme (SPRINT2 · KIRO2 Onboarding.dc.html)
// Tema = PAPER. Durum: ton (Adım 1) → calib (Adım 2, 6 soru) → hazir (Adım 3).
// Kopya §C0 ton adımı DC'den BİREBİR; §C calib/hazir SPRINT2_SPEC'ten. Auth GEREKMEZ (misafir).
// Kanon: DC'deki lacivert hover TAŞINMAZ — Button coralCtaBg kullanır; stepper tik bespoke SVG.
// Motorlar SUNUCUDA: live'da yerleştirme /cat/next; MOCK modda catBankMat merdiveni (dogru yerel).
// (ton-adım "Devam et" CTA etiketi DC'den çıkarılamadı — çıkarım; diğer kopya birebir.)
// ============================================================================
import * as React from 'react';

import kiroData from '../api/kiro-data.json';
import { color, font, radius, space } from '../tokens';
import type { CatItem } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { ConfettiDawn } from '../ui/ConfettiDawn';
import '../tokens/tokens.css';

type Adim = 'ton' | 'calib' | 'hazir';
type Ton = 'agir' | 'gelgit' | 'sakin';

const PAGE_BG = 'radial-gradient(1200px 500px at 50% -10%, #FFF3EE 0%, #F1F2F6 60%)';
const SORULAR = (kiroData as unknown as { catBankMat: CatItem[] }).catBankMat.slice(0, 6);

const TON: Record<Ton, { label: string; yanit: string }> = {
  agir: { label: 'Kaygı ağır basıyor', yanit: "Anlaşıldı. Acele etmiyoruz: kısa oturumlar, erken 'oldu' anları. Burada kimse seni sıralamayla sıkıştırmaz — ritmi sen belirlersin." },
  gelgit: { label: 'Değişken — güne göre', yanit: 'Çoğumuz öyleyiz. Plan güne uyar: iyi günde ileri gidersin, zor günde kısa bir tekrar da sayılır.' },
  sakin: { label: 'Genelde sakinim', yanit: 'Güzel. O zaman doğrudan ölçüme geçelim — yol haritan birazdan netleşir.' },
};
const TON_SIRA: Ton[] = ['agir', 'gelgit', 'sakin'];

function sonuc(dogru: number) {
  const seviye = dogru <= 2 ? 'Temel' : dogru === 3 ? 'Orta' : dogru === 4 ? 'Orta-üst' : 'İleri';
  const net = Math.max(180, Math.min(360, 225 + dogru * 13));
  const odak = dogru >= 4 ? 'Türev' : dogru >= 2 ? 'Problemler' : 'Temel İşlemler';
  return { seviye, net, odak };
}

function Tik({ size = 12, renk = '#fff' }: { size?: number; renk?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={renk} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

function Stepper({ adim }: { adim: Adim }) {
  const nodes: { ad: string; durum: 'done' | 'active' | 'wait' }[] = [
    { ad: 'Hoş geldin', durum: adim === 'ton' ? 'active' : 'done' },
    { ad: 'Seviye tespiti', durum: adim === 'calib' ? 'active' : adim === 'hazir' ? 'done' : 'wait' },
    { ad: 'Planın hazır', durum: adim === 'hazir' ? 'active' : 'wait' },
  ];
  return (
    <div aria-hidden style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 20 }}>
      {nodes.map((n, i) => (
        <React.Fragment key={n.ad}>
          {i > 0 && <div style={{ width: 28, height: 2, background: nodes[i - 1].durum === 'done' ? '#1FB683' : '#E2E5EB' }} />}
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{ width: 22, height: 22, borderRadius: 999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: n.durum === 'done' ? '#1FB683' : n.durum === 'active' ? '#FFF3EE' : '#fff', border: n.durum === 'active' ? '2px solid #FF6F5C' : n.durum === 'wait' ? '1px solid #ECE6DD' : 'none' }}>
              {n.durum === 'done' ? <Tik /> : <span style={{ ...numText, fontSize: 11, fontWeight: 800, color: n.durum === 'active' ? color.dawn.coralTextOnLight : '#9A93A5' }}>{i + 1}</span>}
            </div>
            <span style={{ fontSize: 12, fontWeight: 700, color: n.durum === 'wait' ? '#9A93A5' : color.ink.secondary }}>{n.ad}</span>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
}

export function OnboardingPage(): React.ReactElement {
  const [adim, setAdim] = React.useState<Adim>('ton');
  const [ton, setTon] = React.useState<Ton | null>(null);
  const [qi, setQi] = React.useState(0);
  const [dogru, setDogru] = React.useState(0);

  const oran = qi === 0 ? 0 : dogru / qi; // yanıtlanan üzerinden
  const tahmin = qi === 0 ? 'ölçülüyor' : oran < 0.4 ? 'temel' : oran < 0.7 ? 'orta' : 'orta-üst';
  const pinLeft = 12 + oran * 76;

  const cevapla = (secim: number) => {
    const soru = SORULAR[qi];
    if (soru && secim === soru.dogru) setDogru((d) => d + 1); // MOCK: dogru yerel (live'da sunucu)
    if (qi + 1 >= SORULAR.length) setAdim('hazir');
    else setQi((n) => n + 1);
  };
  const yenidenCoz = () => { setQi(0); setDogru(0); setAdim('calib'); };

  const r = sonuc(dogru);

  const kartStil: React.CSSProperties = {
    width: '100%', maxWidth: 560, margin: '0 auto', boxSizing: 'border-box',
    background: color.paper.card, borderRadius: radius.cardLg, border: `1px solid ${color.paper.border}`,
    boxShadow: '0 20px 50px -24px rgba(42,36,51,0.3)', padding: '26px 28px 30px',
  };
  const linkBtn: React.CSSProperties = { minHeight: 44, display: 'inline-flex', alignItems: 'center', fontSize: 13, fontWeight: 700, color: color.dawn.coralTextOnLight, background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: font.sans };

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: PAGE_BG, fontFamily: font.sans, color: color.ink.primary, position: 'relative' }}>
        {adim === 'hazir' && <ConfettiDawn count={26} />}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', maxWidth: 1100, margin: '0 auto', flexWrap: 'wrap', gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#9A93A5' }} aria-live="polite">
            Adım {adim === 'ton' ? 1 : adim === 'calib' ? 2 : 3} / 3
          </span>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <a href="/giris" style={{ ...linkBtn, textDecoration: 'none' }}>Hesabın var mı? Giriş yap</a>
            <a href="/panel" style={{ ...linkBtn, textDecoration: 'none' }}>Atla</a>
          </div>
        </div>

        <div style={{ padding: '8px 24px 56px' }}>
          <Stepper adim={adim} />
          <div style={kartStil}>

            {adim === 'ton' && (
              <div role="radiogroup" aria-labelledby="ob-ton-baslik">
                <h1 id="ob-ton-baslik" style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 28, fontWeight: 400, margin: 0 }}>Hoş geldin. Önce sen, sonra sorular.</h1>
                <p style={{ marginTop: 8, fontSize: 14, lineHeight: 1.55, color: color.ink.secondary }}>Tek soru — cevabın planının tonunu belirler.</p>
                <div style={{ marginTop: space[4], display: 'grid', gap: 10 }}>
                  {TON_SIRA.map((t) => {
                    const secili = ton === t;
                    return (
                      <button key={t} type="button" role="radio" aria-checked={secili} onClick={() => setTon(t)}
                        style={{ display: 'flex', alignItems: 'center', gap: 10, minHeight: 52, padding: '0 16px', textAlign: 'left', cursor: 'pointer', borderRadius: 13, background: secili ? '#FFF8F2' : '#fff', border: `1.5px solid ${secili ? '#FF6F5C' : '#ECE6DD'}`, fontFamily: font.sans, fontSize: 14.5, fontWeight: 600, color: color.ink.primary }}>
                        <span aria-hidden style={{ width: 18, height: 18, borderRadius: 999, flexShrink: 0, border: `2px solid ${secili ? '#FF6F5C' : '#D9D2C7'}`, background: secili ? '#FF6F5C' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{secili ? <Tik size={10} /> : null}</span>
                        {TON[t].label}
                      </button>
                    );
                  })}
                </div>
                {ton && (
                  <div role="status" aria-live="polite" style={{ marginTop: space[4], padding: '12px 14px', borderRadius: radius.chip, background: color.paper.subtle, border: `1px solid ${color.paper.border}`, fontSize: 13.5, lineHeight: 1.55, color: color.ink.secondary }}>
                    {TON[ton].yanit}
                  </div>
                )}
                <div style={{ marginTop: space[5], display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                  <Button variant="primary" size="lg" disabled={!ton} onClick={() => setAdim('calib')}>Devam et</Button>
                  <button type="button" onClick={() => { setTon(null); setAdim('calib'); }} style={linkBtn}>Bu soruyu geç</button>
                </div>
              </div>
            )}

            {adim === 'calib' && SORULAR[qi] && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 700, color: '#3B82F6', background: 'rgba(59,130,246,0.10)', padding: '4px 10px', borderRadius: 999 }}>TYT Matematik</span>
                  <span style={{ ...numText, fontSize: 12.5, fontWeight: 700, color: color.ink.muted }}>Soru {qi + 1} / 6</span>
                </div>
                <h2 style={{ marginTop: 14, fontSize: 22, fontWeight: 800, lineHeight: 1.25 }}>Seviyeni öğreniyoruz</h2>
                <p style={{ marginTop: 6, fontSize: 13.5, color: color.ink.secondary }}>Sadece <strong>6 soru · ~2 dakika</strong>. Her cevap sonrakini seçer — tahmin değil, ölçüm.</p>

                <div style={{ marginTop: space[4], padding: '18px 18px 16px', borderRadius: radius.card, background: color.paper.subtle, border: `1px solid ${color.paper.border}` }}>
                  <div style={{ fontSize: 15.5, fontWeight: 700, lineHeight: 1.4 }}>{SORULAR[qi].soru}</div>
                  <div style={{ marginTop: 14, display: 'grid', gap: 8 }}>
                    {SORULAR[qi].secenekler.map((sec, i) => (
                      <button key={i} type="button" onClick={() => cevapla(i)}
                        style={{ display: 'flex', alignItems: 'center', gap: 10, minHeight: 46, padding: '0 14px', textAlign: 'left', cursor: 'pointer', borderRadius: 11, background: '#fff', border: `1px solid ${color.paper.border}`, fontFamily: font.sans, fontSize: 14, color: color.ink.primary }}>
                        <span aria-hidden style={{ width: 24, height: 24, borderRadius: 8, flexShrink: 0, background: color.paper.subtle, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 12.5, color: color.ink.secondary }}>{String.fromCharCode(65 + i)}</span>
                        {sec}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ marginTop: space[4] }}>
                  <div style={{ fontSize: 12.5, color: color.ink.muted }}>
                    Seviye tahmini netleşiyor · <strong style={{ color: color.ink.secondary }}>{tahmin}</strong>
                    <span style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>Seviye tahmini: {tahmin}</span>
                  </div>
                  <div aria-hidden style={{ marginTop: 8, position: 'relative', height: 8, borderRadius: 999, background: 'linear-gradient(90deg,#FCA5A5,#FCD34D,#86EFAC)' }}>
                    <div style={{ position: 'absolute', top: -3, left: `${pinLeft}%`, width: 14, height: 14, borderRadius: 999, background: '#fff', border: '2px solid #FF6F5C' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 11, color: color.ink.muted }}><span>Temel</span><span>Orta</span><span>İleri</span></div>
                </div>
                <p style={{ marginTop: space[4], fontSize: 12.5, color: color.ink.muted }}>Hesap oluşturmaya gerek yok — önce değerini gör, sonra kaydet.</p>
              </div>
            )}

            {adim === 'hazir' && (
              <div style={{ textAlign: 'center' }}>
                <h1 style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 30, fontWeight: 400, margin: 0 }}>Planın hazır!</h1>
                <p style={{ marginTop: 10, fontSize: 14.5, lineHeight: 1.6, color: color.ink.secondary }}>
                  6 soruda seviyeni ölçtük — <strong style={{ color: color.ink.primary }}><span style={numText}>{dogru}</span>/6 doğru</strong>. Sana özel 30 günlük yol haritasını kurduk; zayıf konuların öncelikli.
                </p>
                <div style={{ marginTop: space[5], display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                  {[{ e: 'Tahmini seviye', d: r.seviye }, { e: 'Net potansiyeli', d: `~${r.net}` }, { e: 'Odak konu', d: r.odak }].map((s) => (
                    <div key={s.e} style={{ background: color.paper.subtle, border: `1px solid ${color.paper.border}`, borderRadius: radius.card, padding: '14px 10px' }}>
                      <div style={{ ...numText, fontSize: 16, fontWeight: 800 }}>{s.d}</div>
                      <div style={{ marginTop: 3, fontSize: 11.5, color: color.ink.muted }}>{s.e}</div>
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: space[5], padding: '14px 16px', borderRadius: radius.card, background: '#FFF8F2', border: '1px solid #F6D9CB', textAlign: 'left' }}>
                  <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', color: color.dawn.coralTextOnLight }}>İlk haftan</div>
                  <div style={{ marginTop: 6, fontSize: 13, color: color.ink.secondary, lineHeight: 1.6 }}>Gün 1 · {r.odak} temel · Gün 2 · Paragraf · Gün 3 · Deneme</div>
                </div>
                <div style={{ marginTop: space[5], display: 'grid', gap: 10 }}>
                  <Button variant="primary" size="lg" onClick={() => undefined}>Çalışmaya başla</Button>
                  <button type="button" onClick={() => undefined} style={{ ...linkBtn, fontSize: 13.5 }}>Hesabını oluştur ve ilerlemeni kaydet</button>
                  <button type="button" onClick={yenidenCoz} style={{ ...linkBtn, color: color.ink.muted, fontSize: 13 }}>Testi yeniden çöz</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default OnboardingPage;
