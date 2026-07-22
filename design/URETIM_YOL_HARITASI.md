# KIRO2 — Üretim Frontend Yol Haritası (backend entegrasyonu dahil)

> Mevcut duruma göre hazırlandı (DEVIR §22s-w sonrası). Ölçülmüş kapsam (dosya sayımları, bu belgeyle aynı gün):
> **45 ürün DC'si** = 41 taşınacak ekran (**39 üretim + 2 araştırma yüzeyi** — Kaygı Ölçüm · Moderatör Kılavuzu saha paketidir, üretim uygulamasına port edilmez) + 4 paylaşılan bileşen (Kenar ×3 + Mastery Rozet) · **sözleşmede 26 uç kartı + 8 satır-içi uç** ·
> **29 veri anahtarı** (`window.__KIRO`) · **18 ui-starter dosyası** (15 bileşen, test edilmemiş) · **19 flow PNG** (görsel regresyon referansı).
> Otoriter referanslar: `KIRO2 Tasarim Sistemi.dc.html` (görsel) · `KIRO2 API Sozlesmesi.dc.html` (veri) ·
> `KIRO Bilesenler.dc.html` (P0 piksel) · `KIRO Durumlar.dc.html` (durum standardı) · `CLAUDE.md` (kanon).

---

## FAZ 0 — Kuruluş & kararlar (kapsam: 1 monorepo + 5 ADR kararı)

> **GÜNCELLEME (2026-07-04, ADR-000):** Keşif sonrası karar — `HuseyinAts/kiro2` reposunda olgun bir Vite+React frontend ve backend zaten var. Faz 0.1 "boş monorepo" yerine **mevcut repoya retrofit** uygulanır; Next.js'e geçilmez. Ayrıntı: `design_handoff_kiro2/ADR.md` + `CLAUDE_CODE_TALIMAT.md`. Aşağıdaki 0.1 tarihsel plan olarak korunmuştur.

**0.1 Monorepo**
- pnpm + Turborepo: `apps/web` (Next.js, App Router) · `apps/mobile` (Expo RN) · `packages/tokens · types · api-client · ui`.
- TypeScript `strict`, ESLint + Prettier, commit hook (lint-staged).
- CI (GitHub Actions): typecheck + lint + test + build her PR'da.

**0.2 Verilecek kararlar (her biri tek satırlık ADR olarak yazılsın)**
- [ ] Auth sağlayıcı: kendi JWT'miz mi, yönetilen mi (Supabase/Auth0)? Sözleşme `/auth/*` şeklini varsayar.
- [x] Ödeme sağlayıcı: **Stripe birincil, iyzico yedek** (ADR-002 kabul) — kart **tokenize** edilir, bizde tutulmaz (Ödeme ekranı sözü).
- [ ] Gerçek zamanlı katman: Düello/Lig için WebSocket mi 15sn polling mi (MVP: polling yeter).
- [ ] Push: FCM + APNs (Bildirim Merkezi + "deneme bitmeden hatırlat" ürün sözü buna bağlı).
- [ ] Analitik + hata izleme: Sentry + (opt-in) ürün analitiği. KVKK: 17-19 yaş kullanıcı — veli aydınlatması.
- State yönetimi (karar verildi sayılabilir): **TanStack Query** (sunucu verisi) + hafif yerel state (Zustand/useState). Redux gereksiz — prototipteki tüm state ekran-yereldi.

**0.3 Tasarım kaynağı**
- `design_handoff_kiro2/` zip'ini repoya `design/` olarak koy; flow PNG'leri görsel regresyon referansı olacak.

**Çıkış kriteri:** boş monorepo CI'da yeşil; ADR'ler yazılı.

---

## FAZ 1 — Ortak çekirdek paketleri (kapsam: 3 paket — tokens · types · api-client)

**1.1 `packages/tokens`** — `tokens.ts` + `tokens.css` birebir taşınır.
- Tema **kullanıcı toggle'ı DEĞİL, ekran türüdür**: `k-paper` (çalışma) / `k-dusk` (duygusal). Route-bazlı uygulanır.
- Fontlar: Instrument Serif (his/mantra, italik) · Hanken Grotesk (işlev + TÜM sayılar `tabular-nums`) · IBM Plex Mono. Web: `next/font`; mobile: `expo-font`.
- Sıkı-AA çifti unutulmasın: açık zeminde küçük gri `#6B6478`, amber METİN `#9A5D0D`, coral METİN `#C2452B`; koyu zeminde bu "düzeltmeler" YAPILMAZ.

