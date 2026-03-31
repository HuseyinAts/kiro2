# Manual SQL Migrations

These files were executed manually outside of Alembic.
The current DB schema is captured in `docs/schema_snapshot_20260331.sql`.

**Rule: New migrations MUST use `alembic revision --autogenerate`. Manual SQL is PROHIBITED for new work.**

## Alembic Status

- Head: `learning_events_001`
- DB is stamped at head as of 2026-03-31

## File Index

| File | Purpose |
|------|---------|
| 001_create_users_table.sql | Users table |
| 001_yks_generation_tables.sql | YKS question generation |
| 002_create_exams_table.sql | Exams table |
| 003_create_questions_table.sql | Questions table (legacy, empty) |
| 004_create_exam_answers_table.sql | Exam answers |
| 005_create_gamification_tables.sql | Gamification (badges, points, levels) |
| 005_learning_path.sql | Learning path tables |
| 006_create_eba_khan_tables.sql | EBA + Khan Academy integration |
| 007_create_parent_teacher_tables.sql | Parent/teacher relationships |
| 008_create_video_cache_table.sql | YouTube video cache |
| 009_create_learning_path_tables.sql | Learning path v2 tables |
| 010_topic_hierarchy_v2.sql | Topic hierarchy tree |
| 010_upgrade_question_bank_v2.sql | Question bank v2 columns |
| 011_make_correct_answer_nullable.sql | Schema fix |
| 012_add_visual_content_column.sql | Visual content support |
| 013_create_sorular_table.sql | Sorular table |
| 014_add_performance_indexes.sql | GIN + composite indexes |
| 015_question_bank_stats_triggers.sql | Stats triggers |
| 016_isolate_synthetic_events.sql | Move synthetic events to archive table |
| 016_subjects_student_abilities_daily_plans.sql | Student abilities + daily plans |
| add_*.sql | Various feature tables (chat, API keys, live sessions, etc.) |
| backfill_learning_events.sql | Data backfill |
| create_*.sql | Feature tables (curriculum, social, safety) |
| update_response_log_view.sql | Calibration candidate views |
| temp_gamification.sql | Temporary gamification seed |
