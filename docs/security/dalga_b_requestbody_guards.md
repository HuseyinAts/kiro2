# Dalga B — requestBody tenant ipuçları ve guard özeti

Kaynak: [dalga_b_requestbody_tenant_hints.tsv](dalga_b_requestbody_tenant_hints.tsv) (OpenAPI `requestBody` şema özellik adları).

Bu dosya P0 IDOR incelemesi sonrası **hangi uçta hangi koruma** olduğunu tek bakışta gösterir. Üretim kodu değişince satırları güncelleyin.

| method | path | body_tenant_hint | Guard / not |
|--------|------|------------------|-------------|
| POST | /api/v1/berturk/motivation/assess | student_id | Staff veya `current_user.id` eşleşmesi ([berturk_api.py](../../backend/api/berturk_api.py)) |
| POST | /api/v1/billing/webhook | user_id | `BILLING_WEBHOOK_SECRET` + header ([billing_api.py](../../backend/api/billing_api.py)) |
| POST | /api/v1/compliance/coppa/parental-consent | child_id, parent_id | Veli+onaylı ilişki / admin ([ferpa_coppa_compliance_api.py](../../backend/api/ferpa_coppa_compliance_api.py)) |
| POST | /api/v1/compliance/ferpa/consent | parent_id, student_id | Öğrenci / veli+ilişki / staff (aynı modül) |
| POST | /api/v1/eba-tv/recommendations | student_id | `assert_can_access_body_student_id` ([ebatv.py](../../backend/api/ebatv.py)) |
| POST | /api/v1/enhanced-chat/message | student_id | `verify_student_access` ([enhanced_chat.py](../../backend/api/enhanced_chat.py)) |
| POST | /api/v1/enhanced-chat/stream | student_id | Aynı |
| POST | /api/v1/irt-morfoloji/recommend-questions | student_id | `assert_can_access_body_student_id` ([irt_morfoloji.py](../../backend/api/irt_morfoloji.py)) |
| POST | /api/v1/learning-path/adapt-path | student_id | `verify_student_access` ([learning_path_v2.py](../../backend/api/learning_path_v2.py)) |
| POST | /api/v1/learning-path/assess-knowledge | student_id | Aynı |
| PUT | /api/v1/learning-path/completion/{student_id} | student_id | Aynı |
| POST | /api/v1/learning-path/create-path | student_id | Aynı |
| POST | /api/v1/learning-path/quiz/{quiz_id}/submit | student_id | Aynı |
| POST | /api/v1/learning-style/behavioral-data/{student_id} | student_id | `verify_student_access` ([learning_style.py](../../backend/api/learning_style.py)) |
| POST | /api/v1/learning-style/questionnaire/{student_id} | student_id | Aynı |
| POST | /api/v1/live-sessions/{session_id}/chat | recipient_id | Katılımcı + alıcı doğrulama; GET chat özel mesaj filtre ([live_session_routes.py](../../backend/api/live_session_routes.py)) |
| POST | /api/v1/manipulatives/geogebra/activity | user_id | Gövde `user_id` = token ([manipulatives_api.py](../../backend/api/manipulatives_api.py)) |
| POST | /api/v1/manipulatives/geometry/tool-usage | user_id | Aynı |
| POST | /api/v1/manipulatives/tangram/puzzle | user_id | Aynı |
| POST | /api/v1/math-solution-steps/check-answer | student_id | `_verify_student_access` ([math_solution_steps.py](../../backend/api/math_solution_steps.py)) |
| POST | /api/v1/moderation/actions | target_user_id | `get_current_admin_user` ([moderation_api.py](../../backend/api/moderation_api.py)) |
| POST | /api/v1/moderation/reports | reported_user_id | Raporlayan = token; kendini rapor yok |
| POST | /api/v1/parent/notifications | child_id | Veli + `ParentService` onaylı ilişki ([parent.py](../../backend/api/parent.py)) |
| POST | /api/v1/recommendations/ | user_id | `_authorized_target_user_id` ([content_recommendation.py](../../backend/api/v1/content_recommendation.py)) |
| POST | /api/v1/recommendations/interaction | user_id | Aynı |
| POST | /api/v1/revolutionary-features/.../calculate | student_id | `verify_student_access` ([revolutionary_features.py](../../backend/api/revolutionary_features.py)) |
| POST | /api/v1/revolutionary-features/.../cultural-context | student_id | Aynı |
| POST | /api/v1/revolutionary-features/.../recommend | student_id | Aynı |
| POST | /api/v1/sync/progress | userId | `userId` = token ([pwa_sync_api.py](../../backend/api/pwa_sync_api.py)) |
| POST | /api/v1/sync/exam-sessions | (session_id) | Mevcut oturum sahibi + conflict’te `student_id` güncellenmez |
| POST | /api/v1/turkish-nlp-chat/context/manage | student_id | `verify_student_access` ([turkish_nlp_chat.py](../../backend/api/turkish_nlp_chat.py)) |
| POST | /api/v1/turkish-nlp-chat/message | student_id | Aynı |
| POST | /api/v1/turkish-nlp-chat/step-by-step-solution | student_id | Aynı |
| POST | /api/v1/zpd-maarif/hesapla | ogrenci_id | `assert_can_access_body_student_id` ([zpd_maarif.py](../../backend/api/zpd_maarif.py)) |
| POST | /api/v1/zpd-maarif/optimize | ogrenci_id | Aynı |
| PUT | /api/v1/zpd-maarif/profil/kulturel/{ogrenci_id} | ogrenci_id | Aynı |
| PUT | /api/v1/zpd-maarif/profil/maarif/{ogrenci_id} | ogrenci_id | Aynı |
| POST | /api/v1/zpd-maarif/revolutionary/* | student_id | Aynı |
| POST | /api/v2/cat/start | student_id | `_verify_student_access` ([question_bank_v2_routes.py](../../backend/api/question_bank_v2_routes.py)) |
| POST | /api/v2/knowledge-graph/recommendations | student_id | Aynı |

**Yenileme:** OpenAPI değiştikten sonra TSV’yi üretmek için:

```bash
cd backend
python scripts/dalga_b_requestbody_tenant_id.py openapi.json
```

Ardından bu tabloyu yeni uçlar için gözden geçirin.
