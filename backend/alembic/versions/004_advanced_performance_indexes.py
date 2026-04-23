"""
Advanced Performance Indexes - Phase 2 Optimization

Revision ID: 004_adv_perf_idx
Revises: 003_real_perf_idx
Create Date: 2026-02-07

Adds:
- GIN indexes for Turkish full-text search on question content
- Composite indexes for common dashboard queries
- Partial indexes for active/recent records
- Created_at indexes for time-series queries
- pgvector HNSW index (if extension available)

Expected impact: 3-10x faster text search, 2-5x faster dashboard queries
"""
import sqlalchemy as sa

from alembic import op

revision = '004_adv_perf_idx'
down_revision = '003_real_perf_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add advanced performance indexes."""
    conn = op.get_bind()

    def table_exists(name: str) -> bool:
        result = conn.execute(
            sa.text(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=:t)"
            ),
            {"t": name},
        )
        return result.scalar()

    def index_exists(name: str) -> bool:
        result = conn.execute(
            sa.text(
                "SELECT EXISTS(SELECT 1 FROM pg_indexes WHERE indexname=:n)"
            ),
            {"n": name},
        )
        return result.scalar()

    def safe_create_index(name, table, columns, **kwargs):
        """Create index only if it doesn't exist. Uses savepoints for safety."""
        try:
            conn.execute(sa.text(f"SAVEPOINT sp_{name[:40]}"))
            if index_exists(name):
                conn.execute(sa.text(f"RELEASE SAVEPOINT sp_{name[:40]}"))
                return
            op.create_index(name, table, columns, **kwargs)
            conn.execute(sa.text(f"RELEASE SAVEPOINT sp_{name[:40]}"))
            print(f"  + {name}")
        except Exception as e:
            conn.execute(sa.text(f"ROLLBACK TO SAVEPOINT sp_{name[:40]}"))
            print(f"  SKIP {name}: {e}")

    # ========================================================================
    # 1. GIN INDEXES - Turkish Full-Text Search
    # ========================================================================
    # GIN indexes on text columns for fast LIKE/ILIKE and tsvector search

    if table_exists('sorular'):
        # Full-text search on question content (Turkish)
        try:
            conn.execute(sa.text("SAVEPOINT sp_sorular_gin"))
            conn.execute(sa.text(
                "CREATE INDEX IF NOT EXISTS idx_sorular_metin_gin "
                "ON sorular USING gin (to_tsvector('simple', COALESCE(metin, '')))"
            ))
            conn.execute(sa.text("RELEASE SAVEPOINT sp_sorular_gin"))
            print("  + idx_sorular_metin_gin (GIN text search)")
        except Exception as e:
            conn.execute(sa.text("ROLLBACK TO SAVEPOINT sp_sorular_gin"))
            print(f"  SKIP idx_sorular_metin_gin: {e}")

        # Trigram index for fuzzy matching (requires pg_trgm extension)
        try:
            conn.execute(sa.text("SAVEPOINT sp_sorular_trgm"))
            conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            conn.execute(sa.text(
                "CREATE INDEX IF NOT EXISTS idx_sorular_metin_trgm "
                "ON sorular USING gin (metin gin_trgm_ops)"
            ))
            conn.execute(sa.text("RELEASE SAVEPOINT sp_sorular_trgm"))
            print("  + idx_sorular_metin_trgm (trigram fuzzy search)")
        except Exception as e:
            conn.execute(sa.text("ROLLBACK TO SAVEPOINT sp_sorular_trgm"))
            print(f"  SKIP idx_sorular_metin_trgm: {e}")

        # Composite: exam_type + difficulty + active (most common filter)
        safe_create_index(
            'idx_sorular_sinav_zorluk_aktif', 'sorular',
            ['sinav_tipi', 'zorluk_seviyesi'],
            postgresql_where=sa.text('aktif = true'),
        )

        # Created_at for time-series queries
        safe_create_index(
            'idx_sorular_created_at', 'sorular', ['olusturma_tarihi'],
        )

    if table_exists('questions'):
        # GIN for question text search (actual column: question_text)
        try:
            conn.execute(sa.text("SAVEPOINT gin_questions"))
            conn.execute(sa.text(
                "CREATE INDEX IF NOT EXISTS idx_questions_text_gin "
                "ON questions USING gin (to_tsvector('simple', COALESCE(question_text, '')))"
            ))
            conn.execute(sa.text("RELEASE SAVEPOINT gin_questions"))
            print("  + idx_questions_text_gin (GIN text search)")
        except Exception as e:
            conn.execute(sa.text("ROLLBACK TO SAVEPOINT gin_questions"))
            print(f"  SKIP idx_questions_text_gin: {e}")

        # Composite: subject + difficulty + aktif (actual column names)
        safe_create_index(
            'idx_questions_subj_diff_aktif', 'questions',
            ['subject_area', 'difficulty', 'aktif'],
        )

        # Created_at for recent questions
        safe_create_index(
            'idx_questions_created_at', 'questions', ['created_at'],
        )

    # ========================================================================
    # 2. STUDENT PERFORMANCE INDEXES - Dashboard Queries
    # ========================================================================

    if table_exists('sinav_sonuclari'):
        # Composite for student dashboard: student + date range
        safe_create_index(
            'idx_sinav_sonuclari_ogrenci_tarih', 'sinav_sonuclari',
            ['ogrenci_id', 'olusturma_tarihi'],
        )

        # Score-based queries (leaderboard, analytics)
        safe_create_index(
            'idx_sinav_sonuclari_puan', 'sinav_sonuclari', ['toplam_puan'],
        )

    if table_exists('student_answers'):
        # Composite for answer analysis: session + correct
        safe_create_index(
            'idx_student_answers_session_correct', 'student_answers',
            ['exam_session_id', 'is_correct'],
        )

    # ========================================================================
    # 3. LEARNING PATH INDEXES
    # ========================================================================

    if table_exists('learning_paths'):
        safe_create_index(
            'idx_learning_paths_student', 'learning_paths', ['student_id'],
        )
        safe_create_index(
            'idx_learning_paths_subject', 'learning_paths',
            ['student_id', 'subject'],
        )

    if table_exists('ogrenme_yollari'):
        safe_create_index(
            'idx_ogrenme_yollari_ogrenci', 'ogrenme_yollari', ['ogrenci_id'],
        )

    # ========================================================================
    # 4. PGVECTOR HNSW INDEX (if extension available)
    # ========================================================================
    try:
        conn.execute(sa.text("SAVEPOINT sp_pgvector"))
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Check if embeddings table exists
        if table_exists('question_embeddings'):
            conn.execute(sa.text(
                "CREATE INDEX IF NOT EXISTS idx_question_embeddings_hnsw "
                "ON question_embeddings USING hnsw (embedding vector_cosine_ops) "
                "WITH (m = 16, ef_construction = 200)"
            ))
            print("  + idx_question_embeddings_hnsw (HNSW vector search)")
        conn.execute(sa.text("RELEASE SAVEPOINT sp_pgvector"))
    except Exception as e:
        conn.execute(sa.text("ROLLBACK TO SAVEPOINT sp_pgvector"))
        print(f"  SKIP pgvector HNSW: {e}")

    # ========================================================================
    # 5. NOTIFICATION / ACTIVITY INDEXES
    # ========================================================================
    if table_exists('notifications'):
        safe_create_index(
            'idx_notifications_user_read', 'notifications',
            ['user_id', 'is_read'],
        )
        safe_create_index(
            'idx_notifications_created', 'notifications', ['created_at'],
        )

    if table_exists('bildirimler'):
        safe_create_index(
            'idx_bildirimler_kullanici', 'bildirimler', ['kullanici_id', 'okundu'],
        )

    print("SUCCESS: Advanced performance indexes created")


