"""add embedding column to long_term_memories

Revision ID: add_memory_embedding
Revises: add_long_term_memory
Create Date: 2024-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_memory_embedding'
down_revision: Union[str, None] = 'add_long_term_memory'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 embedding 列（TEXT 类型，存储 JSON 格式的向量）
    op.add_column(
        'long_term_memories',
        sa.Column('embedding', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('long_term_memories', 'embedding')
