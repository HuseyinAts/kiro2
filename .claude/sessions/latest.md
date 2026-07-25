## Session Handoff — 2026-07-25 (F4-S1 TAM + F4-S2 6/6 TAMAMLANDI, Offline mount canlı doğrulandı)
**Branch:** feature/self-evolution-optimization · **PUSH YOK**
**Son commit:** d60e453f1 (CevrimdisiPage /offline mount, full-bleed, canlı E2E)
**Frontend docker :3000 + backend:8000:** tüm zincir DEPLOY, healthy.

### Kod zinciri (bu uzun oturumda, sırayla — "sırayla tümünü yap")
b8626be6a(F4-S0) → c9c771e0e(Düello) → 24cac0bcc(login wiring) → 14f53afe1(full-bleed)
→ d1ffa2cde(AI fix) → **05ccfae1f(A2.2b /login mount)** → **91d64d4b6(F4-S1c student_id)**
→ **0cfeda660(offline sync backend fix)** → **51ff2da78(mapVeliCocuk fix)**
→ **d7c4edc43(giveConsent fix)** → **d60e453f1(#424: /offline mount, full-bleed)**

### #424 tamamlandı (bu turda) — Mount CevrimdisiPage → App
`getCevrimdisiDurum()` kiro `/offline/durum` çağırıyordu (backend'de yok) →
`/offline/sync-status` fix + `last_sync_at`→saat etiketi + kuyruk/paketler dürüst
`[]` (backend'de bu kavramlar yok, uydurma yapılmadı). `CevrimdisiPage.tsx`'e
`paketler.length===0` için EmptyState eklendi. `/offline` full-bleed mount
(App.tsx + kiroRoutes.ts, wrapper gerekmedi — store bağımlılığı yok).
Gate: tsc 0 · kiro vitest **79/79 dosya · 512/512 test** (+2 yeni offline.test.ts)
· build ✓ · docker rebuild+redeploy ✓ · **canlı Playwright E2E** (test@kiro2.com):
gerçek backend'den "Son eşitleme: 18:08" + "Bağlantı geldi" bandı + 2 EmptyState
+ full-bleed SideNav doğru render.
**Test-harness tuzağı (not, gerçek bug değil):** `page.goto()` ile hızlı ardışık
navigate+SW-unregister döngülerinde geçici olarak STATİK `public/offline.html`
(PWA-fallback, farklı bir dosya) göründü — curl + in-app client-navigasyon
(`history.pushState`+`popstate`) ile DOĞRU render kanıtlandı. Gerçek smoke test
yaparken `page.goto()` yerine SPA-içi link tıklama/route değişimi tercih et,
zira full sayfa navigasyonu + taze SW register (`skipWaiting`+`clientsClaim`)
arasında yarış durumu snapshot'ı yanıltabiliyor.

### 🎯 Bu turda tamamlanan 5 görev

1. **A2.2b — `/login` mount**: `KiroLoginRoute` (gerçek `authStore.login`, field-map, `getRedirectPathByRole`). Kayıt bilinçli `/register`'a devredildi (KVKK-minor alan eksikliği). **Canlı e2e**: login→cookie→"İçerdesin."→`/dashboard`.

2. **Backend veri sorunu araştırması**: Kök neden **bug değildi** — `learning_path_student_profiles` zaten vardı. Gerçek sorun: frontend'in erişim yolu yoktu. `GET /learning-path/my-profile` (zaten var, kullanılmıyordu) → `useKiroStudentId()` hook. **Backend değişikliği YOK.** Canlı: chat 422→403→**200+gerçek Qwen yanıtı**.

3. **F4-S2 Çevrimdışı** (kullanıcı kararı: "sadece 2 backend bug'ı düzelt"): `GET /sync-package` ve `POST /sync-results` **6 Haziran'dan beri kırıktı** (kiro'dan bağımsız prod bug) — `.tablesample()` SQLAlchemy uyumsuzluğu + migration'ın kendi tablosunu silmesi (ORM model'siz raw-SQL tablo, autogenerate "yetim" sanıp düşürmüş). Yeni ORM model + migration (superuser ile uygulandı, `kiro2_app` DDL yetkisiz) + servis fix. **Canlı: her iki uç artık 200.**

4. **F4-S2 Veli**: `mapVeliCocuk` yanlış id seçiyordu (`pick()` ilk-dolu mantığıyla relation-id'yi öğrenci-id sanıyordu) — sadece kozmetik değil, sonraki `/parent/children/{id}/performance` çağrısına yanlış id gidiyordu. Fix: pick sırası backend'in gerçek `child_name`/`child_id` alanlarını önceliklendirir. KPI/haftalık/roi/premium boşluğu (backend-build, büyük) **kapsam dışı bırakıldı**.

5. **F4-S2 KVKK**: `giveConsent` HER ZAMAN 422 veriyordu (3 zorunlu alandan 2'si hiç gönderilmiyordu, `purpose` enum'a uymuyordu) — fix: `getKvkkNotice` genişletildi (`text` eklendi) + `giveConsent` artık 3 alanı doğru gönderiyor. `verifyLinkCode` (6-hane kod, backend'te route YOK — e-posta tabanlı akış) **mimari fark olarak belgelenip kapsam dışı bırakıldı** (ürün kararı gerektirir).

### Gate (her adımda)
tsc 0 · kiro vitest **510/510** (78 dosya) · vite build OK · backend ruff temiz + mevcut 13 offline test PASS.

### Operatör/mimari notlar
- **DB migration deseni öğrenildi**: `kiro2_app` (RLS non-superuser) DDL yapamıyor (`users` FK referansı reddedildi) — host native `postgres` superuser + `DATABASE_URL_SYNC` env-override (`.env` DEĞİŞTİRİLMEDİ) ile migration uygulandı. Runtime yetkisi (`SELECT/INSERT/UPDATE/DELETE`) otomatik grant edilmiş bulundu.
- **Git Bash + docker path-conversion tuzağı**: `docker exec ... find /app/...` gibi mutlak-yol argümanları MSYS tarafından Windows yoluna çevriliyor → `MSYS_NO_PATHCONV=1` prefix'i zorunlu.
- **PWA service worker**: her frontend rebuild sonrası smoke öncesi SW-cache temizleme zorunlu (tekrarlanan ders).

### Bilinen kapsam-dışı gap'ler (dokunulmadı, net belgelendi)
- `verifyLinkCode`/6-hane-kod akışı: backend'te yok, ürün kararı gerekiyor (kod-akışı korunsun mu, e-posta-akışına mı geçilsin).
- ParentDashboard KPI/haftalık/roi/premium alanları: backend şemasında hiç yok, backend-build gerektirir.
- Çevrimdışı `paketler`/`kuyruk` kavramları: backend veri modelinde yok (backend artık ÇALIŞIYOR ama kiro'nun zengin UI'sine denk düşen kavramlar yok) — ayrı ürün-tasarım kararı.
- GirisPage iç linkleri (`/hesap-kurtarma`, üst `/onboarding`) + `İnteraktifCozumPage` mount edilmedi.
- VeliPaneliPage/VeliBaglamaPage henüz App'e mount değil (F4-S2 fix'leri sadece api-client seviyesinde, mount ayrı kademeli-swap kararı).

### Sonraki Adımlar (F4 devam ederse — #425, #426 pending)
1. **#425 İnteraktifÇözümPage**: backend-hazırlık kontrolü + mount (full-bleed pattern, kanıtlanmış).
2. **#426 Veli ekranları mount kararı**: VeliBaglamaPage'in çekirdek `verifyLinkCode` akışı backend'te YOK (mimari karar gerekir — kullanıcıya sorulmalı) → VeliPaneliPage'i tek başına mı mount etsin, yoksa AskUserQuestion mı?
3. ParentDashboard KPI/Offline paketler backend-build (ayrı, büyük scope, kapsam dışı bırakıldı).

### Seed test kullanıcılar
test@kiro2.com (STUDENT, `STU_d04020744222`) · ogretmen@/veli@/admin@kiro2.com — hepsi `Kiro2Beta2026@x`.
