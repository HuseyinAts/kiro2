## Session Handoff — 2026-07-24 (F4-S1a devam)
**Branch:** feature/self-evolution-optimization
**Son commit:** 24cac0bcc feat(kiro): F4-S1a GirisPage→authStore login wiring
**Commit zinciri (push YOK):** b8626be6a (F4-S0) · 95a5ebe6f (handoff) · c9c771e0e (Düello live) · 24cac0bcc (login wiring)

### Yapılanlar
- **F4-S0 TAMAM** (b8626be6a): 3 blocker (B1 cookie · B2 /api/v1 apiPath · B3 rota) + merkezi config + 39 ekran mock-strip. Gate 491/491.
- **F4-S1 keşif** (wf_6f30bedd-a95): plan matrisini kısmen çürüttü — gerçek quick-win YALNIZ Düello. AI frontend-fixable (student_id eksik→422 + session-unwrap). Çevrimdışı/Veli/KVKK **backend işi** (offline veri modeli / ParentDashboard alanları / KVKK verify-code+consent kontratı). Kullanıcı kapsamı **"Temel + Düello e2e"** seçti.
- **A1 Düello live** (c9c771e0e): App /duel → kiro DuelloPage (kademeli-swap) + /lig→/league. DuelloPage.test 6/6 · build ✓.
- **A2.1 login wiring** (24cac0bcc): GirisPage onLogin/onVerify2fa/onRegister prop-enjekte (fallback korunur) + 2FA TOTP adımı + ProtectedRoute.getRedirectPathByRole export. GirisPage.test 14/14 · tsc 0.

### Fail Eden Testler
YOK. (GirisPage.test 14/14, DuelloPage.test 6/6, tsc 0. Full kiro gate A2.2 başında koşulacak — beklenen 495/495.)

### Engelleyiciler / Operatör girdisi (A2.2 için)
1. **Test öğrenci kimliği** (email+şifre, seed'li) — canlı login-smoke (login→cookie→/duel) için ZORUNLU.
2. **FE serve kararı**: canlı UI-smoke için ya `docker compose build frontend`+redeploy (:3000 stale 43h) YA `npm run dev` (:3001, vite proxy). Hangisi?

### Sonraki Adımlar
1. **A2.2**: App.tsx `/login` → `KiroLoginRoute` wrapper swap (useAuthStore.login field-map {eposta,sifre}→{email,password} + verifyTwoFactor + onRegister→/register + onLanding→getRedirectPathByRole(store.user.rol)). Full kiro gate + build. **Canlı login-smoke** (cred gelince) → commit.
2. F4-S1b: AI yüzeyi frontend-fix (student_id + session-unwrap+mesaj-çekme).
3. F4-S2+: Çevrimdışı/Veli/KVKK backend işi (ayrı scope, migration + KVKK ürün kararı).

### Stack durumu (canlı, doğrulandı)
Docker stack AYAKTA: kiro2-backend healthy (/health 200, OpenAPI 1135 path, 4 yüzey uçları + /auth/login/secure + /auth/me[gizli] mevcut) · redis · frontend(:3000 STALE) · native PG18 5434 · celery. `/api/v1/auth/me` include_in_schema=False (phantom değil).

### Kararlar / Notlar
- baseUrl=origin (VITE_API_URL DEĞİL — cookie SameSite). unwrapData lenient DOĞRU (keşif teyit: sıkılaştırma duel/parent/kvkk/offline'ı kırardı).
- Rol tek-kaynak: gerçek user.rol (GET /api/v1/auth/me); kiro getRol wrapper'da atlanır (onLogin path). getRedirectPathByRole export edildi.
