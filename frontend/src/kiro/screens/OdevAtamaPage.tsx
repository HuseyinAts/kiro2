// ============================================================================
// KIRO2 — Ödev Atama (SPRINT9-B · KIRO2 Odev Atama.dc.html)
// Tema = PAPER (öğretmen çalışma yüzeyi; rol=öğretmen). SideNav(assignments) +
// header + iki-sütun form (konu · kapsam&teslim · öğrenciler) + sağ sticky Özet.
// Rota: /ogretmen/odev/yeni (+ ?ogrenci=id ön-seçim · ?sinif/ders bağlam).
//
// SUNUCU-OTORİTE: θ-tabanlı set kurulumu SUNUCUDA (motor her öğrenci için ayrı
// set kurar). İstemci YALNIZ formu (konuId/adet/teslim/kisisel/ogrenciIds)
// gönderir — soru seçimi / θ / hâkimiyet HESAPLAMAZ. Konu hâkimiyet%/kademe +
// roster θ/hâkimiyet/risk getAtamaKonular / getAtamaRoster'dan OKUNUR.
//
// KOPYA: DC birebir (meslektaş "sana" dili). Empty(roster boş → Sınıf Kurulumu /
// konu havuzu boş) + Error(form-state kaybolmaz) inferred → ONAY BEKLER.
// ============================================================================
import * as React from 'react';

import { getAtamaKonular, getAtamaRoster, postAtama } from '../api/api-client';
import { color, font, hit } from '../tokens';
import type { AtamaForm, AtamaOgrenci, KonuAtom } from '../types';
import { KiroThemeProvider, numText } from '../ui/theme';
import { Button } from '../ui/Button';
import { ErrorState } from '../ui/ErrorState';
import { MasteryBadge } from '../ui/MasteryBadge';
import { SegmentedControl } from '../ui/SegmentedControl';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

const ACCENT = color.dawn.coralCtaBg; // #C2452B — beyaz-metin coral CTA (DC #FF6F5C AA-değil → override)

// SideNav ≤1023px'te 64px ikon rayına çöker (BREAKPOINT_SPEC §3) — jsdom matchMedia'sız guard'lı.
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

