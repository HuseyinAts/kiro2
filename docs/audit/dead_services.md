# Dead Service Raporu

Tarih: 2026-03-23 | Yontem: Python import cross-reference (api/ + core/ + services/)

## Ozet

| Metrik | Deger |
|--------|-------|
| Toplam servis dosyasi | ~173 |
| Kullanilan | ~122 |
| **DEAD (hicbir yerden import edilmiyor)** | **51** |
| **Dead code satir sayisi** | **28,568** |

## Dead Service Listesi (buyukten kucuge)

| Dosya | Satir | Kategori |
|-------|-------|----------|
| performance_analytics_system.py | 1150 | analytics |
| item_selection_optimizer.py | 1149 | irt/adaptive |
| enhanced_resource_recommendation_engine.py | 1110 | recommendation |
| content_management_service.py | 1048 | content |
| realtime_adaptation_system.py | 1042 | adaptive |
| question_generation_service.py | 949 | generation |
| doc_updater_service.py | 940 | docs |
| similar_question_service.py | 937 | question |
| meta_learning_service.py | 874 | adaptive |
| alert_service.py | 827 | monitoring |
| performance_monitor_service.py | 820 | monitoring |
| osym_scoring_system.py | 818 | exam |
| safety_service.py | 809 | security |
| ab_testing_service.py | 804 | testing |
| rule_evolution_service.py | 802 | adaptive |
| pattern_service.py | 792 | adaptive |
| accessibility_service.py | 761 | a11y |
| unified_resource_provider.py | 733 | resource |
| youtube_enhanced.py | 714 | youtube |
| study_room_service.py | 636 | collaboration |
| feedback_service.py | 628 | feedback |
| curriculum_compliance_service.py | 601 | curriculum |
| batch_processing.py | 574 | infra |
| chromadb_collection_manager.py | 568 | vector |
| log_management_service.py | 567 | monitoring |
| motivation_support.py | 564 | gamification |
| ydt_time_tracking_service.py | 552 | ydt |
| formative_test.py | 541 | test_types |
| similarity_base.py | 529 | similarity |
| diagnostic_test.py | 510 | test_types |
| ydt_optical_form_service.py | 484 | ydt |
| tyt_exam_service.py | 467 | exam |
| dual_coding_optimizer.py | 441 | learning |
| ab_testing.py | 436 | testing |
| quality_aware_question_generator.py | 418 | generation |
| sse_service.py | 367 | realtime |
| retrieval_practice_engine.py | 341 | learning |
| hybrid_learning_style_detector.py | 340 | learning |
| ydt_exam_service.py | 306 | ydt |
| irt_parameter_estimator.py | 299 | irt |
| osym_question_scraper.py | 244 | scraping |
| sindbert_turkembed_service.py | 243 | nlp |
| zemberek_nlp_server.py | 203 | nlp |
| mock_exam.py | 169 | exam |
| benchmark_test.py | 125 | testing |
| fast_learning_service.py | 100 | learning |
| team_challenges.py | 95 | gamification |
| summative_test.py | 75 | test_types |
| advanced_analytics.py | 52 | analytics |
| tyt_optical_form_service.py | 14 | exam |
| test_types_implementation.py | 0 | test_types |

## Kategori Dagilimi

| Kategori | Dosya | Satir |
|----------|-------|-------|
| adaptive/learning | 8 | 5,487 |
| exam/test_types | 7 | 2,600 |
| monitoring/logging | 3 | 2,214 |
| irt/psychometric | 2 | 1,448 |
| youtube/content | 2 | 1,762 |
| testing (ab) | 3 | 1,365 |
| question generation | 3 | 2,304 |
| nlp | 2 | 446 |
| ydt | 3 | 1,342 |
| diger | 18 | 10,600 |

## Oneriler

1. **Hemen silinebilir (0 risk):** `test_types_implementation.py` (0 satir), `tyt_optical_form_service.py` (14 satir)
2. **Buyuk dead code bloklari:** Ilk 10 dosya = 9,927 satir (%35 of dead)
3. **Duplikasyon:** `ab_testing.py` + `ab_testing_service.py`, `tyt_exam_service` + `tyt_optical_form_service`
4. **Potansiyel gelecek kullanim:** `sse_service.py`, `retrieval_practice_engine.py` — Master Plan v2.0'da aktive edilebilir

## Sonraki Adim

Kullanici karari bekleniyor: hangileri silinecek, hangileri korunacak.
`_deprecated/services/` klasorune tasimak en guvenli yaklasim.
