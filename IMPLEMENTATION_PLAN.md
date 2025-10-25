# Implementation Plan - Step by Step

Practical guide to build the complete Opera Research Agentic System with Tableau MCP integration.

## Overview

**Goal:** Transform your vision into a working system in ~14 weeks

**Current Status:** ✅ Phase 1 Complete (Web scraping foundation)

**Next Milestone:** Phase 2 - Database + LLM Extraction (4-6 weeks)

---

## Phase 2: Data Extraction & Storage (Weeks 1-6)

### Week 1: Database Setup

**Day 1-2: PostgreSQL Installation & Configuration**

```bash
# Install PostgreSQL
brew install postgresql@15  # macOS
# or
sudo apt-get install postgresql-15  # Linux

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb opera_research

# Update .env
echo "DATABASE_URL=postgresql://localhost/opera_research" >> .env
```

**Day 3-4: Alembic Setup & Initial Migration**

```bash
# Install dependencies
pip install alembic sqlalchemy psycopg2-binary

# Initialize Alembic
alembic init alembic

# Create first migration
alembic revision -m "create_staging_tables"
```

Edit `alembic/versions/001_create_staging_tables.py`:
```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create stg_scraped_pages
    op.create_table(
        'stg_scraped_pages',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('url', sa.Text, nullable=False),
        sa.Column('company_domain', sa.Text, nullable=False),
        sa.Column('scraped_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('html_content', sa.Text),
        sa.Column('status_code', sa.Integer),
        sa.Column('page_type', sa.Text),
        sa.Column('is_processed', sa.Boolean, default=False),
        sa.Column('checksum', sa.Text),
    )

    # Create stg_llm_extractions
    op.create_table(
        'stg_llm_extractions',
        sa.Column('id', UUID, primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('scraped_page_id', UUID, sa.ForeignKey('stg_scraped_pages.id')),
        sa.Column('extracted_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('raw_response', JSONB, nullable=False),
        sa.Column('confidence_score', sa.Numeric(3, 2)),
        sa.Column('llm_model', sa.Text),
        sa.Column('is_validated', sa.Boolean, default=False),
    )

def downgrade():
    op.drop_table('stg_llm_extractions')
    op.drop_table('stg_scraped_pages')
```

```bash
# Run migration
alembic upgrade head
```

**Day 5: Core Tables Migration**

Create migration for companies, opera_works, seasons, productions tables (see DATABASE_SCHEMA.md).

### Week 2: LLM Extraction Prototype

**Day 1-2: Set up LangChain Extraction**

Create `src/pipeline/llm_extraction.py`:

```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

class ProductionExtraction(BaseModel):
    """Schema for production data extraction."""
    opera_title: str
    composer: str
    conductor: Optional[str] = None
    director: Optional[str] = None
    premiere_date: Optional[str] = None
    cast_members: List[dict] = []

def extract_production(html: str) -> dict:
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    parser = PydanticOutputParser(pydantic_object=ProductionExtraction)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract opera production information from this HTML. {format_instructions}"),
        ("user", "{html}")
    ])

    chain = prompt | llm | parser
    result = chain.invoke({
        "html": html[:50000],
        "format_instructions": parser.get_format_instructions()
    })

    return result.dict()
```

**Day 3-4: Test with Real Data**

```python
# Test script: test_extraction.py
from scraping.compliant_scraper import CompliantOperaScraper
from pipeline.llm_extraction import extract_production

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

# Test with Met Opera
html = scraper.fetch_page("https://www.metopera.org/season/2024-25-season/")
result = extract_production(html)
print(result)
```

**Day 5: Build Staging Loader**

Create `src/pipeline/loaders.py` (see DATA_PIPELINE.md for full implementation).

### Week 3-4: Complete Extraction Pipeline

**Week 3: Build Full Pipeline**

1. Implement page discovery (find all production pages)
2. Create batch extraction process
3. Add error handling and retries
4. Implement validation checks
5. Test with 3-5 opera companies

**Week 4: Data Quality**

1. Build confidence scoring
2. Add data validation rules
3. Create manual review interface
4. Test and refine extraction prompts
5. Document extraction patterns

### Week 5-6: dbt Setup & Transformations

**Week 5: dbt Project Setup**

```bash
# Initialize dbt
cd src
dbt init dbt_opera

# Configure profile
cat > dbt_opera/profiles.yml << EOF
opera:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: ${DB_USER}
      password: ${DB_PASSWORD}
      dbname: opera_research
      schema: analytics
      threads: 4
EOF

# Test connection
cd dbt_opera
dbt debug
```

**Create dbt Models:**

1. `models/staging/_sources.yml` - Define staging sources
2. `models/core/companies.sql` - Company transformations
3. `models/core/productions.sql` - Production transformations
4. `models/marts/mart_production_summary.sql` - Analytics mart

**Week 6: dbt Testing & Documentation**

1. Write dbt tests (data quality checks)
2. Add documentation
3. Create macros for common transformations
4. Set up incremental models
5. Test full pipeline end-to-end

**Deliverables:**
- ✅ Working PostgreSQL database
- ✅ LLM extraction pipeline
- ✅ Data from 10+ opera houses in database
- ✅ dbt transformations working
- ✅ Data quality tests passing

---

## Phase 3: Analytics & Tableau (Weeks 7-10)

### Week 7-8: Tableau Setup

**Week 7: Connect Tableau to PostgreSQL**

