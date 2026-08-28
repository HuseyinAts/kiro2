# KIRO2 — Claude Code Uygulama Talimatı (v2 · 2026-07-22)

> `HuseyinAts/kiro2` reposunda çalışan geliştirici/Claude Code için giriş noktası.
> Bu klasörü (`design_handoff_kiro2/`) repoya **`design/`** olarak kopyala ve bu talimatı izle.
> Repo-temelli dosya-dosya iş planı: **`ENTEGRASYON_PLANI.md`** — bu talimatla birlikte okunur;
> çelişkide ENTEGRASYON_PLANI (daha yeni, repo keşfine dayalı) kazanır.

## 0. Bu paket nedir, ne değildir
- İçerideki `.dc.html` prototipleri ve bu klasör **tasarım referansıdır** — üretim kodu değildir,
  kopyala-yapıştır edilmez. Görev: bu tasarımları hedef repo ortamında (Vite + React 18 + TS)
  **yeniden inşa etmek**.
- Fidelite: **hi-fi**. Renk, tipografi, boşluk ve kopya METİNLERİ birebir taşınır — kopya yeniden
  yazılmaz (tümü kullanıcı onaylı; değişiklik = yeni onay). Piksel referansları:
  `KIRO Bilesenler.dc.html` (bileşen) · `screenshots/flow/` **22 PNG** (ekran).
