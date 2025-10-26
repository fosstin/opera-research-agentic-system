# Data Sources Integration Strategy

## Overview

The Opera Research platform integrates multiple authoritative data sources to build a comprehensive opera company database.

## Data Sources

### 1. Opera America Field Reports (Primary Source)
**Type**: Excel files (annual field reports)
**Coverage**: ~100 professional opera companies (US & Canada)
**Data Includes**:
- Company names and locations
- Budget tiers (Budget 1-5, $100K - $50M+)
- Performance statistics
- Audience metrics
- Financial data

**Refresh**: Annual
**Storage**: `data/seeds/opera_america/`
**Load Method**: Python seed loader → `seed_opera_america_companies`

---

### 2. Candid (formerly GuideStar) API
**Type**: REST API
**Coverage**: 1.8M+ nonprofit organizations (IRS 990 data)
**API Docs**: https://developer.candid.org/reference/essentials-v3-api
**Authentication**: API key required

**Data Includes**:
- EIN (Employer Identification Number)
- Legal name and DBA names
- Mission statement
- Revenue, expenses, assets
- Board members and key staff
- Programs and services
- IRS classification codes (NTEE)

**Refresh**: Updated continuously from IRS filings
**Storage**: `seed_candid_nonprofits`
**Load Method**: API → PostgreSQL

**Search Example**:
```bash
curl -X POST "https://api.candid.org/essentials/v3/search" \
  -H "Subscription-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "search_terms": "opera",
    "filters": {
      "ntee_codes": ["A6E"],
      "state": "NY"
    }
  }'
```

**NTEE Codes for Opera**:
- `A6E` - Performing Arts Organizations (opera-specific)
- `A60` - Performing Arts Organizations (general)
- `A65` - Theater

---

### 3. IRS 990 Filings (via IRS API or AWS S3)
**Type**: XML/JSON files
**Coverage**: All US nonprofits with >$200K revenue
**Access**:
- IRS API: https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads
- AWS S3: `s3://irs-form-990/` (public bucket)

**Data Includes**:
- Form 990, 990-EZ, 990-PF
- Revenue and expenses (detailed schedules)
- Executive compensation
- Program service revenue
- Grants and contributions

**Refresh**: Annual (filed 6-12 months after fiscal year)
**Storage**: `seed_irs_990_filings`
**Load Method**: API/S3 → PostgreSQL

---

### 4. Web Scraping (Current Implementation)
**Type**: HTML scraping + LLM extraction
**Coverage**: Any opera company with a website
**Data Includes**:
- Current season productions
- Performance dates and times
- Cast and creative team
- Ticket pricing
- Real-time updates

**Refresh**: Daily/weekly (configurable)
**Storage**: `stg_scraped_pages` → `stg_llm_extractions`
**Load Method**: CompliantOperaScraper → LLMExtractor → PostgreSQL

---

### 5. Future Sources (Planned)

**Operabase API** (if available)
- International opera company directory
- Performer database
- Production archive

**Wikipedia/Wikidata**
- Opera work metadata
- Historical information
- International companies

**MusicBrainz**
- Opera work catalog
- Composer information
- Recording data

---

## Data Integration Architecture

### Seed Tables (Source Data)

```sql
-- Opera America (primary company list)
CREATE TABLE seed_opera_america_companies (
    id UUID PRIMARY KEY,
    company_name TEXT,
    city TEXT,
    state TEXT,
    country TEXT,
    budget_category TEXT,  -- "Budget 1", "Budget 2", etc.
    budget_min NUMERIC,
    budget_max NUMERIC,
    fiscal_year TEXT,
    performances_count INTEGER,
    attendance INTEGER,
    source_file TEXT,
    loaded_at TIMESTAMP
);

-- Candid/GuideStar data
CREATE TABLE seed_candid_nonprofits (
    id UUID PRIMARY KEY,
    ein TEXT UNIQUE,  -- IRS Employer ID
    legal_name TEXT,
    dba_names TEXT[],
    ntee_code TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    revenue NUMERIC,
    expenses NUMERIC,
    assets NUMERIC,
    mission TEXT,
    website TEXT,
    phone TEXT,
    fiscal_year_end TEXT,
    api_response JSONB,
    loaded_at TIMESTAMP
);

-- IRS 990 filings
CREATE TABLE seed_irs_990_filings (
    id UUID PRIMARY KEY,
    ein TEXT,
    tax_year INTEGER,
    organization_name TEXT,
    form_type TEXT,  -- "990", "990EZ", "990PF"
    revenue NUMERIC,
    expenses NUMERIC,
    executive_compensation JSONB,
    program_service_revenue NUMERIC,
    xml_url TEXT,
    json_data JSONB,
    loaded_at TIMESTAMP
);

-- Website mappings (enrichment)
CREATE TABLE seed_company_websites (
    id UUID PRIMARY KEY,
    company_name TEXT,
    website_url TEXT,
    season_page_url TEXT,
    ein TEXT,  -- Link to IRS/Candid
    opera_america_match TEXT,  -- Link to Opera America
    verified BOOLEAN DEFAULT FALSE,
    last_verified TIMESTAMP,
    notes TEXT
);
```

