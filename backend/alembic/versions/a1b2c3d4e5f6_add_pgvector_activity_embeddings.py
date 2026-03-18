"""Add pgvector extension and activity_embeddings table

Revision ID: a1b2c3d4e5f6
Revises: ffe04748bc6e
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ffe04748bc6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension (requires PostgreSQL superuser or pg_extension privilege)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create activity_embeddings table with vector column directly via raw SQL
    # (SQLAlchemy create_table doesn't natively support pgvector column types)
    op.execute("""
        CREATE TABLE IF NOT EXISTS activity_embeddings (
            id SERIAL PRIMARY KEY,
            activity_id INTEGER NOT NULL UNIQUE REFERENCES activities(id),
            embedding_vec vector(1536),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.create_index('ix_activity_embeddings_activity_id', 'activity_embeddings', ['activity_id'])

    # Create HNSW index for fast approximate nearest neighbor search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_activity_embeddings_hnsw "
        "ON activity_embeddings USING hnsw (embedding_vec vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_activity_embeddings_hnsw")
    op.drop_index('ix_activity_embeddings_activity_id', table_name='activity_embeddings')
    op.drop_table('activity_embeddings')
    op.execute("DROP EXTENSION IF EXISTS vector")
