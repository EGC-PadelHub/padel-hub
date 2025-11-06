"""add anonymous flag to ds_meta_data

Revision ID: 002
Revises: 001
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add anonymous boolean column to ds_meta_data with default False
    op.add_column(
        'ds_meta_data',
        sa.Column('anonymous', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )
    # remove server default to keep schema clean
    op.alter_column('ds_meta_data', 'anonymous', server_default=None)


def downgrade():
    # Remove the anonymous column
    op.drop_column('ds_meta_data', 'anonymous')
