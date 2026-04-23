# Mutating HTTP route envanteri (F4 — Dalga A)

**Tarih:** 2026-04-23  
**Yöntem:** `backend/api/**/*.py` içinde `@router.post|put|patch|delete` sayımı (`rg`).

## Özet

| Desen | Yaklaşık eşleşme (dosya başına) |
|--------|----------------------------------|
| `@router.post(` | ~280+ (çoklu dosya) |
| `@router.put(` | (post ile birlikte sayıldı) |
| `delete` / `patch` | dağıtılmış |

**Not:** Bu sayım **dekoratör satırı** bazlıdır; alt router birleşimleri ve `app.include_router` önekleri OpenAPI ile birlikte doğrulanmalı.

## En yoğun modüller (mutating endpoint)

Örnek yüksek sayım (tek dosya): `diary_api.py`, `teacher_routes.py`, `live_session_routes.py`, `auth.py`, `multisensory_learning_api.py`, `video_analytics_routes.py`, `student_dashboard.py`, `question_crud_api.py`, `learning_path_v2.py`, `zpd_maarif.py`.

## Dalga B önceliği (öğrenci verisi)

1. `student_id` / `user_id` gövde veya path taşıyan **POST/PUT/PATCH** (öğrenci rolü ile).  
2. `question_crud_api`, `learning_path_v2`, `offline_sync_api`, `pwa_sync_api`, `student_dashboard` (hedef yazma).  
3. Chroma: `content_recommendation`, `semantic_search`, `duplicate_detection` — **IDOR** (plan F4).

## Komut (yenileme)

```bash
cd backend && rg "@router\.(post|put|patch|delete)\(" api --glob "*.py" -c
```

## Dalga B — kapanan örnek (2026-04-23)

| Modül | Uç | Düzeltme |
|--------|-----|----------|
| `api.revolutionary_features` | `POST .../zpd-maarif/revolutionary/calculate` | `verify_student_access` |
| `api.revolutionary_features` | `POST .../zpd-maarif/revolutionary/recommend` | `verify_student_access` |
| `api.revolutionary_features` | `POST .../zpd-maarif/revolutionary/cultural-context` | `verify_student_access` |
| `api.zpd_maarif` | `POST /api/v1/zpd-maarif/revolutionary/calculate` | `verify_student_access` + `get_db` |
| `api.zpd_maarif` | `POST .../revolutionary/recommend` | aynı |
| `api.zpd_maarif` | `POST .../revolutionary/cultural-context` | aynı |
| `api.zpd_maarif` | `POST .../revolutionary/adapt-difficulty` | aynı |
| `api.zpd_maarif` | `POST .../revolutionary/learning-balance` | aynı |
| `api.zpd_maarif` | `POST .../revolutionary/cultural-patterns` | aynı |
| `api.turkish_nlp_chat` | `POST .../turkish-nlp-chat/message` | aynı |
| `api.turkish_nlp_chat` | `POST .../turkish-nlp-chat/context/manage` | aynı |
| `api.turkish_nlp_chat` | `POST .../turkish-nlp-chat/step-by-step-solution` | aynı (2026-04-23 ek) |
| `api.berturk_api` | `POST .../berturk/motivation/assess` (`student_id`) | `UserRole` staff + `str(id)` self; önceden `["teacher","admin"]` + `SUPER_ADMIN` dışı |
| `api.berturk_api` | `GET .../performance/stats`, `POST .../cache/clear` | `ADMIN` \| `SUPER_ADMIN` |
| `api.cultural_adaptation_api` | `GET/PUT .../student/{student_id}*` | `UserRole` staff + self; `SUPER_ADMIN` eklendi; `/test-adaptation` `ADMIN`\|`SUPER_ADMIN` |

