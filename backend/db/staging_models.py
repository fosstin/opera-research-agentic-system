"""
SQLAlchemy ORM models for STAGING layer tables.

These tables store raw scraped HTML and LLM extraction results
before they are transformed and loaded into the core layer.

Staging layer follows ELT pattern:
1. Extract: Scrape HTML
2. Load: Insert raw HTML into stg_scraped_pages
3. Transform: Process with LLM → stg_llm_extractions → dbt → core tables
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Numeric, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .connectors import Base


class ScrapedPage(Base):
    """Raw HTML scraped from opera company websites."""
    __tablename__ = "stg_scraped_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # URL and Source
    url = Column(Text, nullable=False, unique=True)
    domain = Column(String, nullable=False)
    company_name = Column(String)  # Optional hint for which company

    # Content
    html_content = Column(Text)
    text_content = Column(Text)  # Extracted plain text for LLM processing
    page_title = Column(String)

    # HTTP Response Metadata
    status_code = Column(Integer)
    content_type = Column(String)
    content_length = Column(Integer)
    http_headers = Column(JSONB)

    # Scraping Metadata
    scraped_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    scraper_version = Column(String)
    user_agent = Column(String)

    # Processing Status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(TIMESTAMP(timezone=True))
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)

    # Cache Control
    cache_key = Column(String, unique=True)
    expires_at = Column(TIMESTAMP(timezone=True))

    # Data Quality
    is_valid_html = Column(Boolean)
    parsing_errors = Column(JSONB)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    llm_extractions = relationship("LLMExtraction", back_populates="scraped_page")


class LLMExtraction(Base):
    """Structured data extracted from HTML using LLM."""
    __tablename__ = "stg_llm_extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scraped_page_id = Column(UUID(as_uuid=True), ForeignKey("stg_scraped_pages.id"), nullable=False)

    # Extraction Context
    extraction_type = Column(String, nullable=False)  # e.g., "production", "season", "company_info"
    schema_version = Column(String)  # Track schema changes over time

    # LLM Response
    raw_response = Column(JSONB, nullable=False)  # Full JSON response from LLM
    parsed_data = Column(JSONB)  # Validated and cleaned data

    # LLM Metadata
    llm_model = Column(String, nullable=False)  # e.g., "gpt-4-turbo-preview", "gemini-pro"
    llm_provider = Column(String, nullable=False)  # e.g., "openai", "google"
    prompt_template = Column(Text)  # The prompt used
    prompt_version = Column(String)

    # Cost Tracking
    tokens_input = Column(Integer)
    tokens_output = Column(Integer)
    tokens_total = Column(Integer)
    estimated_cost_usd = Column(Numeric(10, 6))

    # Quality Metrics
    confidence_score = Column(Numeric(3, 2))  # 0.00 to 1.00
    extraction_quality = Column(String)  # "high", "medium", "low"
    validation_errors = Column(JSONB)

    # Processing Metadata
    extracted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processing_time_seconds = Column(Numeric(8, 3))

    # Validation & Status
    is_validated = Column(Boolean, default=False)
    validated_at = Column(TIMESTAMP(timezone=True))
    validated_by = Column(String)  # "auto" or user identifier

    is_loaded_to_core = Column(Boolean, default=False)
    loaded_at = Column(TIMESTAMP(timezone=True))
    core_entity_id = Column(UUID(as_uuid=True))  # Reference to core table record

    # Error Handling
    extraction_error = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    scraped_page = relationship("ScrapedPage", back_populates="llm_extractions")


class ScrapeLog(Base):
    """Audit log for all scraping operations."""
    __tablename__ = "stg_scrape_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request Details
    url = Column(Text, nullable=False)
    domain = Column(String)
    http_method = Column(String, default="GET")

    # Response
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    content_length = Column(Integer)

    # Success/Failure
    is_success = Column(Boolean, nullable=False)
    error_type = Column(String)  # "timeout", "404", "rate_limit", "robots_txt_blocked", etc.
    error_message = Column(Text)

    # Compliance
    robots_txt_allowed = Column(Boolean)
    rate_limit_wait_ms = Column(Integer)
    used_cache = Column(Boolean, default=False)

    # Metadata
    scraped_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    scraper_version = Column(String)
    user_agent = Column(String)
    ip_address = Column(String)

    # Batch Tracking
    batch_id = Column(UUID(as_uuid=True))
    batch_name = Column(String)


class ExtractionLog(Base):
    """Audit log for LLM extraction operations."""
    __tablename__ = "stg_extraction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference
    scraped_page_id = Column(UUID(as_uuid=True), ForeignKey("stg_scraped_pages.id"))
    llm_extraction_id = Column(UUID(as_uuid=True), ForeignKey("stg_llm_extractions.id"))

    # Operation
    operation_type = Column(String, nullable=False)  # "extract", "validate", "retry", "manual_review"
    is_success = Column(Boolean, nullable=False)

    # LLM Call Details
    llm_model = Column(String)
    llm_provider = Column(String)
    tokens_used = Column(Integer)
    cost_usd = Column(Numeric(10, 6))
    response_time_seconds = Column(Numeric(8, 3))

    # Error Handling
    error_type = Column(String)
    error_message = Column(Text)

    # Metadata
    performed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    performed_by = Column(String)  # "system" or user identifier

    # Additional Context
    notes = Column(Text)
    metadata = Column(JSONB)
