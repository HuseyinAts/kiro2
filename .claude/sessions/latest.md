## Session Handoff — 2026-08-14 01:40
**Branch:** feature/self-evolution-optimization (origin ile SENKRON, push edildi)
**Son commit:** 5976671e0 fix(db): baseline downgrade RuntimeError kullansin
**Uncommitted:** 3544 dosya — **kasıtlı** (Gemini 7-11 Ağu commit'siz devri, S206 kararı; bu oturumda DOKUNULMADI)

### Yapilanlar
- `backend/tests/db/test_alembic_from_scratch.py` — YENİ bekçi. Boş DB'de
  `alembic upgrade head` koşturur, 244 tablo + `users` bekler. (`42ee0baba` RED → `e002f550b` GREEN)
- `backend/alembic/versions/0001_baseline_squash.py` + `backend/alembic/baseline/0001_baseline_schema.sql`
  — squash tabanı: 243 tablo + 637 index + **79 RLS policy**. (`e002f550b`)
- `backend/alembic/versions_archive/` — eski **117 revizyon** taşındı (silinmedi). (`e002f550b`)
- `backend/scripts/generate_alembic_baseline.py` — baseline üreteci + 3 tuzağın belgesi. (`e002f550b`)
- `backend/scripts/audit_{sql_vs_alembic,orm_vs_livedb,missing_table_consumers}.py` — ölçüm aletleri. (`42ee0baba`)
- `.pre-commit-config.yaml:10` — `versions_archive/` global exclude. `.gitignore:439` — `backend/backups/`. (`e002f550b`)
- Canlı DB: `alembic stamp --purge 0001_baseline` (cdea871deea9 → 0001_baseline, 244 tablo değişmedi).

### Fail Eden Testler
YOK. `tests/db/test_alembic_from_scratch.py` **1 passed**.
Parite ölçüldü: taze-kurulan **244 tablo / 936 index / 79 policy / 2 view** = canlı ile birebir.

### Engelleyiciler
YOK. Push tamam (`3f7c1341a..5976671e0`), pre-push bekçileri geçti.

### Sonraki Adimlar (maks 5)
1. Denek DB'leri düşür: `kiro2_migaudit`, `kiro2_migaudit2`, `kiro2_migaudit3` (DROP proje kuralında yasak — operatör).
2. **Bekçi kalibrasyonu (ölçülmedi):** `backend/hooks/reward_hacking/config/patterns.py:52-53` KASITLI olarak
   yalnız argümansız `NotImplementedError`'ı hedefler, ama `analyzers/ast_analyzer.py:301` argümana bakmaz →
   mesajlı olanlar da placeholder sayılır. #451 dersi: düzeltmeden önce kazanç/bedel ölç.
3. Kalan ~109 `.py` Gemini kirli ağaç sınıflandırması.
4. #444 Öğretmen Öğrenciler sayfası UI (roster backend hazır).
5. `backend/core/rag_service.py:682` `search_with_mmr` O(k²) embed kusuru (S207'de ölçüldü, kapsam dışı).

### Kararlar (gelecek session tekrar tartismasin)
- **Kök neden sıralama değil BOŞ TABAN**: `60e185cfcca9_unified_schema` (down_revision=None) ve
  `f822e22c28c6` ikisi de `upgrade(): pass` idi — `--autogenerate` ZATEN DOLU DB'ye karşı koşturulmuş.
  Şemayı fiilen `backend/migrations/*.sql` kuruyordu; o klasör legacy borç DEĞİL, tabanın eksik parçası.
- **İki onarım tasarımı da ÖLÇÜMLE elendi** (tekrar denenmesin):
  (i) `001-009*.sql` porte → bayat; `001`'in `users.id UUID`'si canlıya (`character varying`) uymuyor,
  probe: *"FK cannot be implemented — incompatible types: character varying and uuid"*.
  (ii) pg_dump tabanı + mevcut zincir → 1. revizyonda `DuplicateTable kvkk_consents`; revizyonlar
  tutarsız idempotent (`d7a10d07b648` savunmacı, `kvkk_compliance_001` değil).
- **BREAKING:** `alembic downgrade` ile eski sürümlere inilemez. Pratikte zaten inilemiyordu.
- Baseline üretiminde 3 tuzak: PG17+ pg_dump psql meta-komutu yazar (SQLAlchemy çalıştıramaz) ·
  `search_path`'i boşaltır (alembic `alembic_version`'a niteliksiz erişir) · `alembic_version` dump
  DIŞINDA olmalı (alembic onu migration'dan ÖNCE kendi yaratır).
- Reward-hacking bekçisi push'u blokladı; **bekçi değiştirilmedi**, kod semantik düzeltildi
  (`RuntimeError` = desteklenmiyor; `NotImplementedError` = henüz yazılmadı). Kendi push'unu geçirmek
  için güvenlik kapısı gevşetilmez.
