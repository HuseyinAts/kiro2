// ============================================================================
// KIRO2 — Giriş & Kayıt (SPRINT1 · KIRO2 Giris.dc.html)
// Tema = PAPER (kanon: kapı/çalışma = açık; route-bazlı, toggle YOK).
// Kopya SPRINT1_SPEC §B'den BİREBİR — istisna: iki absence-dili içeren dize kanon-lint
// (ve spec'in kendi "çıktıda absence-dili yok" kuralı) gereği nötrlendi (onay bekler).
// Veri: api-client (mock modda sahte token → 'tamam' durumu).
// ============================================================================
import * as React from 'react';

import type { KiroRol } from '../types';
import { getRol, login as apiLogin, register as apiRegister } from '../api/api-client';
import { roleLanding } from '../lib/routeGuard';
import { color, font, radius, space } from '../tokens';
import { KiroThemeProvider } from '../ui/theme';
import { Button } from '../ui/Button';
import '../tokens/tokens.css';

type Mod = 'giris' | 'kayit';
type Durum = 'form' | '2fa' | 'tamam';

// Türkçe harf dahil — SPRINT1_SPEC §B kural satırı
const HARF = /[a-zA-ZçğıöşüÇĞİÖŞÜ]/;
const RAKAM = /[0-9]/;
const gecerliEposta = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());

const HINT = {
  // SPEC hint'i absence-dili içeriyordu → kanon gereği "yarım"
  eposta: 'Bu adres yarım görünüyor — bir kez daha bakar mısın?',
  sifreBos: 'Şifreni yazmayı unuttun gibi — acele yok.',
  ad: 'Adını da alalım — sana adınla seslenelim.',
  sifreZayif: 'Şifre en az 8 karakter, harf + rakam bir arada olsun.',
} as const;

const T = {
  ustLink: 'İlk kez mi? Önce değerini gör',
  girisBaslik: 'Tekrar hoş geldin.',
  girisAlt: 'Serin ve ilerlemen seni bekliyor — kaldığın yerden devam.',
  sifreLink: 'Şifreni mi unuttun?',
  girisCta: 'Devam edelim',
  girisDip: 'Girişte sıralama yok, alarm yok — sadece bugünkü planın.',
  kayitBaslik: 'Başlayalım.',
  kayitAlt: 'Hesap açmak 1 dakika. İstersen önce 6 soruluk seviye ölçümünü dene — kayıt sonrası da yapabilirsin.',
  kayitCta: 'Hesabımı aç',
  kayitDip: 'Verilerin sende kalır; sınıf arkadaşlarına hiçbir şey yayınlanmaz.',
  tamamGirisBaslik: 'İçerdesin.',
  tamamGirisAlt: 'Serin ve ilerlemen aynen yerinde. Bugünkü planın hazır.',
  tamamGirisCta: 'Panele geç',
  tamamKayitBaslik: 'Hesabın hazır.',
  tamamKayitAlt: 'Şimdi 6 soruluk seviye ölçümüyle sana özel planını çıkaralım — 2 dakika.',
  tamamKayitCta: 'Seviyeni ölçelim',
  sayfaAlti: 'Takıldıysan destek ekibine yaz — gerçek bir insan, okul saatlerinde ~10 dk içinde döner.',
} as const;

const PAGE_BG = 'radial-gradient(1200px 500px at 50% -10%, #FFF3EE 0%, #F1F2F6 60%)';

// Küçük şafak illüstrasyonu — dekoratif (aria-hidden), transform yok
function Sunrise() {
  return (
    <svg width="150" height="46" viewBox="0 0 150 46" fill="none" aria-hidden style={{ display: 'block', margin: '0 auto' }}>
      <line x1="8" y1="38" x2="55" y2="38" stroke="#E2DACE" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="95" y1="38" x2="142" y2="38" stroke="#E2DACE" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M58 38a17 17 0 0 1 34 0Z" fill="#FF8A5B" />
      <path d="M58 38a17 17 0 0 1 34 0" stroke="#FF6F5C" strokeWidth="1.6" fill="none" />
    </svg>
  );
}

interface AlanProps {
  id: string;
  label: string;
  tip?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  aciklama?: string; // aria-describedby hedefi
  sag?: React.ReactNode; // sağ üst link (Şifreni mi unuttun?)
  ic?: React.ReactNode; // input içi sağ (Göster butonu)
}

