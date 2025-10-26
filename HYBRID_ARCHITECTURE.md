# Hybrid Architecture - Opera Research Intelligence Platform

## Overview

This project combines **two architectural approaches** to create a comprehensive opera data intelligence platform:

1. **Data Warehouse Architecture** - Rich analytics and Tableau integration
2. **Operabase-style API** - Web application with REST API and frontend

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                           │
├─────────────────────────────────────────────────────────────┤
│  • Tableau Dashboards (data analysts)                       │
│  • Web UI / React Frontend (end users)                      │
│  • REST API (developers)                                    │
│  • LLM Agent / Tableau MCP (conversational)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  backend/api/main.py                                        │
│  • GET /companies - List opera companies                    │
│  • GET /productions - List productions                      │
│  • GET /artists - List performers                           │
│  • GET /metadata/scraping-stats - Data lineage              │
│  • POST /search/semantic - Vector search (future)           │
│  • POST /agent/query - LLM agent (future)                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               ANALYTICS LAYER (dbt marts)                    │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL - Analytics Schema                              │
│  • mart_production_summary (Tableau optimized)              │
│  • mart_performer_career (career analytics)                 │
│  • mart_repertoire_trends (trend analysis)                  │
│  • Materialized views for performance                       │
└─────────────────────────────────────────────────────────────┘
                            ↑ (dbt transformations)
┌─────────────────────────────────────────────────────────────┐
│                 CORE LAYER (Normalized)                      │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL - Core Schema                                   │
│  • companies (opera houses)                                 │
│  • opera_works (opera catalog)                              │
│  • productions (specific stagings)                          │
│  • performances (individual shows)                          │
│  • performers (artists)                                     │
│  • cast_assignments (roles)                                 │
│  • financial_data (company finances)                        │
└─────────────────────────────────────────────────────────────┘
                            ↑ (dbt transformations)
┌─────────────────────────────────────────────────────────────┐
│                STAGING LAYER (Raw/Semi-structured)           │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL - Staging Schema                                │
│  • stg_scraped_pages (raw HTML + metadata)                  │
│  • stg_llm_extractions (LLM-parsed JSONB)                   │
└─────────────────────────────────────────────────────────────┘
                            ↑ (Python loads)
┌─────────────────────────────────────────────────────────────┐
│                  EXTRACTION LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Python + LangChain                                         │
│  • LLM-powered HTML parsing (GPT-4/Gemini)                  │
│  • Structured data extraction                               │
│  • Confidence scoring                                       │
└─────────────────────────────────────────────────────────────┘
                            ↑ (Python scrapes)
