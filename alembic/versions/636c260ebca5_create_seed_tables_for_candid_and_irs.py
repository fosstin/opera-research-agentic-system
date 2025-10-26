"""create_seed_tables_for_candid_and_irs

Revision ID: 636c260ebca5
Revises: 28f497fc7f2a
Create Date: 2025-10-26 13:48:28.342055

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '636c260ebca5'
down_revision: Union[str, Sequence[str], None] = '28f497fc7f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create seed tables for external data sources (Candid, IRS, etc.)."""

    # Table: seed_candid_nonprofits
    op.create_table(
        'seed_candid_nonprofits',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ein', sa.String(9), unique=True, nullable=False),
        sa.Column('legal_name', sa.Text(), nullable=False),
        sa.Column('dba_names', sa.Text()),  # JSON array as text
        sa.Column('ntee_code', sa.String(10)),
        sa.Column('city', sa.String()),
        sa.Column('state', sa.String(2)),
        sa.Column('zip', sa.String(10)),
        sa.Column('revenue', sa.Numeric(15, 2)),
        sa.Column('expenses', sa.Numeric(15, 2)),
        sa.Column('assets', sa.Numeric(15, 2)),
        sa.Column('mission', sa.Text()),
        sa.Column('website', sa.String()),
        sa.Column('phone', sa.String(20)),
        sa.Column('fiscal_year_end', sa.String(10)),
        sa.Column('api_response', JSONB()),
        sa.Column('loaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

    op.create_index('idx_candid_ein', 'seed_candid_nonprofits', ['ein'], unique=True)
    op.create_index('idx_candid_ntee', 'seed_candid_nonprofits', ['ntee_code'])
    op.create_index('idx_candid_state', 'seed_candid_nonprofits', ['state'])

    # Table: seed_irs_990_filings
    op.create_table(
        'seed_irs_990_filings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ein', sa.String(9), nullable=False),
        sa.Column('tax_year', sa.Integer(), nullable=False),
        sa.Column('organization_name', sa.Text()),
        sa.Column('form_type', sa.String(10)),  # 990, 990EZ, 990PF
        sa.Column('revenue', sa.Numeric(15, 2)),
        sa.Column('expenses', sa.Numeric(15, 2)),
        sa.Column('assets', sa.Numeric(15, 2)),
        sa.Column('executive_compensation', JSONB()),
        sa.Column('program_service_revenue', sa.Numeric(15, 2)),
        sa.Column('xml_url', sa.String()),
        sa.Column('json_data', JSONB()),
        sa.Column('loaded_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now())
    )

    op.create_index('idx_irs_ein', 'seed_irs_990_filings', ['ein'])
    op.create_index('idx_irs_tax_year', 'seed_irs_990_filings', ['tax_year'])
    op.create_index('idx_irs_ein_year', 'seed_irs_990_filings', ['ein', 'tax_year'], unique=True)

    # Table: seed_company_websites
    op.create_table(
        'seed_company_websites',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_name', sa.Text(), nullable=False),
        sa.Column('website_url', sa.String(), nullable=False),
        sa.Column('season_page_url', sa.String()),
        sa.Column('ein', sa.String(9)),
        sa.Column('candid_match_id', UUID(as_uuid=True)),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('last_verified', sa.TIMESTAMP(timezone=True)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    op.create_index('idx_websites_ein', 'seed_company_websites', ['ein'])
    op.create_index('idx_websites_url', 'seed_company_websites', ['website_url'])


def downgrade() -> None:
    """Drop seed tables."""
    op.drop_table('seed_company_websites')
    op.drop_table('seed_irs_990_filings')
    op.drop_table('seed_candid_nonprofits')