function Alan({ id, label, tip = 'text', value, onChange, placeholder, aciklama, sag, ic }: AlanProps) {
  return (
    <div style={{ marginTop: space[4] }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 6 }}>
        <label htmlFor={id} style={{ fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, color: color.ink.secondary }}>
          {label}
        </label>
        {sag}
      </div>
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          id={id}
          type={tip}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          aria-describedby={aciklama}
          style={{
            width: '100%', minHeight: 48, boxSizing: 'border-box',
            padding: ic ? '0 96px 0 14px' : '0 14px',
            borderRadius: radius.input, border: `1px solid ${color.paper.border}`,
            background: color.paper.card, color: color.ink.primary,
            fontFamily: font.sans, fontSize: 14, outlineOffset: 2,
          }}
        />
        {ic}
      </div>
    </div>
  );
}

/** GirisPage props — WIRING (ADDITIVE): giriş-sonrası rol-landing köprüsü.
 *  onLanding: 'tamam' CTA'sında çağrılır (prop-enjekte; Faz 4 router'a bağlar) —
 *    giriş → roleLanding(rol); kayıt → /onboarding (6 soruluk seviye ölçüm).
 *    Verilmezse eski davranış (no-op) korunur.
 *  rol: verilirse landing kaynağı; verilmezse giriş BAŞARISINDAN sonra getRol()
 *    ile yüklenir (kimliksiz mount'ta ÇEKİLMEZ; fallback 'ogrenci').
 *  onLogin/onVerify2fa/onRegister (F4-S1): gerçek authStore enjeksiyonu (prop-enjekte).
 *    Verilmezse kiro api-client (mock/live) fallback — test/story izolasyonu korunur.
 *    Çağıran {eposta,sifre} → gerçek {email,password}'e map eder. */
export interface GirisPageProps {
  onLanding?: (rota: string) => void;
  rol?: KiroRol;
  onLogin?: (creds: { eposta: string; sifre: string }) => Promise<boolean | '2fa_required'>;
  onVerify2fa?: (args: { eposta: string; sifre: string; kod: string }) => Promise<boolean>;
  onRegister?: (creds: { eposta: string; sifre: string; ad: string }) => void | Promise<void>;
}

