// ============================================================================
// KIRO2 — Sokratik AI (SPRINT11 · Grup 9 · KIRO2 Sokratik AI.dc.html)
// Tema = PAPER (öğrenci → SEN). 3-sütun uygulama kabuğu:
//   SideNav(active 'ai') + MERKEZ sohbet kolonu (topbar → konuşma akışı ChatBubble
//   → giriş dock) + SAĞ RAY ("Üzerinde çalışılan soru" + "İpucu merdiveni" +
//   "Sokratik ilerleme"). ≤1023px sağ ray gizlenir; ≤760px SideNav 64px'e çöker.
//
// SUNUCU-OTORİTE: AI yanıtı streamSohbet(teaching:'socratic') ile SUNUCUDAN akar —
// istemci CEVAP UYDURMAZ. Sokratik ton cevabı VERMEZ, yönlendirir (kiro-data.sokratik
// acilis + adimlar yönlendirici sorular). "Çözümü göster (son çare)" → sunucudan
// direct-mode YÖNTEM açıklaması (yine istemci sonuç hesaplamaz). "Üzerinde çalışılan
// soru" öğrencinin ilk mesajından türetilir (istemci soru uydurmaz).
//
// KANON: paper CTA/pil = coralCtaBg #C2452B + beyaz; coral METİN #C2452B (#FF6F5C
// yalnız dekoratif gradyanda). Risk/seri = amber (#9A5D0D metin); alarm-kırmızı YOK.
// İkincil metin ink.muted (AA). Streaming typing-dots RM-guard (useReducedMotion) +
// yalnız opacity — layout-anim yok; progress fill genişliği STATIK (transition yok).
// box-sizing:border-box KÖK dahil; hit-target ≥44; bespoke SVG; emoji yok; SEN dili.
// ============================================================================
import * as React from 'react';

import {
  getMe, getSohbet, postSohbetMesaj, streamSohbet,
} from '../api/api-client';
import { color, font } from '../tokens';
import type { Persona, SohbetMesaj, SohbetOturum } from '../types';
import { ChatBubble } from '../ui/ChatBubble';
import { useReducedMotion } from '../ui/ConfettiDawn';
import { EmptyState } from '../ui/EmptyState';
import { ErrorState } from '../ui/ErrorState';
import { SideNav } from '../ui/SideNav';
import { Skeleton } from '../ui/Skeleton';
import { KiroThemeProvider, numText } from '../ui/theme';
import '../tokens/tokens.css';

// Ekranda tutulan mesaj — SohbetMesaj + streaming sırasında soluk balon işareti.
type EkranMesaj = SohbetMesaj & { pending?: boolean };

// İpucu merdiveni etiketleri (DC-birebir statik — 3 basamak). Kaynak: DC labels.
const MERDIVEN = ['Kavramı hatırlat', 'Yöntemi yönlendir', 'İlk adımı birlikte yap'] as const;

// Typing-dots opacity nabzı — yalnız opacity (layout-anim yok), 500ms (LONG_DURATION eşiği altı).
const TYPING_KEYFRAMES = '@keyframes kiroType { 0%,100% { opacity: 0.22; } 50% { opacity: 0.9; } }';

// Giriş alanı odak halkası — statik (hareket değil). Inline outline:none GLOBAL
// :focus-visible halkasını ezmesin diye class-tabanlı: base outline'ı susturur,
// klavye odağında coral (#C2452B) halka basar (AISohbet .k-chat-field deseni · a11y 2.4.7).
const FOCUS_STYLE =
  `.k-sok-field{outline:none;}.k-sok-field:focus-visible{outline:2px solid ${color.dawn.coralCtaBg};outline-offset:2px;}`;

