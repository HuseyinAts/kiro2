# Gemini kirli ağacı — .py sınıflandırması (S209, 14 Ağu 2026)

**Kapsam:** `feature/self-evolution-optimization` dalındaki 3544 commit'siz dosyanın
**343 `.py`** olanı. Kaynak: Gemini'nin 7-11 Ağu commit'siz devri
(`docs/HANDOFF_2026-08-07_gemini.md`, bkz. S206).

**Alet:** `backend/scripts/audit_dirty_tree_py.py` (salt-okunur)
**Ham veri:** `docs/audits/2026-08-14_kirli_agac_py.tsv`

## Methodology

- Örneklem: evrenin tamamı (343/343), örnekleme yok.
- `M` → `ast.dump(HEAD) == ast.dump(worktree)`, docstring-normalize. Tırnak stili ve
  boşluk etkilemez; **sabit değeri** değişirse etkiler.
- `D` → çift koşul: (a) meşru import adıyla canlı referans var, (b) o adı başka canlı
  dosya/paket **ve** site-packages sağlamıyor.
- Tekrarlanabilir: `python backend/scripts/audit_dirty_tree_py.py --tsv <yol>`
- Truncation: yok.

### Kontrol kolu (aleti doğrulama)

AST karşılaştırıcısı 7 bilinen vaka ile sınandı, **7/7**: tırnak stili / boşluk /
docstring → AYNI; sabit değeri / daralan RLS predicate'i / eklenen null-safety →
FARKLI; bozuk sözdizimi → PARSE_FAIL (sessizce "aynı" demez).

`D` sınıfı ayrıca **canlı import denemesiyle** çivilendi (8/8 `ModuleNotFoundError`).

## Sonuç

| durum | sınıf | adet |
|---|---|---:|
| D | REFERANSSIZ | 129 |
| M | **YAPISAL** | **110** |
| ?? | YENI_YETIM | 40 |
| D | **KIRIK_IMPORT** | **23** |
| M | KOZMETIK | 14 |
| ?? | YENI_BAGLI | 11 |
| D | TASINMIS_OLABILIR | 8 |
| M | PARSE_HATASI | 4 |
| D | AD_COZULUYOR | 3 |
| D | UCUNCU_TARAF | 1 |

**M'in yalnızca %11'i (14/128) kozmetik.** S206'daki "M = kozmetik reformat"
varsayımı beşinci kez çürüdü.

## P0-A · 23 silme canlı import kırıyor

21'inin `.archive/` dışında canlı tüketicisi var; 2'si (`backend/optimal_hybrid_system.py`,
`orchestrator/master_orchestrator.py`) yalnız `.archive/` tarafından import ediliyor.

`orchestrator/core/` altından **17 modül** silinmiş (taşınmamış — aynı adlı canlı dosya yok).
Canlı kanıt, şu anki çalışma ağacında:

```
python -c "import orchestrator"
  -> ModuleNotFoundError: No module named 'orchestrator.core.memory'
```

`orchestrator/` CLAUDE.md'de **ACTIVE v2.5.0**. `backend/api/orchestrator_api.py` ve
`.claude/orchestration/mcp_orchestrator.py` bu modülleri import ediyor. Bu, S206'daki
`backend/services/bkt_service.py` vakasının **ikinci tekrarı**.

Ayrıca: `backend/tasks/ai_tasks.py` ← `backend/celery_worker.py`,
`backend/models_unified.py` ← `backend/core/database_query_optimizer.py`.

**Geri yükleme risksiz:** `D` dosyalarında commit'siz iş YOK; `git checkout HEAD -- <yol>`
yalnızca HEAD içeriğini geri getirir.

### ✅ KAPANDI — 22 dosya geri yüklendi (kullanıcı onayı, çalışma ağacı; commit YOK)

21 dosya + kaskad olarak ortaya çıkan `orchestrator/config.py`. Kaskad şöyle bulundu:
geri yüklenen `orchestrator/core/memory.py:352` ve `state.py:265` **fonksiyon içinde**
`from orchestrator.config import get_config` yapıyor — tembel import olduğu için
modül-seviyesi probe'u geçmişti, ama çalışma anında patlardı.

Doğrulama (geri yükleme bir İDDİADIR, ölçüldü):

