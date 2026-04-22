# Pilot state — Autopilot Debt #6 Round 2

**Repo:** `C:\Users\husey\kiro2`  
**Round 1 referans (dokunulmadı):** `backend/_pilots/20260425_autopilot_debt_6_review_state.md`, `.cursor/plans/20260425_autopilot_debt_6_review_RESULT.md`

---

## Round 2 — A1.a Deploy Fix + A2/A3/A4 Teşhis (2026-04-22)

### A1.a — DEPLOY FIX (ham çıktı)

**Komutlar (sırayla):** `docker cp` → `find …pyc` → `docker restart` → `Start-Sleep -Seconds 8` → `grep -n -A5` → `curl -s /health`

**Birleşik ilk çalıştırma (PowerShell; çıkış kodu 1):**

```
kiro2-backend
322:def require_role(*roles: str) -> AuthorizationDependency:
323-    """FastAPI dependency: kullanıcının verilen rollerden birine sahip olmasını zorunlu kılar.
324-
325-    RBAC rol id'leri küçük harf (örn. ``admin``, ``teacher``). ``"ADMIN"`` gibi
326-    büyük harf değerler otomatik küçültülür.
327-    """
000
```

**Not (ham çıktıya ek):** `grep -A5` gövdeyi kesiyor; hemen ardından konteynerde tam gövde:

```
docker exec kiro2-backend grep -n -A12 "^def require_role" /app/core/auth_dependencies.py
```

```
322:def require_role(*roles: str) -> AuthorizationDependency:
323-    """FastAPI dependency: kullanıcının verilen rollerden birine sahip olmasını zorunlu kılar.
324-
325-    RBAC rol id'leri küçük harf (örn. ``admin``, ``teacher``). ``"ADMIN"`` gibi
326-    büyük harf değerler otomatik küçültülür.
327-    """
328-    normalized = [str(r).strip().lower() for r in roles if str(r).strip()]
329-    return AuthorizationDependency(required_roles=normalized or ["admin"])
330-
331-
332-def require_permission(*permissions: str) -> AuthorizationDependency:
333-    """FastAPI dependency: verilen izinlerden en az birini zorunlu kılar."""
334-    perms = [str(p).strip() for p in permissions if str(p).strip()]
```

**İlk `curl`:** `HTTP_CODE:000` (restart sonrası servis henüz hazır değildi). **Sonraki teyit** (`Start-Sleep` sonrası): `GET http://127.0.0.1:8000/health` → **200**, JSON gövde `health_status":"healthy"`.

**Plan teyidi — `grep -n -A5` + `curl -s` (stabil window, ham):**

```
---
322:def require_role(*roles: str) -> AuthorizationDependency:
323-    """FastAPI dependency: kullanıcının verilen rollerden birine sahip olmasını zorunlu kılar.
324-
325-    RBAC rol id'leri küçük harf (örn. ``admin``, ``teacher``). ``"ADMIN"`` gibi
326-    büyük harf değerler otomatik küçültülür.
327-    """
---
{"status":"success","health_status":"healthy","service":"Türkiye Üniversite Sınavları Hazırlık Platformu","version":"1.0.0","environment":"development","timestamp":"2026-04-22T18:43:25.069129+00:00","response_time_ms":111.39,"components":[...],"summary":{"total":5,"healthy":5,"unhealthy":0,"critical_healthy":1}}
```

---

### A2 — ALEMBIC DRIFT TEŞHİSİ (ham çıktı)

**Repo migration dosya adları (`Select-String`):**

```

20260412_student_reviews_drop_recreate.py
20260420_create_offline_sync_packages.py
20260422_diary_drift_recovery.py
```

**`docker exec kiro2-backend alembic current`:**

```
[ALEMBIC] Using database: postgresql:***@host.docker.internal:5434/kiro2
diary_drift_recovery_20260422 (head)
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

**`docker exec kiro2-backend alembic heads`:**

```
diary_drift_recovery_20260422 (head)
```

**`docker exec kiro2-backend alembic history --verbose | Select-Object -First 30`:**

```
Rev: diary_drift_recovery_20260422 (head)
Parent: offline_sync_pkg_20260420
Path: /app/alembic/versions/20260422_diary_drift_recovery.py

    Idempotent diary / learning journal schema for fresh DB installs.
    
    Revision ID: diary_drift_recovery_20260422
    Revises: offline_sync_pkg_20260420
    
    Drift: diary tablolari gelistirme DB'de vardi; Alembic grafiginde yoktu
    (_archive/20260119_add_diary_tables.py.disabled — ayrica eski UUID user_id).
    
    Bu revision canli VARCHAR + PostgreSQL enum semasini models/diary.py ile hizalar.
    Mevcut kurulumlarda CREATE IF NOT EXISTS ile no-op; taze DB'de tablolar olusur.
    
    Downgrade: tablolari ve enum tiplerini kaldirir (veri kaybi).