- Kapsam: **43 ekran** (42 port + 1 MVP-dışı bekleme: Çözüm Paylaş). İlerleme takibi
  `PORT_DURUM.md` — her PR ilgili satırın DoD kutularını işaretler.
  `Tasarim Dili` (public sayfa) ve `Eposta Bildirim` (kopya sistemi spec'i) PORT EDİLMEZ — referans yüzeyleri.
- Otoriter sıra: `CLAUDE.md` (kanon) → `tokens.ts`/`tokens.css` → `openapi.yaml` + `types.ts` +
  `api-client.ts` + `kiro-api.js` (veri/davranış) → `ui-starter/` (20 bileşen) → ekran DC'leri →
  sprint spec'leri (`SPRINT1..12_SPEC.md`).

## 1. Hedef ortam (ADR-000)
- **Yeni monorepo YOK.** Mevcut `frontend/` (Vite + React 18 + TS) içinde çalış.
- Yerleşim:
  - `frontend/src/kiro/tokens/`  ← tokens.ts + tokens.css (birebir)
  - `frontend/src/kiro/types/`   ← types.ts
  - `frontend/src/kiro/api/`     ← api-client.ts + kiro-data.json
  - `frontend/src/kiro/ui/`      ← ui-starter/ (20 bileşen)
  - `frontend/src/kiro/screens/` ← Faz 3 ekran portları (route-bazlı)
- **Yeni KIRO ekranlarında YASAK bağımlılıklar:** MUI, @mui/icons-material, lucide-react, emotion,
  react-hot-toast (kendi Callout/ErrorState'imiz var). İkonlar bespoke inline SVG
  (`ui/SideNav.tsx → NAV_ICONS` örnek desen). Emoji hiçbir yüzeyde yok.
- `react-query` v3 → `@tanstack/react-query` v5 yükselt (ADR-006).
- ADR.md'deki kararları repoya `docs/adr/` olarak taşı (durum: kabul). ⚠ ADR-001 güncellemesi:
  kendi JWT'miz, **cookie-taşımalı** (ENTEGRASYON_PLANI kararı) — openapi güvenlik şeması
  `cookieAuth`a revize edilir.

## 2. Tema kuralı (EN sık ihlal edilen kanon)
- Tema kullanıcı toggle'ı DEĞİL, **ekran türüdür**: çalışma/odak/analitik/panel = `paper` (açık,
  sıcak kâğıt #F7F4EF) · duygusal/hub/kutlama/mola/ritüel = `dusk` (koyu şafak). Route-bazlı
  `KiroThemeProvider theme=...` ile uygula; ASLA karıştırma, asla kullanıcıya seçtirme.
- Sıkı-AA yalnız AÇIK zeminde: küçük gri #6B6478 · amber METİN #9A5D0D · coral METİN #C2452B.
  Koyu zeminde bu düzeltmeler YAPILMAZ.
- Alarm-kırmızısı tüm üründe yasak; risk her zaman sıcak amber. Tek istisna:
  Boss arenası (`kanon-allow: boss-arena`, onaylı).

## 3. İş sırası
**Repo-temelli fazlar ve dosya-dosya görevler: `ENTEGRASYON_PLANI.md` (Faz 0 → S12).** Özet:
1. **Kuruluş (Faz 0-1):** `src/kiro/` yerleşimi + tokens/types/api-client derlenir;
   `configureKiroApi({mode:'mock', mockData})` ile örnek sayfa render alır. ADR'ler `docs/adr/`ye.
2. **Faz 2 — 20 bileşen:** ui-starter TEST EDİLMEMİŞ başlangıçtır. Her bileşen: (a) Storybook story
   (b) RTL etkileşim testi (c) axe temiz (d) `KIRO Bilesenler.dc.html`'e karşı görsel diff
   (BackstopJS kurulu). Skeleton'ın şafak kişiliği (kiroSweep + 3sn mantra satırı) spec'in parçasıdır.
3. **Faz 3 — ekranlar, MOCK modda:** sprint sırası `SPRINT1..12_SPEC.md`; her spec'in sonunda
   **"Erişilebilirlik satırları" bölümü ekran-özel DoD'dir** — pas geçilmez. İlk sprint
   kalibrasyonu: Button+Card+StatusChip + Giriş + Ödevlerim; süreyi ölç, kalan işi çarpanla tahmin
   et. Sprint kapsamları: S2 Hesap Kurtarma + Onboarding (yeni Adım 1: kaygı-tonu — kopyalar
   onaylı, birebir) + Öğrenci Paneli · S3 Soru Çözme + Neden + FSRS · S4 Adaptif Test +
   Harmanlanmış Deneme + Sınav Sonuç · S5 Haftalık Plan + Öğrenme Yolu + Bilgi Atomları + Çalışma
   Modları · S6 Bugün/Şafak + Kutlama + Mola (İLK dusk ekranlar) · S7 Geri Sayım + Başarımlar +
   Boss · S8 Lig + Düello + Arkadaş Serisi + Seri Dondurma (lig ucu: önce backend keşfi) ·
   S9 Sokratik AI + AI Sohbet + İnteraktif Çözüm + Kaygı Ölçüm (AI yalnız sunucu proxy'sinden;
   STAI lisansı ön koşul) · S10 Abonelik + Ödeme + Ayarlar + Bildirim Merkezi (kart alanları
   YALNIZ Stripe Elements, ADR-002) · S11 Öğretmen Paneli + Öğrenci Özeti + Veli Paneli + Veli
   Bağlama + Ödev Atama + **Sınıf Kurulumu** (risk sinyali yalnız yetişkine) · S12 Çevrimdışı +
   Alan Kütüphanesi (SON).
4. **Faz 4 — backend:** `openapi.yaml` sözleşmedir; backend contract-test, frontend zod şemaları
   buradan üretilir. Mock→live geçişi uç-uç feature flag; ekran kodu değişmez
   (`configureKiroApi({mode:'live', baseUrl, ...})`). **Motorları istemciye TAŞIMA** — θ/CAT/FSRS/BKT
   sunucuda; prototipteki istemci simülasyonları yalnız mock modda kalır.
   **Davranış referansı: `kiro-api.js`** — sözleşmenin çalışan mock'u (prototipte
   `KIRO2 API Konsol.dc.html` ile canlı test edilir): hata zarfı `{error:{code,message}}`,
   kaygı-duyarlı hata mesajları, sunucu-otoriter kurallar (`dogru`/çözüm YALNIZ answer yanıtında;
   `cat/next` 'dogru'suz; sınıf varsayılanlarını sunucu yazar). MSW handler'larını bu dosyadan türet.
5. **Faz 5-6:** 5 E2E senaryosu (Playwright kurulu) + `ACCESSIBILITY.md` manuel listesi +
   kanon lint'i (§4) + `BREAKPOINT_SPEC.md` QA matrisi (390/768/834/1024/1194/1280/1440;
   DoD: overflowX=0 · hit ≥44 (≤1199) · odak halkası iki zeminde · tema değişmez).

