## Session Handoff — 2026-07-26 (G4-B)
**Branch:** feature/self-evolution-optimization
**Son commit:** d6ff32d5d fix(cat): omit ("Emin değilim") artık θ'ya yanlış olarak girmiyor
**Push:** EDİLDİ (f8339ffa6..d6ff32d5d)

### Yapilanlar
- **G4-B `/cat/next`** `125fb87f1` — `app/api/cat.py` (+`POST /next`, `get_optional_user`, `cat_sid` HttpOnly çerez, `@limiter.limit("30/minute")`) + `app/schemas/cat_schemas.py` (4 şema, TR camelCase sözleşme paritesi) + `app/services/cat_session.py` (`is_guest`, `pending_question_id`, `max_items`/`se_threshold`, `topic_hierarchy` JOIN, `fetch_question_detail`) + `app/services/irt_engine.py` (6 panel türevi) + `tests/unit/test_cat_next_adapter.py` (32 test, YENİ).
- **Pre-existing P0 fix:** `app/api/cat.py` FastAPI 0.103.2'de import edilemiyordu (`abandon_session() -> None` + 204) → TÜM CAT router'ı kayıtsız, `/api/v1/cat/*` 404. GF13 `!= 500` dediği için false-green'di.
- **Adversarial (5 skeptik, 37 bulgu)** sonrası kapatılanlar: cevap-anahtarı oracle'ı (P0), misafir oturum sızıntısı (P0), rate-limit yokluğu (P0), şık indeks kayması (P1), sessiz misafire düşme (P1).

- **Omit fix** `d6ff32d5d` — `skip_question()`: omit θ'ya girmez (12/12 omit → prior, güvenilirlik %0), tekrar sunulmaz, bütçeden düşer. `kalanTahmini` bütçesi de düzeltildi (yeni test yakaladı).

### Fail Eden Testler
- YOK. 34/34 yeni + bağımlı modüller dahil 166/166 pass. Ruff: değişen satırlarda 0 (kalan 2 B905 `_persist_session_to_db` pre-existing).

### Engelleyiciler
- Redis + Docker DOWN → canlı E2E yapılamadı (PG 5434 UP, SQL'ler canlı doğrulandı).
- **Ekran blocker:** CAT-uygun MATEMATIK havuzunun %60.7'si (6,129/10,102) LaTeX içeriyor; `AdaptifTestPage.tsx:180` düz metin basıyor → KaTeX/MathJax olmadan mount edilmemeli.
- Adversarial 37 bulgunun P0/P1'leri kapatıldı; kalan P2'ler (SE çubuğu ekranda %0'da çakılı, "tahmin yeterince kararlı" metni gerçek dışı, kalibre edilmemiş parametreler üzerinden nüfus-referanslı iddialar) **ekran/kalibrasyon işi** — backend adaptörü değil.

### Sonraki Adimlar (maks 5)
1. **AdaptifTestPage mount + KaTeX** — ekran hiçbir route'a bağlı değil; LaTeX render'ı ön koşul.
3. **Canlı E2E** — Redis + Docker ayağa kalkınca `/api/v1/cat/next` gerçek havuzla smoke.
4. **Görev 2 Offline** — SW+IndexedDB çöz-döngüsü (ürün-fork).
5. **IRT kalibrasyonu** — panel iddiaları (üst %X, N net, seviye) bootstrap parametreler üzerinde; gerçek kalibrasyon ayrı iş.

### Kararlar
- **G4-A `/auth/recover` ERTELENDİ** (kullanıcı kararı, 26 Tem): e-posta/SMTP altyapısı repo'da yok → işlevsel kurtarma yazılamaz. Endpoint-stub da KONMAYACAK (çalışmayan uç, çalışıyor sanılır). SMTP geldiğinde açılacak. **G4 (C→B→A) bu kararla KAPANDI.**
- Oturum kimliği = anonim HttpOnly `cat_sid` çerezi (frontend'e 0 dosya dokunuldu, sözleşme birebir).
- Yerleştirme = 12 madde + SE≤0.45. Ölçüm: havuz a≈1.00/c=0.20/b∈[-1.05,0.89] → motorun SE 0.35 eşiği 20 maddede bile yakalanmıyor (SE≈0.51). 12 sayısı panelin θ-SVG'siyle de uyumlu (`cx=20+(i/11)*300`).
- `app/api/cat.py`'de `from __future__ import annotations` YASAK — slowapi wrapper'ı `__globals__`'ı değiştirdiği için gövde parametresi query'ye düşüp 422 üretiyor.
- Keşif devir notunu çürüttü: **OnboardingPage `/cat/next` çağırmıyor** (statik JSON + istemci-taraflı puanlama); tek tüketici AdaptifTestPage ve o da mount edilmemiş.
