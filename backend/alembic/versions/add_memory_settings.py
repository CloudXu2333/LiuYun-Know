"""add memory settings to user

Revision ID: add_memory_settings
Revises: add_long_term_memory
Create Date: 2024-12-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_memory_settings'
down_revision = 'add_long_term_memory'
branch_labels = None
depends_on = None


def upgrade():
    # 添加记忆设置字段到 users 表
    op.add_column('users', sa.Column('memory_top_k', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('users', sa.Column('core_memory_threshold', sa.Integer(), nullable=False, server_default='80'))


def downgrade():
    op.drop_column('users', 'core_memory_threshold')
    op.drop_column('users', 'memory_top_k')
