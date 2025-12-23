"""add message metadata column

Revision ID: add_message_metadata
Revises: add_user_llm_configs
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_message_metadata'
down_revision = 'add_user_llm_configs'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 metadata_json 列到 messages 表
    op.add_column('messages', sa.Column('metadata_json', sa.Text(), nullable=True))


def downgrade():
    # 删除 metadata_json 列
    op.drop_column('messages', 'metadata_json')
