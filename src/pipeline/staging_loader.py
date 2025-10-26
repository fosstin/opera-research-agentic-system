"""
Data loader for staging tables.

Loads scraped HTML and LLM extractions into PostgreSQL staging tables.

ELT Flow:
1. Scrape HTML → Load to stg_scraped_pages
2. Extract with LLM → Load to stg_llm_extractions
3. Log operations → stg_scrape_logs, stg_extraction_logs
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.db.connectors import SessionLocal, get_engine
from backend.db.staging_models import ScrapedPage, LLMExtraction, ScrapeLog, ExtractionLog
from src.scraping.compliant_scraper import CompliantOperaScraper
from src.extraction.llm_extractor import LLMExtractor


class StagingLoader:
    """Load scraped data and extractions into staging tables."""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize loader.

        Args:
            db: SQLAlchemy session (optional, will create if not provided)
        """
        self.db = db or SessionLocal()
        self.owns_session = db is None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session if we own it."""
        if self.owns_session:
            self.db.close()

    def load_scraped_page(
        self,
        url: str,
        html_content: str,
        domain: str,
        company_name: Optional[str] = None,
        status_code: int = 200,
        scraper_version: str = "1.0.0",
        user_agent: str = "OperaResearchBot/1.0"
    ) -> ScrapedPage:
        """
        Load scraped HTML into stg_scraped_pages.

        Args:
            url: Source URL
            html_content: Raw HTML
            domain: Domain name
            company_name: Opera company name (optional)
            status_code: HTTP status code
            scraper_version: Version of scraper
            user_agent: User agent string

        Returns:
            Created ScrapedPage record
        """
        # Check if URL already exists
        existing = self.db.query(ScrapedPage).filter(ScrapedPage.url == url).first()

        if existing:
            # Update existing record
            existing.html_content = html_content
            existing.status_code = status_code
            existing.scraped_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing

        # Create new record
        scraped_page = ScrapedPage(
            id=uuid.uuid4(),
            url=url,
            domain=domain,
            company_name=company_name,
            html_content=html_content,
            status_code=status_code,
            scraper_version=scraper_version,
            user_agent=user_agent,
            is_processed=False,
            scraped_at=datetime.utcnow()
        )

        self.db.add(scraped_page)
        self.db.commit()
        self.db.refresh(scraped_page)

        return scraped_page

    def load_llm_extraction(
        self,
        scraped_page_id: uuid.UUID,
        extraction_result: Dict[str, Any],
        extraction_type: str = "production",
        schema_version: str = "1.0"
    ) -> LLMExtraction:
        """
        Load LLM extraction result into stg_llm_extractions.

        Args:
            scraped_page_id: ID of scraped page
            extraction_result: Result from LLMExtractor
            extraction_type: Type of extraction
            schema_version: Schema version

        Returns:
            Created LLMExtraction record
        """
        extraction = LLMExtraction(
            id=uuid.uuid4(),
            scraped_page_id=scraped_page_id,
            extraction_type=extraction_type,
            schema_version=schema_version,
            raw_response=extraction_result.get("raw_response"),
            parsed_data=extraction_result.get("parsed_data"),
            llm_model=extraction_result.get("llm_model"),
            llm_provider=extraction_result.get("llm_provider"),
            tokens_input=extraction_result.get("tokens_input"),
            tokens_output=extraction_result.get("tokens_output"),
            tokens_total=extraction_result.get("tokens_total"),
            estimated_cost_usd=extraction_result.get("estimated_cost_usd"),
            confidence_score=extraction_result.get("confidence_score"),
            processing_time_seconds=extraction_result.get("processing_time_seconds"),
            extraction_error=extraction_result.get("extraction_error"),
            is_validated=extraction_result.get("success", False),
            extracted_at=datetime.utcnow()
        )

        self.db.add(extraction)
        self.db.commit()
        self.db.refresh(extraction)

        # Mark scraped page as processed
        scraped_page = self.db.query(ScrapedPage).filter(ScrapedPage.id == scraped_page_id).first()
        if scraped_page:
            scraped_page.is_processed = True
            scraped_page.processed_at = datetime.utcnow()
            self.db.commit()

        return extraction

    def log_scrape_operation(
        self,
        url: str,
        domain: str,
        is_success: bool,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        robots_txt_allowed: Optional[bool] = None,
        rate_limit_wait_ms: Optional[int] = None,
        used_cache: bool = False,
        batch_id: Optional[uuid.UUID] = None
    ) -> ScrapeLog:
        """
        Log scrape operation to stg_scrape_logs.

        Args:
            url: Scraped URL
            domain: Domain
            is_success: Whether scrape succeeded
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            error_type: Error type if failed
            error_message: Error message if failed
            robots_txt_allowed: Whether robots.txt allowed
            rate_limit_wait_ms: Rate limit wait time
            used_cache: Whether cache was used
            batch_id: Batch ID for grouping

        Returns:
            Created ScrapeLog record
        """
        log = ScrapeLog(
            id=uuid.uuid4(),
            url=url,
            domain=domain,
            is_success=is_success,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_type=error_type,
            error_message=error_message,
            robots_txt_allowed=robots_txt_allowed,
            rate_limit_wait_ms=rate_limit_wait_ms,
            used_cache=used_cache,
            batch_id=batch_id,
            scraped_at=datetime.utcnow()
        )

        self.db.add(log)
        self.db.commit()

        return log

    def get_unprocessed_pages(self, limit: int = 10) -> List[ScrapedPage]:
        """
        Get unprocessed scraped pages.

        Args:
            limit: Maximum number of pages to return

        Returns:
            List of unprocessed ScrapedPage records
        """
        return self.db.query(ScrapedPage).filter(
            ScrapedPage.is_processed == False
        ).limit(limit).all()

    def get_extraction_stats(self) -> Dict[str, Any]:
        """
        Get extraction statistics.

        Returns:
            Dictionary with stats
        """
        total_pages = self.db.query(ScrapedPage).count()
        processed_pages = self.db.query(ScrapedPage).filter(
            ScrapedPage.is_processed == True
        ).count()
        total_extractions = self.db.query(LLMExtraction).count()
        successful_extractions = self.db.query(LLMExtraction).filter(
            LLMExtraction.is_validated == True
        ).count()

        # Calculate total cost
        cost_result = self.db.execute(
            text("SELECT SUM(estimated_cost_usd) FROM stg_llm_extractions")
        ).scalar()
        total_cost = float(cost_result) if cost_result else 0.0

        # Calculate total tokens
        tokens_result = self.db.execute(
            text("SELECT SUM(tokens_total) FROM stg_llm_extractions")
        ).scalar()
        total_tokens = int(tokens_result) if tokens_result else 0

        return {
            "total_pages_scraped": total_pages,
            "pages_processed": processed_pages,
            "pages_pending": total_pages - processed_pages,
            "total_extractions": total_extractions,
            "successful_extractions": successful_extractions,
            "failed_extractions": total_extractions - successful_extractions,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens
        }


def scrape_and_load(
    urls: List[str],
    provider: str = "openai",
    batch_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    End-to-end: Scrape URLs, extract data, load to staging.

    Args:
        urls: List of URLs to scrape
        provider: LLM provider ("openai" or "gemini")
        batch_name: Optional batch name for grouping

    Returns:
        Summary statistics
    """
    batch_id = uuid.uuid4()

    # Initialize scraper and extractor
    scraper = CompliantOperaScraper(
        user_agent=os.getenv("SCRAPER_USER_AGENT", "OperaResearchBot/1.0"),
        contact_info=os.getenv("SCRAPER_CONTACT_INFO", "https://github.com/austinkness/opera-research-agentic-system"),
        respect_robots_txt=True,
        enable_rate_limiting=True,
        enable_caching=True,
        requests_per_second=1.0,
        min_delay_seconds=2.0,
        cache_ttl_seconds=86400
    )

    extractor = LLMExtractor(provider=provider)

    results = {
        "batch_id": str(batch_id),
        "batch_name": batch_name,
        "urls_processed": 0,
        "successful_scrapes": 0,
        "failed_scrapes": 0,
        "successful_extractions": 0,
        "failed_extractions": 0,
        "total_cost_usd": 0.0
    }

    with StagingLoader() as loader:
        for url in urls:
            print(f"\nProcessing: {url}")

            # Scrape
            try:
                html = scraper.fetch_page(url)
                if html:
                    # Extract domain
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc

                    # Load to staging
                    scraped_page = loader.load_scraped_page(
                        url=url,
                        html_content=html,
                        domain=domain
                    )

                    # Log successful scrape
                    loader.log_scrape_operation(
                        url=url,
                        domain=domain,
                        is_success=True,
                        status_code=200,
                        batch_id=batch_id
                    )

                    results["successful_scrapes"] += 1

                    # Extract data with LLM
                    print(f"  Extracting data with {provider}...")
                    extraction_result = extractor.extract_production_data(html, url)

                    # Load extraction to staging
                    loader.load_llm_extraction(
                        scraped_page_id=scraped_page.id,
                        extraction_result=extraction_result
                    )

                    if extraction_result.get("success"):
                        results["successful_extractions"] += 1
                        print(f"  ✓ Extracted {len(extraction_result['parsed_data'].get('productions', []))} productions")
                    else:
                        results["failed_extractions"] += 1
                        print(f"  ✗ Extraction failed: {extraction_result.get('extraction_error')}")

                    results["total_cost_usd"] += extraction_result.get("estimated_cost_usd", 0.0)

                else:
                    # Log failed scrape
                    loader.log_scrape_operation(
                        url=url,
                        domain=urlparse(url).netloc,
                        is_success=False,
                        error_type="no_content",
                        error_message="Scraper returned no content",
                        batch_id=batch_id
                    )
                    results["failed_scrapes"] += 1

            except Exception as e:
                print(f"  ✗ Error: {e}")
                loader.log_scrape_operation(
                    url=url,
                    domain=urlparse(url).netloc if url else "unknown",
                    is_success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    batch_id=batch_id
                )
                results["failed_scrapes"] += 1

            results["urls_processed"] += 1

    return results


