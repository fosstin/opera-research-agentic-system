# Opera Research Database Schema

Complete PostgreSQL database schema for opera production metadata with ETL/ELT pipeline integration.

## Architecture Philosophy

**ELT Approach (Extract, Load, Transform):**
```
Raw HTML → LLM Extraction → Staging Tables → dbt Transformations → Analytics Tables → Tableau
```

**Why ELT over ETL:**
- Load raw/semi-structured data quickly
- Transform in-database using SQL (fast)
- Version control transformations with dbt
- Easy to reprocess and iterate
- Leverage PostgreSQL's power

---

## Schema Layers

### Layer 1: Staging (Raw Ingestion)
Semi-structured data loaded directly from extraction

### Layer 2: Core (Normalized Business Entities)
Clean, validated, normalized data

### Layer 3: Analytics (Aggregates & Marts)
dbt-built tables optimized for querying and visualization

---

## Complete Schema

### STAGING LAYER

#### `stg_scraped_pages`
Raw HTML storage and metadata

```sql
CREATE TABLE stg_scraped_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT NOT NULL,
    company_domain TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    html_content TEXT,
    status_code INTEGER,
    response_headers JSONB,
    page_type TEXT, -- 'season', 'production', 'cast', 'about', etc.
    scraper_version TEXT,
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    checksum TEXT, -- MD5 of content for change detection
    UNIQUE(url, scraped_at)
);

CREATE INDEX idx_scraped_pages_company ON stg_scraped_pages(company_domain);
CREATE INDEX idx_scraped_pages_processed ON stg_scraped_pages(is_processed);
CREATE INDEX idx_scraped_pages_type ON stg_scraped_pages(page_type);
```

#### `stg_llm_extractions`
Raw LLM extraction output (JSONB)

```sql
CREATE TABLE stg_llm_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scraped_page_id UUID REFERENCES stg_scraped_pages(id),
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    extraction_prompt TEXT,
    llm_model TEXT, -- 'gpt-4', 'gemini-pro', etc.
    raw_response JSONB NOT NULL, -- Full structured extraction
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    extraction_version TEXT,
    validation_errors JSONB, -- Array of validation issues
    is_validated BOOLEAN DEFAULT FALSE,
    UNIQUE(scraped_page_id, extraction_version)
);

CREATE INDEX idx_llm_extractions_page ON stg_llm_extractions(scraped_page_id);
CREATE INDEX idx_llm_extractions_validated ON stg_llm_extractions(is_validated);
```

---

### CORE LAYER

#### `companies`
Opera houses and companies

```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    name_native TEXT, -- Local language name
    slug TEXT UNIQUE NOT NULL, -- URL-friendly: 'metropolitan-opera'

    -- Location
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    country_code CHAR(2), -- ISO 3166-1 alpha-2
    region TEXT, -- 'North America', 'Europe', 'Asia', etc.
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),

    -- Classification
    tier TEXT CHECK (tier IN ('tier-1', 'tier-2', 'tier-3', 'regional', 'festival')),
    company_type TEXT, -- 'resident', 'festival', 'touring', etc.

    -- Venue
    primary_venue_name TEXT,
    venue_capacity INTEGER,
    additional_venues JSONB, -- Array of other venues used

    -- Contact & Web
    website_url TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL, -- Extracted domain for scraping
    social_media JSONB, -- {twitter, instagram, facebook, etc.}
    contact_email TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    founded_year INTEGER,
    closed_year INTEGER,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_quality_score DECIMAL(3,2), -- 0.00 to 1.00
    notes TEXT
);

CREATE INDEX idx_companies_country ON companies(country);
CREATE INDEX idx_companies_tier ON companies(tier);
CREATE INDEX idx_companies_active ON companies(is_active);
CREATE INDEX idx_companies_domain ON companies(domain);

-- GIS support (install PostGIS extension first)
-- CREATE INDEX idx_companies_location ON companies USING GIST(geography(point(longitude, latitude)));
```

