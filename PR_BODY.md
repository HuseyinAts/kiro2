# DB Audit (5 geçiş) + Remediation R1–R5

## Özet
Production veritabanının (host PG18 `:5434/kiro2`, 276 tablo / 1.83 GB) tam audit'i + 5 veri-bütünlüğü remediation'ı. Tüm ölçümler salt-okunur ve evren-level; tüm değişiklikler **backup'lı, atomik, geri-alınabilir**, dry-run→apply→verify döngüsüyle uygulandı. Detaylı rapor: [`docs/audits/2026-06-10_full_db_audit.md`](docs/audits/2026-06-10_full_db_audit.md) (§J = remediation log).

## Audit bulguları (öne çıkanlar)
- 276 tablonun **161'i boş** (kullanılmayan özellik şeması); ~75 kullanıcı → seed/dev ortamı, tek ciddi varlık 187K soru bankası.
- `embedding vector(768)` dolu (147K) ama **ANN/vector index yoktu** → semantik arama tam tarama.
- `is_calibrated=82,530` ama %99.98'i `bootstrap_difficulty_prior` (öğrenci yanıtından değil); `irt_calibrated=0`. CAT motoru bunları "kalibre" sanıyordu.
- `student_answers` (161,910) = **load-test artığı**: 4 test hesabı, sabit 15.5s, uniform şıklar, `is_correct` boş, %99.8 orphan question_id.
- 74 FK-siz referans kolonu (enforcement gap); 97 index'siz FK; 19 ölü kolon; kaynak künyesi %99.9 kayıp.

## Remediation (R1–R5)

| # | Aksiyon | Önce → Sonra | Backup / Geri-alma |
|---|---|---|---|
| R1 | `student_answers` load-test temizliği (4 test hesabı) | 161,910 → **0** | `student_answers_backup_20260610` |
| R2 | `is_calibrated` bootstrap-flag reset (yanıt yok → FALSE) | TRUE 82,530 → **196** | `question_bank_iscalib_reset_backup_20260610` |
| R3 | `question_bank.embedding` HNSW index (vector_cosine_ops) | ANN yok → `idx_qb_embedding_hnsw` | migration `b2f1a9c7d3e4` |
| R4 | exam_sessions/exam_questions test temizliği (CASCADE) | 323 / 28,508 → **0 / 0** | `exam_sessions_backup_20260610`, `exam_questions_backup_20260610` |
| R5 | FK `student_answers.question_id → question_bank.id` | FK yok → eklendi | migration `c3d2e1f0a9b8` |

Doğrulama: R2 sonrası kalan 196 TRUE'nun hepsi gerçek `kiro2_learning_events` destekli. Tüm post-apply sayımları verify edildi.

## Kök neden (veriyle)
- **R2:** `bootstrap_irt_params.py` `is_calibrated`'ı difficulty→sabit prior ile TRUE yapmış; düzeltme script'i `irt_reset_bootstrap_flags.py` hiç koşmamış. `irt_calibrated` ayrı 4PL bayrağı, finalize edilmemiş.
- **R1/R4:** Tüm satırlar `test@/admin@/ogrenci@/beta01@kiro2.com` hesaplarına ait; gerçek kullanıcı verisi yok.

## Güvenlik / geri-alma
- Her remediation öncesi tam backup tablosu; mismatch'te otomatik rollback.
- 5 backup tablosu rollback için duruyor (güven periyodu sonrası DROP).
- Geri-alma SQL'leri rapor §J'de + script footer'larında.

## Migration zinciri
`5aabf9a6c658` (mevcut head) → `b2f1a9c7d3e4` (HNSW) → `c3d2e1f0a9b8` (FK).
⚠️ `5aabf9a6c658` ayrı commit'lenmeli (zincir tutarlılığı için bu PR'a dahil edilmeli).

## Kapsam dışı (etkilenmeyen)
- Bu branch ayrıca Session 138 dilbilimsel/eşzamanlılık/test düzeltmelerini de içeriyor.
- Lokaldeki uncommitted çalışma dosyaları ve `ENTERPRISE_*` artefaktları bu PR'a dahil değil.

## Kalan iş (ayrı)
- **Aktif havuz inceleme** (98,361 unverified/pending) — judge pipeline; bütçe (~$5–7K) + API key gerektirir, pilot (~$60) ile başlanmalı.
- 161 boş + 35 eski yedek tablo gözden geçir; json→jsonb (9 qb kolonu); tz'siz timestamp; 7 dup index.

## Test / doğrulama
- Tüm DB değişiklikleri salt-okunur dry-run + apply + post-verify ile yapıldı (script'ler `docs/audits/2026-06-10_db_audit_artifacts/`).
- Şema değişiklikleri (HNSW, FK) idempotent migration'larla yakalandı.