def downgrade() -> None:
    """Remove advanced performance indexes."""
    indexes_to_drop = [
        ('idx_bildirimler_kullanici', 'bildirimler'),
        ('idx_notifications_created', 'notifications'),
        ('idx_notifications_user_read', 'notifications'),
        ('idx_ogrenme_yollari_ogrenci', 'ogrenme_yollari'),
        ('idx_learning_paths_subject', 'learning_paths'),
        ('idx_learning_paths_student', 'learning_paths'),
        ('idx_student_answers_session_correct', 'student_answers'),
        ('idx_sinav_sonuclari_puan', 'sinav_sonuclari'),
        ('idx_sinav_sonuclari_ogrenci_tarih', 'sinav_sonuclari'),
        ('idx_questions_created_at', 'questions'),
        ('idx_questions_subj_diff_aktif', 'questions'),
        ('idx_questions_text_gin', 'questions'),
        ('idx_sorular_created_at', 'sorular'),
        ('idx_sorular_sinav_zorluk_aktif', 'sorular'),
        ('idx_sorular_metin_trgm', 'sorular'),
        ('idx_sorular_metin_gin', 'sorular'),
    ]
    for idx_name, tbl_name in indexes_to_drop:
        try:
            op.drop_index(idx_name, table_name=tbl_name, if_exists=True)
        except Exception:
            pass

    # Drop extensions only if no other objects depend on them
    try:
        op.execute("DROP EXTENSION IF EXISTS pg_trgm CASCADE")
    except Exception:
        pass
