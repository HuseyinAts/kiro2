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
