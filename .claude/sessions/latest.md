## Session Handoff — 2026-07-26 (G4-B)
**Branch:** feature/self-evolution-optimization
**Son commit:** d6ff32d5d fix(cat): omit ("Emin değilim") artık θ'ya yanlış olarak girmiyor
**Push:** EDİLDİ (f8339ffa6..d6ff32d5d)

### Yapilanlar
- **G4-B `/cat/next`** `125fb87f1` — `app/api/cat.py` (+`POST /next`, `get_optional_user`, `cat_sid` HttpOnly çerez, `@limiter.limit("30/minute")`) + `app/schemas/cat_schemas.py` (4 şema, TR camelCase sözleşme paritesi) + `app/services/cat_session.py` (`is_guest`, `pending_question_id`, `max_items`/`se_threshold`, `topic_hierarchy` JOIN, `fetch_question_detail`) + `app/services/irt_engine.py` (6 panel türevi) + `tests/unit/test_cat_next_adapter.py` (32 test, YENİ).
- **Pre-existing P0 fix:** `app/api/cat.py` FastAPI 0.103.2'de import edilemiyordu (`abandon_session() -> None` + 204) → TÜM CAT router'ı kayıtsız, `/api/v1/cat/*` 404. GF13 `!= 500` dediği için false-green'di.
- **Adversarial (5 skeptik, 37 bulgu)** sonrası kapatılanlar: cevap-anahtarı oracle'ı (P0), misafir oturum sızıntısı (P0), rate-limit yokluğu (P0), şık indeks kayması (P1), sessiz misafire düşme (P1).

- **Omit fix** `d6ff32d5d` — `skip_question()`: omit θ'ya girmez (12/12 omit → prior, güvenilirlik %0), tekrar sunulmaz, bütçeden düşer. `kalanTahmini` bütçesi de düzeltildi (yeni test yakaladı).

- **KaTeX + mount** `6a97a5c17` + `30f6752a5` — MathText testsizdi → 7 test (gerçek DB dizeleri). `kiro/ui/MathText.tsx` sarmalayıcı (`inline` zorlar, dış import tek dosyada). AdaptifTestPage stem+şık sarmalandı. `/yerlestirme` mount (ProtectedRoute['ogrenci'] + full-bleed); `/cat` DOKUNULMADI. kiro süiti **80 dosya/518 test PASS**, tsc temiz, kanon-lint 0 ihlal.

- **Görsel + a11y doğrulama** `53c9c3762` — Storybook `Formullu` story (gerçek DB dizeleri) + Chromium ölçümü. **Bulgu:** KaTeX MathML `<annotation>` ham TeX'i erişilebilir ada sokuyordu (4 şıkkın 2'si); `.k-math .katex annotation{display:none}` ile 2→0. Ayrıca doğrulandı: iç içe `<p>`=0, 390px'te taşma YOK, buton 58px, `.katex` 20.57px=1.21×17px.

- **CANLI E2E `/api/v1/cat/next`** — Docker stack (27 Tem 04:0x). Image 2026-07-04 tarihliydi → 404; kanonik döngü (docker cp 4 dosya + pyc temizlik + restart + 22sn) ile yamalandı. Sonuçlar:
  - misafir ilk çağrı **200** (auth YOK), `Set-Cookie: cat_sid=…; HttpOnly; Max-Age=3600; Path=/api/v1/cat; SameSite=lax` (dev'de Secure yok — doğru), gerçek havuzdan madde (`konu=Geometri`, 5 şık), **`dogru` sızıntısı YOK**
  - **oracle denemesi (yabancı maddeId) → 409** ✓ P0 fix canlıda çalışıyor
  - gerçek cevap → 200, madde=1, θ=0.2706 SE=0.9538 güvenilirlik %9 kalan=11
  - **omit (secim=null)** → madde ARTMADI (1), θ **DEĞİŞMEDİ** (0.2706→0.2706), bütçe 11→10 ✓ tasarım birebir
  - **misafir kalıcı yazım: 6 tabloda da 0 satır** (kiro2_cat_sessions, student_abilities, xp_transactions, user_theta, kiro2_learning_events, streaks)
  - Redis'te `cat:active:guest:<uuid>:MATEMATIK` mevcut → misafir kimliği korunuyor (oturum sızıntısı fix'i canlı doğrulandı)

