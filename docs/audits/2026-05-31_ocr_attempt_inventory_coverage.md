# COVERAGE SYNTHESIS — 275 Script + Veri-Artifact ↔ Kök-Neden (K1-K20)

**Tarih:** 2026-05-31
**Girdi:** 14 envanter batch'i (`inv_finding_01..14.md`, ~275 script), `data_db.md` (14 .db), `data_jsonl.md` (283 .jsonl), kök-neden raporu `docs/audits/2026-05-31_ocr_pipeline_rootcause.md` (K1-K20).
**Görev:** (1) Kapsama matrisi, (2) yeni hata modları, (3) ölü/tekrar-riskli scriptler, (4) kök-neden raporu kapsam açığı.

---

## 1. KAPSAMA MATRİSİ — Her Kök-Neden → Kaç/Hangi Script Çarptı

Sayım: 14 batch'in script→kök eşlemelerinden agregat. "Vuruş" = bir scriptin o köke kanıtla atfedildiği. Bir script birden çok köke çarpabilir.

| Kök | Kısa ad | Vuruş (~) | Temsilci scriptler (kanıt) | Yoğunluk |
|---|---|---|---|---|
| **K1a** | Gate format ölçüyor (okunabilirlik değil) | **~38** | `_apply_C1/C2/C3_scoring.py`, `validate_sample`/`test_pipeline.py`, `r1_legacy_v3_restore_apply.py`, `beta_eligible_filter[_v2].py`, `beta_pattern_scanner.py`, `deactivate_bad_questions.py`, `filter_critical.py`, `filter_crop_ocr.py`, `clean_v2_4.py`, `tier_j_*`, `quality_improvement_pipeline.py` | **ÇOK-TEKRARLI** |
| **K1b** | Dairesel GT (0 insan onayı) | **~34** | `build_ground_truth_sample.py:428-430` (auto-verify KESİN), `validate_ground_truth.py` check#6, `measure_tier_accuracy.py`, `confidence_calibration.py`, `faz_2_6_score_w20.py`, `faz_6_6_score.py`, `llm_judge_build/apply.py`, `s198_build_consensus.py`, `verify_all_questions.py`, `ensemble_voting.py`, `metadata_phase7_*` | **ÇOK-TEKRARLI** |
| **K2a** | Kaynak 1080p ekran-yakalama | ~8 | `image_quality_audit.py`, `extract_real_qnum.py`, `vision_solve_codex/opus.py`, `preprocess_screenshots.py` | orta |
| **K2b** | Upscale yok (downscale+1024 cap) | **~22** | `script_common.py:123-126` (KESİN), `crop_preprocessor.py` (upscale-dalı yok), `reocr_pilot_v1.py`, `tier_i_reocr_apply[_threaded].py`, `ocr_crops[.py/(1)]`, `solve_crops.py`, `alibaba_crop_solver.py`, tüm crop-OCR/solve | **ÇOK-TEKRARLI** |
| **K3** | Soru↔crop deterministik bağ yok | **~30** | `crop_from_detections.py:266-274` (KESİN), `pipeline.py:3315`, `image_match_metadata_v1.py`, `populate_image_urls_tier_c.py`, `tier_d/f/g_*`, `strategy_a/b/c/d_*`, `pilot_n_to_n*`, `image_match_jsonl_v2`, `research_deep_gap.py` (kanıt) | **ÇOK-TEKRARLI** |
| **K4a** | Crop=blok → cevap sızıntısı | ~10 | `image_audit_v1.py` (%100 leak KESİN), `pipeline.py:164-166`, `solve_crops.py`, `solve_unmatched_v3.py`, `vision_solve_*` (leak solver'a taşınıyor), `beta_eligible_filter_v2` | orta |
| **K4b** | Frontend `false &&` tüm görsel gizli | ~3 | `beta_flag_resolver.py` (9× image-bound itiraf), `bug_7_10_smoke.py`, `image_audit_v1.py` | düşük (ama P0) |
| **K5** | page_inline düşük-qnum çökme → A/E bias | **~18** | `phase4_page_inline_answers.py` (kaynak), `reextract_answer_keys.py:494-521`, `extract_real_qnum.py`, `audit_ground_truth_bias.py`, `analyze_pilot_results.py`, `_spot_check.py`, `validate_match_*` (qnum=1 dominance check) | **ÇOK-TEKRARLI** |
| **K6** | Cevap↔soru pozisyonla (içerik değil) | **~20** | `match_crop_answers.py:20,26` (40.9% ZERO KESİN), `prove_random_test.py` (BİZZAT İSPAT), `root_cause_solution.py`, `find_nearest_test`/`match_from_db.py`, `detect_qnum_by_position.py`, `implement_4tier.py`, `match_simple_v4.py`, `solve_unmatched_v3.py` | **ÇOK-TEKRARLI** |
| **K7** | Cevap-OCR tek-engine (Gemini Flash) | ~14 | `phase4_page_inline_answers.py:58` (KESİN), `cevap_crop_ocr.py`, `reextract_answer_keys.py`, `solution_distillation.py`, `claude_solve_pipeline.py`, `ab_test_*`, `ai_solve_pipeline.py` | orta |
| **K8** | Çekirdek match tek-sinyal (q_no) | **~26** | `pipeline.py:2902-2924` (KESİN), `match_crop_answers.py`, `match_simple_v4`, `rematch_with_test_no.py`, `update_answers_from_json.py`, `image_match_jsonl/fuzzy/v9_loose`, `merge_*`, `ensemble_voting` | **ÇOK-TEKRARLI** |
| **K9/R6** | Tek-sinyal → Tier H 49,468 rollback | ~7 | `tier_h_qip_exact.py:132`, `tier_h_v2_qip_offset.py`, `pilot_strategy_h_unique_id.py`, `pilot_tier_h_shift_fix.py`, `audit_task02[b]_tier_h_*` | orta (yüksek tekrar-riski) |
| **K10** | Crop count ≠ DB count | ~12 | `image_match_v15a_labelme_exact:97-103`, `image_match_v12/v13`, `analyze_n_to_n_groups.py`, `strategy_c_unused_crop`, `tier_d/g` (page-fallback), `image_match_n_to_n_text_v7` | orta |
| **K11** | 19+ matcher sürümü → provenance kaybı | **~33** | TÜM `image_match_v1..v15a` (11 sürüm tek batch'te!), `tier_c/d/f/g/h`, `image_match_rebuild_v5/rollback_v4`, `verify_image_match_*`, `deep_correctness_audit_v2`, `final_correctness_audit` | **ÇOK-TEKRARLI** |
| **K12** | Figür-bağımlı dışlama tutarsız | ~7 | `bug_7_10_smoke.py`, `classify_questions.py`, `audit_remaining_pool.py`, `beta_pattern_scanner`, `analyze_pilot_results` | düşük |
| **K13** | OCR prompt figürü tarif etmiyor | ~5 | `pipeline.py:290`, `classify_questions.py`, `solve_pipeline_v2.py`, `bug_7_10_smoke.py` | düşük |
| **K14** | Bayesian ai_upgrade (FIX'Lİ) + kalıntı | ~6 | `cross_validate_answers.py:114` (FIX canlı — PHANTOM), `cross_validate_answers (1).py` (fix DOĞRULANMADI), `test_cross_validate[.py/(1)]`, `merge_sources` | düşük (kalıntı P1) |
| **K15** | Kitap-adı join I→ı non-canonical | **~16** | `match_simple_v4.py:27-33`, `cross_validate_answers.py:159-170`, `create_answers_v8.py:134`, `merge_sources/v3`, `analyze_book_mapping.py`, `check_high_qnums`, `deep_audit`, `ensemble_voting`, `publisher_alignment_audit`, `test_preprocess_and_normalization.py` (kuralı SABİTLİYOR) | orta-yüksek |
| **K16** | Funnel'da provenance silme (dedup son-kazanır) | ~9 | `create_answers_v8.py:131-141`, `merge_v3_solved/production.py`, `merge_sources.py`, `clean_v2_4.py`, `fix_perfect_metadata.py` | orta |
| **K17** | Çözünürlük teşhisi var ama OCR'a bağlı değil (dead) | ~7 | `script_common.py:1665` (KESİN dead code), `image_quality_audit.py`, `assess_text_results.py`, `preprocess_screenshots`, `cutoff_detector_v1` | düşük |
| **K18** | Vanity-metrik (chi-square/sayı) gerçek metriği gizledi | **~16** | `validate_3tier[_selective].py` (chi-sq), `validate_match_[results/v3].py`, `analyze_coverage_impact/crossval`, `deep_audit`, `ma_tracker.py`, `update_quality_scores.py`, `eval_selective_prediction` (kısmi panzehir) | orta-yüksek |
| **K19** | Audit dalga-içi kapanıyor (audit-as-progress) | **~17** | `weekly_audit.py`, `faz_6_6_reject_audit.py`, `s198_promote_36.py` (phantom düzeltme itirafı), `diagnose_version_gap.py`, `microscopic_qa_analysis.py`, `drift_dashboard.py`, tüm `analyze_*` audit serisi | orta-yüksek |
| **K20** | OCR metni NFC-normalize edilmiyor (yazma anında) | ~12 | `ocr_crops.py` (NFC grep=0), `script_common.py`, `strategy_b_image_ocr` (NFKD≠NFC), `fix_near_classification` (encoding-artifact), `tier_j`, `wrong_case_deep_dive`, `test_script_common_new.py` | orta |

### En çok-tekrarlı 7 kök (sistemik baskı göstergesi)
1. **K1a (~38)** — gate format ölçer; her quality-gate/filter scripti buna çarpıyor.
2. **K1b (~34)** — dairesel GT; tüm LLM-judge/calibration/validate-GT zinciri.
3. **K11 (~33)** — matcher sürüm patlaması; tek başına 11 `image_match_v*` + 8 tier.
4. **K3 (~30)** — deterministik bağ yok; tüm post-hoc matcher'lar bunun tezahürü.
5. **K8 (~26)** — tek-sinyal match; çekirdek pipeline + tüm rakip matcher'lar.
6. **K2b (~22)** — upscale yok; tüm crop-OCR/solve scriptleri aynı 9px tavanı miras alıyor.
7. **K6 (~20)** — pozisyon-eşleşme; `prove_random_test.py` bunu BİZZAT İSPATLAMIŞ.

**Yorum:** Çok-tekrarlılık iki sınıfa ayrılıyor: (a) **ÖLÇÜM dairesi** (K1a/K1b/K18/K19 = ~105 vuruş toplam) — raporun "en derin kök ölçüm-tasarımı çöküşü" tezini sayısal olarak doğruluyor; (b) **POST-HOC YAMA dairesi** (K3/K8/K11 = ~89 vuruş) — ingest'te bağ kurulmadığı için her başarısızlık yeni script doğurmuş. İki daire toplamı ~194 vuruş, raporun K-zincir haritasındaki "META-KÖK iki kol" yapısını birebir yansıtıyor.

---

## 2. YENİ HATA MODLARI (K1-K20 DIŞI)

Batch'lerden çıkan, kök-neden raporunda **isimlendirilmemiş** modlar. İkiye ayırdım: (A) gerçek-yeni içerik/operasyon modu, (B) mevcut köklerin alt-tezahürü (yeni değil ama vurgu değer).

### A. GERÇEK YENİ MODLAR (rapora eklenmeli)

| # | Yeni mod | Kanıt | Neden K1-K20 değil |
|---|---|---|---|
| **M-A1** | **Subject-tag yanlış-sınıflama** (soru→subject_area etiket hatası) | `validate_subject_classification.py` (MATH_INDICATORS keyword → reclassify); MEMORY "Fizik→aritmetik, Kimya→dilbilgisi 5+ vaka" | K1-K20 metin/görsel/cevap/encoding eksenlerini kapsıyor ama **etiket-doğruluğu ekseni YOK**. Tek-sinyal keyword reclassify (K8'in subject ekseni) yanlış soruyu yanlış sınava sokar — beta'da görünür ürün hatası. |
| **M-A2** | **VLM safety-filter içerik kaybı** (geometri şekilleri sistematik bloke) | `tier_i_geometri_retry.py`: Gemini `HARM_CATEGORY_DANGEROUS_CONTENT`, `finish_reason != STOP`, 346 satır kayıp | K2 (çözünürlük) / K7 (tek-engine) ile akraba ama mekanizma farklı: engine **içeriği görmeyi reddediyor** (yanlış okumuyor). Subject-bias'lı sessiz veri kaybı; çok-model konsensüs bunu kapatır ama rapor bahsetmiyor. |
| **M-A3** | **Chi-square-driven cevap MUTASYONU** (vanity-metriği aktif veri-değişimine çevirme) | `validate_3tier_selective.py:2` "apply answer changes ONLY for books that improve [chi-square]" | K18 vanity-metriği **ölçer**; M-A3 o yanlış metriğe göre **production cevabını değiştirir** → gerçek-doğru cevapları bozma riski (YKS dağılımı uniform değil). K18'in pasif→aktif türevi, ayrı kayda değer. |
| **M-A4** | **Disk-üzeri " (1)" kopya / kanonik-dosya belirsizliği** (workspace hijyeni) | `cross_validate_answers (1).py`, `crop_from_detections (1).py`, `confidence_calibration (1).py`, `script_common (1).py`, `ocr_crops (1).py` (farklı engine!), `preprocess_screenshots (1).py` (farklı girdi!), `quality_improvement_pipeline (1).py`, `reextract_answer_keys (1).py`, `test_cross_validate (1).py`, `match_crop_answers (1).py`, `filter_crop_ocr (1).py`, `answers_v8 (1).db`, `eslesmis_sorucevap (1).jsonl`, `kiro2_questions_20260105` (v4 re-export) | K11 kod-içi *kasıtlı* sürümleme. Bu **kazara dosya-kopyası**: isimden kanonik belli değil, `import script_common` hangi kopyayı çözer belirsiz (PYTHONPATH/cwd). **K14 fix güvenini geçersiz kılıyor** — fix sadece canonical'da doğrulandı, " (1)" kopyada DOĞRULANMADI. ≥14 vaka. |

### B. ALT-TEZAHÜR (mevcut kök, yeni framing)

| # | Gözlem | İlişkili kök |
|---|---|---|
| M-B1 | **Alt-engine kurtarma silosu** (`paddleocr_recovery`, `ollama_crop_solver`, `qwen_vl_local_ocr`, `pix2text_enrichment` — hepsi upscale içermez, hiçbiri garble'ı çözmez, prod-funnel'a bağlanması izlenmez) | K2b + K11 (provenance-kopuk paralel silo) |
| M-B2 | **Ölü-tablo kalıntısı** (≥4 script v8'de SİLİNMİŞ `answers` tablosunu hâlâ sorguluyor → sessiz boş-sonuç riski) | K9/K11 alt-sınıfı |
| M-B3 | **İteratif eşik-sertleştirme canlı-DB'de** (`fix_near_classification`→`fix_near_strict_v2`→`fix_final_residual` aynı 7,302 NEAR'ı 3× farklı eşikle UPDATE) | K11 (rollback tarafı) + K16 (provenance) + audit-methodology.md ihlali |
| M-B4 | **Metadata cluster-reuse hata yayılımı** (`metadata_phase7_llm_generation.py:23-25` sim≥0.92 ile yanlış rationale'i N benzer soruya kopyalar) | K1b amplifier |
| M-B5 | **Metadata zinciri dairesel-GT'ye sessiz bağımlı** (`metadata_phase2_irt_compute.py` "KESIN_DOGRU" üzerinden IRT SE/Fisher üretir; etiket dairesel ise IRT-metadata kontamine) | K1b downstream amplifikasyon |
| M-B6 | **Hardcoded mutlak path / hardcoded API key** (`irt_calibration_runner.py` sys.path; `alibaba_crop_solver.py:38` DashScope key plaintext) | K-dışı; güvenlik/taşınabilirlik (rotate gerek) |
| M-B7 | **OCR-dışı pilot kirliliği** (`_pilots/` içinde auth-security, Locust load, property-BKT/IRT/FSRS, race-condition — 4+ script OCR pipeline DIŞI) | meta; provenance şeması yok |

**Net sonuç:** İçerik-kalite ekseninde **1 gerçek yeni kök** (M-A1 subject-tag) + **3 türev-yeni mod** (M-A2 VLM-safety, M-A3 chi-sq-mutasyon, M-A4 dosya-kopya belirsizliği). Diğer ~270 script K1-K20'ye temiz oturuyor.

---

## 3. ÖLÜ / TEKRAR-RİSKLİ SCRIPTLER

### 3a. Rollback olmuş ama silinmemiş (yüksek tekrar-riski)
| Script | Durum | Risk |
|---|---|---|
| `tier_h_qip_exact.py` | 49,468 satır YANLIŞ, rollback `6a3fa7fc0` | Silinmedi; tek-sinyal pattern tekrar çalıştırılabilir |
| `tier_h_v2_qip_offset.py` | Konsept iptal, pilot %75 yanlış | Silinmedi |
| `pilot_tier_h_shift_fix.py` | Rollback'li Tier H'i diriltme girişimi | **EN yüksek** — rollback edilmişi geri açmaya çalışıyor |
| `pilot_strategy_h_unique_id.py` | Tier H temeli (rollback'e gitti) | tekrar-riski |
| `eslesmis_sorucevap_rematched_HARMFUL.jsonl` | Adıyla "zararlı", arşivlenmiş | İyi pratik (arşive alınmış) |

### 3b. Ölü-tablo sorgulayan (sessiz boş-sonuç)
`match_crop_answers (1).py`, `match_from_db.py`, `implement_4tier.py`, `match_simple_v4.py` (bookend dalı), `rematch_with_*.py`, `replace_db_v7_sources.py` — hepsi v8'de **silinmiş `answers` tablosunu** (%39 doğruluk) sorguluyor.

### 3c. Çelişen/mükerrer rakip girişimler (aynı işi farklı mantıkla)
- **4+ rakip cevap-matcher:** `match_simple_v4`, `match_from_db`, `match_crop_answers`, `implement_4tier`, `rematch_with_test_no` — hangisi son üretim belirsiz.
- **19+ image-matcher** (K11): `image_match_v1..v15a` + `tier_c..h` + `strategy_a..d` + `pilot_n_to_n*`. **Geç sürüm = daha zayıf sinyal** (v6/v12 det.1:1 → v13 3/5 → v15a Y-sıra → v15 tüm-sayfa) — coverage baskısı kaliteyi DÜŞÜRMÜŞ.
- **≥14 " (1)" kazara kopya** (M-A4) — biri Gemini/biri Qwen, biri JSONL/biri dizin (davranışsal FARKLI, isim neredeyse aynı).

### 3d. Stub (hiç çalışmamış)
`pix2text_enrichment.py`, `qwen_vl_local_ocr.py` — STUB/FUTURE, CUDA/VRAM gereksinimi karşılanmamış.

### 3e. Veri-artifact ölü/duplicate (`data_db.md` + `data_jsonl.md`)
- **Ölü .db:** `answer_keys_v6/progress.db` (answers boş), `matched_v1..v4` (tarihsel), `answers_v7/v9/v10`.
- **Duplicate .db:** `answers_v8 (1).db`, `kiro2_questions_20260105` (v4 re-export).
- **Canlı:** sadece `answers_v8.db` + `ocr_v3/progress.db` (75,819 OCR kaynak).
- **15+ matched .jsonl sürümü** + 11 backup + 11 answer-key sürümü → masif tarihsel birikim, hiçbiri temizlenmemiş.

**Öneri:** `_deprecated/` taşıma + import path'leri tek kanonik dosyaya sabitleme (CLAUDE.md deprecation-guard.md prosedürüyle). Tier-H ailesi `sys.exit(DEPRECATED)` ile mühürlenmeli.

---

## 4. KAPSAM AÇIĞI — 31 May Raporu Bu 275 Girişimi Kapsadı mı?

**Genel:** Rapor (8 eksen, 20 kök) içerik-kalite eksenini **mükemmele yakın** kapsıyor. ~270/275 script K1-K20'ye temiz oturuyor. Ancak şu **5 alan atlanmış/eksik kapsanmış**:

| # | Atlanan alan | Detay |
|---|---|---|
| **AÇIK-1** | **Subject-tag doğruluğu ekseni YOK** (M-A1) | 8 eksen metin/görsel/cevap/encoding/ölçüm-meta'yı kapsıyor; **soru→ders etiketi** ekseni hiç yok. `validate_subject_classification.py` + MEMORY 5+ vaka kanıtlı. Beta'da görünür ürün hatası — eklenmesi gerek. |
| **AÇIK-2** | **VLM safety-filter veri kaybı** (M-A2) | K7 "tek-engine" var ama "engine içeriği görmeyi reddediyor" mekanizması ayrı. 346 geometri satırı sessiz kayboldu; subject-bias'lı. Rapor değinmiyor. |
| **AÇIK-3** | **Vanity-metriğin aktif veri-mutasyonuna dönüşmesi** (M-A3) | K18 metriği "gizledi" diyor ama `validate_3tier_selective.py`'ın chi-square'i iyileştirmek için **cevap değiştirdiği** (production'ı bozma) belirtilmemiş. K18'den ayrı şiddette. |
| **AÇIK-4** | **Workspace hijyeni / kanonik-dosya belirsizliği** (M-A4) | K11 *kod-içi* sürümlemeyi kapsıyor ama disk-üzeri ≥14 " (1)" kopyayı (farklı-davranış-aynı-isim) kapsamıyor. **K14 phantom-fix güvenini doğrudan etkiliyor** — fix " (1)" kopyada doğrulanmadı. Bu, raporun "K14 FIX'Lİ → PHANTOM" sonucunu kısmen riske atıyor. |
| **AÇIK-5** | **Audit-script provenance'ı** (Batch 01/02 meta-gözlem) | K11 *matcher* provenance'ını kapsıyor; ama her matcher sürümünün kendi `deep_correctness_audit_v2`/`final_correctness_audit`/per-tier audit scriptini doğurduğu **audit-deposu kirliliği** ayrı kapsanmamış. K19'un alt-mekanizması ama explicit değil. |

**İkincil eksikler (rapor doğru ama eksik vurgu):**
- **Metadata zinciri kontaminasyonu** (M-B4/M-B5): K1b "kalibrasyonu invalide et" diyor ama `metadata_phase2-7` zincirinin (IRT-SE, Fisher, cluster-reuse rationale) bu invalidasyona dahil olduğu explicit değil — downstream amplifikasyon kapsam-dışı.
- **CLAUDE.md isim driftı** (`data_jsonl.md`): `d-dataset/ocr_output/` ve `d-dataset/answer_keys/` dizinleri **hiç var olmamış** (silinmemiş, isim driftı). Rapor K-listesi bunu yakalamıyor; gerçek yollar `output/ocr*` ve `output/answer_keys_v2..v11`. Belge-kod uyumsuzluğu.
- **Ölü-tablo kalıntısı** (M-B2): K9 Tier-H'i kapsıyor ama silinmiş `answers` tablosunu hâlâ sorgulayan ≥4 scriptin **sessiz boş-sonuç** riski ayrı işaretlenmemiş.

**Sonuç:** Rapor içerik-kalite kök-nedenlerini büyük doğrulukla kapsadı (3 challenge ile 5/5 doğrulandı, phantom filtresi uygulandı). Ancak **4 yeni mod (M-A1..M-A4)** ve **5 kapsam açığı** eklenebilir — bunların hiçbiri raporun TOP-5 tezini çürütmüyor, üzerine genişletiyor. En kritik açık **M-A4 (dosya-kopya belirsizliği)**: raporun K14 "PHANTOM-fix" güven derecesini doğrudan zayıflatan tek bulgu.
