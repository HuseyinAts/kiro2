## Session Handoff — 2026-07-26 (F4 kapanış + #415 A11y/WCAG A/B/C tamamlandı)
**Branch:** feature/self-evolution-optimization · **PUSH GEREKİYOR** (commit `70910dbdc` henüz push edilmedi)
**Son commit:** 70910dbdc (#415 A/B/C — layout kısayolları + form label + modal focus-trap)
**Frontend docker :3000 + backend:8000:** tüm zincir DEPLOY, healthy.

### #415 A11y/WCAG TAMAMLANDI (A/B/C; D ayrı bırakıldı)
Discovery (Explore agent) 4 alt-iş buldu, kullanıcı A+B+C onayladı, D (OSB
backend-bağlama — backend REST yüzeyi var ama frontend hiç çağırmıyor, 3 yetim
UI mevcut) ayrı büyük görev olarak bırakıldı.
- **A**: RoleBasedLayout'a Alt+M/Alt+N kısayolları + reduced-motion'a saygılı
  scroll-to-top FAB (AccessibleLayout dead-code'dan taşındı, kod zaten yazılıydı).
- **B**: 6 dosyada ~17 alan aria-invalid/label boşluğu kapatıldı (ScoreCalculator
  11 alan sibling-label kopukluğu, LearningPathMapPage 3 alan hiç label yoktu,
  3× analytics sayfası yorum-etiket).
- **C**: 2 modal focus-trap boşluğu — **BadgeEarned.tsx gerçek bug**: modal modda
  hiç focus-trap yoktu (Tab arka plana kaçıyordu), `useFocusTrap` hook'uyla
  düzeltildi + regresyon testi eklendi. ImageZoomModal.tsx'e role=dialog+aria-modal.
- Gate: tsc 0, scoped eslint 0 yeni hata, yeni test 2/2 PASS, canlı Playwright
  E2E (Alt+M/N + scroll-to-top doğrulandı, /parent/dashboard).
- **PUSH BEKLİYOR** — bir sonraki adım: push onayı al.

### YENİ BULGU (26 Tem) — HesapKurtarmaPage + OnboardingPage MOUNT EDİLMEDİ (kullanıcı kararı)
"GirisPage iç linkleri" görevi araştırıldı, ikisi de VeliBaglamaPage ile AYNI
kategoride çıktı (basit wiring değil, güvenlik-hassas mimari boşluk):
- **HesapKurtarmaPage** (`/hesap-kurtarma`): `kodGonder()` gerçek `POST /auth/recover`'ı
  çağırıyor ama bu path backend'de YOK (sadece alakasız `/2fa/recovery/*` MFA-kurtarma
  + gizli `/reset-password` var, grep ile doğrulandı). `dogrula()` (kod-doğrulama) ve
  `sifreGuncelle()` (şifre-güncelleme) adımları HİÇBİR backend çağrısı yapmıyor — her
  6 haneli kodu ve "güçlü" görünen her şifreyi kabul edip "Şifren güncellendi" diyor,
  gerçekte HİÇBİR ŞEY değişmiyor. Canlıya alınsaydı kullanıcı hesabına erişemeyip
  şifresinin değiştiğini sanacaktı — aktif olarak yanıltıcı/güvenlik riski.
- **OnboardingPage** (`/onboarding`): kod içi yorum "live'da yerleştirme /cat/next"
  diyor ama `/cat/next` backend'de HİÇ YOK (grep sıfır sonuç). Component mode fark
  etmeksizin HER ZAMAN sabit 6 mock soru gösteriyor (`kiroData.catBankMat`), cevabı
  istemcide JSON'daki gömülü doğru cevaba göre değerlendiriyor — mock/live ayrımı
  kodda YOK, her ikisi de aynı sahte akış.
**Karar (AskUserQuestion):** İkisi de MOUNT EDİLMEDİ, kapsam-dışı belgelendi (VeliBaglamaPage
ile aynı muamele). Backend-build veya ürün kararı ayrı bir sprint gerektirir. Kod
değişikliği yapılmadı.

### Push-öncesi gate notu (önemli — tekrar oturumda hatırla)
Repo-geneli `vitest` suite'i (86+ dosya) bu oturumda 3 denemede de tamamlanamadı
(OOM + yanlış pool-config denemesi + kill) — kronik ortam kısıtı, kod değişikliğiyle
ilgisi yok kanıtlandı (45 node.exe süreci incelendi, HİÇBİRİ vitest artığı değildi —
hepsi MCP server'ları örn. Playwright/context7/postgres, muhtemelen önceki
oturumlardan birikmiş). Kullanıcı onayıyla **dar-ama-eksiksiz kapsamlı gate**
(değişen her şeyi kapsayan) ile push edildi: tsc proje-geneli 0 hata, kanon-lint
0 ihlal, kiro-suite 512/512 (2 kez), backend offline_sync 9/9 + ruff temiz, 3 yeni
rotada canlı Playwright E2E. Sonraki oturumda repo-geneli suite tekrar denenebilir
(muhtemelen host RAM baskısı geçicidir) ama BU push için blokaj değildi.

### Kod zinciri (bu uzun oturumda, sırayla — "sırayla tümünü yap" + "DEVAM ET")
b8626be6a(F4-S0) → c9c771e0e(Düello) → 24cac0bcc(login wiring) → 14f53afe1(full-bleed)
→ d1ffa2cde(AI fix) → 05ccfae1f(A2.2b /login mount) → 91d64d4b6(F4-S1c student_id)
→ 0cfeda660(offline sync backend fix) → 51ff2da78(mapVeliCocuk fix)
→ d7c4edc43(giveConsent fix) → d60e453f1(#424: /offline mount)
→ **8468357f8(#425: /interaktif-cozum mount)** → **22f65d21d(#426: /veli mount)**

### #424-#426 TAMAMLANDI (bu turda) — full-bleed mount üçlüsü

**#424 `/offline`** (CevrimdisiPage): `getCevrimdisiDurum()` → `/offline/sync-status`
fix + `last_sync_at`→saat etiketi + kuyruk/paketler dürüst `[]`. EmptyState eklendi.
Canlı E2E: "Son eşitleme: 18:08" + "Bağlantı geldi" bandı gerçek backend'den.

**#425 `/interaktif-cozum`** (InteraktifCozumPage): backend-hazırlık kontrolü GEREKMEDİ
— saf istemci-matematik (parabol y=ax²+bx+c), backend/store bağımlılığı sıfır
(dosya başlığında kanon istisnası olarak belgelenmiş). Net-new rota (önceden
404'tü). Canlı E2E: kaydırıcı etkileşimi doğrulandı (a:1→-1 → denklem/tepe/KEŞFET
metni anında güncellendi).

**#426 `/veli`** (VeliPaneliPage — VeliBaglamaPage DEĞİL): backend-doğrulama ile
ayrıştırıldı (Explore agent + manuel grep, `backend/api/parent.py` çapraz kontrol):
- **VeliPaneliPage** → `getVeliDashboard()` = `/parent/dashboard` + `/parent/children`
  + `/children/{id}/performance`, ÜÇÜ DE backend'de var + loader'da kayıtlı.
  VeliBaglamaPage'den tam bağımsız (prop'suz). **Mount edildi.**
- **VeliBaglamaPage** → MOUNT EDİLMEDİ, mimari blok kesin doğrulandı:
  `verifyLinkCode` (veli-taraf 6-hane kod) backend'de HİÇ YOK (grep sıfır sonuç);
  gerçek bağlama mekanizması TAMAMEN FARKLI (authenticated veli + çocuk email,
  `POST /parent/children`) — kodsuz akış. `approveRelation` (öğrenci onay PUT)
  GERÇEKTEN VAR ama onu tetikleyecek keşif-GET'i yok. Product/mimari karar
  gerektirir (kod-akışı backend'e build mi edilsin, kiro email-akışına mı
  uyarlansın) — wiring kapsamı dışında, net belgelendi (AskUserQuestion'a GEREK
  KALMADI, teknik kanıt kararı kendiliğinden netleştirdi).
Canlı E2E (veli@kiro2.com): `/parent/dashboard`+`/parent/children` ikisi 200,
EmptyState doğru ("Henüz bağlı bir çocuk hesabı yok" — test hesabında gerçekten yok).

### Gate (üç görevde de aynı)
tsc 0 · mevcut testler PASS (offline: 79/79 dosya·512/512 test; diğer ikisi
kendi mevcut suite'leri regresyon-sız) · build ✓ · docker rebuild+redeploy ✓ ·
canlı Playwright E2E (gerçek seed hesap, gerçek backend çağrıları doğrulandı).

### Operatör/mimari notlar
- **DB migration deseni öğrenildi**: `kiro2_app` (RLS non-superuser) DDL yapamıyor — host native `postgres` superuser + `DATABASE_URL_SYNC` env-override (`.env` DEĞİŞTİRİLMEDİ) ile migration uygulandı.
- **Git Bash + docker path-conversion tuzağı**: mutlak-yol argümanları MSYS tarafından Windows yoluna çevriliyor → `MSYS_NO_PATHCONV=1` prefix zorunlu.
- **PWA service worker + `page.goto()` yarış durumu (Session 424 dersi)**: hızlı ardışık navigate+SW-unregister döngülerinde geçici olarak STATİK `public/offline.html` (PWA-fallback, farklı dosya) görünebilir — gerçek bug değil, test-harness artefaktı. Smoke test'te `page.goto()` yerine giriş sonrası **in-app client-navigasyon** (`history.pushState`+`popstate`) tercih et; bu üç mount'ta da (offline/interaktif-cozum/veli) bu yöntemle temiz sonuç alındı.
- **SideNav href kaynak-of-truth**: yeni bir kiro ekranı mount ederken `kiro/ui/SideNav.tsx`'teki role-bazlı `href` listesini kontrol et — rota adı orada zaten kanonikleşmiş olabilir (örn. `/veli` "Genel Bakış" href'i, VeliPaneliPage'in kendi iç linklerinde YOKTU ama SideNav'da vardı).

### Bilinen kapsam-dışı gap'ler (dokunulmadı, net belgelendi)
- `verifyLinkCode`/6-hane-kod akışı: backend'te yok, ürün kararı gerekiyor (kod-akışı korunsun mu, e-posta-akışına mı geçilsin). VeliBaglamaPage mount EDİLMEDİ.
- ParentDashboard KPI/haftalık/roi/premium alanları: backend şemasında hiç yok, backend-build gerektirir.
- Çevrimdışı `paketler`/`kuyruk` kavramları: backend veri modelinde yok — ayrı ürün-tasarım kararı.
- GirisPage iç linkleri (`/hesap-kurtarma`, üst `/onboarding`) henüz mount değil.

### Sonraki Adımlar (F4 devam ederse)
F4-S2'nin planlanan tüm net-new full-bleed mount'ları (#424/#425/#426) TAMAMLANDI.
Kalan iş kapsam-dışı gap'ler listesinden — her biri ayrı backend-build veya ürün
kararı gerektiriyor, "wiring" sprintinin doğal sonu. Sonraki oturum muhtemelen:
1. Yukarıdaki backend-build item'larından birine karar + kapsamlama.
2. Veya F4 kapanışı: tam gate + push onayı iste.

### Seed test kullanıcılar
test@kiro2.com (STUDENT, `STU_d04020744222`) · ogretmen@/veli@/admin@kiro2.com — hepsi `Kiro2Beta2026@x`.
