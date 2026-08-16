## KIRO2 Nedir, Şu An Nerede, Nereye Gidiyor (teknik olmayan özet — 16 Ağustos 2026)

**Nedir:** KIRO2, Türkiye'de üniversite giriş sınavına (YKS/TYT/AYT) hazırlanan
öğrenciler için bir çalışma platformu. Amaç her öğrenciye tam ona göre bir
çalışma deneyimi sunmak: çok kolay soruyla zaman kaybettirmemek, çok zor
soruyla moralini bozmamak, unutmaya başladığı konuyu tam zamanında hatırlatmak.

**Elde ne var:**
- ~188 bin soru — bunların ~111 bini şu an aktif kullanılabilir, ~25 bini de
  ayrıca kalite kontrolünden geçip "öğrenciye güvenle gösterilebilir" diye
  işaretlenmiş bir havuzda.
- 405 kaynak kitaptan derlenmiş içerik.
- Öğrencinin hangi konuda zayıf olduğunu tahmin eden, ne zaman tekrar etmesi
  gerektiğini hatırlatan, kişiye özel çalışma planı çıkaran bir motor.
- Öğretmen sınıfını takip edebiliyor, veli çocuğunun ilerlemesini görebiliyor.

**Şu an neyle uğraşıyoruz:** Platform aylardır büyüyor; bir ara hız kazanmak
için kısayollar alındı — geçen ay bir yapay zekâ aracının devraldığı bir
dönemde, kod tabanına gözden geçirilmeden ve test edilmeden çok fazla
değişiklik girdi. Şu anki iş bunun temizliği: soru veritabanının iç yapısını
daha sağlam bir şekle sokuyoruz (tek büyük, hantal bir tabloyu yönetilebilir
parçalara ayırdık) ve bu ayırmanın her yerde doğru çalıştığını, tek tek test
yazarak kanıtlıyoruz. Sıkıcı ama gerekli bir iş — atlanırsa öğrenciye yanlış
soru gitmesi veya sistemin sessizce çökmesi gibi fark edilmesi zor hatalar
üretir.

**Nereye gidiyor:** Hedef, platformu öğrencilere doğrudan abonelik olarak
sunmak (okul/kurum üzerinden değil, öğrencinin kendisinin abone olduğu bir
model). Bunun için önce birkaç güvenlik ve sağlamlık kapısının kapanması
gerekiyor: kimin neyi görebileceğinin sıkılaştırılması, verinin tutarlılığının
garanti altına alınması, testlerin platformun büyük bölümünü kapsıyor olması.
Bu kapıların çoğu ya kapandı ya da kapanmak üzere.

**Özetle:** İçerik ve zekâ tarafı zengin ve büyük ölçüde hazır; şu anki emek
bu zenginliğin üzerine sağlam ve güvenilir bir temel inşa etmek. O tamamlanınca
öğrencilere açılış için teknik bir engel kalmayacak.

---

## Session Handoff — 2026-08-16 (S219)

**Branch:** `feature/self-evolution-optimization` · **HEAD:** `05148d0ee` · **Push:** ✅ edildi (`74c8f9d80..05148d0ee`, 11 commit)
**Ana iş:** #485 — `core/osym_exam_engine.py` göçü. Ama asıl bulgu: **göç sayacı %94 kördü.**

### ⚠️ ÖNCE BUNU OKU — "kalan 9/5" rakamı GEÇERSİZ