export function GirisPage({ onLanding, rol: rolProp, onLogin, onVerify2fa, onRegister }: GirisPageProps = {}): React.ReactElement {
  const [mod, setMod] = React.useState<Mod>('giris');
  const [durum, setDurum] = React.useState<Durum>('form');
  const [ad, setAd] = React.useState('');
  const [eposta, setEposta] = React.useState('');
  const [sifre, setSifre] = React.useState('');
  const [goster, setGoster] = React.useState(false);
  const [hint, setHint] = React.useState<string | null>(null);
  const [gonderiliyor, setGonderiliyor] = React.useState(false);
  const [yuklenenRol, setYuklenenRol] = React.useState<KiroRol>('ogrenci');
  const [kod, setKod] = React.useState(''); // F4-S1: 2FA TOTP kodu

  // Rol = giriş-sonrası landing kaynağı (Persona'dan AYRI). Prop verilirse onu kullan;
  // yoksa giriş BAŞARISINDAN sonra getRol() ile yüklenir (gonder()) — kimliksiz mount'ta
  // ÇEKİLMEZ (live'da pre-auth GET /me/rol 401 önlenir); hata/mock-yoksa fallback 'ogrenci'.
  const rol = rolProp ?? yuklenenRol;

  const modaGec = (m: Mod) => {
    setMod(m);
    setHint(null);
  };

  const dogrula = (): string | null => {
    if (mod === 'kayit' && ad.trim().length < 2) return HINT.ad;
    if (!gecerliEposta(eposta)) return HINT.eposta;
    if (mod === 'giris' && sifre.length === 0) return HINT.sifreBos;
    if (mod === 'kayit' && (sifre.length < 8 || !HARF.test(sifre) || !RAKAM.test(sifre))) return HINT.sifreZayif;
    return null;
  };

  const gonder = async () => {
    const h = dogrula();
    setHint(h);
    if (h) return;
    setGonderiliyor(true);
    try {
      if (mod === 'kayit') {
        // Kayıt: gerçek /register akışına delege et (varsa); yoksa kiro api-client fallback.
        if (onRegister) { await onRegister({ eposta, sifre, ad }); return; }
        await apiRegister({ eposta, sifre, ad });
      } else if (onLogin) {
        // Gerçek auth (cookie). 2FA dalı ve hatalı-kimlik ayrı ele alınır.
        const r = await onLogin({ eposta, sifre });
        if (r === '2fa_required') { setHint(null); setDurum('2fa'); return; }
        if (r === false) { setHint('E-posta ya da şifre eşleşmedi — bir daha dener misin?'); return; }
      } else {
        await apiLogin({ eposta, sifre });
      }
      // Kimlik OLUŞTUKTAN sonra rolü çek (sunucu-otorite; pre-auth çağrı YOK). Gerçek auth'ta
      // (onLogin) rol store'dan gelir → getRol atlanır (/me/rol 404 gürültüsü önlenir).
      if (!onLogin && rolProp == null) void getRol().then(setYuklenenRol).catch(() => undefined);
      setDurum('tamam');
    } catch {
      // Sunucu hatası → aynı amber hint (sorun sende değil tonu; alarm-kırmızısı YOK)
      setHint('Koç şu an toparlanıyor — birazdan yeniden dene, çalışman güvende.');
    } finally {
      setGonderiliyor(false);
    }
  };

  // F4-S1: 2FA doğrulama adımı (TOTP). onVerify2fa prop-enjekte; başarıda 'tamam'a geçer.
  const dogrula2fa = async () => {
    if (!onVerify2fa) return;
    if (kod.trim().length < 6) { setHint('6 haneli kodu tam gir — acele yok.'); return; }
    setGonderiliyor(true);
    try {
      const ok = await onVerify2fa({ eposta, sifre, kod: kod.trim() });
      if (ok) { setHint(null); setDurum('tamam'); }
      else setHint('Kod doğrulanmadı — tekrar dener misin?');
    } catch {
      setHint('Doğrulama şu an yapılamadı — birazdan yeniden dene.');
    } finally {
      setGonderiliyor(false);
    }
  };

  const s = { color: color.ink };
  const kartStil: React.CSSProperties = {
    width: '100%', maxWidth: 460, margin: '0 auto', boxSizing: 'border-box',
    background: color.paper.card, borderRadius: radius.cardLg,
    border: `1px solid ${color.paper.border}`, boxShadow: '0 20px 50px -24px rgba(42,36,51,0.3)',
    padding: '26px 28px 30px',
  };

  const tamamMi = durum === 'tamam';

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: PAGE_BG, fontFamily: font.sans, color: s.color.primary }}>
        {/* Üst bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div aria-hidden style={{ width: 32, height: 32, borderRadius: 9, background: color.dawn.coralCtaBg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5" /><path d="M3 12l9 5 9-5" />
              </svg>
            </div>
            <span style={{ fontWeight: 800, fontSize: 17, letterSpacing: '-0.02em' }}>
              KIRO<span style={{ color: color.dawn.coralTextOnLight }}>2</span>
            </span>
          </div>
          <a href="/onboarding" style={{ fontSize: 13, fontWeight: 700, color: color.dawn.coralTextOnLight, textDecoration: 'none' }}>
            {T.ustLink}
          </a>
        </div>

        <div style={{ padding: '0 24px 48px' }}>
          <div style={{ marginTop: 8, marginBottom: 18 }}><Sunrise /></div>

          <div style={kartStil}>
            {durum === 'form' && (
              <div role="radiogroup" aria-label="Giriş ya da Kayıt" style={{ display: 'flex', gap: 4, background: color.paper.subtle, borderRadius: radius.button, padding: 4, marginBottom: 4 }}>
                {(['giris', 'kayit'] as const).map((m) => {
                  const aktif = mod === m;
                  return (
                    <button
                      key={m}
                      type="button"
                      role="radio"
                      aria-checked={aktif}
                      onClick={() => modaGec(m)}
                      style={{
                        flex: 1, minHeight: 44, border: 'none', cursor: 'pointer',
                        borderRadius: radius.input, fontFamily: font.sans, fontSize: 14, fontWeight: 700,
                        background: aktif ? color.paper.card : 'transparent',
                        color: aktif ? color.ink.primary : color.ink.muted,
                        boxShadow: aktif ? '0 1px 2px rgba(16,24,40,0.04)' : undefined,
                      }}
                    >
                      {m === 'giris' ? 'Giriş' : 'Kayıt'}
                    </button>
                  );
                })}
              </div>
            )}

            {durum === '2fa' ? (
              <div style={{ paddingTop: space[4] }}>
                <h1 style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 30, fontWeight: 400, margin: 0, color: color.ink.primary }}>
                  İki adımlı doğrulama
                </h1>
                <p style={{ marginTop: 10, fontSize: 14.5, lineHeight: 1.6, color: color.ink.secondary }}>
                  Doğrulama uygulamandaki 6 haneli kodu gir — hesabın güvende kalsın.
                </p>
                <Alan
                  id="giris-2fa"
                  label="Doğrulama kodu"
                  value={kod}
                  onChange={setKod}
                  placeholder="123456"
                  aciklama={hint ? 'giris-hint' : undefined}
                />
                {hint && (
                  <div id="giris-hint" role="status" aria-live="polite" style={{ marginTop: space[4], padding: '10px 13px', borderRadius: radius.chip, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, color: color.semantic.riskTextOnLight, fontSize: 13, lineHeight: 1.5 }}>
                    {hint}
                  </div>
                )}
                <div style={{ marginTop: space[5] }}>
                  <Button variant="primary" size="lg" disabled={gonderiliyor} onClick={() => void dogrula2fa()}>
                    Doğrula
                  </Button>
                </div>
              </div>
            ) : tamamMi ? (
              <div style={{ paddingTop: space[4] }}>
                <h1 style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 30, fontWeight: 400, margin: 0, color: color.ink.primary }}>
                  {mod === 'giris' ? T.tamamGirisBaslik : T.tamamKayitBaslik}
                </h1>
                <p style={{ marginTop: 10, fontSize: 14.5, lineHeight: 1.6, color: color.ink.secondary }}>
                  {mod === 'giris' ? T.tamamGirisAlt : T.tamamKayitAlt}
                </p>
                <div style={{ marginTop: space[5] }}>
                  <Button variant="primary" size="lg" onClick={() => onLanding?.(mod === 'kayit' ? '/onboarding' : roleLanding(rol))}>
                    {mod === 'giris' ? T.tamamGirisCta : T.tamamKayitCta}
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); void gonder(); }} noValidate>
                <h1 style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 30, fontWeight: 400, margin: '18px 0 0', color: color.ink.primary }}>
                  {mod === 'giris' ? T.girisBaslik : T.kayitBaslik}
                </h1>
                <p style={{ marginTop: 8, fontSize: 14, lineHeight: 1.55, color: color.ink.secondary }}>
                  {mod === 'giris' ? T.girisAlt : T.kayitAlt}
                </p>

                {mod === 'kayit' && (
                  <Alan id="giris-ad" label="Adın" value={ad} onChange={setAd} placeholder="Adın" />
                )}

                <Alan
                  id="giris-eposta"
                  label="E-posta adresin"
                  tip="email"
                  value={eposta}
                  onChange={setEposta}
                  placeholder="ornek@eposta.com"
                  aciklama={hint ? 'giris-hint' : undefined}
                />

                <Alan
                  id="giris-sifre"
                  label="Şifren"
                  tip={goster ? 'text' : 'password'}
                  value={sifre}
                  onChange={setSifre}
                  aciklama={hint ? 'giris-hint' : undefined}
                  sag={
                    mod === 'giris' ? (
                      <a href="/hesap-kurtarma" style={{ fontSize: 12.5, fontWeight: 700, color: color.dawn.coralTextOnLight, textDecoration: 'none' }}>
                        {T.sifreLink}
                      </a>
                    ) : undefined
                  }
                  ic={
                    <button
                      type="button"
                      onClick={() => setGoster((g) => !g)}
                      aria-pressed={goster}
                      aria-label={goster ? 'Şifreyi gizle' : 'Şifreyi göster'}
                      style={{
                        position: 'absolute', right: 6, minHeight: 44, padding: '0 12px',
                        border: `1px solid ${color.paper.border}`, borderRadius: 8, background: color.paper.card,
                        color: color.ink.secondary, fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, cursor: 'pointer',
                      }}
                    >
                      {goster ? 'Gizle' : 'Göster'}
                    </button>
                  }
                />

                {hint && (
                  <div
                    id="giris-hint"
                    role="status"
                    aria-live="polite"
                    style={{
                      marginTop: space[4], padding: '10px 13px', borderRadius: radius.chip,
                      background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`,
                      color: color.semantic.riskTextOnLight, fontSize: 13, lineHeight: 1.5,
                    }}
                  >
                    {hint}
                  </div>
                )}

                <div style={{ marginTop: space[5] }}>
                  <Button variant="primary" size="lg" disabled={gonderiliyor} onClick={() => void gonder()}>
                    {mod === 'giris' ? T.girisCta : T.kayitCta}
                  </Button>
                </div>

                <p style={{ marginTop: space[4], fontSize: 12.5, lineHeight: 1.5, color: color.ink.muted }}>
                  {mod === 'giris' ? T.girisDip : T.kayitDip}
                </p>
              </form>
            )}
          </div>

          <p style={{ maxWidth: 460, margin: '18px auto 0', textAlign: 'center', fontSize: 12.5, lineHeight: 1.55, color: color.ink.muted }}>
            {T.sayfaAlti}
          </p>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default GirisPage;
