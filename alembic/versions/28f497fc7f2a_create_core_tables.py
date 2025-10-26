"""create_core_tables

Revision ID: 28f497fc7f2a
Revises: 4e0bc941d1d5
Create Date: 2025-10-25 20:54:32.191402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '28f497fc7f2a'
down_revision: Union[str, Sequence[str], None] = '4e0bc941d1d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core layer tables for normalized opera production data."""

    # Table: companies
    op.create_table(
        'companies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('name_native', sa.String()),
        sa.Column('slug', sa.String(), unique=True, nullable=False),
        # Location
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('country_code', sa.String(2)),
        sa.Column('region', sa.String()),
        sa.Column('latitude', sa.Numeric(9, 6)),
        sa.Column('longitude', sa.Numeric(9, 6)),
        # Classification
        sa.Column('tier', sa.String()),
        sa.Column('company_type', sa.String()),
        # Venue
        sa.Column('primary_venue_name', sa.String()),
        sa.Column('venue_capacity', sa.Integer()),
        sa.Column('additional_venues', JSONB()),
        # Contact & Web
        sa.Column('website_url', sa.String(), unique=True, nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('social_media', JSONB()),
        sa.Column('contact_email', sa.String()),
        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('founded_year', sa.Integer()),
        sa.Column('closed_year', sa.Integer()),
        # Metadata
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('data_quality_score', sa.Numeric(3, 2)),
        sa.Column('notes', sa.Text())
    )

    op.create_index('idx_companies_slug', 'companies', ['slug'], unique=True)
    op.create_index('idx_companies_country', 'companies', ['country'])
    op.create_index('idx_companies_tier', 'companies', ['tier'])
    op.create_index('idx_companies_is_active', 'companies', ['is_active'])

    # Table: opera_works
    op.create_table(
        'opera_works',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('title_native', sa.String()),
        sa.Column('slug', sa.String(), unique=True, nullable=False),
        # Composition
        sa.Column('composer', sa.String(), nullable=False),
        sa.Column('librettist', sa.String()),
        sa.Column('language', sa.String()),
        # Classification
        sa.Column('genre', sa.String()),
        sa.Column('period', sa.String()),
        sa.Column('acts', sa.Integer()),
        sa.Column('approximate_duration_minutes', sa.Integer()),
        # History
        sa.Column('premiere_date', sa.Date()),
        sa.Column('premiere_venue', sa.String()),
        sa.Column('premiere_city', sa.String()),
        # External IDs
        sa.Column('musicbrainz_id', UUID(as_uuid=True)),
        sa.Column('wikidata_id', sa.String()),
        sa.Column('imslp_id', sa.String()),
        # Metadata
        sa.Column('synopsis', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    op.create_index('idx_opera_works_slug', 'opera_works', ['slug'], unique=True)
    op.create_index('idx_opera_works_composer', 'opera_works', ['composer'])
    op.create_index('idx_opera_works_genre', 'opera_works', ['genre'])

    # Table: seasons
    op.create_table(
        'seasons',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('season_name', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        # Metadata
        sa.Column('is_current', sa.Boolean(), default=False),
        sa.Column('theme', sa.String()),
        sa.Column('artistic_director', sa.String()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    op.create_index('idx_seasons_company', 'seasons', ['company_id'])
    op.create_index('idx_seasons_dates', 'seasons', ['start_date', 'end_date'])
    op.create_index('idx_seasons_is_current', 'seasons', ['is_current'])

    # Table: performers
    op.create_table(
        'performers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), unique=True, nullable=False),
        # Performer Details
        sa.Column('birth_name', sa.String()),
        sa.Column('birth_date', sa.Date()),
        sa.Column('birth_country', sa.String()),
        sa.Column('nationality', sa.String()),
        # Classification
        sa.Column('performer_type', sa.String()),
        sa.Column('voice_type', sa.String()),
        sa.Column('voice_subtype', sa.String()),
        # Career
        sa.Column('career_start_year', sa.Integer()),
        sa.Column('career_end_year', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), default=True),
        # External IDs
        sa.Column('musicbrainz_id', UUID(as_uuid=True)),
        sa.Column('wikidata_id', sa.String()),
        sa.Column('operabase_id', sa.String()),
        # Contact
        sa.Column('website_url', sa.String()),
        sa.Column('agency', sa.String()),
        sa.Column('social_media', JSONB()),
        # Bio
        sa.Column('biography', sa.Text()),
        sa.Column('awards', JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    op.create_index('idx_performers_slug', 'performers', ['slug'], unique=True)
    op.create_index('idx_performers_voice_type', 'performers', ['voice_type'])
    op.create_index('idx_performers_is_active', 'performers', ['is_active'])

    # Table: productions
    op.create_table(
        'productions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('opera_work_id', UUID(as_uuid=True), sa.ForeignKey('opera_works.id'), nullable=False),
        sa.Column('season_id', UUID(as_uuid=True), sa.ForeignKey('seasons.id')),
        # Production Details
        sa.Column('production_title', sa.String()),
        sa.Column('production_type', sa.String()),
        sa.Column('language', sa.String()),
        # Creative Team
        sa.Column('conductor', sa.String()),
        sa.Column('director', sa.String()),
        sa.Column('set_designer', sa.String()),
        sa.Column('costume_designer', sa.String()),
        sa.Column('lighting_designer', sa.String()),
        sa.Column('choreographer', sa.String()),
        sa.Column('creative_team', JSONB()),
        # Schedule
        sa.Column('premiere_date', sa.Date(), nullable=False),
        sa.Column('closing_date', sa.Date()),
        sa.Column('total_performances', sa.Integer()),
        # Venue
        sa.Column('venue_name', sa.String()),
        sa.Column('venue_capacity', sa.Integer()),
        # Financial
        sa.Column('estimated_production_budget', sa.Numeric(12, 2)),
        sa.Column('budget_currency', sa.String(3)),
        sa.Column('estimated_total_revenue', sa.Numeric(12, 2)),
        # Ticket Pricing
        sa.Column('ticket_price_min', sa.Numeric(8, 2)),
        sa.Column('ticket_price_max', sa.Numeric(8, 2)),
        sa.Column('ticket_price_currency', sa.String(3)),
        # Additional Data
        sa.Column('is_premiere', sa.Boolean(), default=False),
        sa.Column('co_production_partners', JSONB()),
        sa.Column('production_photos_url', sa.String()),
        sa.Column('trailer_url', sa.String()),
        # Metadata
        sa.Column('source_url', sa.String()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('data_quality_score', sa.Numeric(3, 2))
    )

    op.create_index('idx_productions_company', 'productions', ['company_id'])
    op.create_index('idx_productions_opera_work', 'productions', ['opera_work_id'])
    op.create_index('idx_productions_season', 'productions', ['season_id'])
    op.create_index('idx_productions_premiere_date', 'productions', ['premiere_date'])

    # Table: performances
    op.create_table(
        'performances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('production_id', UUID(as_uuid=True), sa.ForeignKey('productions.id'), nullable=False),
        # Performance Details
        sa.Column('performance_date', sa.Date(), nullable=False),
        sa.Column('performance_datetime', sa.TIMESTAMP(timezone=True)),
        # Type
        sa.Column('performance_type', sa.String()),
        sa.Column('is_livestream', sa.Boolean(), default=False),
        sa.Column('is_broadcast', sa.Boolean(), default=False),
        # Cast
        sa.Column('cast_note', sa.String()),
        # Ticketing
        sa.Column('tickets_sold', sa.Integer()),
        sa.Column('capacity', sa.Integer()),
        sa.Column('attendance_percentage', sa.Numeric(5, 2)),
        sa.Column('box_office_revenue', sa.Numeric(10, 2)),
        sa.Column('revenue_currency', sa.String(3)),
        # Status
        sa.Column('is_cancelled', sa.Boolean(), default=False),
        sa.Column('cancellation_reason', sa.String()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    op.create_index('idx_performances_production', 'performances', ['production_id'])
    op.create_index('idx_performances_date', 'performances', ['performance_date'])

    # Table: cast_assignments
    op.create_table(
        'cast_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('production_id', UUID(as_uuid=True), sa.ForeignKey('productions.id'), nullable=False),
        sa.Column('performance_id', UUID(as_uuid=True), sa.ForeignKey('performances.id')),
        sa.Column('performer_id', UUID(as_uuid=True), sa.ForeignKey('performers.id'), nullable=False),
        # Role Details
        sa.Column('role_name', sa.String(), nullable=False),
        sa.Column('role_type', sa.String()),
        sa.Column('voice_type', sa.String()),
        # Assignment Details
        sa.Column('is_understudy', sa.Boolean(), default=False),
        sa.Column('is_debut', sa.Boolean(), default=False),
        sa.Column('is_cover', sa.Boolean(), default=False),
        # Dates
        sa.Column('performance_dates', JSONB()),
        # Financial
        sa.Column('estimated_fee', sa.Numeric(10, 2)),
        sa.Column('fee_currency', sa.String(3)),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    op.create_index('idx_cast_assignments_production', 'cast_assignments', ['production_id'])
    op.create_index('idx_cast_assignments_performer', 'cast_assignments', ['performer_id'])
    op.create_index('idx_cast_assignments_role', 'cast_assignments', ['role_name'])


def downgrade() -> None:
    """Drop core layer tables."""
    op.drop_table('cast_assignments')
    op.drop_table('performances')
    op.drop_table('productions')
    op.drop_table('performers')
    op.drop_table('seasons')
    op.drop_table('opera_works')
    op.drop_table('companies')