Rev: offline_sync_pkg_20260420
Parent: student_review_drift_001
Path: /app/alembic/versions/20260420_create_offline_sync_packages.py

    Create offline_sync_packages table
    
    Revision ID: offline_sync_pkg_20260420 (<=32 chars for alembic_version)
    Revises: student_review_drift_001
    Create Date: 2026-04-20

Rev: student_review_drift_001
Parent: osb_access_001
Path: /app/alembic/versions/20260412_student_reviews_drop_recreate.py
```

---

### A3 — SEED USER + DB BAĞLANTI (ham çıktı)

**`docker exec kiro2-backend env | Select-String -Pattern "DB_|DATABASE_|POSTGRES"`:**

```

DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2
```

**`Select-String -Path C:\Users\husey\kiro2\.env.mvp -Pattern "DB_|DATABASE_|POSTGRES"`:**

```

.env.mvp:2:# Native Windows PostgreSQL (port 5434) + Redis (port 6379)
.env.mvp:5:DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2
.env.mvp:7:DB_POOL_SIZE=20
.env.mvp:8:DB_MAX_OVERFLOW=30
.env.mvp:17:# NOT: production config.py 'postgres' sifresi + localhost CORS redediyor.
```

**DB_ADI (ENV):** URL yolundan **`kiro2`**. Host:**`host.docker.internal:5434`**.

**`docker exec kiro2_postgres psql -U postgres -d kiro2` (plan metnindeki kalıp — konteyner içi varsayılan sunucu):**

```
psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  database "kiro2" does not exist
```

**Aynı komut `\d users` için de aynı hata** (veritabanı `kiro2_postgres` konteynerinde yok; Round 1’deki `kiro2_db` ayrı instance).

**Gerçek DSN üzerinde sorgu:** `docker run --rm postgres:16-alpine psql "postgresql://postgres:postgres@host.docker.internal:5434/kiro2" -c "..."`

**`\d users` (tam ham çıktı):**

```
                              Table "public.users"
       Column        |           Type           | Collation | Nullable | Default 
---------------------+--------------------------+-----------+----------+---------
 id                  | character varying        |           | not null | 
 email               | character varying(255)   |           | not null | 
 username            | character varying(100)   |           | not null | 
 password_hash       | character varying(255)   |           | not null | 
 secret_2fa          | character varying(32)    |           |          | 
 is_2fa_enabled      | boolean                  |           | not null | false
 backup_codes_hashed | json                     |           |          | 
 is_premium          | boolean                  |           | not null | false
 premium_expires_at  | timestamp with time zone |           |          | 
 first_name          | character varying(100)   |           | not null | 
 last_name           | character varying(100)   |           | not null | 
 role                | userrole                 |           | not null | 
 phone               | character varying(20)    |           |          | 
 birth_date          | date                     |           |          | 
 total_xp            | integer                  |           | not null | 0
 level               | integer                  |           | not null | 1
 last_level_up_at    | timestamp with time zone |           |          | 
 is_active           | boolean                  |           | not null | true
 is_verified         | boolean                  |           | not null | false
 created_at          | timestamp with time zone |           | not null | now()
 updated_at          | timestamp with time zone |           | not null | now()
 last_login          | timestamp with time zone |           |          | 
 elo_rating          | integer                  |           | not null | 1000
 is_parent           | boolean                  |           | not null | false
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)
    "idx_user_created_at" btree (created_at)
    "idx_user_email" btree (email)
    "idx_user_role" btree (role)
    "idx_user_username" btree (username)
    "idx_users_premium" btree (email, username) WHERE is_premium = true
    "ix_users_email" UNIQUE, btree (email)
    "ix_users_username" UNIQUE, btree (username)
Check constraints:
    "check_birth_date" CHECK (birth_date <= CURRENT_DATE AND birth_date >= '1950-01-01'::date)
