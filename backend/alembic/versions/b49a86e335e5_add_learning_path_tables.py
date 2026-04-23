"""add_learning_path_tables

Revision ID: b49a86e335e5
Revises: 370b03703c0d
Create Date: 2026-01-27 19:32:17.045308

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b49a86e335e5'
down_revision: Union[str, None] = '370b03703c0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Learning Path tables only (stripped autogenerate noise)

    op.create_table('curriculum_update_requests',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('update_type', sa.String(length=50), nullable=False),
    sa.Column('subject', sa.String(length=50), nullable=False),
    sa.Column('affected_standards', sa.JSON(), nullable=True),
    sa.Column('changes_description', sa.Text(), nullable=False),
    sa.Column('source_document', sa.String(length=500), nullable=True),
    sa.Column('requested_by', sa.String(length=100), nullable=False),
    sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('reviewed_by', sa.String(length=100), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('implementation_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_update_req_status', 'curriculum_update_requests', ['status'])
    op.create_index('idx_update_req_subject', 'curriculum_update_requests', ['subject'])
    op.create_index('idx_update_req_type', 'curriculum_update_requests', ['update_type'])

    op.create_table('fallback_videos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('subject', sa.String(length=100), nullable=False),
    sa.Column('topic', sa.String(length=100), nullable=True),
    sa.Column('video_id', sa.String(length=100), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
    sa.Column('duration', sa.String(length=20), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=True),
    sa.Column('channel_name', sa.String(length=200), nullable=True),
    sa.Column('channel_id', sa.String(length=100), nullable=True),
    sa.Column('turkish_score', sa.Float(), nullable=False),
    sa.Column('relevance_score', sa.Float(), nullable=False),
    sa.Column('quality_score', sa.Float(), nullable=False),
    sa.Column('final_score', sa.Float(), nullable=False),
    sa.Column('is_accessible', sa.Boolean(), nullable=False),
    sa.Column('is_embeddable', sa.Boolean(), nullable=False),
    sa.Column('is_turkish', sa.Boolean(), nullable=False),
    sa.Column('is_example', sa.Boolean(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('video_id')
    )
    op.create_index('idx_fallback_final_score', 'fallback_videos', ['final_score'])
    op.create_index('idx_fallback_is_example', 'fallback_videos', ['is_example'])
    op.create_index('idx_fallback_subject_topic', 'fallback_videos', ['subject', 'topic'])

    op.create_table('meb_curriculum_standards',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('subject', sa.String(length=50), nullable=False),
    sa.Column('grade_level', sa.String(length=10), nullable=False),
    sa.Column('unit_name', sa.String(length=200), nullable=False),
    sa.Column('topic_name', sa.String(length=200), nullable=False),
    sa.Column('learning_outcomes', sa.JSON(), nullable=True),
    sa.Column('key_concepts', sa.JSON(), nullable=True),
    sa.Column('skills', sa.JSON(), nullable=True),
    sa.Column('prerequisites', sa.JSON(), nullable=True),
    sa.Column('assessment_criteria', sa.JSON(), nullable=True),
    sa.Column('duration_hours', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_meb_active', 'meb_curriculum_standards', ['is_active'])
    op.create_index('idx_meb_grade_level', 'meb_curriculum_standards', ['grade_level'])
    op.create_index('idx_meb_subject', 'meb_curriculum_standards', ['subject'])
    op.create_index('idx_meb_subject_grade', 'meb_curriculum_standards', ['subject', 'grade_level'])

    op.create_table('osym_standards',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('exam_type', sa.String(length=20), nullable=False),
    sa.Column('subject', sa.String(length=50), nullable=False),
    sa.Column('topic_code', sa.String(length=50), nullable=False),
    sa.Column('topic_name', sa.String(length=200), nullable=False),
    sa.Column('priority_level', sa.Integer(), nullable=False),
    sa.Column('question_count_range', sa.JSON(), nullable=True),
    sa.Column('difficulty_distribution', sa.JSON(), nullable=True),
    sa.Column('cognitive_levels', sa.JSON(), nullable=True),
    sa.Column('exam_frequency', sa.Float(), nullable=False),
    sa.Column('last_exam_appearance', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_osym_active', 'osym_standards', ['is_active'])
    op.create_index('idx_osym_exam_type', 'osym_standards', ['exam_type'])
    op.create_index('idx_osym_priority', 'osym_standards', ['priority_level'])
    op.create_index('idx_osym_subject', 'osym_standards', ['subject'])

    op.create_table('quizzes',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('subject', sa.String(length=100), nullable=False),
    sa.Column('topic', sa.String(length=200), nullable=True),
    sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
    sa.Column('passing_score', sa.Float(), nullable=False),
    sa.Column('shuffle_questions', sa.Boolean(), nullable=False),
    sa.Column('show_answers_after', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_quiz_subject_topic', 'quizzes', ['subject', 'topic'])

    # Tables with foreign keys to above tables
    op.create_table('curriculum_alignments',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('meb_standard_id', sa.String(length=100), nullable=False),
    sa.Column('osym_standard_id', sa.String(length=100), nullable=False),
    sa.Column('alignment_score', sa.Float(), nullable=False),
    sa.Column('alignment_type', sa.String(length=50), nullable=False),
    sa.Column('gaps_identified', sa.JSON(), nullable=True),
    sa.Column('recommendations', sa.JSON(), nullable=True),
    sa.Column('verified_by', sa.String(length=100), nullable=True),
    sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('alignment_score >= 0.0 AND alignment_score <= 1.0', name='check_alignment_score'),
    sa.ForeignKeyConstraint(['meb_standard_id'], ['meb_curriculum_standards.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['osym_standard_id'], ['osym_standards.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alignment_meb', 'curriculum_alignments', ['meb_standard_id'])
    op.create_index('idx_alignment_osym', 'curriculum_alignments', ['osym_standard_id'])
    op.create_index('idx_alignment_score', 'curriculum_alignments', ['alignment_score'])

    op.create_table('learning_outcomes',
    sa.Column('id', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('subject', sa.String(length=50), nullable=False),
    sa.Column('grade_level', sa.String(length=10), nullable=False),
    sa.Column('cognitive_level', sa.String(length=50), nullable=False),
    sa.Column('bloom_taxonomy', sa.String(length=20), nullable=False),
    sa.Column('meb_standard_id', sa.String(length=100), nullable=False),
    sa.Column('assessment_methods', sa.JSON(), nullable=True),
    sa.Column('sample_activities', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['meb_standard_id'], ['meb_curriculum_standards.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_outcome_code', 'learning_outcomes', ['code'])
    op.create_index('idx_outcome_meb_standard', 'learning_outcomes', ['meb_standard_id'])
    op.create_index('idx_outcome_subject', 'learning_outcomes', ['subject'])

    op.create_table('learning_path_student_profiles',
    sa.Column('student_id', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.String(length=100), nullable=True),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('grade', sa.String(length=20), nullable=False),
    sa.Column('exam_target', sa.String(length=50), nullable=False),
    sa.Column('learning_style', sa.String(length=50), nullable=False),
    sa.Column('knowledge_level', sa.String(length=50), nullable=False),
    sa.Column('interests', sa.JSON(), nullable=False),
    sa.Column('goals', sa.JSON(), nullable=False),
    sa.Column('available_time', sa.Integer(), nullable=False),
    sa.Column('target_university', sa.String(length=200), nullable=True),
    sa.Column('target_department', sa.String(length=200), nullable=True),
    sa.Column('target_ranking', sa.String(length=50), nullable=True),
    sa.Column('weekly_study_commitment', sa.Integer(), nullable=True),
    sa.Column('exam_date', sa.Date(), nullable=True),
    sa.Column('vark_visual_score', sa.Float(), nullable=True),
    sa.Column('vark_auditory_score', sa.Float(), nullable=True),
    sa.Column('vark_reading_score', sa.Float(), nullable=True),
    sa.Column('vark_kinesthetic_score', sa.Float(), nullable=True),
    sa.Column('felder_active_reflective', sa.Float(), nullable=True),
    sa.Column('felder_sensing_intuitive', sa.Float(), nullable=True),
    sa.Column('felder_visual_verbal', sa.Float(), nullable=True),
    sa.Column('felder_sequential_global', sa.Float(), nullable=True),
    sa.Column('overall_progress', sa.Float(), nullable=True),
    sa.Column('average_quiz_score', sa.Float(), nullable=True),
    sa.Column('total_study_time_minutes', sa.Integer(), nullable=True),
    sa.Column('last_activity_at', sa.DateTime(), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    sa.PrimaryKeyConstraint('student_id')
    )
    op.create_index('idx_student_exam_target', 'learning_path_student_profiles', ['exam_target'])
    op.create_index('idx_student_grade', 'learning_path_student_profiles', ['grade'])
    op.create_index('idx_student_last_activity', 'learning_path_student_profiles', ['last_activity_at'])
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_student_learning_style ON learning_path_student_profiles (learning_style)"))
    op.create_index('idx_student_user_id', 'learning_path_student_profiles', ['user_id'])

    op.create_table('learning_paths',
    sa.Column('path_id', sa.String(length=100), nullable=False),
    sa.Column('student_id', sa.String(length=100), nullable=False),
    sa.Column('subject', sa.String(length=100), nullable=False),
    sa.Column('difficulty_level', sa.String(length=50), nullable=False),
    sa.Column('duration_weeks', sa.Integer(), nullable=False),
    sa.Column('target_date', sa.DateTime(), nullable=True),
    sa.Column('modules', sa.JSON(), nullable=False),
    sa.Column('phases', sa.JSON(), nullable=False),
    sa.Column('resources', sa.JSON(), nullable=False),
    sa.Column('ai_generated', sa.Boolean(), nullable=False),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('agent_metadata', sa.JSON(), nullable=False),
    sa.Column('total_modules', sa.Integer(), nullable=False),
    sa.Column('completed_modules', sa.Integer(), nullable=False),
    sa.Column('total_topics', sa.Integer(), nullable=False),
    sa.Column('completed_topics', sa.Integer(), nullable=False),
    sa.Column('overall_progress', sa.Float(), nullable=False),
    sa.Column('total_time', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('overall_progress >= 0 AND overall_progress <= 100', name='check_progress_range'),
    sa.ForeignKeyConstraint(['student_id'], ['learning_path_student_profiles.student_id']),
    sa.PrimaryKeyConstraint('path_id')
    )
    op.create_index('idx_path_created_at', 'learning_paths', ['created_at'])
    op.create_index('idx_path_student_subject', 'learning_paths', ['student_id', 'subject'])

    op.create_table('quiz_questions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('quiz_id', sa.String(length=100), nullable=False),
    sa.Column('question_id', sa.String(), nullable=False),
    sa.Column('order_number', sa.Integer(), nullable=False),
    sa.Column('points', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_quiz_question_order', 'quiz_questions', ['quiz_id', 'order_number'])

    op.create_table('quiz_submissions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('student_id', sa.String(length=100), nullable=False),
    sa.Column('quiz_id', sa.String(length=100), nullable=False),
    sa.Column('question_count', sa.Integer(), nullable=False),
    sa.Column('passing_score', sa.Float(), nullable=False),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('correct_count', sa.Integer(), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('answers', sa.JSON(), nullable=False),
    sa.Column('total_time_seconds', sa.Integer(), nullable=False),
    sa.Column('submitted_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('score >= 0 AND score <= 100', name='check_quiz_score_range'),
    sa.ForeignKeyConstraint(['student_id'], ['learning_path_student_profiles.student_id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_quiz_student_quiz', 'quiz_submissions', ['student_id', 'quiz_id'])
    op.create_index('idx_quiz_submitted_at', 'quiz_submissions', ['submitted_at'])

    op.create_table('topic_completions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('student_id', sa.String(length=100), nullable=False),
    sa.Column('node_id', sa.String(length=100), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.Column('completion_date', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['learning_path_student_profiles.student_id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_completion_student_node', 'topic_completions', ['student_id', 'node_id'], unique=True)

    op.create_table('topic_progress',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('student_id', sa.String(length=100), nullable=False),
    sa.Column('node_id', sa.String(length=100), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=False),
    sa.Column('time_spent', sa.Integer(), nullable=False),
    sa.Column('completed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_percentage'),
    sa.ForeignKeyConstraint(['student_id'], ['learning_path_student_profiles.student_id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_progress_student_node', 'topic_progress', ['student_id', 'node_id'])


def downgrade() -> None:
    op.drop_table('topic_progress')
    op.drop_table('topic_completions')
    op.drop_table('quiz_submissions')
    op.drop_table('quiz_questions')
    op.drop_table('learning_paths')
    op.drop_table('learning_path_student_profiles')
    op.drop_table('learning_outcomes')
    op.drop_table('curriculum_alignments')
    op.drop_table('quizzes')
    op.drop_table('osym_standards')
    op.drop_table('meb_curriculum_standards')
    op.drop_table('fallback_videos')
    op.drop_table('curriculum_update_requests')
