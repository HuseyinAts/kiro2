# Ç4 — 82 Boş Tablo Sınıflaması (kanıt-tabanlı, agent-team)

**Yöntem:** 7-ajan workflow (wlibjxlwy), her tablo için CANLI `rg` ile ORM `__tablename__` modeli + api/service wiring kanıtı. Silme YOK — sadece kanıt.

## Sonuç: "82 boş = bloat at" VARSAYIMI ÇÜRÜDÜ

| Sınıf | Adet | Anlam | Aksiyon |
|---|---|---|---|
| **MODELED_WIRED** | **51** | ORM modeli VAR + api/service kullanıyor; tablo boş = sadece **veri beslenmemiş (lansman öncesi)** | **KORU** — drop uygulamayı kırar |
| **MODELED_UNWIRED** | **30** | ORM modeli VAR ama hiçbir endpoint/service kullanmıyor = **özellik-stub / ölü-kod** | Kod+şema temizlik backlog'u (model+tablo BİRLİKTE, test kontrolüyle) — DB-only drop değil |
| **DEAD** | **1** | ORM modeli YOK + wiring YOK | **platform_stats** — tek doğrulanmış-güvenli drop |

> **Kritik düzeltme:** İlk turda inline-grep "0/82 modelsiz" dedi (escape bozuktu). Grep tool ile çürütüldü: 81/82 modelli. Körlemesine drop olsaydı **81 ORM modeli kırılırdı**. Kırık-ölçüm dersi canlı tekrar.

## DEAD (1) — doğrulanmış-güvenli drop adayı
- **platform_stats**: `rg platform_stats backend/models|app|api|services` → yalnız `alembic/env.py` + `scripts/fix_optimize_kiro2.sql`; canlı model/endpoint YOK.

## MODELED_UNWIRED (30) — kod-temizlik backlog (DB-only drop YASAK)
class_reports, classrooms, curriculum_alignments, curriculum_update_requests, duels, eba_content_analytics,
eba_content_collections, eba_video_recommendations, eba_video_usage, educational_contents, fallback_videos,
**fsrs_reviews, fsrs_schedules, fsrs_student_profiles, fsrs_study_sessions, fsrs_subject_stats**, learning_outcomes,
meb_curriculum_standards, osym_standards, parent_approvals, parent_reports, point_transactions,
quality_gate_results, quality_gates_override_audit, quality_gates_runs, question_knowledge_mappings,
question_performance_analytics, sessions, student_grades, system_configurations

**Önemli alt-bulgu — FSRS çift şema:** 5 `fsrs_*` tablosu modelli ama wire'sız; canlı FSRS `fsrs_cards` (116 satır, dolu) kullanıyor. → **terkedilmiş ikinci FSRS şeması** (review.md GF4 fsrs_cards ile çalışıyor). Kod-temizlik adayı (model+tablo birlikte).

## MODELED_WIRED (51) — aktif özellik, veri bekliyor (KORU)
audit_logs, blocked_users, chat_analytics, dina_parameters, duel_matches, duel_sessions, eba_videos,
error_clusters, exam_questions, exam_sessions, forum_solutions/votes, knowledge_points, learning_analytics,
manipulative_*, mentor_*, moderation_actions, nano_skills, **notifications, student_answers, student_goals,
study_rooms, study_sessions, teacher_profiles, user_badges, user_achievements, veli_consent, quizzes, quiz_***...
(tam liste empty_classify.json)

## Öneri (kanıtlı)
1. **DB drop (güvenli, 1):** platform_stats — tek DEAD. (Kullanıcı onayıyla; bu oturumda drop'lar durduruldu.)
2. **Kod+şema temizlik backlog (30):** her UNWIRED için model+tablo birlikte sil — ayrı refactor sprint'i, test-kontrollü (DB-only drop ORM'i yetim bırakır). Öncelik: FSRS çift-şema 5 tablo + quality_gates 3 tablo.
3. **51 WIRED:** dokunma — lansmanla dolacak özellikler.
4. **165 all-null sütun:** aynı mantık — çoğu modelli alan, körlemesine drop değil; UNWIRED model temizliğiyle birlikte ele al.

**Net:** "şema şişkinliği" büyük ölçüde **scaffold-debt değil, lansman-öncesi-boş aktif özellik**. Gerçek atılabilir: 1 tablo + 30 stub (kod-eşli). DB satır şişkinliği asıl mock'ta (200K) — o ayrı (Ç1).

---
*Workflow wlibjxlwy (7 ajan, 159 tool-use, 82/82). Kanıt: empty_classify.json. Hiçbir drop uygulanmadı.*

---
## C1 TAM DOĞRULAMA (30/30, 2-pass + deterministik) — 22 Haz
**Sonuç: otonom-güvenli DROP YOK. Şema-silme deploy-gate'li refactor gerektirir.**

- 8 tablo "safe" işaretlendi AMA kesin değil — verification scope'u tekrar tekrar komplikasyon çıkardı:
  - **fallback_videos:** ilk-pass "safe", resume-pass "BLOCKED" — `database/learning_path_repository.py:481-536` FallbackVideo CRUD + canlı endpoint (learning_path_v2.py:1693) bulundu. Scope `api/services/app` idi, **`database/` repository-katmanı kaçtı.**
  - **sessions:** `Session` SQLAlchemy ile 182-dosya isim-çakışması → grep'le güvenli denemez.
  - **duels:** gamification.Duel kullanılmıyor ama 10 `\bDuel\b` hit (alembic/celery) — inceleme gerek.
  - **quality_gates_override_audit:** tüm-backend 0 hit — tek net-temiz aday.
- **22 blocked:** relationship-target (EBAVideo→usage/recommendations, FSRSCard/User→fsrs_reviews, curriculum standards→alignments, User→classrooms), test-coverage (eba_*, educational_contents 25+ test), incoming-FK (osym_standards), seed-script (educational_contents).

### Kanıta dayalı karar
Mass tablo+model silme: (1) repository/seed/alembic katmanlarını da tarayan tam-scope verify, (2) ORM-model + tablo + test birlikte kaldırma, (3) container rebuild + golden-flow test, (4) per-tablo insan onayı gerektirir. **Otonom DB-drop YASAK** (deprecation-guard.md + İnsan-Döngüsü). Bu oturumda hiçbir şema-silme uygulanmadı; yalnız `platform_stats` (DEAD, 0-model) daha önce düşürüldü.
