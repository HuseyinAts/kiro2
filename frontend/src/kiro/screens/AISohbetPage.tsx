// ============================================================================
// KIRO2 — AI Sohbet (SPRINT11 · Grup 9 · KIRO2 AI Sohbet.dc.html · TEMA = PAPER)
// Öğrenci → SEN dili. AI Öğretmen Asistanı: kullanıcı yazar, sunucu-otoriter yanıt
// streamSohbet'ten token token akar (istemci CEVAP UYDURMAZ — mock katmanı sunucu
// yanıtının deterministik eşdeğeri). Yöntem = 'direct' (Sokratik AI ayrı ekran).
//
// Akış: getSohbet('direct') → açılış AI mesajı (boş sohbet durumu). Kullanıcı gönderince
//   (a) {rol:'ben'} balon + (b) {rol:'ai', pending} balon push → onToken metne APPEND →
//   onFinished pending'i tam mesajla değiştir. streamSohbet unsubscribe DÖNER; unmount +
//   yeni mesaj öncesi çağrılır (cleanup). Stream/fetch hatası → sakin ErrorState (tekrar).
// A11y: mesaj listesi role="log" aria-live="polite" (token akışı duyurulur); Enter=gönder,
//   Shift+Enter=yeni satır; ikon-yalnız düğmelerde aria-label. Motion: yalnız "yazıyor"
//   opasite-nabzı — useReducedMotion + calmMode saygı (layout-anim yok).
// ============================================================================
import * as React from 'react';

import {
  getMe,
  getSohbet,
  streamSohbet,
} from '../api/api-client';
import { color, font } from '../tokens';
import type { Persona, SohbetMesaj, SohbetOturum } from '../types';
import { KiroThemeProvider } from '../ui/theme';
import { useReducedMotion } from '../ui/ConfettiDawn';
import { ChatBubble } from '../ui/ChatBubble';
import { ErrorState } from '../ui/ErrorState';
import { Skeleton } from '../ui/Skeleton';
import { SideNav } from '../ui/SideNav';
import '../tokens/tokens.css';

// "Yazıyor" opasite nabzı — yalnız transform/opacity (layout hareketi YOK).
const DOT_KEYFRAMES = '@keyframes kiroChatDot{0%,80%,100%{opacity:.3}40%{opacity:1}}';
// Odak halkası CSS'te (inline outline:none ile EZİLEMEZ — 2.4.7 görünür odak).
// Taban outline'ı gizle, :focus-visible ile görünür coral halka geri getir.
const FOCUS_STYLE =
  `.k-chat-field{outline:none;}` +
  `.k-chat-field:focus-visible{outline:2px solid ${color.dawn.coralCtaBg};outline-offset:2px;}`;

const srOnly: React.CSSProperties = {
  position: 'absolute', width: 1, height: 1, padding: 0, margin: -1,
  overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', border: 0,
};

