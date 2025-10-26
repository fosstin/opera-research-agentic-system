"""
Candid API Integration for Opera Company Data

This module fetches nonprofit organization data from Candid's API,
focusing on opera companies (NTEE code A6E).

API Documentation: https://developer.candid.org/reference/essentials-v3-api
Data Portal: https://data.candid.org/

Candid provides:
- Current year financial data (most recent 990)
- Organization details (name, EIN, location, mission)
- Contact information (website, phone)
- NTEE classification codes

For historical financial data, use IRS 990 filings separately.
"""

import os
import requests
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.connectors import SessionLocal
from dotenv import load_dotenv

load_dotenv()


class CandidAPIClient:
    """Client for Candid (GuideStar) Essentials API v3."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Candid API client.

        Args:
            api_key: Candid API subscription key (from environment if not provided)
        """
        self.api_key = api_key or os.getenv("CANDID_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CANDID_API_KEY not found. "
                "Get your key at: https://developer.candid.org/"
            )

        self.base_url = "https://api.candid.org/essentials/v3"
        self.headers = {
            "Subscription-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def search_organizations(
        self,
        search_terms: Optional[str] = None,
        ntee_codes: Optional[List[str]] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search for organizations using Candid API.

        Args:
            search_terms: Free text search (e.g., "opera")
            ntee_codes: List of NTEE codes (e.g., ["A6E", "A60"])
            state: Two-letter state code
            city: City name
            limit: Number of results per page (max 100)
            offset: Pagination offset

        Returns:
            API response with organization data

        Example:
            >>> client = CandidAPIClient()
            >>> results = client.search_organizations(
            ...     ntee_codes=["A6E"],
            ...     state="NY",
            ...     limit=100
            ... )
        """
        url = f"{self.base_url}/search"

        # Build search payload
        payload = {
            "limit": limit,
            "offset": offset
        }

        if search_terms:
            payload["search_terms"] = search_terms

        if ntee_codes or state or city:
            payload["filters"] = {}

            if ntee_codes:
                payload["filters"]["ntee_codes"] = ntee_codes

            if state:
                payload["filters"]["state"] = state

            if city:
                payload["filters"]["city"] = city

        # Make API request
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Invalid API key. Check CANDID_API_KEY environment variable.")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded. Upgrade your Candid API plan.")
            else:
                raise RuntimeError(f"Candid API error: {e}")

    def get_organization(self, ein: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific organization by EIN.

        Args:
            ein: IRS Employer Identification Number (9 digits)

        Returns:
            Organization details

        Example:
            >>> client = CandidAPIClient()
            >>> org = client.get_organization("131741186")  # Met Opera
        """
        url = f"{self.base_url}/organizations/{ein}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise ValueError(f"Organization with EIN {ein} not found.")
            else:
                raise RuntimeError(f"Candid API error: {e}")

    def search_opera_companies(
        self,
        state: Optional[str] = None,
        include_all_performing_arts: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search specifically for opera companies.

        Args:
            state: Filter by state (None = all states)
            include_all_performing_arts: If True, include broader NTEE codes

        Returns:
            List of opera organizations

        NTEE Codes:
            - A6E: Opera-specific
            - A60: Performing Arts Organizations (general)
            - A65: Theater
        """
        # Define NTEE codes
        if include_all_performing_arts:
            ntee_codes = ["A6E", "A60", "A65", "A6A", "A6B", "A6C"]
        else:
            ntee_codes = ["A6E"]  # Opera-specific only

        all_results = []
        offset = 0
        limit = 100

        while True:
            response = self.search_organizations(
                ntee_codes=ntee_codes,
                state=state,
                limit=limit,
                offset=offset
            )

            organizations = response.get("organizations", [])
            if not organizations:
                break

            all_results.extend(organizations)

            # Check if there are more results
            total_count = response.get("total_count", 0)
            if offset + limit >= total_count:
                break

            offset += limit

        return all_results


def load_candid_data_to_postgres(
    organizations: List[Dict[str, Any]],
    db: Optional[Session] = None
) -> int:
    """
    Load Candid organization data to PostgreSQL seed table.

    Args:
        organizations: List of organization dicts from Candid API
        db: SQLAlchemy session

    Returns:
        Number of organizations loaded
    """
    if db is None:
        db = SessionLocal()
        owns_session = True
    else:
        owns_session = False

    try:
        loaded_count = 0

        for org in organizations:
            # Extract fields
            ein = org.get("ein")
            if not ein:
                continue

            # Check if already exists
            existing = db.execute(
                "SELECT id FROM seed_candid_nonprofits WHERE ein = :ein",
                {"ein": ein}
            ).fetchone()

            if existing:
                # Update existing
                db.execute("""
                    UPDATE seed_candid_nonprofits
                    SET
                        legal_name = :legal_name,
                        dba_names = :dba_names,
                        ntee_code = :ntee_code,
                        city = :city,
                        state = :state,
                        zip = :zip,
                        revenue = :revenue,
                        expenses = :expenses,
                        assets = :assets,
                        mission = :mission,
                        website = :website,
                        phone = :phone,
                        fiscal_year_end = :fiscal_year_end,
                        api_response = :api_response,
                        loaded_at = :loaded_at
                    WHERE ein = :ein
                """, {
                    "ein": ein,
                    "legal_name": org.get("name"),
                    "dba_names": json.dumps(org.get("dba_names", [])),
                    "ntee_code": org.get("ntee_code"),
                    "city": org.get("city"),
                    "state": org.get("state"),
                    "zip": org.get("zip"),
                    "revenue": org.get("revenue"),
                    "expenses": org.get("expenses"),
                    "assets": org.get("assets"),
                    "mission": org.get("mission"),
                    "website": org.get("website"),
                    "phone": org.get("phone"),
                    "fiscal_year_end": org.get("fiscal_year_end"),
                    "api_response": json.dumps(org),
                    "loaded_at": datetime.utcnow()
                })
            else:
                # Insert new
                db.execute("""
                    INSERT INTO seed_candid_nonprofits (
                        id, ein, legal_name, dba_names, ntee_code,
                        city, state, zip, revenue, expenses, assets,
                        mission, website, phone, fiscal_year_end,
                        api_response, loaded_at
                    ) VALUES (
                        :id, :ein, :legal_name, :dba_names, :ntee_code,
                        :city, :state, :zip, :revenue, :expenses, :assets,
                        :mission, :website, :phone, :fiscal_year_end,
                        :api_response, :loaded_at
                    )
                """, {
                    "id": str(uuid.uuid4()),
                    "ein": ein,
                    "legal_name": org.get("name"),
                    "dba_names": json.dumps(org.get("dba_names", [])),
                    "ntee_code": org.get("ntee_code"),
                    "city": org.get("city"),
                    "state": org.get("state"),
                    "zip": org.get("zip"),
                    "revenue": org.get("revenue"),
                    "expenses": org.get("expenses"),
                    "assets": org.get("assets"),
                    "mission": org.get("mission"),
                    "website": org.get("website"),
                    "phone": org.get("phone"),
                    "fiscal_year_end": org.get("fiscal_year_end"),
                    "api_response": json.dumps(org),
                    "loaded_at": datetime.utcnow()
                })

            loaded_count += 1

        db.commit()
        return loaded_count

    finally:
        if owns_session:
            db.close()


def main():
    """
    Main function to fetch opera companies from Candid and load to PostgreSQL.
    """
    print("=" * 60)
    print("CANDID API - OPERA COMPANY LOADER")
    print("=" * 60)

    # Initialize client
    try:
        client = CandidAPIClient()
        print("✓ Candid API client initialized")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("\nTo get a Candid API key:")
        print("1. Visit: https://developer.candid.org/")
        print("2. Register for a free account (100 requests/month)")
        print("3. Copy your Subscription Key")
        print("4. Add to .env: CANDID_API_KEY=your_key_here")
        return

    # Search for opera companies
    print("\nSearching for opera companies (NTEE: A6E)...")
    try:
        opera_companies = client.search_opera_companies(include_all_performing_arts=False)
        print(f"✓ Found {len(opera_companies)} opera companies")

        # Show sample
        if opera_companies:
            print("\n=== SAMPLE RESULTS ===")
            for i, org in enumerate(opera_companies[:5], 1):
                print(f"\n{i}. {org.get('name')}")
                print(f"   EIN: {org.get('ein')}")
                print(f"   Location: {org.get('city')}, {org.get('state')}")
                print(f"   Revenue: ${org.get('revenue', 0):,.0f}")
                print(f"   Website: {org.get('website', 'N/A')}")

        # Load to PostgreSQL
        print(f"\nLoading {len(opera_companies)} organizations to PostgreSQL...")
        loaded = load_candid_data_to_postgres(opera_companies)
        print(f"✓ Loaded {loaded} organizations to seed_candid_nonprofits")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