Referenced by:
    TABLE "api_keys" CONSTRAINT "api_keys_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "appointment_reminders" CONSTRAINT "appointment_reminders_recipient_id_fkey" FOREIGN KEY (recipient_id) REFERENCES users(id)
    TABLE "appointments" CONSTRAINT "appointments_cancelled_by_fkey" FOREIGN KEY (cancelled_by) REFERENCES users(id)
    TABLE "appointments" CONSTRAINT "appointments_confirmed_by_fkey" FOREIGN KEY (confirmed_by) REFERENCES users(id)
    TABLE "appointments" CONSTRAINT "appointments_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "audit_logs" CONSTRAINT "audit_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "bkt_states" CONSTRAINT "bkt_states_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "chat_analytics" CONSTRAINT "chat_analytics_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "class_reports" CONSTRAINT "class_reports_teacher_user_id_fkey" FOREIGN KEY (teacher_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "coppa_parental_consents" CONSTRAINT "coppa_parental_consents_child_id_fkey" FOREIGN KEY (child_id) REFERENCES users(id)
    TABLE "coppa_parental_consents" CONSTRAINT "coppa_parental_consents_parent_id_fkey" FOREIGN KEY (parent_id) REFERENCES users(id)
    TABLE "daily_quests" CONSTRAINT "daily_quests_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "data_retention_policies" CONSTRAINT "data_retention_policies_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id)
    TABLE "diary_entries" CONSTRAINT "diary_entries_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "diary_exports" CONSTRAINT "diary_exports_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "duels" CONSTRAINT "duels_player1_id_fkey" FOREIGN KEY (player1_id) REFERENCES users(id)
    TABLE "duels" CONSTRAINT "duels_player2_id_fkey" FOREIGN KEY (player2_id) REFERENCES users(id)
    TABLE "dungeon_progress" CONSTRAINT "dungeon_progress_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "eba_content_collections" CONSTRAINT "eba_content_collections_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    TABLE "eba_video_watches" CONSTRAINT "eba_video_watches_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "eba_videos" CONSTRAINT "eba_videos_moderated_by_fkey" FOREIGN KEY (moderated_by) REFERENCES users(id) ON DELETE CASCADE
    TABLE "educational_record_access_logs" CONSTRAINT "educational_record_access_logs_accessor_id_fkey" FOREIGN KEY (accessor_id) REFERENCES users(id)
    TABLE "educational_record_access_logs" CONSTRAINT "educational_record_access_logs_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "emotional_states" CONSTRAINT "emotional_states_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "ferpa_consents" CONSTRAINT "ferpa_consents_parent_id_fkey" FOREIGN KEY (parent_id) REFERENCES users(id)
    TABLE "ferpa_consents" CONSTRAINT "ferpa_consents_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "file_versions" CONSTRAINT "file_versions_uploaded_by_fkey" FOREIGN KEY (uploaded_by) REFERENCES users(id)
    TABLE "fsrs_cards" CONSTRAINT "fsrs_cards_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "fsrs_reviews" CONSTRAINT "fsrs_reviews_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "fsrs_schedules" CONSTRAINT "fsrs_schedules_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "fsrs_student_profiles" CONSTRAINT "fsrs_student_profiles_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "fsrs_study_sessions" CONSTRAINT "fsrs_study_sessions_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "fsrs_subject_stats" CONSTRAINT "fsrs_subject_stats_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "goals" CONSTRAINT "goals_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "image_uploads" CONSTRAINT "image_uploads_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "insights" CONSTRAINT "insights_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "khan_certificates" CONSTRAINT "khan_certificates_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "khan_oauth_tokens" CONSTRAINT "khan_oauth_tokens_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "khan_user_progress" CONSTRAINT "khan_user_progress_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "kvkk_audit_logs" CONSTRAINT "kvkk_audit_logs_accessed_by_fkey" FOREIGN KEY (accessed_by) REFERENCES users(id)
    TABLE "kvkk_audit_logs" CONSTRAINT "kvkk_audit_logs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "kvkk_consents" CONSTRAINT "kvkk_consents_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "kvkk_data_deletion_requests" CONSTRAINT "kvkk_data_deletion_requests_reviewed_by_fkey" FOREIGN KEY (reviewed_by) REFERENCES users(id)
    TABLE "kvkk_data_deletion_requests" CONSTRAINT "kvkk_data_deletion_requests_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "kvkk_data_export_requests" CONSTRAINT "kvkk_data_export_requests_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "kvkk_privacy_policy_versions" CONSTRAINT "kvkk_privacy_policy_versions_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id)
    TABLE "learning_entries" CONSTRAINT "learning_entries_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "learning_path_student_profiles" CONSTRAINT "learning_path_student_profiles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "live_sessions" CONSTRAINT "live_sessions_host_id_fkey" FOREIGN KEY (host_id) REFERENCES users(id)
    TABLE "manipulative_activities" CONSTRAINT "manipulative_activities_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "manipulative_progress" CONSTRAINT "manipulative_progress_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "moderation_queue" CONSTRAINT "moderation_queue_assigned_to_fkey" FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL
    TABLE "notifications" CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "oba_uyeler" CONSTRAINT "oba_uyeler_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "offline_sync_packages" CONSTRAINT "offline_sync_packages_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "osb_settings" CONSTRAINT "osb_settings_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "parent_approvals" CONSTRAINT "parent_approvals_parent_user_id_fkey" FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "parent_approvals" CONSTRAINT "parent_approvals_student_user_id_fkey" FOREIGN KEY (student_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "parent_child" CONSTRAINT "parent_child_child_id_fkey" FOREIGN KEY (child_id) REFERENCES users(id)
    TABLE "parent_child" CONSTRAINT "parent_child_parent_id_fkey" FOREIGN KEY (parent_id) REFERENCES users(id)
    TABLE "parent_notifications" CONSTRAINT "parent_notifications_child_id_fkey" FOREIGN KEY (child_id) REFERENCES users(id)
    TABLE "parent_notifications" CONSTRAINT "parent_notifications_parent_id_fkey" FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "parent_profiles" CONSTRAINT "parent_profiles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "parent_reports" CONSTRAINT "parent_reports_parent_user_id_fkey" FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "parent_reports" CONSTRAINT "parent_reports_student_user_id_fkey" FOREIGN KEY (student_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "peer_comparisons" CONSTRAINT "peer_comparisons_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "performance_history" CONSTRAINT "performance_history_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "point_transactions" CONSTRAINT "point_transactions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "question_bank" CONSTRAINT "question_bank_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    TABLE "question_bank" CONSTRAINT "question_bank_reviewed_by_fkey" FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE CASCADE
    TABLE "questions" CONSTRAINT "questions_created_by_fkey" FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    TABLE "realm_progress" CONSTRAINT "realm_progress_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "reasoning_sessions" CONSTRAINT "reasoning_sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    TABLE "recording_bookmarks" CONSTRAINT "recording_bookmarks_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "recording_views" CONSTRAINT "recording_views_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "reflections" CONSTRAINT "reflections_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "refresh_tokens" CONSTRAINT "refresh_tokens_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "review_reports" CONSTRAINT "review_reports_reporter_id_fkey" FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "review_reports" CONSTRAINT "review_reports_resolved_by_fkey" FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
    TABLE "review_votes" CONSTRAINT "review_votes_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "room_chat_messages" CONSTRAINT "room_chat_messages_deleted_by_fkey" FOREIGN KEY (deleted_by) REFERENCES users(id)
    TABLE "room_chat_messages" CONSTRAINT "room_chat_messages_pinned_by_fkey" FOREIGN KEY (pinned_by) REFERENCES users(id)
    TABLE "room_chat_messages" CONSTRAINT "room_chat_messages_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "room_invitations" CONSTRAINT "room_invitations_invitee_id_fkey" FOREIGN KEY (invitee_id) REFERENCES users(id)
    TABLE "room_invitations" CONSTRAINT "room_invitations_inviter_id_fkey" FOREIGN KEY (inviter_id) REFERENCES users(id)
    TABLE "room_members" CONSTRAINT "room_members_invited_by_fkey" FOREIGN KEY (invited_by) REFERENCES users(id)
    TABLE "room_members" CONSTRAINT "room_members_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "screen_shares" CONSTRAINT "screen_shares_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "session_chat_messages" CONSTRAINT "session_chat_messages_deleted_by_fkey" FOREIGN KEY (deleted_by) REFERENCES users(id)
    TABLE "session_chat_messages" CONSTRAINT "session_chat_messages_recipient_id_fkey" FOREIGN KEY (recipient_id) REFERENCES users(id)
    TABLE "session_chat_messages" CONSTRAINT "session_chat_messages_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "session_participants" CONSTRAINT "session_participants_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "sessions" CONSTRAINT "sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "shared_files" CONSTRAINT "shared_files_deleted_by_fkey" FOREIGN KEY (deleted_by) REFERENCES users(id)
    TABLE "shared_files" CONSTRAINT "shared_files_uploaded_by_fkey" FOREIGN KEY (uploaded_by) REFERENCES users(id)
    TABLE "streaks" CONSTRAINT "streaks_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "student_abilities" CONSTRAINT "student_abilities_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "student_goals" CONSTRAINT "student_goals_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "student_grades" CONSTRAINT "student_grades_student_user_id_fkey" FOREIGN KEY (student_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "student_grades" CONSTRAINT "student_grades_teacher_user_id_fkey" FOREIGN KEY (teacher_user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "student_learning_profiles" CONSTRAINT "student_learning_profiles_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "student_nano_skill_mastery" CONSTRAINT "student_nano_skill_mastery_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "student_profiles" CONSTRAINT "student_profiles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "student_question_responses" CONSTRAINT "student_question_responses_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "student_reviews" CONSTRAINT "student_reviews_moderated_by_fkey" FOREIGN KEY (moderated_by) REFERENCES users(id) ON DELETE SET NULL
    TABLE "student_reviews" CONSTRAINT "student_reviews_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "study_plans" CONSTRAINT "study_plans_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "study_rooms" CONSTRAINT "study_rooms_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES users(id)
    TABLE "teacher_certifications" CONSTRAINT "teacher_certifications_verified_by_fkey" FOREIGN KEY (verified_by) REFERENCES users(id)
    TABLE "teacher_pool_profiles" CONSTRAINT "teacher_pool_profiles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "teacher_pool_profiles" CONSTRAINT "teacher_pool_profiles_verified_by_fkey" FOREIGN KEY (verified_by) REFERENCES users(id)
    TABLE "teacher_profiles" CONSTRAINT "teacher_profiles_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "teacher_reviews" CONSTRAINT "teacher_reviews_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "user_achievements" CONSTRAINT "user_achievements_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "user_badges" CONSTRAINT "user_badges_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "user_university_preferences" CONSTRAINT "user_university_preferences_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "video_analytics_summary" CONSTRAINT "video_analytics_summary_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "video_analytics" CONSTRAINT "video_analytics_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "video_bookmarks" CONSTRAINT "video_bookmarks_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "video_completion_milestones" CONSTRAINT "video_completion_milestones_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "video_notes" CONSTRAINT "video_notes_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "video_solutions" CONSTRAINT "video_solutions_approved_by_fkey" FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    TABLE "video_solutions" CONSTRAINT "video_solutions_uploaded_by_fkey" FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
    TABLE "video_transcripts" CONSTRAINT "video_transcripts_manually_edited_by_fkey" FOREIGN KEY (manually_edited_by) REFERENCES users(id) ON DELETE SET NULL
    TABLE "video_transcripts" CONSTRAINT "video_transcripts_verified_by_fkey" FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
    TABLE "video_watch_sessions" CONSTRAINT "video_watch_sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "weekly_progress" CONSTRAINT "weekly_progress_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "weekly_reports" CONSTRAINT "weekly_reports_child_id_fkey" FOREIGN KEY (child_id) REFERENCES users(id) ON DELETE CASCADE
    TABLE "whiteboard_equations" CONSTRAINT "whiteboard_equations_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "whiteboard_strokes" CONSTRAINT "whiteboard_strokes_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "xp_transactions" CONSTRAINT "xp_transactions_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
    TABLE "zpd_history" CONSTRAINT "zpd_history_student_id_fkey" FOREIGN KEY (student_id) REFERENCES users(id)
