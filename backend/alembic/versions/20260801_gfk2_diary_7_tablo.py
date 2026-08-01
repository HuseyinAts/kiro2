"""GF-K2: diary modulunun 7 tablosunu geri getir

Revision ID: gfk2_diary_20260801
Revises: gfk1_restore_20260801
Create Date: 2026-08-01

NEDEN
-----
`gf26 diary/goals create` 500 veriyordu: `relation "goals" does not exist`.
Bu, `gfk1_restore_20260801` ile kapatilan sinifin KACAN KARDESI — ilk turda
gorunmemisti cunku ayni istek once `emotional_states` yoklugunda patliyordu.
Ilk engel kalkinca ikinci engel ortaya cikti (katmanli hata).

SISTEMIK OLCUM (1 Agu 2026) — UC UCA KESFETMEYI BIRAKTIK
---------------------------------------------------------
models/*.py'nin TAMAMI tarandi (83 modul, 228 ORM tablo tanimi) ve canli
semayla (217 tablo) karsilastirildi:

    MODELDE VAR / DB'DE YOK : 67 tablo

Modul dagilimi: diary 7 · study_room 7 · student_review 6 · teacher_pool 5 ·
university_info 5 · department_info 5 · university 5 · khan_content 3 ·
osym_question 3 · reasoning_models 3 · video_analytics 3 · ...

Yani tek tek uc kovalamak kaybeden strateji. Bu goc **modul butunu** olarak
diary'yi kapatir; kalan 60 tablo `GF-K5` altinda kayitli ve URUN KARARI
gerektirir (hepsi canli ozellik degil; bir kismi hic shiplenmemis model olabilir).

TABLOLAR (bagimlilik sirasi)
    diary_entries     -> users
    diary_exports     -> users
    goals             -> users
    learning_entries  -> users
    peer_comparisons  -> users
    insights          -> users, diary_entries
    reflections       -> users, diary_entries

DDL KAYNAGI: ORM modellerinden `alembic.autogenerate.render_python_code`.
ENUM: exportformat, goalstatus, insightcategory, reflectiondepth — DORDU DE
canlida ZATEN VAR (`DROP TABLE` enum tipini dusurmez) -> `create_type=False`.
RLS : organization_id kolonu YOK -> politika ICAT EDILMEDI (#461 karari).
VERI: tablolar BOS gelir.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "gfk2_diary_20260801"
down_revision = "gfk1_restore_20260801"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('diary_entries',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('success_count', sa.Integer(), nullable=True),
    sa.Column('failure_count', sa.Integer(), nullable=True),
    sa.Column('total_tasks', sa.Integer(), nullable=True),
    sa.Column('total_duration_minutes', sa.Integer(), nullable=True),
    sa.Column('highlights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('learnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('challenges', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tasks_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('markdown_content', sa.Text(), nullable=True),
    sa.Column('file_path', sa.String(length=512), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('diary_exports',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('format', postgresql.ENUM('MARKDOWN', 'PDF', 'JSON', name='exportformat', create_type=False), nullable=False),
    sa.Column('date_from', sa.Date(), nullable=False),
    sa.Column('date_to', sa.Date(), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=True),
    sa.Column('file_size', sa.Integer(), nullable=True),
    sa.Column('privacy_filter_applied', sa.Boolean(), nullable=True),
    sa.Column('redacted_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('share_token', sa.String(length=64), nullable=True),
    sa.Column('share_url', sa.String(length=512), nullable=True),
    sa.Column('share_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('share_access_count', sa.Integer(), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('is_backup', sa.Boolean(), nullable=True),
    sa.Column('is_encrypted', sa.Boolean(), nullable=True),
    sa.Column('encryption_algorithm', sa.String(length=50), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('goals',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('specific', sa.Text(), nullable=True),
    sa.Column('measurable', sa.Text(), nullable=True),
    sa.Column('achievable', sa.Text(), nullable=True),
    sa.Column('relevant', sa.Text(), nullable=True),
    sa.Column('time_bound', sa.DateTime(timezone=True), nullable=True),
    sa.Column('progress', sa.Integer(), nullable=True),
    sa.Column('current_value', sa.Float(), nullable=True),
    sa.Column('target_value', sa.Float(), nullable=False),
    sa.Column('unit', sa.String(length=50), nullable=True),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'COMPLETED', 'AT_RISK', 'CANCELLED', name='goalstatus', create_type=False), nullable=True),
    sa.Column('milestones', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('milestone_celebrations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_at_risk', sa.Boolean(), nullable=True),
    sa.Column('risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('predicted_completion', sa.DateTime(timezone=True), nullable=True),
    sa.Column('velocity', sa.Float(), nullable=True),
    sa.Column('adjustments', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('lessons_learned', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('success_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('challenges_faced', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('start_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('target_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('category', sa.String(length=100), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('learning_entries',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('domain', sa.String(length=100), nullable=True),
    sa.Column('skill_type', sa.String(length=100), nullable=True),
    sa.Column('related_concepts', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('concept_links', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('next_review', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_count', sa.Integer(), nullable=True),
    sa.Column('last_review', sa.DateTime(timezone=True), nullable=True),
    sa.Column('retention_score', sa.Float(), nullable=True),
    sa.Column('ease_factor', sa.Float(), nullable=True),
    sa.Column('interval_days', sa.Integer(), nullable=True),
    sa.Column('importance', sa.Integer(), nullable=True),
    sa.Column('mastery_level', sa.Float(), nullable=True),
    sa.Column('source_type', sa.String(length=50), nullable=True),
    sa.Column('source_reference', sa.String(length=512), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('peer_comparisons',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('period_start', sa.Date(), nullable=False),
    sa.Column('period_end', sa.Date(), nullable=False),
    sa.Column('success_rate_percentile', sa.Float(), nullable=True),
    sa.Column('speed_percentile', sa.Float(), nullable=True),
    sa.Column('quality_percentile', sa.Float(), nullable=True),
    sa.Column('overall_percentile', sa.Float(), nullable=True),
    sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('improvements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('best_practices', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_anonymized', sa.Boolean(), nullable=True),
    sa.Column('noise_added', sa.Boolean(), nullable=True),
    sa.Column('k_anonymity', sa.Integer(), nullable=True),
    sa.Column('peer_group_size', sa.Integer(), nullable=True),
    sa.Column('peer_group_avg_success_rate', sa.Float(), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('insights',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('diary_entry_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('category', postgresql.ENUM('TECHNICAL', 'PROCESS', 'COMMUNICATION', name='insightcategory', create_type=False), nullable=False),
    sa.Column('pattern', sa.Text(), nullable=False),
    sa.Column('root_cause', sa.Text(), nullable=True),
    sa.Column('correlation', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('evidence_count', sa.Integer(), nullable=True),
    sa.Column('recommendation', sa.Text(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=True),
    sa.Column('evidence_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['diary_entry_id'], ['diary_entries.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reflections',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('diary_entry_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('what_went_well', sa.Text(), nullable=True),
    sa.Column('what_could_improve', sa.Text(), nullable=True),
    sa.Column('what_did_i_learn', sa.Text(), nullable=True),
    sa.Column('what_will_i_do_differently', sa.Text(), nullable=True),
    sa.Column('additional_notes', sa.Text(), nullable=True),
    sa.Column('depth', postgresql.ENUM('SURFACE', 'MODERATE', 'DEEP', name='reflectiondepth', create_type=False), nullable=True),
    sa.Column('depth_score', sa.Float(), nullable=True),
    sa.Column('extracted_learnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('action_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['diary_entry_id'], ['diary_entries.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table("reflections")
    op.drop_table("insights")
    op.drop_table("peer_comparisons")
    op.drop_table("learning_entries")
    op.drop_table("goals")
    op.drop_table("diary_exports")
    op.drop_table("diary_entries")
