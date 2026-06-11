"""fix_schema_drift_concurrently

Revision ID: 5aabf9a6c658
Revises: beta_vp_idx_20260602
Create Date: 2026-06-07 14:37:59.122456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5aabf9a6c658'
down_revision: Union[str, None] = 'beta_vp_idx_20260602'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    # Commit the transaction started by env.py first to allow changing isolation level
    if bind.in_transaction():
        bind.commit()
        
    # D. Migration dosyasındaki upgrade fonksiyonuna op.get_bind().execution_options(isolation_level="AUTOCOMMIT") ekle.
    op.get_bind().execution_options(isolation_level="AUTOCOMMIT")
    
    # İndeks oluşturma satırına postgresql_concurrently=True parametresini dahil et.
    # 1. idx_qb_primary_topic
    try:
        op.create_index(
            'idx_qb_primary_topic',
            'question_bank',
            ['primary_topic_id'],
            postgresql_concurrently=True,
            postgresql_where='primary_topic_id IS NOT NULL'
        )
        print("Created index idx_qb_primary_topic concurrently.")
    except Exception as e:
        print(f"Skipping idx_qb_primary_topic (already exists or error): {e}")

    # 2. idx_qb_calib_pool
    try:
        op.create_index(
            'idx_qb_calib_pool',
            'question_bank',
            ['is_calib_pool'],
            postgresql_concurrently=True,
            postgresql_where='is_calib_pool = true'
        )
        print("Created index idx_qb_calib_pool concurrently.")
    except Exception as e:
        print(f"Skipping idx_qb_calib_pool (already exists or error): {e}")

    # 3. idx_qb_cat_subject_active
    try:
        op.create_index(
            'idx_qb_cat_subject_active',
            'question_bank',
            [sa.text('lower(subject_area)'), 'is_active'],
            postgresql_concurrently=True,
            postgresql_where='is_active = true'
        )
        print("Created index idx_qb_cat_subject_active concurrently.")
    except Exception as e:
        print(f"Skipping idx_qb_cat_subject_active (already exists or error): {e}")

    # 4. idx_qb_soru_hash
    try:
        op.create_index(
            'idx_qb_soru_hash',
            'question_bank',
            ['soru_hash'],
            postgresql_concurrently=True
        )
        print("Created index idx_qb_soru_hash concurrently.")
    except Exception as e:
        print(f"Skipping idx_qb_soru_hash (already exists or error): {e}")

    # 5. uq_qb_soru_hash_active
    try:
        op.create_index(
            'uq_qb_soru_hash_active',
            'question_bank',
            ['soru_hash'],
            unique=True,
            postgresql_concurrently=True,
            postgresql_where='is_active = true'
        )
        print("Created index uq_qb_soru_hash_active concurrently.")
    except Exception as e:
        print(f"Skipping uq_qb_soru_hash_active (already exists or error): {e}")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.in_transaction():
        bind.commit()
        
    op.get_bind().execution_options(isolation_level="AUTOCOMMIT")
    
    try:
        op.drop_index('uq_qb_soru_hash_active', table_name='question_bank', postgresql_concurrently=True)
        print("Dropped index uq_qb_soru_hash_active concurrently.")
    except Exception as e:
        print(f"Skipping drop uq_qb_soru_hash_active: {e}")
        
    try:
        op.drop_index('idx_qb_soru_hash', table_name='question_bank', postgresql_concurrently=True)
        print("Dropped index idx_qb_soru_hash concurrently.")
    except Exception as e:
        print(f"Skipping drop idx_qb_soru_hash: {e}")
        
    try:
        op.drop_index('idx_qb_cat_subject_active', table_name='question_bank', postgresql_concurrently=True)
        print("Dropped index idx_qb_cat_subject_active concurrently.")
    except Exception as e:
        print(f"Skipping drop idx_qb_cat_subject_active: {e}")
        
    try:
        op.drop_index('idx_qb_calib_pool', table_name='question_bank', postgresql_concurrently=True)
        print("Dropped index idx_qb_calib_pool concurrently.")
    except Exception as e:
        print(f"Skipping drop idx_qb_calib_pool: {e}")
        
    try:
        op.drop_index('idx_qb_primary_topic', table_name='question_bank', postgresql_concurrently=True)
        print("Dropped index idx_qb_primary_topic concurrently.")
    except Exception as e:
        print(f"Skipping drop idx_qb_primary_topic: {e}")