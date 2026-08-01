"""GF-K1: c555a10f4b93 tarafindan dusurulen 7 tabloyu geri getir

Revision ID: gfk1_restore_20260801
Revises: restore_uif_20260801
Create Date: 2026-08-01

NEDEN
-----
1 Agu 2026 canli Golden Flow kosumu (178 test) 12 kirik akis gosterdi; baskin
sebep `UndefinedTable` (konteyner logunda 74 kez). Kok neden:
`c555a10f4b93_sync_db_changes.py` `upgrade()` icinde **145 adet**
`op.execute('DROP TABLE IF EXISTS ... CASCADE')` var. O goc autogenerate ile
uretilmisti ve `alembic/env.py` model modullerinin bir kismini metadata'ya
katmadigi icin alembic bu tablolari "modelde yok, fazlalik" saydi.
(Ayni sinif `#461`'de `user_item_fsrs` icin kapatilmisti; bu onun devami.)

GECISLI KAPANIS: 6 DEGIL 7 TABLO
---------------------------------
Golden Flow log'u 6 tablo gosteriyordu, ama `appointments.availability_slot_id`
-> `teacher_availability.id` FK'si var ve O TABLO DA yoktu. FK kapanisi
olculunce olusturulmasi gereken tablo sayisi 7 cikti. Sira asagida bagimlilik
sirasidir; degistirilirse FK hatasi verir.

    reasoning_cache        (FK yok)
    video_watch_sessions   -> users
    emotional_states       -> users
    teacher_availability   -> teacher_pool_profiles
    video_notes            -> users, video_watch_sessions
    live_sessions          -> users, teacher_profiles
    appointments           -> users, teacher_pool_profiles, teacher_availability

DDL KAYNAGI
-----------
Elle yazilmadi: ORM modellerinden `alembic.autogenerate.render_python_code`
ile uretildi, yani kodun BUGUN bekledigi sema. Kaynak modeller:
models/video_analytics.py · models/diary.py · models/teacher_pool.py ·
models/live_session.py · models/reasoning_models.py

ENUM NOTU (CLAUDE.md sert kurali)
----------------------------------
Sekiz PG enum tipi (dayofweek, timeslotstatus, sessiontype, sessionstatus,
platformtype, appointmenttype, subjectexpertise, appointmentstatus) canlida
ZATEN VAR — `DROP TABLE` enum tipini dusurmez. Duz `sa.Enum` kullanmak
`CREATE TYPE` deneyip "type already exists" ile patlardi. Bu yuzden hepsi
`postgresql.ENUM(..., create_type=False)`.

RLS
---
Bu yedi tabloda `organization_id` kolonu YOK; 79-tablo RLS deseni uygulanamaz.
Kapsam disi birakildi — politika ICAT EDILMEDI (`#461` ile ayni karar).

VERI
----
Tablolar BOS gelir. Dusen veri bu goc ile GERI GELMEZ.

DOGRULAMA
---------
tests/integration/test_gf_k1_tablo_restore.py — varlik + ORM kolon esitligi
(tablo var ama kolon eksik olursa uc yine 500 verir; GF106 vakasi).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "gfk1_restore_20260801"
down_revision = "restore_uif_20260801"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('reasoning_cache',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('problem_hash', sa.String(length=64), nullable=False),
    sa.Column('problem_embedding', postgresql.ARRAY(sa.Float()), nullable=True),
    sa.Column('problem_text', sa.Text(), nullable=False),
    sa.Column('reasoning_data', sa.JSON(), nullable=False, comment='Full reasoning result'),
    sa.Column('provider', sa.String(length=50), nullable=True),
    sa.Column('hit_count', sa.Integer(), nullable=True, comment='Number of cache hits'),
    sa.Column('last_hit', sa.DateTime(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('was_verified', sa.Boolean(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('video_watch_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('video_id', sa.String(length=100), nullable=False),
    sa.Column('video_source', sa.String(length=20), nullable=False),
    sa.Column('watch_duration', sa.Integer(), nullable=True),
    sa.Column('video_duration', sa.Integer(), nullable=False),
    sa.Column('completion_percentage', sa.Float(), nullable=True),
    sa.Column('last_position', sa.Integer(), nullable=True),
    sa.Column('watched_segments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('pause_count', sa.Integer(), nullable=True),
    sa.Column('seek_count', sa.Integer(), nullable=True),
    sa.Column('playback_speed', sa.Float(), nullable=True),
    sa.Column('dropped_at', sa.Integer(), nullable=True),
    sa.Column('is_completed', sa.Boolean(), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('emotional_states',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('confidence_level', sa.Integer(), nullable=False),
    sa.Column('frustration_score', sa.Float(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('error_count', sa.Integer(), nullable=True),
    sa.Column('flow_state', sa.Boolean(), nullable=True),
    sa.Column('productivity_score', sa.Float(), nullable=True),
    sa.Column('tasks_completed', sa.Integer(), nullable=True),
    sa.Column('trigger_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('task_type', sa.String(length=100), nullable=True),
    sa.Column('self_awareness_score', sa.Float(), nullable=True),
    sa.Column('predicted_state', sa.String(length=50), nullable=True),
    sa.Column('actual_state', sa.String(length=50), nullable=True),
    sa.Column('context_notes', sa.Text(), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('teacher_availability',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('teacher_id', sa.String(), nullable=False),
    sa.Column('day_of_week', postgresql.ENUM('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', name='dayofweek', create_type=False), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('specific_date', sa.Date(), nullable=True),
    sa.Column('valid_from', sa.Date(), nullable=True),
    sa.Column('valid_until', sa.Date(), nullable=True),
    sa.Column('status', postgresql.ENUM('AVAILABLE', 'BOOKED', 'BLOCKED', name='timeslotstatus', create_type=False), nullable=True),
    sa.Column('max_students', sa.Integer(), nullable=True),
    sa.Column('current_bookings', sa.Integer(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_recurring', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['teacher_id'], ['teacher_pool_profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('video_notes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('video_id', sa.String(length=100), nullable=False),
    sa.Column('video_source', sa.String(length=20), nullable=False),
    sa.Column('session_id', sa.String(), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.Integer(), nullable=False),
    sa.Column('is_important', sa.Boolean(), nullable=True),
    sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('video_caption', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['video_watch_sessions.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('live_sessions',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('session_type', postgresql.ENUM('ONE_ON_ONE', 'GROUP_SESSION', 'WEBINAR', 'STUDY_GROUP', name='sessiontype', create_type=False), nullable=True),
    sa.Column('host_id', sa.String(), nullable=False),
    sa.Column('teacher_id', sa.String(), nullable=True),
    sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=True),
    sa.Column('status', postgresql.ENUM('SCHEDULED', 'LIVE', 'ENDED', 'CANCELLED', name='sessionstatus', create_type=False), nullable=True),
    sa.Column('platform', postgresql.ENUM('ZOOM', 'GOOGLE_MEET', 'JITSI', 'CUSTOM', name='platformtype', create_type=False), nullable=True),
    sa.Column('meeting_id', sa.String(length=100), nullable=True),
    sa.Column('meeting_password', sa.String(length=100), nullable=True),
    sa.Column('meeting_url', sa.String(length=500), nullable=True),
    sa.Column('join_url', sa.String(length=500), nullable=True),
    sa.Column('host_url', sa.String(length=500), nullable=True),
    sa.Column('zoom_meeting_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('meet_event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('max_participants', sa.Integer(), nullable=True),
    sa.Column('current_participants', sa.Integer(), nullable=True),
    sa.Column('allow_screen_share', sa.Boolean(), nullable=True),
    sa.Column('allow_whiteboard', sa.Boolean(), nullable=True),
    sa.Column('allow_recording', sa.Boolean(), nullable=True),
    sa.Column('allow_chat', sa.Boolean(), nullable=True),
    sa.Column('is_recorded', sa.Boolean(), nullable=True),
    sa.Column('auto_record', sa.Boolean(), nullable=True),
    sa.Column('enable_waiting_room', sa.Boolean(), nullable=True),
    sa.Column('require_password', sa.Boolean(), nullable=True),
    sa.Column('enable_mute_on_join', sa.Boolean(), nullable=True),
    sa.Column('subject', sa.String(length=100), nullable=True),
    sa.Column('topics', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['host_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['teacher_id'], ['teacher_profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('appointments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('teacher_id', sa.String(), nullable=False),
    sa.Column('student_id', sa.String(), nullable=False),
    sa.Column('availability_slot_id', sa.String(), nullable=True),
    sa.Column('appointment_type', postgresql.ENUM('ONE_ON_ONE', 'GROUP_SESSION', 'QUESTION_ANSWER', 'EXAM_PREP', name='appointmenttype', create_type=False), nullable=True),
    sa.Column('subject', postgresql.ENUM('MATHEMATICS', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY', 'TURKISH', 'HISTORY', 'GEOGRAPHY', 'ENGLISH', 'PHILOSOPHY', 'LITERATURE', 'GEOMETRY', name='subjectexpertise', create_type=False), nullable=True),
    sa.Column('scheduled_date', sa.Date(), nullable=False),
    sa.Column('start_time', sa.Time(), nullable=False),
    sa.Column('end_time', sa.Time(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=True),
    sa.Column('status', postgresql.ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW', name='appointmentstatus', create_type=False), nullable=True),
    sa.Column('topic', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('student_notes', sa.Text(), nullable=True),
    sa.Column('teacher_notes', sa.Text(), nullable=True),
    sa.Column('preparation_materials', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confirmed_by', sa.String(), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancelled_by', sa.String(), nullable=True),
    sa.Column('cancellation_reason', sa.Text(), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('session_summary', sa.Text(), nullable=True),
    sa.Column('homework_assigned', sa.Text(), nullable=True),
    sa.Column('meeting_url', sa.String(length=500), nullable=True),
    sa.Column('meeting_id', sa.String(length=100), nullable=True),
    sa.Column('meeting_password', sa.String(length=100), nullable=True),
    sa.Column('reminder_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reminder_count', sa.Integer(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('currency', sa.String(length=10), nullable=True),
    sa.Column('payment_status', sa.String(length=50), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['availability_slot_id'], ['teacher_availability.id'], ),
    sa.ForeignKeyConstraint(['cancelled_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['confirmed_by'], ['users.id'], ),
    sa.ForeignKeyConstraint(['student_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['teacher_id'], ['teacher_pool_profiles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table("appointments")
    op.drop_table("live_sessions")
    op.drop_table("video_notes")
    op.drop_table("teacher_availability")
    op.drop_table("emotional_states")
    op.drop_table("video_watch_sessions")
    op.drop_table("reasoning_cache")
