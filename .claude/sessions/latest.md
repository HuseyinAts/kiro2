## Session Handoff — 2026-08-14 (S209)
**Branch:** feature/self-evolution-optimization
**Son commit:** b40fe4885 chore: session handoff — S209 kirli agac .py siniflandirmasi
**Uncommitted:** 3521 dosya (2019 M / 1415 D / 87 ??) — tamamı **kasıtlı** Gemini devri
(S206), DOKUNMA. Bu oturumun 22 geri yüklemesi zaten HEAD ile ayni (1437→1415).

### Yapilanlar
- Denek DB'leri düşürüldü: `kiro2_migaudit{,2,3}` (~54 MB). Kalan `kiro2` 33 MB, `kiro2_test` 24 MB.
  Not: `DROP DATABASE` tek `psql -c`'de çoklu deyimle koşmaz — her biri ayrı `-c`.
- `backend/scripts/audit_dirty_tree_py.py` — YENİ. Kirli ağaç .py sınıflandırıcı (ast + import grafiği).
- `backend/scripts/audit_orm_vs_db_parity.py` — YENİ. ORM ↔ canlı `information_schema` paritesi.
- `docs/audits/2026-08-14_kirli_agac_py_siniflandirma.md` + 2 TSV — 343 .py sınıflandırıldı.
- **22 dosya geri yüklendi** (`git checkout HEAD --`, working-tree, commit yok):
  `orchestrator/core/` 17 modül + `orchestrator/config.py` + `backend/tasks/ai_tasks.py`,
  `models_unified.py`, `setup_database.py`, `diagnostic_video_api.py`.

### Fail Eden Testler
YOK. Koşulan: `backend/tests/db/test_alembic_from_scratch.py` **1 passed** (gerçek PG ile;
`KVKK_VERIFY_DSN="postgresql://postgres@localhost:5434/kiro2"` şart, `DATABASE_URL` yetmez —
`backend/conftest.py:21` onu sqlite'a eziyor). 110 YAPISAL dosya için test koşulmadı.

### Engelleyiciler
YOK.

### Sonraki Adimlar (maks 5)
1. **P0-B commit kapsamı**: `backend/models/{question_bank,study_room,billing,system_models}.py`
   commit'lenmeli (commit'siz sürüm canlı DB'ye uyan). `oba_seferleri.py` için ÖNCE alembic revizyonu
   (`oba_challenges.ai_story`, `.personalized_targets` DB'de yok).
2. 110 YAPISAL'ın kalanı: ESIT 25 karakterize edilmedi; `backend/core` (17), `backend/api` (13),
   `_scripts` (13), `scripts` (8), `agents` (6) — şema merceği geçmiyor, ayrı mercek gerek.
3. #444 Öğretmen Öğrenciler sayfası UI (roster backend hazır).
4. `backend/core/rag_service.py:682` `search_with_mmr` O(k²) embed kusuru.
5. #433 ES index'ini `v_safe_for_beta`'dan yeniden kur.

### Kararlar (gelecek session tekrar tartismasin)
- **"Commit'siz = çöp" ÇÜRÜK.** M'in yalnız %11'i kozmetik (14/128); 4 model dosyasında
  commit'siz sürüm HEAD'den DOĞRU. `question_bank.py`: HEAD `question_bank.question_text`
  bekliyor, DB'de yok (12 kolon + `question_content`/`_metadata`/`_statistics`).
  `study_room`/`billing` rename: HEAD'de `StudySession` İKİ dosyada tanımlı, ikisi de
  `study_sessions`'a eşleniyordu (testing.md #6). Toptan `git checkout` = şema kaybı.
- **#483 bekçi `NotImplementedError`: DOKUNULMAYACAK.** 3 aday ölçüldü — regex genişletme
  +4 bulgu/hepsi kopya/yeni satır 0; AST daraltma −7 (6'sı gerçek pozitif); dedup +1 kazanç.
  #451 ile aynı sonuç. Handoff'taki "KASITLI" iddiası çürüdü (`git blame` → `1fe3a390a`).
- **S208 alembic kararları geçerli**: kök neden BOŞ TABAN; iki onarım tasarımı da ölçümle
  elendi; `alembic downgrade` BREAKING.
- **Ölçüm aleti dersi:** `audit_dirty_tree_py.py`'de 4 kusur çıktı, KIRIK_IMPORT
  31→19→18→15→**23** salındı (çıplak-ad çakışması / index'in son-bileşeni / `node.level` /
  göreli import'ları tümden atma). ORM parite aletinin bias'ı: **model silmeyi ödüllendirir** —
  `DISK_DOGRU` kararı silinen-eklenen sınıf listesiyle birlikte okunmalı.
- Geri yükleme bir İDDİADIR: ilk deneme Python `print`'in `\r\n`'i yüzünden 21/21 sessizce
  düştü. `git checkout` çıktısı + dosya varlığı doğrulanmadan "geri yüklendi" denmez.
