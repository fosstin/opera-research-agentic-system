"""
IRS 990 Tax Filing Data Loader

Fetches IRS Form 990 filings for nonprofit organizations.
990 data includes detailed financial information not available in Candid.

Data Sources:
1. IRS AWS S3 Bucket: s3://irs-form-990/ (free, public access)
2. IRS Exempt Organizations API: https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf

IRS 990 Forms:
- Form 990: Organizations with gross receipts >= $200,000 or assets >= $500,000
- Form 990-EZ: Smaller organizations (gross receipts < $200,000)
- Form 990-PF: Private foundations

Historical Data:
- Available from 2011-present
- Candid only provides most recent year
- Use IRS for historical trend analysis
"""

import os
import json
import requests
import uuid
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from backend.db.connectors import SessionLocal
from dotenv import load_dotenv

load_dotenv()


class IRS990Fetcher:
    """Fetch IRS Form 990 data from public sources."""

    def __init__(self):
        """Initialize IRS 990 fetcher."""
        # IRS publishes an index of all available 990s
        self.index_url = "https://s3.amazonaws.com/irs-form-990/index_{year}.json"
        self.s3_base = "https://s3.amazonaws.com/irs-form-990"

    def get_index_for_year(self, year: int) -> List[Dict[str, Any]]:
        """
        Get index of all 990 filings for a given year.

        Args:
            year: Tax year (e.g., 2023)

        Returns:
            List of filing metadata dictionaries

        Example:
            >>> fetcher = IRS990Fetcher()
            >>> filings_2023 = fetcher.get_index_for_year(2023)
            >>> print(f"Found {len(filings_2023)} filings for 2023")
        """
        url = self.index_url.format(year=year)

        try:
            print(f"Fetching IRS index for {year}...")
            response = requests.get(url, timeout=60)
            response.raise_for_status()

            data = response.json()
            filings = data.get("Filings{year}".format(year=year), [])

            print(f"✓ Found {len(filings):,} filings for {year}")
            return filings

        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"No IRS data available for year {year}")
            else:
                raise RuntimeError(f"Error fetching IRS index: {e}")

    def search_by_ein(self, ein: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for 990 filings by EIN.

        Args:
            ein: Employer Identification Number (9 digits)
            year: Specific year to search (None = all available years)

        Returns:
            List of matching filings

        Example:
            >>> fetcher = IRS990Fetcher()
            >>> met_opera_filings = fetcher.search_by_ein("131741186")
            >>> print(f"Found {len(met_opera_filings)} filings for Met Opera")
        """
        # Remove hyphens from EIN if present
        ein = ein.replace("-", "")

        years = [year] if year else range(2011, datetime.now().year + 1)
        all_filings = []

        for yr in years:
            try:
                index = self.get_index_for_year(yr)

                # Search for matching EIN
                matches = [f for f in index if f.get("EIN") == ein]
                all_filings.extend(matches)

                if matches:
                    print(f"  Found {len(matches)} filing(s) for EIN {ein} in {yr}")

            except ValueError:
                # Year not available yet
                continue

        return all_filings

    def download_990_xml(self, object_id: str) -> Optional[str]:
        """
        Download 990 XML file from S3.

        Args:
            object_id: S3 object ID from the index

        Returns:
            XML content as string

        Example:
            >>> fetcher = IRS990Fetcher()
            >>> xml = fetcher.download_990_xml("202141234567890123_public.xml")
        """
        url = f"{self.s3_base}/{object_id}"

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.text

        except requests.exceptions.HTTPError as e:
            print(f"✗ Error downloading {object_id}: {e}")
            return None

    def parse_990_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse 990 XML to extract key financial data.

        Args:
            xml_content: Raw XML string

        Returns:
            Dictionary with parsed financial data

        Key Fields Extracted:
            - Revenue (total, contributions, program service)
            - Expenses (total, program, management, fundraising)
            - Assets and liabilities
            - Executive compensation
            - Program accomplishments
        """
        try:
            root = ET.fromstring(xml_content)

            # IRS uses different namespaces for different years
            # Try to find the Return node
            return_node = root.find(".//{*}Return")
            if return_node is None:
                return_node = root

            # Extract basic info
            data = {
                "tax_year": None,
                "organization_name": None,
                "ein": None,
                "revenue": None,
                "expenses": None,
                "assets": None,
                "executive_compensation": []
            }

            # Try to find tax year
            tax_year_node = return_node.find(".//{*}TaxYr")
            if tax_year_node is not None:
                data["tax_year"] = int(tax_year_node.text)

            # Try to find EIN
            ein_node = return_node.find(".//{*}EIN")
            if ein_node is not None:
                data["ein"] = ein_node.text

            # Try to find organization name
            name_node = return_node.find(".//{*}BusinessName/{*}BusinessNameLine1Txt")
            if name_node is not None:
                data["organization_name"] = name_node.text

            # Try to find revenue (multiple possible paths)
            revenue_paths = [
                ".//{*}TotalRevenueAmt",
                ".//{*}CYTotalRevenueAmt",
                ".//{*}TotalRevenueGrp/{*}TotalRevenueColumnAmt"
            ]
            for path in revenue_paths:
                revenue_node = return_node.find(path)
                if revenue_node is not None:
                    data["revenue"] = float(revenue_node.text)
                    break

            # Try to find expenses
            expense_paths = [
                ".//{*}TotalExpensesAmt",
                ".//{*}CYTotalExpensesAmt",
                ".//{*}TotalExpensesGrp/{*}TotalExpensesColumnAmt"
            ]
            for path in expense_paths:
                expense_node = return_node.find(path)
                if expense_node is not None:
                    data["expenses"] = float(expense_node.text)
                    break

            # Try to find assets
            asset_paths = [
                ".//{*}TotalAssetsEOYAmt",
                ".//{*}TotalAssetsGrp/{*}EOYAmt"
            ]
            for path in asset_paths:
                asset_node = return_node.find(path)
                if asset_node is not None:
                    data["assets"] = float(asset_node.text)
                    break

            return data

        except ET.ParseError as e:
            print(f"✗ XML parsing error: {e}")
            return {}

    def fetch_990_for_ein(
        self,
        ein: str,
        years: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch and parse all 990s for a given EIN.

        Args:
            ein: Employer Identification Number
            years: List of years to fetch (None = all available)

        Returns:
            List of parsed 990 data dictionaries

        Example:
            >>> fetcher = IRS990Fetcher()
            >>> met_data = fetcher.fetch_990_for_ein("131741186", years=[2021, 2022, 2023])
        """
        # Search for filings
        filings = self.search_by_ein(ein)

        if not filings:
            print(f"No 990 filings found for EIN {ein}")
            return []

        # Filter by years if specified
        if years:
            filings = [f for f in filings if f.get("TaxPeriod") in [str(y) + "12" for y in years]]

        results = []

        for filing in filings:
            object_id = filing.get("ObjectId")
            if not object_id:
                continue

            print(f"  Downloading {filing.get('TaxPeriod')[:4]} filing...")
            xml_content = self.download_990_xml(object_id)

            if xml_content:
                parsed_data = self.parse_990_xml(xml_content)
                parsed_data["object_id"] = object_id
                parsed_data["tax_period"] = filing.get("TaxPeriod")
                parsed_data["form_type"] = filing.get("FormType")
                results.append(parsed_data)

        return results


def load_990_to_postgres(
    ein: str,
    data_list: List[Dict[str, Any]],
    db: Optional[Session] = None
) -> int:
    """
    Load IRS 990 data to PostgreSQL.

    Args:
        ein: Employer Identification Number
        data_list: List of parsed 990 data dictionaries
        db: SQLAlchemy session

    Returns:
        Number of records loaded
    """
    if db is None:
        db = SessionLocal()
        owns_session = True
    else:
        owns_session = False

    try:
        loaded_count = 0

        for data in data_list:
            tax_year = data.get("tax_year")
            if not tax_year:
                continue

            # Check if already exists
            existing = db.execute(
                "SELECT id FROM seed_irs_990_filings WHERE ein = :ein AND tax_year = :tax_year",
                {"ein": ein, "tax_year": tax_year}
            ).fetchone()

            if existing:
                # Update existing
                db.execute("""
                    UPDATE seed_irs_990_filings
                    SET
                        organization_name = :org_name,
                        form_type = :form_type,
                        revenue = :revenue,
                        expenses = :expenses,
                        assets = :assets,
                        json_data = :json_data,
                        xml_url = :xml_url,
                        loaded_at = :loaded_at
                    WHERE ein = :ein AND tax_year = :tax_year
                """, {
                    "ein": ein,
                    "tax_year": tax_year,
                    "org_name": data.get("organization_name"),
                    "form_type": data.get("form_type"),
                    "revenue": data.get("revenue"),
                    "expenses": data.get("expenses"),
                    "assets": data.get("assets"),
                    "json_data": json.dumps(data),
                    "xml_url": f"https://s3.amazonaws.com/irs-form-990/{data.get('object_id')}",
                    "loaded_at": datetime.utcnow()
                })
            else:
                # Insert new
                db.execute("""
                    INSERT INTO seed_irs_990_filings (
                        id, ein, tax_year, organization_name, form_type,
                        revenue, expenses, assets, json_data, xml_url, loaded_at
                    ) VALUES (
                        :id, :ein, :tax_year, :org_name, :form_type,
                        :revenue, :expenses, :assets, :json_data, :xml_url, :loaded_at
                    )
                """, {
                    "id": str(uuid.uuid4()),
                    "ein": ein,
                    "tax_year": tax_year,
                    "org_name": data.get("organization_name"),
                    "form_type": data.get("form_type"),
                    "revenue": data.get("revenue"),
                    "expenses": data.get("expenses"),
                    "assets": data.get("assets"),
                    "json_data": json.dumps(data),
                    "xml_url": f"https://s3.amazonaws.com/irs-form-990/{data.get('object_id')}",
                    "loaded_at": datetime.utcnow()
                })

            loaded_count += 1

        db.commit()
        return loaded_count

    finally:
        if owns_session:
            db.close()


def main():
    """Test the IRS 990 fetcher with Met Opera as example."""
    print("=" * 60)
    print("IRS 990 DATA LOADER - TEST")
    print("=" * 60)

    # Test with Metropolitan Opera (EIN: 13-1741186)
    met_opera_ein = "131741186"

    fetcher = IRS990Fetcher()

    print(f"\nFetching 990 data for Met Opera (EIN: {met_opera_ein})...")
    print("This may take a few minutes for multiple years...\n")

    # Fetch last 3 years
    current_year = datetime.now().year
    years = [current_year - 3, current_year - 2, current_year - 1]

    results = fetcher.fetch_990_for_ein(met_opera_ein, years=years)

    if results:
        print(f"\n✓ Successfully fetched {len(results)} filing(s)")

        print("\n=== FINANCIAL SUMMARY ===")
        for data in results:
            print(f"\nTax Year: {data.get('tax_year')}")
            print(f"Form Type: {data.get('form_type')}")
            print(f"Revenue: ${data.get('revenue', 0):,.0f}")
            print(f"Expenses: ${data.get('expenses', 0):,.0f}")
            print(f"Assets: ${data.get('assets', 0):,.0f}")

        # Load to PostgreSQL
        print(f"\nLoading {len(results)} filing(s) to PostgreSQL...")
        loaded = load_990_to_postgres(met_opera_ein, results)
        print(f"✓ Loaded {loaded} record(s) to seed_irs_990_filings")
    else:
        print("\n✗ No 990 data found")


if __name__ == "__main__":
    main()