def test_staging_loader():
    """Test the staging loader."""

    print("Testing Staging Loader...")

    # Test URLs
    test_urls = [
        "https://www.metopera.org/season/2024-25-season/",
    ]

    # Run scrape and load
    provider = os.getenv("AI_PROVIDER", "openai")
    print(f"\nUsing LLM provider: {provider}")

    results = scrape_and_load(
        urls=test_urls,
        provider=provider,
        batch_name="test_batch"
    )

    print("\n" + "="*60)
    print("BATCH RESULTS")
    print("="*60)
    print(f"Batch ID: {results['batch_id']}")
    print(f"URLs processed: {results['urls_processed']}")
    print(f"Successful scrapes: {results['successful_scrapes']}")
    print(f"Failed scrapes: {results['failed_scrapes']}")
    print(f"Successful extractions: {results['successful_extractions']}")
    print(f"Failed extractions: {results['failed_extractions']}")
    print(f"Total cost: ${results['total_cost_usd']:.6f}")

    # Get overall stats
    with StagingLoader() as loader:
        stats = loader.get_extraction_stats()

        print("\n" + "="*60)
        print("OVERALL STATS")
        print("="*60)
        print(f"Total pages scraped: {stats['total_pages_scraped']}")
        print(f"Pages processed: {stats['pages_processed']}")
        print(f"Pages pending: {stats['pages_pending']}")
        print(f"Total extractions: {stats['total_extractions']}")
        print(f"Successful extractions: {stats['successful_extractions']}")
        print(f"Failed extractions: {stats['failed_extractions']}")
        print(f"Total cost: ${stats['total_cost_usd']:.6f}")
        print(f"Total tokens: {stats['total_tokens']:,}")


if __name__ == "__main__":
    test_staging_loader()