┌─────────────────────────────────────────────────────────────┐
│                 WEB SCRAPING LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Compliant Scraper (Python)                                 │
│  • robots.txt compliance ✅                                 │
│  • Rate limiting ✅                                         │
│  • Caching ✅                                               │
│  • Request logging ✅                                       │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
opera-research-agentic-system/
│
├── backend/                      # NEW: API & Backend Services
│   ├── api/
│   │   ├── main.py              # FastAPI application
��   │   └── routes/              # API route modules (future)
│   ├── db/
│   │   ├── connectors.py        # Database connections
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── metadata_examples.json
│   ├── ingestion/
│   │   └── config.yaml          # Scraping configuration
│   └── utils/                   # Shared utilities
│
├── frontend/                     # NEW: Web UI (Planned)
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   └── services/
│   │       └── apiClient.js     # API client
│   └── README.md
│
├── src/                         # EXISTING: Core Pipeline
│   ├── scraping/
│   │   ├── compliant_scraper.py # Production scraper
│   │   ├── compliance.py        # Compliance middleware
│   │   ├── robots_parser.py     # robots.txt parser
│   │   ├── rate_limiter.py      # Rate limiting
│   │   └── cache.py             # Response caching
│   ├── processing/              # Data processing (future)
│   ├── db/                      # Database utilities (future)
│   ├── analytics/               # Analytics scripts (future)
│   └── main.py                  # Original CLI entry point
│
├── dbt_opera/                   # PLANNED: dbt Project
│   ├── models/
│   │   ├── staging/             # Staging transformations
│   │   ├── core/                # Core table transformations
│   │   └── marts/               # Analytics marts
│   └── tests/                   # Data quality tests
│
├── alembic/                     # PLANNED: Database Migrations
│   └── versions/                # Migration scripts
│
├── tests/                       # Test Suite
│   ├── test_scraper.py          # EXISTING
│   ├── test_api.py              # NEW (future)
│   └── test_pipeline.py         # NEW (future)
│
├── notebooks/                   # NEW: Jupyter Notebooks
│   ├── data_exploration.ipynb
│   └── metadata_tests.ipynb
│
├── data/                        # EXISTING: Data Storage
│   ├── cache/                   # Scraped page cache
│   ├── raw/                     # Raw data files
│   └── processed/               # Processed data
│
├── docs/                        # Documentation
│   ├── PROJECT_VISION.md        # Overall vision
│   ├── DATABASE_SCHEMA.md       # Database design
│   ├── DATA_PIPELINE.md         # Pipeline architecture
│   ├── IMPLEMENTATION_PLAN.md   # Step-by-step guide
│   ├── WEB_SCRAPING_COMPLIANCE.md
│   └── HYBRID_ARCHITECTURE.md   # THIS FILE
│
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # Main README
```

## Technology Stack

### Data Layer
- **Database:** PostgreSQL (compatible with Neon, Supabase)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Transformations:** dbt (data build tool)

### Backend/API Layer
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Authentication:** (Future - JWT/OAuth)

### Frontend Layer (Planned)
- **Framework:** React or Vue.js
- **Styling:** Tailwind CSS
- **API Client:** Fetch/Axios
- **State Management:** React Query / Pinia

### Data Pipeline
- **Scraping:** Python + BeautifulSoup/Playwright
- **LLM:** LangChain + OpenAI/Gemini
- **Orchestration:** Prefect
- **Compliance:** Custom middleware

### Analytics & Visualization
- **Primary:** Tableau Desktop/Server
- **Secondary:** Plotly, Matplotlib
- **LLM Integration:** Tableau MCP

### Future Enhancements
- **Vector Search:** ChromaDB or pgvector
- **Real-time:** WebSockets
- **Caching:** Redis
- **CDN:** Cloudflare

## Key Features

### Data Warehouse Features (Original Architecture)
✅ Comprehensive database schema (15+ tables)
✅ 3-layer data architecture (staging → core → analytics)
✅ dbt transformations for data quality
✅ Tableau integration for deep analytics
✅ Compliance system (robots.txt, rate limiting)
✅ LLM-powered data extraction

### API/Application Features (New Addition)
✅ REST API for programmatic access
✅ SQLAlchemy ORM models
✅ FastAPI with automatic API docs
✅ Web UI capability (frontend scaffold)
✅ Flexible JSONB metadata
✅ Vector search foundation (future)

## Use Cases by Interface

### Tableau Dashboards (Data Analysts)
- Complex trend analysis
- Financial comparisons
- Geographic visualizations
- Executive reporting
- Custom SQL queries

### Web UI (General Users)
- Browse companies and productions
- Search for specific operas
- Explore artist profiles
- View upcoming performances
- Discover repertoire trends

### REST API (Developers)
- Integrate with other applications
- Build custom tools
- Automated data retrieval
- Third-party integrations

### LLM Agent (Everyone)
- Natural language queries
- Conversational exploration
- Automatic visualization generation
- Context-aware recommendations

## Data Flow Examples

### Example 1: Production Data Pipeline

```
1. Web Scraping:
   Met Opera website → CompliantScraper
   ↓
2. Raw Storage:
   HTML → stg_scraped_pages (PostgreSQL)
   ↓
