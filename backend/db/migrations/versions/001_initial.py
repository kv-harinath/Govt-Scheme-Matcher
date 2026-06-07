"""Initial migration - create schema.

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01T00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone')
    )
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)
    
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('district', sa.String(50), nullable=True),
        sa.Column('annual_income', sa.Integer(), nullable=True),
        sa.Column('caste', sa.String(20), nullable=True),
        sa.Column('occupation', sa.String(50), nullable=True),
        sa.Column('education', sa.String(50), nullable=True),
        sa.Column('bpl_card', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('disability', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('disability_type', sa.String(100), nullable=True),
        sa.Column('land_holding', sa.Float(), nullable=True),
        sa.Column('marital_status', sa.String(50), nullable=True),
        sa.Column('owns_house', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('jan_dhan_account', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('preferred_language', sa.String(10), nullable=True, server_default='en'),
        sa.Column('profile_hash', sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('ix_user_profiles_profile_hash', 'user_profiles', ['profile_hash'])
    
    # Create schemes table
    op.create_table(
        'schemes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('ministry', sa.String(255), nullable=True),
        sa.Column('level', sa.String(20), nullable=False, server_default='central'),
        sa.Column('state', sa.String(50), nullable=True),
        sa.Column('category', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('benefits', sa.Text(), nullable=False),
        sa.Column('eligibility_criteria', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('required_documents', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('application_mode', sa.String(20), nullable=True),
        sa.Column('application_url', sa.String(500), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('last_synced', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_url')
    )
    
    # Create indexes
    op.create_index(
        'idx_eligibility_criteria_gin',
        'schemes',
        ['eligibility_criteria'],
        postgresql_using='gin'
    )
    op.create_index(
        'idx_search_vector_gin',
        'schemes',
        ['search_vector'],
        postgresql_using='gin'
    )
    op.create_index('idx_state', 'schemes', ['state'])
    op.create_index('idx_level', 'schemes', ['level'])
    op.create_index('idx_is_active', 'schemes', ['is_active'])
    op.create_index('idx_category', 'schemes', ['category'], postgresql_using='gin')
    op.create_index('ix_schemes_source_url', 'schemes', ['source_url'], unique=True)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('ix_schemes_source_url', table_name='schemes')
    op.drop_index('idx_category', table_name='schemes')
    op.drop_index('idx_is_active', table_name='schemes')
    op.drop_index('idx_level', table_name='schemes')
    op.drop_index('idx_state', table_name='schemes')
    op.drop_index('idx_search_vector_gin', table_name='schemes')
    op.drop_index('idx_eligibility_criteria_gin', table_name='schemes')
    op.drop_table('schemes')
    
    op.drop_index('ix_user_profiles_profile_hash', table_name='user_profiles')
    op.drop_table('user_profiles')
    
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_table('users')