// ---- Bespoke inline SVG (emoji/stok-lib YOK) ----
const RobotIcon = (
  <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="M12 8V4M8 8h8M5 12h14a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1Z" />
    <circle cx="9" cy="16" r="1" fill="#fff" stroke="none" /><circle cx="15" cy="16" r="1" fill="#fff" stroke="none" />
  </svg>
);
const InfoIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="9" /><path d="M12 16v-4M12 8h.01" />
  </svg>
);
const BulbIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0 }}>
    <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2Z" />
  </svg>
);
const SendIcon = (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <path d="m22 2-7 20-4-9-9-4Z" /><path d="M22 2 11 13" />
  </svg>
);
const CheckIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const FlameIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0 }}>
    <path d="M12 2c1.2 3 4 4.2 4 7.8A4 4 0 0 1 8 10c0-1.4.5-2.4 1-3 .2 1 .9 1.6 1.6 1.6C9.6 6.4 10.8 4.2 12 2Z" />
  </svg>
);
const RetryIcon = (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0 }}>
    <path d="M3 12a9 9 0 0 1 15-6.6L21 8" /><path d="M21 4v4h-4" />
  </svg>
);
function LockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.ink.faded3} strokeWidth="2" aria-hidden style={{ marginLeft: 'auto', flexShrink: 0 }}>
      <rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  );
}

// ---- jsdom matchMedia'sız guard'lı responsive kanca ----
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

// ---- Streaming "düşünüyor" göstergesi — RM-guard + calmMode saygı ----
function TypingDots({ reduced }: { reduced: boolean }) {
  if (reduced) {
    return <span style={{ fontFamily: font.sans, fontSize: 14, color: color.ink.muted }}>düşünüyor…</span>;
  }
  return (
    <span aria-label="düşünüyor" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <style>{TYPING_KEYFRAMES}</style>
      {[0, 1, 2].map((i) => (
        <span key={i} aria-hidden style={{ width: 6, height: 6, borderRadius: '50%', background: color.dawn.coralTextOnLight, opacity: 0.22, animation: `kiroType 500ms ease-in-out ${i * 150}ms infinite` }} />
      ))}
    </span>
  );
}

// ---- Sohbet balonu — SohbetMesaj → ChatBubble props eşlemesi ----
function Balon({ m, reduced }: { m: EkranMesaj; reduced: boolean }) {
  if (m.rol === 'ben') {
    return <ChatBubble role="me">{m.metin}</ChatBubble>;
  }
  const dogrudan = m.tag === 'Doğrudan çözüm';
  const govde = m.pending && !m.metin ? <TypingDots reduced={reduced} /> : m.metin;
  return (
    <ChatBubble
      role="ai"
      pending={m.pending}
      {...(m.tag ? { tag: m.tag } : {})}
      {...(dogrudan ? { tagBg: color.semantic.riskBgSoft, tagFg: color.semantic.riskTextOnLight } : {})}
    >
      {govde}
    </ChatBubble>
  );
}

// ---- Topbar durum pili (seri / xp) ----
function DurumPil({ bg, fg, ikon, deger }: { bg: string; fg: string; ikon: React.ReactNode; deger: string }) {
  return (
    <div style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 6, padding: '7px 12px', borderRadius: 999, background: bg, color: fg }}>
      {ikon}
      <span style={{ ...numText, fontSize: 13, fontWeight: 800 }}>{deger}</span>
    </div>
  );
}