**1.2 `packages/types`** — `types.ts` (Odev/OdevDurum, SinifOgrenci, KatalogUniteler, AuthTokens dahil — güncel).

**1.3 `packages/api-client`** — `api-client.ts` + `kiro-data.json`.
- Eklenecekler: 401 → `/auth/refresh` interceptor'ı; istek iptali (AbortController); `zod` ile yanıt şema doğrulama (sözleşmeden şemalar).
- Test: MSW ile mock↔live davranış eşitliği; `KiroApiError` her uçta.

**1.4 A11y temel araçları** — `:focus-visible` coral ring, `useReducedMotion`, ikonlar bespoke inline SVG (kütüphane YOK), emoji YOK.

**Çıkış kriteri:** üç paket yayınlanıyor; örnek sayfa mock veriyle token'lı render alıyor.

---

## FAZ 2 — P0 bileşen kütüphanesi (kapsam: 15 iskelet + 5 prototipten çıkarılacak = 20 bileşen × 4 kalite kapısı)

`ui-starter/` 15 iskeleti temel al ama **test edilmemiş** — her birini Storybook + test + piksel karşılaştırmayla üret. Piksel referansı: `KIRO Bilesenler.dc.html`.

**İskeletteki 15 bileşen + tema altyapısı (ui-starter/ dosya listesi, birebir):**
- theme.tsx (KiroThemeProvider — bileşen değil altyapı; tema ekran TÜRÜdür; `surf()` yüzey çözücü; `numText` tabular)
- Button (primary/ghost/disabled, ≥44pt) · Card · Input (+amber hint kutusu) · SegmentedControl · Chip
- Callout (sakin amber bilgi kutusu) · IconBadge · Avatar · StatBlock · ZoneHeader
- ProgressBar (ders-renkli; tamam=yeşil) · ProgressRing
- Skeleton · EmptyState · ErrorState — `KIRO Durumlar` standardı: zıplamayan iskelet, yönlendiren boşluk, sakin amber hata + "sorun sende değil"

