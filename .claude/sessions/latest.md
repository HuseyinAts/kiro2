## Session Handoff — 2026-07-25 (F4-S1a + full-bleed layout — CANLI PASS)
**Branch:** feature/self-evolution-optimization · **PUSH YOK**
**Son commit:** 14f53afe1 (full-bleed layout)
**Kod zinciri:** b8626be6a (F4-S0) → c9c771e0e (Düello live) → 24cac0bcc (login wiring) → 14f53afe1 (full-bleed)
**Frontend docker :3000:** F0+A1+A2.1+full-bleed DEPLOY (rebuild edildi, healthy).

### 🎯 CANLI KANITLAR (docker :3000 + native PG18 5434 + backend)
- **Backend cookie e2e:** login/secure→200+httpOnly cookie · /auth/me→200 · /api/v1/duel/rating→200.
- **Frontend e2e (Playwright):** login (test@kiro2.com) → cookie → /duel → **kiro DuelloPage render → POST /api/v1/duel/matchmake 200**.
- **Full-bleed:** /duel → App shell YOK (kiro arena tam-ekran) · /dashboard → App shell KORUNDU (scoped, regresyon yok).

### Yapılanlar (commit'li)
- **F4-S0** (b8626be6a): 3 blocker + merkezi config + 39 strip. 491/491.
- **A1 Düello live** (c9c771e0e): App /duel→kiro DuelloPage + /lig→/league. CANLI PASS.
- **A2.1 login wiring** (24cac0bcc): GirisPage onLogin/onVerify2fa/onRegister prop-enjekte + 2FA. 14/14. (Mount DEĞİL — A2.2b.)
- **Full-bleed** (14f53afe1): `kiro/kiroRoutes.ts` KIRO_FULLBLEED_ROUTES + RoleBasedLayout bypass (useLocation). CANLI PASS.

### ⚠️ Operasyonel ders (KRİTİK)
**PWA service worker cache**: frontend docker rebuild sonrası tarayıcı `workbox-precache` ile ESKİ bundle'ı servis eder → değişiklik görünmez. Smoke öncesi SW unregister + `caches.delete` ZORUNLU (veya hard-reload). Playwright: `navigator.serviceWorker.getRegistrations()→unregister` + `caches.keys()→delete` sonra reload.

### Seed test kullanıcılar (GF)
test@kiro2.com (STUDENT) · ogretmen@kiro2.com · veli@kiro2.com · admin@kiro2.com — hepsi şifre `Kiro2Beta2026@x`.

### Sonraki Adımlar
1. **A2.2b** — /login → GirisPage swap: kiro iç link hizala (/hesap-kurtarma→/forgot-password, /onboarding→/register) + register field-set (soyad/birth_date/rol/veli_email KVKK) + KiroLoginRoute wrapper + /login'i KIRO_FULLBLEED_ROUTES'a ekle (GirisPage zaten kendi kabuklu).
2. **F4-S1b** — AI frontend-fix: postSohbetMesaj/streamSohbet gövdesine student_id (persona.id) + getSohbet /sessions zarf-aç + mesaj ayrı uçtan çek. AI ekranları mount + KIRO_FULLBLEED_ROUTES.
3. **F4-S2+** backend yüzeyler: Çevrimdışı (offline modeli) · Veli (mapVeliCocuk child_name bug + ParentDashboard alanları) · KVKK (verify-code/consent — mimari karar).
4. Minor: /duel'de ara sıra 1 console error (fonksiyonel değil; matchmake retry olabilir).

### Kararlar
- Layout: kiro ekranları **full-bleed** (KIRO_FULLBLEED_ROUTES tek-kaynak; App.tsx <Route> + buraya path birlikte).
- baseUrl=origin · unwrapData lenient (canlı duel/parent RAW pydantic teyit).
- Docker FE deploy: `docker compose build frontend` + `up -d --no-deps frontend` + SW-cache temizle.
