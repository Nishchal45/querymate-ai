"""Create query_history table

Revision ID: 001
Revises:
Create Date: 2026-03-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'query_history',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('natural_language', sa.Text(), nullable=False),
        sa.Column('generated_sql', sa.Text(), nullable=False),
        sa.Column('execution_time_ms', sa.Float(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('was_cached', sa.Boolean(), server_default='false'),
        sa.Column('cache_level', sa.String(2), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        'idx_query_history_created_at',
        'query_history',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_query_history_created_at')
    op.drop_table('query_history')
