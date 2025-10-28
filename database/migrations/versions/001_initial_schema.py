"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-01-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create provinces table
    op.create_table(
        'provinces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provinces_id'), 'provinces', ['id'], unique=False)
    op.create_index(op.f('ix_provinces_name'), 'provinces', ['name'], unique=True)

    # Create districts table
    op.create_table(
        'districts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('province_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['province_id'], ['provinces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_districts_id'), 'districts', ['id'], unique=False)
    op.create_index(op.f('ix_districts_name'), 'districts', ['name'], unique=False)

    # Create wards table
    op.create_table(
        'wards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('district_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wards_id'), 'wards', ['id'], unique=False)
    op.create_index(op.f('ix_wards_name'), 'wards', ['name'], unique=False)

    # Create form_metadata table
    op.create_table(
        'form_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('province_id', sa.Integer(), nullable=False),
        sa.Column('district_id', sa.Integer(), nullable=False),
        sa.Column('ward_id', sa.Integer(), nullable=False),
        sa.Column('prepared_by', sa.String(length=200), nullable=False),
        sa.Column('sign', sa.String(length=200), nullable=True),
        sa.Column('contact', sa.String(length=50), nullable=True),
        sa.Column('submission_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['district_id'], ['districts.id'], ),
        sa.ForeignKeyConstraint(['province_id'], ['provinces.id'], ),
        sa.ForeignKeyConstraint(['ward_id'], ['wards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_form_metadata_id'), 'form_metadata', ['id'], unique=False)

    # Create members table
    op.create_table(
        'members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('gender', sa.Enum('M', 'F', 'OTHER', name='genderenum'), nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('nrc', sa.String(length=50), nullable=True),
        sa.Column('voters_id', sa.String(length=50), nullable=True),
        sa.Column('contact', sa.String(length=50), nullable=True),
        sa.Column('ward_id', sa.Integer(), nullable=False),
        sa.Column('form_metadata_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['form_metadata_id'], ['form_metadata.id'], ),
        sa.ForeignKeyConstraint(['ward_id'], ['wards.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_members_id'), 'members', ['id'], unique=False)
    op.create_index(op.f('ix_members_name'), 'members', ['name'], unique=False)
    op.create_index(op.f('ix_members_nrc'), 'members', ['nrc'], unique=False)
    op.create_index(op.f('ix_members_voters_id'), 'members', ['voters_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_members_voters_id'), table_name='members')
    op.drop_index(op.f('ix_members_nrc'), table_name='members')
    op.drop_index(op.f('ix_members_name'), table_name='members')
    op.drop_index(op.f('ix_members_id'), table_name='members')
    op.drop_table('members')
    
    op.drop_index(op.f('ix_form_metadata_id'), table_name='form_metadata')
    op.drop_table('form_metadata')
    
    op.drop_index(op.f('ix_wards_name'), table_name='wards')
    op.drop_index(op.f('ix_wards_id'), table_name='wards')
    op.drop_table('wards')
    
    op.drop_index(op.f('ix_districts_name'), table_name='districts')
    op.drop_index(op.f('ix_districts_id'), table_name='districts')
    op.drop_table('districts')
    
    op.drop_index(op.f('ix_provinces_name'), table_name='provinces')
    op.drop_index(op.f('ix_provinces_id'), table_name='provinces')
    op.drop_table('provinces')
    
    # Drop enum type
    sa.Enum(name='genderenum').drop(op.get_bind(), checkfirst=True)
