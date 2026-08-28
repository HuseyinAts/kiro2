// ============================================================================
// KIRO2 — Sınav Sonuç (SPRINT4 · KIRO2 Sinav Sonuc.dc.html)
// Tema = PAPER. SideNav YOK — header (geri→Panel) + içerik (net-birincil hiyerarşi).
// Kanon: büyük sayı=net, sıralama küçük+çerçeveli; "Tahmini sıralama · yalnız yön göstergesi"
// BİREBİR (asla kaldırma). ConfettiDawn YOK (sonuç ≠ kutlama). Yanlış stat zemini #FBE8E2 (#FEF2F2 DEĞİL).
// İçerik salt-okur (getExamResult/getTopics/getSubjects/getMe); AI metni SUNUCUDAN (istemci şablon doldurmaz).
// ============================================================================
import * as React from 'react';

import { getExamResult, getTopics, getMe } from '../api/api-client';
import type { LastExam, Topic, SubjectKey, Persona } from '../types';
import { color, font } from '../tokens';
import { KiroThemeProvider, numText } from '../ui/theme';
import { ProgressRing } from '../ui/ProgressRing';
import { ProgressBar } from '../ui/ProgressBar';
import { Skeleton } from '../ui/Skeleton';
import { ErrorState } from '../ui/ErrorState';
import '../tokens/tokens.css';

const trNet = (n: number) => new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 }).format(n);

function useMedia(query: string): boolean {
  const [m, setM] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia(query);
    const on = () => setM(mq.matches);
    on(); mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, [query]);
  return m;
}

