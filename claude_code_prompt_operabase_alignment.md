# Claude Code Prompt — Setup Instructions for the Opera Data Intelligence Project

You are a senior full-stack data engineer helping me align my existing GitHub repository to a new data architecture plan.
I'm building an intelligent opera data platform inspired by Operabase — focused on structured data, LLM reasoning, and metadata interpretation via MCP.
You will update my repo workspace in VS Code to reflect this design.

---

## GOAL
Refactor and scaffold the project so it supports:
1. A PostgreSQL-based data layer (Neon or Supabase compatible)
2. Python-based ingestion and ETL scripts for scraping and normalizing opera data
3. JSONB metadata schema for flexible context interpretation
4. Optional vector embedding support for semantic queries
5. Future integration with an LLM agent (LangChain or MCP SDK)
6. A lightweight REST/GraphQL API to serve queries to the web frontend
7. Deployment-friendly organization for free-tier hosting (Neon, Cloudflare Pages, Supabase)

---

## ACTION PLAN

### 1. Repository Restructure
Create or update the following top-level directory structure:
```
/opera-data-intelligence
│
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── companies.py
│   │   │   ├── productions.py
│   │   │   ├── artists.py
│   │   │   └── performances.py
│   ├── db/
│   │   ├── schema.sql
│   │   ├── models.py
│   │   ├── connectors.py
│   │   └── metadata_examples.json
│   ├── ingestion/
│   │   ├── scraper.py
│   │   ├── parser.py
│   │   ├── loader.py
│   │   └── config.yaml
│   └── utils/
│       ├── logging_config.py
│       ├── constants.py
│       └── helpers.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   │       └── apiClient.js
│   ├── package.json
│   └── tailwind.config.js
│
├── notebooks/
│   ├── data_exploration.ipynb
│   └── metadata_tests.ipynb
│
├── tests/
│   ├── test_scraper.py
│   ├── test_loader.py
│   └── test_api.py
│
├── requirements.txt
├── .env.example
├── README.md
└── docker-compose.yml
```

### 2. Virtual Environment & Dependencies
Initialize a Python virtual environment and install dependencies:
```
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn sqlalchemy psycopg2-binary requests beautifulsoup4 playwright pandas pydantic chromadb
pip freeze > requirements.txt
```

Include instructions in the README for setting up the `.env`:
```
DATABASE_URL=postgresql+psycopg2://user:password@host/dbname
VECTOR_DB_PATH=./backend/vectorstore
SCRAPE_BASE_URL=https://exampleopera.org/
```

### 3. Database Schema (Postgres)
Create `backend/db/schema.sql` and define relational tables:
- `opera_company`, `artist`, `production`, `performance`, `repertoire`
- Include JSONB columns named `metadata` for flexible contextual fields.

Add a simple SQLAlchemy ORM mapping in `backend/db/models.py`.

### 4. Example Metadata
Add a `metadata_examples.json` file showing how scraped data is represented with lineage info:
```
{
  "source": "https://operanorth.co.uk/productions/la-traviata",
  "scraped_at": "2025-10-25T15:00:00Z",
  "parser_version": "1.1",
  "fields_extracted": ["title", "composer", "cast"],
  "confidence": 0.92
}
```

### 5. API Layer
Implement a `main.py` FastAPI app with `/companies`, `/productions`, and `/artists` endpoints.
Each should query the database and return JSON.

Add `/metadata` endpoint to inspect stored metadata schemas.

### 6. Scraper MVP
Implement a scraper in `backend/ingestion/scraper.py` using `requests` or `Playwright` to fetch HTML for 3–5 known opera company URLs.
Parse minimal fields (company name, show title, composer, and dates).

### 7. Version Control & Documentation
- Commit all new files and push to main branch.
- Update README.md with:
  - Project purpose
  - Local development setup instructions
  - Example API calls
  - Future roadmap (LLM integration, vector search, MCP)

### 8. Future Enhancements (commented for later)
Leave commented placeholders in `main.py` for:
- LangChain SQL agent integration
- MCP protocol handler
- Vector store querying function (ChromaDB or pgvector)

---

## OUTPUT FORMAT
When ready, Claude should:
1. Create or update the file structure in the local VS Code workspace.
2. Generate the scaffolding code and comments in each new file.
3. Ensure dependencies are added.
4. Stage and commit the new structure with a message like:
   "Initial data intelligence project scaffold aligned with Operabase LLM plan."
5. Print a summary of what was created or changed.