#### `opera_works`
Catalog of operas (the works themselves)

```sql
CREATE TABLE opera_works (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    title_native TEXT, -- Original language title
    slug TEXT UNIQUE NOT NULL,

    -- Composition
    composer TEXT NOT NULL,
    librettist TEXT,
    language TEXT, -- Primary language

    -- Classification
    genre TEXT, -- 'opera seria', 'opera buffa', 'grand opera', etc.
    period TEXT, -- 'baroque', 'classical', 'romantic', 'modern', 'contemporary'
    acts INTEGER,
    approximate_duration_minutes INTEGER,

    -- History
    premiere_date DATE,
    premiere_venue TEXT,
    premiere_city TEXT,

    -- Metadata
    synopsis TEXT,
    musicbrainz_id UUID, -- Link to MusicBrainz
    wikidata_id TEXT, -- Link to Wikidata
    imslp_id TEXT, -- Link to IMSLP

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_opera_works_composer ON opera_works(composer);
CREATE INDEX idx_opera_works_period ON opera_works(period);
CREATE INDEX idx_opera_works_premiere ON opera_works(premiere_date);
CREATE UNIQUE INDEX idx_opera_works_title_composer ON opera_works(title, composer);
```

#### `seasons`
Opera seasons

```sql
CREATE TABLE seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    season_name TEXT NOT NULL, -- '2024-25', '2025'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Metadata
    is_current BOOLEAN DEFAULT FALSE,
    theme TEXT, -- Some seasons have themes
    artistic_director TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(company_id, season_name),
    CHECK (end_date > start_date)
);

CREATE INDEX idx_seasons_company ON seasons(company_id);
CREATE INDEX idx_seasons_current ON seasons(is_current);
CREATE INDEX idx_seasons_dates ON seasons(start_date, end_date);
```

