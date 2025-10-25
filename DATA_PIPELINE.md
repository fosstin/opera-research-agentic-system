# Data Pipeline Architecture

Complete ELT pipeline design for the Opera Research Agentic System using modern data tools.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: EXTRACT (Python)                                       │
├─────────────────────────────────────────────────────────────────┤
│ Compliant Web Scraper                                           │
│   ├─ Fetch HTML (with rate limiting, caching, robots.txt)      │
│   ├─ Store in stg_scraped_pages                                │
│   └─ Trigger LLM extraction                                     │
│                                                                  │
│ LLM-Powered Extraction (LangChain + GPT-4/Gemini)              │
│   ├─ Parse HTML → Structured JSON                              │
│   ├─ Extract: Productions, Cast, Financials, Schedules         │
│   ├─ Store in stg_llm_extractions                              │
│   └─ Mark validation status                                     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: LOAD (Python + SQLAlchemy)                            │
├─────────────────────────────────────────────────────────────────┤
│ Raw Load to Staging                                             │
│   ├─ Load HTML → stg_scraped_pages                             │
│   ├─ Load JSON → stg_llm_extractions                           │
│   └─ Minimal transformations (deduplication only)               │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: TRANSFORM (dbt)                                        │
├─────────────────────────────────────────────────────────────────┤
│ Staging → Core Transformations                                  │
│   ├─ Parse JSONB → Normalized tables                           │
│   ├─ Data validation & quality checks                          │
│   ├─ Entity resolution & deduplication                         │
│   ├─ Reference data enrichment                                 │
│   └─ Load to core tables (companies, productions, etc.)        │
│                                                                  │
│ Core → Analytics Transformations                                │
│   ├─ Build data marts (production_summary, etc.)               │
│   ├─ Calculate aggregations                                    │
│   ├─ Create materialized views                                 │
│   └─ Optimize for Tableau queries                              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: SERVE (PostgreSQL + Tableau)                          │
├─────────────────────────────────────────────────────────────────┤
│ Analytics Layer                                                  │
│   ├─ Tableau connects to PostgreSQL                            │
│   ├─ Pre-built dashboards                                      │
│   ├─ LLM agent queries via Tableau MCP                         │
│   └─ Interactive exploration                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tool Stack Decision

### **Extract: Python + LangChain**
**Why:**
- Complex web scraping needs custom logic
- LLM integration for intelligent parsing
- Compliance middleware already built
- Flexible error handling

**Tools:**
- BeautifulSoup/Playwright (scraping)
- LangChain (LLM orchestration)
- OpenAI/Gemini (extraction)
- SQLAlchemy (database writes)

### **Load: Python + SQLAlchemy**
**Why:**
- Simple bulk inserts to staging
- ORM makes schema management easy
- Transactional safety
- Fast bulk operations

**Tools:**
- SQLAlchemy Core (bulk inserts)
- Psycopg3 (PostgreSQL driver)
- Pandas (optional, for CSV loads)

### **Transform: dbt (data build tool)**
**Why:**
- ✅ SQL-based transformations (leverage PostgreSQL)
- ✅ Version control for transformations
- ✅ Testing framework built-in
- ✅ Dependency management (DAG)
- ✅ Documentation generation
- ✅ Incremental models
- ✅ Perfect for ELT pattern
- ✅ Tableau-friendly output

**What dbt does:**
- Staging → Core transformations
- Core → Analytics transformations
- Data quality tests
- Materialized views
- Incremental updates

**What dbt doesn't do:**
- Web scraping (use Python)
- LLM calls (use Python)
- Initial data loading (use Python)
- Real-time streaming (use Python/Kafka)

### **Orchestration: Prefect or Dagster**
**Why:**
- Schedule scraping jobs
- Manage dependencies
- Retry logic
- Monitoring and alerts
- dbt integration

**Choice:**
- **Prefect** - Simpler, Python-native, good for getting started
- **Dagster** - More powerful, better for complex pipelines

---

## Detailed Pipeline Steps

### Step 1: Web Scraping (Python)

