// ============================================================================
// KIRO2 — Harmanlanmış Deneme (SPRINT4 · KIRO2 Harmanlanmis Deneme.dc.html)
// Tema = PAPER. SideNav(active=deneme) + içerik (lobi ön-sayfa: yöntemi anlatır, Soru Çözme'ye gönderir).
// Kopya PEDAGOJİK VARLIK — birebir. harman/bloklu toggle ÜRETİMDE KALIR (deneme her zaman harmanlı başlar).
// "Denemeyi başlat" → /cozum/harman-{id}. Bileşim: getReviewTopics().slice(0,4) + getTopics (durum join).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getReviewTopics, getTopics } from '../api/api-client';
import type { MockData } from '../api/api-client';
import type { ReviewItem, Topic } from '../types';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { SideNav } from '../ui/SideNav';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { Button } from '../ui/Button';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const DURUM: Record<string, string> = { zayif: 'zayıf', gelisiyor: 'gelişiyor', iyi: 'iyi', guclu: 'güçlü' };

function useDar(): boolean {
  const [dar, setDar] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 1023px)');
    const on = () => setDar(mq.matches);
    on(); mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return dar;
}
function useTek(): boolean {
  const [tek, setTek] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 720px)');
    const on = () => setTek(mq.matches);
    on(); mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return tek;
}

const kart: React.CSSProperties = { background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 22 };
const KIRPT = <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 6 9 17l-5-5" /></svg>;

interface Bilesen { name: string; color: string; count: number; tur: string; durum: string }

