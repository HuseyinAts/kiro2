## Session Handoff — 2026-07-24 (F4-S0 build)
**Branch:** feature/self-evolution-optimization
**Son commit:** b8626be6a feat(kiro): Faz 4 F4-S0 — backend wiring blocker + plumbing
**Uncommitted:** temiz. **PUSH YOK** (standing kural) — origin ccfe794e0 gerisinde 3 doc + 1 kod commit önde.

### Yapılanlar — F4-S0 TAMAM (3 blocker + plumbing, kilitli kararlarla)
- **B1 cookie-auth** (`kiro/api/api-client.ts`): `live()` + `streamSohbet` Bearer/getToken düştü → `credentials:'include'`; `KiroApiConfig.getToken` alanı silindi (grep: başka çağıran yok).
- **B2 baseUrl**: transport-katmanı `apiPath()` helper — `/api/v1` ile başlamayan tüm yolları idempotent prefixler (~62 çıplak normalize, 13 prefixli + duel-EventSource değişmez). baseUrl=`window.location.origin` (VITE_API_URL DEĞİL — same-origin cookie zorunlu; main.tsx global fetch override credentials ekler).
- **B3 rota**: `routeGuard.ROL_LANDING` İngilizce kanona (`/dashboard`·`/parent/dashboard`·`/teacher/dashboard`, getRedirectPathByRole mirror + drift-guard yorum), AuthGate `/giris`→`/login`. `routeGuard.test` + `GirisPage.test` lockstep güncellendi.
- **Plumbing**: `main.tsx` merkezi `configureKiroApi({mode: VITE_KIRO_API_MODE|'live', baseUrl: origin})`; `live()` merkezi `unwrapData` + `401→/login`; **39 ekran modül-üstü mock çağrısı kaldırıldı** (39 paralel agent, 0 anomali) + `src/test/setup.ts` paylaşılan default mock köprüsü. KutlamaPage `kiroData` başka yerde kullanıyor→import KORUNDU.
- **Ertelendi**: `mappers.ts` iskeleti → F4-S1 (YAGNI). Billing PSP → F4-S4 sonrası.

### Gate (hepsi YEŞİL)
tsc `--noEmit` 0 (×2) · eslint `no-unused-vars` 0 (tsconfig noUnusedLocals açık) · **vitest kiro 491/491 PASS** (72 dosya) · `vite build` OK (2m20s). eslint kiro'da 385 pre-existing stil hatası (curly/eqeqeq — port'un kendi stili, gate DEĞİL; kanon-lint kullanılıyor).

### Fail Eden Testler
YOK.

### Engelleyiciler
F4-S1 **canlı-smoke** için dev-stack ayakta gerekir: backend + PG **5434** + Redis (şu an KAPALI — operatör). Login→cookie→canlı ekran uçtan-uca kanıt bunsuz yapılamaz.

### Sonraki Adımlar (F4-S1 — quick-win + uçtan-uca kanıt)
1. Dev stack ayağa kaldır (operatör): backend + PG5434 + Redis + health.
2. AI·Düello·Çevrimdışı·Veli/KVKK live'a çevir (🟢 gerçek-hazır; Çevrimdışı 1-satır yol `/offline/durum`→`/offline/sync-status`).
3. kiro ekranlarını `App.tsx <Routes>`'a İngilizce kanon rotalarda ProtectedRoute ile mount (kademeli-swap, Modern* rota-rota).
4. `GirisPage`→`authStore.login` (cookie) + `navigate(getRedirectPathByRole(user.rol))` + `2fa_required` dalı + onboarding `/giris`→`/login` href.
5. Her yüzeye canlı-smoke + `mappers.ts` gerçek ihtiyaç netleşince yaz.

### Kararlar / Notlar (F4-S0 keşif inceltmeleri)
- Gerçek stack ZATEN cookie (login/secure httpOnly, main.tsx global fetch override same-origin credentials). Kiro live() relative/origin tutulmalı — mutlak VITE_API_URL cookie'yi kırar.
- Rol kaynağı: gerçek stack `user.rol` (GET /api/v1/auth/me), kiro getRol (GET /me/rol) AYRI — F4-S1'de ProtectedRoute tek-kaynak (user.rol) kullanmalı, redirect-loop riski.
- `unwrapData` merkezi (live()) → typed uçlar da zarf-tolerant; 21 manuel-çözen uç idempotent double-unwrap. Backend zarf şekli F4-S1 canlı-smoke'ta doğrulanacak.
- Recon workflow `wf_e4d634ca-298`; strip workflow `wf_d72172e6-6dd`.
