"""add max_context_tokens to user_llm_configs

Revision ID: add_max_context_tokens
Revises: add_message_metadata
Create Date: 2025-12-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_max_context_tokens'
down_revision = 'add_message_metadata'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 max_context_tokens 列到 user_llm_configs 表
    op.add_column('user_llm_configs', sa.Column('max_context_tokens', sa.Integer(), nullable=True, server_default='65536'))
    
    # 更新现有记录的默认值
    op.execute("UPDATE user_llm_configs SET max_context_tokens = 65536 WHERE max_context_tokens IS NULL")
    
    # 设置为非空
    op.alter_column('user_llm_configs', 'max_context_tokens', nullable=False)


def downgrade():
    op.drop_column('user_llm_configs', 'max_context_tokens')