| `api.parent_social_api` | `GET/PUT .../settings/{student_id}`, `activity`, `flags`, `disable-all` | `PARENT` + `parent_child.approved` (önceden sahte `ParentSocialSettings` ile IDOR) |
| `api.irt_morfoloji` | `POST .../recommend-questions` (`student_id`) | staff \| self `users.id` \| `verify_student_access` |
| `api.exam_performance` | `GET .../student/{id}/improvement-trends` | `UserRole` staff + `str` id; önceden yalnızca `"admin"` string |
| `api.exam_performance` | `GET .../{exam_session_id}/detailed-analysis`, `weaknesses`, `study-recommendations`, `performance-comparison` | Oturum `student_id` sahibi veya staff (`_assert_exam_session_authorized`) |
| `api.elasticsearch` | `GET .../analytics/user/{user_id}` | `TEACHER`/`ADMIN`/`SUPER_ADMIN` veya self; önceden yalnızca `"admin"` string |
| `api.ferpa_coppa_compliance_api` | COPPA oluşturma / doğrulama / çekme / FERPA oluşturma / COPPA GET | Veli+`parent_child`, staff, veya öğrenci self; açık uçlar kapatıldı |
| `api.analytics` | `GET .../student/{student_id}` | Staff, self `users.id`, veya `verify_student_access` (STU profil) |
| `api.elasticsearch` | `GET .../admin/indices/stats` | `UserRole.ADMIN` \| `SUPER_ADMIN` (string `role_val` kaldırıldı) |
| `api.video_solution` | silme / streaming oluşturma / onay | Yükleyen veya `ADMIN`\|`SUPER_ADMIN` |
| `api.bionic_reading` | `/stats`, `/cache` (clear_all) | `ADMIN`\|`SUPER_ADMIN` |
| `api.content_api` | makale PUT/DELETE | Yazar veya `ADMIN`\|`SUPER_ADMIN` |
| `api.enhanced_user_management_api` | `require_admin` / `require_admin_or_self` | `UserRole` (`ADMIN`\|`SUPER_ADMIN`); self `str(id)` eşlemesi |
| `api.quality_gates_api` | override onay / sil | Onay: `TEACHER`\|`ADMIN`\|`SUPER_ADMIN`; sil: talep eden veya `ADMIN`\|`SUPER_ADMIN` |
| `api.content_management` | tüm `admin_yetki_kontrolu` uçları | `MockUser`/string liste kaldırıldı; `AuthenticatedUser` + `UserRole` staff |
| `api.enhanced_chat` | `POST /message`, `POST /stream` (`student_id` gövde) | `verify_student_access`; kimliği doğrulanmış + DB yoksa 503 |
| `api.enhanced_chat` | `GET /history/{student_id}` | 401 (anon); `verify_student_access` + sohbet sorgusu profil sahibi `user_id` ile |
| `api.enhanced_chat` | `POST /message-with-attachment` | Form `student_id` zorunlu (auth varken); `verify_student_access` |
| `api.v1.expert_agents_api` | `POST /api/v1/ask-question` (`student_id` opsiyonel gövde) | Dolu ise `verify_student_access` + ORM `User` string rol desteği (`learning_path_auth`) |

Birim: `tests/unit/test_revolutionary_features_idor.py`, `tests/unit/test_zpd_maarif_revolutionary_idor.py`, `tests/unit/test_turkish_nlp_chat_idor.py`, `tests/unit/test_berturk_motivation_idor.py`, `tests/unit/test_cultural_adaptation_auth.py`, `tests/unit/test_parent_social_access.py`, `tests/unit/test_irt_morfoloji_recommend_idor.py`, `tests/unit/test_exam_performance_improvement_auth.py`, `tests/unit/test_exam_performance_session_guard.py`, `tests/unit/test_ferpa_coppa_guards.py`, `tests/unit/test_analytics_student_access.py`, `tests/unit/test_enhanced_user_management_auth.py`, `tests/unit/test_enhanced_chat_student_guard.py`, `tests/unit/test_learning_path_auth_roles.py`, `tests/unit/test_moderation_check_status_auth.py`.

## Okuma / durum sorgusu (F4 — IDOR)

| Modül | Uç | Düzeltme |
|--------|-----|----------|
| `api.moderation_api` | `GET /api/v1/moderation/check-status/{user_id}` | Yalnızca **self** veya `ADMIN` / `SUPER_ADMIN` (önceden her auth kullanıcı başkasının mute/ban durumunu sorgulayabiliyordu) |

## Sonraki adım

- Dalga B: kalan `student_id` / `user_id` gövdeli POST’lar için CSV + sırayla guard.  
- Her düzeltme sonrası `test_golden_flows` veya birim test.