## 4. Kanon lint'i (CI'a ekle)
Hazır script: `scripts/kanon-lint.mjs` — CI adımı:
`node design/scripts/kanon-lint.mjs frontend/src/kiro` (ihlalde exit 1). Kurallar:
- grep-yasak: emoji; indigo/lacivert hex; alarm-kırmızısı (#DC2626, #EF4444, #B91C1C vb.) —
  risk HER ZAMAN amber.
- "eksik" kelimesi ödev bağlamında yasak → "bekliyor".
- Koyu ekran dosyalarında `#6B6478` kullanımına uyarı (açık-zemin grisidir).
- Tüm sayısal metinlerde `tabular-nums` (ui/theme.tsx → `numText`).
- Animasyon transform-only + `useReducedMotion` (ui/ConfettiDawn.tsx örnek desen).

## 5. Bilinen tuzaklar
- `SideNav` preset href'leri placeholder — router'ına `renderLink` ile bağla; 64px ikon-only
  daralmayı `collapsed` prop'u veya container-query ile koru (768–1023 rail kuralı:
  BREAKPOINT_SPEC §3).
- Soru payload'ında `dogru` alanı istemciye ASLA inmez; yalnız `POST /questions/:id/answer`
  yanıtında gelir (openapi.yaml).
- Kutlama (ConfettiDawn) yalnız GERÇEK kademe geçişinde — sunucu yanıtındaki geçiş bilgisiyle
  tetiklenir, istemci tahminiyle değil.
- Veli yüzünde SİZ-dili; öğrenci yüzünde akran sesi + "sen vs dün". Fiyat yalnız veli rolünde
  görünür. Sıralama-baskısı deseni hiçbir yüzeyde yok (lig "sakin mod" + gizlenebilir sıralama).
- Kaygı-tonu (`kaygiTonu`) ve mood verisi veliye/öğretmene ASLA gösterilmez (KARARLAR #5);
  öğretmen yüzü sohbet/mood/tekil cevaplara erişemez — API de döndürmez.
- Geri sayım varsayılan kapalı; açılırsa bile SAYISIZ kaygı-nötr varyant varsayılandır (S7 spec).
- Prototip DC'lerindeki `background:#fff` + `box-shadow:inset 0 0 0 999px <renk>` seçim-dolgusu
  deseni prototip-runtime'ının çözümüdür — üretime TAŞINMAZ; normal state'li stil kullan.
- Prototipteki senkron `kiro-seed.js` yalnız prototip içindir; üretimde veri her zaman
  api-client'tan (mock modda `kiro-data.json`) akar.

## 6. Tanım-of-Done (her ekran PR'ı)
1. Piksel: flow PNG'sine ve DC'ye karşı görsel diff makul (BackstopJS).
2. Kopya birebir; Türkçe sayı biçimi (virgül, tabular-nums).
3. Tema doğru (`paper`/`dusk`) + sıkı-AA yalnız açık zeminde.
4. Sprint spec'inin "Erişilebilirlik satırları" DoD'si + axe temiz.
5. `BREAKPOINT_SPEC.md` bantlarında overflowX=0, hit ≥44 (≤1199).
6. Kanon lint yeşil; `PORT_DURUM.md` satırı işaretlendi.
