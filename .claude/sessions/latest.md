## Session Handoff — 2026-07-24 21:30
**Branch:** feature/self-evolution-optimization
**Son commit:** dbb455970 docs(kiro): Faz 4 backend wiring planı + kilitli kararlar
**Uncommitted:** temiz (origin `ccfe794e0` senkron; 2 local doc-commit önde: fe4ddfc03 + dbb455970, push YOK — standing kural)

### Yapılanlar
- 🎯 **Faz 3 ekran-portu TAMAM 42/42** — Şafak design system → `frontend/src/kiro/`. Bu oturum Grup 8 (S10-A/B/C) + Grup 9 (S11) + auth kalıntı (İlk Hafta + `kiro/lib/routeGuard.ts` + GirisPage `onLanding` wiring).
- Her sprint: keşif→build→adversarial→fix→breakpoint-gate→docs→commit. Raporlar: `docs/audits/2026-07-2{3,4}_*` (sprint10a/b/c, sprint11-grup9, faz3-kapanis).
- Roadmap C: full frontend derleme ✓ (proje-tsc 0 + `vite build` ✓) · **Ödev Atama↔Ödevlerim döngü E2E** `frontend/src/kiro/api/odev-dongu.test.ts` (postAtama→ortak-store→getAssignments; `configureKiroApi` structuredClone izolasyon) · **push ✓** (41 commit → origin ccfe794e0).
- 📋 **Faz 4 planı** `docs/plans/2026-07-24_faz4-backend-wiring-plan.md` — kararlar kilitli.

### Fail Eden Testler
- YOK. kiro suite: vitest **72 dosya / 491 test PASS** · kanon 0 ihlal · scoped tsc 0 · breakpoint 0 FAIL/490 · axe temiz. Proje-geneli tsc 0.

### Engelleyiciler
- YOK. (F4-S0 için dev-stack — backend+PG5434+Redis — F4-S1 canlı-smoke'ta gerekir; şu an kapalı.)

### Sonraki Adımlar (maks 5)
1. **F4-S0** (Faz 4 blocker+plumbing): B1 `live()`+`streamSohbet` → `credentials:'include'` (cookie, Bearer kaldır) · B2 baseUrl tek `/api/v1` (çıplak yolları normalize) · B3 `routeGuard`→`getRedirectPathByRole` hizala · merkezi `configureKiroApi` (main.tsx, VITE_API_URL) + ekran modül-başı mock çağrılarını kaldır · `live()` unwrapData + 401→/login + `kiro/api/mappers.ts` iskeleti. Gate: 491 mock testi bozulmaz (default mock).
2. **F4-S1** quick-win + uçtan-uca kanıt: AI·Düello·Çevrimdışı·Veli/KVKK live + kiro ekranları App.tsx İngilizce rotalara ProtectedRoute ile mount + GirisPage→authStore.login (cookie) + her yüzeye canlı-smoke.
3. F4-S2 çekirdek-döngü adaptör (soru/CAT/FSRS BFF — ürünün kalbi, en ağır) → F4-S3 roller → F4-S4 iş katmanı.
4. Opsiyonel: fe4ddfc03+dbb455970 doc-commit'lerini push (onayla).

### Kararlar (gelecek session tekrar tartışmasın)
- Faz 3 = mock-katmanı port BİTTİ; Faz 4 = gerçek backend wiring. Port zaten çift-kollu (mock|live) — F4 sıfırdan-yazma değil, blocker+adaptör.
- Faz 4 kilitli kararlar: **kademeli-swap** migrasyon (Modern* rota-rota) · auth=**cookie** (Bearer düşer) · baseUrl=**/api/v1** · ilk sprint **F4-S0+S1** · **Billing PSP ertele** (B2B invoice-tabanlı).
- Yeni guard İCAT ETME → `ProtectedRoute`+`getRedirectPathByRole` reuse. Persona API-sözleşmesi BİREBİR (rol ayrı kaynak `getRol`).
- Her yeni ekranda: faded/faded2/faded3 okunur-metin AA + inline `outline:none` odak-halkası + interaktif input minHeight≥44 taraması (5 sprint tekrarladı).
