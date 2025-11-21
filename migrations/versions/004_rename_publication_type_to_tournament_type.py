"""rename publication_type to tournament_type

Revision ID: 004
Revises: 003
Create Date: 2025-11-21 13:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Rename column in ds_meta_data table
    op.execute("ALTER TABLE ds_meta_data CHANGE COLUMN publication_type tournament_type "
               "ENUM('NONE', 'MASTER_FINAL', 'MASTER', 'OPEN', 'QUALIFYING', 'NATIONAL_TOURS', 'OTHER') NOT NULL")

    # Rename column in fm_meta_data table
    op.execute("ALTER TABLE fm_meta_data CHANGE COLUMN publication_type tournament_type "
               "ENUM('NONE', 'MASTER_FINAL', 'MASTER', 'OPEN', 'QUALIFYING', 'NATIONAL_TOURS', 'OTHER') NOT NULL")


def downgrade():
    # Revert column name in ds_meta_data table
    op.execute("ALTER TABLE ds_meta_data CHANGE COLUMN tournament_type publication_type "
               "ENUM('NONE', 'MASTER_FINAL', 'MASTER', 'OPEN', 'QUALIFYING', 'NATIONAL_TOURS', 'OTHER') NOT NULL")

    # Revert column name in fm_meta_data table
    op.execute("ALTER TABLE fm_meta_data CHANGE COLUMN tournament_type publication_type "
               "ENUM('NONE', 'MASTER_FINAL', 'MASTER', 'OPEN', 'QUALIFYING', 'NATIONAL_TOURS', 'OTHER') NOT NULL")