```

**`SELECT DISTINCT role FROM users;`:**

```
  role   
---------
 TEACHER
 STUDENT
 ADMIN
 PARENT
(4 rows)
```

**Seed sorgusu (placeholder küçük harf yerine DISTINCT’teki gerçek enum değerleri: `STUDENT`, `TEACHER`, `PARENT`):**

```
SELECT id, email, role FROM users WHERE role IN ('STUDENT', 'TEACHER', 'PARENT') AND (email LIKE '%test%' OR email LIKE '%seed%' OR email LIKE '%dev%') ORDER BY role LIMIT 12;
```

```
                  id                  |         email         |  role   
--------------------------------------+-----------------------+---------
 e5675924-0f81-4c14-801c-eef5b4cbbf0b | beta026@kiro2test.com | STUDENT
 f52cb3ba-9f76-4996-a350-61b5bf641f7d | beta027@kiro2test.com | STUDENT
 58b06c00-7be4-4285-83dc-e12adde0f08f | beta001@kiro2test.com | STUDENT
 4e43d112-d2f9-48a1-aec6-fa002b233236 | beta002@kiro2test.com | STUDENT
 a5644a99-fa08-4792-b24d-755bd816ddda | beta003@kiro2test.com | STUDENT
 002c3e02-21f9-4f72-9ba3-f753e44b4dce | beta004@kiro2test.com | STUDENT
 a44cc7d0-9444-4bbb-b8db-113b5e75d5c5 | beta005@kiro2test.com | STUDENT
 8b14b2ec-d054-4f36-b253-f4b515e6d0b7 | beta006@kiro2test.com | STUDENT
 cc2dc904-ad61-4789-a474-1fbed06609f5 | beta007@kiro2test.com | STUDENT
 9aa86d84-ffa8-4d44-87c8-c7deb535aa1d | beta008@kiro2test.com | STUDENT
 a86c9c0b-12db-422b-a8f3-477bb5801a4d | beta009@kiro2test.com | STUDENT
 41411c25-5c85-4470-a6ac-ac31c60ce732 | beta025@kiro2test.com | STUDENT