```python
# src/pipeline/extract.py
from scraping.compliant_scraper import CompliantOperaScraper
from pipeline.loaders import StagingLoader
import logging

def scrape_company(company_domain: str):
    """Scrape a single company and load to staging."""

    scraper = CompliantOperaScraper(
        user_agent="OperaResearchBot/1.0",
        contact_info="https://github.com/austinkness/opera-research-agentic-system",
        respect_robots_txt=True,
        enable_rate_limiting=True,
        enable_caching=True,
        requests_per_second=1.0,
        min_delay_seconds=2.0,
        cache_ttl_seconds=86400
    )

    loader = StagingLoader()

    # Discover pages to scrape
    pages_to_scrape = discover_pages(company_domain)

    for page_url in pages_to_scrape:
        # Fetch HTML
        html = scraper.fetch_page(page_url)

        if html:
            # Load to staging
            page_id = loader.load_scraped_page(
                url=page_url,
                company_domain=company_domain,
                html_content=html,
                page_type=detect_page_type(page_url)
            )

            logging.info(f"Loaded page {page_url} → {page_id}")

    return scraper.get_stats()
```

### Step 2: LLM Extraction (Python + LangChain)

```python
# src/pipeline/llm_extraction.py
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json

class ProductionExtraction(BaseModel):
    """Structured extraction schema for productions."""
    opera_title: str = Field(description="Title of the opera")
    composer: str = Field(description="Composer name")
    conductor: Optional[str] = Field(description="Conductor name")
    director: Optional[str] = Field(description="Director name")
    premiere_date: Optional[str] = Field(description="Opening date (YYYY-MM-DD)")
    closing_date: Optional[str] = Field(description="Closing date (YYYY-MM-DD)")
    cast_members: List[dict] = Field(description="List of {performer, role, voice_type}")
    ticket_prices: Optional[dict] = Field(description="{min, max, currency}")
    venue: Optional[str] = Field(description="Venue name")

def extract_production_data(html: str, url: str) -> dict:
    """Use LLM to extract structured production data from HTML."""

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    parser = PydanticOutputParser(pydantic_object=ProductionExtraction)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at extracting structured data from opera
        house websites. Extract production information from the HTML.

        {format_instructions}

        If information is not present, use null. Be conservative - only extract
        information you're confident about."""),
        ("user", "URL: {url}\n\nHTML:\n{html}")
    ])

    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "html": html[:50000],  # Truncate if too long
            "url": url,
            "format_instructions": parser.get_format_instructions()
        })

        return {
            "success": True,
            "data": result.dict(),
            "confidence": calculate_confidence(result)
        }
    except Exception as e:
        logging.error(f"Extraction failed for {url}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def process_extractions():
    """Process all unprocessed scraped pages."""
    from pipeline.loaders import StagingLoader

    loader = StagingLoader()
    unprocessed_pages = loader.get_unprocessed_pages()

    for page in unprocessed_pages:
        extraction = extract_production_data(
            html=page.html_content,
            url=page.url
        )

        if extraction['success']:
            loader.load_llm_extraction(
                scraped_page_id=page.id,
                raw_response=extraction['data'],
                confidence_score=extraction['confidence'],
                llm_model="gpt-4-turbo-preview"
            )

            # Mark page as processed
            loader.mark_page_processed(page.id)
```

### Step 3: Load to Staging (Python + SQLAlchemy)

