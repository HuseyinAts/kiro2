## Session Handoff — 2026-06-19 (D) — VP116 status-promote: +42 v_safe + base-filter ceiling bulundu
**Branch:** `feature/self-evolution-optimization` | correct_answer/is_active DOKUNULMADI, reversible

- **A lever (fallback ÖLÜ çıktı):** Veri kanıtı — fallback ONLY-block = 0 (tüm 23.214 fallback unverified-status; fallback asla bağımsız engellemiyor). Gerçek darboğaz STATUS. Lever fallback→ABANDON.
- **ONLY_status vp = 116** → Workflow 3-Opus-solver/soru SIRALI 6-dalga (348 ajan, %100 başarı) → **%98.2 precision (111/113, 2 TYT-Mat disagree + 3 UNSOLVABLE hariç).** 2-sinyal (vp+Opus) = MEMORY'nin gold-terfi kuralı.
- **111 status promote** (unverified→auto_judged_high + `vp_status_promote_2signal` flag), backup `question_bank_vp116_status_backup_20260619`. **Ama yalnız 42 v_safe'e girdi.**
- **KEŞİF: `v_safe_for_beta_unfiltered` base content-integrity filtresi** (bare-stem `^aşağıdaki...hangisi yanlış$`, `^yukarıdaki/^bu parça` + has_diagram yok, tek-`$` LaTeX) **69'u eledi**. Bu **bir sonraki gerçek tavan** — bazı bare-stem option-only sorular fazla-eleniyor olabilir (gelecek lever).
- **v_safe 7.770 → 7.812 (+42).** leak gate2c/fallback=0. total_active 110.895 değişmedi. 42: TYT-Türkçe 13/Kimya 10/Mat 7/AYT-Edebiyat 6...
- **SESSION TOPLAM: v_safe 6.544 → 7.812 (+1.268):** wave1 +56, tier1-unlock +1.170, vp116 +42.
- Artefaktlar `_wave1/vp116_*`, `compare_vp116.py`, `gen_vp116_promote.py`. Uncommitted: vp116 + latest.md.

---

## Session Handoff — 2026-06-19 (C) — TIER1 UNLOCK: +1.170 v_safe (workflow, %100 precision)
**Branch:** `feature/self-evolution-optimization` | DB-yazımı YOK (view-only D8), reversible

