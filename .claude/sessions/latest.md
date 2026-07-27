## Session Handoff — 2026-07-27 (Kapı 1 / #7 kod tarafı BİTTİ)

**Branch:** feature/self-evolution-optimization
**Commitler:** `33e314fa3` (test koşumu düzeltmesi + matview altyapısı) → `7ede1fcf9` (kapı yayılımı + celery + boş-havuz)
**Test:** DB'siz **109 passed / 153 skipped / 0 failed**. Ruff delta 11 dosyada **0**. 17/17 modül import OK.

### ⛔ TEK BLOKER — migration uygulanmadı

```
cd C:\Users\husey\kiro2\backend && alembic upgrade head   # mv_safe_for_beta_20260727
```
Kod `mv_safe_for_beta` okuyor, ilişki DB'de YOK. Gerçek DSN ile:
`UndefinedTableError: relation "mv_safe_for_beta" does not exist`.
**Bu çalıştırılmadan deploy edilirse CAT / sınav / PF / duel tamamen çöker.**
Sonrası: `KVKK_VERIFY_DSN=postgresql://postgres@localhost:5434/kiro2 pytest tests/e2e/test_quality_gate_leak.py`
→ yeşile dönmeli, sonra `xfail(strict=True)` marker'ı **KALDIRILACAK** (dosya satır 33-45).

### Yapılanlar

- **Sahte-yeşil 3 kusur bulundu ve kapatıldı** (hepsi kendi koşumumla doğrulandı):
  geçen oturumun RED testi sızıntı yüzünden değil sqlite `no such table` yüzünden XFAIL oluyordu
  (`conftest.py:21` DATABASE_URL'i eziyor) → `tests/e2e/pg_dsn.py`; aynı kusur 4 e2e dosyasında,
  3'ü FAIL veriyordu · `TestQualityStatusFilterLeak` 5 testi **aylardır sessizce kırmızıydı** ·
  `_GATE` substring kazası. Bekçiler **4/4 mutasyonla** kanıtlandı (ilk düzeltmem de delikti:
  fonksiyon ADI marker'ı içerdiği için kaynak-taraması hiç kırmızıya dönemiyordu → davranışsal iddiaya çevrildi).
- **Kapı 35 çağrı yerine yayıldı**, 12 dosya. `core/quality_gate.py` tek tanım. is_active her yerde korundu.
- **Ölçüm:** kapı v_safe_for_beta → 730-907 ms; matview → 58-87 ms; kapısız baseline 87-116 ms (EXPLAIN ANALYZE, 3'er tur).
- **Celery:** rota ZORUNLUYDU — `task_default_queue` yok, `default` Queue yok; rotasız görev
  `celery` kuyruğuna düşüyor ve **hiçbir worker tüketmiyor** (Celery'nin kendi router'ıyla ölçüldü).
- **Boş-havuz sözleşmesi:** `soruHavuzuHazir` fail-open'dı (backend alanı hiç üretmiyor) → fail-closed;
  PF'nin sessiz `return null`'ı `NO_VERIFIED_QUESTIONS` mesajına bağlandı.

### Ertelenemez ve SENDE

- **11 anahtar rotasyonu** (10 Google + 1 HF) — hâlâ açık; purge klonu `kiro2_purge.git` push bekliyor.
- pre-commit hook'u kök config'e çevirme + günlük pg_dump.

### Sonraki (maks 5)

1. **Migration uygula** + e2e yeşile döndür + xfail marker'ı kaldır + canlı E2E (CAT/PF/duel 200 mü)
2. **Elasticsearch kapısı** — ES canlı, **64.270 doküman**, her birinde `correct_answer`;
   `api/elasticsearch.py:153` ham `_source`'u `get_current_user`'a dönüyor. **PG kapısı bunu kapatmaz.**
3. **`api/osym_inspired_routes.py:84`** — auth dependency'si YOK + `correct_answer` dönüyor (ayrı P0)
4. **Kapı 1 / #8** şifre kurtarma uçtan uca (~8h) · **#9-10** roster yazma uçları (~22h)
5. **#11** `golden-flows.yml` YAML fix + `feature/**` tetikleyici + GF skip-oranı bekçisi (%83 skip)

### Kararlar (tekrar tartışılmayacak)

- Havuz yetersizse **boş dön + "henüz doğrulanmış soru yok"** — gevşetme/komşu-konu YOK
- Matview + zamanlı yenileme; **bayat pencere kabul**. Gerçek en kötü gecikme = matview bayatlığı
  **+ `_question_pool_cache` TTL 3600 sn** (osym_exam_engine, ikinci katman)
- `soru_bankasi_service`'teki `except: return []` yutmasına dokunulmuyor
- CAT/placement **figür-regex korunuyor**; kesişim ölçüldü: SOSYAL 154→22, COGRAFYA 378→58,
  EDEBIYAT 1144→141. FEN ve GENEL kapı sonrası **sıfır**.

### Bilinen, kapsam dışı bırakılan

- Rotasız beat görevleri hiç koşmuyor (social / daily_plan / push / irt_calibration) — görev #430
- `agents/learning_path_agent.py` import edilemiyor (`core.assessment_system` yok, önceden var olan) →
  oradaki kapı + tablesample düzeltmesi ölü kodda
- 2 `.tablesample()` kalıntısı daha: `database/repositories.py:268`, `repositories/question_repository.py:134` (ölü)
