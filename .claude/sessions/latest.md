## Session Handoff — 2026-08-15 (S212)
**Branch:** feature/self-evolution-optimization
**Son commit:** `2fb518b1e` fix(backend): duel_api — 108-set JOIN çevirisi (dosya 3/17)
**Bu turdaki zincir:** `904f9579a` (JOIN 13/13) → `666155dfa` (stub) → `8d5ebe761` (select_from bug) →
`44924c574` (create_question + eager-load + 15 test) → `96c3b16d1` (stub) → `f91470250` (S211 retro) →
`d731de9b4` (handoff, **buraya kadar PUSH EDİLDİ**) → `2fb518b1e` (duel_api)
**PUSH BEKLİYOR: 2 commit** (`2fb518b1e` + bu handoff).
**Not:** push `--no-verify` gerektirdi — pre-push bekçisi `test_coverage_final_50.py`'deki
3 PRE-EXISTING bulguyu (meşru async test double'ları, satır 342/399/426) bloklayıcı sayıyor.
Kullanıcı onaylı. Bekçi "dokunulan dosyadaki pre-existing bulgu" ayrımı yapmıyor — kalan
dosyalarda tekrar çıkacak.

### ⚠️ EN ÖNEMLİ DERS (bu tur 4 kusur bu yüzden kaçtı)
"JOIN'e çevirdim + testler yeşil" **yetersiz bir kabul kriteri.** #485'in geri kalan
15 dosyasında ZORUNLU 4 adım:
1. **Sorguyu DERLE** — `stmt.compile(dialect=postgresql.dialect(), literal_binds)`.
   Gözle okumak yakalamıyor: `select(func.avg(SplitTablo.x)).join(SplitTablo, ...)`
   sol tarafı split tablo sanıp kendine JOIN etmeye çalışır → `InvalidRequestError`,
   sorgu çalışma anında değil **derleme anında** patlar. `.select_from(QuestionBankItem)` şart.
2. **Kartezyen kontrolünü `get_final_froms()` ile yap**, metinle DEĞİL. "FROM'da virgül var mı"
   `SELECT count(*) FROM (SELECT a, b ...)` şeklinde yanlış-pozitif verir (bir kez verdi).
3. **Delege okuyan her yol eager-load etmeli.** content/metadata_info/statistics hepsi
   `lazy='select'` → async'te yüklenmemiş erişim `MissingGreenlet`. JOIN yalnız SQL katmanını
   düzeltir. Beteri: bu servislerde çıplak `except Exception` var → hata YUTULUR, kusur
   "soru bulunamadı" / "versiyon oluşmadı" diye sessizce görünür.
4. **Gerçek modele karşı test yaz.** `tests/unit/test_coverage_final_50.py` sahte
   `models.question_bank` stub'ı kullanıyor — kırık kodda da yeşil kalıyor
   (`test_create_question` tam olarak bunu yaptı). Örnek: `tests/fast/test_question_bank_service_split.py`,
   `tests/fast/test_question_crud_service_split.py`.

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
1. **PUSH** (10 commit bekliyor) — pre-push bekçisi var, commit'siz iş yok.
2. #485 devamı: **41/108, 14 dosya.** Yoğunluk: `curator.py` (10),
   `productive_failure_service.py` (9), ...
   Bul: `grep -rn 'QuestionBankItem\.' backend/services backend/api backend/core`
   **Yukarıdaki 4 adımlı kabul kriterini uygula** — 3 dosyanın 3'ünde de kusur çıktı.
   Bugüne kadarki skor: dosya 1 (crud) 2 kusur · dosya 2 (bank) 3 kusur ·
   dosya 3 (duel) sorgu HİÇ kurulamıyordu.
3. Her dosya = ayrı turn + ayrı commit. pre-commit'i BEKLE (bare ruff/mypy yetmez);
   mypy "Failed" görünce pre-existing mi yeni mi diye HEAD ile karşılaştır — hook ayrım YAPMAZ.
4. Kirli ağaç (3390 dosya, Gemini kalıntısı) triyaj bekliyor — ayrı görev.
5. #444 (Öğretmen Öğrenciler UI) ve #467-471 (S200 backlog) bekliyor.

### duel_api'den çıkan iki ek ders
- **Kolon seçimi vs entity seçimi ayrımı yap.** duel_api'nin 12 erişiminin hepsi
  `select(QuestionBankItem.question_text, ...)` biçimindeydi — entity yok, Row dönüyor,
  yani **eager-load N/A**. Bunu varsaymak yerine ölçtüm:
  `grep 'select(QuestionBankItem)' api/duel_api.py` → 0. Her dosyada bu ayrımı yap,
  yoksa gereksiz `selectinload` eklersin.
- **Biçimlendirici import siliyor.** `correct_answer`'ı `QuestionContent`'e çevirince
  `QuestionBankItem` o fonksiyonda kullanılmaz kaldı → import OTOMATİK silindi, ama
  `QuestionContent` import'u yoktu → `NameError` olacaktı. Alan taşırken **kullanımı
  önce yaz, sonra import'u doğrula** (MEMORY: `reference_formatter-import-stripping`).

### Ölçülen ama DÜZELTİLMEYEN (bilinçli)
- `tests/fast` genelinde **22 fail + 43 error PRE-EXISTING** — pathspec'li stash ile HEAD'e
  karşı ölçüldü, aynı 22. Ürün kırık DEĞİL: `subject_db` doğrudan import'ta var; testler
  `core.turkish_nlp_utils`'i `sys.modules`'te stub'layıp gölgeliyor = **test kirliliği**.
  Dosyalar tek başına koşunca geçiyor (`batch14` 63 passed). Ayrı görev.
- `tests/unit/test_coverage_final_50.py` — 40 pre-existing ruff + 1 secrets false-positive.
  İki commit `--no-verify` ile geçti (kullanıcı onaylı, `666155dfa` + `96c3b16d1`).

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
