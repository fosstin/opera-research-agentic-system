# Opera Research ELT Pipeline - Setup Complete ✓

## Summary

Successfully implemented a complete ELT (Extract-Load-Transform) pipeline for opera production metadata with:
- PostgreSQL database with 12 tables (staging + core layers)
- Compliant web scraping system
- LLM-powered data extraction (OpenAI/Gemini)
- Database migrations with Alembic
- Data transformations with dbt

---

## What Was Built

### 1. Database Infrastructure ✓

**PostgreSQL Database**: `opera_research`

**Tables Created** (12 total):
- **Staging Layer (4 tables)**:
  - `stg_scraped_pages` - Raw HTML from opera websites
  - `stg_llm_extractions` - Structured data from LLM parsing
  - `stg_scrape_logs` - Audit log for all scrape operations
  - `stg_extraction_logs` - Audit log for LLM extractions

- **Core Layer (7 tables)**:
  - `companies` - Opera companies and houses
  - `opera_works` - Catalog of operas (the works themselves)
  - `seasons` - Opera seasons
  - `productions` - Specific productions
  - `performances` - Individual performance events
  - `performers` - Individual performers (singers, conductors, etc.)
  - `cast_assignments` - Links performers to productions

- **System Table (1)**:
  - `alembic_version` - Migration tracking

### 2. Database Migrations ✓

**Tool**: Alembic

**Migrations Created**:
1. [4e0bc941d1d5_create_staging_tables.py](alembic/versions/4e0bc941d1d5_create_staging_tables.py) - Staging layer
2. [28f497fc7f2a_create_core_tables.py](alembic/versions/28f497fc7f2a_create_core_tables.py) - Core layer

**Status**: ✓ Applied to database

### 3. Web Scraping System ✓

**File**: [src/scraping/compliant_scraper.py](src/scraping/compliant_scraper.py)

**Features**:
- robots.txt compliance
- Rate limiting (configurable per-domain)
- Caching to reduce server load
- Request logging
- Mandatory ethical parameters

### 4. LLM Extraction Module ✓

**File**: [src/extraction/llm_extractor.py](src/extraction/llm_extractor.py)

**Key Improvements** (production-grade):
- ✓ Deterministic responses (seed parameter, JSON mode)
- ✓ Accurate token counting (tiktoken)
- ✓ Pydantic schema validation
- ✓ Intelligent text chunking (preserves context)
- ✓ Retry logic on failures
- ✓ Cache key generation for deduplication
- ✓ Support for OpenAI (GPT-4) and Google (Gemini)

**Cost Tracking**:
- Accurate token counting
- Per-extraction cost calculation
- Aggregated cost reporting

### 5. Data Loading System ✓

**File**: [src/pipeline/staging_loader.py](src/pipeline/staging_loader.py)

**Functions**:
- `load_scraped_page()` - Insert HTML into staging
- `load_llm_extraction()` - Insert LLM results
- `log_scrape_operation()` - Audit logging
- `get_extraction_stats()` - Cost and quality metrics
- `scrape_and_load()` - End-to-end pipeline function

### 6. dbt Transformation Layer ✓

**Project**: `dbt_opera/`

**Configuration**:
- Database: `opera_research`
- Schema: `analytics`
- Target: `dev` (local PostgreSQL)

**Models Created**:
- `stg_validated_extractions` - Filtered, high-quality extractions

**Features**:
- Source definitions for staging tables
- Data quality tests
- Configurable confidence thresholds
- JSONB extraction for productions

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                   OPERA RESEARCH PIPELINE                 │
└──────────────────────────────────────────────────────────┘

1. EXTRACT (Web Scraping)
   └─→ compliant_scraper.py
       ├─ robots.txt compliance
       ├─ rate limiting
       └─ caching

2. LOAD (Raw Data → Staging)
   └─→ staging_loader.load_scraped_page()
       └─→ PostgreSQL: stg_scraped_pages

3. EXTRACT (LLM Parsing)
   └─→ llm_extractor.extract_production_data()
       ├─ OpenAI GPT-4 or Google Gemini
       ├─ JSON schema validation
       └─ Cost tracking

4. LOAD (Extractions → Staging)
   └─→ staging_loader.load_llm_extraction()
       └─→ PostgreSQL: stg_llm_extractions

5. TRANSFORM (dbt)
   └─→ dbt models
       ├─ stg_validated_extractions (view)
       └─→ PostgreSQL: analytics schema
```

---

## How to Use

### 1. Run Web Scraping + LLM Extraction

```bash
# Activate virtual environment
source venv/bin/activate

# Run the end-to-end pipeline
python src/pipeline/staging_loader.py
```

This will:
- Scrape opera company websites
- Extract data with LLM
- Load into staging tables
- Log all operations
- Report costs and quality metrics

### 2. Run dbt Transformations

```bash
# Run all dbt models
venv/bin/dbt run --project-dir dbt_opera --profiles-dir .

# Run specific model
venv/bin/dbt run --project-dir dbt_opera --profiles-dir . --select stg_validated_extractions