// --- Bespoke SVG (emoji/glyph yok) ---
const Geri = (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
  </svg>
);
function Tik({ size = 17, stroke, sw = 2.4 }: { size?: number; stroke: string; sw?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

// --- Kademe etiketi (durum → renk). Zayıf=amber (alarm değil) · Gelişiyor=mavi · Sağlam=yeşil ---
function kademe(durum: KonuAtom['durum']): { t: string; fg: string; bg: string } {
  if (durum === 'zayif') return { t: 'Zayıf', fg: color.semantic.riskTextOnLight, bg: color.semantic.riskBgSoft };
  if (durum === 'gelisiyor') return { t: 'Gelişiyor', fg: '#3B82F6', bg: '#EFF6FF' };
  return { t: 'Sağlam', fg: color.semantic.successTextOnLight, bg: color.semantic.successBgSoft };
}

// --- Teslim yardımcıları (form normalizasyonu — metrik/θ değil) ---
function isoIn(gun: number): string {
  const d = new Date();
  d.setDate(d.getDate() + gun);
  return d.toISOString().slice(0, 10);
}
function nextWeekday(hedef: number): string {
  const d = new Date();
  let ekle = (hedef - d.getDay() + 7) % 7;
  if (ekle === 0) ekle = 7;
  d.setDate(d.getDate() + ekle);
  return d.toISOString().slice(0, 10);
}
type TeslimKey = 'yarin' | 'cuma' | 'pazar' | 'ozel';
function teslimLabel(key: TeslimKey, ozel: string): string {
  if (key === 'yarin') return 'Yarın';
  if (key === 'cuma') return 'Cuma';
  if (key === 'pazar') return 'Pazar';
  if (ozel) return new Intl.DateTimeFormat('tr-TR', { day: 'numeric', month: 'long' }).format(new Date(ozel + 'T00:00:00'));
  return 'Özel tarih';
}
function teslimTarihi(key: TeslimKey, ozel: string): string {
  if (key === 'yarin') return isoIn(1);
  if (key === 'cuma') return nextWeekday(5);
  if (key === 'pazar') return nextWeekday(0);
  return ozel;
}

type AdetKey = '10' | '15' | '20';
const ADET_OPTS: { key: AdetKey; label: string }[] = [
  { key: '10', label: '10' }, { key: '15', label: '15' }, { key: '20', label: '20' },
];
const TESLIM_OPTS: { key: TeslimKey; label: string }[] = [
  { key: 'yarin', label: 'Yarın' }, { key: 'cuma', label: 'Cuma' }, { key: 'pazar', label: 'Pazar' },
];

const sectionStil: React.CSSProperties = {
  boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`,
  borderRadius: 18, padding: 22,
};

// --- Konu radiogroup (ok-tuşlarıyla gezinilir; roving tabindex) ---
function KonuRadioGroup({ konular, seciliId, onSelect }: { konular: KonuAtom[]; seciliId: string | null; onSelect: (id: string) => void }) {
  const refs = React.useRef<(HTMLButtonElement | null)[]>([]);
  const idx = konular.findIndex((k) => k.id === seciliId);

  const onKey = (e: React.KeyboardEvent) => {
    let next = -1;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') next = (idx + 1 + konular.length) % konular.length;
    else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') next = (idx - 1 + konular.length) % konular.length;
    if (next >= 0) {
      e.preventDefault();
      onSelect(konular[next].id);
      refs.current[next]?.focus();
    }
  };

  return (
    <div role="radiogroup" aria-label="Ödev konusu" onKeyDown={onKey} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {konular.map((k, i) => {
        const on = k.id === seciliId;
        const e = kademe(k.durum);
        const havuz = k.soruHavuzuHazir ? 'soru havuzunda hazır' : 'soru havuzu hazırlanıyor';
        return (
          <button
            key={k.id}
            ref={(el) => { refs.current[i] = el; }}
            type="button"
            role="radio"
            aria-checked={on}
            tabIndex={on ? 0 : -1}
            onClick={() => onSelect(k.id)}
            style={{
              boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 12, width: '100%', minHeight: hit.minTarget,
              padding: '12px 14px', borderRadius: 13, border: `1.5px solid ${on ? ACCENT : color.paper.border}`,
              background: on ? '#FFF9F6' : color.paper.card, fontFamily: font.sans, cursor: 'pointer', textAlign: 'left',
            }}
          >
            <span aria-hidden style={{ width: 18, height: 18, flexShrink: 0, borderRadius: '50%', border: `2px solid ${on ? ACCENT : '#D9D2C7'}`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: on ? ACCENT : 'transparent' }} />
            </span>
            <span style={{ flex: 1, minWidth: 0 }}>
              <span style={{ display: 'block', fontSize: 13.5, fontWeight: 700, color: color.ink.primary }}>{k.ad}</span>
              <span style={{ ...numText, display: 'block', fontSize: 11.5, color: color.ink.muted, marginTop: 1 }}>
                Sınıf hâkimiyeti ~%{k.hakimiyet} · {havuz}
              </span>
            </span>
            <span style={{ flexShrink: 0, fontSize: 11, fontWeight: 800, letterSpacing: '0.04em', color: e.fg, background: e.bg, borderRadius: 999, padding: '4px 10px', textTransform: 'uppercase' }}>{e.t}</span>
          </button>
        );
      })}
    </div>
  );
}

// --- Öğrenci seçim satırı (checkbox; risk = amber, öğrenciye bayrak yok) ---
function OgrenciSecimSatiri({ o, secili, dar, onToggle }: { o: AtamaOgrenci; secili: boolean; dar: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={secili}
      onClick={onToggle}
      style={{
        boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 12, width: '100%', minHeight: hit.minTarget,
        padding: '10px 12px', borderRadius: 12, border: `1px solid ${secili ? '#F2D9CE' : color.paper.borderFaint}`,
        background: secili ? '#FFFDFA' : color.paper.card, fontFamily: font.sans, cursor: 'pointer', textAlign: 'left',
      }}
    >
      <span aria-hidden style={{ width: 19, height: 19, flexShrink: 0, borderRadius: 6, border: `2px solid ${secili ? ACCENT : '#D9D2C7'}`, background: secili ? ACCENT : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {secili ? <Tik size={12} stroke="#fff" sw={3.2} /> : null}
      </span>
      <span aria-hidden style={{ width: 30, height: 30, flexShrink: 0, borderRadius: 9, background: '#F2EEE7', color: color.ink.secondary, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11.5, fontWeight: 800 }}>{o.ini}</span>
      <span style={{ flex: 1, minWidth: 0 }}>
        <span style={{ display: 'block', fontSize: 13, fontWeight: 700, color: color.ink.primary }}>{o.ad}</span>
        {o.risk ? (
          <span style={{ display: 'block', fontSize: 11.5, fontWeight: 600, color: color.semantic.riskTextOnLight, marginTop: 1 }}>{o.risk}</span>
        ) : null}
      </span>
      {!dar && <MasteryBadge pct={o.hakimiyet} trend="stable" />}
    </button>
  );
}

function OzetSatiri({ etiket, deger, sayi }: { etiket: string; deger: string; sayi?: boolean }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
      <span style={{ fontSize: 13, color: color.ink.muted, fontWeight: 600 }}>{etiket}</span>
      <span style={{ ...(sayi ? numText : null), fontSize: 13, fontWeight: 700, textAlign: 'right' }}>{deger}</span>
    </div>
  );
}

export interface OdevAtamaPageProps {
  /** ?ogrenci=id — ön-seçim (yalnız bu öğrenci seçili başlar). */
  ogrenciId?: string;
  /** ?sinif — sınıf bağlamı (getAtamaKonular/getAtamaRoster). */
  sinifId?: string;
}

export function OdevAtamaPage({ ogrenciId, sinifId = '12-A' }: OdevAtamaPageProps = {}): React.ReactElement {
  const dar = useMedia('(max-width: 1023px)');
  const tekSutun = useMedia('(max-width: 1120px)');
  const daralt = useMedia('(max-width: 560px)');
  const reduced = useMedia('(prefers-reduced-motion: reduce)');

  const [konular, setKonular] = React.useState<KonuAtom[] | null>(null);
  const [roster, setRoster] = React.useState<AtamaOgrenci[] | null>(null);
  const [seciliKonuId, setSeciliKonuId] = React.useState<string | null>(null);
  const [seciliIds, setSeciliIds] = React.useState<string[] | null>(null);
  const [adet, setAdet] = React.useState(10);
  const [teslimKey, setTeslimKey] = React.useState<TeslimKey>('cuma');
  const [ozelTarih, setOzelTarih] = React.useState('');
  const [kisisel, setKisisel] = React.useState(true);
  const [atandi, setAtandi] = React.useState(false);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  // Herhangi bir form değişikliği başarı bandını sıfırlar (yeni ödev başka bir set demektir).
  const degisti = () => setAtandi(false);

  React.useEffect(() => {
    let alive = true;
    setKonular(null);
    setRoster(null);
    setHata(false);
    Promise.all([getAtamaKonular(sinifId), getAtamaRoster(sinifId)])
      .then(([ks, rs]) => {
        if (!alive) return;
        setKonular(ks);
        setRoster(rs);
        setSeciliKonuId((prev) => prev ?? ks[0]?.id ?? null);
        setSeciliIds((prev) => {
          if (prev) return prev;
          if (ogrenciId && rs.some((r) => r.id === ogrenciId)) return [ogrenciId];
          return rs.map((r) => r.id);
        });
      })
      .catch(() => {
        if (alive) setHata(true);
      });
    return () => {
      alive = false;
    };
  }, [sinifId, ogrenciId, yeniden]);

  const seciliKonu = konular?.find((k) => k.id === seciliKonuId) ?? null;
  const secSayi = seciliIds?.length ?? 0;
  const topSayi = roster?.length ?? 0;
  const hepsi = secSayi > 0 && secSayi === topSayi;

  const konuSec = (id: string) => { setSeciliKonuId(id); degisti(); };
  const ogrenciToggle = (id: string) => {
    setSeciliIds((prev) => {
      const cur = prev ?? [];
      return cur.includes(id) ? cur.filter((x) => x !== id) : cur.concat(id);
    });
    degisti();
  };
  const tumunuSec = () => {
    setSeciliIds(hepsi ? [] : (roster ?? []).map((r) => r.id));
    degisti();
  };
  const ata = async () => {
    if (secSayi === 0 || !seciliKonuId) return;
    const form: AtamaForm = {
      konuId: seciliKonuId, adet, teslimTarihi: teslimTarihi(teslimKey, ozelTarih), kisisel, ogrenciIds: seciliIds ?? [],
    };
    try {
      await postAtama(form);
      setAtandi(true);
    } catch {
      // Form-state korunur (inferred error sözleşmesi → onay bekler).
    }
  };

  const yukleniyor = konular === null || roster === null || seciliIds === null;
  const ozTeslim = teslimLabel(teslimKey, ozelTarih) + ' 23:59';

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ boxSizing: 'border-box', minHeight: '100vh', width: '100%', overflowX: 'hidden', background: color.paper.bg, display: 'flex', fontFamily: font.sans, color: color.ink.primary }}>
        <SideNav role="ogretmen" activeId="assignments" collapsed={dar} userName="Öğretmen" userSub="Sınıf görünümü" showSettings />

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          {/* Header */}
          <header
            style={{
              boxSizing: 'border-box', position: 'sticky', top: 0, zIndex: 5, minHeight: 66, display: 'flex',
              alignItems: 'center', flexWrap: 'wrap', gap: 12, padding: '9px 24px',
              background: 'rgba(250,247,242,0.86)', backdropFilter: 'blur(8px)', borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <a
              href="/ogretmen"
              aria-label="Öğretmen paneline dön"
              style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 44, height: 44, flexShrink: 0, borderRadius: 11, background: color.paper.card, border: `1px solid ${color.paper.border}`, color: color.ink.muted, textDecoration: 'none' }}
            >
              {Geri}
            </a>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 16, fontWeight: 800 }}>Yeni ödev</div>
              <div style={{ fontSize: 12, color: color.ink.muted }}>{sinifId} · Matematik</div>
            </div>
            <span style={{ flex: 1 }} />
            <Button variant="ghost" onClick={() => undefined}>Taslak kaydet</Button>
            <Button variant="primary" disabled={secSayi === 0} onClick={ata}>
              {atandi ? <>Atandı <Tik size={15} stroke="#fff" /></> : `Ödevi ata (${secSayi} öğrenci)`}
            </Button>
          </header>

          <main style={{ boxSizing: 'border-box', width: '100%', maxWidth: 1160, padding: '26px 30px 60px' }}>
            {hata ? (
              <ErrorState
                serifTitle="Ödev ekranı şu an gelmedi."
                body="Sorun sende değil — bağlantı bir soluklandı, seçtiklerin kaybolmadı. Birazdan yeniden dene."
                onRetry={() => setYeniden((n) => n + 1)}
              />
            ) : yukleniyor ? (
              <div aria-busy="true" aria-label="Ödev atama yükleniyor" style={{ display: 'grid', gap: 18 }}>
                <div style={sectionStil}><Skeleton shape="card" delayMs={0} slowAfterMs={null} /></div>
                <div style={sectionStil}><Skeleton shape="row" delayMs={0} /></div>
              </div>
            ) : topSayi === 0 || (konular?.length ?? 0) === 0 ? (
              <div style={{ ...sectionStil, textAlign: 'center', padding: '40px 24px' }}>
                <h2 style={{ margin: '0 0 6px', fontSize: 17, fontWeight: 800 }}>Önce bir sınıf kur.</h2>
                <p style={{ margin: '0 auto', maxWidth: 420, fontSize: 13.5, lineHeight: 1.6, color: color.ink.secondary }}>
                  Ödev atamak için sınıfında öğrenci ve soru havuzu olması yeterli. Sınıf Kurulumu'ndan başlayabilirsin.
                </p>
                <div style={{ marginTop: 18, display: 'flex', justifyContent: 'center' }}>
                  <a href="/ogretmen/siniflar" style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', minHeight: hit.minTarget, padding: '0 18px', borderRadius: 11, background: ACCENT, color: '#fff', fontSize: 13.5, fontWeight: 700, textDecoration: 'none' }}>
                    Sınıf Kurulumu'na git
                  </a>
                </div>
              </div>
            ) : (
              <div className="k-rtwo" style={{ display: 'grid', gridTemplateColumns: tekSutun ? '1fr' : 'minmax(0,1.5fr) minmax(0,1fr)', gap: 20, alignItems: 'start' }}>
                {/* SOL — form */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18, minWidth: 0 }}>
                  {/* 1 · Konu */}
                  <section style={sectionStil}>
                    <h2 style={{ margin: '0 0 4px', fontSize: 15, fontWeight: 800 }}>1 · Konu</h2>
                    <p style={{ margin: '0 0 14px', fontSize: 12.5, color: color.ink.muted }}>Sınıfın son deneme verisine göre zayıf konular önde.</p>
                    <KonuRadioGroup konular={konular ?? []} seciliId={seciliKonuId} onSelect={konuSec} />
                  </section>

                  {/* 2 · Kapsam & teslim */}
                  <section style={sectionStil}>
                    <h2 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 800 }}>2 · Kapsam & teslim</h2>
                    <div style={{ display: 'grid', gridTemplateColumns: daralt ? '1fr' : 'minmax(0,1fr) minmax(0,1fr)', gap: 14 }}>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 8 }}>Soru sayısı</div>
                        <SegmentedControl<AdetKey>
                          options={ADET_OPTS}
                          value={String(adet) as AdetKey}
                          onChange={(k) => { setAdet(Number(k)); degisti(); }}
                          variant="scale"
                          ariaContext="Soru sayısı"
                        />
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 8 }}>Teslim</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                          <SegmentedControl<TeslimKey>
                            options={TESLIM_OPTS}
                            value={teslimKey}
                            onChange={(k) => { setTeslimKey(k); degisti(); }}
                            variant="scale"
                            ariaContext="Teslim günü"
                          />
                          <input
                            type="date"
                            aria-label="Özel teslim tarihi"
                            value={ozelTarih}
                            onChange={(e) => { setOzelTarih(e.target.value); setTeslimKey('ozel'); degisti(); }}
                            style={{ boxSizing: 'border-box', minHeight: hit.minTarget, padding: '0 12px', borderRadius: 11, border: `1.5px solid ${teslimKey === 'ozel' ? ACCENT : color.paper.border}`, background: color.paper.card, fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, color: color.ink.primary }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* θ toggle — kişiye özel zorluk */}
                    <div style={{ boxSizing: 'border-box', marginTop: 16, display: 'flex', alignItems: 'flex-start', gap: 12, padding: '13px 15px', background: '#FFF3EE', border: '1px solid #F6D9CB', borderRadius: 13 }}>
                      <button
                        type="button"
                        role="switch"
                        aria-checked={kisisel}
                        aria-label="Kişiye özel zorluk"
                        onClick={() => { setKisisel((v) => !v); degisti(); }}
                        style={{ boxSizing: 'border-box', width: 44, height: 44, flexShrink: 0, border: 'none', background: 'transparent', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}
                      >
                        <span aria-hidden style={{ position: 'relative', width: 40, height: 24, borderRadius: 999, background: kisisel ? color.semantic.success : '#D9D2C7', display: 'block' }}>
                          <span style={{ position: 'absolute', top: 3, left: 3, width: 18, height: 18, borderRadius: '50%', background: '#fff', boxShadow: '0 1px 3px rgba(0,0,0,0.25)', transform: `translateX(${kisisel ? 16 : 0}px)`, transition: reduced ? undefined : 'transform .15s ease' }} />
                        </span>
                      </button>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 700, color: color.ink.primary }}>Kişiye özel zorluk (önerilen)</div>
                        <div style={{ fontSize: 12, color: color.ink.muted, marginTop: 2, lineHeight: 1.55 }}>
                          Her öğrenci aynı konudan kendi θ seviyesine göre soru alır — kimse boğulmaz, kimse sıkılmaz. Sınıf ortalaması öğrencilere gösterilmez.
                        </div>
                      </div>
                    </div>
                  </section>

                  {/* 3 · Öğrenciler */}
                  <section style={sectionStil}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
                      <h2 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>3 · Öğrenciler</h2>
                      <span aria-live="polite" style={{ ...numText, fontSize: 12, fontWeight: 700, color: color.ink.muted }}>{secSayi} / {topSayi} seçili</span>
                      <span style={{ flex: 1 }} />
                      <button
                        type="button"
                        onClick={tumunuSec}
                        style={{ boxSizing: 'border-box', minHeight: hit.minTarget, display: 'inline-flex', alignItems: 'center', padding: '0 4px', background: 'transparent', border: 'none', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, color: color.dawn.coralTextOnLight, cursor: 'pointer' }}
                      >
                        {hepsi ? 'Tümünü bırak' : 'Tümünü seç'}
                      </button>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {(roster ?? []).map((o) => (
                        <OgrenciSecimSatiri key={o.id} o={o} secili={(seciliIds ?? []).includes(o.id)} dar={daralt} onToggle={() => ogrenciToggle(o.id)} />
                      ))}
                    </div>
                  </section>
                </div>

                {/* SAĞ — özet + kaygı-duyarlı varsayılanlar + başarı bandı */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 18, minWidth: 0, position: tekSutun ? 'static' : 'sticky', top: tekSutun ? undefined : 92 }}>
                  <section style={sectionStil}>
                    <h2 style={{ margin: '0 0 14px', fontSize: 14, fontWeight: 800 }}>Özet</h2>
                    <div aria-live="polite" style={{ display: 'flex', flexDirection: 'column', gap: 11 }}>
                      <OzetSatiri etiket="Konu" deger={`Matematik · ${seciliKonu?.ad ?? '—'}`} />
                      <OzetSatiri etiket="Soru" deger={`${adet} soru · ~${Math.round(adet * 1.6)} dk`} sayi />
                      <OzetSatiri etiket="Teslim" deger={ozTeslim} />
                      <OzetSatiri etiket="Öğrenci" deger={`${secSayi} kişi`} sayi />
                      <OzetSatiri etiket="Zorluk" deger={kisisel ? 'Kişiye özel (θ tabanlı)' : 'Herkese aynı set'} />
                    </div>
                    <div style={{ marginTop: 16, paddingTop: 14, borderTop: `1px solid ${color.paper.borderFaint}`, fontSize: 12, color: color.ink.muted, lineHeight: 1.6 }}>
                      {kisisel
                        ? `Motor, her öğrencinin θ kestirimine göre ${adet} soruluk ayrı bir set kurar; zayıf atomlara ağırlık verir.`
                        : `Tüm sınıf aynı ${adet} soruyu alır. Seviye farkı yüksek sınıflarda kişiye özel zorluk önerilir.`}
                    </div>
                  </section>

                  {/* Kaygı-duyarlı varsayılanlar — öğretmene kanonu öğretir; ASLA kaldırılmaz */}
                  <section style={{ boxSizing: 'border-box', background: color.paper.card, border: '1px dashed #E0D8CB', borderRadius: 18, padding: 20 }}>
                    <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '0.07em', color: color.ink.muted, textTransform: 'uppercase', marginBottom: 10 }}>Kaygı-duyarlı varsayılanlar</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12.5, color: color.ink.secondary, lineHeight: 1.55 }}>
                      {[
                        'Öğrenci yalnız kendi ilerlemesini görür; sınıf sıralaması yayınlanmaz.',
                        'Geciken teslim kapanmaz; "bekliyor" olarak etiketlenir.',
                        'Riskli öğrenciler sana amber ile işaretlenir, öğrenciye bayrak gösterilmez.',
                      ].map((t) => (
                        <div key={t} style={{ display: 'flex', gap: 9 }}>
                          <span style={{ flexShrink: 0, display: 'inline-flex', marginTop: 1 }}><Tik size={15} stroke={color.semantic.successTextOnLight} sw={2.6} /></span>
                          <span>{t}</span>
                        </div>
                      ))}
                    </div>
                  </section>

                  {atandi && (
                    <div role="status" style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 10, padding: '13px 16px', background: '#E4F7F0', border: '1px solid #BEE9D9', borderRadius: 14 }}>
                      <span style={{ display: 'inline-flex', flexShrink: 0 }}><Tik size={17} stroke={color.semantic.successTextOnLight} sw={2.4} /></span>
                      <span style={{ fontSize: 13, fontWeight: 700, color: color.semantic.successTextOnLight }}>Ödev atandı — öğrencilere sakin bir bildirim gitti.</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default OdevAtamaPage;