```
python -c "import orchestrator"                            -> OK
python -c "import orchestrator.core.routing"               -> OK
python -c "import orchestrator.core.state"                 -> OK
python -c "from orchestrator.config import get_config"     -> OK
backend/ kokunden: models_unified, tasks.ai_tasks,
                   setup_database, diagnostic_video_api     -> 4/4 OK
```

KIRIK_IMPORT **23 → 2**. Kalan 2 (`backend/optimal_hybrid_system.py`,
`orchestrator/master_orchestrator.py`) yalnız `.archive/` tarafından import ediliyor —
`.archive/` pre-commit'te zaten dışlanmış, geri yüklenmedi.

> Tuzak notu: ilk geri yükleme denemesi Python `print`'in Windows'ta `\r\n` yazması
> yüzünden `git checkout HEAD -- 'yol.py\r'` diye çalıştı ve **21/21 sessizce
> başarısız** oldu. Dosya varlığı kontrolü yakaladı. `git checkout` çıktısı
> okunmadan "geri yüklendi" denemez.

## P0-B · `question_bank.py`'de commit'siz sürüm DOĞRU olan

En büyük yapısal fark: `backend/models/question_bank.py` **777 → 321** satır.
`QuestionBankItem` 84 → 21 alan; `question_text`, `correct_answer`, `option_a..e`,
`explanation` üç yeni tabloya taşınmış (`QuestionContent`, `QuestionMetadata`,
`QuestionStatistics` — mixin değil, `__tablename__`'li ayrı modeller).

Canlı DB ölçümü (port 5434, db `kiro2`):

| tablo | kolon |
|---|---:|
| `question_bank` | **12** (`id, soru_hash, primary_topic_id, is_active, is_public, created_by, reviewed_by, created_at, updated_at, is_ai_generated, review_status, is_anchor`) |
| `question_content` | 19 (`question_text … correct_answer, explanation …`) |
| `question_metadata` | 21 |
| `question_statistics` | 34 |

Yani **canlı şema bölünmüş durumda** ve commit'siz model ona uyuyor; **HEAD'deki
commit'li model uymuyor** (`question_bank.question_text` sütunu yok → HEAD modeliyle
her soru sorgusu `UndefinedColumn` verir).

Sonuç: "kirli ağacı at, HEAD'e dön" **bu dosya için yıkıcı** olurdu. M/YAPISAL kümesi
tek tip değil; en az bir üyesi HEAD'den daha doğru.

> Uyarı: bu makine taze ortam (`question_bank` 0 satır, bkz.
> `memory/project_ortam-tazelendi-20260812.md`). Bölünmüş şemanın 6 Ağu'daki dolu
> ortamda da geçerli olup olmadığı **ölçülmedi**.

## 110 YAPISAL — 1. mercek: ORM ↔ canlı DB paritesi (model dosyaları)

Alet: `backend/scripts/audit_orm_vs_db_parity.py`. Model dosyaları **import edilmez**
(33 modeli import etmek SQLAlchemy kayıt defterinde çakışma riski); `ast` ile
`__tablename__` + kolon adları çıkarılır, canlı `information_schema` ile karşılaştırılır.
Ham veri: `docs/audits/2026-08-14_orm_db_parite.tsv`.

**Kontrol kolu:** cevabı elle bilinen `question_bank.py` — disk 0 eksik, HEAD **69 eksik
kolon**. Alet beklenen sonucu verdi.

30 model dosyasından:

| karar | adet | dosyalar |
|---|---:|---|
| **DISK_DOGRU** | 4 | `question_bank.py`, `billing.py`, `study_room.py`, `system_models.py` |
| **HEAD_DOGRU** | 1 | `oba_seferleri.py` |
| ESIT | 25 | şema açısından fark yok — yapısal fark başka katmanda |

### DISK_DOGRU — commit'siz sürüm canlı DB'ye uyan

| dosya | HEAD'in DB'de olmayan kolonları |
|---|---|
| `question_bank.py` | `question_bank`: **69** (`question_text`, `correct_answer`, `option_a..e` …) |
| `study_room.py` | `study_sessions`: 7 (`room_id`, `user_id`, `topic`, `notes`, `pomodoros_completed` …) |
| `billing.py` | `data_processing_agreements`: 6 (`status`, `version`, `signer_email` …) |
| `system_models.py` | `sessions`: 1 (`token`) |

`study_room.py` ve `billing.py`'de yapılan şey **silme değil yeniden adlandırma**:

- `StudySession` → `RoomStudySession`, tablo `study_sessions` → **`room_study_sessions`**
- `DataProcessingAgreement` → `BillingDataProcessingAgreement`, tablo →
  **`billing_data_processing_agreements`**

Her iki yeni tablo da canlı DB'de **var**. Sebep ölçüldü: HEAD'de `StudySession`
sınıfı **iki dosyada** tanımlı (`study_room.py` ve `learning_path_models.py:580`),
ikisi de `study_sessions`'a eşleniyordu — `testing.md` #6'daki SQLAlchemy çakışma
kalıbı. Commit'siz sürüm oda-kapsamlı olanı kendi tablosuna ayırarak çakışmayı çözüyor.

> Bunun S203'te açık kalan `/study-sessions/start` **500** kalemiyle (`FSRS-K1`)
> aynı tabloya işaret ettiğine dikkat — bağlantı **kurulmadı, ölçülmedi**; ayrı görev.

### HEAD_DOGRU — commit'siz sürümün migration'ı eksik

`oba_seferleri.py`: disk sürümü `oba_challenges`'a `ai_story` ve `personalized_targets`
ekliyor; **bu iki kolon canlı DB'de yok.** Yani bu değişiklik migration'sız — commit
edilecekse önce alembic revizyonu gerekir.

### Aletin bilinen bias'ı (ölçüm sırasında fark edildi)

Parite skoru **model silmeyi ödüllendirir**: var olmayan bir model uyuşmazlık üretemez.
`study_room.py` ilk bakışta "disk modeli kaldırmış" gibi göründü; sınıf-düzeyi
HEAD↔disk farkı alınınca gerçekte **rename** olduğu görüldü. Bu yüzden her
`DISK_DOGRU` kararı, silinen/eklenen sınıf listesiyle birlikte okunmalıdır.

### Kalan kapsam (bu tur yapılmadı)

ESIT 25 dosyanın yapısal farkı **karakterize edilmedi** (şema aynı, fark ilişki/mantık
katmanında). `backend/core` (17), `backend/api` (13), `_scripts` (13), `scripts` (8),
`agents` (6) grupları için şema merceği geçerli değil — ayrı mercek gerekir.

## PARSE_HATASI (4)

`ai_ml/turkish_nlp_system.py`, `ai_ml/yks_score_prediction_models.py`,
`.archive/root_cleanup_20260402/{create_csv,gemini_cli}.py` — HEAD **ve** diskte
parse edilemiyor, yani bu diff'in getirdiği bir kusur değil (pre-existing).

## Alet doğrulamasında bulunan 4 kusur (ölçüm sırasında düzeltildi)

Bu sayılar ilk turda **çok farklıydı**; her biri ölçüm aletinin kendi kusuruydu:

| # | Kusur | Etki |
|---|---|---|
| 1 | Çıplak-ad eşleşmesi (`models`) canlı `backend/models/` paketiyle çakışıyordu | `backend/models.py` sahte P0 |
| 2 | Index `core.config` → son bileşen `config`'i de kaydediyordu | `orchestrator/config.py` "93 canlı import" |
| 3 | `from .config import X`'te `node.level` kontrol edilmiyordu | aynı dosya "23 canlı import" |
| 4 | (3)'ü düzeltirken göreli import'lar **tümden** atıldı | `orchestrator/core/__init__.py`'nin 8 gerçek referansı kayboldu |

KIRIK_IMPORT sayısı sırasıyla **31 → 19 → 18 → 15 → 23** oldu. Ara değerlerin hiçbiri
doğru değildi. Ders: bir denetim sayısını raporlamadan önce **aletin kendisini** bilinen
sonuçlu vakalarla sına (`.claude/rules/audit-methodology.md`, "Ölçüm aletini doğrula").

## Karar bekleyenler

1. **P0-A:** 21 dosya geri yüklensin mi? (kullanıcı "3544 dosya kasıtlı, dokunma" dedi —
   geri yükleme o kümeye dokunur, onay gerekiyor)
2. **P0-B:** `question_bank.py` ve kardeşleri commit'lenmeli — HEAD canlı DB ile uyumsuz.
3. Kalan 110 YAPISAL dosyanın dosya-bazlı incelemesi (bu tur yalnız **sınıflandırdı**,
   içerik yargısı vermedi).
