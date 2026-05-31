# FINAL INVENTORY — OCR Pipeline & Tüm Girişimler Eksiksiz Envanter

**Tarih:** 2026-05-31
**Baş analist:** konsolidasyon turu
**Girdi zinciri:**
- `_inv_tmp/COVERAGE_SYNTHESIS.md` (275 script ↔ K1-K20 kapsama sentezi)
- `_inv_tmp/data_db.md` (14 .db artifact arkeolojisi)
- `_inv_tmp/data_jsonl.md` (283 .jsonl artifact arkeolojisi)
- `_inv_tmp/data_manifest.json` (ham sayım manifesti)
- `docs/audits/2026-05-31_ocr_pipeline_rootcause.md` (8 eksen, 20 kök-neden, 3 adversarial challenge)
- Destek: 14 `inv_batch_*.json` + 14 `inv_finding_*.md` + `inventory.json` (193KB master)

**Görev:** Eksiksiz envanter — yönetici özeti, kapsama matrisi (K1-K20), yeni hata modları, ölü/tekrar-riskli script listesi, veri-artifact özeti, nihai "eksiksiz analiz edildi mi?" kararı.

---

## 1. Yönetici Özeti

**Kaç girişim analiz edildi?**
Manifest doğrulaması: `d-dataset/scripts` 110 .py + `backend/_pilots` 59 .py + `backend/scripts` 200 .py (tüm) = ham havuz ~369 dosya; bunların OCR/kalite-pipeline ile alakalı **~275'i** 14 envanter batch'inde script→kök eşlemesiyle analiz edildi. Geri kalan ~94 dosya OCR-dışı (auth, load-test, BKT/IRT/FSRS property-test — M-B7 ile işaretli). Veri tarafında **14 .db** + **283 .jsonl** + `processed/` 3,866 dosya artifact taranıp canlı/ölü sınıflandırıldı.

**Kapsam tam mı?**
EVET — kapsam tamdır. 275 scriptin ~270'i (≈%98) K1-K20'ye temiz oturuyor; kalan ~5'i 4 yeni mod (M-A1..M-A4) altında toplandı. Tüm büyük artifact aileleri (OCR-run, answer-key v2-v11, matched v1-v5, vision-solve, ground-truth, backup) envantere alındı. Hiçbir batch eksik değil (14/14 mevcut, finding 14/14 mevcut).

**Kök-neden raporu eksiksiz mi yoksa eksik mi?**
**Büyük ölçüde eksiksiz ama 4 yeni mod + 5 kapsam açığı kadar EKSİK.** Rapor içerik-kalite kök-nedenlerini (metin/görsel/cevap/encoding/ölçüm-meta 8 ekseni) yüksek doğrulukla yakaladı; TOP-5 tezi 3 challenge ile 5/5 doğrulandı, phantom filtresi (Bayesian fix, kalibrasyon dosyaları) uygulandı. Ancak şu eksenler **isimlendirilmemiş**: (1) **subject-tag doğruluğu** (M-A1, gerçek yeni kök), (2) **VLM safety-filter veri kaybı** (M-A2), (3) **vanity-metriğin aktif veri-mutasyonu** (M-A3), (4) **disk-üzeri kanonik-dosya belirsizliği** (M-A4 — raporun K14 "PHANTOM-fix" güvenini doğrudan zayıflatıyor). Bu eklemeler raporun hiçbir TOP-5 tezini çürütmüyor, üzerine genişletiyor.

---

## 2. Kapsama Matrisi — K1-K20 × Script-Sayısı / Örnek

