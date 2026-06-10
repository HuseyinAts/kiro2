"""add HNSW index on question_bank.embedding (vector_cosine_ops)

Bağlam: 2026-06-10 DB audit — embedding vector(768) dolu (147K) ama hiçbir
ANN/vector index yoktu; semantik arama tam tarama yapıyordu. Bu migration
pgvector HNSW index'ini ekler (cosine). CONCURRENTLY autocommit_block içinde
çalışır; IF NOT EXISTS sayesinde ad-hoc oluşturulduysa no-op'tur.

Revision ID: b2f1a9c7d3e4
Revises: 5aabf9a6c658
Create Date: 2026-06-10
"""
from alembic import op

revision = "b2f1a9c7d3e4"
down_revision = "5aabf9a6c658"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CONCURRENTLY transaction bloğunda çalışamaz -> autocommit_block
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qb_embedding_hnsw "
            "ON question_bank USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_qb_embedding_hnsw")
