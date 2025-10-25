"""
Main entry point for the Opera Research Agentic System.
Uses the compliant scraper with ethical web scraping practices.
"""
import os
from dotenv import load_dotenv
from scraping.compliant_scraper import CompliantOperaScraper
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    logger.info("Starting Opera Research Agentic System")

    # Initialize compliant scraper with ethical defaults
    scraper = CompliantOperaScraper(
        user_agent=os.getenv('SCRAPER_USER_AGENT', 'OperaResearchBot/1.0'),
        contact_info=os.getenv(
            'SCRAPER_CONTACT_INFO',
            'https://github.com/austinkness/opera-research-agentic-system'
        ),
        respect_robots_txt=True,
        enable_rate_limiting=True,
        enable_caching=True,
        requests_per_second=float(os.getenv('REQUESTS_PER_SECOND', '1.0')),
        min_delay_seconds=float(os.getenv('MIN_DELAY_SECONDS', '2.0')),
        cache_ttl_seconds=int(os.getenv('CACHE_TTL_SECONDS', '86400'))
    )

    # Example opera companies to scrape
    opera_companies = [
        "https://www.metopera.org",
        "https://www.roh.org.uk",
        "https://www.wiener-staatsoper.at",
    ]

    results = []
    for url in opera_companies:
        logger.info(f"Scraping {url}...")
        result = scraper.scrape_basic_info(url)
        results.append(result)

        # Print summary
        if result['success']:
            print(f"\n✓ {url}")
            print(f"  Title: {result['title']}")
            print(f"  Links found: {result['link_count']}")
        else:
            print(f"\n✗ {url}")
            print(f"  Error: {result.get('error')}")

    logger.info(f"Completed scraping {len(results)} websites")
    successful = sum(1 for r in results if r['success'])
    print(f"\n=== Summary ===")
    print(f"Total sites: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")

    # Show compliance statistics
    stats = scraper.get_stats()
    print(f"\n=== Compliance Statistics ===")
    print(f"Cache hit rate: {stats['cache_hit_rate']}%")
    print(f"Robots.txt blocks: {stats['robots_blocked']}")
    print(f"Total requests: {stats['total_requests']}")


if __name__ == "__main__":
    main()