```python
# src/pipeline/loaders.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import hashlib
from datetime import datetime
import json

class StagingLoader:
    """Handles loading data to staging tables."""

    def __init__(self):
        db_url = os.getenv('DATABASE_URL')
        self.engine = create_engine(db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def load_scraped_page(
        self,
        url: str,
        company_domain: str,
        html_content: str,
        page_type: str,
        status_code: int = 200,
        response_headers: dict = None
    ) -> str:
        """Load scraped HTML to staging table."""

        checksum = hashlib.md5(html_content.encode()).hexdigest()

        query = text("""
            INSERT INTO stg_scraped_pages (
                url, company_domain, html_content, status_code,
                response_headers, page_type, checksum
            ) VALUES (
                :url, :company_domain, :html_content, :status_code,
                :response_headers, :page_type, :checksum
            )
            ON CONFLICT (url, scraped_at) DO NOTHING
            RETURNING id
        """)

        result = self.session.execute(query, {
            'url': url,
            'company_domain': company_domain,
            'html_content': html_content,
            'status_code': status_code,
            'response_headers': json.dumps(response_headers or {}),
            'page_type': page_type,
            'checksum': checksum
        })

        self.session.commit()

        row = result.fetchone()
        return str(row[0]) if row else None

    def load_llm_extraction(
        self,
        scraped_page_id: str,
        raw_response: dict,
        confidence_score: float,
        llm_model: str
    ) -> str:
        """Load LLM extraction results to staging."""

        query = text("""
            INSERT INTO stg_llm_extractions (
                scraped_page_id, raw_response, confidence_score,
                llm_model, extraction_version
            ) VALUES (
                :scraped_page_id, :raw_response, :confidence_score,
                :llm_model, :extraction_version
            )
            ON CONFLICT (scraped_page_id, extraction_version)
            DO UPDATE SET
                raw_response = EXCLUDED.raw_response,
                confidence_score = EXCLUDED.confidence_score,
                extracted_at = NOW()
            RETURNING id
        """)

        result = self.session.execute(query, {
            'scraped_page_id': scraped_page_id,
            'raw_response': json.dumps(raw_response),
            'confidence_score': confidence_score,
            'llm_model': llm_model,
            'extraction_version': 'v1.0'
        })

        self.session.commit()

        row = result.fetchone()
        return str(row[0]) if row else None

    def get_unprocessed_pages(self, limit: int = 100):
        """Get scraped pages that haven't been extracted yet."""

        query = text("""
            SELECT id, url, html_content, page_type
            FROM stg_scraped_pages
            WHERE is_processed = FALSE
            AND status_code = 200
            LIMIT :limit
        """)

        result = self.session.execute(query, {'limit': limit})
        return result.fetchall()

    def mark_page_processed(self, page_id: str):
        """Mark a page as processed."""

        query = text("""
            UPDATE stg_scraped_pages
            SET is_processed = TRUE, processed_at = NOW()
            WHERE id = :page_id
        """)

        self.session.execute(query, {'page_id': page_id})
        self.session.commit()
```

### Step 4: Transform with dbt

#### dbt Project Structure

```
dbt_opera/
├── dbt_project.yml
├── profiles.yml
├── models/
│   ├── staging/
│   │   ├── _sources.yml           # Define staging tables
│   │   ├── stg_productions.sql    # Clean staging data
│   │   └── stg_performers.sql
│   ├── core/
│   │   ├── companies.sql          # Incremental upserts
│   │   ├── productions.sql
│   │   ├── performers.sql
│   │   └── cast_assignments.sql
│   └── marts/
│       ├── mart_production_summary.sql
│       ├── mart_performer_career.sql
│       └── mart_repertoire_trends.sql
├── tests/
│   ├── assert_no_null_company_names.sql
│   └── assert_valid_dates.sql
├── macros/
│   ├── normalize_currency.sql
│   └── calculate_quality_score.sql
└── seeds/
    ├── country_codes.csv
    └── voice_types.csv
```

#### Example dbt Model: `models/core/productions.sql`

```sql
{{
    config(
        materialized='incremental',
        unique_key='id',
        on_schema_change='sync_all_columns'
    )
}}

WITH source_data AS (
    SELECT
        e.id AS extraction_id,
        e.scraped_page_id,
        e.raw_response,
        e.confidence_score,
        p.company_domain,
        p.url AS source_url,
        p.scraped_at
    FROM {{ source('staging', 'stg_llm_extractions') }} e
    JOIN {{ source('staging', 'stg_scraped_pages') }} p
        ON e.scraped_page_id = p.id
    WHERE e.is_validated = TRUE
    AND e.confidence_score >= 0.7
    {% if is_incremental() %}
        AND e.extracted_at > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

parsed_data AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['source_url', 'raw_response->>' || '''opera_title''']) }} AS id,

        -- Link to company (lookup or create)
        (SELECT id FROM {{ ref('companies') }}
         WHERE domain = source_data.company_domain) AS company_id,

        -- Link to opera work (lookup or create)
        (SELECT id FROM {{ ref('opera_works') }}
         WHERE title = raw_response->>'opera_title'
         AND composer = raw_response->>'composer') AS opera_work_id,

        -- Extract fields from JSONB
        raw_response->>'opera_title' AS production_title,
        raw_response->>'conductor' AS conductor,
        raw_response->>'director' AS director,
        (raw_response->>'premiere_date')::DATE AS premiere_date,
        (raw_response->>'closing_date')::DATE AS closing_date,
        raw_response->'ticket_prices'->>'min' AS ticket_price_min,
        raw_response->'ticket_prices'->>'max' AS ticket_price_max,
        raw_response->'ticket_prices'->>'currency' AS ticket_price_currency,
        raw_response->>'venue' AS venue_name,

        source_url,
        confidence_score AS data_quality_score,
        NOW() AS created_at,
        NOW() AS updated_at
    FROM source_data
)

SELECT * FROM parsed_data
WHERE company_id IS NOT NULL  -- Only include if we can link to a company
```

