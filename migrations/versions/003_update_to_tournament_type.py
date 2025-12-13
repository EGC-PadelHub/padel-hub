"""update publication_type enum to tournament_type with padel values

Revision ID: 003
Revises: 002
Create Date: 2025-11-21 10:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    import sqlalchemy as sa
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Update the enum type for ds_meta_data.publication_type (if column exists)
    ds_columns = [col['name'] for col in inspector.get_columns('ds_meta_data')]
    if 'publication_type' in ds_columns:
        op.execute("""
            ALTER TABLE ds_meta_data
            MODIFY COLUMN publication_type
            ENUM('NONE', 'MASTER_FINAL', 'MASTER', 'OPEN', 'QUALIFYING', 'NATIONAL_TOURS', 'OTHER')
            NOT NULL
        """)

    # Update the enum type for fm_meta_data.publication_type (if table exists)
    if 'fm_meta_data' in tables:
        op.execute("""
            ALTER TABLE fm_meta_data
            MODIFY COLUMN publication_type
            ENUM('NONE', 'MASTER_FINAL', 'MASTER', 'OPEN', 'QUALIFYING', 'NATIONAL_TOURS', 'OTHER')
            NOT NULL
        """)


def downgrade():
    # Revert to the old enum values
    op.execute("""
        ALTER TABLE ds_meta_data
        MODIFY COLUMN publication_type
        ENUM('NONE', 'ANNOTATION_COLLECTION', 'BOOK', 'BOOK_SECTION', 'CONFERENCE_PAPER',
             'DATA_MANAGEMENT_PLAN', 'JOURNAL_ARTICLE', 'PATENT', 'PREPRINT',
             'PROJECT_DELIVERABLE', 'PROJECT_MILESTONE', 'PROPOSAL', 'REPORT',
             'SOFTWARE_DOCUMENTATION', 'TAXONOMIC_TREATMENT', 'TECHNICAL_NOTE',
             'THESIS', 'WORKING_PAPER', 'OTHER')
        NOT NULL
    """)

    op.execute("""
        ALTER TABLE fm_meta_data
        MODIFY COLUMN publication_type
        ENUM('NONE', 'ANNOTATION_COLLECTION', 'BOOK', 'BOOK_SECTION', 'CONFERENCE_PAPER',
             'DATA_MANAGEMENT_PLAN', 'JOURNAL_ARTICLE', 'PATENT', 'PREPRINT',
             'PROJECT_DELIVERABLE', 'PROJECT_MILESTONE', 'PROPOSAL', 'REPORT',
             'SOFTWARE_DOCUMENTATION', 'TAXONOMIC_TREATMENT', 'TECHNICAL_NOTE',
             'THESIS', 'WORKING_PAPER', 'OTHER')
        NOT NULL
    """)
