// ============================================================================
// KIRO2 — Neden Geri Bildirim (SPRINT3 · KIRO2 Neden Geri Bildirim.dc.html)
// Tema = PAPER. SideNav(active=practice) + orta (max 720) + sağ ray 312 (dar ekranda gizli).
// İçerik TÜMÜYLE postAnswer(AnswerResult) yanıtından (ekran salt-okur). Kaygı-tonu: yanlış =
// terracotta "birlikte bakalım", alarm-kırmızısı YOK. DC'deki tik/çarpı glyph'leri bespoke SVG (ikon kanonu).
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getQuestionSet, getMe, postAnswer } from '../api/api-client';
import type { MockData, SoruSetItem, AnswerResult } from '../api/api-client';
import type { Persona } from '../types';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { SideNav } from '../ui/SideNav';
import { MasteryBadge } from '../ui/MasteryBadge';
import { Button } from '../ui/Button';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const HARFLER = ['A', 'B', 'C', 'D', 'E', 'F'];

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

const S = { fill: 'none' as const, stroke: 'currentColor', strokeWidth: 2.2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
const Tik = ({ size = 16 }: { size?: number }) => <svg width={size} height={size} viewBox="0 0 24 24" {...S} aria-hidden><path d="M20 6 9 17l-5-5" /></svg>;
const Capraz = ({ size = 16 }: { size?: number }) => <svg width={size} height={size} viewBox="0 0 24 24" {...S} aria-hidden><path d="M18 6 6 18M6 6l12 12" /></svg>;
const Refresh = () => <svg width="16" height="16" viewBox="0 0 24 24" {...S} strokeWidth={1.9} aria-hidden><path d="M3 12a9 9 0 0 1 15-6.6L21 8M21 4v4h-4M21 12a9 9 0 0 1-15 6.6L3 16M3 20v-4h4" /></svg>;
const Takvim = () => <svg width="14" height="14" viewBox="0 0 24 24" {...S} strokeWidth={1.9} aria-hidden><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M3 9h18M8 2v4M16 2v4" /></svg>;
const Alev = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden><path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" /></svg>;
const Soru = () => <svg width="16" height="16" viewBox="0 0 24 24" {...S} aria-hidden><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.7-2.5 2-2.5 4M12 17h.01" /></svg>;

function Pil({ children, bg, fg }: { children: React.ReactNode; bg: string; fg: string }) {
  return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: bg, color: fg, borderRadius: 999, padding: '5px 10px', fontSize: 12, fontWeight: 700 }}>{children}</span>;
}

const kart: React.CSSProperties = { background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 16, padding: 20 };

export interface NedenPageProps {
  /** Demo senaryosu: 'yanlis' (varsayılan — zengin yol) veya 'dogru'. Üretimde cevap yanıtından. */
  senaryo?: 'dogru' | 'yanlis';
}

