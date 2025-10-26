"""create_staging_tables

Revision ID: 4e0bc941d1d5
Revises:
Create Date: 2025-10-25 20:53:05.870275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '4e0bc941d1d5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create staging layer tables for raw scraped data."""

    # Table: stg_scraped_pages
    op.create_table(
        'stg_scraped_pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(), nullable=False),
        sa.Column('company_name', sa.String()),
        sa.Column('html_content', sa.Text()),
        sa.Column('text_content', sa.Text()),
        sa.Column('page_title', sa.String()),
        sa.Column('status_code', sa.Integer()),
        sa.Column('content_type', sa.String()),
        sa.Column('content_length', sa.Integer()),
        sa.Column('http_headers', JSONB()),
        sa.Column('scraped_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('scraper_version', sa.String()),
        sa.Column('user_agent', sa.String()),
        sa.Column('is_processed', sa.Boolean(), default=False),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('processing_error', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('cache_key', sa.String()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('is_valid_html', sa.Boolean()),
        sa.Column('parsing_errors', JSONB()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Indexes for stg_scraped_pages
    op.create_index('idx_scraped_pages_url', 'stg_scraped_pages', ['url'], unique=True)
    op.create_index('idx_scraped_pages_domain', 'stg_scraped_pages', ['domain'])
    op.create_index('idx_scraped_pages_processed', 'stg_scraped_pages', ['is_processed'])
    op.create_index('idx_scraped_pages_scraped_at', 'stg_scraped_pages', ['scraped_at'])

    # Table: stg_llm_extractions
    op.create_table(
        'stg_llm_extractions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('scraped_page_id', UUID(as_uuid=True), sa.ForeignKey('stg_scraped_pages.id'), nullable=False),
        sa.Column('extraction_type', sa.String(), nullable=False),
        sa.Column('schema_version', sa.String()),
        sa.Column('raw_response', JSONB(), nullable=False),
        sa.Column('parsed_data', JSONB()),
        sa.Column('llm_model', sa.String(), nullable=False),
        sa.Column('llm_provider', sa.String(), nullable=False),
        sa.Column('prompt_template', sa.Text()),
        sa.Column('prompt_version', sa.String()),
        sa.Column('tokens_input', sa.Integer()),
        sa.Column('tokens_output', sa.Integer()),
        sa.Column('tokens_total', sa.Integer()),
        sa.Column('estimated_cost_usd', sa.Numeric(10, 6)),
        sa.Column('confidence_score', sa.Numeric(3, 2)),
        sa.Column('extraction_quality', sa.String()),
        sa.Column('validation_errors', JSONB()),
        sa.Column('extracted_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('processing_time_seconds', sa.Numeric(8, 3)),
        sa.Column('is_validated', sa.Boolean(), default=False),
        sa.Column('validated_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('validated_by', sa.String()),
        sa.Column('is_loaded_to_core', sa.Boolean(), default=False),
        sa.Column('loaded_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('core_entity_id', UUID(as_uuid=True)),
        sa.Column('extraction_error', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Indexes for stg_llm_extractions
    op.create_index('idx_llm_extractions_page', 'stg_llm_extractions', ['scraped_page_id'])
    op.create_index('idx_llm_extractions_type', 'stg_llm_extractions', ['extraction_type'])
    op.create_index('idx_llm_extractions_validated', 'stg_llm_extractions', ['is_validated'])
    op.create_index('idx_llm_extractions_loaded', 'stg_llm_extractions', ['is_loaded_to_core'])

    # Table: stg_scrape_logs
    op.create_table(
        'stg_scrape_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('domain', sa.String()),
        sa.Column('http_method', sa.String(), default='GET'),
        sa.Column('status_code', sa.Integer()),
        sa.Column('response_time_ms', sa.Integer()),
        sa.Column('content_length', sa.Integer()),
        sa.Column('is_success', sa.Boolean(), nullable=False),
        sa.Column('error_type', sa.String()),
        sa.Column('error_message', sa.Text()),
        sa.Column('robots_txt_allowed', sa.Boolean()),
        sa.Column('rate_limit_wait_ms', sa.Integer()),
        sa.Column('used_cache', sa.Boolean(), default=False),
        sa.Column('scraped_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('scraper_version', sa.String()),
        sa.Column('user_agent', sa.String()),
        sa.Column('ip_address', sa.String()),
        sa.Column('batch_id', UUID(as_uuid=True)),
        sa.Column('batch_name', sa.String())
    )

    # Indexes for stg_scrape_logs
    op.create_index('idx_scrape_logs_url', 'stg_scrape_logs', ['url'])
    op.create_index('idx_scrape_logs_scraped_at', 'stg_scrape_logs', ['scraped_at'])
    op.create_index('idx_scrape_logs_success', 'stg_scrape_logs', ['is_success'])
    op.create_index('idx_scrape_logs_batch', 'stg_scrape_logs', ['batch_id'])

    # Table: stg_extraction_logs
    op.create_table(
        'stg_extraction_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('scraped_page_id', UUID(as_uuid=True), sa.ForeignKey('stg_scraped_pages.id')),
        sa.Column('llm_extraction_id', UUID(as_uuid=True), sa.ForeignKey('stg_llm_extractions.id')),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('is_success', sa.Boolean(), nullable=False),
        sa.Column('llm_model', sa.String()),
        sa.Column('llm_provider', sa.String()),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('cost_usd', sa.Numeric(10, 6)),
        sa.Column('response_time_seconds', sa.Numeric(8, 3)),
        sa.Column('error_type', sa.String()),
        sa.Column('error_message', sa.Text()),
        sa.Column('performed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('performed_by', sa.String()),
        sa.Column('notes', sa.Text()),
        sa.Column('metadata', JSONB())
    )

    # Indexes for stg_extraction_logs
    op.create_index('idx_extraction_logs_page', 'stg_extraction_logs', ['scraped_page_id'])
    op.create_index('idx_extraction_logs_extraction', 'stg_extraction_logs', ['llm_extraction_id'])
    op.create_index('idx_extraction_logs_performed_at', 'stg_extraction_logs', ['performed_at'])


def downgrade() -> None:
    """Drop staging layer tables."""
    op.drop_table('stg_extraction_logs')
    op.drop_table('stg_scrape_logs')
    op.drop_table('stg_llm_extractions')
    op.drop_table('stg_scraped_pages')
