# A1 — Beta Havuzu Hedefli Temizlik (gerçek-öğrenci flag'leri)

**Tarih:** 2 Haziran 2026
**Track:** Track 1 / A1 (gerçek-öğrenci döngüsünü kapat)
**Tetikleyici:** İlk gerçek-öğrenci beta → 55 çözülmemiş flag (54 soru, 2 öğrenci)

## Bağlam

Beta sinyali kök-nedeni canlı doğruladı: flag'lerin **%85'i render/OCR**
(içerik değil). `false &&` görsel-gizleme (K4) + garble (K2) baskın.

| flag_type | beta'da (vp=true) | beta dışı | aksiyon |
|-----------|-------------------|-----------|---------|
| figure_needed | 35 | 0 | beta'dan çıkar (içerik korunur) |
| incomplete_text | 9 | 3 | beta'dan çıkar + re-OCR adayı |
| circular | 1 | 0 | A3/curator |
| wrong_answer | 3 | 1 | A3/curator (cevap hatası) |
| other | 1 | 2 | curator |

## Yapılan (non-destructive)

- **Backup:** `question_bank_a1_beta_cleanup_backup_20260602` (44 satır:
  id, quality_review_status, pipeline_metadata, correct_answer)
- **35 figure_needed** → `pipeline_metadata.verified_provisional = "false"`
  + `beta_pull = {reason:"figure_needed", run:"a1_beta_cleanup_20260602"}`
- **9 incomplete_text** → `verified_provisional="false"` +
  `beta_pull = {reason:"garbled_incomplete", reocr_candidate:true}`
- **44 flag** → `resolution="confirmed"` (öğrenci bildirimi doğru),
  `resolved_by="system_a1_beta_cleanup_removed_from_beta"`
- **DOKUNULMADI:** `correct_answer`, `quality_review_status`, `status`
  (hepsi `auto_judged_high` kaldı — figür gelince beta'ya geri dönebilir)

## Doğrulama (hepsi yeşil)

- Beta havuzu: **2734 → 2690** (−44)
- figure_needed çözülmemiş flag: **0** (hepsi resolve)
- incomplete_text kalan: 3 (beta-dışı, doğru bırakıldı)
- beta_pull tag: 35 figure_needed + 9 garbled_incomplete
- correct_answer diff (backup vs live): **0**

## Bilinen kısıt (self-healing)

`osym_exam_engine.py:1282` in-process `TTLCache("BETA:verified_provisional:all",
ttl=3600)`. Çıkarılan 44 soru ≤1 saat cache'te kalabilir. Restart edilmedi
(2 aktif öğrenci session'ı korundu); cache 1 saatte kendiliğinden yenilenir.
Sorular zaten flag'li olduğundan kullanıcı zararı yok.

## Rollback

```sql
UPDATE question_bank qb SET pipeline_metadata = b.pipeline_metadata
FROM question_bank_a1_beta_cleanup_backup_20260602 b WHERE qb.id = b.id;
```

## Sonraki

- **A2:** Sistemik figür-bağımlı süpürme (tüm 2,690 havuzu — flag beklemeden)
- **A3:** Curator manuel kuyruğu (202 concept + splits + wrong_answer flag'leri)