S211-S218'in ilerleme ölçütü olan regex sayacı iki yönde birden yanılıyordu (ölçüldü):
- **FAZLA:** yorum satırını erişim sayıyordu (`osym_exam_engine.py:1327`, `models/question_bank.py:528` → 10 kalemin 2'si fantom)
- **EKSİK:** alias'lı import'ları göremiyordu (15 alias import / 11 dosya: `as Question` ×13, `as Soru`, `as _QB`)

**Gerçek kapsam (AST, alias-farkında):** `SINIF=146 · KWARG=12 · ENTITY=69 · 26 dosya`.
Alet: `backend/scripts/scan_split_accesses.py` (10 test + kontrol kolu ile çivili).
Ölçüm çıktısı: `docs/audits/2026-08-16_485_ast_olcum.txt`.

**İyi haber:** S211-S218'in kapanış ilanları FANTOM DEĞİL — 11 ilanın 10'u dosya okunarak
doğrulandı, gerçekten kapalı. Tek istisna `question_crud_service.py` `archive/restore`
(eager-load atlanmış, API tüketicisi yok). Sorun "yanlış kapatma" değil, **hiç açılmama**.

### Kalan iş (ölçülmüş, öncelik sırasıyla)

| Dosya | SINIF+KWARG+ENTITY | Not |
|---|---|---|
| `core/osym_exam_engine.py` | 42+2+5 | **bu planın konusu**, 2/7 task kapandı |
| `services/soru_bankasi_service.py` | 41+0+15 | canlı, P0 — ayrı plan |
| `application/commands/sinav.py` | 16+0+0 | canlı, P0 — **BKT hiç çalışmıyor**, ayrı plan |
| `repositories/question_repository.py` | 16+5 | **sıfır tüketici** → göç değil, SİLME kararı |
| `services/exam_performance_service.py` | 11+0+0 | P1 |
| `core/irt_daemon.py` | 2+6+1 | **KWARG'lar: her IRT kalibrasyon yazımı `CompileError`** |
| `services/irt_analysis_service.py` | 1+4+3 | alias `as Soru` |
| diğer 6 dosya | ~10 | P2 |

### Yapılanlar (11 commit, hepsi push edildi)

- `bdc84e9bc` · `2222337fb` · `224303eff` — **Task 0:** AST sayacı + KWARG/`db.query` sınıfları + 10 test (2 vakum test yakalandı ve düzeltildi)
- `f7f39c2bc` · `fc276b35d` · `e32ab0ace` — **Task 1:** `tests/fast/test_osym_exam_engine_split.py`, **18 RED test**. Bağımsız reviewer kendi fix'ini yazıp 15/15 geçirdi → aşırı-kısıt yok
- `d7eaeb3b1` — **Task 2:** `save_answer` notlandırma → `QuestionContent` (JOIN gerekmedi, paylaşılan PK). 3 mutasyon öldürüldü
- `398a6a5de` — **Task 3:** `_select_beta_questions` `pipeline_metadata` → `QuestionMetadata` JOIN. 2 mutasyon öldürüldü. Diff 12/2, süpürme yok
- `12a35b7b5` · `b46f6ffda` · `05148d0ee` — plan + Task 7 tehlike bloğu + H1/H2 kararları + pre-commit CWD uyarısı

**Test durumu:** `tests/fast/test_osym_exam_engine_split.py` → **5 passed / 13 failed** (13'ü Task 4-7 kapsamı, beklenen).

### Fail Eden Testler

13 FAIL **kasıtlı** (Task 4-7 henüz yapılmadı): `TestEntityQueriesEagerLoad` 2 ·
`TestAnalyzePerformance` 4 · `TestSelectQuestions` 7. Hepsi `AttributeError: ... sinif
duzeyinde kullanilamaz`. Yeni kırık YOK.

### Engelleyiciler

- **`question_bank` = 0 satır (bu makine).** Uçtan uca doğrulama YAPILAMIYOR. Kabul kriteri
  sorgu-yapısı düzeyinde; hiçbir task "öğrenci akışı çalışıyor" kanıtı üretmiyor.
- **3389 dosyalık pre-existing kirli ağaç** (S210 Gemini devri) — ayrı triyaj.
- ~~`SKIP=pytest-fast` zorunlu~~ **FANTOM, ÇÜRÜTÜLDÜ** (aşağıya bak).

### Sonraki Adımlar (maks 5)

1. **Task 4** — `get_current_question` eager-load (`:567`). Sorgu kuruluyor ama `.options()` yok;
   `api/sinav.py:493-508` **12 split alan** okuyor → `MissingGreenlet` → HTTP 500.
   `navigate_to_question:817` aynı fonksiyona delege ediyor. 1 test, 1 mutasyon hazır.
2. **Task 5** — `get_subject_performance` eager-load (`:1313`), üç ilişki birden.
3. **Task 6** — `_analyze_performance` (`:1716` + iki `update()`), **tek commit** (seri bağlı).
4. **Task 7** — `_select_questions` 3-yollu JOIN (37 erişim). **Plandaki TEHLİKE BLOĞUNU
   OKUMADAN BAŞLAMA** — H1/H2 kararları orada.
5. **Task 8** — handoff düzeltmesi + `application/commands/sinav.py` ayrı plan.

Plan: `docs/superpowers/plans/2026-08-16-osym-exam-engine-split-gocu.md`

### Kararlar (gelecek session tekrar tartışmasın)

- **`SKIP=` GEREKMİYOR — ölçüldü.** `.git/hooks/pre-commit` kök config'i sabitliyor
  (`--config=.pre-commit-config.yaml`); `pytest-fast` `backend/.pre-commit-config.yaml`'da
  ve o config `git commit`'te **hiç yüklenmiyor**. S215-S218'den taşınan engelleyici fantom.
- **`pre-commit run --files`'ı `backend/` içinden ÇALIŞTIRMA** — yanlış config yüklenir,
  kapıda olmayan `black` devreye girer, dokunulmamış satırları süpürür ve `# nosec B311`
  yorumunu kapanış parantezine taşıyıp bandit bastırmasını kırabilir. Kökten koş.
- **H1 (boş havuz koşulsuz cache) → Task 7'de DÜZELT** (kod kararı, guard geri gelecek).
- **H2 (%15 IRT-ankraj kotası) → Task 7'de KAPAT** (`anchor_target = 0`), kod silinmez,
  gerekçe yorumla yazılır. Psikometrik ürün kararı, ayrı oturumda ele alınacak.
  **Kullanıcı onayı alındı (16 Ağu).**
- Mutasyon harness'lerinde **`read_bytes()`/`write_bytes()`** kullan — `write_text()`
  Windows'ta LF→CRLF çevirip geri-alım doğrulamasını yanlış-pozitif bozuyor.
- Commit ayırma: "ağaç kirli" gerekçe değil, `git stash push -- <dosya>` tek komut.

### Bu oturumun dersleri (kalıcı kayıt)

`.claude/lessons/ders_kaydi.yaml` → **8 yeni ders** (`L-s219-*`), hepsi `aktif` + kanıtlı,
bekçi 9/9 geçiyor. Uzun anlatım: `.claude/rules/audit-methodology.md` (5 yeni bölüm).

Özet: ilerleme sayacı da bir ölçüm aletidir · yanlış-**sıfır** tek kabul edilemez hata
türü · test paketi de bir dilim ölçer · "göç ettin mi" ≠ "koruduun mu" · **yorum CI'da
düşmez** · `pre-commit` yanlış CWD'den kapının ölçümü değil · `write_text()` geri alımı
bozar · "ağaç kirli" süpürme gerekçesi değil.

### Açık iş olarak düşen yeni kalemler

- `tests/integration/test_beta_practice_selection.py:32` — canlı `Question.pipeline_metadata`
  erişimi, `except Exception: return False` içinde → beta-havuz hazırlık kontrolü **sonsuza
  dek `False`**
- `backend/.pre-commit-config.yaml` commit anında **ölü** — tanımladığı her hook sessizce
  yüklenmiyor (gerçek `pytest-fast` kapısı dahil). Ya köke taşınmalı ya ölü işaretlenmeli
- Sayaçta 5 minor kalem (sıralama, KWARG satır numarası zincir başını gösteriyor, iki
  docstring satırı) — hiçbiri yanlış-sıfır üretemez

---

## Session Handoff — 2026-08-16 (S218)
**Branch:** feature/self-evolution-optimization
**Son commit:** 7febaeac9 fix(backend): placement_assessment_api.py _check_correctness — QuestionContent'e çevrildi (#485)
**Uncommitted:** temiz (bu session'ın dosyaları). 3388 dosyalık pre-existing kirli ağaç (S210 Gemini devri) var, bu session'a ait değil — ayrı triyaj görevi. **Push edilmedi — kullanıcı onayı bekliyor.**

### Yapılanlar
- `backend/api/placement_assessment_api.py:281-302` — `_check_correctness`'taki `QuestionBankItem.correct_answer` (kolon-select) `QuestionContent`'e çevrildi (`7febaeac9`, #485). JOIN gerekmedi: dosyada `QuestionBankItem`'ın başka kolonu kullanılmıyordu, `QuestionContent.id` `question_bank.id` ile aynı paylaşılan PK.
- `backend/tests/fast/test_placement_assessment_api_split.py` — 7 yeni test, mutasyonla çivili (`git stash push -- <dosya>` ile eski kod geri konunca 7/7 aynı AttributeError'la düştü, sonra geri alındı)
- Yan bulgu — dosyada pre-existing pre-commit borcu (dokunulmayan kod): `_store_session`/`_load_session` pickle kullanımı (bandit B403×2 + B301) + mypy no-any-return (satır 301, `row[0]: Any`). Kontrol kolu: `pre-commit run bandit/mypy --files` stash'lenmiş HEAD'e karşı çalıştırıldı, ikisi de zaten vardı. Inline `# nosec`/`# type: ignore` ile işaretlendi, davranış değiştirilmedi.
- `SKIP=kiro2-api-import-smoke` (kullanıcı onayıyla) — değişen dosyayla ilgisiz WinError 127 ortam kusuru (`api.rag`/`api.youtube_routes`/`api.v1.semantic_search`, S211'den beri bilinen)

### Fail Eden Testler
YOK — yeni 7 test + `tests/unit/test_exam_event_wiring.py` (6 test, aynı modülü tüketiyor) hepsi PASS

### Engelleyiciler
- `pytest-fast` FK fixture kırığı (S215'ten devir) — backend commit'leri hâlâ `SKIP=` zorunda, bu turda dokunulmadı
- `kiro2-api-import-smoke` WinError 127 — S211'den beri her `api/` commit'inde SKIP gerektiriyor, kök neden hâlâ açık
- 3388 dosyalık kirli ağaç (S210 Gemini devri) — bu session'a ait değil, ayrı triyaj bekliyor

### Sonraki Adımlar (maks 5)
1. #485 devamı — `core/osym_exam_engine.py` (1 erişim) veya 4'lü grup (`difficulty_classification_service.py` · `placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py`, 2 erişim/dosya)
2. `git push` bekliyor (kullanıcı onayı gerekir)
3. `pytest-fast` FK fixture kırığı — ayrı görev, birikmeden kapatılmalı
4. `kiro2-api-import-smoke` WinError 127 kök nedeni — ayrı görev, her `api/` commit'ini SKIP'e zorluyor
5. Kirli ağaç triyajı (3388 dosya)

### Kararlar (gelecek session tekrar tartışmasın)
- 5 adımlı kabul kriteri değişmedi (derle → `get_final_froms` → eager-load ölçümü → gerçek model testi → mutasyon)
- Kolon-select sorgularda (entity-select değil), JOIN'e ihtiyaç YOKSA (başka split-tablo kolonu kullanılmıyorsa) doğrudan split tabloya filtrelemek yeterli — JOIN eklemek gereksiz karmaşıklık olurdu
- pre-commit borcu (bandit/mypy) keşfedilirse aynı dosyada: kontrol kolu (`pre-commit run <hook> --files`, stash'li) ile HEAD'de zaten var olduğu doğrulanmadan işaretleme yapılmaz

---

## Session Handoff — 2026-08-16 07:53
**Branch:** feature/self-evolution-optimization
**Son commit:** f5b1f5a6c chore: S217 handoff — parent_service.py 1/1 kapandı; kalan 10/6 ÖLÇÜLDÜ
**Uncommitted:** temiz (bu session'ın dosyaları). 3388 dosyalık pre-existing kirli ağaç (S210 Gemini devri) var, bu session'a ait değil — ayrı triyaj görevi.

### Yapılanlar
- `backend/services/parent_service.py:572-580` — `get_child_performance`'taki `QuestionBankItem.subject_area` `QuestionMetadata` JOIN'ine çevrildi (`a74755a43`, #485)
- `backend/tests/fast/test_parent_service_split.py` — 6 yeni test, mutasyonla çivili (`git stash` ile eski kod geri konunca 6/6 aynı AttributeError'la düştü)
- `backend/pyproject.toml` — pre-existing S112 borcu (`parent_service.py:854`, dokunulmayan fonksiyon) per-file-ignore + inline `# nosec B112` ile işaretlendi
- `.claude/sessions/latest.md` — S217 handoff yazıldı (`f5b1f5a6c`)
- `git push origin feature/self-evolution-optimization` — `bafdaf0ba..f5b1f5a6c` gönderildi, push-secret-guard + reward-hacking-check PASS
- `memory/MEMORY.md` — 22.7KB→17.5KB kompakte edildi (S206/S209-S214 satırları birleştirildi, detay zaten topic dosyalarında duruyordu, bilgi kaybı yok) + S215-S217 index satırı eklendi

### Fail Eden Testler
YOK — yeni 6 test + mevcut parent-ilişkili 39 test (kpi_aggregation 22 + link_code 17) hepsi PASS

### Engelleyiciler
- `pytest-fast` FK fixture kırığı (S215'ten devir) — backend commit'leri hâlâ `SKIP=` zorunda
- 3388 dosyalık kirli ağaç (S210 Gemini devri) — bu session'a ait değil, ayrı triyaj bekliyor

### Sonraki Adımlar (maks 5)
1. #485 devamı — `api/placement_assessment_api.py` (1 erişim, `correct_answer`→muhtemelen `QuestionContent`) veya 4'lü grup (`difficulty_classification_service.py` · `placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py`, 2 erişim/dosya)
2. `pytest-fast` FK fixture kırığı — ayrı görev, birikmeden kapatılmalı
3. Kirli ağaç triyajı (3388 dosya)

### Kararlar (gelecek session tekrar tartışmasın)
- 5 adımlı kabul kriteri değişmedi (derle → `get_final_froms` → eager-load ölçümü → gerçek model testi → mutasyon)
- Kolon-select sorgularda (entity-select değil) eager-load N/A — bu dosyada yalnız sınıf-düzeyi risk vardı

---

## Session Handoff — 2026-08-16 (S217)
**Branch:** `feature/self-evolution-optimization` · **HEAD:** `a74755a43` · **Push:** ⏳ commit'li, henüz push edilmedi
**Ana iş:** #485 devamı — `services/parent_service.py` (1/1 kapandı)

`a74755a43` — **`get_child_performance`**: sınıf-düzeyi `QuestionBankItem.subject_area`
(kolon-select `answers_stmt` içinde, entity-select DEĞİL) `QuestionMetadata` JOIN'ine
çevrildi. Eager-load N/A (ölçüldü: sorgu `StudentAnswer.*` + `subject_area` kolonlarını
tek satırda unpack ediyor, instance-level lazy-load riski yok — offline_sync/osym_routes'tan
farklı olarak bu dosyada örnek-düzeyi risk YOK). `tests/fast/test_parent_service_split.py`
(6 test: derleme + tek FROM + SELECT kolonunun `question_metadata`'ya ait olduğu + JOIN
yapısı + WHERE + subject_area→subject_progress unpacking doğruluğu). Mutasyon: `git stash
push -- services/parent_service.py` ile eski kod geri konunca 6/6 test aynı AttributeError
ile düştü, sonra geri alındı (git status ile doğrulandı).

**Yan bulgu — dosyada pre-existing pre-commit borcu (dokunulmayan fonksiyon):**
`get_parent_dashboard_data`'daki `except Exception: continue` (S112/bandit B112),
kontrol kolu `git show HEAD:...| ruff check -` → 1 hata (HEAD'de zaten vardı). Ruff
tarafı `pyproject.toml` per-file-ignore, bandit tarafı inline `# nosec B112` ile
işaretlendi — davranış değiştirilmedi, sadece görünür kılındı.

**Kalan: 10 erişim / 6 dosya** (S216 sonu: 11/7).

### Sonraki Adımlar
1. #485 devamı — sıradaki: `api/placement_assessment_api.py` (1 erişim, `correct_answer`
   → muhtemelen `QuestionContent`), veya 4'lü grup (`difficulty_classification_service.py`
   · `placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py`,
   2 erişim/dosya). Aynı 5 adımlı süreç.
2. `pytest-fast` FK fixture kırığı — S215'ten devir, hâlâ açık.
3. `git push` — S215+S216+S217 birlikte bekliyor (kullanıcı onayı gerekir).

---

## Session Handoff — 2026-08-16 (S216)
**Branch:** `feature/self-evolution-optimization` · **HEAD:** `22aedbf40` · **Push:** ⏳ commit'li, henüz push edilmedi
**Ana iş:** #485 devamı — `services/offline_sync_service.py` (1/1 kapandı)

`22aedbf40` — **`build_sync_package`**: sınıf-düzeyi `QuestionBankItem.subject_area` WHERE'i
`QuestionMetadata` JOIN'ine çevrildi. **Ayrıca** sayaç görmediği bir örnek-düzeyi risk ölçüldü
(S214 dersiyle aynı desen): `select(QuestionBankItem)` ile entity seçilip döngüde
`q.question_text`/`.option_a-e`/`.correct_answer` (content), `.subject_area` (metadata_info),
`.difficulty_level` (statistics) okunuyordu — üçü de `lazy='select'`, async oturumda
eager-load'suz erişim `MissingGreenlet` atardı. 3 ilişki için `selectinload` eklendi.
`tests/fast/test_offline_sync_service_split.py` (7 test); mutasyon: eski kod geri konunca
**3/7 test düştü** (eager-load yapısı, JOIN, subject WHERE) — 4 test (compile, is_active,
business-logic mock, empty-list) subject=None olduğu için eski koda karşı da geçiyordu,
bu beklenen (mnemonic testindeki business-logic testiyle aynı sınırlama: mock session lazy-load
tetiklemiyor). Ruff clean. `process_sync_results`/diğer offline_sync testleri (9+6) regresyonsuz.

**Kalan: 11 erişim / 7 dosya** (S215 sonu: 12/8).

### Sonraki Adımlar
1. #485 devamı — sıradaki en küçük: `services/parent_service.py` veya `api/placement_assessment_api.py`
   (1 erişim), veya 4'lü grup (`difficulty_classification_service.py` · `placement_assessment_service.py`
   · `irt_daemon.py` · `mega_feature_tasks.py`, 2 erişim). Aynı 5 adımlı süreç.
2. `pytest-fast` FK fixture kırığı — S215'ten devir, hâlâ açık.
3. `git push` — S215 + S216 birlikte bekliyor (kullanıcı onayı gerekir).

---

## Session Handoff — 2026-08-16 (S215)
**Branch:** `feature/self-evolution-optimization` · **HEAD:** `3a1aabd0d` · **Push:** ⏳ commit'li, henüz push edilmedi
**Ana iş:** #485 — `question_bank` 69-alan split'inin JOIN göçü (S210-S214 devamı)
**Uncommitted:** bu işin dosyaları **temiz**. (Ağaçtaki 3388 kirli dosya = Gemini S210 devri, ayrı görev.)

### İlerleme — ÖLÇÜLDÜ (aynı script, kontrol kolu S213'te doğrulanmıştı)

**Kalan: 12 erişim / 8 dosya** (S214 sonu: 14/9 — bu turda 2 erişim/1 dosya kapandı, arithmetik ile birebir örtüştü).

```
python -c "import re,sys;sys.path.insert(0,'.');from models.question_bank import QuestionContent,QuestionMetadata,QuestionStatistics;
d={c.name for t in (QuestionContent,QuestionMetadata,QuestionStatistics) for c in t.__table__.columns if c.name!='id'};
from pathlib import Path;[print(len([m for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8')) if m.group(1) in d]),p) for x in ('services','api','core','app','tasks') for p in Path(x).rglob('*.py') if '__pycache__' not in p.parts and any(m.group(1) in d for m in re.finditer(r'QuestionBankItem\.(\w+)',p.read_text(encoding='utf-8',errors='ignore')))]"
```

| # | Dosya | Erişim |
|---|---|---|
| 1 | `services/difficulty_classification_service.py` · `services/placement_assessment_service.py` · `core/irt_daemon.py` · `tasks/mega_feature_tasks.py` | 2 ×4 |
| 2 | `services/offline_sync_service.py` · `services/parent_service.py` · `api/placement_assessment_api.py` · `core/osym_exam_engine.py` | 1 ×4 |

### Yapılanlar

`3a1aabd0d` — **`backend/api/osym_routes.py` (8/17)** — `auto_assign_anchors()`'daki 2 sınıf-düzeyi
`QuestionBankItem.subject_area` erişimi (alan artık `QuestionMetadata`'da) JOIN'e çevrildi.
`id`/`is_anchor` split edilmedi, dokunulmadı — order_by ve `q.is_anchor = ...` aynen kaldı.
Eager-load **N/A** (ölçüldü: 2 `select(QuestionBankItem)`, ikisi de yalnız `is_anchor` yazıyor,
instance-level, split tabloya dokunmuyor). + `tests/fast/test_osym_routes_split.py` (6 test),
mutasyon **3/3 öldürüldü** (WHERE reverti → AttributeError, JOIN'siz kartezyen → `get_final_froms()==2`,
`order_by` kaybı).

**Yan bulgu — dosya HEAD'de hiç commit edilmemişti** (S210 Gemini devrinden kalma çalışan-ağaç
içeriği: `analyze_osym_pdf`/`auto_assign_anchors`/`run_equating` hiçbiri git'te yoktu). Bu yüzden
`pre-commit run --files` baseline'ı S211-S214'ten farklı bir sınıf borç çıkardı:
- mypy: `bloomLevel: int = 3` iki kez tanımlıydı (no-redef) — silindi.
- ruff B007: `batch_generate`'te kullanılmayan döngü değişkeni `i` — `_i`'ye çevrildi (dokunulmayan fonksiyon, tek-karakter, sıfır risk).
- ruff N815 ×4 (`examType`/`bloomLevel` — frontend camelCase JSON sözleşmesi) + RET504 ×2
  (`generate_question`/`validate_question`, ara değişken) — **dokunulmayan fonksiyonlarda,
  pre-existing.** `pyproject.toml` `per-file-ignores`'a `"api/osym_routes.py" = ["N815", "RET504"]`
  eklendi (5 emsal aynı desende zaten var: `multi_layer_cache.py`, `osym_exam_engine.py`,
  `soru_bankasi_service.py`, `admin.py`, `test_golden_flows.py`).

### Fail Eden Testler
- **Yeni testler: 6/6 PASS.** Mutasyon 3/3.
- ⚠️ **PRE-EXISTING, dokunulmadı, YENİ BULGU:** `pytest-fast` pre-commit hook'u (`pass_filenames:
  false`, `files:` filtresi yok → her backend commit'inde koşuyor) şu an KIRIK —
  `tests/unit/test_fsrs_card_persistence.py::test_fsrs_card_insert_persists_core_fields`
  FK ihlaliyle düşüyor (`bkt_states.student_id` → `users` tablosunda yok), ardından aynı
  worker'daki `test_bkt_record_answer_batch1b*.py` `PendingRollbackError` ile ERROR veriyor
  (aynı transaction'ın devamı). #485/`question_bank` ile **ilgisi yok** — BKT/FSRS test
  fixture'ında eksik `users` seed satırı. Kullanıcı onayıyla `SKIP=pytest-fast` ile commit'e
  devam edildi. **Bu turda çözülmedi, ayrı görev gerekiyor.**
- `kiro2-api-import-smoke` — bilinen ortam kusuru (WinError 127), kontrol kolu değişmedi.

### Engelleyiciler
- **Yeni:** `pytest-fast` hook'u kırık — yukarıya bkz. Backend'e dokunan HER commit bunu
  SKIP etmek zorunda kalacak ta ki fixture düzelene kadar.
- Kökte `models/` = YOLO ağırlık klasörü, `kiro2-api-import-smoke` kırık — değişmedi (S211-S214).

### Sonraki Adımlar
1. **#485 devamı — `services/offline_sync_service.py` (1 erişim) veya `services/difficulty_classification_service.py` (2 erişim).** Aynı 5 adımlı zorunlu sıra (S214 handoff'undaki liste).
2. **YENİ: `pytest-fast` FK fixture kırığı.** `test_fsrs_card_persistence.py` + `test_bkt_record_answer_batch1b*.py` — `users` tablosuna eksik seed satırı ekle veya fixture'ı `users` FK'sini karşılayacak şekilde düzelt. #485 kapsamı DIŞINDA, ayrı görev — ama her backend commit'i şu an bunu SKIP etmek zorunda, biriktirmeden kapatılmalı.
3. `git push` bekliyor (kullanıcı onayı gerekir).
4. `tests/test_curator_api.py`'nin 2 pre-existing kusuru (stale mock + celery hang) — S213'ten devir.
5. Kirli ağaç triyajı (3388 dosya) · `#444` Öğretmen Öğrenciler UI · `#467-471`.

### Kararlar (gelecek session tekrar tartışmasın)
- **Dosya hiç commit edilmemiş olabilir** (S210 devri) — bu durumda `pre-commit run --files`
  baseline'ı HEAD'e karşı değil, çalışan ağaca karşı ölçer; "kontrol kolu HEAD'de de var mı"
  sorusu bazı bulgular için (yeni eklenen fonksiyonlardaki N815 gibi) anlamsız hale gelir.
  Yine de karar aynı kalır: dokunulmayan fonksiyondaki borç per-file-ignore'a gider, dokunulan
  fonksiyondaki borç düzeltilir.
- **pytest-fast gibi unconditional pre-commit hook'ları** (`pass_filenames: false`, `files:`
  filtresiz) #485 dosyalarıyla hiç ilgisi olmayan bir hatayla kırılabilir. Kırıksa ve konu
  dışıysa `SKIP=` ile geç (kullanıcı onayı ile), ama görev listesine YENİ madde olarak düş —
  sessizce biriktirme.
- 5 adımlı kabul kriteri değişmedi (bkz. S214 handoff). **Skor: elden geçen 8 dosyanın 8'inde kusur.**

### Kalıcı kayıt nerede
- **Uzun anlatım:** `.claude/rules/audit-methodology.md`
- **Bellek:** `memory/MEMORY.md` S214 satırı → bu session S215 olarak eklenecek (ayrı adım)