#### Example dbt Model: `models/marts/mart_production_summary.sql`

```sql
{{
    config(
        materialized='table',
        indexes=[
            {'columns': ['company_name'], 'type': 'btree'},
            {'columns': ['opera_title'], 'type': 'btree'},
            {'columns': ['season_name'], 'type': 'btree'},
        ]
    )
}}

SELECT
    p.id AS production_id,
    c.name AS company_name,
    c.city,
    c.country,
    c.tier AS company_tier,
    c.venue_capacity AS company_capacity,

    ow.title AS opera_title,
    ow.composer,
    ow.period AS opera_period,
    ow.language AS opera_language,

    s.season_name,
    p.premiere_date,
    p.closing_date,
    p.total_performances,

    p.conductor,
    p.director,

    p.ticket_price_min,
    p.ticket_price_max,
    p.ticket_price_currency,

    -- Calculate metrics
    EXTRACT(DAY FROM (p.closing_date - p.premiere_date)) AS run_length_days,

    -- Aggregated cast data
    COUNT(DISTINCT ca.performer_id) AS total_cast_members,
    STRING_AGG(DISTINCT pf.name, ', ' ORDER BY pf.name)
        FILTER (WHERE ca.role_type = 'principal') AS principal_cast,

    -- Aggregated performance data
    COUNT(DISTINCT perf.id) AS actual_performances,
    AVG(perf.attendance_percentage) AS avg_attendance_pct,
    SUM(perf.box_office_revenue) AS total_box_office_revenue,

    -- Quality indicator
    p.data_quality_score,

    p.source_url,
    p.updated_at

FROM {{ ref('productions') }} p
JOIN {{ ref('companies') }} c ON p.company_id = c.id
JOIN {{ ref('opera_works') }} ow ON p.opera_work_id = ow.id
LEFT JOIN {{ ref('seasons') }} s ON p.season_id = s.id
LEFT JOIN {{ ref('cast_assignments') }} ca ON p.id = ca.production_id
LEFT JOIN {{ ref('performers') }} pf ON ca.performer_id = pf.id
LEFT JOIN {{ ref('performances') }} perf ON p.id = perf.production_id

WHERE p.premiere_date IS NOT NULL

GROUP BY
    p.id, c.name, c.city, c.country, c.tier, c.venue_capacity,
    ow.title, ow.composer, ow.period, ow.language,
    s.season_name, p.premiere_date, p.closing_date, p.total_performances,
    p.conductor, p.director, p.ticket_price_min, p.ticket_price_max,
    p.ticket_price_currency, p.data_quality_score, p.source_url, p.updated_at
```

#### dbt Tests: `tests/assert_valid_production_dates.sql`

```sql
-- Ensure premiere_date is before or equal to closing_date
SELECT *
FROM {{ ref('productions') }}
WHERE closing_date IS NOT NULL
  AND premiere_date > closing_date
```

### Step 5: Orchestration with Prefect

