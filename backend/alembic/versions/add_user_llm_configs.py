"""add user llm configs

Revision ID: add_user_llm_configs
Revises: 
Create Date: 2024-12-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_llm_configs'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None


def upgrade():
    # 创建 user_llm_configs 表
    op.create_table(
        'user_llm_configs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # 创建索引
    op.create_index('ix_user_llm_configs_user_id', 'user_llm_configs', ['user_id'])


def downgrade():
    op.drop_index('ix_user_llm_configs_user_id', 'user_llm_configs')
    op.drop_table('user_llm_configs')