(12 rows)
```

**Login / token:** yapılmadı (plan notu).

---

### A4 — 0.e KAPSAM REVİZYONU (ham çıktı)

**`docker exec kiro2-backend bash -c "grep -rn 'require_student\|require_teacher\|require_parent\|required_roles=\|AuthorizationDependency(\|Depends(require_role' /app --include='*.py' | head -80"`:**

```
/app/api/analytics.py:282:    _: None = Depends(require_role("ADMIN")),
/app/api/eba_routes.py:556:    _: None = Depends(require_role("ADMIN")),
/app/api/eba_routes.py:591:    _: None = Depends(require_role("ADMIN")),
/app/api/eba_routes.py:622:    _: None = Depends(require_role("ADMIN")),
/app/api/elasticsearch.py:316:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:97:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:125:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:155:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:183:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:221:async def get_prometheus_metrics(_: None = Depends(require_role("ADMIN"))) -> str:
/app/api/monitoring.py:244:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:337:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:371:async def stop_monitoring(_: None = Depends(require_role("ADMIN"))) -> dict[str, Any]:
/app/api/monitoring.py:398:    _: None = Depends(require_role("ADMIN")),
/app/api/monitoring.py:439:    _: None = Depends(require_role("ADMIN")),
/app/api/auth.py:28:from core.authorization import require_student_owner_or_privileged
/app/api/auth.py:1554:    require_student_owner_or_privileged(mevcut_kullanici, profil.kullanici_id)
/app/api/production_monitoring.py:28:async def get_quality_stats(_: None = Depends(require_role("ADMIN"))):
/app/api/production_monitoring.py:53:    last_n: Optional[int] = None, _: None = Depends(require_role("ADMIN"))
/app/api/production_monitoring.py:130:    limit: int = 10, _: None = Depends(require_role("ADMIN"))
/app/api/v1/content_recommendation.py:24:get_current_admin_user = AuthorizationDependency(required_roles=["admin", "super_admin"])
/app/api/v1/duplicate_detection.py:26:get_current_admin_user = AuthorizationDependency(required_roles=["admin", "super_admin"])
/app/api/sequential_reasoning_api.py:22:get_current_admin_user = AuthorizationDependency(
/app/api/sequential_reasoning_api.py:23:    required_roles=["admin", "super_admin"]
/app/tests/unit/test_api_batch1.py:550:                    "core.authorization.require_student_owner_or_privileged"
/app/tests/unit/test_auth_coverage.py:1682:                "require_student_owner_or_privileged",
/app/core/auth_dependencies.py:183:                required_roles=self.required_roles,
/app/core/auth_dependencies.py:234:require_admin = AuthorizationDependency(required_roles=["admin", "super_admin"])
/app/core/auth_dependencies.py:235:require_teacher = AuthorizationDependency(
/app/core/auth_dependencies.py:236:    required_roles=["teacher", "admin", "super_admin"]
/app/core/auth_dependencies.py:238:require_student = AuthorizationDependency(
/app/core/auth_dependencies.py:239:    required_roles=["student", "teacher", "admin", "super_admin"]
/app/core/auth_dependencies.py:243:require_read_permission = AuthorizationDependency(required_permissions=["read"])
/app/core/auth_dependencies.py:244:require_write_permission = AuthorizationDependency(required_permissions=["write"])
/app/core/auth_dependencies.py:245:require_delete_permission = AuthorizationDependency(required_permissions=["delete"])
/app/core/auth_dependencies.py:246:require_manage_users = AuthorizationDependency(required_permissions=["manage_users"])
/app/core/auth_dependencies.py:247:require_manage_content = AuthorizationDependency(required_permissions=["manage_content"])
/app/core/auth_dependencies.py:250:require_view_analytics = AuthorizationDependency(
/app/core/auth_dependencies.py:258:    return AuthorizationDependency(
/app/core/auth_dependencies.py:267:    return AuthorizationDependency(
/app/core/auth_dependencies.py:274:    return AuthorizationDependency(
/app/core/auth_dependencies.py:281:    return AuthorizationDependency(
/app/core/auth_dependencies.py:329:    return AuthorizationDependency(required_roles=normalized or ["admin"])
/app/core/auth_dependencies.py:335:    return AuthorizationDependency(required_permissions=perms or ["read"])
/app/core/auth_dependencies.py:359:        required_roles=roles or [],
/app/core/learning_path_auth.py:214:            _: bool = Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))
/app/core/authorization.py:79:def require_teacher_or_admin(current_user: Kullanici) -> None:
/app/core/authorization.py:92:def require_student_owner_or_privileged(
```

**`docker exec kiro2-backend bash -c "grep -rn 'current_user.role\|user.role ==' /app --include='*.py' | head -40"`:**

```
/app/api/math_solution_steps.py:29:    if current_user.role in (
/app/api/zpd_maarif.py:37:    if current_user.role in (UserRole.ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN):
/app/api/zpd_maarif.py:146:    if request.ogrenci_id != str(current_user.id) and current_user.role.value not in (
/app/api/quality_gates_api.py:450:    user_role = current_user.role.value
/app/api/quality_gates_api.py:497:    user_role = current_user.role.value
/app/api/enhanced_user_management_api.py:83:    if current_user.role in ["admin", "super_admin"]:
/app/api/enhanced_user_management_api.py:107:    if (current_user.role or "").lower() not in ["admin", "super_admin"]:
/app/api/enhanced_user_management_api.py:111:            user_role=current_user.role,
/app/api/enhanced_user_management_api.py:654:                "requester_role": current_user.role,
/app/api/config_routes.py:26:    if current_user.role in (
/app/api/exam_performance.py:657:        if current_user.id != student_id and current_user.role.value != "admin":
/app/api/video_solution.py:419:    if video.uploaded_by != current_user.id and current_user.role.value != "admin":
/app/api/video_solution.py:442:    if current_user.role.value != "admin":
/app/api/video_solution.py:538:        if video.uploaded_by != current_user.id and current_user.role.value != "admin":
/app/api/content_management.py:33:    if current_user.role not in ["admin", "teacher"]:
/app/api/elasticsearch.py:281:        if str(current_user.id) != user_id and current_user.role.value != "admin":
/app/api/question_bank_v2_routes.py:73:    if current_user.role in (UserRole.ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN):
/app/api/khan_routes.py:625:    if current_user.role != UserRole.ADMIN:
/app/api/cultural_adaptation_api.py:87:            current_user.role.value not in ["admin", "teacher"]
/app/api/cultural_adaptation_api.py:138:            current_user.role.value not in ["admin", "teacher"]
/app/api/cultural_adaptation_api.py:353:        if current_user.role.value != "admin":
/app/api/encryption_management.py:48:    if current_user.role != UserRole.ADMIN:
/app/api/v1/content_recommendation.py:343:    if str(current_user.id) != user_id and current_user.role.value not in (
/app/api/admin.py:42:    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
/app/api/content_api.py:179:        and current_user.role.value != "admin"
/app/api/content_api.py:216:        and current_user.role.value != "admin"
/app/api/bionic_reading.py:267:        if current_user.role.value != "admin":
/app/api/bionic_reading.py:300:        user_role = current_user.role.value
/app/api/bionic_reading.py:309:        target_user_id = None if (clear_all and user_role == "admin") else user_id
/app/api/audit_logs_api.py:64:    if current_user.role != UserRole.ADMIN:
/app/api/berturk_api.py:238:            current_user.role not in ["teacher", "admin"]
/app/api/berturk_api.py:515:        if current_user.role != UserRole.ADMIN:
/app/api/berturk_api.py:549:        if current_user.role != UserRole.ADMIN:
/app/api/rate_limit_api.py:107:        if user_role == "admin" or user_role == "superadmin":
/app/api/rate_limit_api.py:109:        elif user_role == "premium" or getattr(current_user, "is_premium", False):
/app/api/rate_limit_api.py:156:        if user_role == "admin" or user_role == "superadmin":
/app/api/rate_limit_api.py:158:        elif user_role == "premium" or getattr(current_user, "is_premium", False):
/app/api/parent.py:36:    if current_user.role != UserRole.PARENT:
/app/api/parent.py:69:    if current_user.role != UserRole.PARENT:
/app/api/parent.py:99:    if current_user.role != UserRole.PARENT:
```

**`Depends(require_role())` argümansız (ek kontrol):** `grep` eşleşmesi yok (boş çıktı).

---

## Özet

- **A1.a:** D-12 giderildi. Konteynerde `require_role` gövdesi `return AuthorizationDependency(required_roles=normalized or ["admin"])`. İlk health isteği restart sonrası **000**; kısa süre sonra **200** ve `healthy`. `grep -A5` teyitte gövdeyi kesiyor; tam gövde için `-A12` kullanıldı.
- **A2:** Repoda `20260422_diary_drift_recovery.py` var. `alembic current` ve `alembic heads` ikisi de **`diary_drift_recovery_20260422 (head)`** — **çift head yok**. Round 1’deki “revision bulunamadı” durumu bu ortamda **görülmedi** (konteyner `/app` ile uyumlu; DB `host.docker.internal:5434/kiro2`). **Fix önerisi yok** — karar Hüseyin’e.
- **A3:** Backend gerçek DB: **`postgresql://…@host.docker.internal:5434/kiro2`**. `kiro2_postgres` konteynerine `-d kiro2` ile bağlanmak **yanlış hedef** (içeride `kiro2` yok). **`users.role`** PostgreSQL enum’u: **`STUDENT`, `TEACHER`, `ADMIN`, `PARENT` — büyük harf etiketler** (10_BRIEFING §Kritik Kolon Adları “BÜYÜK HARF” ifadesi bu örnekle **uyumlu**; auth kodu ise `require_role` içinde `.lower()` ile normalize ediyor — briefing’de çelişen kısım “ezber küçük harf DB” iddiası olurdu, burada DB **büyük**). Test e-postalı seed benzeri kullanıcılar **STUDENT** için mevcut; sorgu `TEACHER`/`PARENT` satırı bu `LIMIT 12` diliminde görünmedi (yalnızca STUDENT sıralı geldi).
- **A4:** **A4.i baskın:** `require_student` ve `require_teacher` doğrudan `AuthorizationDependency(required_roles=[...])` fabrikaları; çok sayıda endpoint `Depends(require_role("ADMIN"))`. **`require_parent`** diye ayrı fabrika yok; **PARENT** için `parent.py` içinde **`UserRole.PARENT` runtime kontrolü (A4.iii)**. `learning_path_auth.py` içinde `Depends(require_role(UserRole.TEACHER, UserRole.ADMIN))` özel örnek. Kod tarafında `required_roles` listeleri **küçük harf** string; DB enum **büyük harf** — karşılaştırma katmanında normalize edildiği varsayımı A1 ile tutarlı; matris için endpoint seçimi **`Depends(require_role("STUDENT"))` dar grep’ten** çıkıp **`require_student` / `require_teacher` / `parent` route** ve runtime check’lere genişletilmeli. **3 rol × ≥3 endpoint** matrisi bu genişletilmiş envanterle **kurulabilir** görünüyor; dar 0.e grep ile **çelişki** devam eder. **Saf A4.ii değil** (üç rolün tamamı tek desende homojen değil). **Önerilen etiket:** **A4.i (+ PARENT için A4.iii tamamlayıcı)**.

---

## Plan §YASAK Listesi — ihlal kontrolü (20260422 planı)

| Madde | İhlal? |
|--------|--------|
| `git commit` / `push` / `cherry-pick` / `checkout` | **Hayır** |
| `alembic upgrade` | **Hayır** |
| Workspace kaynak kodu değişikliği | **Hayır** (`docker cp` yalnızca konteyner) |
| `RESULT` dosyasına dokunma | **Hayır** |
| A5 cherry-pick uygulama | **Hayır** |
| Round 1 `20260425_...state.md` değişikliği | **Hayır** |

**Sonuç:** İhlal yok.
