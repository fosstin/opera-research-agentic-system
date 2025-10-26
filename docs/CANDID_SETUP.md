# Candid API Setup Guide

## Overview

Candid (formerly GuideStar) provides comprehensive data on US nonprofit organizations through their Essentials API. This is the **primary source** for building our opera company database.

---

## Step 1: Get API Key (5 minutes)

1. Go to: **https://developer.candid.org/**
2. Click **"Sign Up"** or **"Log In"**
3. Navigate to **"My Applications"**
4. Create a new application:
   - **Name**: Opera Research Platform
   - **Description**: Academic research project for opera production data
5. Copy your **Subscription Key**

**Free Tier Limits**:
- 100 requests per month
- Sufficient for ~100 opera companies
- No credit card required

---

## Step 2: Add API Key to Environment

```bash
# Edit .env file
nano .env

# Add your key:
CANDID_API_KEY=your_actual_key_here
```

---

## Step 3: Test API Connection

```bash
# Run the Candid loader script
python src/seeds/candid_loader.py
```

**Expected Output**:
```
============================================================
CANDID API - OPERA COMPANY LOADER
============================================================
✓ Candid API client initialized

Searching for opera companies (NTEE: A6E)...
✓ Found 87 opera companies

=== SAMPLE RESULTS ===

1. Metropolitan Opera Association Inc
   EIN: 131741186
   Location: New York, NY
   Revenue: $312,416,635
   Website: http://www.metopera.org

2. San Francisco Opera Association
   EIN: 941156998
   Location: San Francisco, CA
   Revenue: $74,185,829
   Website: http://www.sfopera.com
...

Loading 87 organizations to PostgreSQL...
✓ Loaded 87 organizations to seed_candid_nonprofits
```

---

## Step 4: Query the Data

```bash
# Connect to PostgreSQL
psql -d opera_research
```

```sql
-- View opera companies
SELECT
    legal_name,
    city,
    state,
    revenue,
    website
FROM seed_candid_nonprofits
WHERE ntee_code = 'A6E'
ORDER BY revenue DESC
LIMIT 10;

-- Count by state
SELECT
    state,
    COUNT(*) as num_companies,
    SUM(revenue) as total_revenue
FROM seed_candid_nonprofits
WHERE ntee_code = 'A6E'
GROUP BY state
ORDER BY num_companies DESC;

-- Companies with websites
SELECT
    COUNT(*) FILTER (WHERE website IS NOT NULL) as has_website,
    COUNT(*) FILTER (WHERE website IS NULL) as missing_website,
    COUNT(*) as total
FROM seed_candid_nonprofits
WHERE ntee_code = 'A6E';
```

---

## Step 5: Enrich with Websites (Manual)

Many companies may not have websites in Candid data. You'll need to enrich:

```sql
-- Insert into website enrichment table
INSERT INTO seed_company_websites (
    id,
    company_name,
    website_url,
    season_page_url,
    ein,
    candid_match_id
) VALUES (
    gen_random_uuid(),
    'Metropolitan Opera',
    'https://www.metopera.org',
    'https://www.metopera.org/season/2024-25-season/',
    '131741186',
    (SELECT id FROM seed_candid_nonprofits WHERE ein = '131741186')
);
```

---

## Step 6: Generate Scraping Targets

```sql
-- Get opera companies with websites ready to scrape
SELECT
    c.legal_name,
    c.city,
    c.state,
    w.website_url,
    w.season_page_url,
    c.revenue
FROM seed_candid_nonprofits c
JOIN seed_company_websites w ON c.ein = w.ein
WHERE c.ntee_code = 'A6E'
  AND w.verified = TRUE
ORDER BY c.revenue DESC;
```

---

## Understanding NTEE Codes

**NTEE**: National Taxonomy of Exempt Entities (IRS classification)

**Opera-Related Codes**:
- `A6E` - **Opera** (most specific)
- `A60` - Performing Arts Organizations
- `A65` - Theater
- `A6A` - Ballet
- `A6B` - Music
- `A6C` - Singing, Choral

**Recommended**: Use `A6E` only for pure opera companies.

---

## Data Fields Available

From Candid API:
```json
{
  "ein": "131741186",
  "name": "Metropolitan Opera Association Inc",
  "dba_names": ["The Met", "Metropolitan Opera"],
  "ntee_code": "A6E",
  "city": "New York",
  "state": "NY",
  "zip": "10023",
  "revenue": 312416635.00,
  "expenses": 298437219.00,
  "assets": 454827163.00,
  "mission": "To create and present world-class opera...",
  "website": "http://www.metopera.org",
  "phone": "(212) 362-6000",
  "fiscal_year_end": "2023-07-31"
}
```

---

## Troubleshooting

### Error: "Invalid API key"
- Check `.env` file has correct key
- Verify no extra spaces or quotes
- Test key at: https://developer.candid.org/

### Error: "Rate limit exceeded"
- Free tier: 100 requests/month
- Wait until next month or upgrade plan
- Cache results in database to avoid re-fetching

### No results found
- NTEE code might be wrong
- Try broader search: `["A6E", "A60"]`
- Check if state filter is too restrictive

---

## Next Steps

After loading Candid data:

1. ✅ **Enrich websites** (manual or semi-automated)
2. ✅ **Generate scraping targets** from `seed_company_websites`
3. ✅ **Run web scraper** on enriched companies
4. ✅ **Match with IRS 990 data** for historical financials
5. ✅ **Build dbt models** to integrate all sources

---

## Costs & Limits

| Plan | Requests/Month | Cost |
|------|----------------|------|
| Free | 100 | $0 |
| Basic | 5,000 | $500 |
| Pro | 50,000 | Custom |

**Recommendation**: Start with free tier (sufficient for 100 companies).

---

## Related Documentation

- [DATA_SOURCES_STRATEGY.md](DATA_SOURCES_STRATEGY.md) - Multi-source integration
- [QUICKSTART.md](../QUICKSTART.md) - Getting started
- [Candid API Docs](https://developer.candid.org/reference/essentials-v3-api)

---

**Last Updated**: October 26, 2024