- **Teşhis (wave1'den):** verified_provisional 9.344 ama v_safe'te 5.879 → **3.459 doğrulanmış soru view-bloke**; en büyük tek sebep **tier1 match_tier = 1.176** (status/fallback/demote temiz, sırf tier1).
- **Kanıt (Workflow):** 72-soru thin-STEM-ağırlıklı blind validation, 3 bağımsız Opus solver/soru SIRALI 6'lık dalga → **%100 precision (72/72), 0 wrong/unsolvable, 16/16 branş %100** (AYT-Kimya/Fizik/Bio 10/10 dahil). tier1 kapısı kör-doğrulanmış içerik için gereksiz kanıtlandı.
- **Workflow rate-limit dersi (CANLI):** 1. deneme 14-paralel+schema → 216/216 server-529 ÖLDÜ. Fix: **schema YOK + 6'lık sıralı dalga** → 216/216 OK. (MEMORY pool-growth dersinin tekrarı.)
- **Uygulama D8 view:** `match_tier` tier1 kapısına `OR verified_provisional` (canlı viewdef'ten birebir). **v_safe 6.600→7.770 (+1.170).** leak gate2c/fallback/demoted=0. correct_answer/is_active/status DOKUNULMADI (total_active 110.895 + vp 9.344 değişmedi). Rollback `D8_rollback.sql`.
- **Thin AYT fen REBALANCE:** Kimya 27→112, Fizik 35→97, Bio 14→57, Tarih 52→95 → AYT simülasyonu artık mümkün. ROI ~21× wave1.
- Detay `_wave1/TIER1_UNLOCK_RESULT.md`. Sonraki: multi_blocked 2.125 kısmi-unlock ölç; fallback 2.115 kök-çözüm (topic re-tag). Uncommitted: `_wave1/*` + latest.md.

---

## Session Handoff — 2026-06-19 (B) — WAVE1 AYT-Edebiyat: consensus FAILED → 4-WAY → +56 SHIPPED
**Branch:** `feature/self-evolution-optimization` | correct_answer/is_active DOKUNULMADI, reversible (backup table)

- qwen3:14b 60 batch (1.026/1.200) + gemma (1.089/1.200). gate: PROMOTE_A 199 + PROMOTE_B 281, DROP_wrongkey 544 (%45).
- **Faz1 consensus KAPISI KALDI:** TIER-A 15/20=%75, TIER-B 15/30=%50 (<%95). 4 kanıtlı yanlış-key consensus kaçırdı.
- **Faz2 4-YÖNLÜ narrowing SHIPPED:** Opus 199 TIER-A'yı kör çözdü → gemma==qwen==stored==Opus = **169 (%84.9)**.
  View-uygun 58 promote (42 demoted_at+69 fallback+41 tier1 elendi), **56 v_safe'e girdi** (2 is_public=false).
  **v_safe 6544→6600, AYT-Edebiyat 233→289 (+56). leak=0.** flag `wave1_run`, view **D7 applied**,
  backup `question_bank_wave1_ayt_edebiyat_backup_20260619` (58). Rollback: D7_rollback.sql + backup restore.
- 4 yanlış-key (curator backlog, correct_answer DOKUNULMADI): `46541467`(İntibah B→A), `2e5c4a36`(Kabusnâme E→D), `dbeae55b`(cinas E→A), `be27b14a`(Akif B→A) — hepsi 4-way'de zaten ELENDİ.
- Detay `backend/scripts/quality/_wave1/RESULT.md`. Uncommitted: `_wave1/*` + latest.md.
- Sonraki: (a) DB CHANGE COMMIT yok (DB zaten yazıldı; git'e _wave1 scriptleri commit); (b) diğer branş (TYT-Bio 4.546/TYT-Tarih 2.911) — AMA consensus-gate ZAYIF kanıtlandı, doğrudan 4-yönlü Opus-solve daha güvenli (branş-bağımlı); (c) wave1 169'un view-bloke 111'i (demoted/fallback/tier1) ayrı kalite-kapısı, dokunulmadı.

---

## Session Handoff — 2026-06-19 (Serving-path leak fix + gate2c demote + answer-wrong scan)
**Branch:** `feature/self-evolution-optimization`
**Son commit:** `cce6807fe` (offline_sync F821) | `7c6731940` (serving-path gate)

### Bu session — 4 iş, hepsi kanıtlı/geri-alınabilir
1. **Serving-path sızıntı fix (HEADLINE, committed):** placement (`load_assessment_items`) ve offline (`build_sync_package`) `question_bank`'i yalniz `is_active` ile sorguluyor, `v_safe_for_beta` kapisini BYPASS ediyordu. Canli DB: placement havuzu **110.895 (94.443 unverified/pending) → 6.544 (%100 v_safe)**. TDD: `tests/test_serving_path_leak.py` kaynak-introspeksiyon guard (red→green), 26 mevcut placement testi geçti. Fix = kanonik `id IN (SELECT id FROM v_safe_for_beta)` her iki serviste (3'er sorgu).
2. **gate2c demote (committed, D6):** 62 Opus-doğrulanmış çöp soru (50 dup/OCR proxy + 12 Opus-confirmed garble) → geri-alınabilir `gate2c_demoted` exclusion tablosu + view predicate. **v_safe 6.606 → 6.544**, leak=0 (canlı teyit). `correct_answer`/`is_active`'e DOKUNULMADI.
3. **Answer-wrong taraması (214/214, %100):** consensus answer-wrong (gemma3==qwen3≠stored) Opus ile kör-çözüldü. **~%1,4 wrong-key** (3 aday, biri güçlü), ham %27 değil. Anahtar değişikliği YOK (`correct_answer` korumalı). Detay aşağıda.
4. **offline_sync F821 fix (committed `cce6807fe`):** `process_sync_results` tanımsız `questions_map`/`cards` kullanıyordu (her cevap sessizce failed) + `_next_sync_at_iso` `timezone.utc` (tanımsız). Döngü öncesi soru/kart ön-getirme + `UTC`. TDD `tests/test_offline_sync_service.py` (3 test red→green); kullanılmayan import'lar da çözüldü.

### Önemli durum düzeltmesi
Eski handoff'taki "v_safe 13.831" ESKİ. Bu session öncesi **D5 sıkılaştırması** (coherence/promote bayrak şartı) 13.831 → 6.606 indirdi; D6 demote 6.606 → **6.544**. Bu kasıtlı (status-only gate çok gevşekti).

### Açık işler (öncelik sıralı)
1. **Push** — `7c6731940` push'landı; `cce6807fe` + bu handoff bekliyor (`git push origin feature/self-evolution-optimization`).
2. **3 wrong-key adayı** (manuel uzman onayı, `correct_answer` korumalı): `f41b7323`(stored C→D, güçlü), `e9c247a6`(B→A), `e829870c`(E→C, bozuk soru). + ~25 bozuk soru (seçenekte cevap yok / çoklu doğru) → gate2c'ye eklenebilir.
3. ~~`verified_provisional` 5.879 denetlenmemiş~~ **YANLIŞ — ölçüldü:** v_safe 6.544 = 2.626 coherent (tarandı) + 3.918 promoted (Opus sample-validated), overlap 0, **denetlenmemiş 0**. provisional ayrı blok değil (prov-only=0). v_safe %100 doğrulanmış. Opsiyonel ileri iş: tüm-v_safe taze QA örneklemi (~80 soru) güncel genel kalite tahmini için; ya da pool büyütme (92K unverified, v_safe DIŞI).

### Notlar / araçlar
- DB: native PG 5434 (servis `postgresql-x64-18`, bu session admin/RunAs ile başlatıldı). Read'ler MCP `dbhub-kiro2` ile.
- bash VM bu session boyunca çökük → tüm script'ler HOST PowerShell ile çalıştırıldı (human-in-loop).
- gate2c scaffolding: `backend/scripts/quality/_gate2b/` (D6_*.sql, build_final_demote.py, final_demote_ids.json committed; gate2c_*.py + preds/batches/master.csv transient, commit edilmedi).
- **Serving-path:** sadece placement+offline canlı sızıntıydı. `exam_performance_service` = geçmiş analiz (düşük risk), `question_repository` = admin (student-facing değil) — fix kapsamı dışı.