export function NedenPage({ senaryo = 'yanlis' }: NedenPageProps): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const rayGizli = useMedia('(max-width: 1100px)');
  const [q, setQ] = React.useState<SoruSetItem | null>(null);
  const [secilen, setSecilen] = React.useState(0);
  const [sonuc, setSonuc] = React.useState<AnswerResult | null>(null);
  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setSonuc(null);
    setHata(false);
    (async () => {
      try {
        const [set, p] = await Promise.all([getQuestionSet('mat', 'Türev'), getMe()]);
        const soru = set[1] ?? set[0];
        if (!soru || !alive) return;
        // İlk postAnswer doğru şıkkı verir; senaryoya göre seçimi belirleyip TEK otoriter yanıtı alırız.
        const ilk = await postAnswer(soru.id, 0);
        const sec = senaryo === 'dogru' ? ilk.dogru : (ilk.dogru + 1) % soru.secenekler.length;
        const r = sec === 0 ? ilk : await postAnswer(soru.id, sec);
        if (!alive) return;
        setQ(soru);
        setSecilen(sec);
        setSonuc(r);
        setPersona(p);
      } catch {
        if (alive) setHata(true);
      }
    })();
    return () => { alive = false; };
  }, [senaryo, yeniden]);

  const dogru = !!sonuc?.correct;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogrenci" activeId="practice" collapsed={dar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
          {/* Header */}
          <header style={{ flexShrink: 0, minHeight: 64, display: 'flex', alignItems: 'center', gap: 12, padding: '10px 24px', flexWrap: 'wrap', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}` }}>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Çözüm &amp; Açıklama</div>
              <div style={{ fontSize: 12, color: color.ink.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>AYT Matematik · {q?.konu ?? 'Türev'} · Soru <span style={numText}>7/20</span></div>
            </div>
            <Pil bg={color.semantic.riskBgSoft} fg={color.semantic.riskTextOnLight}><Alev /><span style={numText}>{persona?.seri ?? 0}</span></Pil>
            <Pil bg="#FFF3EE" fg={color.dawn.coralTextOnLight}>XP <span style={numText}>{new Intl.NumberFormat('tr-TR').format(persona?.xp ?? 0)}</span></Pil>
          </header>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', gap: 0 }}>
            {hata ? (
              <div style={{ flex: 1, padding: 26 }}>
                <ErrorState serifTitle="Çözüm şu an gelmedi — senlik bir şey değil." body="Bağlantı bir soluklandı, çalışman güvende. Hazır olduğunda tekrar dene." onRetry={() => setYeniden((n) => n + 1)} retryLabel="Yeniden dene" />
              </div>
            ) : sonuc === null || q === null ? (
              <div aria-busy="true" aria-label="Çözüm hazırlanıyor" style={{ flex: 1, maxWidth: 720, margin: '0 auto', padding: '26px 32px', display: 'grid', gap: 16 }}>
                <div style={kart}><Skeleton shape="row" delayMs={0} slowAfterMs={null} /></div>
                <div style={kart}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
              </div>
            ) : (
              <>
                {/* Orta sütun */}
                <div style={{ flex: 1, minWidth: 0, maxWidth: 720, margin: '0 auto', padding: '26px 32px', display: 'grid', gap: 16 }}>
                  {/* Sonuç bandı */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '16px 18px', borderRadius: 16, background: dogru ? '#F0FDF4' : '#FCEDE8', border: `1px solid ${dogru ? '#BBF7D0' : '#F0A593'}` }}>
                    <span aria-hidden style={{ flexShrink: 0, width: 42, height: 42, borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', background: dogru ? '#1FB683' : color.dawn.coralCtaBg, color: '#fff' }}>{dogru ? <Tik size={22} /> : <Capraz size={22} />}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: dogru ? '#166534' : '#9A3520' }}>{dogru ? 'Doğru!' : 'Yanlış — hadi nedenini görelim'}</div>
                      <div style={{ fontSize: 13, color: dogru ? '#15803D' : color.dawn.coralTextOnLight }}>{dogru ? 'Güzel iş. Yine de mantığı pekiştirelim.' : 'Hata, öğrenmenin en değerli anı. Aşağıda tam olarak neden.'}</div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontSize: 10.5, fontWeight: 700, color: color.ink.muted, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Süre</div>
                      <div style={{ ...numText, fontSize: 15, fontWeight: 800 }}>1:12</div>
                    </div>
                  </div>

                  {/* Soru özeti */}
                  <div style={kart}>
                    <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', color: color.ink.muted, marginBottom: 8 }}>SORU</div>
                    <p style={{ margin: '0 0 14px', fontSize: 16, fontWeight: 600, lineHeight: 1.6 }}>{q.soru}</p>
                    <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 8, listStyle: 'none' }}>
                      {q.secenekler.map((sec, i) => {
                        const isDogru = i === sonuc.dogru;
                        const isSecilen = i === secilen;
                        const g = isDogru
                          ? { bg: '#F0FDF4', bd: '#86EFAC', rz: '#15803D', et: isSecilen ? 'Senin cevabın' : 'Doğru cevap', etFg: '#15803D', ikon: <Tik size={13} /> }
                          : isSecilen
                            ? { bg: '#FCEDE8', bd: '#F0A593', rz: color.dawn.coralCtaBg, et: 'Senin cevabın', etFg: color.dawn.coralTextOnLight, ikon: <Capraz size={13} /> }
                            : { bg: color.paper.card, bd: color.paper.border, rz: '#8C8598', et: undefined as string | undefined, etFg: '', ikon: null };
                        return (
                          <li key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '11px 13px', borderRadius: 11, background: g.bg, border: `1.5px solid ${g.bd}` }}>
                            <span aria-hidden style={{ flexShrink: 0, width: 26, height: 26, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', background: g.rz, color: '#fff', fontSize: 12.5, fontWeight: 800 }}>{HARFLER[i]}</span>
                            <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: '#3A3446' }}>{sec}</span>
                            {g.et && <span style={{ flexShrink: 0, display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, fontWeight: 800, color: g.etFg }}>{g.ikon}{g.et}</span>}
                          </li>
                        );
                      })}
                    </ul>
                  </div>

                  {/* Neden? bloğu */}
                  <div style={kart}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <span aria-hidden style={{ width: 30, height: 30, borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#FFF3EE', color: color.dawn.coral }}><Soru /></span>
                      <h3 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>Neden?</h3>
                    </div>
                    <div style={{ display: 'grid', gap: 12 }}>
                      <div style={{ padding: '13px 15px', borderRadius: 12, background: '#F0FDF4', border: '1px solid #BBF7D0' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 800, color: '#16A34A', marginBottom: 5 }}><Tik size={13} />NEDEN {HARFLER[sonuc.dogru]} DOĞRU</div>
                        <div style={{ fontSize: 13.5, lineHeight: 1.6, color: '#166534' }}>{sonuc.neden}</div>
                      </div>
                      {!dogru && sonuc.nedenYanlis && (
                        <div style={{ padding: '13px 15px', borderRadius: 12, background: '#FCEDE8', border: '1px solid #F0A593' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 800, color: color.dawn.coralTextOnLight, marginBottom: 5 }}><Capraz size={13} />NEDEN {HARFLER[secilen]} YANLIŞ</div>
                          <div style={{ fontSize: 13.5, lineHeight: 1.6, color: '#9A3520' }}>{sonuc.nedenYanlis}</div>
                        </div>
                      )}
                      <div style={{ padding: '14px 16px', borderRadius: 12, background: '#FBF7F1', border: `1px solid ${color.paper.border}` }}>
                        <div style={{ fontSize: 12, fontWeight: 800, letterSpacing: '0.03em', color: color.ink.secondary, marginBottom: 10 }}>ÇÖZÜM · adım adım</div>
                        <ol style={{ margin: 0, padding: 0, display: 'grid', gap: 10, listStyle: 'none' }}>
                          {sonuc.cozum.map((adim, i) => (
                            <li key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                              <span aria-hidden style={{ ...numText, flexShrink: 0, width: 22, height: 22, borderRadius: 999, background: color.ink.primary, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800 }}>{i + 1}</span>
                              <span style={{ fontSize: 14, lineHeight: 1.6, color: color.ink.secondary }}>{adim}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>
                  </div>

                  {/* Aksiyonlar */}
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <Button variant="primary" onClick={() => undefined}>Benzer soru çöz →</Button>
                    <Button variant="ghost" onClick={() => undefined}>Kavramı tekrar et</Button>
                  </div>
                </div>

                {/* Sağ ray */}
                {!rayGizli && (
                  <aside aria-label="Etki özeti" style={{ flexShrink: 0, width: 312, borderLeft: `1px solid ${color.paper.border}`, background: color.paper.card, padding: 20, display: 'grid', gap: 16, alignContent: 'start' }}>
                    {/* Hafıza motoru (coral gradyan) */}
                    <div style={{ borderRadius: 16, padding: 18, background: `linear-gradient(135deg, ${color.dawn.coralCtaBg}, ${color.dawn.coral})`, color: '#fff' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5, fontWeight: 800 }}><Refresh />Hafıza motoru (FSRS)</div>
                      <p style={{ margin: '10px 0 12px', fontSize: 13, lineHeight: 1.55 }}>Yanlış yaptığın için bu kavram <strong>tekrar kuyruğuna</strong> eklendi.</p>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 700, background: 'rgba(255,255,255,0.16)', borderRadius: 9, padding: '7px 11px' }}><Takvim /><span style={numText}>{sonuc.fsrsNextDays ?? 2}</span> gün sonra tekrar göreceksin</div>
                    </div>
                    {/* Kavram hâkimiyeti */}
                    {sonuc.mastery && (
                      <div style={kart}>
                        <div style={{ fontSize: 13.5, fontWeight: 800, marginBottom: 10 }}>Kavram hâkimiyeti etkisi</div>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 10 }}>
                          <span style={{ fontSize: 12.5, fontWeight: 700, color: color.ink.secondary }}>{sonuc.mastery.konu}</span>
                          <MasteryBadge pct={sonuc.mastery.pct} trend={sonuc.mastery.trend} />
                        </div>
                        <div aria-hidden style={{ height: 9, borderRadius: 999, background: '#F0EAE1', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${sonuc.mastery.pct}%`, background: 'linear-gradient(90deg,#F59E0B,#E0593F)' }} />
                        </div>
                        <p style={{ margin: '9px 0 0', fontSize: 12, color: color.ink.muted }}>Birkaç doğru çözümle geri yükselir.</p>
                      </div>
                    )}
                    {/* İlgili kavramlar */}
                    {sonuc.relatedConcepts && sonuc.relatedConcepts.length > 0 && (
                      <div style={kart}>
                        <div style={{ fontSize: 13.5, fontWeight: 800, marginBottom: 10 }}>İlgili kavramlar</div>
                        <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 9, listStyle: 'none' }}>
                          {sonuc.relatedConcepts.map((k) => (
                            <li key={k.ad} style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 13, color: color.ink.secondary }}>
                              <span aria-hidden style={{ width: 9, height: 9, borderRadius: 999, background: k.renk, flexShrink: 0 }} />{k.ad}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </aside>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default NedenPage;
