## Session Handoff — 2026-07-24 (F4-S1a — Düello e2e CANLI PASS)
**Branch:** feature/self-evolution-optimization
**Son commit:** f53b8bf8c (handoff) · kod: 24cac0bcc (login wiring) · c9c771e0e (Düello live) · b8626be6a (F4-S0)
**PUSH YOK.** Frontend docker :3000 REBUILD edildi (F0+A1+A2.1 deploy, healthy).

### 🎯 UÇTAN-UCA KANIT (canlı, docker :3000 + native PG18 + backend)
- **Backend cookie e2e (curl):** login/secure→200 {user.rol:ogrenci} + httpOnly access/refresh cookie · /auth/me→200 · /api/v1/duel/rating→200 {elo:1200}.
- **Frontend e2e (Playwright):** ModernLoginPage login (test@kiro2.com / Kiro2Beta2026@x) → cookie → ProtectedRoute geçti (/learning-path) → **/duel → kiro DuelloPage CANLI render → POST /api/v1/duel/matchmake → 200 OK** → "rakip yok" (tek kullanıcı doğru).
- Bu, F4-S0'ı canlıda doğrular: B1 cookie (200≠401) · B2 /api/v1 · merkezi live config (origin) · A1 mount.
- **Seed test kullanıcı:** test@kiro2.com / Kiro2Beta2026@x (STUDENT, GF testlerinden; TEACHER=ogretmen@, PARENT=veli@, ADMIN=admin@, hepsi aynı şifre).

### Yapılanlar (commit'li)
- **F4-S0** (b8626be6a): 3 blocker + merkezi config + 39 strip. Gate 491/491.
- **A1 Düello live** (c9c771e0e): App /duel→kiro DuelloPage + /lig→/league. DuelloPage.test 6/6. **CANLI PASS.**
- **A2.1 login wiring** (24cac0bcc): GirisPage onLogin/onVerify2fa/onRegister prop-enjekte + 2FA TOTP + ProtectedRoute.getRedirectPathByRole export. GirisPage.test 14/14. (Henüz mount DEĞİL — A2.2b.)

### Fail Eden Testler / Engelleyiciler
YOK. (1 console error /duel'de — fonksiyonel değil, network 200 + render OK; ileride bakılabilir.)

### Sonraki Adımlar
1. **Layout stratejisi** (kademeli-swap kritik): kiro ekranları App ModernLayout kabuğu İÇİNDE render oluyor (full-bleed tasarıma aykırı). Karar: kiro rotaları layout-bypass mı, App kabuğu mu? Tüm kiro mount'ları etkiler.
2. **A2.2b** — /login → GirisPage swap: kiro iç linkleri (/hesap-kurtarma→/forgot-password, /onboarding→/register) hizala + register field-set (soyad/birth_date/rol/veli_email KVKK) + KiroLoginRoute wrapper (login({email,password}) + verify2fa + onLanding→getRedirectPathByRole(store.user.rol)).
3. **F4-S1b** — AI yüzeyi frontend-fix: postSohbetMesaj/streamSohbet gövdesine student_id (persona.id) + getSohbet /sessions zarf-aç ({success,sessions}) + mesaj ayrı uçtan çek.
4. F4-S2+ backend yüzeyler: Çevrimdışı (offline veri modeli) · Veli (mapVeliCocuk child_name/child_id bug + ParentDashboard alanları) · KVKK (verify-code/consent kontratı — mimari karar).

### Kararlar / Notlar
- baseUrl=origin (VITE_API_URL DEĞİL). unwrapData lenient DOĞRU (canlı duel/parent RAW pydantic zarfsız — teyit edildi).
- Docker: `docker compose build frontend` + `up -d --no-deps frontend` (:3000). Native PG18 5434 (docker pg15 çakışması YOK — footgun'dan kaçınıldı).
- Keşif workflow'ları: F4-S1 recon wf_6f30bedd-a95.
