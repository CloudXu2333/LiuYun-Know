"""add knowledge base tables

Revision ID: 002
Revises: 001
Create Date: 2025-12-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # 创建知识库表
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'PROCESSING', name='knowledgebasestatus'), nullable=True),
        sa.Column('working_dir', sa.String(length=500), nullable=False),
        sa.Column('owner_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('working_dir')
    )
    op.create_index(op.f('ix_knowledge_bases_id'), 'knowledge_bases', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_bases_name'), 'knowledge_bases', ['name'], unique=False)
    
    # 创建知识库文件表
    op.create_table(
        'knowledge_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('minio_path', sa.String(length=1000), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='filestatus'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_id', sa.String(length=255), nullable=True),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_files_id'), 'knowledge_files', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_knowledge_files_id'), table_name='knowledge_files')
    op.drop_table('knowledge_files')
    op.drop_index(op.f('ix_knowledge_bases_name'), table_name='knowledge_bases')
    op.drop_index(op.f('ix_knowledge_bases_id'), table_name='knowledge_bases')
    op.drop_table('knowledge_bases')
