import * as React from 'react';

import { color, font } from '../tokens';
import { useKiroTheme, surf, numText } from './theme';
import { Card } from './Card';
import { Callout } from './Callout';
import { MasteryBadge, type MasteryTrend } from './MasteryBadge';
import type { AnswerResult } from '../api/api-client';

// ============================================================================
// KIRO2 — QuestionCard (SPRINT3 çekirdek-döngü composite · KIRO2 Soru Cozme.dc.html)
// KONTROLLÜ / SUNUM bileşeni: doğru/çözüm/neden'i KENDİ HESAPLAMAZ — `sonuc`
// (postAnswer → AnswerResult) prop'undan alır (kanon: motorlar SUNUCUDA).
// `sonuc` yoksa → etkileşimli (radiogroup); varsa → çözüm/review modu.
// Kaygı-tonu: yanlış = sıcak terracotta/amber "birlikte bakalım", ALARM-KIRMIZISI YOK.
// Hareket YOK (transition/animation kullanılmaz → kanon RM-guard gerekmez).
// ============================================================================

const HARFLER = ['A', 'B', 'C', 'D', 'E', 'F'];

// Review durum paletleri — DC'den birebir; yeşil=doğru, terracotta=yanlış (alarm DEĞİL).
const REVIEW = {
  dogru: { bg: '#E9F8F1', border: '#6FD9B0', rozet: '#1FB683', etiket: '#0E9E6E' },
  yanlis: { bg: '#FCEDE8', border: '#F0A593', rozet: '#E8836B', etiket: color.dawn.coralTextOnLight },
} as const;

// Çözüm paneli (DC "Çözüm · adım adım") — kanon-temiz yeşil aile.
const PANEL = {
  bg: '#EEF9F3', border: '#C5EBD9', baslik: '#0E9E6E',
  adimBg: '#D3EFE1', adimFg: '#0E7C57', nedenMetin: '#3E7A64', neden: '#0E5C40',
} as const;

function zorlukChip(b: number): { ad: string; bg: string; fg: string } {
  if (b < 0.1) return { ad: 'Kolay', bg: '#E3F6EE', fg: '#0E9E6E' };
  if (b <= 0.75) return { ad: 'Orta', bg: '#FBF0DE', fg: '#9A5D0D' };
  return { ad: 'Zor', bg: '#FBE8E2', fg: '#DD5A3D' };
}

const Im = {
  imle: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M19 21l-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z" /></svg>
  ),
  imli: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M19 21l-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2Z" /></svg>
  ),
  ok: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M5 12h14M13 6l6 6-6 6" /></svg>
  ),
  onay: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M20 6 9 17l-5-5" /></svg>
  ),
};

export interface QuestionCardProps {
  soruNo: number;
  toplam: number;
  konu: string;
  /** IRT güçlük — zorluk chip'ini türetir (b<0.1 Kolay · ≤0.75 Orta · Zor) */
  zorlukB: number;
  soru: string;
  secenekler: string[];
  /** Kontrollü seçim (indeks). null = henüz seçilmedi. */
  secilen: number | null;
  /** Seçim callback'i — verilmezse (veya sonuc varsa) şıklar kilitli. */
  onSelect?: (i: number) => void;
  /** Sunucu yanıtı — VARSA çözüm/review modu (doğru/çözüm/neden buradan). */
  sonuc?: AnswerResult | null;
  /** Cevap POST'u uçuşta — seçili ama henüz notlanmadı. */
  bekliyor?: boolean;
  /** Konu hâkimiyet rozeti (opsiyonel). */
  konuHakimiyet?: number;
  konuTrend?: MasteryTrend;
  isaretli?: boolean;
  onToggleIsaret?: () => void;
}

