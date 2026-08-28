# P1 — Atıl Özellik Aktivasyon Keşfi (write-path tracing, agent-team)

**Yöntem:** 15 çekirdek wired-boş özelliğin WRITE-path'i agent-team ile izlendi (wr40px1m9, read-only, file:line kanıtlı). Kanıt: feature_activation.json.

## Sonuç: "wired-boş = aktive edilebilir borç" premisi ÇÜRÜDÜ
- **DORMANT 10/15:** write-path CANLI + erişilebilir, boş çünkü kullanıcı trafiği yok. Lansman-öncesi DOĞRU durum, kod sorunu değil. Beta ile dolar.
- **NO_WRITE_PATH 5/15:** gerçek eksik.

## DORMANT (kod değil — beta-trafiği bekliyor; sahte-seed YASAK)
| Tablo | Write-path (canlı) |
|---|---|
| exam_sessions / exam_questions / student_answers | osym_exam_engine.py:424/438/665 (sınav motoru, GF3 write tarafı) |
| study_sessions | learning_path.py:1584 (POST /study-session/start) |
| topic_completions | learning_path.py:1030 (PUT /completion) |
| notifications | tasks/push_tasks.py:28 (Celery beat scheduled) |
| student_goals / user_badges / study_rooms / streak_daily_log | dashboard/learning_event/study_rooms/streak servisleri |

## NO_WRITE_PATH (gerçek eksik — backlog, deploy-gate)
| Tablo | Efor | Sorun (kanıt) |
|---|---|---|
| **quiz_submissions** | MED | **SESSİZ-VERİ-KAYBI:** writer `learning_path_repository.py:443 create_quiz_submission()` VAR ama 0 caller; canlı submit endpoint (learning_path.py:1077) skoru döndürüp persist ETMİYOR. Ama quizzes boş olduğundan endpoint zaten 404 → moot. |
| quizzes / quiz_questions | HIGH | Yazıcı HİÇ yok; submit endpoint select-only, 404 üretiyor. Quiz-üretim/seed yolu inşa edilmeli. |
| user_achievements | HIGH | Award-mantığı hiç yazılmamış (yalnız read). Gamification yarım. |
| knowledge_points | MED | Statik referans taksonomi → SEED gerek (runtime writer değil). Değeri knowledge-graph kullanımına bağlı. |

## Kanıta dayalı öneri (revize)
- **P1 cheap-otonom-kazanç vermedi.** 10 dormant özellik = lansman bekliyor (kod yok); 5 eksik = tam-özellik-inşa (deploy-gate) veya değeri-belirsiz seed.
- **Gerçek unlock = P3 (beta launch):** dormant 10 tabloyu gerçek trafikle doldurur — sahte-seed değil. Quiz/achievement = ayrı feature-build sprint'i (lansman sonrası).
- **Latent bug kayda geçti:** quiz_submissions wiring (quiz-feature inşa edilirse mutlaka eklenmeli, yoksa öğrenci quiz cevapları sessizce kaybolur).
