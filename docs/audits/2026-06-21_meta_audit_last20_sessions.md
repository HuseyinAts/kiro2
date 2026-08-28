# Meta-Audit — Son ~20 Oturum (2026-06-21)

**Yöntem:** Canlı-DB bütünlük taraması (12 sorgu) + workflow agent-team (5 boyut × kanıt-zorunlu) + adversarial phantom-filtre. Hiçbir bulgu eski audit-doc'undan kopyalanmadı; her iddia canlı kod/DB/git'ten doğrulandı (23 May meta-audit'te P0'ların %87'si phantom çıkmıştı — bu sefer phantom-filtre fazı zorunlu kılındı).

**Sonuç:** 17 doğrulama kontrolünden **14 temiz**, **4 gerçek bulgu düzeltildi**, **2 phantom elendi**. Tüm fix'ler reversible; correct_answer/is_active hiç dokunulmadı.

## A. Canlı-DB Bütünlük Taraması (12 kontrol)

| # | Kontrol | Sonuç | Verdict |
|---|---|---|---|
| I1 | v_safe'te status-dışı / inactive satır | 0 / 0 | ✅ |
| I2 | rejected ∧ is_active=true (lesson#31 sızıntı) | 0 | ✅ |
| I3 | status dağılımı (drift) | rejected 56.652 / unverified 39.453 / pending 36.923 / **auto_judged_high 34.378** / legacy 20.231 / bronze 197 | ✅ (blind-solve+PoolA ile auto_high büyüdü) |
| I4 | v_safe toplam | 25.755 | ✅ |
| **I5** | **vp=true ∧ status≠auto_high (bayat flag)** | **200** | ⚠️→**FIX** |
| I6 | v_safe'te content-signal'siz | 0 | ✅ |
| I7 | backup tabloları (reversibility) | 36 | ✅ |
| I8 | v_safe duplicate soru_hash | 0 | ✅ |
| I9 | blind-solve flag'li (w1-25+PoolA) | 16.031 | ✅ |
| I10 | v_safe null/orphan primary_topic | 0 / 0 | ✅ |
| I11 | v_safe geçersiz correct_answer (A-E dışı) | 0 | ✅ |
| I12 | answer-key düzeltme markerları | 1.265 | ✅ (S195/math_promote izli) |

## B. Kod-Audit Agent-Team (5 boyut → 5 bulgu → adversarial verify)

| ID | Alan | İddia | İlk verdict | Adversarial | Aksiyon |
|---|---|---|---|---|---|
| **F4** | Şema/migration | beta_vp partial index DB'de yok (migration stamped, index absent) | BROKEN/P1 | **GERÇEK** | ✅ `idx_qbank_verified_provisional` CONCURRENTLY oluşturuldu (indisvalid=t) |
| **F2** | Kalite pipeline | ölü `cross_validate_answers (1).py` A-bias fix'i yok, kazara çalıştırılabilir | GAP/P2 | **GERÇEK** | ✅ silindi (kanonik korundu) |
| **F5** | Test/build | Pydantic `validate` alanı BaseModel.validate'i gölgeliyor (UserWarning) | GAP/P2 | **GERÇEK** | ✅ `should_validate`(alias='validate'), API sözleşmesi korundu, ruff temiz |
| P1 | Kalite pipeline | lesson#31 kuralı `_ACCEPTED_QUALITY_STATUS` sabitine atıf, kod değişmiş | GAP/P2 | **PHANTOM** | ❌ aksiyon yok (testing.md o sabite atıf yapmıyor — yanlış okuma) |
| P2 | Auth/middleware | `setup_csrf_protection` middleware'i 2× ekliyor | GAP/P2 | **PHANTOM** | ❌ aksiyon yok (fonksiyon main.py'de hiç çağrılmıyor = ölü kod, zararsız) |

### Doğrulanan (HOLDS) — son 20 oturumun fix'leri canlı
- **A-bias fix** `cross_validate_answers.py:114` ai_upgrade tier=0.65 (S194) ✅
- **lesson#31 servis sızıntısı** → `soru_bankasi_service._safe_for_beta_gate()` v_safe_for_beta view ile TÜM öğrenci selektörlerinde (commit 13eb6b07a, eski sabitten daha güçlü) ✅
- **Mühürlü scriptler** validate_3tier_selective + 2 Tier-H: `ALLOW_DEPRECATED_*`+sys.exit(2) DB-yazımından önce ✅
- **CSRF JSONResponse** (raise değil) + Bearer early-return (commit cf4147b92) ✅
- **IDOR** verify_student_access 8 çağrı await+db ✅
- **Router registration** test mevcut, 9/9 app/api router kayıtlı ✅
- **KVKK** student_profiles.veli_email kolonu DB'de ✅

## C. Uygulanan Fix'ler + Doğrulama

| Fix | Tür | Backup/Geri-alma | Doğrulama |
|---|---|---|---|
| I5 — 200 bayat vp flag strip | DB | question_bank_stale_vp_backup_20260621 (200) | I5 tekrar=0, v_safe değişmedi (25.755) |
| F4 — beta_vp index oluştur | DB | DROP INDEX (migration downgrade) | pg_index indisvalid=t |
| F5 — Pydantic alan rename | Kod | git revert | import smoke OK (alias kabul), ruff passed |
| F2 — ölü duplicate sil | Disk (gitignored) | git'te yok; kanonik dosya duruyor | kanonik cross_validate_answers.py korundu |

**Commit:** e4f13b99a (pushed). **Phantom oranı:** 2/5 (%40) — phantom-filtre çalıştı.

## D. Açık (düzeltilmeyen, bilinçli)
- 253 `poolA_answer_dispute` + 96 `poolA_subject_2nd`: 3.farklı-model sinyali bekliyor (A-bias gereği aynı-model gold sayılmaz).
- CSRF double-add ölü kodu: zararsız (çağrılmıyor); temizlik P3.
- Pool A kalan ~11.301 fallback: sonraki dalgalar.

---
*Workflow: w38f5d6ro (kod-audit) + canlı DB sweep. Hiçbir P0 yok. Tüm kritik invariant'lar (correct_answer/is_active dokunulmadı, v_safe sızıntı yok) doğrulandı.*