#### `productions`
Specific productions (a company's staging of an opera)

```sql
CREATE TABLE productions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),
    opera_work_id UUID NOT NULL REFERENCES opera_works(id),
    season_id UUID REFERENCES seasons(id),

    -- Production Details
    production_title TEXT, -- Sometimes differs from work title
    production_type TEXT, -- 'new', 'revival', 'co-production', 'rental'
    language TEXT, -- Language performed in (may differ from original)

    -- Creative Team
    conductor TEXT,
    director TEXT,
    set_designer TEXT,
    costume_designer TEXT,
    lighting_designer TEXT,
    choreographer TEXT,
    creative_team JSONB, -- Full credits as JSON

    -- Schedule
    premiere_date DATE NOT NULL,
    closing_date DATE,
    total_performances INTEGER,

    -- Venue
    venue_name TEXT,
    venue_capacity INTEGER,

    -- Financial (estimates when not public)
    estimated_production_budget DECIMAL(12,2),
    budget_currency CHAR(3), -- ISO 4217 currency code
    estimated_total_revenue DECIMAL(12,2),

    -- Ticket Pricing
    ticket_price_min DECIMAL(8,2),
    ticket_price_max DECIMAL(8,2),
    ticket_price_currency CHAR(3),

    -- Additional Data
    is_premiere BOOLEAN DEFAULT FALSE, -- World/national premiere
    co_production_partners JSONB, -- Array of company IDs
    production_photos_url TEXT,
    trailer_url TEXT,

    -- Metadata
    source_url TEXT, -- Original scrape source
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data_quality_score DECIMAL(3,2)
);

CREATE INDEX idx_productions_company ON productions(company_id);
CREATE INDEX idx_productions_opera ON productions(opera_work_id);
CREATE INDEX idx_productions_season ON productions(season_id);
CREATE INDEX idx_productions_dates ON productions(premiere_date, closing_date);
CREATE INDEX idx_productions_conductor ON productions(conductor);
CREATE INDEX idx_productions_director ON productions(director);
```

#### `performances`
Individual performance events

```sql
CREATE TABLE performances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID NOT NULL REFERENCES productions(id),

    -- Performance Details
    performance_date DATE NOT NULL,
    performance_time TIME,
    performance_datetime TIMESTAMPTZ, -- Combined for convenience

    -- Type
    performance_type TEXT, -- 'regular', 'preview', 'opening_night', 'closing_night', 'gala', 'matinee'
    is_livestream BOOLEAN DEFAULT FALSE,
    is_broadcast BOOLEAN DEFAULT FALSE,

    -- Cast (references to cast_assignments)
    cast_note TEXT, -- 'Role debuts', 'Understudy performance', etc.

    -- Ticketing
    tickets_sold INTEGER,
    capacity INTEGER,
    attendance_percentage DECIMAL(5,2),
    box_office_revenue DECIMAL(10,2),
    revenue_currency CHAR(3),

    -- Status
    is_cancelled BOOLEAN DEFAULT FALSE,
    cancellation_reason TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(production_id, performance_datetime)
);

CREATE INDEX idx_performances_production ON performances(production_id);
CREATE INDEX idx_performances_date ON performances(performance_date);
CREATE INDEX idx_performances_type ON performances(performance_type);
```

#### `performers`
Individual performers (singers, conductors, directors, etc.)

```sql
CREATE TABLE performers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,

    -- Performer Details
    birth_name TEXT,
    birth_date DATE,
    birth_country TEXT,
    nationality TEXT,

    -- Classification
    performer_type TEXT, -- 'singer', 'conductor', 'director', 'designer', etc.
    voice_type TEXT, -- 'soprano', 'mezzo-soprano', 'tenor', 'baritone', 'bass'
    voice_subtype TEXT, -- 'coloratura', 'lyric', 'dramatic', 'spinto', etc.

    -- Career
    career_start_year INTEGER,
    career_end_year INTEGER,
    is_active BOOLEAN DEFAULT TRUE,

    -- External IDs
    musicbrainz_id UUID,
    wikidata_id TEXT,
    operabase_id TEXT,

    -- Contact
    website_url TEXT,
    agency TEXT,
    social_media JSONB,

    -- Bio
    biography TEXT,
    awards JSONB, -- Array of awards

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_performers_type ON performers(performer_type);
CREATE INDEX idx_performers_voice_type ON performers(voice_type);
CREATE INDEX idx_performers_active ON performers(is_active);
CREATE INDEX idx_performers_name ON performers(name);
CREATE INDEX idx_performers_slug ON performers(slug);
```

#### `cast_assignments`
Links performers to productions/performances

```sql
CREATE TABLE cast_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    production_id UUID NOT NULL REFERENCES productions(id),
    performance_id UUID REFERENCES performances(id), -- NULL if for all performances
    performer_id UUID NOT NULL REFERENCES performers(id),

    -- Role Details
    role_name TEXT NOT NULL, -- 'Don Giovanni', 'Violetta', etc.
    role_type TEXT, -- 'principal', 'comprimario', 'chorus', 'supernumerary'
    voice_type TEXT, -- Expected voice type for role

    -- Assignment Details
    is_understudy BOOLEAN DEFAULT FALSE,
    is_debut BOOLEAN DEFAULT FALSE, -- Role debut
    is_cover BOOLEAN DEFAULT FALSE,

    -- Dates (if performer doesn't do all performances)
    performance_dates JSONB, -- Array of specific dates if not all

    -- Financial (often not public)
    estimated_fee DECIMAL(10,2),
    fee_currency CHAR(3),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(production_id, performance_id, performer_id, role_name)
);

CREATE INDEX idx_cast_production ON cast_assignments(production_id);
CREATE INDEX idx_cast_performance ON cast_assignments(performance_id);
CREATE INDEX idx_cast_performer ON cast_assignments(performer_id);
CREATE INDEX idx_cast_role ON cast_assignments(role_name);
```

#### `financial_data`
Company-level financial information

```sql
CREATE TABLE financial_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),

    -- Period
    fiscal_year INTEGER NOT NULL,
    fiscal_period TEXT, -- 'annual', 'Q1', 'Q2', etc.
    period_start_date DATE,
    period_end_date DATE,

    -- Revenue
    total_revenue DECIMAL(14,2),
    ticket_revenue DECIMAL(14,2),
    subscription_revenue DECIMAL(14,2),
    donation_revenue DECIMAL(14,2),
    government_grants DECIMAL(14,2),
    corporate_sponsorship DECIMAL(14,2),
    endowment_income DECIMAL(14,2),
    other_revenue DECIMAL(14,2),

    -- Expenses
    total_expenses DECIMAL(14,2),
    artist_fees DECIMAL(14,2),
    production_costs DECIMAL(14,2),
    venue_costs DECIMAL(14,2),
    marketing_costs DECIMAL(14,2),
    administrative_costs DECIMAL(14,2),
    other_expenses DECIMAL(14,2),

    -- Currency
    currency CHAR(3) NOT NULL,

    -- Metrics
    net_income DECIMAL(14,2), -- revenue - expenses
    operating_margin DECIMAL(5,2), -- (net_income / total_revenue) * 100

    -- Source
    source_type TEXT, -- 'annual_report', 'tax_filing', 'press_release', 'estimated'
    source_url TEXT,
    is_estimated BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(company_id, fiscal_year, fiscal_period)
);

CREATE INDEX idx_financial_company ON financial_data(company_id);
CREATE INDEX idx_financial_year ON financial_data(fiscal_year);
```

---

### ANALYTICS LAYER (dbt Models)

These tables are built and maintained by dbt transformations.

#### `mart_production_summary`
Denormalized production data for analytics

```sql
-- This will be created by dbt
CREATE TABLE mart_production_summary AS
SELECT
    p.id AS production_id,
    c.name AS company_name,
    c.city,
    c.country,
    c.tier AS company_tier,
    ow.title AS opera_title,
    ow.composer,
    ow.period AS opera_period,
    s.season_name,
    p.premiere_date,
    p.closing_date,
    p.total_performances,
    p.conductor,
    p.director,
    p.ticket_price_min,
    p.ticket_price_max,
    p.estimated_production_budget,

    -- Aggregated metrics (from other tables)
    COUNT(DISTINCT ca.performer_id) AS total_cast_members,
    COUNT(DISTINCT perf.id) AS actual_performances,
    AVG(perf.attendance_percentage) AS avg_attendance,
    SUM(perf.box_office_revenue) AS total_box_office
FROM productions p
JOIN companies c ON p.company_id = c.id
JOIN opera_works ow ON p.opera_work_id = ow.id
LEFT JOIN seasons s ON p.season_id = s.id
LEFT JOIN cast_assignments ca ON p.id = ca.production_id
LEFT JOIN performances perf ON p.id = perf.production_id
GROUP BY p.id, c.name, c.city, c.country, c.tier,
         ow.title, ow.composer, ow.period, s.season_name,
         p.premiere_date, p.closing_date, p.total_performances,
         p.conductor, p.director, p.ticket_price_min,
         p.ticket_price_max, p.estimated_production_budget;
```

#### `mart_performer_career`
Performer career trajectory and statistics

```sql
-- Built by dbt
CREATE TABLE mart_performer_career AS
SELECT
    pf.id AS performer_id,
    pf.name,
    pf.voice_type,
    pf.nationality,

    -- Career metrics
    COUNT(DISTINCT ca.production_id) AS total_productions,
    COUNT(DISTINCT c.id) AS companies_performed_at,
    COUNT(DISTINCT c.country) AS countries_performed_in,
    MIN(p.premiere_date) AS career_first_performance,
    MAX(p.premiere_date) AS career_latest_performance,

    -- Role diversity
    COUNT(DISTINCT ca.role_name) AS unique_roles,
    COUNT(DISTINCT ow.composer) AS composers_performed,

    -- Prestige metrics
    COUNT(DISTINCT CASE WHEN c.tier = 'tier-1' THEN p.id END) AS tier1_productions,
    SUM(CASE WHEN ca.is_debut THEN 1 ELSE 0 END) AS role_debuts,

    -- Financial (when available)
    AVG(ca.estimated_fee) AS avg_fee,
    MAX(ca.estimated_fee) AS max_fee
FROM performers pf
LEFT JOIN cast_assignments ca ON pf.id = ca.performer_id
LEFT JOIN productions p ON ca.production_id = p.id
LEFT JOIN companies c ON p.company_id = c.id
LEFT JOIN opera_works ow ON p.opera_work_id = ow.id
WHERE pf.performer_type = 'singer'
GROUP BY pf.id, pf.name, pf.voice_type, pf.nationality;
```

#### `mart_repertoire_trends`
Opera work popularity over time

```sql
-- Built by dbt
CREATE TABLE mart_repertoire_trends AS
SELECT
    ow.id AS opera_work_id,
    ow.title,
    ow.composer,
    ow.period,
    EXTRACT(YEAR FROM p.premiere_date) AS performance_year,

    -- Production metrics
    COUNT(DISTINCT p.id) AS productions_count,
    COUNT(DISTINCT p.company_id) AS companies_count,
    COUNT(DISTINCT c.country) AS countries_count,

    -- Performance metrics
    SUM(p.total_performances) AS total_performances,
    AVG(p.ticket_price_max) AS avg_ticket_price,

    -- Geographic distribution
    STRING_AGG(DISTINCT c.country, ', ') AS countries_performed
FROM opera_works ow
JOIN productions p ON ow.id = p.opera_work_id
JOIN companies c ON p.company_id = c.id
GROUP BY ow.id, ow.title, ow.composer, ow.period,
         EXTRACT(YEAR FROM p.premiere_date);
```

---

## Supporting Objects

### Materialized Views (for Performance)

```sql
-- Fast company statistics
CREATE MATERIALIZED VIEW mv_company_stats AS
SELECT
    c.id,
    c.name,
    COUNT(DISTINCT p.id) AS total_productions,
    COUNT(DISTINCT s.id) AS total_seasons,
    MIN(p.premiere_date) AS first_production_date,
    MAX(p.premiere_date) AS latest_production_date,
    COUNT(DISTINCT ow.id) AS unique_operas_performed
FROM companies c
LEFT JOIN productions p ON c.id = p.company_id
LEFT JOIN seasons s ON c.id = s.company_id
LEFT JOIN opera_works ow ON p.opera_work_id = ow.id
GROUP BY c.id, c.name;

CREATE UNIQUE INDEX idx_mv_company_stats ON mv_company_stats(id);
```

### Functions

```sql
-- Calculate data quality score
CREATE OR REPLACE FUNCTION calculate_data_quality_score(
    table_name TEXT,
    record_id UUID
) RETURNS DECIMAL(3,2) AS $$
DECLARE
    score DECIMAL(3,2);
BEGIN
    -- Implementation would check field completeness
    -- This is a simplified example
    RETURN 0.85;
END;
$$ LANGUAGE plpgsql;

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- (Apply similar triggers to all tables with updated_at)
```

---

## Next Steps

1. **Implement Schema:**
   - SQL migration scripts with Alembic
   - Seed data for testing
   - Validation constraints

2. **Set Up dbt:**
   - dbt project structure
   - Source definitions
   - Model transformations
   - Tests and documentation

3. **Build Pipeline:**
   - Extraction → Staging
   - Staging → Core (validation & normalization)
   - Core → Analytics (dbt transformations)

See [DATA_PIPELINE.md](DATA_PIPELINE.md) for complete pipeline architecture.