- **Sessiz-404 sınıfı KAPATILDI** `66154afc5` + `fe7fafc9f` — `api/alternative_solutions_api.py` 4 fonksiyonda defaultsuz-parametre-defaultludan-sonra → SyntaxError → router hiç yüklenmiyordu (**8 endpoint 404**). Fix + `tests/test_router_registration.py::test_mapped_routers_are_importable` (ROUTER_MAPPING'deki her modülü gerçekten import eder). **Mutasyon testiyle kanıtlandı**: iki hata sınıfında da (SyntaxError · FastAPI 204 assert) bozunca KIRMIZI, düzeltince YEŞİL.
- **Image kalıcılaştırıldı** — `docker compose build backend` + `up -d --no-deps` (image 2026-07-27T04:15). `docker cp` yaması artık yok; rebuild sonrası `/api/v1/cat/next` **200**, `/api/v1/questions/alternatives/health` **200**, loglarda import hatası **yok**.
- **CAT 204 hatasının gerçek mekanizması**: `-> None` TEK BAŞINA yetmiyor; `from __future__ import annotations` ile BİRLİKTE gerekiyor (ölçüldü). cat.py'deki uyarı yorumu düzeltildi.

- **Yüzdelik aşırı-özgüveni** `cbea98413` — `theta_percentile` ölçüm hatasını yok sayıyordu: E[Φ(θ)] = Φ(θ̂/√(1+SE²)). Etki: θ̂=2.0/SE=0.95'te "üst %2" → "üst %7". Canlı doğrulandı (rebuild sonrası θ=0→%50, θ=-0.46/SE=0.90→%63).
- **Görev 2 Offline KAPANDI** `bec215698` — kullanıcı kararı: çöz-döngüsü YAPILMAYACAK, dürüst yüzey son hâl. Ama yüzey dürüst DEĞİLDİ (ölçüldü: kiro `live()`'da offline yolu yok, `backgroundSyncService` hiçbir cevap yolunda değil, kuyruk sayacı backend'den geliyor, IndexedDB README'de işaretsiz) → çevrimdışı cevap **kayboluyor** ama ekran "hiçbir şey kaybolmaz" diyordu. 2 cümlelik kopya düzeltmesi + test güncellendi.

### Fail Eden Testler
- YOK. 34/34 yeni + bağımlı modüller dahil 166/166 pass. Ruff: değişen satırlarda 0 (kalan 2 B905 `_persist_session_to_db` pre-existing).

### Engelleyiciler
- Redis + Docker DOWN → canlı E2E yapılamadı (PG 5434 UP, SQL'ler canlı doğrulandı).
- ~~Ekran blocker (LaTeX)~~ **ÇÖZÜLDÜ** — `30f6752a5`. Kalan: gerçek tarayıcıda tipografi/taşma gözle kontrolü.
- Adversarial 37 bulgunun P0/P1'leri kapatıldı; kalan P2'ler (SE çubuğu ekranda %0'da çakılı, "tahmin yeterince kararlı" metni gerçek dışı, kalibre edilmemiş parametreler üzerinden nüfus-referanslı iddialar) **ekran/kalibrasyon işi** — backend adaptörü değil.

### Sonraki Adimlar (maks 5)
1. **`docker compose build backend`** — canlı doğrulama `docker cp` ile yapıldı, GEÇİCİ. Container yeniden yaratılırsa 2026-07-04 image'ına döner ve `/cat/next` yine 404 olur. Kod git'te, rebuild kalıcılaştırır.
2. **IRT kalibrasyonu ERTELENDİ (veri yok)** — ölçüldü: 110,858 aktif sorudan yalnız 263'ünde yanıt var, **hiçbirinde ≥30** (2PL ~100, 3PL ~200 ister). Parametreler uzun süre bootstrap kalacak; panelin nüfus-referanslı iddiaları bu kısıtla okunmalı.
3. **Çevrimdışı çöz-döngüsü** — kapsam dışı bırakıldı (karar). Yapılacaksa: kiro `live()`'a kuyruk + IndexedDB + SW sync; kopya da geri alınmalı.

### Kararlar
- **G4-A `/auth/recover` ERTELENDİ** (kullanıcı kararı, 26 Tem): e-posta/SMTP altyapısı repo'da yok → işlevsel kurtarma yazılamaz. Endpoint-stub da KONMAYACAK (çalışmayan uç, çalışıyor sanılır). SMTP geldiğinde açılacak. **G4 (C→B→A) bu kararla KAPANDI.**
- Oturum kimliği = anonim HttpOnly `cat_sid` çerezi (frontend'e 0 dosya dokunuldu, sözleşme birebir).
- Yerleştirme = 12 madde + SE≤0.45. Ölçüm: havuz a≈1.00/c=0.20/b∈[-1.05,0.89] → motorun SE 0.35 eşiği 20 maddede bile yakalanmıyor (SE≈0.51). 12 sayısı panelin θ-SVG'siyle de uyumlu (`cx=20+(i/11)*300`).
- `app/api/cat.py`'de `from __future__ import annotations` YASAK — slowapi wrapper'ı `__globals__`'ı değiştirdiği için gövde parametresi query'ye düşüp 422 üretiyor.
- Keşif devir notunu çürüttü: **OnboardingPage `/cat/next` çağırmıyor** (statik JSON + istemci-taraflı puanlama); tek tüketici AdaptifTestPage ve o da mount edilmemiş.
