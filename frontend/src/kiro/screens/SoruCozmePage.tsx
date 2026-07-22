// ============================================================================
// KIRO2 — Soru Çözme (SPRINT3 · KIRO2 Soru Cozme.dc.html)
// Tema = PAPER (çalışma yüzeyi — koyu zemin YASAK). SideNav YOK, tam ekran odak.
// Header (sayaç PASİF amber, geri sayar ama kırmızıya dönmez/yanıp sönmez) +
// ilerleme şeridi (width transition YOK — kanon) + QuestionCard + footer + navigatör.
// Sunucu-otoriter: tap → postAnswer → AnswerResult (doğru/çözüm/neden yalnız yanıttan).
// Klavye: 1-5/A-E şık (QuestionCard) · ←/→ soru gezinme · M işaretle.
// ============================================================================
import * as React from 'react';

import { configureKiroApi, getQuestionSet, postAnswer } from '../api/api-client';
import type { MockData, SoruSetItem, AnswerResult } from '../api/api-client';
import kiroData from '../api/kiro-data.json';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { QuestionCard } from '../ui/QuestionCard';
import { Skeleton } from '../ui/Skeleton';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

configureKiroApi({ mode: 'mock', mockData: kiroData as unknown as MockData });

const SET_BOYU = 10;
const BASLANGIC_SURE = 20 * 60; // 20:00 — prototip sabiti (üretimde plan verisinden)

const srOnly: React.CSSProperties = { position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0 };

function mmss(s: number): string {
  return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0');
}

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

const Im = {
  kapat: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M18 6 6 18M6 6l12 12" /></svg>
  ),
  saat: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>
  ),
};

interface Kayit { secilen: number; sonuc: AnswerResult }

