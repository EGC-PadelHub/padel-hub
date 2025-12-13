"""remove feature models and update file table

Revision ID: 005
Revises: 004
Create Date: 2025-12-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection to execute raw SQL
    connection = op.get_bind()
    
    # Check if dataset_id column already exists
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('file')]
    
    if 'dataset_id' not in columns:
        # Add dataset_id column as nullable first
        op.add_column('file', sa.Column('dataset_id', sa.Integer(), nullable=True))
        
        # Check if feature_model table exists and has data to migrate
        tables = inspector.get_table_names()
        if 'feature_model' in tables and 'feature_model_id' in columns:
            # Migrate data: set dataset_id from feature_model relationship
            connection.execute(sa.text("""
                UPDATE file 
                INNER JOIN feature_model ON file.feature_model_id = feature_model.id
                SET file.dataset_id = feature_model.data_set_id
            """))
        
        # Now make dataset_id NOT NULL (requires existing_type for MySQL)
        op.alter_column('file', 'dataset_id', nullable=False, existing_type=sa.Integer())
    
    # Remove foreign key constraint from file table if exists
    try:
        op.drop_constraint('file_ibfk_1', 'file', type_='foreignkey')
    except:
        pass
    
    # Drop feature_model_id column from file table if exists
    if 'feature_model_id' in columns:
        op.drop_column('file', 'feature_model_id')
    
    # Add foreign key constraint to dataset if not exists
    try:
        op.create_foreign_key('file_dataset_fk', 'file', 'data_set', ['dataset_id'], ['id'])
    except:
        pass
    
    # Remove fm_meta_data_id from author table if exists
    author_columns = [col['name'] for col in inspector.get_columns('author')]
    if 'fm_meta_data_id' in author_columns:
        try:
            op.drop_constraint('author_ibfk_2', 'author', type_='foreignkey')
        except:
            pass
        op.drop_column('author', 'fm_meta_data_id')
    
    # Drop feature_model table if exists
    tables = inspector.get_table_names()
    if 'feature_model' in tables:
        op.drop_table('feature_model')
    
    # Drop fm_meta_data table if exists
    if 'fm_meta_data' in tables:
        op.drop_table('fm_meta_data')


def downgrade():
    # Recreate fm_meta_data table
    op.create_table('fm_meta_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uvl_filename', sa.String(length=120), nullable=True),
        sa.Column('title', sa.String(length=120), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tournament_type', sa.String(length=120), nullable=True),
        sa.Column('publication_doi', sa.String(length=120), nullable=True),
        sa.Column('tags', sa.String(length=120), nullable=True),
        sa.Column('uvl_version', sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate feature_model table
    op.create_table('feature_model',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data_set_id', sa.Integer(), nullable=False),
        sa.Column('fm_meta_data_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['data_set_id'], ['data_set.id'], ),
        sa.ForeignKeyConstraint(['fm_meta_data_id'], ['fm_meta_data.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add fm_meta_data_id back to author table
    op.add_column('author', sa.Column('fm_meta_data_id', sa.Integer(), nullable=True))
    op.create_foreign_key('author_ibfk_2', 'author', 'fm_meta_data', ['fm_meta_data_id'], ['id'])
    
    # Remove dataset_id from file table
    op.drop_constraint('file_dataset_fk', 'file', type_='foreignkey')
    op.drop_column('file', 'dataset_id')
    
    # Add feature_model_id back to file table
    op.add_column('file', sa.Column('feature_model_id', sa.Integer(), nullable=False))
    op.create_foreign_key('file_ibfk_1', 'file', 'feature_model', ['feature_model_id'], ['id'])