# Run tests
venv/bin/dbt test --project-dir dbt_opera --profiles-dir .
```

### 3. Query the Data

```sql
-- Check extraction statistics
SELECT
    COUNT(*) as total_extractions,
    COUNT(*) FILTER (WHERE is_validated = TRUE) as validated,
    SUM(tokens_total) as total_tokens,
    SUM(estimated_cost_usd) as total_cost,
    AVG(confidence_score) as avg_confidence
FROM stg_llm_extractions;

-- View validated extractions
SELECT * FROM analytics.stg_validated_extractions;

-- Get cost breakdown by LLM provider
SELECT
    llm_provider,
    llm_model,
    COUNT(*) as num_extractions,
    SUM(tokens_total) as total_tokens,
    SUM(estimated_cost_usd) as total_cost
FROM stg_llm_extractions
GROUP BY llm_provider, llm_model
ORDER BY total_cost DESC;
```

---

## Database Connection

**Connection String**:
```
postgresql://austinkness@localhost:5432/opera_research
```

**Using psql**:
```bash
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d opera_research
```

---

## Key Files Created

### Database
- `/alembic.ini` - Alembic configuration
- `/alembic/versions/4e0bc941d1d5_create_staging_tables.py`
- `/alembic/versions/28f497fc7f2a_create_core_tables.py`
- `/backend/db/connectors.py` - Database connections
- `/backend/db/models.py` - Core layer ORM models
- `/backend/db/staging_models.py` - Staging layer ORM models

### Pipeline
- `/src/scraping/compliant_scraper.py` - Web scraper
- `/src/extraction/llm_extractor.py` - LLM extraction
- `/src/pipeline/staging_loader.py` - Data loader

### dbt
- `/dbt_opera/dbt_project.yml` - Project configuration
- `/profiles.yml` - Database connection profiles
- `/dbt_opera/models/staging/schema.yml` - Source definitions
- `/dbt_opera/models/staging/stg_validated_extractions.sql` - Staging model

---

## Next Steps

### Immediate (Ready to Use)
1. ✓ Scrape opera company websites
2. ✓ Extract data with LLM
3. ✓ Load into database
4. ✓ Transform with dbt

### Near-Term Enhancements
1. **Add more dbt models**:
   - `core_productions` - Normalized productions
   - `core_companies` - Normalized companies
   - `analytics_season_overview` - BI-ready views

2. **Implement FastAPI endpoints** (code already exists in `backend/api/main.py`):
   - GET /companies
   - GET /productions
   - GET /metadata/scraping-stats

3. **Add orchestration** (Prefect):
   - Schedule daily scraping
   - Automatic LLM extraction
   - dbt runs on new data

4. **Add data quality monitoring**:
   - dbt data tests
   - Anomaly detection
   - Cost alerts

### Long-Term
1. Vector search (ChromaDB/pgvector)
2. Tableau dashboard integration
3. LLM agent for natural language queries (Tableau MCP)
4. Frontend web application

---

## Costs

**LLM Extraction Costs** (estimated per page):
- OpenAI GPT-4 Turbo: ~$0.01-0.05 per page
- Google Gemini Pro: ~$0.001-0.005 per page

**Recommendation**: Start with Gemini for cost efficiency, use GPT-4 for complex extractions

---

## Quality & Reliability

**Production-Grade Features**:
- ✓ Deterministic LLM responses (seed, JSON mode)
- ✓ Accurate token counting (tiktoken)
- ✓ Schema validation (Pydantic)
- ✓ Retry logic on failures
- ✓ Comprehensive error logging
- ✓ Database migrations (version controlled)
- ✓ Data quality tests (dbt)

**Monitoring**:
- Scrape logs in `stg_scrape_logs`
- Extraction logs in `stg_extraction_logs`
- Cost tracking per extraction
- Confidence scores for quality assessment

---

## Testing

**LLM Extractor Test**:
```bash
python src/extraction/llm_extractor.py
```

**Data Loader Test**:
```bash
python src/pipeline/staging_loader.py
```

**dbt Test**:
```bash
venv/bin/dbt test --project-dir dbt_opera --profiles-dir .
```

---

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@15

# Test connection
psql -d opera_research -c "SELECT version();"
```

### Alembic Migration Issues
```bash
# Check current migration status
alembic current

# View migration history
alembic history

# Downgrade if needed
alembic downgrade -1
```

### dbt Issues
```bash
# Debug connection
venv/bin/dbt debug --project-dir dbt_opera --profiles-dir .

# Compile without running
venv/bin/dbt compile --project-dir dbt_opera --profiles-dir .
```

---

## Documentation References

- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Complete database schema
- [DATA_PIPELINE.md](DATA_PIPELINE.md) - ELT pipeline architecture
- [WEB_SCRAPING_COMPLIANCE.md](WEB_SCRAPING_COMPLIANCE.md) - Legal/ethical guidelines
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 14-week roadmap
- [HYBRID_ARCHITECTURE.md](HYBRID_ARCHITECTURE.md) - Combined data warehouse + API approach

---

**Status**: ✓ READY FOR PRODUCTION TESTING

Date: October 25, 2025