3. LLM Extraction:
   HTML → GPT-4 → Structured JSON → stg_llm_extractions
   ↓
4. dbt Staging:
   JSONB → Parse → Validate → stg_productions (SQL)
   ↓
5. dbt Core:
   Staging → Normalize → Link entities → productions table
   ↓
6. dbt Analytics:
   Core tables → Aggregate → mart_production_summary
   ↓
7. Multiple Interfaces:
   ├─ FastAPI: GET /productions → JSON response
   ├─ Tableau: Direct PostgreSQL connection → Dashboard
   ├─ Web UI: Fetch from API → Render in React
   └─ LLM Agent: Natural language → SQL → Tableau viz
```

### Example 2: User Query Flow

```
User asks: "Show me soprano roles in Verdi operas this season"

Path A - Tableau (Analyst):
  LLM Agent → Generate SQL → Execute → Send to Tableau MCP
  → Interactive dashboard

Path B - Web UI (End User):
  Frontend → apiClient.getProductions({composer: 'Verdi'})
  → FastAPI /productions endpoint
  → SQLAlchemy query → PostgreSQL
  → JSON response → Render in browser

Path C - API (Developer):
  curl http://localhost:8000/productions?composer=Verdi
  → FastAPI → SQLAlchemy → PostgreSQL → JSON
```

## Deployment Strategy

### Development
- PostgreSQL: Local instance
- FastAPI: `uvicorn main:app --reload`
- Frontend: `npm run dev`
- dbt: `dbt run --target dev`

### Staging/Production
- Database: Neon (serverless Postgres) or Supabase
- API: Docker container on Cloud Run / Railway / Fly.io
- Frontend: Cloudflare Pages (free tier)
- dbt: dbt Cloud or scheduled with Prefect

## Migration Path

### Phase 1 (Current) ✅
- [x] Compliant web scraper
- [x] Database schema design
- [x] Pipeline architecture
- [x] FastAPI backend scaffold
- [x] Frontend scaffold

### Phase 2 (Next 4-6 weeks)
- [ ] PostgreSQL setup
- [ ] Alembic migrations
- [ ] LLM extraction implementation
- [ ] dbt models
- [ ] API endpoints implementation

### Phase 3 (Weeks 7-10)
- [ ] Tableau dashboards
- [ ] Frontend development
- [ ] Testing & optimization

### Phase 4 (Weeks 11-14)
- [ ] LLM agent integration
- [ ] Tableau MCP integration
- [ ] Vector search
- [ ] Production deployment

## Benefits of Hybrid Approach

### For Data Analysts
- Rich Tableau dashboards
- Full SQL access
- dbt-tested data quality
- Comprehensive schema

### For Developers
- REST API access
- Well-documented endpoints
- OpenAPI/Swagger docs
- Flexible querying

### For End Users
- Intuitive web interface
- Fast search and browse
- Mobile-friendly
- No technical knowledge required

### For Everyone
- LLM-powered natural language queries
- Conversational data exploration
- Automatic insights
- Context-aware recommendations

## Getting Started

### 1. Set Up Database
```bash
createdb opera_research
cp .env.example .env
# Edit .env with your DATABASE_URL
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run FastAPI Server
```bash
cd backend/api
python main.py
# Or: uvicorn main:app --reload
```

### 4. Access API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. Test API
```bash
curl http://localhost:8000/
curl http://localhost:8000/companies
```

## Next Steps

1. **Review** this hybrid architecture
2. **Set up** PostgreSQL database
3. **Create** Alembic migrations (see DATABASE_SCHEMA.md)
4. **Implement** LLM extraction (see DATA_PIPELINE.md)
5. **Build** dbt models
6. **Test** API endpoints
7. **Deploy** to staging environment

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed week-by-week guide.

---

**Status:** Architecture complete, ready for implementation
**Last Updated:** January 2025
**Contributors:** Opera Research Team
