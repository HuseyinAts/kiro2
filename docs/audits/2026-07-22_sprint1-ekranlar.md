# Faz 3 · SPRINT1 — Giriş & Ödevlerim ekran portları (2026-07-22)

Kapsam: 2 ekran (Giriş & Kayıt · Ödevlerim). Kalibrasyon sprinti — ekran-port template + infra kurar.
Kaynak: SPRINT1_SPEC §B/§C, BREAKPOINT_SPEC §4, kiro-api.js, `screenshots/flow/{giris,odevlerim}.png`.

## DoD sonuçları

| Ekran | tema | axe | breakpoint (390→1440) | odak halkası | kanon | tsc | vitest |
|---|---|---|---|---|---|---|---|
| Giriş & Kayıt | **paper** | ✅ | ✅ 7/7 overflowX=0 · hit≥44 | ✅ `:focus-visible` | ✅ 0 | ✅ 0 | ✅ |
| Ödevlerim | **paper** | ✅ | ✅ 7/7 overflowX=0 · hit≥44 | ✅ | ✅ | ✅ | ✅ |

- **vitest:** 13 test PASS (Giriş 6 + Ödevlerim 6 + OrnekPage 1). RTL etkileşim + jest-axe her ekranda.
- **breakpoint:** `npm run kiro:breakpoints` → Playwright, storybook-static iframe'lerini 390/768/834/1024/1194/1280/1440'ta ölçer: **14/14 kontrol PASS** (overflowX=0 + hit≥44; `<a>` text linkleri §2 istisna).
  - Ödevlerim SideNav ≤1023px'te 64px ikon rayına çöker (matchMedia, jsdom-guard'lı) — 390'da overflowX=0.
- **Veri:** ekranlar `configureKiroApi` mock modda (Ödevlerim getMe+getAssignments; Giriş login/register sahte token → `tamam`). **MSW handler seti** `kiro/api/mswHandlers.ts` — kiro-api.js'ten türetildi (live/E2E yolu için; hata zarfı `{error:{code,message}}`).

## Tema kararı (netleşti)
SPRINT1_SPEC §B + Giris.dc.html **paper** diyor; ilk talimat "Giriş=dusk" idi → **AskUserQuestion ile paper onaylandı**.
Route-bazlı tema korundu (her iki ekran paper; ekran-türü, toggle YOK).

## Kopya sapmaları (BİREBİR kuralına istisna — ONAY BEKLER)
kanon-lint + SPRINT1_SPEC'in kendi "çıktıda absence-dili yok" kuralı, spec kopyasındaki iki dizeyi engelledi:
1. **Giriş e-posta hint'i:** `"Bu adres eksik görünüyor…"` → `"Bu adres yarım görünüyor — bir kez daha bakar mısın?"` (aynı nazik ton, forbidden kelime yok).
2. **Ödevlerim liste dipnotu:** `'…ödev "eksik" değil, bekliyor…'` → `"Geciken ödev kapanmaz — 'bekliyor'dur; kaldığın yerden devam etmen yeter. Sınıf sıralaması yayınlanmaz."`

## Diğer sapmalar
- **coral-CTA:** onaylı — CTA dolgusu `coralCtaBg #C2452B` + beyaz (parlak `#FF6F5C` yalnız aksan: şafak illüstrasyonu). Piksel-ref'te bilinçli fark.
- **Button `md` 40→44px:** SPRINT1_SPEC A1 "Button ≥44 hedef" + hit≥44 DoD gereği (Faz-2 bileşen refit; testler etkilenmedi, backstop bitmaps gitignore → yerel re-baseline).
- **Header "12-A":** öğrenci mock'unda sınıf-seksiyonu yok → mock-görünüm etiketi (live: teacher/classes ucu); öğretmen `odevler[].atayan`'dan.
- ProgressBar iz rengi bileşenin `s.skeleton`'ı (#ECE6DD) — SPEC #F0EAE1'e yakın, ihmal edilebilir fark.

## Kalibrasyon — kalan 40 ekran çarpanı
Bu sprintte **bir-seferlik infra** kuruldu: ekran-port template (self-theme-wrap + api-client mock),
MSW handler kalıbı, `kiro:breakpoints` Playwright denetçisi, tema-çelişki çözüm akışı, kopya-gotcha
(absence-dili) tespiti. Bu maliyet tekrar etmez.

Ekran-başı **marjinal** iş (infra sonrası): 1 ekran bileşeni (150–230 satır, kopya birebir) + 1 RTL/axe
testi + 1 story + doğrulama. İki ekran gözlemi:
- **Form-ağırlıklı ekran** (Giriş: state-machine + validation + a11y form) ≈ 1.0 birim.
- **Layout+veri+durum ekranı** (Ödevlerim: SideNav + kart + Skeleton/Empty/Error + responsive) ≈ 1.3 birim.

Kalan 42−2 = **40 ekran**. Kompozisyon karışık (basit paneller ~0.7, composite döngü ekranları ~1.5–2.0).
Kaba tahmin: **40 ekran ≈ 44–52 ekran-birimi** (P1 SideNav/TopBar/MasteryBadge + P2 QuestionCard seti
gibi paylaşılan composite'ler bir kez yapılınca sonraki ekranlar ucuzlar — envanter §E bağımlılık grafiği).
Öneri: S2'de (Kurtarma+Onboarding+Panel) yeniden ölç; composite-yoğun S3–S5'te çarpan yukarı revize edilir.

## Komutlar
- `npm run kiro:breakpoints` — breakpoint matrisi (Playwright)
- `npx vitest --run src/kiro/screens/` — ekran RTL+axe
- `node ../design/scripts/kanon-lint.mjs src/kiro` — kanon
