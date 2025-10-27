# IRS 990 Data Integration

## Overview

IRS Form 990 provides detailed financial data for US nonprofit organizations. Unlike Candid (which provides only current-year data), IRS 990 filings go back to 2011, enabling historical trend analysis.

## Data Access Methods

### Option 1: IRS AWS S3 Bucket (Free, Public)

**URL**: `s3://irs-form-990/`

**Contents**:
- XML files for all 990 filings (2011-present)
- JSON index files listing all available filings
- Updated regularly

**Access**:
- No authentication required
- HTTP access: `https://s3.amazonaws.com/irs-form-990/`
- AWS CLI: `aws s3 ls s3://irs-form-990/ --no-sign-request`

### Option 2: IRS Bulk Data Download

**URL**: https://www.irs.gov/charities-non-profits/form-990-series-downloads

**Contents**:
- Bulk downloads of all filings by year
- CSV format available
- Easier for bulk analysis

### Option 3: Third-Party APIs

**ProPublica Nonprofit Explorer API**:
- **URL**: https://projects.propublica.org/nonprofits/api
- **Free**: No authentication required
- **Data**: Parsed 990 data in JSON format
- **Coverage**: 2011-present
- **Easier to use** than raw IRS XML

---

## Recommended Approach: ProPublica API

For this project, use **ProPublica's Nonprofit Explorer API** because:
- ✅ Free, no API key required
- ✅ JSON format (easier than XML)
- ✅ Already parsed and cleaned
- ✅ Search by EIN or organization name
- ✅ Historical data included

### Example API Calls

**Search by Organization Name**:
```bash
curl "https://projects.propublica.org/nonprofits/api/v2/search.json?q=metropolitan+opera"
```

**Get Organization by EIN**:
```bash
curl "https://projects.propublica.org/nonprofits/api/v2/organizations/131741186.json"
```

**Get Specific 990 Filing**:
```bash
curl "https://projects.propublica.org/nonprofits/api/v2/organizations/131741186/202107.json"
```

---

## Implementation Plan

### Phase 1: Use ProPublica API (Recommended)

1. No API key needed
2. Search for opera companies by name
3. Get their EINs
4. Fetch historical 990 data
5. Load to `seed_irs_990_filings`

### Phase 2: Fall Back to AWS S3 (If Needed)

1. Use AWS CLI to list available files
2. Download XML for specific EINs
3. Parse XML to extract financial data
4. Load to database

---

## Data Fields Available

From 990 filings:

**Revenue Sources**:
- Contributions and grants
- Program service revenue
- Investment income
- Other revenue

**Expenses**:
- Program expenses
- Management expenses
- Fundraising expenses

**Assets & Liabilities**:
- Total assets (end of year)
- Total liabilities
- Net assets

**Executive Compensation**:
- Officer names and titles
- Compensation amounts
- Benefits

**Program Information**:
- Mission statement
- Program descriptions
- Grants awarded

---

## Sample Data Structure (ProPublica)

```json
{
  "organization": {
    "ein": "131741186",
    "name": "METROPOLITAN OPERA ASSOCIATION INC",
    "city": "NEW YORK",
    "state": "NY",
    "ntee_code": "A68"
  },
  "filings_with_data": [
    {
      "tax_prd": "202107",
      "tax_prd_yr": "2021",
      "totrevenue": 123456789,
      "totfuncexpns": 98765432,
      "totassetsend": 456789012,
      "totliabend": 123456789
    }
  ]
}
```

---

## Next Steps

1. ✅ Create seed table for IRS data (done)
2. ⏳ Update loader to use ProPublica API
3. ⏳ Test with Met Opera
4. ⏳ Bulk load for all opera companies
5. ⏳ Create dbt models to integrate with Candid data

---

## Cost

**Free** - Both IRS S3 and ProPublica API are free

---

## Update Status

The current `irs_990_loader.py` needs to be updated to:
1. Use ProPublica API instead of direct S3 access
2. Handle JSON responses instead of XML parsing
3. Add retry logic and error handling

This will be implemented once Candid API data is loaded and we have a list of EINs to fetch.

---

**Last Updated**: October 26, 2024
**Status**: Pending ProPublica API integration