| Kök | Kısa ad | Vuruş (~) | Temsilci script(ler) | Yoğunluk |
|---|---|---|---|---|
| **K1a** | Gate format ölçüyor (okunabilirlik değil) | ~38 | `_apply_C1/C2/C3_scoring.py`, `validate_sample.py`, `beta_eligible_filter[_v2].py`, `deactivate_bad_questions.py`, `filter_critical.py`, `clean_v2_4.py`, `quality_improvement_pipeline.py` | ÇOK-TEKRARLI |
| **K1b** | Dairesel GT (0 insan onayı) | ~34 | `build_ground_truth_sample.py:428-430`, `validate_ground_truth.py`, `measure_tier_accuracy.py`, `confidence_calibration.py`, `llm_judge_build/apply.py`, `s198_build_consensus.py`, `metadata_phase7_*` | ÇOK-TEKRARLI |
| **K2a** | Kaynak 1080p ekran-yakalama | ~8 | `image_quality_audit.py`, `vision_solve_codex/opus.py`, `preprocess_screenshots.py`, `extract_real_qnum.py` | orta |
| **K2b** | Upscale yok (downscale + 1024 cap) | ~22 | `script_common.py:123-126`, `crop_preprocessor.py`, `reocr_pilot_v1.py`, `tier_i_reocr_apply[_threaded].py`, `ocr_crops.py`, `solve_crops.py`, `alibaba_crop_solver.py` | ÇOK-TEKRARLI |
| **K3** | Soru↔crop deterministik bağ yok | ~30 | `crop_from_detections.py:266-274`, `pipeline.py:3315`, `image_match_metadata_v1.py`, `populate_image_urls_tier_c.py`, `tier_d/f/g_*`, `strategy_a/b/c/d_*`, `pilot_n_to_n*` | ÇOK-TEKRARLI |
| **K4a** | Crop=blok → cevap sızıntısı | ~10 | `image_audit_v1.py`, `pipeline.py:164-166`, `solve_crops.py`, `solve_unmatched_v3.py`, `vision_solve_*`, `beta_eligible_filter_v2` | orta |
| **K4b** | Frontend `false &&` tüm görsel gizli | ~3 | `beta_flag_resolver.py`, `bug_7_10_smoke.py`, `image_audit_v1.py` | düşük (P0) |
| **K5** | page_inline düşük-qnum çökme → A/E bias | ~18 | `phase4_page_inline_answers.py`, `reextract_answer_keys.py:494-521`, `extract_real_qnum.py`, `audit_ground_truth_bias.py`, `analyze_pilot_results.py` | ÇOK-TEKRARLI |
| **K6** | Cevap↔soru pozisyonla (içerik değil) | ~20 | `match_crop_answers.py:20,26`, `prove_random_test.py`, `root_cause_solution.py`, `detect_qnum_by_position.py`, `implement_4tier.py`, `match_simple_v4.py` | ÇOK-TEKRARLI |
| **K7** | Cevap-OCR tek-engine (Gemini Flash) | ~14 | `phase4_page_inline_answers.py:58`, `cevap_crop_ocr.py`, `reextract_answer_keys.py`, `solution_distillation.py`, `ai_solve_pipeline.py` | orta |
| **K8** | Çekirdek match tek-sinyal (q_no) | ~26 | `pipeline.py:2902-2924`, `match_crop_answers.py`, `match_simple_v4`, `rematch_with_test_no.py`, `image_match_jsonl/fuzzy/v9_loose`, `ensemble_voting` | ÇOK-TEKRARLI |
| **K9/R6** | Tek-sinyal → Tier H 49,468 rollback | ~7 | `tier_h_qip_exact.py:132`, `tier_h_v2_qip_offset.py`, `pilot_strategy_h_unique_id.py`, `pilot_tier_h_shift_fix.py`, `audit_task02[b]_tier_h_*` | orta (yüksek tekrar-riski) |
| **K10** | Crop count ≠ DB count | ~12 | `image_match_v15a_labelme_exact:97-103`, `image_match_v12/v13`, `analyze_n_to_n_groups.py`, `strategy_c_unused_crop`, `image_match_n_to_n_text_v7` | orta |
| **K11** | 19+ matcher sürümü → provenance kaybı | ~33 | TÜM `image_match_v1..v15a`, `tier_c/d/f/g/h`, `image_match_rebuild_v5/rollback_v4`, `verify_image_match_*`, `deep_correctness_audit_v2`, `final_correctness_audit` | ÇOK-TEKRARLI |
| **K12** | Figür-bağımlı dışlama tutarsız | ~7 | `bug_7_10_smoke.py`, `classify_questions.py`, `audit_remaining_pool.py`, `beta_pattern_scanner` | düşük |
| **K13** | OCR prompt figürü tarif etmiyor | ~5 | `pipeline.py:290`, `classify_questions.py`, `solve_pipeline_v2.py`, `bug_7_10_smoke.py` | düşük |
| **K14** | Bayesian ai_upgrade (FIX'Lİ) + kalıntı | ~6 | `cross_validate_answers.py:114` (FIX canlı — PHANTOM), `cross_validate_answers (1).py` (fix DOĞRULANMADI), `test_cross_validate[.py/(1)]`, `merge_sources` | düşük (kalıntı P1) |
| **K15** | Kitap-adı join I→ı non-canonical | ~16 | `match_simple_v4.py:27-33`, `cross_validate_answers.py:159-170`, `create_answers_v8.py:134`, `merge_sources/v3`, `analyze_book_mapping.py`, `ensemble_voting`, `publisher_alignment_audit` | orta-yüksek |
| **K16** | Funnel'da provenance silme (dedup son-kazanır) | ~9 | `create_answers_v8.py:131-141`, `merge_v3_solved/production.py`, `merge_sources.py`, `clean_v2_4.py`, `fix_perfect_metadata.py` | orta |
| **K17** | Çözünürlük teşhisi dead code | ~7 | `script_common.py:1665`, `image_quality_audit.py`, `assess_text_results.py`, `preprocess_screenshots`, `cutoff_detector_v1` | düşük |
| **K18** | Vanity-metrik gerçek metriği gizledi | ~16 | `validate_3tier[_selective].py`, `validate_match_[results/v3].py`, `analyze_coverage_impact/crossval`, `deep_audit`, `ma_tracker.py`, `update_quality_scores.py` | orta-yüksek |
| **K19** | Audit dalga-içi kapanıyor (audit-as-progress) | ~17 | `weekly_audit.py`, `faz_6_6_reject_audit.py`, `s198_promote_36.py`, `diagnose_version_gap.py`, `microscopic_qa_analysis.py`, `drift_dashboard.py` | orta-yüksek |
| **K20** | OCR metni NFC-normalize edilmiyor (yazma anında) | ~12 | `ocr_crops.py`, `script_common.py`, `strategy_b_image_ocr`, `fix_near_classification`, `tier_j`, `test_script_common_new.py` | orta |

**Toplam vuruş ≈ 350** (bir script birden çok köke çarpabilir; 275 benzersiz script).

**En çok-tekrarlı 7 kök (sistemik baskı):** K1a(~38) > K1b(~34) > K11(~33) > K3(~30) > K8(~26) > K2b(~22) > K6(~20).

**İki sistemik daire:**
- **ÖLÇÜM dairesi** (K1a+K1b+K18+K19) ≈ **105 vuruş** → raporun "en derin kök = ölçüm-tasarımı çöküşü" tezini sayısal doğruluyor.
- **POST-HOC YAMA dairesi** (K3+K8+K11) ≈ **89 vuruş** → ingest'te deterministik bağ kurulmadığı için her başarısızlık yeni script doğurmuş.

---

## 3. YENİ Hata Modları (K1-K20 Dışı)

### A. GERÇEK YENİ MODLAR — kök-neden raporuna EKLENMELİ

| # | Yeni mod | Kanıt | Neden K1-K20 değil | Önerilen aksiyon |
|---|---|---|---|---|
| **M-A1** | **Subject-tag yanlış-sınıflama** (soru → subject_area etiket hatası) | `validate_subject_classification.py` (MATH_INDICATORS keyword reclassify); MEMORY "Fizik→aritmetik, Kimya→dilbilgisi 5+ vaka" | 8 eksen **etiket-doğruluğu eksenini içermiyor**. Tek-sinyal keyword reclassify yanlış soruyu yanlış sınava sokar → beta'da görünür ürün hatası | Yeni K ekseni: subject-tag doğruluğu; çift-sinyal sınıflandırma (keyword + LLM) |
| **M-A2** | **VLM safety-filter içerik kaybı** (geometri şekilleri sistematik bloke) | `tier_i_geometri_retry.py`: Gemini `HARM_CATEGORY_DANGEROUS_CONTENT`, `finish_reason != STOP`, 346 satır kayıp | K2/K7 akraba ama mekanizma farklı: engine **içeriği görmeyi reddediyor** (yanlış okumuyor); subject-bias'lı sessiz veri kaybı | Çok-model konsensüs (bir engine bloklarsa diğeri tamamlar); blok-oranı subject bazlı izlenmeli |
| **M-A3** | **Chi-square-driven cevap MUTASYONU** (vanity-metriği aktif veri-değişimine çevirme) | `validate_3tier_selective.py:2` "apply answer changes ONLY for books that improve [chi-square]" | K18 metriği **ölçer**; M-A3 yanlış metriğe göre **production cevabını DEĞİŞTİRİR** → gerçek-doğru cevapları bozma riski (YKS dağılımı uniform değil) | Chi-square-tabanlı cevap UPDATE'i yasakla; cevap değişimi yalnız içerik-eşleşme kanıtıyla |
| **M-A4** | **Disk-üzeri " (1)" kopya / kanonik-dosya belirsizliği** | `cross_validate_answers (1).py`, `crop_from_detections (1).py`, `script_common (1).py`, `ocr_crops (1).py` (farklı engine!), `preprocess_screenshots (1).py` (farklı girdi!), `answers_v8 (1).db`, `eslesmis_sorucevap (1).jsonl` — ≥14 vaka | K11 *kod-içi kasıtlı* sürümleme; bu **kazara dosya-kopyası** — `import script_common` hangi kopyayı çözer belirsiz (PYTHONPATH/cwd). **K14 fix güvenini geçersiz kılıyor** — fix sadece canonical'da doğrulandı, " (1)" kopyada DOĞRULANMADI | Tüm " (1)" kopyaları `_deprecated/`; tek kanonik import path; K14 fix'ini " (1)" kopyada da re-verify |

### B. ALT-TEZAHÜR (mevcut kök, yeni framing — yeni değil ama vurgu değer)

| # | Gözlem | İlişkili kök |
|---|---|---|
| M-B1 | Alt-engine kurtarma silosu (`paddleocr_recovery`, `ollama_crop_solver`, `qwen_vl_local_ocr`, `pix2text_enrichment` — upscale içermez, garble çözmez, prod-funnel'a bağlanması izlenmez) | K2b + K11 |
| M-B2 | Ölü-tablo kalıntısı (≥4 script v8'de SİLİNMİŞ `answers` tablosunu hâlâ sorguluyor → sessiz boş-sonuç) | K9/K11 alt-sınıfı |
| M-B3 | İteratif eşik-sertleştirme canlı-DB'de (`fix_near_classification`→`fix_near_strict_v2`→`fix_final_residual` aynı 7,302 NEAR'ı 3× UPDATE) | K11 + K16 + audit-methodology.md ihlali |
| M-B4 | Metadata cluster-reuse hata yayılımı (`metadata_phase7_llm_generation.py:23-25` sim≥0.92 ile yanlış rationale N benzer soruya kopyalanır) | K1b amplifier |
| M-B5 | Metadata zinciri dairesel-GT'ye sessiz bağımlı (`metadata_phase2_irt_compute.py` "KESIN_DOGRU" üzerinden IRT SE/Fisher üretir; etiket dairesel ise IRT-metadata kontamine) | K1b downstream amplifikasyon |
| M-B6 | Hardcoded mutlak path / hardcoded API key (`irt_calibration_runner.py` sys.path; `alibaba_crop_solver.py:38` DashScope key plaintext) | K-dışı; güvenlik/taşınabilirlik (rotate gerek) |
| M-B7 | OCR-dışı pilot kirliliği (`_pilots/` içinde auth-security, Locust load, property-BKT/IRT/FSRS — 4+ script OCR pipeline DIŞI) | meta; provenance şeması yok |

---

## 4. Ölü / Tekrar-Riskli Script Listesi (temizlik gerek)

### 4a. Rollback olmuş ama silinmemiş (yüksek tekrar-riski)
| Script | Durum | Risk | Aksiyon |
|---|---|---|---|
| `tier_h_qip_exact.py` | 49,468 satır YANLIŞ, rollback `6a3fa7fc0` | Tek-sinyal pattern tekrar çalıştırılabilir | `sys.exit(DEPRECATED)` + `_deprecated/` |
| `tier_h_v2_qip_offset.py` | Konsept iptal, pilot %75 yanlış | Tekrar-riski | `_deprecated/` |
| `pilot_tier_h_shift_fix.py` | Rollback'li Tier H'i diriltme girişimi | **EN yüksek** — rollback edilmişi geri açıyor | Sil/mühürle |
| `pilot_strategy_h_unique_id.py` | Tier H temeli (rollback'e gitti) | Tekrar-riski | `_deprecated/` |
| `eslesmis_sorucevap_rematched_HARMFUL.jsonl` | "Zararlı", arşivlenmiş | Düşük (zaten arşivde) | İyi pratik, dokunma |

### 4b. Ölü-tablo sorgulayan (sessiz boş-sonuç riski)
`match_crop_answers (1).py`, `match_from_db.py`, `implement_4tier.py`, `match_simple_v4.py` (bookend dalı), `rematch_with_*.py`, `replace_db_v7_sources.py` — hepsi v8'de **silinmiş `answers` tablosunu** (%39 doğruluk) sorguluyor → try/except guard veya silme.

### 4c. Çelişen/mükerrer rakip girişimler (aynı işi farklı mantıkla)
- **4+ rakip cevap-matcher:** `match_simple_v4`, `match_from_db`, `match_crop_answers`, `implement_4tier`, `rematch_with_test_no` — hangisi son üretim belirsiz.
- **19+ image-matcher** (K11): `image_match_v1..v15a` + `tier_c..h` + `strategy_a..d` + `pilot_n_to_n*`. **Geç sürüm = daha zayıf sinyal** (v6/v12 det.1:1 → v13 3/5 → v15a Y-sıra → v15 tüm-sayfa) — coverage baskısı kaliteyi DÜŞÜRMÜŞ.
- **≥14 " (1)" kazara kopya** (M-A4) — biri Gemini/biri Qwen, biri JSONL/biri dizin (davranışsal FARKLI, isim neredeyse aynı).

### 4d. Stub (hiç çalışmamış)
`pix2text_enrichment.py`, `qwen_vl_local_ocr.py` — STUB/FUTURE, CUDA/VRAM gereksinimi karşılanmamış.

**Öneri (CLAUDE.md `deprecation-guard.md` prosedürü):** `_deprecated/` taşıma + import path'leri tek kanonik dosyaya sabitleme + Tier-H ailesi `sys.exit(DEPRECATED)` mührü.

---

## 5. Veri-Artifact Özeti (db/jsonl sürümleri — canlı/ölü)

### 5a. .db artifactları (14 dosya)
| Durum | Dosyalar |
|---|---|
| **CANLI (production-referansli)** | `answers_v8.db` (answers_page_inline:78,720 — production cevap kaynağı; `answers` tablosu KASITLI YOK) · `ocr_v3/progress.db` (done:75,819 — OCR ham kaynak, en büyük DB 69MB) |
| **EN YENİ incremental** | `answers_v11.db` (page_inline:10,035 + answers:1,444 — v8 üstüne kısmi) · `matched_v5_combined/kiro2_final` (questions:31,305 — match zinciri son halkası) |
| **DUPLICATE (silinebilir)** | `answers_v8 (1).db` (indirme kopyası, eski `answers:66,450` tablolu) · `kiro2_questions_20260105` (v4 re-export, 21,321 satır aynı) |
| **ÖLÜ/eski prototip** | `answer_keys_v6/progress.db` (answers boş) · `answers_v7.db` · `answers_v9/v10.db` (242/1,254 satır) · `matched_v1(40K)/v2(42K)/v3(37K)/v4(21K)` |

**Match evrimi:** v1(40K) → v2(42K) → v3(37K kalite-filtreli) → v4(21K kiro2-şema) → v5_combined(31K final). Hepsi 2 Ocak 2026. **Production'a geçiş `eslesmis_sorucevap.jsonl`'e taşınmış** — match DB'leri artık tarihsel.

### 5b. .jsonl artifactları (283 dosya)
| Aile | Sürüm sayısı | Canlı | Not |
|---|---|---|---|
| `eslesmis_sorucevap` (matched ürün) | **15+ adlandırılmış sürüm** (v2.0→v2.5, v3.0→v3.4_clean + ara türevler) + 11 backup | `eslesmis_sorucevap.jsonl` **77,336** (v3.5+ PRODUCTION) | `eslesmis_sorucevap (1).jsonl` (M-A4 duplicate); `_rematched_HARMFUL` (arşiv) |
| Answer-key çıkarım | **11 sürüm** (`answer_keys_v2..v11` + `_ai`) | `answer_keys_v8` (answers_v8.db kaynağı) | En agresif versiyonlama burada |
| OCR-run | **6 motor × 3-4 jenerasyon** (`ocr→ocr_results→ocr_results_v2→ocr_v3`) | `ocr_v3` | Gemini/PaddleOCR/Surya/EasyOCR/Hybrid/Qwen3-VL+Ollama |
| Match-girişimi | 5 ana run + 3 final-merge + 1 zararlı rematch ≈ **8-9 katman** | — (JSONL'e taşındı) | `matched_v1..v5_combined`, `final_matched v1-v3` |
| Vision-solve | 14 dizin (codex/gemini/opus/sonnet/minimax/crop/override...) | — (ara artifact) | "AI %4→%30" sprint (S48-60) |
| Ground-truth | **1 dosya** `ground_truth_v1.jsonl` **600 satır** `verifier:"human"` | — | Pipeline'daki **TEK** insan-GT artifaktı → K1b dairesellik kanıtı (tek timestamp, mismatch=0) |

### 5c. Kritik belge-kod uyumsuzluğu (rapor K-listesi yakalamıyor)
`d-dataset/ocr_output/` ve `d-dataset/answer_keys/` dizinleri **HİÇ VAR OLMAMIŞ** (silinmemiş/taşınmamış — isim driftı). Gerçek yollar: raw OCR `output/ocr*`, answer-key `output/answer_keys_v2..v11`. CLAUDE.md'deki File Access Rules bu phantom yolları "READ-ONLY" işaretliyor → belge düzeltilmeli.

---

## 6. Nihai Cevap: "TÜM OCR ve Girişimler Eksiksiz Analiz Edildi Mi?"

**EVET — eksiksiz analiz edildi.**

**Gerekçe:**
1. **Script kapsamı tam:** Manifest'teki tüm OCR/kalite-pipeline scriptleri (~275/369; kalan ~94 OCR-dışı M-B7 ile sınırlandırıldı) 14 batch'te script→kök eşlemesiyle tarandı. 14/14 batch ve 14/14 finding dosyası mevcut, master `inventory.json` (193KB) bütün.
2. **Artifact kapsamı tam:** 14/14 .db ve 283/283 .jsonl artifact canlı/ölü/duplicate sınıflandırmasıyla envantere alındı; tüm sürüm zincirleri (matched v1-v5, answer-key v2-v11, eslesmis v2.0-v3.5+, 6 OCR motoru, 14 vision-solve dizini) izlendi.
3. **Kök-neden eşleşmesi yüksek:** ~270/275 script (≈%98) K1-K20'ye temiz oturuyor; sapan ~5'i 4 yeni mod (M-A1..M-A4) altında izah edildi — boşta kalan açıklanamayan script yok.
4. **Çapraz doğrulama:** İki sistemik daire (ölçüm ~105 + post-hoc yama ~89 vuruş) raporun META-KÖK iki-kol yapısını sayısal teyit ediyor; adversarial 5/5 doğrulama + phantom filtresi (Bayesian fix, kalibrasyon dosyaları) tutarlı.

**Şart/uyarı (eksiksiz ama genişletilmeli):** Analiz eksiksiz olsa da kök-neden raporu **4 yeni mod (M-A1 subject-tag, M-A2 VLM-safety, M-A3 chi-sq mutasyon, M-A4 dosya-kopya) + 5 kapsam açığı** ile genişletilmelidir. En kritik açık **M-A4**: raporun K14 "PHANTOM-fix" güven derecesi yalnız canonical dosyada doğrulandı, " (1)" kopyada doğrulanmadı — bu güven derecesini düşürür ve re-verify gerektirir.

---

## 7. M-A4 Doğrulama Sonucu (post-workflow, ana-loop teyidi)

`cross_validate_answers (1).py` kopyası `ai_upgrade` tier'ını **HİÇ içermiyor**
(diff: 5 ai_upgrade satırı yalnız kanonikte; " (1)" S194-öncesi eski sürüm).
Dosya adındaki **boşluk** nedeniyle `import cross_validate_answers` ile YÜKLENEMEZ
→ yalnız elle `python "...(1).py"` ile çalışırsa devreye girer (orphan).

**Sonuç:** K14 "ai_upgrade fix CANLI (phantom-bug)" iddiası **kanonik/import-edilen
dosya için GEÇERLİ**. " (1)" kopyası import-edilemez yetim, aktif pipeline'da değil.
M-A4'ün K14-güven-zayıflatma riski bu dosya için **çözüldü**; ancak genel duplicate
hijyeni (≥14 " (1)" kopya, bazıları farklı-engine/farklı-girdi) hâlâ P1 temizlik.
