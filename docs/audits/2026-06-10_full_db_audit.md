# KIRO2 — Tam Veritabanı Audit (Şema + Veri-Kalitesi + Kök Neden)

**Tarih:** 2026-06-10
**Hedef:** host-native PostgreSQL 18, `host.docker.internal:5434/kiro2` (backend container `kiro2-backend` bu DSN ile bağlanıyor; server_addr 127.0.0.1)
**Kapsam:** 276 tablo + 7 view, 1.83 GB
**Yöntem:** Salt-okunur, backend'in kendi bağlantısı (psycopg2, AUTOCOMMIT) üzerinden 5 geçiş. Tüm sayılar **tam tarama** (sample değil). Truncation yok.
**Mega Audit Lock (S197):** Kullanıcı explicit override verdi (bu rapor onun talebiyle oluşturuldu).

---

## Metodoloji

| Geçiş | Script | Üretilen |
|---|---|---|
| 1 | `db_audit.py` | Şema envanteri, her tablo/sütun/tip/null/default/FK/index/constraint, her sütun null sayımı, FK orphan (tanımlı FK'ler), KIRO2 kalite kontrolleri |
| 2 | `db_audit2.py` | Değer dağılımları, çapraz-tablolar, kapsama, duplicate derinliği, encoding disambiguation |
| 3 | `db_audit3.py` | embedding/vector index, ID tip tutarlılığı, 7 view tanımı, staging, IRT history, rationale kalitesi, kullanıcı profili |
| 4 | `db_audit4.py` + text-mining | FK-siz linklerde mantıksal orphan; eksik-FK / fazlalık-index / tip-koku taraması (parser, 13,148 satırın tamamı) |
| 5 | `db_audit5.py` | Kök neden forensiği (is_calibrated kaynağı; student_answers kaynağı) + kod incelemesi |

Ham çıktılar ve script'ler: `docs/audits/2026-06-10_db_audit_artifacts/` (`db_audit_output.txt` 13,148 satır, `db_audit2..5_output.txt`, `db_audit*.py`, `db_audit_full.sql`, `find_db.py`).
Yeniden üretilebilir: evet (script'ler salt-okunur, AUTOCOMMIT).

**Audit-methodology uyumu:** Sayılar evren-level (full `count(*)`), sample değil. İlk geçişte bir **null-yüzdesi ters okuma hatası** yapıldı (§Düzeltmeler) ve ölçümle düzeltildi. "FK yok → bütünlük kırık" varsayımı pass-4 ölçümüyle daraltıldı. "IRT kalibre" iddiası `irt_method` ölçümüyle çürütüldü.

---

## Yönetici Özeti

KIRO2 DB'si bir **seed/dev** ortamı: ~75 kullanıcı, 161/276 tablo boş, çekirdek öğrenme tabloları çok küçük. Tek ciddi varlık **187,834 satırlık soru bankası**. En yakıcı üç sorun:

1. **IRT/kalibrasyon empirik değil.** `is_calibrated=TRUE` olan 82,530 sorunun 82,517'si `bootstrap_difficulty_prior` (difficulty→sabit prior), gerçek yanıt-destekli yalnız 196. `irt_calibrated` (gerçek 4PL bayrağı) = 0. Adaptif motor bunları kalibre sanıp önceliklendiriyor.
2. **`student_answers` (161,910) load-test artığı.** 161,658 satır 2026-06-09'da tek koşuda, 4 sahte kullanıcı, sabit 15.5s, uniform şıklar, grade'siz, question_id'ler güncel bankada yok (%99.8 orphan). Gerçek öğrenme sinyali değil.
3. **Aktif soru havuzunun %88.7'si incelenmemiş** (110,895 aktiften yalnız 12,534'ü yargılı-iyi).

---

## A. Yapısal Bulgular

### A1. 161/276 tablo boş (%58) — kullanılmayan özellik şeması
Tüm özellik alanları hiç doldurulmamış: forum, düello, Khan, EBA video (7 tablo), study rooms + whiteboard, öğretmen/veli/mentor akışları, FSRS review, quiz, referans veri (universities/departments), uyumluluk (KVKK/FERPA/COPPA), reasoning, nano_skills/q_matrix/DINA, notifications/sessions/audit_logs. (Tam liste: `db_audit_output.txt` Bölüm C + parser çıktısı.)

Satır ölçeği: 4 tablo ≥100K, 15 tablo 1K–100K, geri kalan <1000; ~73 gerçek dolu tablo.

### A2. embedding'de vektör index YOK
`question_bank.embedding` = `vector(768)`, pgvector **0.8.2 kurulu**, 147,196 vektör dolu — ama tablodaki 18 index'in hepsi **btree**. HNSW/ivfflat yok → semantik arama ANN index'siz (tam tarama). CLAUDE.md "pgvector HNSW deployed, 21ms" iddiası canlı şemada **yok** (phantom).

### A3. ID tip karmaşası
DB genelinde `id` kolonları: **193 varchar, 38 uuid, 31 integer**. `users.id`/`question_bank.id`/`questions.id`/`student_answers.id` varchar (içinde UUIDv5 string'i). Her join'de `::text` cast gerekiyor.

### A4. 74 FK-siz referans kolonu (enforcement gap)
`*_id`/`*_by` kolonu var ama FK constraint'i yok (dolu, yedek-olmayan tablolarda). Kritikler: `student_answers.question_id`, `kiro2_learning_events.{question_id,user_id,session_id}`, tüm soru-ailesi linkleri, `user_theta.user_id`, `bkt_states.topic_id`, `chat_sessions.user_id`. **Pass-4 ölçümü:** bunlar şu an çoğunlukla tutarlı (orphan yok) — yani DB-seviyesinde *latent risk* (gelecek koruması yok), mevcut bozulma değil. **Tek istisna `student_answers`** (§B2).

### A5. 97/248 FK index'siz (%39)
Çoğu `users(id)` → `ON DELETE CASCADE`. 135 FK users'a bakıyor (users=75 satır).

### A6. 7 fazlalık (duplicate) index
Aynı tablo + aynı kolon + aynı predicate: `question_bank` (`idx_qb_review_status_active` == `idx_qbank_status_active`), `dina_parameters`, `duel_ratings`, `knowledge_components`, `knowledge_points`, `league_memberships`, `topic_prerequisites`.

### A7. Tip kokuları
- **38 `json` (jsonb değil)** dolu tabloda — `question_bank`: `pipeline_metadata, kc_ids, q_matrix, solution_steps, secondary_topics, similar_question_ids, alternative_solutions, answer_equivalent_forms, misconception_tags`. `idx_qbank_beta_filter_rule` sorgu anında `::jsonb` cast'liyor (verimsiz).
- **30 `timestamp without time zone`** kolon (DB'nin geri kalanı timestamptz; TR saat diliminde karışım riski).

### A8. 35 yedek tablo (~50 MB)
`question_bank_*_backup_*` + `soft_fix_backup`. PK'sız tek tablolar bunlar. Disk sorunu değil (asıl boyut: `question_bank` 1.42 GB — embedding + jsonb), ama karışıklık.

### A9. Enum dağınıklığı
3 konu enum'u (`subjectarea`/`subjecttype`/`subjectexpertise`) + 2 zorluk enum'u (`questiondifficulty`/`questiondifficultylevel`). `subject_area` kolonu enum-bağlı değil (GEOMETRI/TARIH/EDEBIYAT/TDE enum'da yok).

---

## B. Veri-Kalitesi Bulguları

### B1. Aktif soru havuzu %88.7 incelenmemiş

| status | aktif | pasif |
|---|---|---|
| unverified | 61,481 | 1 |
| pending | 36,880 | 44 |
| auto_judged_high | 12,337 | 11 |
| bronze_clean | 197 | 0 |
| rejected | 0 | 56,652 |
| legacy_v3_unaudited | 0 | 20,231 |

Aktif = 110,895; yargılı-iyi yalnız 12,534 (%11.3). `human_verified`/`archived` statüleri tanımlı ama 0 satır (insan-doğrulaması hiç kullanılmamış). Her konuda %85–94 incelenmemiş.

### B2. `student_answers` (161,910) — load-test artığı, %99.8 orphan
- `question_id` → `question_bank`: **161,663 orphan (%99.8)**, yalnız 247 çözülüyor.
- `is_correct`: 45 true / 100 false / 161,765 NULL.
- Kaynak forensiği (§E2): bugünkü load-test.

### B3. 6,233 aktif mükerrer + çelişkili etiket
3,955 birebir-dup grubu (normalize=3,970 → gerçekten birebir). Aynı metin farklı `subject_area` + farklı kalite verdict taşıyor.

### B4. Kaynak künyesi kayıp
`source_book` %99.9 NULL (109 satır dolu), `source_page` %99.9 NULL — "405 kaynak kitap" iddiasına rağmen menşe izlenemiyor.

### B5. Embedding menşei yok
147,196 embedding'in 119,847'sinde (%81) `embedding_model` NULL.

### B6. 19 ölü kolon (question_bank) + DB-geneli 188 all-null kolon
`question_html, question_latex, question_audio_url, explanation_video_url, alternative_solutions, last_calibration_date, reviewed_by, irt_calibrated_at, answer_equivalent_forms, numeric_tolerance, mufredat_kazanim_id, mufredat_versiyon, dina_slip, dina_guess, diagram_type, alt_text, last_flagged_date, metadata_completeness_score, reviewed_at`. MEB müfredat + DINA tamamen boş. `question_bank_staging` 78 kolonun 22'si all-null.

### B7. Gerçek bozulma küçük
Newline/tab hariç control char: **179 satır**; ayrıca metinde **NUL byte** içeren satırlar var. 86,778 satırdaki control char zararsız `\n\t`.

### B8. misconception_tag %100 NULL
`question_option_rationales` (486,270 satır): is_correct False 389,016 / True 97,254; LLM üretimi (gemini-flash 416,090 + qwen3:8b 70,130 + gpt-4o-mini 50); 97,255 soru kapsıyor (%52). `misconception_tag` tamamen boş.

### B9. manual_review_queue %99.5 işlenmemiş
1,842 satır; decision boş 1,833, sadece 9 'replace'.

---

## C. Soru-Tablosu Ailesi

| tablo | satır | kapsama / not |
|---|---|---|
| `question_bank` | 187,834 | asıl varlık (1.42 GB) |
| `question_option_rationales` | 486,270 | 97,255 soru (%52), 0 orphan |
| `question_kc_mapping` | 168,283 | 167,559 soru (%89), 0 orphan |
| `question_math` | 37,088 | %20, 0 orphan |
| `exam_questions` | 28,508 | 22,083 distinct; 1,300 orphan (%4.6), ~1,149 legacy'ye |
| `questions` (legacy) | 36,381 | seed import 26 Oca 2026 (14 dk), hepsi `aktif=true`, %43 (15,662) qb ile metin çakışması, **0 FK referans** → ada |
| `osym_questions` | 0 | boş, FK hedefi → ölü |
| `student_question_responses` | 0 | boş → ölü |

---

## D. View'lar (7)

2'si pg_stat_statements gürültüsü. Gerçek 5:
- `v_safe_for_beta` / `v_safe_for_beta_unfiltered` (71,602 satır) — uygulamanın beta serve ettiği set; **ölü kolonları da expose ediyor**.
- `v_response_log` — `kiro2_learning_events`'ten (cat_answer/exam_answer/synthetic). Gerçek yanıt sinyali burada.
- `v_calibration_candidates` — soru başına ≥50 yanıt; 287 olayla ~0 aday.
- `vw_user_topic_mastery` — `kiro2_cat_sessions` (8 satır) → fiilen boş.

---

## E. Kök Neden Forensiği (veri + kod)

### E1. `is_calibrated=82,530` vs `irt_calibrated=0`

| Ölçüm | Değer |
|---|---|
| `irt_method='bootstrap_difficulty_prior'` (is_calibrated=TRUE içinde) | **82,517 / 82,530** |
| calibration_history yok (saf flag) | 82,170 |
| gerçek EM history (se>0) | 360 |
| gerçek yanıt-destekli (learning_event var) | 196 |
| `irt_calibrated` TRUE | **0** |

**Kök neden:** `is_calibrated=TRUE`'nun %99.98'i `backend/scripts/bootstrap_irt_params.py` tarafından set edilmiş — `difficulty_level`'ı sabit a/b/c prior'a map'liyor (öğrenci yanıtından değil). `irt_calibrated`, migration `20260126_add_irt_4pl_calibration.py` ile eklenen **ayrı** 4PL bayrağı; finalize eden pipeline hiç çalışmamış → 0. İki nesil bayrak yan yana (legacy `is_calibrated` bootstrap'la kirli + yeni `irt_calibrated` boş). Düzeltme script'i `backend/scripts/irt_reset_bootstrap_flags.py` **çalıştırılmamış** (docstring'i tam bu durumu anlatıyor). CAT motoru (`app/services/cat_session.py`) `is_calibrated=TRUE`'yu önceliklendiriyor → bootstrap-prior soruları kalibre sanıyor.

### E2. `student_answers` 161,910 satır kaynağı

| Sinyal | Değer | Yorum |
|---|---|---|
| answered_at | **161,658 satır 2026-06-09** | tek bulk koşu |
| distinct session → kullanıcı | 159 → **4 user** | seed user |
| session başına satır | ort 1,018, maks 3,937 | gerçek sınav imkansız |
| response_time_seconds | maks=ort=**15.5s**, stddev 0.6 | sabit → scriptli |
| selected_answer | A/B/C/D/E ≈ 32,300'er | uniform → scriptli |
| is_correct | %99.9 NULL | servis insert'te grade etmiyor (`exam_answer_tracking_service.py` satır 428 `is_correct=None`) |
| question_id | UUIDv5, %99.8 bankada yok | test setine bakıyor |

**Kök neden:** 161,658 satır **bugün çalıştırılan bir load-test / workload-simülasyonu** (`backend/_pilots/audit_locust_load_test.py` / `audit_workload_simulator.py` türü) çıktısı. exam-answer endpoint'i 4 sahte kullanıcıyla dövülmüş; servis insert'te grade etmediği için `is_correct` NULL; grading hiç çağrılmamış. Gerçek öğrenci aktivitesi değil.

---

## F. İyi Durumda Olanlar (phantom-doğrulandı)

- **63 check constraint sağlam** (IRT sınırları, bloom 1-6, correct_answer A-E, quality 0-100, `times_correct<=times_asked`, selected_answer A-E).
- **0 FK orphan** (tanımlı 248 FK için referans bütünlüğü tam).
- `rejected` (56,652) + `legacy_v3_unaudited` (20,231) **hepsi pasif** → Lesson #31 sızıntısı kapalı.
- Çekirdek öğrenme tabloları (FK'siz olsa da) şu an tutarlı: `kiro2_learning_events` (287) %100 temiz, `bkt_states/user_theta/zpd_history/student_abilities/fsrs_cards/daily_plans/chat_sessions` 0 orphan.
- `subject_area` %100 UPPERCASE; tek alembic head (`5aabf9a6c658`); pgvector kurulu; encoding UTF8.

---

## G. Düzeltmeler (önceki tur hataları — ölçümle düzeltildi)

1. **metadata enrichment** ilk geçişte "%11" denildi → null-yüzdesi ters okumaydı; doğrusu **%89** (167,559 soru). Seyrek olan 3PL `irt_a/b/c` (%1.3, 2,364).
2. **Yedek tablolar 1.8GB değil ~50MB**; asıl boyut question_bank 1.42GB.
3. **Control char 86,898 değil**; gerçek bozulma ~179 + NUL.
4. **"74 FK-siz link = bütünlük kırık"** varsayımı → pass-4 ölçümü: çoğu tutarlı, tek kırık `student_answers`.

---

## H. Ciddiyet Tablosu

| # | Bulgu | §  | Ciddiyet |
|---|---|---|---|
| 1 | IRT/başarı seed (`bootstrap_difficulty_prior`, irt_calibrated=0) | E1/B | **P0** |
| 2 | `student_answers` load-test artığı (%99.8 orphan, is_correct boş) | E2/B2 | **P0** |
| 3 | Gerçek yanıt sinyali 287 olay → kalibrasyon imkansız | D/E | **P0** |
| 4 | Aktif havuz %88.7 incelenmemiş | B1 | **P0** |
| 5 | embedding vektör index yok (HNSW phantom) | A2 | P1 |
| 6 | 161 boş tablo (şema şişkinliği) | A1 | P1 |
| 7 | 6,233 aktif mükerrer + çelişkili etiket | B3 | P1 |
| 8 | Kaynak künyesi %99.9 kayıp | B4 | P1 |
| 9 | manual_review %99.5 işlenmemiş | B9 | P1 |
| 10 | legacy `questions` ada + exam_questions dual-ref | C | P1 |
| 11 | 74 FK-siz referans (latent enforcement gap) | A4 | P1 |
| 12 | 19 ölü kolon + misconception/MEB/DINA boş | B6/B8 | P2 |
| 13 | 97 index'siz FK, ID tip karmaşası, enum sprawl | A3/A5/A9 | P2 |
| 14 | 7 fazlalık index; 38 json(jsonb değil); 30 tz'siz timestamp | A6/A7 | P2 |
| 15 | embedding %81 model'siz; 179+NUL corrupt satır | B5/B7 | P2 |

---

## I. Önerilen Aksiyonlar (write → plan + onay + TDD)

**P0:**
- `irt_reset_bootstrap_flags.py --dry-run` → uygula: `is_calibrated`'ı bootstrap-flag'lerden temizle. Veya `is_calibrated`/`irt_calibrated` semantiğini tek bayrakta birleştir + CAT motorunun önceliklendirmesini gözden geçir.
- `student_answers` load-test artığını ayıkla (`answered_at::date='2026-06-09'` + 4 test-user). Load-test'i prod DB'ye yazmaktan ayır (ayrı test DB / temizlik adımı). `is_correct` grading'i bağla.
- Aktif havuz inceleme stratejisi: 98,361 unverified/pending için yargı pipeline'ı.

**P1/P2:**
- embedding HNSW index (`vector_cosine_ops`).
- 161 boş tablo gözden geçir/sil; 35 yedek + 2 ölü tablo (`osym_questions`, `student_question_responses`).
- `users(id)` FK index'leri; 7 dup index drop; `student_answers.question_id` vb. kritik FK'ler (önce temizlik).
- `json`→`jsonb` (question_bank jsonb kolonları); tz'siz timestamp düzeltme.
- 19 ölü kolon kaldır; duplicate soru dedup; kaynak künyesi geri-doldurma.

---

---

## J. Remediation Log (2026-06-10, aynı gün uygulandı)

Tümü backup'lı + atomik (eng.begin), dry-run → apply → verify; salt veri değişikliği (kod/git değil).

| # | Aksiyon | Önce → Sonra | Backup tablosu |
|---|---|---|---|
| R1 | `student_answers` load-test temizliği (P1: 4 test hesabı — test@/admin@/ogrenci@/beta01@kiro2.com) | 161,910 → **0** | `student_answers_backup_20260610` (161,910) |
| R2 | `is_calibrated` bootstrap-flag reset (guard: yanıt yok → FALSE) | TRUE 82,530 → **196** | `question_bank_iscalib_reset_backup_20260610` (82,334) |
| R3 | `question_bank.embedding` HNSW index (vector_cosine_ops, CONCURRENTLY) | ANN index YOK → `idx_qb_embedding_hnsw` (valid) | — (DROP INDEX ile geri al) + migration `b2f1a9c7d3e4` |

**Doğrulama:** R2 sonrası kalan 196 TRUE'nun hepsi gerçek `kiro2_learning_events` destekli (0 desteksiz). `irt_calibration_history` SE=0&iter=0 = 0 → geçmiş silinmedi.

**Artık bilinen / dürüstlük notu:**
- Kalan 196'nın `irt_method` hâlâ `bootstrap_difficulty_prior` → gerçek EM-kalibre değil; `irt_calibrated`=0. Gerçek kalibrasyon ≥50 yanıt + `irt_calibration_runner` gerektirir (şu an ~287 learning_event).
- CAT motoru (`cat_session.py`) artık bootstrap-prior'ları "kalibre" diye öne almaz; kalanları Öncelik-3 default-param ile ele alır (doğru davranış).
- Geri alma: her iki backup tablosundan tek SQL ile (script footer'larında). Güven periyodu sonrası `DROP` edilebilir.

**Bekleyen P0/P1:** aktif havuz inceleme (98,361 unverified/pending), FK ekleme (student_answers boş artık — FK eklemek güvenli), exam_sessions/exam_questions test artığı temizliği, 35 yedek + 161 boş tablo gözden geçir, gerçek IRT kalibrasyon (yanıt verisi büyüdükçe).

---

*Oluşturma: 2026-06-10. Ham çıktılar + script'ler: `docs/audits/2026-06-10_db_audit_artifacts/`. Tüm ölçümler salt-okunur, evren-level. Remediation script'leri: `docs/audits/2026-06-10_db_audit_artifacts/` (`db_sa_cleanup.py`, `db_reset_apply.py`, `db_verify.py`, `db_sa_profile.py`, `db_reset_dryrun.py`).*