```python
# src/pipeline/flows.py
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta
import logging

@task(retries=3, retry_delay_seconds=60)
def scrape_company_task(company_domain: str):
    """Scrape a single company."""
    from pipeline.extract import scrape_company
    return scrape_company(company_domain)

@task(retries=2)
def extract_llm_data_task():
    """Run LLM extraction on unprocessed pages."""
    from pipeline.llm_extraction import process_extractions
    return process_extractions()

@task
def run_dbt_models():
    """Run dbt transformations."""
    import subprocess

    # Run dbt
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", "./dbt_opera"],
        cwd="./dbt_opera",
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"dbt run failed: {result.stderr}")

    return result.stdout

@task
def run_dbt_tests():
    """Run dbt data quality tests."""
    import subprocess

    result = subprocess.run(
        ["dbt", "test", "--profiles-dir", "./dbt_opera"],
        cwd="./dbt_opera",
        capture_output=True,
        text=True
    )

    return result.stdout

@flow(name="opera-etl-pipeline")
def opera_etl_flow(companies: list[str]):
    """Complete ETL pipeline for opera data."""

    logging.info(f"Starting ETL for {len(companies)} companies")

    # Stage 1: Scrape
    scrape_results = []
    for company in companies:
        result = scrape_company_task(company)
        scrape_results.append(result)

    # Stage 2: Extract with LLM
    extraction_result = extract_llm_data_task()

    # Stage 3: Transform with dbt
    dbt_result = run_dbt_models()

    # Stage 4: Test data quality
    test_result = run_dbt_tests()

    logging.info("ETL pipeline complete")

    return {
        "scrape_stats": scrape_results,
        "extractions": extraction_result,
        "dbt_output": dbt_result,
        "test_output": test_result
    }

# Schedule the flow
if __name__ == "__main__":
    # Run for a list of companies
    companies = [
        "metopera.org",
        "roh.org.uk",
        "wiener-staatsoper.at"
    ]

    opera_etl_flow(companies)
```

---

## Tool Installation & Setup

### 1. Install dbt

```bash
# Add to requirements.txt
dbt-core>=1.7.0
dbt-postgres>=1.7.0

# Install
pip install dbt-core dbt-postgres

# Initialize dbt project
cd src
dbt init dbt_opera
```

### 2. Install Prefect

```bash
# Add to requirements.txt
prefect>=2.14.0

# Install
pip install prefect

# Start Prefect server (optional, for UI)
prefect server start
```

### 3. Configure dbt Profile

```yaml
# ~/.dbt/profiles.yml (or dbt_opera/profiles.yml)
opera:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: "{{ env_var('DB_USER') }}"
      password: "{{ env_var('DB_PASSWORD') }}"
      port: 5432
      dbname: opera_research
      schema: analytics
      threads: 4

    prod:
      type: postgres
      host: "{{ env_var('PROD_DB_HOST') }}"
      user: "{{ env_var('PROD_DB_USER') }}"
      password: "{{ env_var('PROD_DB_PASSWORD') }}"
      port: 5432
      dbname: opera_research_prod
      schema: analytics
      threads: 8
```

---

## Running the Pipeline

### Development Workflow

```bash
# 1. Scrape data
python -m pipeline.extract --company metopera.org

# 2. Run LLM extraction
python -m pipeline.llm_extraction

# 3. Run dbt transformations
cd dbt_opera
dbt run --models staging  # Run staging models
dbt run --models core     # Run core models
dbt run --models marts    # Run mart models
dbt test                   # Run data quality tests

# 4. View docs
dbt docs generate
dbt docs serve
```

### Production Workflow

```bash
# Run complete pipeline with Prefect
python -m pipeline.flows

# Or schedule with Prefect
prefect deployment build pipeline/flows.py:opera_etl_flow \
  --name opera-daily-etl \
  --cron "0 2 * * *"  # Run at 2 AM daily

prefect deployment apply opera_etl_flow-deployment.yaml
```

---

## Advantages of This Approach

**dbt for Transformations:**
- ✅ SQL is faster than Python for transformations
- ✅ Version control for business logic
- ✅ Built-in testing framework
- ✅ Dependency management (DAG)
- ✅ Documentation generation
- ✅ Incremental models (only process new data)
- ✅ Team collaboration (data analysts can contribute)

**Python for Extraction:**
- ✅ Complex scraping logic
- ✅ LLM integration
- ✅ Flexible error handling
- ✅ Custom compliance middleware

**PostgreSQL for Storage:**
- ✅ ACID compliance
- ✅ JSON support (JSONB)
- ✅ Full-text search
- ✅ Geographic queries (PostGIS)
- ✅ Tableau compatibility

**Prefect for Orchestration:**
- ✅ Python-native
- ✅ Dynamic workflows
- ✅ Retry logic
- ✅ Monitoring UI
- ✅ Easy local development

---

## Next Steps

1. **Set up PostgreSQL database**
2. **Create migration scripts** (Alembic)
3. **Implement staging loaders** (Python)
4. **Build LLM extraction** (LangChain)
5. **Create dbt models** (SQL)
6. **Set up Prefect orchestration**
7. **Connect Tableau**
8. **Build LLM agent with MCP**

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed step-by-step guide.
