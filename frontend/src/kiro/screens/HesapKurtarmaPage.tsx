// ============================================================================
// KIRO2 — Hesap Kurtarma (SPRINT2 · KIRO2 Hesap Kurtarma.dc.html)
// Tema = PAPER (Giriş ile aynı warm-radial + kart). Durum: eposta→kod→sifre→tamam.
// Kopya SPRINT2_SPEC §B'den BİREBİR — iki istisna, ikisi de gerçeğe uydurma:
//   1) e-posta hint absence-dili → "yarım" (kanon)
//   2) son adım CTA "Panele dön" → "Girişe dön": sıfırlamadan sonra oturum
//      AÇILMIYOR, kullanıcı panele değil girişe düşüyor. Ekran gerçekte
//      olmayan bir şeyi vaat etmemeli.
//
// F4 — CANLI. Önceden üç adım da MOCK'tu: kodu istemcide doğruluyor (kod.length
// === 6), 3. adımda sunucuya HİÇ gitmiyor, "Panele dön" `() => undefined` idi.
// Yani ekran çalışıyor görünüp şifreyi hiç değiştirmiyordu.
// Sözleşme: recover → verifyResetCode(token) → resetPassword.
// ============================================================================
import * as React from 'react';

import {
  recover as apiRecover,
  resetPassword as apiResetPassword,
  verifyResetCode as apiVerifyResetCode,
} from '../api/api-client';
import { color, font, radius, space } from '../tokens';
import { KiroThemeProvider } from '../ui/theme';
import { Button } from '../ui/Button';
import '../tokens/tokens.css';

type Adim = 'eposta' | 'kod' | 'sifre' | 'tamam';

// Şifre kuralları SUNUCUYLA BİREBİR (backend/api/auth.py `_validate_password`).
// Önceden ekran 3 kural gösteriyordu (>=8 · harf+rakam · tahmini zor) ama sunucu
// 5 uyguluyor; `abcd1234` üç tiki de yeşil yapıp reddediliyordu — hem de kullanıcı
// e-postayı alıp kodu girdikten SONRA. Özel karakter kümesi sunucudaki listenin
// AYNISI: değiştirirsen iki tarafı birlikte değiştir.
const KUCUK_HARF = /[a-zçğıöşü]/;
const BUYUK_HARF = /[A-ZÇĞİÖŞÜ]/;
const RAKAM = /[0-9]/;
const OZEL_KARAKTER = /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/;
const gecerliEposta = (e: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
const zayifOnek = /^(12345678|password|parola|sifre|şifre|1234|qwerty|abcabc)/i;

const PAGE_BG = 'radial-gradient(1200px 500px at 50% -10%, #FFF3EE 0%, #F1F2F6 60%)';

function maskele(e: string): string {
  const at = e.indexOf('@');
  if (at < 0) return e;
  const ad = e.slice(0, at);
  const alan = e.slice(at);
  const bas = ad.length >= 2 ? ad.slice(0, 2) : ad;
  return `${bas}•••${alan}`;
}

const T = {
  ustLink: 'Girişe dön',
  e1Baslik: 'Hesabını birlikte açalım.',
  e1Alt: 'Şifre unutmak da çalışmanın bir parçası. E-postanı yaz, sana 6 haneli bir kod gönderelim.',
  e1Cta: 'Kod gönder',
  e1Dip: 'Adresini hatırlamıyorsan okul e-postanı da deneyebilirsin.',
  k2Baslik: 'Kod yolda.',
  k2Cta: 'Doğrula',
  k2Dip: 'Kod gelmediyse spam klasörüne bakmak genelde yeter.',
  s3Baslik: 'Yeni şifreni seç.',
  s3Alt: 'Hatırlaması kolay, tahmin etmesi zor bir şey iyi gider.',
  s3Cta: 'Şifreyi güncelle',
  t4Baslik: 'Hazırsın.',
  // "kaldığın yerden devam" korunuyor; ama giriş yapılmadığı için CTA panele
  // değil GİRİŞE götürür — kopya bunu doğru söylemeli.
  t4Alt: 'Şifren güncellendi. Serin ve ilerlemen aynen yerinde — yeni şifrenle gir, kaldığın yerden devam.',
  t4Cta: 'Girişe dön',
  sayfaAlti: 'Takıldıysan destek ekibine yaz — gerçek bir insan, okul saatlerinde ~10 dk içinde döner.',
} as const;

const HINT = {
  eposta: 'Bu adres yarım görünüyor — bir kez daha bakar mısın?', // SPEC absence-dili → kanon "yarım"
  kod: 'Kod 6 haneli olmalı — acele yok.',
  // Sunucu "kod yanlış" ile "süre doldu"yu AYIRT ETMEZ (ayırmak saldırgana
  // bilgi verirdi), ekran da ayırmıyor. Yeni kod isteme yolu hemen altında.
  kodGecersiz: 'Bu kod geçmiyor — süresi dolmuş olabilir. Yeni kod isteyebilirsin.',
  sifirlanamadi: 'Şifre güncellenemedi. Yeni bir kod isteyip tekrar dener misin?',
  ag: 'Bağlantı kurulamadı — birazdan tekrar dener misin?',
} as const;

function Kural({ ok, children }: { ok: boolean; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: ok ? '#17936B' : '#9A93A5' }}>
      <span aria-hidden style={{ width: 16, height: 16, borderRadius: 999, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: ok ? '#1FB683' : '#D9D2C7' }}>
        {ok ? (
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
        ) : null}
      </span>
      {children}
    </div>
  );
}

