# Quick Start Guide - Opera Research Pipeline

Get the complete ELT pipeline running in 5 minutes.

## Prerequisites

✓ PostgreSQL 15 installed and running
✓ Python 3.13+ virtual environment
✓ OpenAI or Google API key

## Step 1: Set Up Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_key_here
# or
# GOOGLE_API_KEY=your_key_here
# AI_PROVIDER=openai  # or gemini
```

## Step 2: Verify Database Connection

```bash
# Make sure PostgreSQL is running
brew services list | grep postgresql

# Test connection
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
psql -d opera_research -c "SELECT version();"
```

## Step 3: Run the Pipeline

```bash
# Activate virtual environment
source venv/bin/activate

# Test LLM extraction (uses sample HTML)
python src/extraction/llm_extractor.py

# Run full pipeline (scrape + extract + load)
python src/pipeline/staging_loader.py
```

## Step 4: Run dbt Transformations

```bash
# Run all dbt models
venv/bin/dbt run --project-dir dbt_opera --profiles-dir .

# View results
psql -d opera_research -c "SELECT * FROM analytics.stg_validated_extractions LIMIT 5;"
```

## Step 5: Check Results

```bash
# Connect to database
psql -d opera_research
```

```sql
-- Check extraction statistics
SELECT
    COUNT(*) as total_extractions,
    SUM(tokens_total) as total_tokens,
    SUM(estimated_cost_usd) as total_cost,
    AVG(confidence_score) as avg_confidence
FROM stg_llm_extractions;

-- View scraped pages
SELECT url, company_name, is_processed, scraped_at
FROM stg_scraped_pages
ORDER BY scraped_at DESC;

-- View validated extractions
SELECT * FROM analytics.stg_validated_extractions;
```

## What Just Happened?

1. **Scraped** opera company websites (with robots.txt compliance)
2. **Extracted** structured data using GPT-4 or Gemini
3. **Loaded** raw data into staging tables
4. **Transformed** data with dbt into analytics-ready views
5. **Tracked** costs, quality metrics, and audit logs

## Next Steps

- **Add more URLs** to scrape in `src/pipeline/staging_loader.py`
- **Create more dbt models** in `dbt_opera/models/`
- **Build dashboards** with Tableau or other BI tools
- **Set up orchestration** with Prefect for scheduled runs

## Troubleshooting

**Database connection failed?**
```bash
brew services start postgresql@15
```

**API key not working?**
```bash
# Check .env file
cat .env | grep API_KEY
```

**dbt connection failed?**
```bash
venv/bin/dbt debug --project-dir dbt_opera --profiles-dir .
```

## Full Documentation

See [PIPELINE_SETUP_COMPLETE.md](PIPELINE_SETUP_COMPLETE.md) for comprehensive documentation.