### Integration Logic (dbt Models)

```sql
-- dbt model: int_companies_unified.sql
-- Combines all sources into a unified company record

WITH opera_america AS (
    SELECT
        company_name,
        city,
        state,
        'Opera America' AS source,
        budget_category,
        NULL AS ein
    FROM {{ ref('seed_opera_america_companies') }}
),

candid AS (
    SELECT
        legal_name AS company_name,
        city,
        state,
        'Candid' AS source,
        NULL AS budget_category,
        ein
    FROM {{ ref('seed_candid_nonprofits') }}
    WHERE ntee_code IN ('A6E', 'A60', 'A65')
),

combined AS (
    -- Fuzzy match and deduplicate
    SELECT DISTINCT ON (LOWER(company_name), city, state)
        company_name,
        city,
        state,
        ARRAY_AGG(source) AS data_sources,
        MAX(ein) AS ein,
        MAX(budget_category) AS budget_category
    FROM (
        SELECT * FROM opera_america
        UNION ALL
        SELECT * FROM candid
    ) all_sources
    GROUP BY LOWER(company_name), city, state, company_name
)

SELECT
    c.*,
    w.website_url,
    w.season_page_url,
    i.revenue AS irs_revenue,
    i.tax_year AS irs_tax_year
FROM combined c
LEFT JOIN {{ ref('seed_company_websites') }} w
    ON LOWER(c.company_name) = LOWER(w.company_name)
LEFT JOIN {{ ref('seed_irs_990_filings') }} i
    ON c.ein = i.ein
    AND i.tax_year = (
        SELECT MAX(tax_year)
        FROM {{ ref('seed_irs_990_filings') }}
        WHERE ein = c.ein
    )
```

---

## Implementation Plan

### Phase 1: Opera America (Week 1)
- [x] Explore Excel file structure
- [ ] Create Python seed loader
- [ ] Load to PostgreSQL seed table
- [ ] Add website URLs (manual enrichment)
- [ ] Generate scraping targets

### Phase 2: Candid API (Week 2)
- [ ] Register for Candid API key
- [ ] Create API client module
- [ ] Search for opera companies (NTEE A6E)
- [ ] Load to seed_candid_nonprofits
- [ ] Match with Opera America records (by name/city)

### Phase 3: IRS 990 Data (Week 3)
- [ ] Set up AWS CLI for S3 access
- [ ] Download 990 XMLs for matched EINs
- [ ] Parse XML → PostgreSQL
- [ ] Extract financial metrics
- [ ] Link to company records

### Phase 4: Integration & Deduplication (Week 4)
- [ ] Create dbt integration models
- [ ] Implement fuzzy matching logic
- [ ] Build master company dimension
- [ ] Add data quality checks
- [ ] Create data lineage tracking

---

## Data Quality Considerations

### Matching Strategies
1. **Exact Match**: Name + City + State
2. **Fuzzy Match**: Levenshtein distance < 3
3. **EIN Match**: Use Candid EIN to link IRS data
4. **Website Match**: Domain matching

### Deduplication Rules
1. Opera America = primary source (most curated)
2. Candid = adds EIN and legal structure
3. IRS = adds detailed financial data
4. Web scraping = adds real-time production data

### Data Freshness
- **Opera America**: Annual (static reference)
- **Candid**: Updated continuously (refresh monthly)
- **IRS 990**: Annual (refresh quarterly)
- **Web scraping**: Real-time (refresh daily)

---

## Cost Estimates

### Candid API
- **Free Tier**: 100 requests/month
- **Paid Tier**: $500/month (5,000 requests)
- **Estimated Need**: ~200 companies = 200 requests/month (free tier sufficient)

### IRS Data
- **Cost**: Free (public data)
- **S3 egress**: ~$0.01/GB (minimal)

### LLM Extraction (Web Scraping)
- **OpenAI**: ~$0.02/page
- **Gemini**: ~$0.002/page
- **Estimated**: 100 companies × 5 pages = $1-10/scrape

---

## Storage Strategy

```
data/
├── seeds/                           # Static seed data
│   ├── opera_america/
│   │   ├── 2024-field-report.xlsx  # Gitignored (too large)
│   │   └── README.md                # Metadata about files
│   ├── candid/
│   │   └── api_responses/           # Cache API responses
│   └── irs/
│       └── 990_xmls/                # Downloaded 990s
├── raw/                             # Raw scraped HTML (gitignored)
└── processed/                       # Processed outputs
```

**Git Strategy**:
- ✅ Include: Python scripts, SQL, dbt models
- ✅ Include: Small CSVs (<1MB)
- ❌ Exclude: Excel files, large datasets, API responses
- ❌ Exclude: Scraped HTML, cached files

---

## Next Steps

1. **Immediate**: Load Opera America data
2. **Week 2**: Register for Candid API
3. **Week 3**: Set up IRS data pipeline
4. **Week 4**: Build integration models in dbt

---

## API Keys Required

- [ ] Candid API Key: https://developer.candid.org/
- [ ] IRS Developer Key: Not required (public data)
- [ ] AWS Account: For S3 access (optional)

---

**Last Updated**: October 26, 2024
