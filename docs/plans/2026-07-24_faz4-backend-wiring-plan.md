# KIRO2 — Faz 4 Backend Wiring PLANI (2026-07-24)

Kiro tasarım-portu (`frontend/src/kiro/`, mock-katmanı, 42 ekran) → gerçek backend. Recon: `wf_74e83590-6ac` (live-mode + app-integration + backend uç matrisi).

## Temel gerçek
Port **çift-kollu inşa edildi**: neredeyse her api-client metodunun `if (cfg.mode==='mock') … else live<T>(path)` kolu var. Seam: `configureKiroApi({mode:'live', baseUrl, getToken})`. Yani Faz 4 "sıfırdan yazma" değil — **3 sistemik blocker + yüzey-bazlı doğrulama/adaptör**.

---

## 3 SİSTEMİK BLOCKER (P0 — her şeyi kilitler, ÖNCE)

**B1 · Auth modeli uyuşmazlığı.** kiro `live()` `Authorization: Bearer <getToken()>` kullanıyor; ama gerçek app **httpOnly COOKIE** auth (authStore'da token YOK, `partialize` yalnız {user,isAuthenticated}). `duelStream` zaten `withCredentials:true` (cookie) — geri kalan tutarsız. → **`live()` + `streamSohbet-live` `credentials:'include'`'a çevrilmeli, Bearer/getToken seam'i düşer.**

**B2 · baseUrl prefix drift'i.** Bazı yollar `/api/v1/...` hardcode (duel, league, parent, teacher, kvkk), bazıları çıplak (`/me`, `/subjects`, `/engine`, `/questions/set`). baseUrl `/api/v1` içerirse hardcode olanlar **çift-prefix** olur. → **Tek konvansiyon:** baseUrl = origin, TÜM yollar `/api/v1/...` (çıplakları normalize et).

**B3 · Rota kanon çatışması.** kiro TR (`routeGuard.ROL_LANDING` /panel·/veli·/ogretmen + ekran href /giris·/onboarding) vs repo İNGİLİZCE kanon (`getRedirectPathByRole` /dashboard·/parent/dashboard, /login; path-naming.md, GF5/GF8). → **İngilizce kanona hizala; yeni guard İCAT ETME → `ProtectedRoute`+`getRedirectPathByRole` reuse** (routeGuard bunu delege eder).

**Ek plumbing:** `live()` zarf-çözme (`unwrapData`) yalnız rol/billing'de manuel — düz uçlar backend `{success,data}` sararsa kırılır → merkezi çöz. 401→/login redirect, 503→degraded, `kiro/api/mappers.ts` (snake_case/Türkçe → camelCase kiro tipleri).

---

## APP-INTEGRATION (P0 — B ile paralel)
kiro ekranları **ana App'e mount DEĞİL** (grep: kiro-dışı import 0). Her veri-ekranı modül-başı `configureKiroApi(mock)` çağırıyor (singleton kirlenme riski).
- Merkezi bootstrap: `main.tsx`'te TEK KEZ `configureKiroApi({mode: env, baseUrl: VITE_API_URL})`; ekran modül-başı mock çağrılarını KALDIR (test/story'de fixture olarak kalır).
- kiro ekranlarını `App.tsx <Routes>`'a İngilizce kanon rotalarda mount et, `ProtectedRoute` ile sar (Modern* rota-rota değiştir — **stratejik karar, aşağıda**).
- `GirisPage` → `authStore.login` (cookie) + `navigate(getRedirectPathByRole(user.rol))` + `2fa_required` dalı.

---

## YÜZEY HAZIRLIK MATRİSİ (öncelik = hazırlık × değer)

| Yüzey | Hazırlık | İş | Not |
|---|---|---|---|
| **AI** (Sohbet·Sokratik·İnteraktif) | 🟢 gerçek-hazır | minimal | `enhanced_chat.py` gerçek; streamSohbet zaten POST-SSE doğru. Yol normalizasyonu + mapSohbet. |
| **Düello** (Grup 6) | 🟢 gerçek-hazır | ~0 | api-client zaten `/api/v1/duel/*` SSE+ELO'ya bağlı (SPRINT8). HEMEN live. |
| **Çevrimdışı** (Grup 8) | 🟢 gerçek-hazır | 1 satır | Yalnız yol: `/offline/durum`→`/offline/sync-status` (+snake→camel). |
| **Veli + KVKK** (Grup 7) | 🟢 gerçek-hazır | mapper var | `/parent/*`+`/kvkk/*` gerçek, mapper tolerant. |
| **Çekirdek-döngü** (Grup 3-5: soru·cevap·CAT·FSRS·sınav) | 🟡 kısmi — **ADAPTÖR** | AĞIR (en yüksek değer) | Motorlar GERÇEK (CAT/IRT session-stateful `/api/v1/cat/sessions`, FSRS, ÖSYM-exam) ama kiro **stateless sözleşme** (`/questions/set`,`/cat/next`) → **BFF/adaptör** şart. Ürünün kalbi. |
| **Lig** (Grup 6) | 🟡 kısmi | snake→camel | `/leagues/*` gerçek, eksik alan DTO. |
| **Öğretmen** (Grup 7) | 🟡 parçalı | roster zenginleştirme | İskelet gerçek ama net/hâkimiyet/ad **stub** — student servis join gerek. B2B kritik. |
| **Bildirim** (Grup 8) | 🟠 backend-build | mark-read/unified | öğrenci GET gerçek; mark-read/unread/birleşik `/notifications` YOK. |
| **Ayarlar** (Grup 8) | 🟠 backend-build | `/preferences` | OSB gerçek; calmMode/hideRanking/genel-prefs backend YOK. |
| **Alan Kütüphanesi · Haftalık Plan** | 🟠 backend-build | üretici servis | parçalardan türetilecek kanonik uç YOK. |
| **Billing/Ödeme/Plan** (Grup 8) | 🔴 backend-build ağır | PSP + katalog | `/billing/me` gerçek; PSP/checkout/3DS/plan-katalog/self-serve YOK. **B2B'de invoice-tabanlı → launch-kritikliği DÜŞÜK, ertelenebilir.** |
| **Boss · Arkadaş Serisi · Seri** (Grup 5-6) | ⚫ ertele | — | backend YOK; saf-mock kalır (düşük ROI). |