// ---- İpucu merdiveni basamağı ----
function MerdivenSatir({ label, durum, no }: { label: string; durum: 'done' | 'active' | 'locked'; no: number }) {
  const stil = durum === 'done'
    ? { rowBg: color.semantic.successBgSoft, rowBorder: `1px solid ${color.semantic.successBorderSoft}`, numBg: color.semantic.success, numFg: '#fff', labelColor: color.semantic.successTextOnLight, weight: 700 as const }
    : durum === 'active'
      ? { rowBg: '#FFF3EE', rowBorder: `1px solid ${color.dawn.coralCtaBg}`, numBg: color.dawn.coralCtaBg, numFg: '#fff', labelColor: color.ink.primary, weight: 700 as const }
      : { rowBg: color.paper.subtle2, rowBorder: `1px dashed ${color.paper.borderStrong}`, numBg: color.paper.border, numFg: color.ink.muted, labelColor: color.ink.muted, weight: 600 as const };
  return (
    <div style={{ boxSizing: 'border-box', display: 'flex', gap: 10, alignItems: 'center', padding: '10px 12px', borderRadius: 10, background: stil.rowBg, border: stil.rowBorder }}>
      <span aria-hidden style={{ width: 22, height: 22, flexShrink: 0, borderRadius: '50%', background: stil.numBg, color: stil.numFg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {durum === 'done' ? CheckIcon : <span style={{ ...numText, fontSize: 11, fontWeight: 800 }}>{no}</span>}
      </span>
      <div style={{ fontSize: 12.5, fontWeight: stil.weight, color: stil.labelColor }}>{label}</div>
      {durum === 'locked' && <LockIcon />}
    </div>
  );
}

export function SokratikPage(): React.ReactElement {
  const reduced = useReducedMotion();
  const railGizli = useMedia('(max-width: 1023px)'); // sağ ray gizle
  const navDar = useMedia('(max-width: 760px)'); // SideNav 64px

  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [oturum, setOturum] = React.useState<SohbetOturum | null>(null);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  const [mesajlar, setMesajlar] = React.useState<EkranMesaj[]>([]);
  const [input, setInput] = React.useState('');
  const [pending, setPending] = React.useState(false);
  const [streamHata, setStreamHata] = React.useState(false);
  const [sonMetin, setSonMetin] = React.useState('');
  const [aiTamamlanan, setAiTamamlanan] = React.useState(0);
  const [cozuldu, setCozuldu] = React.useState(false);

  const oturumIdRef = React.useRef<string>('');
  const unsubRef = React.useRef<(() => void) | null>(null);

  // --- Açılış oturumu yükle (Sokratik kip) ---
  React.useEffect(() => {
    let alive = true;
    setOturum(null);
    setHata(false);
    setMesajlar([]);
    setPending(false);
    setStreamHata(false);
    setAiTamamlanan(0);
    setCozuldu(false);
    Promise.all([getMe().catch(() => null), getSohbet('socratic')])
      .then(([p, o]) => {
        if (!alive) return;
        setPersona(p);
        setOturum(o);
        setMesajlar(o.mesajlar.map((m) => ({ ...m })));
        oturumIdRef.current = o.id;
      })
      .catch(() => { if (alive) setHata(true); });
    return () => {
      alive = false;
      if (unsubRef.current) { unsubRef.current(); unsubRef.current = null; }
    };
  }, [yeniden]);

  // Merdiven tamamlanınca çözüldü say.
  React.useEffect(() => {
    if (aiTamamlanan >= MERDIVEN.length) setCozuldu(true);
  }, [aiTamamlanan]);

  // --- Kullanıcı mesajı gönder → Sokratik akış (streamSohbet) ---
  const gonder = React.useCallback((metinRaw: string) => {
    const metin = metinRaw.trim();
    if (!metin || pending) return;
    setStreamHata(false);
    setSonMetin(metin);
    const benId = `ben-${Date.now()}`;
    const aiId = `ai-${Date.now()}`;
    const ipucuNo = Math.min(aiTamamlanan + 1, MERDIVEN.length);
    const tag = `İpucu ${ipucuNo} / ${MERDIVEN.length}`;
    setMesajlar((prev) => [
      ...prev,
      { id: benId, rol: 'ben', metin },
      { id: aiId, rol: 'ai', metin: '', pending: true, tag },
    ]);
    setInput('');
    setPending(true);
    if (unsubRef.current) { unsubRef.current(); unsubRef.current = null; }
    unsubRef.current = streamSohbet(
      { oturumId: oturumIdRef.current, metin, teaching: 'socratic' },
      {
        onConnected: (id) => { oturumIdRef.current = id; },
        onToken: (t) => {
          setMesajlar((prev) => prev.map((m) => (m.id === aiId ? { ...m, metin: m.metin + t } : m)));
        },
        onFinished: (msg) => {
          setMesajlar((prev) => prev.map((m) => (m.id === aiId ? { ...msg, id: aiId, tag, pending: false } : m)));
          setAiTamamlanan((n) => Math.min(n + 1, MERDIVEN.length));
          setPending(false);
          unsubRef.current = null;
        },
        onError: () => {
          setMesajlar((prev) => prev.filter((m) => m.id !== aiId && m.id !== benId));
          setPending(false);
          setStreamHata(true);
          unsubRef.current = null;
        },
      },
    );
  }, [aiTamamlanan, pending]);

  // --- Çözümü göster (son çare) → sunucudan DIRECT-mode yöntem açıklaması ---
  const cozumuGoster = React.useCallback(async () => {
    if (pending) return;
    setStreamHata(false);
    const aiId = `ai-cozum-${Date.now()}`;
    setMesajlar((prev) => [...prev, { id: aiId, rol: 'ai', metin: '', pending: true, tag: 'Doğrudan çözüm' }]);
    setPending(true);
    try {
      const msg = await postSohbetMesaj({ oturumId: oturumIdRef.current, metin: 'Çözümü göster', teaching: 'direct' });
      setMesajlar((prev) => prev.map((m) => (m.id === aiId ? { ...msg, id: aiId, tag: 'Doğrudan çözüm', pending: false } : m)));
      setCozuldu(true);
    } catch {
      setMesajlar((prev) => prev.filter((m) => m.id !== aiId));
      setStreamHata(true);
    } finally {
      setPending(false);
    }
  }, [pending]);

  // --- Yeniden başla (çözüldü → yeni açılış) ---
  const bastan = React.useCallback(() => {
    if (unsubRef.current) { unsubRef.current(); unsubRef.current = null; }
    setMesajlar(oturum ? oturum.mesajlar.map((m) => ({ ...m })) : []);
    setInput('');
    setPending(false);
    setStreamHata(false);
    setAiTamamlanan(0);
    setCozuldu(false);
  }, [oturum]);

  // Türetilmiş değerler
  const soruText = mesajlar.find((m) => m.rol === 'ben')?.metin ?? null;
  const doneCount = cozuldu ? MERDIVEN.length : Math.min(aiTamamlanan, MERDIVEN.length);
  const progressPct = `${Math.round((doneCount / MERDIVEN.length) * 100)}%`;
  const gonderKapali = !input.trim() || pending;

  // ---- Sağ ray (İçerik + İpucu merdiveni + Sokratik ilerleme) ----
  const sagRay = (
    <aside
      style={{ boxSizing: 'border-box', width: 328, flexShrink: 0, borderLeft: `1px solid ${color.paper.border}`, background: color.paper.card, overflowY: 'auto', padding: '22px 20px' }}
      aria-label="Sokratik oturum durumu"
    >
      {/* Üzerinde çalışılan soru — öğrencinin ilk mesajından (sunucu-otorite: istemci soru uydurmaz) */}
      <div style={{ boxSizing: 'border-box', border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: 16, marginBottom: 16 }}>
        <div style={{ fontSize: 10.5, fontWeight: 800, color: color.ink.muted, letterSpacing: '0.05em', marginBottom: 9 }}>ÜZERİNDE ÇALIŞILAN</div>
        {soruText ? (
          <>
            <div style={{ fontSize: 14, color: color.ink.primary, fontWeight: 600, lineHeight: 1.5, marginBottom: 10 }}>{soruText}</div>
            <span style={{ fontSize: 11, fontWeight: 700, color: color.dawn.coralTextOnLight, background: '#FFF3EE', padding: '3px 9px', borderRadius: 7 }}>Senin sorun</span>
          </>
        ) : (
          <div style={{ fontSize: 13, color: color.ink.muted, lineHeight: 1.55 }}>Aşağıya bir soru yaz — üzerinde birlikte, adım adım çalışalım.</div>
        )}
      </div>

      {/* İpucu merdiveni */}
      <div style={{ boxSizing: 'border-box', border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: 16, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: color.ink.primary }}>İpucu merdiveni</div>
          <span style={{ ...numText, fontSize: 11, fontWeight: 700, color: color.dawn.coralTextOnLight }}>{doneCount} / {MERDIVEN.length}</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {MERDIVEN.map((label, i) => {
            const durum = i < doneCount ? 'done' : (i === doneCount && !cozuldu ? 'active' : 'locked');
            return <MerdivenSatir key={label} label={label} durum={durum} no={i + 1} />;
          })}
        </div>
        <button
          type="button"
          onClick={cozumuGoster}
          disabled={pending}
          style={{ boxSizing: 'border-box', display: 'block', width: '100%', minHeight: 44, marginTop: 11, background: 'transparent', border: `1px solid ${color.dawn.coralTextOnLight}`, color: color.dawn.coralTextOnLight, borderRadius: 10, padding: '9px', fontFamily: font.sans, fontSize: 12, fontWeight: 700, cursor: pending ? 'not-allowed' : 'pointer', opacity: pending ? 0.55 : 1 }}
        >
          Çözümü göster (son çare)
        </button>
        <div style={{ marginTop: 9, fontSize: 11, color: color.ink.muted, lineHeight: 1.5, textAlign: 'center' }}>Cevabı görmek yerine ipucu iste — getirim etkisi korunur.</div>
      </div>

      {/* Sokratik ilerleme */}
      <div style={{ boxSizing: 'border-box', border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 800, color: color.ink.primary, marginBottom: 11 }}>Sokratik ilerleme</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <div aria-hidden style={{ flex: 1, height: 8, borderRadius: 999, background: color.paper.borderFaint, overflow: 'hidden' }}>
            {/* Genişlik STATIK (transition yok → layout-anim kanonu) */}
            <div style={{ width: progressPct, height: '100%', borderRadius: 999, background: `linear-gradient(90deg, ${color.dawn.coralCtaBg}, ${color.dawn.coral2})` }} />
          </div>
          <span style={{ ...numText, fontSize: 12, fontWeight: 800, color: color.dawn.coralTextOnLight }}>{doneCount}/{MERDIVEN.length}</span>
        </div>
        <div style={{ fontSize: 12, color: color.ink.muted, lineHeight: 1.5 }}>Adım: ilişki → yöntem → sonuç.</div>
        <div style={{ boxSizing: 'border-box', marginTop: 12, padding: '11px 13px', borderRadius: 10, background: color.semantic.successBgSoft, fontSize: 12, color: color.semantic.successTextOnLight, fontWeight: 600, lineHeight: 1.5 }}>
          {cozuldu ? 'Mükemmel — kavramı kendin kurdun! Getirim etkisi tam.' : 'İpucu iste, cevabı değil — her adımı kendin kurdukça kalıcılık artar.'}
        </div>
      </div>
    </aside>
  );

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{ boxSizing: 'border-box', height: '100vh', width: '100%', overflowX: 'hidden', display: 'flex', background: color.paper.bg, fontFamily: font.sans, color: color.ink.primary, fontSize: 14 }}
      >
        <style>{FOCUS_STYLE}</style>
        <SideNav role="ogrenci" activeId="ai" collapsed={navDar} userName={persona?.ad ?? 'Öğrenci'} userSub={persona?.sinif ?? ''} onAssistant={() => undefined} />

        <main style={{ boxSizing: 'border-box', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100vh', minHeight: 0 }}>

          {/* Topbar */}
          <header style={{ boxSizing: 'border-box', flexShrink: 0, minHeight: 64, background: color.paper.card, borderBottom: `1px solid ${color.paper.border}`, display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', rowGap: 8, padding: '10px 26px' }}>
            <div aria-hidden style={{ width: 36, height: 36, flexShrink: 0, borderRadius: 10, background: 'linear-gradient(135deg,#C2452B,#FF6F5C)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{RobotIcon}</div>
            <div style={{ lineHeight: 1.2 }}>
              <div style={{ fontWeight: 800, fontSize: 16, color: color.ink.primary }}>KIRO Sokratik Asistan</div>
              <div style={{ fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>Qwen3-8B · Türkçe öğretmen modeli</div>
            </div>
            <div style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 7, padding: '6px 12px', borderRadius: 999, background: '#FFF3EE' }}>
              <span aria-hidden style={{ width: 7, height: 7, borderRadius: '50%', background: color.dawn.coralCtaBg }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: color.dawn.coralTextOnLight }}>Sokratik mod · cevabı vermez</span>
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
              {persona?.seri != null && <DurumPil bg={color.semantic.riskBgSoft} fg={color.semantic.riskTextOnLight} ikon={FlameIcon} deger={String(persona.seri)} />}
              {persona?.xp != null && <DurumPil bg="#FFF3EE" fg={color.dawn.coralTextOnLight} ikon={<span style={{ fontSize: 12, fontWeight: 800 }}>XP</span>} deger={persona.xp.toLocaleString('tr-TR')} />}
            </div>
          </header>

          {/* Body — sohbet kolonu + sağ ray */}
          <div style={{ boxSizing: 'border-box', flex: 1, minHeight: 0, display: 'flex' }}>

            {/* Sohbet kolonu */}
            <section style={{ boxSizing: 'border-box', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', minHeight: 0 }}>

              {hata ? (
                <div style={{ boxSizing: 'border-box', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
                  <div style={{ width: '100%', maxWidth: 520 }}>
                    <ErrorState
                      serifTitle="Sokratik oturum şu an açılmadı."
                      body="Sorun sende değil — bağlantı bir soluklandı, ilerlemen güvende. Hazır olduğunda yeniden dene."
                      onRetry={() => setYeniden((n) => n + 1)}
                    />
                  </div>
                </div>
              ) : oturum === null ? (
                <div aria-busy="true" aria-label="Sohbet yükleniyor" style={{ boxSizing: 'border-box', flex: 1, overflowY: 'auto', padding: navDar ? '18px' : '26px 30px' }}>
                  <div style={{ boxSizing: 'border-box', maxWidth: 680, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 18 }}>
                    {[0, 1, 2].map((i) => (
                      <div key={i} style={{ boxSizing: 'border-box', alignSelf: i % 2 ? 'flex-end' : 'flex-start', width: '70%' }}>
                        <div style={{ boxSizing: 'border-box', background: color.paper.card, border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: '14px 16px' }}>
                          <Skeleton shape="row" delayMs={0} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : mesajlar.length === 0 ? (
                <div style={{ boxSizing: 'border-box', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
                  <div style={{ width: '100%', maxWidth: 520 }}>
                    <EmptyState
                      serifTitle="Birlikte başlayalım."
                      body="Aşağıya takıldığın soruyu yaz — cevabı vermeden, adım adım seni çözüme yönlendireceğim."
                    />
                  </div>
                </div>
              ) : (
                <div
                  role="log"
                  aria-live="polite"
                  aria-label="Sokratik sohbet"
                  style={{ boxSizing: 'border-box', flex: 1, minHeight: 0, overflowY: 'auto', padding: navDar ? '18px' : '26px 30px' }}
                >
                  <div style={{ boxSizing: 'border-box', maxWidth: 680, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {/* Açılış bildirimi (DC-birebir) */}
                    <div style={{ boxSizing: 'border-box', alignSelf: 'center', display: 'flex', alignItems: 'center', gap: 9, padding: '8px 15px', borderRadius: 999, background: '#FFF3EE', border: '1px solid #F2D9CE', fontSize: 12, fontWeight: 600, color: color.dawn.coralTextOnLight }}>
                      {InfoIcon}
                      Bu mod cevabı vermez — birlikte düşünür. Öğrenme etkisi korunur.
                    </div>

                    {mesajlar.map((m) => <Balon key={m.id} m={m} reduced={reduced} />)}

                    {streamHata && (
                      <div role="status" style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', padding: '11px 14px', borderRadius: 12, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}` }}>
                        <span style={{ fontSize: 12.5, fontWeight: 600, color: color.semantic.riskTextOnLight, lineHeight: 1.5 }}>Bağlantı bir soluklandı — sorun sende değil.</span>
                        <button
                          type="button"
                          onClick={() => gonder(sonMetin)}
                          style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 6, minHeight: 44, marginLeft: 'auto', background: color.paper.card, border: `1px solid ${color.semantic.riskBorderSoft}`, color: color.semantic.riskTextOnLight, borderRadius: 9, padding: '7px 12px', fontFamily: font.sans, fontSize: 12, fontWeight: 700, cursor: 'pointer' }}
                        >
                          {RetryIcon} Tekrar dene
                        </button>
                      </div>
                    )}

                    {/* İpucu istek çipleri (rail gizliyken de burada erişilir) veya çözüldü çipi */}
                    {cozuldu ? (
                      <div style={{ paddingLeft: 43 }}>
                        <button
                          type="button"
                          onClick={bastan}
                          style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, background: color.semantic.successBgSoft, border: `1px solid ${color.semantic.successBorderSoft}`, color: color.semantic.successTextOnLight, borderRadius: 10, padding: '9px 14px', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, cursor: 'pointer' }}
                        >
                          {CheckIcon} Çözdün — yeni soruyla baştan
                        </button>
                      </div>
                    ) : (
                      <>
                        <div style={{ display: 'flex', gap: 9, flexWrap: 'wrap', paddingLeft: 43 }}>
                          <button
                            type="button"
                            onClick={() => gonder('Bir ipucu daha verir misin?')}
                            disabled={pending}
                            style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, background: color.paper.card, border: '1px solid #F2D9CE', color: color.dawn.coralTextOnLight, borderRadius: 10, padding: '9px 14px', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, cursor: pending ? 'not-allowed' : 'pointer', opacity: pending ? 0.55 : 1 }}
                          >
                            {BulbIcon} Bir ipucu daha ver
                          </button>
                          <button
                            type="button"
                            onClick={() => gonder('Bir örnek üzerinden gösterir misin?')}
                            disabled={pending}
                            style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, background: color.paper.card, border: `1px solid ${color.paper.border}`, color: color.ink.muted, borderRadius: 10, padding: '9px 14px', fontFamily: font.sans, fontSize: 12.5, fontWeight: 600, cursor: pending ? 'not-allowed' : 'pointer', opacity: pending ? 0.55 : 1 }}
                          >
                            Örnek göster
                          </button>
                        </div>
                        {/* railGizli iken sağ ray unmount → "son çare" + kompakt ilerleme ana kola
                            taşınır; geniş ekranda sağ ray gösterir → çift-gösterim yok. */}
                        {railGizli && (
                          <div style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', paddingLeft: 43 }}>
                            <button
                              type="button"
                              onClick={cozumuGoster}
                              disabled={pending}
                              style={{ boxSizing: 'border-box', display: 'inline-flex', alignItems: 'center', gap: 7, minHeight: 44, background: 'transparent', border: `1px solid ${color.dawn.coralTextOnLight}`, color: color.dawn.coralTextOnLight, borderRadius: 10, padding: '9px 14px', fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, cursor: pending ? 'not-allowed' : 'pointer', opacity: pending ? 0.55 : 1 }}
                            >
                              Çözümü göster (son çare)
                            </button>
                            <span style={{ ...numText, fontSize: 12, fontWeight: 800, color: color.dawn.coralTextOnLight }} aria-label={`Sokratik ilerleme ${doneCount} / ${MERDIVEN.length}`}>{doneCount}/{MERDIVEN.length}</span>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Giriş dock — yalnız oturum açıkken */}
              {oturum !== null && !hata && mesajlar.length > 0 && (
                <div style={{ boxSizing: 'border-box', flexShrink: 0, borderTop: `1px solid ${color.paper.border}`, background: color.paper.card, padding: navDar ? '12px 18px' : '16px 30px' }}>
                  <div style={{ boxSizing: 'border-box', maxWidth: 680, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 12, background: color.paper.bg, border: `1px solid ${color.paper.border}`, borderRadius: 14, padding: '7px 7px 7px 18px' }}>
                    <input
                      className="k-sok-field"
                      aria-label="Düşünceni yaz"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); gonder(input); } }}
                      placeholder="Düşünceni yaz — adım adım gidelim…"
                      style={{ boxSizing: 'border-box', flex: 1, minWidth: 0, minHeight: 44, padding: '0 6px', border: 'none', background: 'transparent', fontFamily: font.sans, fontSize: 14, color: color.ink.primary }}
                    />
                    <button
                      type="button"
                      onClick={() => gonder(input)}
                      disabled={gonderKapali}
                      aria-label="Gönder"
                      style={{ boxSizing: 'border-box', width: 44, height: 44, flexShrink: 0, borderRadius: 11, background: gonderKapali ? color.paper.borderStrong : color.dawn.coralCtaBg, border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: gonderKapali ? 'not-allowed' : 'pointer' }}
                    >
                      {SendIcon}
                    </button>
                  </div>
                </div>
              )}
            </section>

            {/* Sağ ray — ≤1023px gizli */}
            {!railGizli && sagRay}
          </div>
        </main>
      </div>
    </KiroThemeProvider>
  );
}

export default SokratikPage;