**İskelette OLMAYAN, prototip DC'lerinden çıkarılacak ek bileşenler (kaynağıyla):**
- SideNav ← `KIRO Kenar.dc.html` (+Veli/Ogretmen varyantları; container-query ile 64px ikon-only; öğrenci navda **Ödevlerim dahil**)
- MasteryBadge ← `KIRO Mastery Rozet.dc.html` (Tanıdık<40 · Yetkin<65 · Usta<85 · Fethedildi)
- StatusChip (ödev hâli) ← `KIRO2 Odevlerim.dc.html` — **acik / bekliyor / tamam**; "bekliyor" amber, asla "eksik"/kırmızı
- ChatBubble ← `KIRO2 Sokratik AI.dc.html` · ConfettiDawn ← `KIRO2 Kutlama.dc.html` (transform-only; reduced-motion'da kapalı)

**Kalite kapısı:** her bileşen için (a) Storybook story, (b) RTL etkileşim testi, (c) axe temiz, (d) `KIRO Bilesenler.dc.html` referansına karşı görsel diff (ekran düzeyinde referans: flow PNG'leri).

---

## FAZ 3 — Ekran portu, MOCK modda (kapsam: 39 üretim ekranı + 4 paylaşılan DC · 39 × 6 DoD maddesi = 234 kontrol)

`configureKiroApi({mode:'mock', mockData: kiroDataJson})` — backend beklemeden 39 ekranın hepsi gerçek veri şekliyle çalışır. Port sırası (bağımlılık sırası; 9 grupta 39 ekranın TAMAMI listelidir):

1. **Auth & ilk temas (4):** Giriş & Kayıt → Hesap Kurtarma (3 adım) → Onboarding (misafir yerleştirme — hesapsız çalışır, "önce değerini gör, sonra kaydet") → İlk Hafta. + route guard + rol yönlendirmesi (öğrenci/veli/öğretmen).
2. **SideNav + Öğrenci Paneli (1):** yoğunluk Rahat/Kompakt.
3. **Çekirdek döngü (6):** Soru Çözme → Neden Geri Bildirim → FSRS Tekrar → Adaptif Test → Harmanlanmış Deneme → Sınav Sonuç (net-birincil hiyerarşi).
4. **Planlama (4):** Haftalık Plan · Öğrenme Yolu · Bilgi Atomları · Çalışma Modları.
5. **Hub/duygusal, koyu (6):** Bugün · Kutlama · Mola · Geri Sayım (**varsayılan kaygı-nötr varyant**) · Başarımlar · Boss.
6. **Oyunlaştırma (4):** Lig (`siralamaGizli` + "Sıralamayı gizle" düğmesi) · Düello · Arkadaş Serisi · Seri Dondurma.
7. **Roller (4):** Veli Paneli · Öğretmen Paneli · **Ödev Atama ↔ Ödevlerim** (tek döngü olarak test edilir).
8. **İş & dayanıklılık (6):** Abonelik (`?rol=veli`) → Ödeme · Ayarlar · Bildirim Merkezi · Alan Kütüphanesi (ünite drill) · Çevrimdışı.
9. **AI & çözüm (4):** AI Sohbet · Sokratik AI (şimdilik mock yanıt; Faz 4'te proxy) · İnteraktif Çözüm · Çözüm Paylaş.

*(Kapsam dışı, 2: Kaygı Ölçüm + Moderatör Kılavuzu — araştırma saha paketi; gerekirse ayrı dahili araç olarak taşınır.)*

**Her ekranın DoD'si (tanım-bitti):**
- [ ] Prototip `.dc.html` ile yan yana piksel karşılaştırma (tarayıcıda aç)
- [ ] Üç durum bağlı: Skeleton / EmptyState / ErrorState (mock'ta gecikme+hata simüle et)
- [ ] 390px'te overflow-x = 0; hit target ≥44pt; telefon safe-area (referans: `KIRO2 Mobil.dc.html`)
- [ ] Kaygı-duyarlı kopya **birebir** (davet dili, "Henüz değil", "bekliyor", sen-vs-dün; veli yüzünde SİZ-dili)
- [ ] Klavye ile gezilebilir; ikon düğmelerde aria-label; axe temiz
- [ ] Ekran-türü teması doğru (çalışma=açık, duygusal=koyu — asla karışmaz)

---

## FAZ 4 — Backend entegrasyonu (Faz 3'le paralel; kapsam: 26 uç kartı + 8 satır-içi uç · 3 sunucu-otoriter motor)

**4.1 Sözleşmeyi makineleştir**
- `KIRO2 API Sozlesmesi.dc.html` → `openapi.yaml` (tüm bölümler: genel · öğrenci · dersler · curriculum · FSRS · CAT · denemeler · oyunlaştırma · motor · **auth · ödevler · bildirim · senkron · fatura**).
- Backend bu şemaya karşı contract-test edilir; frontend zod şemaları buradan üretilir.

**4.2 Kademeli mock→live geçişi** — uç-uç feature flag: `GET /me` → `/subjects` → `/topics` → `/curriculum` → `/review` → `/questions` → `/cat` → geri kalanı. Her uçta: yanıt zod'dan geçer, hata `ErrorState` kopyasına düşer.

**4.3 Sunucu-otoriter motorlar (EN KRİTİK)**
- Prototipteki **istemci simülasyonlarını taşıMA**: θ güncelleme, FSRS zamanlama, BKT — hepsi sunucuda. İstemci yalnız `POST /questions/:id/answer`, `POST /cat/next`, `POST /review/:id/grade` sonuçlarını gösterir.
- Optimistic UI yalnız görsel geri bildirimde (buton durumu); sayılar daima sunucu yanıtından.

**4.4 Auth akışı**
- Web: httpOnly cookie; Mobile: SecureStore. 401 → refresh → tek tekrar. Çıkışta kuyrukları temizle.
- **Misafir→hesap migrasyonu:** yerleştirme sonucu (θ başlangıcı) kayıt anında hesaba taşınır — ürün vaadi.
- Kurtarma: 3 adım (`recover → verify → reset`); başarı kopyası "Serin ve ilerlemen aynen yerinde."

**4.5 AI proxy** — `window.claude.complete` → backend `POST /ai/socratic` / `/ai/chat`. Sistem-prompt sunucuda (en zayıf `topics`'e dayalı, cevabı vermeyen Sokratik ton). Hata → prototipteki scripted fallback korunur. Rate limit + içerik güvenliği sunucuda.

**4.6 Çevrimdışı** — service worker + IndexedDB olay kuyruğu. `GET /sync/packages` çevrimiçiyken otomatik indirme (sıradaki plan görevi + günün kartları); `POST /sync/events` **idempotent** (event id ile), bağlantı dönünce otomatik boşaltma; amber bant UI'ı Çevrimdışı ekranı birebir.

**4.7 Bildirim** — push token kaydı, `/notifications` listesi + okundu; sessiz saatler Ayarlar'dan; kopya kaygı-duyarlı (alarm/baskı yok).

**4.8 Ödeme** — sağlayıcı tokenizasyonu → `POST /billing/trial`. Ürün sözleri backend gereksinimi olarak: **bugün ödeme alınmaz**, deneme bitmeden e-posta hatırlatması ZORUNLU, iptal tek adım, öğrenci rolüne fiyat gösterilmez (veli yüzü).

**4.9 Ödev döngüsü** — Öğretmen `POST /assignments` (kisisel=true → set sunucuda θ'ya göre) → öğrenci `GET /assignments` → `POST /assignments/:id/progress`. Geciken sunucuda da "bekliyor"dur; "eksik" hiçbir katmanda yok.

---

## FAZ 5 — Kalite & sertleştirme (kapsam: 5 E2E senaryosu + ACCESSIBILITY.md manuel listesi + kanon lint'i)

- **E2E (Playwright/Detox):** ① kayıt→yerleştirme→ilk soru→kutlama ② giriş→FSRS→grade ③ öğretmen ödev atar→öğrenci görür→ilerler ④ abonelik→ödeme→deneme ⑤ çevrimdışı çöz→senkron.
- **Erişilebilirlik:** axe CI'da; `ACCESSIBILITY.md` manuel listesi gerçek cihazda (VoiceOver/TalkBack, font %200, güneş ışığı, renk körlüğü simülasyonu).
- **Performans:** LCP < 2.5s, route-bazlı code splitting, PNG→optimize edilmiş görseller, animasyonlar transform-only.
- **Güvenlik/KVKK:** 17-19 yaş verisi; veli izin akışı; PII envanteri; rate limit; Sentry'de PII maskeleme.
- **Kanon denetimi (otomatik lint):** alarm-kırmızısı/indigo hex'leri ve emoji'yi CI'da grep'le yasakla; koyu ekranda `#6B6478` kullanımına uyarı.

## FAZ 6 — Yayın & ölçüm

- Beta: TestFlight / Play Internal → kademeli rollout.
- **Kaygı ölçümü sahada:** `USER_TESTING.md` + Moderatör Kılavuzu + Kaygı Ölçüm anketi (STAI-S lisansı + etik onay araç-dışı ön koşul). Ürünün 1 numaralı iddiasının doğrulanması.
- İzleme: hata oranı, uç gecikmeleri, D1/D7 tutunma, seri kırılma noktaları; Geri Sayım A/B'si (kaygı-nötr vs sayaç) gerçek veriyle karara bağlanır.

---

## Kapsam dökümü (ölçülmüş) ve süre tahmini yöntemi

Aşağıdaki sayılar bu projeden **sayılarak** alındı — varsayım değil:

| İş kalemi | Ölçülmüş kapsam | Kaynağı |
|---|---|---|
| Taşınacak ekran | **39 üretim + 2 araştırma** (+4 paylaşılan DC) | proje dosya sayımı |
| P0 bileşen | **15 iskelet + 5 prototipten çıkarılacak** | `ui-starter/` dosya listesi + Faz 2 |
| API ucu | **26 kart + 8 satır-içi** | `KIRO2 API Sozlesmesi` metod sayımı |
| Veri anahtarı (tip + mock) | **29** | `kiro-seed.js` `__KIRO` sayımı |
| Ekran başına DoD | **6 madde** → 39×6 = **234 kontrol** | bu belge, Faz 3 |
| Görsel regresyon referansı | **19 PNG** | `screenshots/flow/` |
| E2E senaryosu | **5** | bu belge, Faz 5 |

**Süre: takvim haftası UYDURMA.** Ekip hızı bilinmeden hafta tahmini kanıtsızdır; onun yerine kalibrasyon:
1. İlk sprintte **3 bileşen + 2 ekran** (önerilen: Button+Card+StatusChip; Giriş + Ödevlerim — biri basit, biri veri-yoğun) DoD'siyle bitir, gerçek süreyi ölç.
2. Kalan işi çarp: `kalan süre ≈ (ölçülen ekran-başı süre × 37) + (ölçülen bileşen-başı süre × 17) + uç başına entegrasyon süresi × 34`. (37 = 39−2 ölçülen ekran; 17 = 15+5−3 ölçülen bileşen; 34 = 26+8 uç.)
3. Her sprint sonunda çarpanları gerçekleşen hızla güncelle. (Referans eşikler — LCP < 2.5s — tahmin değil, Core Web Vitals standardıdır.)

**Altın kurallar (her fazda):** motorlar sunucuda · tema ekran türüdür · "bekliyor" dili · sıkı-AA yalnız açıkta · tabular-nums tüm sayılarda · ikonlar bespoke SVG · emoji yok · indigo yok · kopyalar prototipten birebir.
