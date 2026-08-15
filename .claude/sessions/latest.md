## Session Handoff — 2026-08-15 (S212)
**Branch:** feature/self-evolution-optimization
**Son commit:** `666155dfa` test(backend): coverage_final_50 stub — QuestionMetadata/QuestionStatistics
**Önceki:** `904f9579a` fix(backend): question_bank_service — 108-set JOIN çevirisi (dosya 2/17)
**Uncommitted:** 3390 dosya kirli — **hepsi pre-existing** (Gemini S210 devir kalıntısı,
zaten dokümante, "ayrı triyaj" konusu). Bu session'ın kendi işi commit'li, bu dosyalara dokunulmadı.

### Yapılanlar
- `backend/services/question_bank_service.py` — #485 kapsamında 13/13 class-düzeyi
  `QuestionBankItem.<alan>` sorgusu `QuestionMetadata`/`QuestionStatistics` JOIN'lerine
  çevrildi (batch_update_difficulties, get_questions_needing_calibration, search_questions,
  get_topic_statistics).
- Pre-existing borç temizlendi: 6x E712, 1x PLC0414 (kasıtlı re-export alias, `# noqa` ile
  korundu). **Yeni ders:** `self.db: Session` (sync tip) → `AsyncSession` — dosya zaten
  `await self.db.execute/commit/...` kullanıyordu (question_crud_service.py'nin konvansiyonu),
  tek satır 31 mypy hatasının 25'ini çözdü. Kalan 5'i `list(...)` sarmalama + 1 anotasyon ile
  kapandı. Pre-commit TAMAMEN yeşil (ilk kez, ruff+format+bandit+mypy+secrets).
- `tests/unit/test_coverage_final_50.py`: dosyanın fake `models.question_bank` stub'ı
  (metaclass tabanlı, ~satır 265-330) QuestionMetadata/QuestionStatistics tanımlamıyordu →
  ImportError → 202 test collection'ı düşüyordu. 2 minimal stub sınıfı eklendi.
  **--no-verify ile ayrı commit** (kullanıcı onayı, AskUserQuestion): dosyanın kalanında
  40 pre-existing ruff bulgusu + 1 secrets false-positive var, #485 kapsamı dışı.
- **Near-miss veri kaybı (kurtarıldı):** `git stash` (pathspec'siz, TÜM 3390 kirli dosyayı da
  içeren) + `pre-commit run --files` arada baseline'a trivial formatter-fix uyguladı +
  `git stash pop` conflict'te durdu, stash KEPT. `git checkout HEAD -- <dosya>` ile
  conflict'i temizleyip pop tekrar denendi, başarılı — diff stat ile doğrulandı. Ders:
  **asla pathspec'siz `git stash` kullanma** kirli bir ağaçta; `git stash -- <dosya>`
  veya commit-önce kullan.

### Fail Eden Testler
YOK — question_bank + compat + coverage_final_50 = 212 passed, 27 skipped (DB-model,
pgvector gerektiriyor, pre-existing skip).

### Engelleyiciler
YOK

### Sonraki Adımlar (maks 5)
1. #485 devamı: 53/108, 15 dosya kaldı. Yoğunluk: `duel_api.py` (12), `curator.py` (10),
   `productive_failure_service.py` (9), ...
   Bul: `grep -rn 'QuestionBankItem\.' backend/services backend/api backend/core`
2. Her dosya = ayrı turn + ayrı commit (subagent disiplini — fat-turn riski).
3. Her dosya sonrası pre-commit'i BEKLE — bare ruff/mypy yetmez. mypy "Failed" görünce
   pre-existing mı yeni mi diye HEAD ile satır sayısı karşılaştır — mypy hook'un exit
   code'u pre-existing/yeni ayrımı YAPMAZ, her ikisi de commit'i bloklar.
4. Kirli ağaç (3390 dosya, Gemini kalıntısı) hâlâ triyaj bekliyor — ayrı görev.
5. #444 (Öğretmen Öğrenciler UI) ve #467-471 (S200 backlog) bekliyor.

### Kararlar (gelecek session tekrar tartışmasın)
- Pre-commit'in bulduğu pre-existing borcu, dokunduğumuz dosyada aynı commit'te
  temizlemek — kullanıcı onayı gerektirir (AskUserQuestion ile soruldu, "evet" alındı).
  ruff'ın "not X" E712 önerisi SQLAlchemy `ColumnElement`de `TypeError` fırlatır —
  KÖRÜ KÖRÜNE `ruff --fix --unsafe-fixes` çalıştırma.
- **Ölçek ayrımı (S212, yeni):** dosyanın DOĞRUDAN #485 kapsamındaki borcu (küçük,
  mekanik, dokunduğumuz satırlara yakın) aynı commit'te temizlenir. Yan-etki olarak
  dokunmak zorunda kaldığımız TAMAMEN ilgisiz bir dosyadaki büyük pre-existing borç
  (örn. 40 bulgu, test niyetini bozma riski) İÇİN AYRI karar/onay gerekir — `--no-verify`
  + commit mesajında gerekçe, kullanıcı onayıyla kabul edilebilir.
- 3390 kirli dosya session-handoff commit'ine KARIŞTIRILMADI — pre-existing + zaten
  dokümante (ayrı triyaj konusu).
