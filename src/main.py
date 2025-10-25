"""
Main entry point for the Opera Research Agentic System.
"""
import os
from dotenv import load_dotenv
from scraping.scraper import OperaScraper
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

    # Initialize scraper
    scraper = OperaScraper()

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


if __name__ == "__main__":
    main()
