## Session Handoff — 2026-08-15 (S211)
**Branch:** feature/self-evolution-optimization
**Son commit:** `18f4ea613` fix(backend): question_crud_service — 108-set JOIN çevirisi (dosya 1/17) + pre-existing lint borcu
**Uncommitted:** 3390 dosya kirli — **hepsi pre-existing** (Gemini S210 devir kalıntısı,
`docs/audits/2026-08-15_s210_gemini_devir_model_split.md` + MEMORY `project_kirli-agac-gemini-devir-20260813.md`'de
"ayrı triyaj" olarak zaten işaretli). Bu session'ın kendi işi commit'li, bu dosyalara dokunulmadı.

### Yapılanlar
- `backend/services/question_crud_service.py` — #485 kapsamında 42/108 class-düzeyi
  `QuestionBankItem.<alan>` sorgusu `QuestionContent`/`QuestionMetadata`/`QuestionStatistics`
  JOIN'lerine çevrildi (search_questions, _calculate_facets, get_question_statistics,
  get_random_questions, list_source_books, get_archived_questions).
- Aynı dosyada `create_question` düzeltildi: split şema sonrası kurucuya delegeli alan
  geçmek (`content` ilişkisi henüz yokken) `AttributeError` atıyordu — artık
  `QuestionContent`/`QuestionMetadata`/`QuestionStatistics` ayrı nesnelerle atanıp cascade
  ile ekleniyor.
- Pre-existing pre-commit borcu (21 ruff + 6 mypy, HEAD'le bire bir aynı satırlar —
  doğrulandı) kullanıcı onayıyla aynı commit'te temizlendi: E712→SQLAlchemy-güvenli
  (`~kolon`, `not X` DEĞİL), PTH122 fix, PTH123 **bilerek atlandı** (`Path.open()`
  `test_upload_question_image`'ın `patch("builtins.open")` mock'unu bypass edip test
  kırıyordu — ölçüldü), PLR0912 → `_apply_search_filters` helper'a bölündü, RET504, mypy 6x.
- 11 yeniden yazılmış sorgu şekli postgres dialect'e karşı derlendi (cartesian-product yok).

### Fail Eden Testler
YOK — koşulan 50 test (question_crud_service + test_question_bank_compat) PASS.
**Not:** tam backend suite bu session'da koşulmadı, sadece etkilenen dosya.

### Engelleyiciler
YOK

### Sonraki Adımlar (maks 5)
1. #485 devamı: 66/108, 16 dosya kaldı. Yoğunluk: `question_bank_service.py` (13),
   `duel_api.py` (12), `curator.py` (10), `productive_failure_service.py` (9).
   Bul: `grep -rn 'QuestionBankItem\.' backend/services backend/api backend/core`
2. Her dosya = ayrı turn + ayrı commit (subagent disiplini — fat-turn riski).
3. Her dosya sonrası pre-commit'i BEKLE — bare ruff/mypy yetmez (bu turda 2 kez yanıldı).
4. Kirli ağaç (3390 dosya, Gemini kalıntısı) hâlâ triyaj bekliyor — ayrı görev.
5. #444 (Öğretmen Öğrenciler UI) ve #467-471 (S200 backlog) bekliyor.

### Kararlar (gelecek session tekrar tartışmasın)
- Pre-commit'in bulduğu pre-existing borcu, dokunduğumuz dosyada aynı commit'te
  temizlemek — kullanıcı onayı gerektirir (AskUserQuestion ile soruldu, "evet" alındı).
  ruff'ın "not X" E712 önerisi SQLAlchemy `ColumnElement`de `TypeError` fırlatır —
  KÖRÜ KÖRÜNE `ruff --fix --unsafe-fixes` çalıştırma.
- 3390 kirli dosya session-handoff commit'ine KARIŞTIRILMADI — pre-existing + zaten
  dokümante (ayrı triyaj konusu).