// SideNav ≤1023px'te 64px ikon rayına çöker — jsdom matchMedia'sız guard'lı.
function useDarEkran(): boolean {
  const [dar, setDar] = React.useState(false);
  React.useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(max-width: 1023px)');
    const on = () => setDar(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return dar;
}

function TypingDots({ reduced }: { reduced: boolean }): React.ReactElement {
  return (
    <span aria-hidden style={{ display: 'inline-flex', gap: 4, alignItems: 'center', padding: '3px 0' }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            width: 6, height: 6, borderRadius: '50%', background: color.ink.muted,
            opacity: reduced ? 0.5 : undefined,
            animation: reduced ? undefined : `kiroChatDot 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </span>
  );
}

// Topbar AI kimlik ikonu (bespoke SVG — mesaj balonu + kıvılcım).
function AsistanIkon(): React.ReactElement {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z" />
      <path d="m11 8 1 2 2 1-2 1-1 2-1-2-2-1 2-1Z" />
    </svg>
  );
}

/** studentId (F4-S1b): backend chat isteklerine (streamSohbet) student_id olarak geçer.
 *  App-side route wrapper (authStore.user.id) enjekte eder; verilmezse mock modda
 *  etkisiz, live modda backend zorunlu alan olduğundan istek 422 döner (auth/mount hatası sinyali). */
export interface AISohbetPageProps {
  studentId?: string;
}

export function AISohbetPage({ studentId }: AISohbetPageProps = {}): React.ReactElement {
  const dar = useDarEkran();
  const reduced = useReducedMotion();

  const [persona, setPersona] = React.useState<Persona | null>(null);
  const [oturum, setOturum] = React.useState<SohbetOturum | null>(null);
  const [messages, setMessages] = React.useState<SohbetMesaj[]>([]);
  const [input, setInput] = React.useState('');
  const [streaming, setStreaming] = React.useState(false);
  const [hata, setHata] = React.useState(false);
  const [yeniden, setYeniden] = React.useState(0);

  const unsubRef = React.useRef<(() => void) | null>(null);
  const logRef = React.useRef<HTMLDivElement>(null);
  // Sunucu-otorite: oturum kimliği server'dan (onConnected) gelir; sonraki gönderilerde
  // bu id kullanılır (istemci kendi id'sini dayatmaz). Açılışta oturum.id ile doldurulur.
  const oturumIdRef = React.useRef<string>('');

  // --- Oturum yükle / yeni sohbet / retry → tam sıfırlama ---
  React.useEffect(() => {
    let alive = true;
    setHata(false);
    setOturum(null);
    setMessages([]);
    setStreaming(false);
    if (unsubRef.current) { unsubRef.current(); unsubRef.current = null; }

    // Persona ikincil: getMe hatası ekranı düşürmez (nav "Öğrenci"e düşer).
    // getSohbet birincil — reddi ErrorState'i tetikler.
    Promise.all([getMe().catch(() => null), getSohbet('direct')])
      .then(([me, o]) => {
        if (!alive) return;
        setPersona(me);
        setOturum(o);
        setMessages(o.mesajlar);
        oturumIdRef.current = o.id;
      })
      .catch(() => {
        if (alive) setHata(true);
      });

    return () => {
      alive = false;
      if (unsubRef.current) { unsubRef.current(); unsubRef.current = null; }
    };
  }, [yeniden]);

  // Yeni mesaj / token geldikçe akışı en alta kaydır (instant — hareket değil).
  React.useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const gonder = React.useCallback(
    (raw: string) => {
      const metin = raw.trim();
      if (!metin || streaming || oturum === null || hata) return;
      // Yeni mesaj → önceki akışı kapat (cleanup sözleşmesi).
      if (unsubRef.current) { unsubRef.current(); unsubRef.current = null; }

      const damga = Date.now();
      const pendingId = 'p-' + damga;
      setMessages((prev) => [
        ...prev,
        { id: 'u-' + damga, rol: 'ben', metin },
        { id: pendingId, rol: 'ai', metin: '', pending: true },
      ]);
      setInput('');
      setStreaming(true);

      unsubRef.current = streamSohbet(
        { oturumId: oturumIdRef.current, metin, teaching: 'direct', studentId },
        {
          // Sunucu bağlanınca gerçek session_id'yi benimse (sonraki gönderiler bunu kullanır).
          onConnected: (id) => { oturumIdRef.current = id; },
          onToken: (t) =>
            setMessages((prev) => prev.map((m) => (m.id === pendingId ? { ...m, metin: m.metin + t } : m))),
          onFinished: (fin) => {
            setMessages((prev) => prev.map((m) => (m.id === pendingId ? { ...fin, id: pendingId } : m)));
            setStreaming(false);
            unsubRef.current = null;
          },
          onError: () => {
            setHata(true);
            setStreaming(false);
            unsubRef.current = null;
          },
        },
      );
    },
    [streaming, oturum, hata, studentId],
  );

  const onKey = React.useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        gonder(input);
      }
    },
    [gonder, input],
  );

  const yeniSohbet = React.useCallback(() => setYeniden((n) => n + 1), []);
  const gonderilebilir = !!input.trim() && !streaming && oturum !== null && !hata;

  return (
    <KiroThemeProvider theme="paper">
      <div
        className="k-paper"
        style={{
          minHeight: '100vh', boxSizing: 'border-box', background: color.paper.bg,
          display: 'flex', fontFamily: font.sans, color: color.ink.primary,
          fontSize: 14, lineHeight: 1.5,
        }}
      >
        <style>{FOCUS_STYLE}</style>
        {!reduced && <style>{DOT_KEYFRAMES}</style>}

        <SideNav
          role="ogrenci"
          activeId="assistant"
          collapsed={dar}
          userName={persona?.ad ?? 'Öğrenci'}
          userSub={persona?.sinif ?? ''}
          onAssistant={() => undefined}
        />

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', minHeight: '100vh', boxSizing: 'border-box' }}>
          {/* ---- Topbar ---- */}
          <header
            style={{
              flexShrink: 0, minHeight: 66, boxSizing: 'border-box',
              display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', rowGap: 8,
              padding: '10px 26px', background: color.paper.card, borderBottom: `1px solid ${color.paper.border}`,
            }}
          >
            <span
              aria-hidden
              style={{
                width: 38, height: 38, flexShrink: 0, borderRadius: 11,
                background: 'linear-gradient(135deg,#C2452B,#FF6F5C)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', boxSizing: 'border-box',
              }}
            >
              <AsistanIkon />
            </span>
            <div style={{ minWidth: 0 }}>
              <h1 style={{ margin: 0, fontSize: 16.5, fontWeight: 800, letterSpacing: '-0.02em', color: color.ink.primary }}>
                AI Öğretmen Asistanı
              </h1>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: color.ink.muted, fontWeight: 600 }}>
                <span aria-hidden style={{ width: 7, height: 7, borderRadius: 999, background: color.semantic.success }} />
                Çevrimiçi · Türkçe · Qwen3-8B
              </div>
            </div>
            <div style={{ flex: 1 }} />
            <button
              type="button"
              className="k-chat-field"
              onClick={yeniSohbet}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 8, minHeight: 44, height: 44, padding: '0 16px',
                border: `1px solid ${color.paper.border}`, background: color.paper.card, borderRadius: 11,
                color: color.ink.secondary, fontFamily: font.sans, fontSize: 13.5, fontWeight: 700,
                cursor: 'pointer', boxSizing: 'border-box',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              Yeni sohbet
            </button>
          </header>

          {/* ---- Mesaj akışı ---- */}
          {hata ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '26px', boxSizing: 'border-box' }}>
              <div style={{ maxWidth: 480, width: '100%', boxSizing: 'border-box' }}>
                <ErrorState
                  serifTitle="Sohbet şu an yüklenemedi."
                  body="Sorun sende değil — bağlantı bir soluklandı, çalışman ve ilerlemen güvende. Hazır olduğunda yeniden dene."
                  onRetry={yeniSohbet}
                />
              </div>
            </div>
          ) : oturum === null ? (
            <div
              aria-busy="true"
              aria-label="Sohbet yükleniyor"
              style={{ flex: 1, overflowY: 'auto', padding: '26px 28px', boxSizing: 'border-box' }}
            >
              <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 18, boxSizing: 'border-box' }}>
                <Skeleton shape="row" />
                <Skeleton shape="card" delayMs={0} slowAfterMs={null} />
              </div>
            </div>
          ) : (
            <div
              ref={logRef}
              role="log"
              aria-live="polite"
              aria-relevant="additions text"
              aria-label="Sohbet akışı"
              style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '26px 28px', boxSizing: 'border-box' }}
            >
              <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 18, boxSizing: 'border-box' }}>
                {messages.map((m) => (
                  <ChatBubble
                    key={m.id}
                    role={m.rol === 'ben' ? 'me' : 'ai'}
                    tag={m.tag}
                    pending={m.pending}
                  >
                    {m.pending && m.metin === '' ? (
                      <>
                        <TypingDots reduced={reduced} />
                        {/* TypingDots aria-hidden — SR için görünmez "yazıyor" işareti (yanıt gelince kalkar) */}
                        <span style={srOnly}>KIRO yazıyor…</span>
                      </>
                    ) : (
                      m.metin
                    )}
                  </ChatBubble>
                ))}
              </div>
            </div>
          )}

          {/* ---- Composer ---- */}
          {!hata && (
            <div style={{ flexShrink: 0, borderTop: `1px solid ${color.paper.border}`, background: color.paper.bg, padding: '14px 28px 18px', boxSizing: 'border-box' }}>
              <div style={{ maxWidth: 760, margin: '0 auto', boxSizing: 'border-box' }}>
                <div
                  style={{
                    display: 'flex', alignItems: 'flex-end', gap: 10, background: color.paper.card,
                    border: `1px solid ${color.paper.borderStrong}`, borderRadius: 15, padding: '8px 8px 8px 14px', boxSizing: 'border-box',
                  }}
                >
                  <label htmlFor="k-chat-input" style={srOnly}>Soru yaz</label>
                  <textarea
                    id="k-chat-input"
                    className="k-chat-field"
                    rows={1}
                    value={input}
                    disabled={oturum === null}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKey}
                    placeholder="Bir soru sor ya da takıldığın konuyu yaz…"
                    aria-label="Soru yaz"
                    style={{
                      flex: 1, minWidth: 0, resize: 'none', maxHeight: 140, minHeight: 44,
                      border: 'none', background: 'transparent',
                      fontFamily: font.sans, fontSize: 14.5, lineHeight: 1.5, color: color.ink.primary,
                      padding: '11px 0', boxSizing: 'border-box',
                    }}
                  />
                  <button
                    type="button"
                    className="k-chat-field"
                    onClick={() => gonder(input)}
                    disabled={!gonderilebilir}
                    aria-label="Gönder"
                    style={{
                      width: 44, height: 44, flexShrink: 0, border: 'none', borderRadius: 11,
                      background: gonderilebilir ? color.dawn.coralCtaBg : color.paper.borderFaint,
                      color: gonderilebilir ? '#fff' : color.ink.faded3,
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                      cursor: gonderilebilir ? 'pointer' : 'default', boxSizing: 'border-box',
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                      <line x1="12" y1="19" x2="12" y2="5" /><polyline points="6 11 12 5 18 11" />
                    </svg>
                  </button>
                </div>
                <p style={{ margin: '9px 0 0', textAlign: 'center', fontSize: 11, color: color.ink.muted }}>
                  KIRO AI hata yapabilir — önemli sonuçları kontrol et.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default AISohbetPage;