---

## ÖNERİLEN FAZLAMA

- **F4-S0 · Blocker + plumbing (P0):** B1 (cookie auth) · B2 (baseUrl /api/v1 normalize) · B3 (rota İngilizce hizala) · merkezi `configureKiroApi` + unwrapData + 401/503 handling + `mappers.ts` iskeleti. *Hiçbir şey bu olmadan live çalışmaz.*
- **F4-S1 · Quick-win + seam doğrulama:** AI + Düello + Çevrimdışı + Veli/KVKK'yı live'a çevir; kiro ekranlarını App'e mount (İngilizce rota + ProtectedRoute); GirisPage→authStore.login. **Uçtan uca kanıt** (login→cookie→canlı ekran) + her yüzeye live-smoke.
- **F4-S2 · Çekirdek-döngü adaptörü (EN YÜKSEK DEĞER):** `/questions/set`·`/cat/next`·`/review/*`·`/exams/*` için BFF/adaptör (CAT stateless cephe: arkada session aç/sür). Ürünün kalbi.
- **F4-S3 · Roller (B2B go-to-market):** öğretmen roster zenginleştirme + öğrenci-özeti + katılım-kodu/rotate/join.
- **F4-S4 · İş katmanı (backend-build):** Bildirim mutation + Ayarlar `/preferences` + Alan Kütüphanesi browse + Haftalık Plan üretici.
- **Ertele:** Boss · Friends/streak · Billing PSP (saf-mock kalır).

Her sprint: keşif→wire→**live-smoke** (dev stack ayakta) → E2E → commit. Mock/story/test DEFAULT mock kalır (env ile live); mode-switch mock testleri bozmamalı.

---

## KARARLAR (2026-07-24 · kullanıcı onayı — KİLİTLİ)
1. **Migrasyon = KADEMELİ SWAP** ✅ — Modern* ekranları rota-rota kiro ile değiştir; her yüzey live olunca eski Modern* düşer (geri-alınabilir, uçtan-uca doğrulanabilir). F4-S1'den hazır yüzeylerle başlar.
2. **Auth = COOKIE** ✅ (teknik-zorunlu) — `live()` + `streamSohbet-live` `credentials:'include'`; Bearer/getToken seam'i düşer (authStore httpOnly cookie, JS token yok).
3. **baseUrl = origin + tüm yollar `/api/v1`** ✅ (teknik-zorunlu) — çıplak yolları (`/me`,`/subjects`,`/engine`,`/questions/set`…) normalize et.
4. **İlk sprint = F4-S0 blocker + F4-S1 quick-wins** ✅ — 3 blocker çöz + AI·Düello·Çevrimdışı·Veli live + App-mount + login → uçtan-uca kanıt.
5. **Billing PSP = ERTELE** ✅ — B2B okul invoice-tabanlı (org_billing gerçek); tüketici PSP/3DS launch-kritik değil, saf-mock kalır (F4-S4 sonrası).

### F4-S0 kapsamı (ilk build turu — kilitli kararlarla)
- B1 cookie: `live()` (api-client.ts:139) + `streamSohbet-live` (1717) `credentials:'include'`; Bearer/getToken kaldır.
- B2 baseUrl: tek konvansiyon — çıplak yolları `/api/v1` prefix'le (VEYA baseUrl'e /api/v1 + hardcode'ları çıplaklaştır; birini seç, tut).
- B3 rota: `routeGuard.ROL_LANDING` → İngilizce (`getRedirectPathByRole` ile hizala/delege).
- Plumbing: merkezi `configureKiroApi` (main.tsx, env baseUrl) + ekran modül-başı mock çağrılarını kaldır (test fixture kalır) + `live()` unwrapData + 401→/login + 503→degraded + `kiro/api/mappers.ts` iskeleti.
- **Gate:** mevcut 491 mock testi BOZULMAMALI (mode default mock; live env ile) + F4-S1'de canlı-smoke (dev stack ayakta).

*Kaynak: recon `wf_74e83590-6ac`. Kararlar kilitli — sıradaki icra adımı: F4-S0 build (keşif→wire→gate→live-smoke→commit).*