export function QuestionCard({
  soruNo, toplam, konu, zorlukB, soru, secenekler, secilen, onSelect,
  sonuc, bekliyor, konuHakimiyet, konuTrend, isaretli, onToggleIsaret,
}: QuestionCardProps): React.ReactElement {
  const s = surf(useKiroTheme());
  const review = sonuc != null;
  const kilitli = review || !onSelect;
  const zor = zorlukChip(zorlukB);
  const grpRef = React.useRef<HTMLDivElement>(null);

  const oku = (i: number) => {
    if (kilitli || !onSelect) return;
    onSelect(i);
  };

  // Klavye: ok tuşları seçim gezinir; 1-5 / A-E doğrudan seçer (SPRINT3 klavye DoD).
  const grupTus = (e: React.KeyboardEvent) => {
    if (kilitli) return;
    const n = secenekler.length;
    const cur = secilen ?? 0;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') { e.preventDefault(); oku((cur + 1) % n); return; }
    if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') { e.preventDefault(); oku((cur - 1 + n) % n); return; }
    if (e.key === 'Home') { e.preventDefault(); oku(0); return; }
    if (e.key === 'End') { e.preventDefault(); oku(n - 1); return; }
    const d = Number(e.key);
    if (Number.isInteger(d) && d >= 1 && d <= n) { e.preventDefault(); oku(d - 1); return; }
    const h = HARFLER.indexOf(e.key.toUpperCase());
    if (h >= 0 && h < n) { e.preventDefault(); oku(h); }
  };

  const satirGorunum = (i: number): { bg: string; border: string; rozetBg: string; rozetFg: string; etiket?: string; etiketFg?: string } => {
    if (review && sonuc) {
      if (i === sonuc.dogru) return { bg: REVIEW.dogru.bg, border: REVIEW.dogru.border, rozetBg: REVIEW.dogru.rozet, rozetFg: '#fff', etiket: 'Doğru cevap', etiketFg: REVIEW.dogru.etiket };
      if (i === secilen) return { bg: REVIEW.yanlis.bg, border: REVIEW.yanlis.border, rozetBg: REVIEW.yanlis.rozet, rozetFg: '#fff', etiket: 'Senin cevabın', etiketFg: REVIEW.yanlis.etiket };
      return { bg: s.card, border: s.border, rozetBg: '#F2EEE7', rozetFg: color.ink.muted };
    }
    if (i === secilen) return { bg: '#FFF3EE', border: color.dawn.coral, rozetBg: color.dawn.coralCtaBg, rozetFg: '#fff' };
    return { bg: s.card, border: s.border, rozetBg: '#F2EEE7', rozetFg: color.ink.muted };
  };

  return (
    <Card variant="solid" radiusSize="lg" style={{ padding: '28px 30px' }}>
      {/* Meta satırı */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
        <span style={{ ...numText, fontSize: 15, fontWeight: 800, color: s.text }}>
          Soru {soruNo} <span style={{ color: '#A39BAA', fontWeight: 700 }}>/ {toplam}</span>
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, height: 26, padding: '0 11px', borderRadius: 999, background: '#EFF6FF', color: color.subject.light.mat, fontSize: 12, fontWeight: 700 }}>
          <span aria-hidden style={{ width: 7, height: 7, borderRadius: 999, background: color.subject.light.mat }} />{konu}
        </span>
        <span style={{ display: 'inline-flex', alignItems: 'center', height: 26, padding: '0 11px', borderRadius: 999, background: zor.bg, color: zor.fg, fontSize: 12, fontWeight: 700 }}>{zor.ad}</span>
        {konuHakimiyet != null && <MasteryBadge pct={konuHakimiyet} trend={konuTrend} />}
        <span style={{ flex: 1 }} />
        {onToggleIsaret && (
          <button
            type="button" onClick={onToggleIsaret} aria-pressed={!!isaretli}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, minHeight: 44, padding: '0 13px', borderRadius: 9, cursor: 'pointer', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700,
              border: `1px solid ${isaretli ? '#F0D9AC' : s.border}`, background: isaretli ? '#FBF0DE' : s.card, color: isaretli ? '#9A5D0D' : color.ink.muted }}
          >
            {isaretli ? Im.imli : Im.imle}{isaretli ? 'İşaretli' : 'İşaretle'}
          </button>
        )}
      </div>

      {/* Soru gövdesi */}
      <p style={{ margin: '0 0 22px', fontSize: 17, lineHeight: 1.75, color: s.text }}>{soru}</p>

      {/* Şıklar */}
      <div
        ref={grpRef} role="radiogroup" aria-label="Şıklar"
        onKeyDown={grupTus}
        style={{ display: 'grid', gap: 11 }}
      >
        {secenekler.map((sec, i) => {
          const g = satirGorunum(i);
          const secili = i === secilen;
          const odaklanabilir = !kilitli && (secilen == null ? i === 0 : secili);
          return (
            <button
              key={i} type="button" role="radio"
              aria-checked={secili} aria-disabled={kilitli || undefined}
              disabled={kilitli} tabIndex={kilitli ? -1 : odaklanabilir ? 0 : -1}
              onClick={() => oku(i)}
              style={{ display: 'flex', alignItems: 'center', gap: 14, minHeight: 44, padding: '13px 16px', textAlign: 'left', width: '100%',
                borderRadius: 13, cursor: kilitli ? 'default' : 'pointer', fontFamily: font.sans,
                background: g.bg, border: `1.5px solid ${g.border}` }}
            >
              <span aria-hidden style={{ flexShrink: 0, width: 30, height: 30, borderRadius: 9, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13.5, fontWeight: 800, background: g.rozetBg, color: g.rozetFg }}>{HARFLER[i]}</span>
              <span style={{ flex: 1, fontSize: 15, fontWeight: 600, color: review ? '#3A3446' : s.text }}>{sec}</span>
              {g.etiket && <span style={{ flexShrink: 0, fontSize: 12, fontWeight: 800, color: g.etiketFg }}>{g.etiket}</span>}
            </button>
          );
        })}
      </div>

      {/* Cevap geri bildirimi (aria-live) + çözüm paneli — yalnız review */}
      <div aria-live="assertive">
        {review && sonuc && (
          <div style={{ marginTop: 20 }}>
            {sonuc.correct ? (
              <Callout tone="success" icon={Im.onay}>
                <strong>Doğru!</strong> Güzel iş — yine de mantığı pekiştirelim.
              </Callout>
            ) : (
              <Callout tone="attention">
                <strong>Yanlış — hadi nedenini görelim.</strong> Hata, öğrenmenin en değerli anı; aşağıda tam olarak neden.
              </Callout>
            )}
          </div>
        )}
      </div>

      {review && sonuc && (
        <section aria-label="Çözüm" style={{ marginTop: 16, padding: '20px 22px', background: PANEL.bg, border: `1px solid ${PANEL.border}`, borderRadius: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ color: PANEL.baslik, display: 'inline-flex' }}>{Im.onay}</span>
            <span style={{ fontSize: 14.5, fontWeight: 800, color: PANEL.baslik }}>Çözüm · adım adım</span>
            <span style={{ flex: 1 }} />
            <span style={{ ...numText, fontSize: 13, fontWeight: 800, color: PANEL.neden }}>Doğru cevap: {HARFLER[sonuc.dogru]}</span>
          </div>
          <ol style={{ margin: 0, padding: 0, display: 'grid', gap: 10, listStyle: 'none' }}>
            {sonuc.cozum.map((adim, i) => (
              <li key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <span aria-hidden style={{ ...numText, flexShrink: 0, width: 22, height: 22, borderRadius: 999, background: PANEL.adimBg, color: PANEL.adimFg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800 }}>{i + 1}</span>
                <span style={{ fontSize: 14, lineHeight: 1.6, color: '#2A5345' }}>{adim}</span>
              </li>
            ))}
          </ol>
          {sonuc.neden && (
            <p style={{ margin: '12px 0 0', paddingTop: 12, borderTop: `1px solid ${PANEL.border}`, fontSize: 13, lineHeight: 1.6, color: PANEL.nedenMetin }}>
              <strong style={{ color: PANEL.neden }}>Neden:</strong> {sonuc.neden}
            </p>
          )}
          <a href="/sokratik" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 14, minHeight: 44, fontSize: 13, fontWeight: 700, color: color.dawn.coralTextOnLight, textDecoration: 'none' }}>
            Takıldıysan — KIRO Koç ile adım adım{Im.ok}
          </a>
        </section>
      )}

      {bekliyor && !review && (
        <p aria-live="polite" style={{ margin: '16px 0 0', fontSize: 12.5, color: color.ink.muted }}>Cevabın değerlendiriliyor…</p>
      )}
    </Card>
  );
}

export default QuestionCard;
