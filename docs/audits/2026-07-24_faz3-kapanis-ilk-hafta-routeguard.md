# KIRO2 — Faz 3 KAPANIŞ (İlk Hafta + Route Guard) — 42/42 🎯

**2026-07-24** — Son iki auth-kalıntı: **İlk Hafta** ekranı (paper) + **route guard / rol yönlendirmesi** (`kiro/lib/routeGuard.ts` + GirisPage wiring). Keşif: elle (İlk Hafta DC + routing/rol infra recon). **Faz 3 ekran-portu TAMAM (42/42).**

## İlk Hafta (Grup 1 Auth — "İlk 7 Gün" yayı)
- **Tema:** paper (DC-kanıtlı #F7F4EF; "Momentum Haftası / İlk 7 Gün" = tasarlanmış yay, kutlama-hub değil). SideNav yok, ortalı tek-kolon (max 960).
- **İçerik:** header + ilerleme-özet kartı (currentDay/yüzde/CTA "Bugünü tamamla →"/bugun) + 7-gün yatay-scroll yay (done/current/lock düğümler, current pulse RM-gate) + 4 milestone kart (BUGÜN/YARIN/GÜN7/NEDEN, DC birebir).
- **Sunucu-otorite:** `getIlkHafta()` (currentDay 3/7, odakKonu mastery-sorted, tier, zayifAtom, gün-durumları). Skeleton + ErrorState (DC'de yok, çıkarım). Öğrenci SEN; "Acelesi yok" absence-dili korundu.
- **Kanon-watch (uygulandı):** DC coral GRADYANLARI (#FF8A5B→#FF5E7E) → solid #C2452B; #E0593F → coralTextOnLight; done yeşil/gün7 amber AA-sertleştirildi; pulse+view-transition → useReducedMotion/.k-calm gate.

## Route Guard / Rol Yönlendirmesi
- **Gerçek durum:** kiro/'da React Router YOK, `Persona`'da rol alanı YOK, GirisPage giriş-sonrası CTA **no-op** idi (boşluk).
- **Port (mock-katmanı):** `kiro/lib/routeGuard.ts` — `KiroRol='ogrenci'|'veli'|'ogretmen'` + `ROL_LANDING` map (öğrenci→/panel · veli→/veli · öğretmen→/ogretmen) + `roleLanding(rol)` + **`AuthGate`** (prop-enjekte `onRedirect`; sabit useNavigate YOK → router'sız test/story korunur; rol=null→/giris). Rol kaynağı **ayrı** (`getRol()` + kiro-data.rol; **`Persona` API-sözleşmesine dokunulmadı**).
- **GirisPage wiring (additive):** `onLanding?`+`rol?` prop; giriş-tamam CTA → `roleLanding(rol)`, **kayıt-tamam → /onboarding** (seviye-ölçüm); `getRol` giriş-SONRASI (pre-auth 401 önleme). Prop yoksa eski no-op korunur (regresyonsuz).
- **Faz 4 (yorumla mühürlü):** yeni guard İCAT ETME → mevcut `ProtectedRoute` + `getRedirectPathByRole` reuse; TR/EN rota drift'i tek kanona hizala.

## Adversarial (22 ajan, 4 boyut) — 17 doğrulandı / 14 unique / 1 phantom (0 P0)
- **major (AA):** YARIN tag #3B6FD4 4.16:1 → #3163C4 (4.95:1). **Guard/Persona TEMİZ** (AuthGate koşulsuz-redirect phantom'u doğru elendi — redirect-gate, content-gate değil).
- **minör fix:** İlk Hafta lock günler `faded3`→`ink.muted` (2.0:1→5.1:1); gün-düğümü srOnly durum metni (renk-yalnız değil); 7-gün şerit tabIndex/role (klavye-scroll WCAG 2.1.1); progress role=progressbar; **MSW `/onboarding/ilk-hafta` handler eklendi**; **GirisPage kayıt-CTA → /onboarding** (wiring'in açtığı yanlış-landing) + getRol post-auth. +test (Error/Skeleton/responsive).
- **Ertelenen (pre-existing, cerrahi kapsam dışı):** GirisPage aria-invalid / 'tamam' focus-move / bazı box-sizing / Sunrise SVG #FF6F5C — ayrı a11y-polish işi.

## Kapı (otoriter, bağımsız)
kanon **0 ihlal** (16 uyarı pre-existing) · scoped tsc **0** · vitest **71 dosya / 489 test PASS** (472→489, +17) · **breakpoint 0 FAIL / 490** · axe temiz.

---

## 🎯 FAZ 3 EKRAN-PORTU TAMAM — 42/42
Grup 1-9 tümü portlu (+ Çözüm Paylaş MVP-dışı; Tasarım Dili / E-posta Bildirim referans-yüzeyi; Kaygı Ölçüm / Moderatör Kılavuzu kapsam-dışı).
**Paylaşılan varlıklar:** QuestionCard · WeeklyActivityBars · VeliYonlendirmeKarti · ui/Switch · ayarStore · routeGuard · ChatBubble (ilk gerçek tüketici).
**Sonraki (roadmap C/D):** Ödev Atama↔Ödevlerim E2E · push (onayla) · full frontend derleme (proje-geneli tsc + vite build) · Faz 4 backend wiring (AI SSE / billing PSP / Çevrimdışı / Bildirim / Ayarlar preferences / route guard→ProtectedRoute).