export function SoruCozmePage(): React.ReactElement {
  const darDikey = useMedia('(max-width: 820px)');
  const [set, setSet] = React.useState<SoruSetItem[] | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);
  const [idx, setIdx] = React.useState(0);
  const [secili, setSecili] = React.useState<number | null>(null);
  const [answers, setAnswers] = React.useState<Record<number, Kayit>>({});
  const [isaretli, setIsaretli] = React.useState<ReadonlySet<number>>(new Set());
  const [remain, setRemain] = React.useState(BASLANGIC_SURE);
  const [gonderiliyor, setGonderiliyor] = React.useState(false);

  // Set yükleme (sunucu-otoriter: dogru/cozum/neden STRIP)
  React.useEffect(() => {
    let alive = true;
    setSet(null);
    setHata(false);
    setIdx(0);
    setSecili(null);
    setAnswers({});
    getQuestionSet('mat', 'Türev')
      .then((s) => { if (alive) setSet(s.slice(0, SET_BOYU)); })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // Pasif geri sayım — amber kalır, alarm YOK (kanon §A.23)
  React.useEffect(() => {
    if (typeof window === 'undefined') return;
    const t = window.setInterval(() => setRemain((r) => Math.max(0, r - 1)), 1000);
    return () => window.clearInterval(t);
  }, []);

  const toplam = set?.length ?? 0;
  const q = set && set[idx];
  const kayit = answers[idx];
  const cevaplanan = Object.keys(answers).length;
  const ilerleme = toplam ? Math.round((cevaplanan / toplam) * 100) : 0;
  const sonSoru = idx + 1 >= toplam;

  const secOku = React.useCallback(async (i: number) => {
    if (!q || answers[idx] || gonderiliyor) return;
    setSecili(i);
    setGonderiliyor(true);
    try {
      const r = await postAnswer(q.id, i);
      setAnswers((a) => ({ ...a, [idx]: { secilen: i, sonuc: r } }));
    } catch {
      // Cevap POST'u düştü → seçimi geri al, tekrar dokunulabilir.
      // (Üretim: yerel kuyruk + /sync/events idempotent — ERTELENDİ.)
      setSecili(null);
    } finally {
      setGonderiliyor(false);
    }
  }, [q, idx, answers, gonderiliyor]);

  const onceki = React.useCallback(() => { setIdx((n) => Math.max(0, n - 1)); setSecili(null); }, []);
  const ileri = React.useCallback(() => {
    setIdx((n) => (n + 1 >= toplam ? n : n + 1));
    setSecili(null);
  }, [toplam]);
  const isaretToggle = React.useCallback(() => {
    setIsaretli((s) => {
      const n = new Set(s);
      if (n.has(idx)) n.delete(idx); else n.add(idx);
      return n;
    });
  }, [idx]);

  // Klavye: ←/→ soru gezinme (radiogroup dışındayken), M işaretle
  React.useEffect(() => {
    const on = (e: KeyboardEvent) => {
      const inRadio = document.activeElement?.getAttribute('role') === 'radio';
      if ((e.key === 'ArrowLeft') && !inRadio) { e.preventDefault(); onceki(); }
      else if ((e.key === 'ArrowRight') && !inRadio) { e.preventDefault(); ileri(); }
      else if (e.key === 'm' || e.key === 'M') { isaretToggle(); }
    };
    window.addEventListener('keydown', on);
    return () => window.removeEventListener('keydown', on);
  }, [onceki, ileri, isaretToggle]);

  const setiBitir = () => undefined; // → Sınav Sonuç (Sprint 4)
  const kapat = () => undefined; // → Bugün hub'ı

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, display: 'flex', flexDirection: 'column', fontFamily: font.sans, color: color.ink.primary, position: 'relative' }}>
        {/* Gün ışığı yıkaması */}
        <div aria-hidden style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 200, background: 'radial-gradient(90% 100% at 50% -40%, rgba(255,158,125,0.07), transparent 70%)', pointerEvents: 'none', zIndex: 0 }} />

        {/* Header */}
        <header style={{ position: 'sticky', top: 0, zIndex: 6, minHeight: 62, display: 'flex', alignItems: 'center', gap: 14, padding: darDikey ? '9px 15px' : '0 22px', flexWrap: 'wrap', background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(10px)', borderBottom: `1px solid ${color.paper.border}` }}>
          <button type="button" onClick={kapat} aria-label="Kapat" style={{ flexShrink: 0, width: 44, height: 44, borderRadius: 12, border: `1px solid ${color.paper.border}`, background: color.paper.card, color: color.ink.secondary, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>{Im.kapat}</button>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 15.5, fontWeight: 800, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Matematik · Günlük Set</div>
            <div style={{ fontSize: 12, color: color.ink.muted, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>Türev odağı · <span style={numText}>{set === null ? '…' : toplam}</span> soru</div>
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 9, height: 40, padding: '0 16px', borderRadius: 11, background: '#FBF0DE', border: '1px solid #F2D9AC', color: '#9A5D0D', flexShrink: 0 }}>
            {Im.saat}
            <span style={{ ...numText, fontSize: 18, fontWeight: 800, letterSpacing: '0.01em' }}>{mmss(remain)}</span>
            <span style={srOnly}>kalan süre</span>
          </div>
          <Button variant="ghost" onClick={setiBitir}>Seti Bitir</Button>
        </header>

        {/* İlerleme şeridi (width transition YOK — kanon) */}
        <div aria-hidden style={{ height: 4, background: color.paper.border, flexShrink: 0 }}>
          <div style={{ height: '100%', width: `${ilerleme}%`, background: 'linear-gradient(90deg,#FF8A5B,#FF6F91)' }} />
        </div>

        {/* Gövde */}
        <main style={{ position: 'relative', zIndex: 1, flex: 1, width: '100%', maxWidth: 1200, margin: '0 auto', boxSizing: 'border-box', padding: darDikey ? '18px 16px 40px' : '26px', display: 'grid', gridTemplateColumns: darDikey ? '1fr' : '1fr 296px', gap: darDikey ? 16 : 22, alignItems: 'start' }}>
          {hata ? (
            <div style={{ gridColumn: '1 / -1' }}>
              <ErrorState serifTitle="Sorular şu an gelmedi." body="Sorun sende değil — bağlantı bir soluklandı, çalışman güvende. Birazdan yeniden dene." onRetry={() => setYeniden((n) => n + 1)} />
            </div>
          ) : set === null ? (
            <div aria-busy="true" aria-label="Sorular hazırlanıyor" style={{ gridColumn: '1 / -1' }}>
              <div style={{ background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, padding: 28 }}>
                <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
                <p style={{ marginTop: 12, fontSize: 12.5, color: color.ink.muted }}>Sorular hazırlanıyor…</p>
              </div>
            </div>
          ) : toplam === 0 || !q ? (
            <div style={{ gridColumn: '1 / -1' }}>
              <EmptyState serifTitle="Bu turu tamamladın." body="Şu an çözülecek soru kalmadı — planına dönüp bir sonraki adımı seçebilirsin." action={<Button variant="primary" onClick={kapat}>Planıma dön</Button>} />
            </div>
          ) : (
            <>
              {/* Soru sütunu */}
              <div style={{ display: 'grid', gap: 16, minWidth: 0 }}>
                <QuestionCard
                  soruNo={idx + 1}
                  toplam={toplam}
                  konu={q.konu}
                  zorlukB={q.b}
                  soru={q.soru}
                  secenekler={q.secenekler}
                  secilen={kayit ? kayit.secilen : secili}
                  onSelect={kayit ? undefined : secOku}
                  sonuc={kayit ? kayit.sonuc : null}
                  bekliyor={gonderiliyor}
                  isaretli={isaretli.has(idx)}
                  onToggleIsaret={isaretToggle}
                />

                {/* Footer gezinme */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <Button variant="ghost" disabled={idx === 0} onClick={onceki}>Önceki</Button>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    {!kayit && (
                      <button type="button" onClick={ileri} style={{ minHeight: 44, padding: '0 6px', background: 'none', border: 'none', cursor: 'pointer', fontFamily: font.sans, fontSize: 13.5, fontWeight: 700, color: color.ink.muted }}>Bu soruyu atla</button>
                    )}
                    <Button variant="primary" onClick={sonSoru ? setiBitir : ileri}>{sonSoru ? 'Seti bitir' : 'Sonraki soru'}</Button>
                  </div>
                </div>
              </div>

              {/* Soru Navigatörü */}
              <nav aria-label="Sorular" style={{ position: darDikey ? 'static' : 'sticky', top: 88, background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 18, order: darDikey ? -1 : 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 15.5, fontWeight: 800 }}>Soru Navigatörü</span>
                  <span style={{ ...numText, fontSize: 12.5, fontWeight: 800, color: color.dawn.coralTextOnLight }}>{cevaplanan}/{toplam}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(44px, 1fr))', gap: 8 }}>
                  {set.map((_, i) => {
                    const cevap = !!answers[i];
                    const isaret = isaretli.has(i);
                    const suanki = i === idx;
                    const durum = suanki ? 'şu anki soru' : cevap ? 'cevaplandı' : isaret ? 'işaretli' : 'boş';
                    const bg = cevap ? color.dawn.coralCtaBg : isaret ? '#FBF0DE' : suanki ? '#FFF3EE' : '#F4F0EA';
                    const fg = cevap ? '#fff' : isaret ? '#9A5D0D' : color.ink.secondary;
                    const bd = suanki ? color.dawn.coral : isaret ? '#F0D9AC' : color.paper.border;
                    return (
                      <button
                        key={i} type="button" onClick={() => { setIdx(i); setSecili(null); }}
                        aria-current={suanki ? 'true' : undefined}
                        style={{ minHeight: 44, borderRadius: 10, border: `1.5px solid ${bd}`, background: bg, color: fg, cursor: 'pointer', fontFamily: font.sans, ...numText, fontSize: 13, fontWeight: 800 }}
                      >
                        <span aria-hidden>{i + 1}</span>
                        <span style={srOnly}>{i + 1}. soru, {durum}</span>
                      </button>
                    );
                  })}
                </div>
                {/* Lejant (DC birebir · Cevaplanan / Şu anki soru / İşaretli / Boş) */}
                <div style={{ marginTop: 14, paddingTop: 12, borderTop: `1px solid ${color.paper.border}`, display: 'grid', gap: 8 }}>
                  {[
                    { et: `Cevaplanan (${cevaplanan})`, sw: color.dawn.coralCtaBg, bd: color.dawn.coralCtaBg },
                    { et: 'Şu anki soru', sw: '#FFF3EE', bd: color.dawn.coral },
                    { et: `İşaretli (${isaretli.size})`, sw: '#FBF0DE', bd: '#F0D9AC' },
                    { et: `Boş (${Math.max(0, toplam - cevaplanan)})`, sw: '#F4F0EA', bd: color.paper.border },
                  ].map((l) => (
                    <div key={l.et} style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 12.5, color: color.ink.secondary }}>
                      <span aria-hidden style={{ flexShrink: 0, width: 14, height: 14, borderRadius: 5, background: l.sw, border: `1.5px solid ${l.bd}` }} />
                      <span>{l.et}</span>
                    </div>
                  ))}
                </div>
              </nav>
            </>
          )}
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default SoruCozmePage;