const S = { fill: 'none' as const, stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
const Geri = () => <svg width="18" height="18" viewBox="0 0 24 24" {...S} aria-hidden><path d="M19 12H5M12 19l-7-7 7-7" /></svg>;
const Onay = () => <svg width="18" height="18" viewBox="0 0 24 24" {...S} strokeWidth={2.2} aria-hidden><path d="M20 6 9 17l-5-5" /></svg>;
const Capraz = () => <svg width="18" height="18" viewBox="0 0 24 24" {...S} strokeWidth={2.2} aria-hidden><path d="M18 6 6 18M6 6l12 12" /></svg>;
const Daire = () => <svg width="18" height="18" viewBox="0 0 24 24" {...S} aria-hidden><circle cx="12" cy="12" r="8" /></svg>;
const Grafik = () => <svg width="18" height="18" viewBox="0 0 24 24" {...S} aria-hidden><path d="M3 3v18h18M8 17v-5M13 17V7M18 17v-9" /></svg>;
const Katman = () => <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 2 2 7l10 5 10-5-10-5ZM2 12l10 5 10-5M2 17l10 5 10-5" /></svg>;
const Dongu = () => <svg width="16" height="16" viewBox="0 0 24 24" {...S} strokeWidth={2.1} aria-hidden><path d="M3 12a9 9 0 0 1 15-6.6L21 8M21 4v4h-4M21 12a9 9 0 0 1-15 6.6L3 16M3 20v-4h4" /></svg>;
const Yukari = () => <svg width="13" height="13" viewBox="0 0 24 24" {...S} strokeWidth={2.3} aria-hidden><path d="M6 15l6-6 6 6" /></svg>;
const Asagi = () => <svg width="13" height="13" viewBox="0 0 24 24" {...S} strokeWidth={2.3} aria-hidden><path d="M6 9l6 6 6-6" /></svg>;

const kart: React.CSSProperties = { background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 18, padding: 22 };

interface Satir { tur: 'TYT' | 'AYT'; ad: string; dogru: number; yanlis: number; bos: number; net: number; soru: number; renk: string }

function StatIkon({ icon, bg, fg }: { icon: React.ReactNode; bg: string; fg: string }) {
  return <span aria-hidden style={{ width: 40, height: 40, flexShrink: 0, borderRadius: 11, background: bg, color: fg, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>{icon}</span>;
}

export function SonucPage(): React.ReactElement {
  const tek = useMedia('(max-width: 720px)');
  const ikiTek = useMedia('(max-width: 900px)');
  const [exam, setExam] = React.useState<LastExam | null>(null);
  const [ad, setAd] = React.useState('');
  const [zayif, setZayif] = React.useState<{ ad: string; ders: string; hakimiyet: number }[]>([]);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  React.useEffect(() => {
    let alive = true;
    setExam(null); setHata(false);
    Promise.all([getExamResult(), getTopics(), getMe()])
      .then(([e, topics, me]: [LastExam, Topic[], Persona]) => {
        if (!alive) return;
        setExam(e);
        setAd(me.adKisa || me.ad);
        setZayif(topics.filter((t) => t.durum === 'zayif').sort((a, b) => a.hakimiyet - b.hakimiyet).slice(0, 4).map((t) => ({ ad: t.ad, ders: t.ders, hakimiyet: t.hakimiyet })));
      })
      .catch(() => { if (alive) setHata(true); });
    return () => { alive = false; };
  }, [yeniden]);

  // Ders adı → renk (light paleti; eşleşmezse nötr)
  const renkAdi: Record<string, SubjectKey> = { 'Türkçe': 'tur', 'Matematik': 'mat', 'Fizik': 'fiz', 'Kimya': 'kim', 'Biyoloji': 'biy' };
  const dersAd: Record<string, string> = { mat: 'Matematik', fiz: 'Fizik', kim: 'Kimya', biy: 'Biyoloji', tur: 'Türkçe', edb: 'Edebiyat', tar: 'Tarih', cog: 'Coğrafya', fel: 'Felsefe', din: 'Din' };
  const dersRenk = (adı: string) => color.subject.light[renkAdi[adı] as SubjectKey] ?? '#9A93A5';

  const satirlar: Satir[] = exam
    ? [...exam.tyt.map((s) => ({ ...s, tur: 'TYT' as const, renk: dersRenk(s.ad) })), ...exam.ayt.map((s) => ({ ...s, tur: 'AYT' as const, renk: dersRenk(s.ad) }))]
    : [];
  const d = satirlar.reduce((a, s) => a + s.dogru, 0);
  const y = satirlar.reduce((a, s) => a + s.yanlis, 0);
  const b = satirlar.reduce((a, s) => a + s.bos, 0);
  const totalQ = satirlar.reduce((a, s) => a + s.soru, 0);
  const toplamNet = exam ? exam.tytNet + exam.aytNet : 0;
  const dogruOrani = totalQ ? Math.round((d / totalQ) * 100) : 0;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary }}>
        <header style={{ position: 'sticky', top: 0, zIndex: 5, minHeight: 62, display: 'flex', alignItems: 'center', gap: 14, padding: '9px 24px', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}` }}>
          <button type="button" onClick={() => undefined} aria-label="Panele dön" style={{ flexShrink: 0, width: 44, height: 44, borderRadius: 12, border: `1px solid ${color.paper.border}`, background: color.paper.card, color: color.ink.muted, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}><Geri /></button>
          <div style={{ minWidth: 0 }}>
            <h1 style={{ margin: 0, fontSize: 15.5, fontWeight: 700, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{exam?.ad ?? 'Sınav Sonucu'}</h1>
            <div style={{ fontSize: 12, color: color.ink.muted }}>{exam ? 'Sonuç · ' + new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(exam.tarih)) : ''}</div>
          </div>
        </header>

        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '26px 24px 50px' }}>
          {hata ? (
            <ErrorState serifTitle="Sonucun şu an gelmedi." onRetry={() => setYeniden((n) => n + 1)} />
          ) : exam === null ? (
            <div aria-busy="true" aria-label="Sınav sonucu yükleniyor" style={{ display: 'grid', gap: 18 }}>
              <div style={{ ...kart, borderRadius: 20 }}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14 }}>{[0, 1, 2, 3].map((i) => <div key={i} style={kart}><Skeleton shape="row" delayMs={0} /></div>)}</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 18 }}>
              {/* Hero */}
              <div style={{ display: 'grid', gridTemplateColumns: tek ? '1fr' : '300px 1fr', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 20, overflow: 'hidden' }}>
                <div style={{ background: '#FBF8F3', borderRight: tek ? 'none' : `1px solid ${color.paper.border}`, borderBottom: tek ? `1px solid ${color.paper.border}` : 'none', padding: '28px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                  <ProgressRing pct={dogruOrani} size={148} strokeWidth={13} ringColor={color.dawn.coral} label={`%${dogruOrani}`} sublabel="doğru oranı" ariaLabel={`Doğru oranı yüzde ${dogruOrani}`} />
                  {exam.trendNet != null && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, borderRadius: 999, padding: '4px 11px', fontSize: 12.5, fontWeight: 700, ...(exam.trendNet >= 0 ? { background: '#ECFDF5', color: '#047857' } : { background: '#FBF0DE', color: '#9A5D0D' }) }}>
                      {exam.trendNet >= 0 ? <Yukari /> : <Asagi />}{exam.trendNet >= 0 ? '+' : '−'}{trNet(Math.abs(exam.trendNet))} net · son denemeye göre
                    </span>
                  )}
                </div>
                <div style={{ padding: '26px 30px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                  <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em' }}>Güzel iş, {ad}!</h2>
                  <p style={{ margin: '6px 0 18px', fontSize: 14, color: color.ink.muted }}><strong style={{ color: color.ink.primary }}>{exam.tip}</strong> · <span style={numText}>{totalQ}</span> soru tamamlandı</p>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
                    <div><div style={{ ...numText, fontSize: 27, fontWeight: 800, lineHeight: 1 }}>{trNet(exam.tytNet)}</div><div style={{ fontSize: 12.5, color: color.ink.muted, marginTop: 5 }}>TYT neti</div></div>
                    <div><div style={{ ...numText, fontSize: 27, fontWeight: 800, lineHeight: 1, color: color.dawn.coralTextOnLight }}>{trNet(toplamNet)}</div><div style={{ fontSize: 12.5, color: color.ink.muted, marginTop: 5 }}>Toplam net</div></div>
                    <div style={{ alignSelf: 'center', border: `1px solid ${color.paper.border}`, borderRadius: 10, background: color.paper.subtle, padding: '8px 11px' }}><div style={{ ...numText, fontSize: 15, fontWeight: 700, lineHeight: 1, color: color.ink.secondary }}>{exam.tahminiSiralama.toLocaleString('tr-TR')}</div><div style={{ fontSize: 11, color: color.ink.muted, marginTop: 3 }}>Tahmini sıralama · <strong style={{ color: color.ink.secondary }}>yalnız yön göstergesi</strong></div></div>
                  </div>
                </div>
              </div>

              {/* Stat ×4 */}
              <div style={{ display: 'grid', gridTemplateColumns: tek ? '1fr 1fr' : 'repeat(4,1fr)', gap: 14 }}>
                {[
                  { i: <StatIkon icon={<Onay />} bg="#ECFDF5" fg="#1FB683" />, v: d, e: 'Doğru', c: color.ink.primary },
                  { i: <StatIkon icon={<Capraz />} bg="#FBE8E2" fg="#E0593F" />, v: y, e: 'Yanlış', c: color.ink.primary },
                  { i: <StatIkon icon={<Daire />} bg="#F2EEE7" fg="#6B6478" />, v: b, e: 'Boş', c: color.ink.primary },
                  { i: <StatIkon icon={<Grafik />} bg="#FFF3EE" fg={color.dawn.coral} />, v: trNet(toplamNet), e: 'Net', c: color.dawn.coralTextOnLight },
                ].map((s) => (
                  <div key={s.e} style={{ ...kart, borderRadius: 15, padding: '16px 18px', display: 'flex', alignItems: 'center', gap: 13 }}>
                    {s.i}
                    <div><div style={{ ...numText, fontSize: 24, fontWeight: 800, lineHeight: 1, color: s.c }}>{s.v}</div><div style={{ fontSize: 12.5, color: color.ink.muted, marginTop: 3 }}>{s.e}</div></div>
                  </div>
                ))}
              </div>

              {/* İki sütun */}
              <div style={{ display: 'grid', gridTemplateColumns: ikiTek ? '1fr' : '1.5fr 1fr', gap: 18 }}>
                {/* Ders dökümü */}
                <div style={kart}>
                  <h3 style={{ margin: '0 0 14px', fontSize: 17, fontWeight: 700, letterSpacing: '-0.015em' }}>Ders Bazında Net Dökümü</h3>
                  <div style={{ display: 'grid', gap: 15 }}>
                    {satirlar.map((s, idx) => (
                      <div key={idx}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                          <span aria-hidden style={{ width: 9, height: 9, borderRadius: 3, background: s.renk, flexShrink: 0 }} />
                          <span style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.04em', borderRadius: 6, padding: '2px 7px', ...(s.tur === 'TYT' ? { background: '#EEF3F8', color: '#5A6B82' } : { background: '#FBF0DE', color: '#9A5D0D' }) }}>{s.tur}</span>
                          <span style={{ fontSize: 13.5, fontWeight: 700 }}>{s.ad}</span>
                          <span style={{ ...numText, fontSize: 11.5, fontWeight: 600, color: color.ink.muted }}>D{s.dogru} · Y{s.yanlis} · B{s.bos}</span>
                          <span style={{ flex: 1 }} />
                          <span style={{ ...numText, fontSize: 13, fontWeight: 800 }}>{trNet(s.net)} <span style={{ color: color.ink.muted }}>/ {s.soru}</span></span>
                        </div>
                        <ProgressBar pct={s.soru ? (s.net / s.soru) * 100 : 0} color={s.renk} height={8} ariaLabel={`${s.ad} net ${trNet(s.net)}`} />
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gap: 18, alignContent: 'start' }}>
                  {/* AI Analizi */}
                  <div style={kart}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                      <span aria-hidden style={{ width: 32, height: 32, borderRadius: 9, background: color.dawn.coralCtaBg, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}><Katman /></span>
                      <span style={{ fontSize: 14.5, fontWeight: 700 }}>AI Analizi</span>
                    </div>
                    <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.7, color: color.ink.secondary }}>{exam.aiOzet}</p>
                  </div>
                  {/* Zayıf konular */}
                  <div style={kart}>
                    <h3 style={{ margin: '0 0 10px', fontSize: 15, fontWeight: 700 }}>Geliştirilecek konular</h3>
                    <ul style={{ margin: 0, padding: 0, display: 'grid', gap: 9, listStyle: 'none' }}>
                      {zayif.map((z) => (
                        <li key={z.ad} style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                          <span aria-hidden style={{ width: 8, height: 8, borderRadius: 999, flexShrink: 0, background: z.hakimiyet < 50 ? '#E0593F' : '#F59E0B' }} />
                          <span style={{ flex: 1, fontSize: 13, fontWeight: 600 }}>{dersAd[z.ders] ? dersAd[z.ders] + ' · ' : ''}{z.ad}</span>
                          <span style={{ ...numText, fontSize: 12, fontWeight: 700, color: z.hakimiyet < 50 ? color.dawn.coralTextOnLight : '#9A5D0D' }}>%{z.hakimiyet}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* CTA */}
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button type="button" onClick={() => undefined} style={{ flex: 1, minWidth: 220, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8, minHeight: 50, borderRadius: 13, border: 'none', background: color.dawn.coralCtaBg, color: '#fff', cursor: 'pointer', fontFamily: font.sans, fontSize: 14.5, fontWeight: 700 }}><Dongu /><span style={numText}>{y}</span> yanlışı tekrar et (FSRS)</button>
                <button type="button" onClick={() => undefined} style={{ flex: 1, minWidth: 200, minHeight: 50, borderRadius: 13, border: '1px solid #E6DFD4', background: color.paper.card, color: color.ink.secondary, cursor: 'pointer', fontFamily: font.sans, fontSize: 14, fontWeight: 700 }}>Zayıf konuları öğrenme yoluna ekle</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default SonucPage;
