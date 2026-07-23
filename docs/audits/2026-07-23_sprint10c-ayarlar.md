# KIRO2 — Faz 3 · SPRINT10-C (Grup 8 BİTER — Ayarlar + davranış wiring)

**2026-07-23** — Ayarlar ✅ + yeni `ui/Switch` + `KullaniciAyar` store + **davranış wiring** → **Grup 8 (İş & dayanıklılık) TAMAM 7/7**. Rapor tamamlayıcı: `2026-07-23_sprint10b-billing.md` · `_sprint10a-is-dayaniklilik.md`.

## Kullanıcı Kararı (uygulandı — "Tek kaynak + TAM davranış")
`KullaniciAyar` (Zustand + localStorage persist) TEK KAYNAK: `dailyGoalMinutes` · 5 bildirim tercihi · `calmMode` · `hideRanking`. **Tam davranış wiring:**
- **calmMode → reduced-motion GLOBAL:** `useReducedMotion` (JS-motion/konfeti) + `theme.tsx` kök `<html>.k-calm` sınıfı → `tokens.css` `.k-calm` bloğu (CSS-@media ambient motion: Skeleton shimmer/keyframe de kısılır). İki katman → calmMode gerçekten global.
- **hideRanking → Lig:** çift-yönlü tek-kaynak (Lig toggle store'u yazar, Ayarlar toggle Lig'i etkiler); prop-override modunda no-op (Storybook/test kirlenmez).
- **calmMode → Arkadaş Serisi:** dürtme/nudge CTA gizlenir ("Sakin mod açık — dürtme kapalı"); tebrik korunur.

## Yeni bileşenler
- **`ui/Switch`** — `role=switch`+aria-checked+Space/Enter; AÇIK track coralCtaBg #C2452B / KAPALI görünür sınır #8F8577 (3.63:1, WCAG 1.4.11); transform-only thumb + RM-guard; opsiyonel `ariaDescribedby`; hit-target ≥44; story+test.
- **`kiro/lib/ayarStore.ts`** — Zustand persist (partialize veri), `useAyar` selector + `ayarDefaults` + `resetAyar()` (test izolasyonu).

## Ayarlar ekranı (öğrenci, paper, tema KİLİTLİ)
SideNav + profil-hero + **gömülü dusk abonelik-banner** (tokens.dusk.ink2, paper #6B6478 değil) + günlük hedef stepper + 5 bildirim Switch + Sakin mod/Sıralamayı gizle + Görünüm KİLİTLİ (SegmentedControl yok) + Hesap (E-posta·Şifre değiştir·Gizlilik&veri[KVKK]·Çıkış) + Vurgu rengi kilitli satır (canon-safe #C2452B swatch). "Kaydedildi" sonlu flash (role=status). client-persist (Faz4 server-sync).

## Adversarial (13 ajan, 4 boyut) — 8 doğrulandı / 1 phantom (0 P0/major)
- **faded2 AA tuzağı YOK** (S10-A/S10-B'de çıkmıştı; ajan öğrenmiş).
- **minör fix:** DC "Gizlilik&veri"(KVKK)+"Şifre değiştir"+"Vurgu rengi" satırları geri; Switch KAPALI track 1.44:1→3.63:1 (görünür sınır); Ayarlar Skeleton/Error/flash/stepper-sınır test kapsamı (+5 test).
- **nit fix:** calmMode gerçekten global değildi (CSS-ambient kaçırıyordu) → `.k-calm` kök-sınıf mekanizması (kararın tam karşılığı); sticky header box-sizing; AyarSatiri `aria-describedby`; Switch `<style>` tekilleştirildi (tokens.css'e taşındı); Lig override no-op.
- **phantom:** 5 bildirim etiketi DC'den yeniden yazıldı (kabul edilebilir).

## Kapı (otoriter, bağımsız)
kanon **0 ihlal** (14 uyarı pre-existing) · scoped tsc **0** · vitest **65 dosya / 423 test PASS** (383→423, +40) · **breakpoint 0 FAIL / 462** · axe temiz. Wiring commit'li ekranları (ConfettiDawn/Lig/Arkadaş Serisi/theme) BOZMADI.

**İlerleme: 38/42 ekran + QuestionCard + WeeklyActivityBars + VeliYonlendirmeKarti + ui/Switch + ayarStore. Grup 8 (İş & dayanıklılık) TAMAM (7/7).**
Sonraki: **Grup 9 AI & Çözüm (3 ekran: AI Sohbet · Sokratik AI · İnteraktif Çözüm)** + Auth kalıntı (İlk Hafta + route guard) → Faz 3 kapanış (42/42).