export function HesapKurtarmaPage(): React.ReactElement {
  const [adim, setAdim] = React.useState<Adim>('eposta');
  const [eposta, setEposta] = React.useState('');
  const [kod, setKod] = React.useState('');
  const [sifre, setSifre] = React.useState('');
  const [goster, setGoster] = React.useState(false);
  const [hint, setHint] = React.useState<string | null>(null);
  const [yeniden, setYeniden] = React.useState(false);
  const [token, setToken] = React.useState<string | null>(null);
  const [mesgul, setMesgul] = React.useState(false);
  const baslikRef = React.useRef<HTMLHeadingElement>(null);

  // Adım değişince başlığa programatik odak (SR akışı — Erişilebilirlik satırları)
  React.useEffect(() => {
    baslikRef.current?.focus();
  }, [adim]);

  const uzunKarakter = sifre.length >= 8;
  const harfCesidi = KUCUK_HARF.test(sifre) && BUYUK_HARF.test(sifre);
  const rakamOzel = RAKAM.test(sifre) && OZEL_KARAKTER.test(sifre);
  const tahminZor = sifre.length >= 8 && !zayifOnek.test(sifre);
  const sifreGecerli = uzunKarakter && harfCesidi && rakamOzel && tahminZor;

  const kodGonder = async () => {
    if (!gecerliEposta(eposta)) { setHint(HINT.eposta); return; }
    setHint(null);
    setMesgul(true);
    try {
      await apiRecover(eposta);
      setAdim('kod');
    } catch {
      // Sunucu adresin kayıtlı olup olmadığını ASLA söylemez; buraya ancak
      // ağ/sunucu hatasıyla düşülür. Adım ilerletilmez.
      setHint(HINT.ag);
    } finally {
      setMesgul(false);
    }
  };

  const dogrula = async () => {
    const temiz = kod.replace(/\D/g, '');
    if (temiz.length !== 6) { setHint(HINT.kod); return; }
    setHint(null);
    setMesgul(true);
    try {
      const { ok, token: yeniToken } = await apiVerifyResetCode(eposta, temiz);
      if (!ok || !yeniToken) { setHint(HINT.kodGecersiz); return; }
      setToken(yeniToken);
      setAdim('sifre');
    } catch {
      setHint(HINT.ag);
    } finally {
      setMesgul(false);
    }
  };

  const sifreGuncelle = async () => {
    if (!sifreGecerli || !token) return;
    setHint(null);
    setMesgul(true);
    try {
      const { ok, mesaj } = await apiResetPassword(token, sifre);
      if (!ok) { setHint(mesaj || HINT.sifirlanamadi); return; }
      setAdim('tamam');
    } catch {
      setHint(HINT.ag);
    } finally {
      setMesgul(false);
    }
  };

  const adresiDegistir = () => {
    setKod(''); setYeniden(false); setHint(null); setToken(null); setAdim('eposta');
  };

  const kodYeniden = async () => {
    setMesgul(true);
    try { await apiRecover(eposta); setYeniden(true); }
    catch { setHint(HINT.ag); }
    finally { setMesgul(false); }
  };

  const girise = () => { window.location.href = '/login'; };

  const kartStil: React.CSSProperties = {
    width: '100%', maxWidth: 460, margin: '0 auto', boxSizing: 'border-box',
    background: color.paper.card, borderRadius: radius.cardLg, border: `1px solid ${color.paper.border}`,
    boxShadow: '0 20px 50px -24px rgba(42,36,51,0.3)', padding: '26px 28px 30px',
  };
  const inputStil: React.CSSProperties = {
    width: '100%', minHeight: 48, boxSizing: 'border-box', padding: '0 14px',
    borderRadius: radius.input, border: `1px solid ${color.paper.border}`, background: color.paper.card,
    color: color.ink.primary, fontFamily: font.sans, fontSize: 14, outlineOffset: 2,
  };
  const linkStil: React.CSSProperties = { fontSize: 12.5, fontWeight: 700, color: color.dawn.coralTextOnLight, textDecoration: 'none', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: font.sans };

  const adimNo = adim === 'eposta' ? 1 : adim === 'kod' ? 2 : 3;

  return (
    <KiroThemeProvider theme="paper">
      <div className="k-paper" style={{ minHeight: '100vh', background: PAGE_BG, fontFamily: font.sans, color: color.ink.primary }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', maxWidth: 1100, margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div aria-hidden style={{ width: 32, height: 32, borderRadius: 9, background: color.dawn.coralCtaBg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3 3 8l9 5 9-5-9-5Z" /><path d="M3 16l9 5 9-5" /><path d="M3 12l9 5 9-5" /></svg>
            </div>
            <span style={{ fontWeight: 800, fontSize: 17, letterSpacing: '-0.02em' }}>KIRO<span style={{ color: color.dawn.coralTextOnLight }}>2</span></span>
          </div>
          {/* /giris kayıtlı bir rota DEĞİL (App.tsx'te yalnız /login var) — ölü linkti. */}
          <a href="/login" style={{ ...linkStil }}>{T.ustLink}</a>
        </div>

        <div style={{ padding: '8px 24px 48px' }}>
          <div style={kartStil}>
            {adim !== 'tamam' && (
              <div aria-live="polite" style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: '#9A93A5' }}>
                Adım {adimNo} / 3
              </div>
            )}

            {adim === 'tamam' ? (
              <div style={{ textAlign: 'center', paddingTop: space[3] }}>
                <div aria-hidden style={{ width: 58, height: 58, margin: '0 auto 14px', borderRadius: 999, background: '#E4F7F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#17936B" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
                </div>
                <h1 ref={baslikRef} tabIndex={-1} style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 30, fontWeight: 400, margin: 0, outline: 'none' }}>{T.t4Baslik}</h1>
                <p style={{ marginTop: 10, fontSize: 14.5, lineHeight: 1.6, color: color.ink.secondary }}>{T.t4Alt}</p>
                <div style={{ marginTop: space[5] }}><Button variant="primary" size="lg" onClick={girise}>{T.t4Cta}</Button></div>
              </div>
            ) : (
              <>
                <h1 ref={baslikRef} tabIndex={-1} style={{ fontFamily: font.serif, fontStyle: 'italic', fontSize: 30, fontWeight: 400, margin: '14px 0 0', outline: 'none' }}>
                  {adim === 'eposta' ? T.e1Baslik : adim === 'kod' ? T.k2Baslik : T.s3Baslik}
                </h1>

                {adim === 'eposta' && (
                  <>
                    <p style={{ marginTop: 8, fontSize: 14, lineHeight: 1.55, color: color.ink.secondary }}>{T.e1Alt}</p>
                    <div style={{ marginTop: space[4] }}>
                      <label htmlFor="hk-eposta" style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 6 }}>E-posta adresin</label>
                      <input id="hk-eposta" type="email" value={eposta} onChange={(e) => setEposta(e.target.value)} placeholder="ornek@eposta.com" aria-describedby={hint ? 'hk-hint' : undefined} style={inputStil} />
                    </div>
                  </>
                )}

                {adim === 'kod' && (
                  <>
                    <p style={{ marginTop: 8, fontSize: 14, lineHeight: 1.55, color: color.ink.secondary }}>
                      <strong style={{ color: color.ink.primary }}>{maskele(eposta)}</strong> adresine 6 haneli bir kod gönderdik. Gelmesi bir dakikayı bulabilir.
                    </p>
                    <div style={{ marginTop: space[4] }}>
                      <label htmlFor="hk-kod" style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 6 }}>Doğrulama kodu</label>
                      <input
                        id="hk-kod" inputMode="numeric" autoComplete="one-time-code" value={kod}
                        onChange={(e) => setKod(e.target.value.replace(/\D/g, '').slice(0, 6))}
                        aria-describedby={hint ? 'hk-hint' : undefined}
                        style={{ ...inputStil, textAlign: 'center', fontSize: 24, fontWeight: 800, letterSpacing: '0.42em', fontVariantNumeric: 'tabular-nums' }}
                      />
                    </div>
                    <div style={{ marginTop: 12, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                      <button type="button" onClick={adresiDegistir} style={linkStil}>Adresi değiştir</button>
                      <button type="button" onClick={kodYeniden} style={{ ...linkStil, color: yeniden ? '#17936B' : color.dawn.coralTextOnLight }}>
                        {yeniden ? 'Gönderildi — gelen kutuna bak' : 'Kodu yeniden gönder'}
                      </button>
                    </div>
                  </>
                )}

                {adim === 'sifre' && (
                  <>
                    <p style={{ marginTop: 8, fontSize: 14, lineHeight: 1.55, color: color.ink.secondary }}>{T.s3Alt}</p>
                    <div style={{ marginTop: space[4] }}>
                      <label htmlFor="hk-sifre" style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: color.ink.secondary, marginBottom: 6 }}>Yeni şifren</label>
                      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                        <input id="hk-sifre" type={goster ? 'text' : 'password'} value={sifre} onChange={(e) => setSifre(e.target.value)} style={{ ...inputStil, padding: '0 96px 0 14px' }} />
                        <button type="button" onClick={() => setGoster((g) => !g)} aria-pressed={goster} aria-label={goster ? 'Şifreyi gizle' : 'Şifreyi göster'} style={{ position: 'absolute', right: 6, minHeight: 44, padding: '0 12px', border: `1px solid ${color.paper.border}`, borderRadius: 8, background: color.paper.card, color: color.ink.secondary, fontFamily: font.sans, fontSize: 12.5, fontWeight: 700, cursor: 'pointer' }}>
                          {goster ? 'Gizle' : 'Göster'}
                        </button>
                      </div>
                    </div>
                    <div aria-live="polite" style={{ marginTop: 12, display: 'grid', gap: 7 }}>
                      <Kural ok={uzunKarakter}>En az 8 karakter</Kural>
                      <Kural ok={harfCesidi}>Büyük ve küçük harf bir arada</Kural>
                      <Kural ok={rakamOzel}>Rakam ve özel karakter (! ? * # gibi)</Kural>
                      <Kural ok={tahminZor}>Tahmini zor</Kural>
                    </div>
                  </>
                )}

                {hint && (
                  <div id="hk-hint" role="status" aria-live="polite" style={{ marginTop: space[4], padding: '10px 13px', borderRadius: radius.chip, background: color.semantic.riskBgSoft, border: `1px solid ${color.semantic.riskBorderSoft}`, color: color.semantic.riskTextOnLight, fontSize: 13, lineHeight: 1.5 }}>
                    {hint}
                  </div>
                )}

                <div style={{ marginTop: space[5] }}>
                  <Button
                    variant="primary"
                    size="lg"
                    disabled={mesgul || (adim === 'sifre' && !sifreGecerli)}
                    onClick={() => (adim === 'eposta' ? void kodGonder() : adim === 'kod' ? void dogrula() : void sifreGuncelle())}
                  >
                    {adim === 'eposta' ? T.e1Cta : adim === 'kod' ? T.k2Cta : T.s3Cta}
                  </Button>
                </div>

                {adim === 'eposta' && <p style={{ marginTop: space[4], fontSize: 12.5, lineHeight: 1.5, color: color.ink.muted }}>{T.e1Dip}</p>}
                {adim === 'kod' && <p style={{ marginTop: space[4], fontSize: 12.5, lineHeight: 1.5, color: color.ink.muted }}>{T.k2Dip}</p>}
              </>
            )}
          </div>

          <p style={{ maxWidth: 460, margin: '18px auto 0', textAlign: 'center', fontSize: 12.5, lineHeight: 1.55, color: color.ink.muted }}>{T.sayfaAlti}</p>
        </div>
      </div>
    </KiroThemeProvider>
  );
}

export default HesapKurtarmaPage;
