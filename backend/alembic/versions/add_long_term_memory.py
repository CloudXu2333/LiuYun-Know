"""add long term memory table

Revision ID: add_long_term_memory
Revises: add_user_llm_configs
Create Date: 2024-12-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_long_term_memory'
down_revision = 'add_user_llm_configs'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'long_term_memories',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), default='general'),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('long_term_memories')
