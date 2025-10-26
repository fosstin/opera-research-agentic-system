"""
SQLAlchemy ORM models for the Opera Research platform.

Maps to the PostgreSQL schema defined in DATABASE_SCHEMA.md.
These models correspond to the CORE layer tables.

Architecture layers:
- Staging: Raw scraped data (not modeled in ORM)
- Core: Normalized entities (THIS FILE)
- Analytics: dbt-generated marts (read-only, not in ORM)
"""

from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, Numeric, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .connectors import Base


class Company(Base):
    """Opera companies and houses."""
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    name_native = Column(String)
    slug = Column(String, unique=True, nullable=False)

    # Location
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)
    country_code = Column(String(2))
    region = Column(String)
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))

    # Classification
    tier = Column(String)
    company_type = Column(String)

    # Venue
    primary_venue_name = Column(String)
    venue_capacity = Column(Integer)
    additional_venues = Column(JSONB)

    # Contact & Web
    website_url = Column(String, unique=True, nullable=False)
    domain = Column(String, nullable=False)
    social_media = Column(JSONB)
    contact_email = Column(String)

    # Status
    is_active = Column(Boolean, default=True)
    founded_year = Column(Integer)
    closed_year = Column(Integer)

    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    data_quality_score = Column(Numeric(3, 2))
    notes = Column(Text)

    # Relationships
    productions = relationship("Production", back_populates="company")
    seasons = relationship("Season", back_populates="company")


class OperaWork(Base):
    """Catalog of operas (the works themselves)."""
    __tablename__ = "opera_works"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    title_native = Column(String)
    slug = Column(String, unique=True, nullable=False)

    # Composition
    composer = Column(String, nullable=False)
    librettist = Column(String)
    language = Column(String)

    # Classification
    genre = Column(String)
    period = Column(String)
    acts = Column(Integer)
    approximate_duration_minutes = Column(Integer)

    # History
    premiere_date = Column(Date)
    premiere_venue = Column(String)
    premiere_city = Column(String)

    # External IDs
    musicbrainz_id = Column(UUID(as_uuid=True))
    wikidata_id = Column(String)
    imslp_id = Column(String)

    # Metadata
    synopsis = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    productions = relationship("Production", back_populates="opera_work")


class Season(Base):
    """Opera seasons."""
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    season_name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Metadata
    is_current = Column(Boolean, default=False)
    theme = Column(String)
    artistic_director = Column(String)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="seasons")
    productions = relationship("Production", back_populates="season")


class Production(Base):
    """Specific productions (a company's staging of an opera)."""
    __tablename__ = "productions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    opera_work_id = Column(UUID(as_uuid=True), ForeignKey("opera_works.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"))

    # Production Details
    production_title = Column(String)
    production_type = Column(String)
    language = Column(String)

    # Creative Team
    conductor = Column(String)
    director = Column(String)
    set_designer = Column(String)
    costume_designer = Column(String)
    lighting_designer = Column(String)
    choreographer = Column(String)
    creative_team = Column(JSONB)

    # Schedule
    premiere_date = Column(Date, nullable=False)
    closing_date = Column(Date)
    total_performances = Column(Integer)

    # Venue
    venue_name = Column(String)
    venue_capacity = Column(Integer)

    # Financial
    estimated_production_budget = Column(Numeric(12, 2))
    budget_currency = Column(String(3))
    estimated_total_revenue = Column(Numeric(12, 2))

    # Ticket Pricing
    ticket_price_min = Column(Numeric(8, 2))
    ticket_price_max = Column(Numeric(8, 2))
    ticket_price_currency = Column(String(3))

    # Additional Data
    is_premiere = Column(Boolean, default=False)
    co_production_partners = Column(JSONB)
    production_photos_url = Column(String)
    trailer_url = Column(String)

    # Metadata
    source_url = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    data_quality_score = Column(Numeric(3, 2))

    # Relationships
    company = relationship("Company", back_populates="productions")
    opera_work = relationship("OperaWork", back_populates="productions")
    season = relationship("Season", back_populates="productions")
    performances = relationship("Performance", back_populates="production")
    cast_assignments = relationship("CastAssignment", back_populates="production")


class Performance(Base):
    """Individual performance events."""
    __tablename__ = "performances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_id = Column(UUID(as_uuid=True), ForeignKey("productions.id"), nullable=False)

    # Performance Details
    performance_date = Column(Date, nullable=False)
    performance_datetime = Column(TIMESTAMP(timezone=True))

    # Type
    performance_type = Column(String)
    is_livestream = Column(Boolean, default=False)
    is_broadcast = Column(Boolean, default=False)

    # Cast
    cast_note = Column(String)

    # Ticketing
    tickets_sold = Column(Integer)
    capacity = Column(Integer)
    attendance_percentage = Column(Numeric(5, 2))
    box_office_revenue = Column(Numeric(10, 2))
    revenue_currency = Column(String(3))

    # Status
    is_cancelled = Column(Boolean, default=False)
    cancellation_reason = Column(String)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    production = relationship("Production", back_populates="performances")


class Performer(Base):
    """Individual performers (singers, conductors, directors, etc.)."""
    __tablename__ = "performers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)

    # Performer Details
    birth_name = Column(String)
    birth_date = Column(Date)
    birth_country = Column(String)
    nationality = Column(String)

    # Classification
    performer_type = Column(String)
    voice_type = Column(String)
    voice_subtype = Column(String)

    # Career
    career_start_year = Column(Integer)
    career_end_year = Column(Integer)
    is_active = Column(Boolean, default=True)

    # External IDs
    musicbrainz_id = Column(UUID(as_uuid=True))
    wikidata_id = Column(String)
    operabase_id = Column(String)

    # Contact
    website_url = Column(String)
    agency = Column(String)
    social_media = Column(JSONB)

    # Bio
    biography = Column(Text)
    awards = Column(JSONB)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    cast_assignments = relationship("CastAssignment", back_populates="performer")


class CastAssignment(Base):
    """Links performers to productions/performances."""
    __tablename__ = "cast_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    production_id = Column(UUID(as_uuid=True), ForeignKey("productions.id"), nullable=False)
    performance_id = Column(UUID(as_uuid=True), ForeignKey("performances.id"))
    performer_id = Column(UUID(as_uuid=True), ForeignKey("performers.id"), nullable=False)

    # Role Details
    role_name = Column(String, nullable=False)
    role_type = Column(String)
    voice_type = Column(String)

    # Assignment Details
    is_understudy = Column(Boolean, default=False)
    is_debut = Column(Boolean, default=False)
    is_cover = Column(Boolean, default=False)

    # Dates
    performance_dates = Column(JSONB)

    # Financial
    estimated_fee = Column(Numeric(10, 2))
    fee_currency = Column(String(3))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    production = relationship("Production", back_populates="cast_assignments")
    performer = relationship("Performer", back_populates="cast_assignments")