export function HarmanPage(): React.ReactElement {
  const dar = useDar();
  const tek = useTek();
  const [comp, setComp] = React.useState<Bilesen[] | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [mode, setMode] = React.useState<'harmanli' | 'bloklu'>('harmanli');

  React.useEffect(() => {
    let alive = true;
    setComp(null); setHata(false);
    Promise.all([getReviewTopics(), getTopics()])
      .then(([queue, topics]: [ReviewItem[], Topic[]]) => {
        if (!alive) return;
        const durumMap = new Map(topics.map((t) => [t.ders + '|' + t.ad, t.durum]));
        const c: Bilesen[] = queue.slice(0, 4).map((q) => ({
          name: q.konu,
          color: color.subject.light[q.ders] ?? color.dawn.coral,
          count: q.kart,
          tur: q.ders === 'tur' ? 'TYT' : 'AYT',
          durum: DURUM[durumMap.get(q.ders + '|' + q.konu) ?? 'gelisiyor'] ?? 'gelişiyor',
        }));
        setComp(c);
      })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  const totalQ = (comp ?? []).reduce((s, c) => s + c.count, 0);
  const estMin = Math.round(totalQ * 1.5);
  const N = Math.min(3, comp?.length ?? 0);
  const chips: number[] = [];
  if (mode === 'harmanli') { for (let r = 0; r < 3; r++) for (let t = 0; t < N; t++) chips.push(t); }
  else { for (let t = 0; t < N; t++) for (let r = 0; r < 3; r++) chips.push(t); }
  const modeLabel = mode === 'harmanli' ? 'Harmanlanmış' : 'Bloklu (karşılaştırma)';

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="deneme" collapsed={dar} userName="Öğrenci" userSub="" onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0, height: '100vh', overflowY: 'auto' }}>
          <header style={{ position: 'sticky', top: 0, zIndex: 5, minHeight: 64, display: 'flex', alignItems: 'center', padding: '10px 24px', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}` }}>
            <div style={{ minWidth: 0 }}>
              <h1 style={{ margin: 0, fontSize: 16, fontWeight: 800 }}>Harmanlanmış Deneme</h1>
              <div style={{ fontSize: 12, color: color.ink.muted }}>Karışık konu pratiği · interleaving</div>
            </div>
          </header>

          <div style={{ maxWidth: 980, margin: '0 auto', padding: '26px 24px 50px' }}>
            {hata ? (
              <ErrorState onRetry={() => setYeniden((n) => n + 1)} />
            ) : comp === null ? (
              <div aria-busy="true" aria-label="Deneme hazırlanıyor" style={{ display: 'grid', gap: 18 }}>
                <div style={{ ...kart, borderRadius: 18 }}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
              </div>
            ) : comp.length === 0 ? (
              <EmptyState serifTitle="Bugün harmanlanacak konu yok — eğrin sağlıklı." body="Tekrar kuyruğun şu an boş; öğrenme yolundan yeni konulara geçebilirsin." action={<Button variant="primary" onClick={() => undefined}>Öğrenme yoluna git</Button>} />
            ) : (
              <div style={{ display: 'grid', gap: 18 }}>
                {/* Hero */}
                <div className="k-hero" style={{ display: 'grid', gridTemplateColumns: tek ? '1fr' : '1.3fr 1fr', gap: 18 }}>
                  <div style={{ ...kart }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 800, color: '#9A5D0D', background: '#FBF0DE', padding: '5px 11px', borderRadius: 8 }}>{KIRPT}KANITLI YÖNTEM · d≈0,35</span>
                    <h2 style={{ margin: '14px 0 0', fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em', lineHeight: 1.15 }}>Konuları karıştır, daha iyi öğren</h2>
                    <p style={{ margin: '10px 0 0', fontSize: 14.5, color: color.ink.muted, lineHeight: 1.6 }}>Tek konu üst üste çalışmak (bloklu) kolay <em>hisseder</em> ama zayıf kalır. Konuları <strong>harmanlamak</strong> beyni her soruda "hangi yöntem?" diye seçim yapmaya zorlar — ayırt etme ve gerçek sınav transferi güçlenir.</p>
                  </div>
                  <div style={{ borderRadius: 18, padding: 24, background: 'linear-gradient(140deg,#C2452B,#E0593F)', color: '#fff', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700 }}>Bu oturum</div>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 4 }}>
                      <span style={{ ...numText, fontSize: 46, fontWeight: 800, lineHeight: 1 }}>{totalQ}</span>
                      <span style={{ fontSize: 15, fontWeight: 700 }}>soru · <span style={numText}>{comp.length}</span> konu</span>
                    </div>
                    <div style={{ fontSize: 13, marginTop: 6 }}>~<span style={numText}>{estMin}</span> dk · karışık sıra</div>
                    <div style={{ flex: 1, minHeight: 12 }} />
                    <button type="button" onClick={() => undefined} style={{ minHeight: 46, borderRadius: 12, border: 'none', background: '#fff', color: color.dawn.coralCtaBg, cursor: 'pointer', fontFamily: font.sans, fontSize: 14, fontWeight: 800, textAlign: 'center' }}>Denemeyi başlat →</button>
                  </div>
                </div>

                {/* Interleaving görselleştirmesi */}
                <div style={kart}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
                    <span style={{ fontSize: 16, fontWeight: 800 }}>Soru sırası · {modeLabel}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                      <span aria-hidden style={{ display: 'inline-flex', gap: 12 }}>
                        {comp.slice(0, N).map((c) => (
                          <span key={c.name} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 700, color: '#4A4456' }}><span style={{ width: 11, height: 11, borderRadius: 3, background: c.color }} />{c.name}</span>
                        ))}
                      </span>
                      <button type="button" onClick={() => setMode((m) => (m === 'harmanli' ? 'bloklu' : 'harmanli'))} title="Modu değiştir" aria-pressed={mode === 'bloklu'} style={{ minHeight: 44, padding: '0 14px', borderRadius: 999, border: `1px solid ${color.paper.border}`, background: color.paper.subtle, color: color.ink.secondary, cursor: 'pointer', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700 }}>{mode === 'harmanli' ? 'Bloklu görünüm' : 'Harmanlı görünüm'}</button>
                    </div>
                  </div>
                  <p style={{ margin: '0 0 16px', fontSize: 12.5, color: color.ink.muted }}>{mode === 'harmanli' ? 'Konular bilinçli karıştırıldı — her soruda yöntem seçimi yeniden tetiklenir.' : 'Aynı konu üst üste gruplanmış — akıcı ama zayıf transfer. (Karşılaştırma için)'}</p>
                  <div aria-hidden style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {chips.map((t, i) => (
                      <span key={i} style={{ ...numText, width: 42, height: 42, borderRadius: 11, display: 'flex', alignItems: 'center', justifyContent: 'center', background: comp[t]!.color, color: '#fff', fontSize: 13, fontWeight: 800, boxShadow: `0 2px 5px -2px ${comp[t]!.color}` }}>{i + 1}</span>
                    ))}
                  </div>
                </div>

                {/* Karşılaştırma kartları */}
                <div className="k-karsi" style={{ display: 'grid', gridTemplateColumns: tek ? '1fr' : '1fr 1fr', gap: 14 }}>
                  <div style={{ ...kart, borderRadius: 16, padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                      <span style={{ fontSize: 11, fontWeight: 800, color: color.ink.muted, background: '#ECE6DD', borderRadius: 7, padding: '3px 8px' }}>BLOKLU</span>
                      <span style={{ ...numText, fontSize: 12, fontWeight: 600, color: color.ink.muted }}>aaa bbb ccc</span>
                    </div>
                    <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 7, listStyle: 'none', fontSize: 13, color: '#4A4456' }}>
                      <li><strong style={{ color: '#16A34A' }}>+</strong> Kolay hisseder, akıcı</li>
                      <li><strong style={{ color: '#E0593F' }}>−</strong> Zayıf uzun-vade transfer</li>
                      <li><strong style={{ color: '#E0593F' }}>−</strong> "Hangi yöntem?" seçimini öğretmez</li>
                    </ul>
                  </div>
                  <div style={{ background: '#FFF3EE', border: '1.5px solid #F2CFC2', borderRadius: 16, padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                      <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', background: color.dawn.coral, borderRadius: 7, padding: '3px 8px' }}>HARMANLANMIŞ</span>
                      <span style={{ ...numText, fontSize: 12, fontWeight: 600, color: color.dawn.coralTextOnLight }}>abc abc abc</span>
                    </div>
                    <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 7, listStyle: 'none', fontSize: 13, color: color.dawn.coralTextOnLight }}>
                      <li><strong style={{ color: '#16A34A' }}>+</strong> Güçlü transfer + ayırt etme</li>
                      <li><strong style={{ color: '#16A34A' }}>+</strong> Gerçek sınav koşuluna yakın</li>
                      <li><strong style={{ color: '#9A5D0D' }}>!</strong> Zor hisseder — bu "istenen zorluk"</li>
                    </ul>
                  </div>
                </div>

                {/* Oturum bileşimi */}
                <div style={kart}>
                  <div style={{ fontSize: 16, fontWeight: 800 }}>Oturum bileşimi</div>
                  <div style={{ fontSize: 13, color: color.ink.muted, margin: '2px 0 16px' }}>FSRS + zayıf konularına göre seçildi — en çok tekrar isteyenler ağırlıkta.</div>
                  <div style={{ display: 'grid', gridTemplateColumns: tek ? '1fr 1fr' : 'repeat(4, 1fr)', gap: 13 }}>
                    {comp.map((c) => (
                      <div key={c.name} style={{ border: `1px solid ${color.paper.border}`, borderRadius: 13, padding: 15 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span aria-hidden style={{ width: 10, height: 10, borderRadius: 3, background: c.color, flexShrink: 0 }} />
                          <span style={{ fontSize: 13, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.name}</span>
                        </div>
                        <div style={{ ...numText, fontSize: 22, fontWeight: 800, marginTop: 8 }}>{c.count}</div>
                        <div style={{ fontSize: 11.5, color: color.ink.muted }}>{c.tur} · {c.durum}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default HarmanPage;