1. Install Tableau Desktop
2. Connect to PostgreSQL database
3. Create initial data source
4. Build first dashboard (production summary)
5. Test queries and performance

**Week 8: Build Core Dashboards**

Create 5 essential dashboards:
1. **Production Overview** - Count by company, season, composer
2. **Geographic Distribution** - Map of opera houses
3. **Repertoire Trends** - Popular operas over time
4. **Cast Networks** - Performer collaboration graph
5. **Financial Analysis** - Budget and pricing trends

### Week 9-10: Optimization & Advanced Features

**Week 9:**
- Optimize database queries
- Create materialized views for performance
- Add filters and parameters to dashboards
- Build drill-down capabilities

**Week 10:**
- User acceptance testing
- Refine visualizations
- Create Tableau workbook templates
- Document dashboard usage

**Deliverables:**
- ✅ 5-10 Tableau dashboards
- ✅ Optimized database queries
- ✅ User documentation

---

## Phase 4: LLM Agent + Tableau MCP (Weeks 11-14)

### Week 11-12: LLM Agent Development

**Week 11: Text-to-SQL Agent**

Create `src/agent/nl_to_sql.py`:

```python
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.sql_database import SQLDatabase
from langchain.chat_models import ChatOpenAI

# Connect to database
db = SQLDatabase.from_uri("postgresql://localhost/opera_research")

# Create LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

# Create toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create agent
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="openai-functions"
)

# Test query
result = agent.run(
    "Show me the top 10 most performed operas in the last 5 years"
)
print(result)
```

**Week 12: Enhance Agent**

1. Add context awareness (remember conversation)
2. Implement query validation
3. Add result formatting
4. Handle ambiguous queries
5. Create error recovery

### Week 13-14: Tableau MCP Integration

**Week 13: Set up Tableau MCP**

1. Install Tableau MCP SDK
2. Configure MCP connection
3. Test basic integration
4. Create visualization generation functions

**Week 14: Complete Integration**

1. Connect LLM agent to Tableau MCP
2. Implement NL query → Tableau viz pipeline
3. Add conversational context
4. Create demo interface
5. User testing and refinement

**Deliverables:**
- ✅ Working NL to SQL agent
- ✅ Tableau MCP integration
- ✅ Demo: "Show me soprano trends" → Interactive dashboard
- ✅ Documentation and examples

---

## Quick Start Guide

### Immediate Next Steps (This Week)

**Day 1:**
```bash
# Set up PostgreSQL
createdb opera_research
pip install alembic sqlalchemy psycopg2-binary
alembic init alembic
```

**Day 2:**
```bash
# Create first migration
alembic revision -m "create_staging_tables"
# Edit migration file (copy from above)
alembic upgrade head
```

**Day 3:**
```bash
# Install LLM dependencies
pip install langchain langchain-openai
# Create extraction prototype (test_extraction.py)
python test_extraction.py
```

**Day 4:**
```bash
# Build staging loader
# Create pipeline/loaders.py
# Test loading data to staging
```

**Day 5:**
```bash
# End-to-end test
# Scrape → Extract → Load → Verify
# Document any issues
```

---

## Success Metrics by Phase

**Phase 2:**
- 10+ companies scraped
- 500+ productions extracted
- 90%+ extraction accuracy
- All dbt tests passing

**Phase 3:**
- 5+ working dashboards
- Query response time <3 seconds
- Tableau refresh time <30 seconds

**Phase 4:**
- NL query accuracy >85%
- Visualization generation <10 seconds
- User satisfaction >4/5

---

## Risk Mitigation

**Technical Risks:**
- LLM extraction accuracy → Solution: Multi-pass validation, manual review sampling
- Database performance → Solution: Indexes, materialized views, query optimization
- dbt complexity → Solution: Start simple, iterate, extensive documentation

**Resource Risks:**
- API costs → Solution: Caching, batch processing, use cheaper models for simple tasks
- Time constraints → Solution: MVP approach, phase releases, prioritize core features

**Data Risks:**
- Website changes → Solution: Version extraction prompts, alert on failures
- Legal/compliance → Solution: Regular ToS reviews, robust compliance system ✅

---

## Tools & Resources

**Development:**
- PostgreSQL GUI: pgAdmin, DBeaver, Postico
- dbt: VSCode extension, dbt Cloud
- Prefect: Local UI at http://localhost:4200

**Learning:**
- dbt: https://docs.getdbt.com/
- LangChain: https://python.langchain.com/
- Tableau: https://help.tableau.com/

**Community:**
- dbt Slack: https://www.getdbt.com/community
- LangChain Discord
- r/dataengineering

---

## Getting Help

**Stuck on:**
- Database schema → Review DATABASE_SCHEMA.md
- Pipeline flow → Review DATA_PIPELINE.md
- Overall vision → Review PROJECT_VISION.md
- Web scraping → Review WEB_SCRAPING_COMPLIANCE.md

**Need to:**
- See the big picture → PROJECT_VISION.md
- Understand data flow → DATA_PIPELINE.md
- Check database design → DATABASE_SCHEMA.md
- Start implementing → You're here! ✨

---

## Next Action

Ready to start? Run:

```bash
# Set up database
createdb opera_research

# Create .env
echo "DATABASE_URL=postgresql://localhost/opera_research" >> .env

# Install Phase 2 dependencies
pip install -r requirements.txt

# Initialize Alembic
alembic init alembic

# You're ready to go! 🚀
```

Then follow Week 1 Day 1-2 instructions above.
