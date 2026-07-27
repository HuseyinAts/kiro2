## Session Handoff — 2026-07-27 07:50
**Branch:** feature/self-evolution-optimization
**Son commit:** 610f20350 chore(kiro): handoff — offline kararı + yüzdelik fix + kalibrasyon ölçümü
**Uncommitted:** temiz (17 commit, f8339ffa6..610f20350 push edildi)

### Yapilanlar
- **G4-B `/cat/next`** `125fb87f1` — `backend/app/api/cat.py` (+POST /next, `get_optional_user`, `cat_sid` HttpOnly çerez, `@limiter.limit("30/minute")`) + `app/schemas/cat_schemas.py` (4 şema, TR camelCase) + `app/services/cat_session.py` (`is_guest`, `pending_question_id`, `max_items`/`se_threshold`, `topic_hierarchy` JOIN) + `app/services/irt_engine.py` (6 panel türevi) + `tests/unit/test_cat_next_adapter.py` (37 test)
- **Pre-existing P0 — CAT router hiç yüklenmiyordu** `125fb87f1` — `app/api/cat.py` FastAPI 0.103.2'de import edilemiyordu → `/api/v1/cat/*` tamamı 404. GF13 `!= 500` dediği için false-green'di
- **Adversarial (5 skeptik, 37 bulgu) P0'ları** `125fb87f1`+`d6ff32d5d` — cevap-anahtarı oracle'ı (`pending_question_id` bağlama, yabancı maddeId→409), misafir oturum sızıntısı, rate-limit yokluğu, şık indeks kayması, omit puanlaması (`cat_session.skip_question`)
- **`api/alternative_solutions_api.py`** `66154afc5` — 4 fonksiyonda defaultsuz param defaultludan sonra → SyntaxError → router yüklenmiyordu, **8 endpoint 404**
- **Sessiz-404 sınıfı kapatıldı** `fe7fafc9f` — `tests/test_router_registration.py::test_mapped_routers_are_importable`; **mutasyon testiyle kanıtlandı** (iki hata sınıfında da bozunca KIRMIZI, düzeltince YEŞİL)
- **KaTeX + mount** `6a97a5c17`+`30f6752a5` — `components/ui/MathText.test.tsx` (7 test, gerçek DB dizeleri) + `kiro/ui/MathText.tsx` (inline zorlar) + `kiro/screens/AdaptifTestPage.tsx` stem+şık + `/yerlestirme` mount (`App.tsx`, `kiro/kiroRoutes.ts`)
- **KaTeX a11y sızıntısı** `53c9c3762`+`e5b889aff` — `components/ui/mathText.css` `.katex annotation{display:none}`; ham TeX erişilebilir ada giriyordu (Chromium ölçümü 2→0), **6 yüzey** (5 sınav arayüzü + kiro)
- **Yüzdelik aşırı-özgüveni** `cbea98413` — `irt_engine.theta_percentile` artık E[Φ(θ)]=Φ(θ̂/√(1+SE²)); θ̂=2.0/SE=0.95'te "üst %2"→"üst %7"
- **Çevrimdışı kopya** `bec215698` — `kiro/screens/CevrimdisiPage.tsx:39,259` tutamayacağı söz veriyordu (çevrimdışı cevap KAYBOLUYOR ama "hiçbir şey kaybolmaz" diyordu)
- **Canlı E2E + image kalıcı** — `docker compose build backend`; misafir 200+çerez, oracle 409, omit θ değişmiyor, misafir kalıcı yazım 6 tabloda 0

### Fail Eden Testler
- **Exam süiti 16 fail** (`tests/unit` içindeki `src/components/Exam` karşılığı) — **PRE-EXISTING**, stash'li/stash'siz baseline karşılaştırmasıyla doğrulandı, benim değişikliklerimden DEĞİL
- Dokunulan her şey yeşil: adapter 37, kiro süiti 80 dosya/518 test, router_registration 3, bağımlı backend modülleri 92

### Engelleyiciler
- `tests/unit` tam süiti (10,184 test) 600s'de bitmiyor — ölçek sorunu, takılma değil (toplama yalnız 28s)

### Sonraki Adimlar (maks 5)
1. **IRT kalibrasyonu — ERTELENDİ, veri yok:** 110,858 aktif sorudan 263'ünde yanıt var, **hiçbirinde ≥30** (2PL ~100, 3PL ~200 ister). Panelin nüfus-referanslı iddiaları bu kısıtla okunmalı
2. **`AdaptifTestPage` görsel ince ayar** — `.katex` 20.57px = 1.21×17px (KaTeX optik ölçeği, kasıtlı bırakıldı); tasarım isterse `.k-math` üzerinden ayarlanır
3. **Çevrimdışı çöz-döngüsü** — kapsam dışı (karar). Yapılırsa: kiro `live()`'a kuyruk + IndexedDB + SW sync; `CevrimdisiPage` kopyası geri alınmalı
4. **#270 GitHub Actions / #390 Dependabot** — operatör (gh CLI kurulu değil)
5. `git stash@{0}` "pre-yolo checkpoint" duruyor (70,797 dosya) — gerekmiyorsa `git stash drop`

### Kararlar (gelecek session tekrar tartismasin)
- **Oturum kimliği = anonim HttpOnly `cat_sid` çerezi** — `CatNextResult` oturumId dönmüyor; frontend'e 0 dosya dokunuldu, sözleşme birebir korundu
- **Yerleştirme = 12 madde + SE≤0.45** — ölçüm: havuz a≈1.00/c=0.20/b∈[-1.05,0.89] → motorun SE 0.35 eşiği 20 maddede bile yakalanmıyor (SE≈0.51). 12 sayısı panelin θ-SVG'siyle uyumlu (`cx=20+(i/11)*300`)
- **Omit = "uygulanmadı"** — yanlış saymak dürüstlüğü kör tahminden ağır cezalandırıyordu (θ_true=+1.0, 6/12 omit → θ̂=-1.04 vs -0.56)
- **`app/api/cat.py`'de `from __future__ import annotations` YASAK** — slowapi wrapper'ı `__globals__`'ı değiştirir, gövde parametresi query'ye düşüp 422 üretir. Ayrıca `-> None` + 204 hatası da YALNIZ bu import varken doğuyor (ölçüldü)
- **G4-A `/auth/recover` ERTELENDİ** — SMTP yok; endpoint-stub da konmayacak (çalışmayan uç çalışıyor sanılır)
- **`/yerlestirme` yeni rota** — `/cat` kademeli-swap edilseydi ders-seçim ekranı (8 kart) kaybolurdu; kiro ekranı MATEMATIK'e sabit
- **Keşif devir notunu çürüttü:** `OnboardingPage` `/cat/next`'i çağırmıyor (statik JSON + istemci puanlama); tek tüketici `AdaptifTestPage`
