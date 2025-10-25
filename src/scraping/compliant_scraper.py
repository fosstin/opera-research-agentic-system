"""
Compliant web scraper that integrates all ethical scraping practices.
This is the recommended scraper to use for production scraping.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
from urllib.parse import urljoin

from .compliance import ComplianceMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompliantOperaScraper:
    """
    Ethical and compliant web scraper for opera company websites.
    Respects robots.txt, implements rate limiting, and caches responses.
    """

    def __init__(
        self,
        user_agent: str,
        contact_info: str,
        respect_robots_txt: bool = True,
        enable_rate_limiting: bool = True,
        enable_caching: bool = True,
        requests_per_second: float = 1.0,
        min_delay_seconds: float = 2.0,
        cache_ttl_seconds: int = 86400,
        timeout: int = 30
    ):
        """
        Initialize the compliant scraper.

        Args:
            user_agent: Bot name and version (e.g., "OperaResearchBot/1.0")
            contact_info: Contact URL or email (REQUIRED)
            respect_robots_txt: Whether to check and respect robots.txt
            enable_rate_limiting: Whether to enforce rate limiting
            enable_caching: Whether to cache responses
            requests_per_second: Max requests per second per domain
            min_delay_seconds: Minimum delay between requests (polite delay)
            cache_ttl_seconds: How long to cache responses
            timeout: Request timeout in seconds
        """
        self.session = requests.Session()
        self.timeout = timeout

        # Initialize compliance middleware
        self.compliance = ComplianceMiddleware(
            user_agent=user_agent,
            contact_info=contact_info,
            respect_robots_txt=respect_robots_txt,
            enable_rate_limiting=enable_rate_limiting,
            enable_caching=enable_caching,
            requests_per_second=requests_per_second,
            min_delay_seconds=min_delay_seconds,
            cache_ttl_seconds=cache_ttl_seconds
        )

        # Set user agent on session
        self.session.headers.update({
            'User-Agent': self.compliance.user_agent
        })

        logger.info(f"CompliantOperaScraper initialized with user-agent: {self.compliance.user_agent}")

    def _fetch_page_internal(self, url: str) -> str:
        """
        Internal fetch function (without compliance checks).

        Args:
            url: URL to fetch

        Returns:
            HTML content

        Raises:
            requests.RequestException: On network errors
        """
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        # Check for X-Robots-Tag header
        robots_tag = response.headers.get('X-Robots-Tag', '')
        if 'noindex' in robots_tag.lower() or 'nofollow' in robots_tag.lower():
            logger.warning(f"X-Robots-Tag detected for {url}: {robots_tag}")

        return response.text

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL with full compliance checks.

        Args:
            url: The URL to fetch

        Returns:
            HTML content as string, or None if blocked or error
        """
        return self.compliance.fetch(url, self._fetch_page_internal)

    def parse_page(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup.

        Args:
            html: HTML content string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')

    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all links from a parsed page.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links

        Returns:
            List of absolute URLs
        """
        links = []
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(base_url, link['href'])
            links.append(absolute_url)
        return links

    def scrape_basic_info(self, url: str) -> Dict[str, any]:
        """
        Scrape basic information from an opera company website.

        Args:
            url: URL of the opera company website

        Returns:
            Dictionary containing basic scraped information
        """
        html = self.fetch_page(url)
        if not html:
            return {'url': url, 'success': False, 'error': 'Failed to fetch page or blocked'}

        soup = self.parse_page(html)

        # Extract basic metadata
        title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})

        # Extract all text content
        text_content = soup.get_text(separator=' ', strip=True)

        # Extract all links
        links = self.extract_links(soup, url)

        return {
            'url': url,
            'success': True,
            'title': title.text.strip() if title else None,
            'description': meta_description.get('content') if meta_description else None,
            'text_length': len(text_content),
            'link_count': len(links),
            'links': links[:50]  # Limit to first 50 links
        }

    def get_stats(self) -> Dict:
        """
        Get scraping statistics including compliance metrics.

        Returns:
            Dictionary with statistics
        """
        return self.compliance.get_stats()

    def clear_cache(self) -> int:
        """
        Clear the scraper cache.

        Returns:
            Number of cache entries cleared
        """
        return self.compliance.clear_cache()


def test_compliant_scraper():
    """Test the compliant scraper with a sample URL."""
    scraper = CompliantOperaScraper(
        user_agent="OperaResearchBot/1.0",
        contact_info="https://github.com/austinkness/opera-research-agentic-system",
        respect_robots_txt=True,
        enable_rate_limiting=True,
        enable_caching=True,
        requests_per_second=1.0,
        min_delay_seconds=2.0
    )

    # Test with a well-known opera company
    test_url = "https://www.metopera.org"

    logger.info(f"Testing compliant scraper with {test_url}")
    result = scraper.scrape_basic_info(test_url)

    print("\n=== Scraping Results ===")
    print(f"URL: {result['url']}")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Title: {result['title']}")
        print(f"Description: {result['description']}")
        print(f"Text Length: {result['text_length']} characters")
        print(f"Links Found: {result['link_count']}")
        print(f"\nFirst 5 links:")
        for link in result['links'][:5]:
            print(f"  - {link}")
    else:
        print(f"Error: {result.get('error')}")

    print("\n=== Compliance Statistics ===")
    stats = scraper.get_stats()
    for key, value in stats.items():
        if not isinstance(value, dict):
            print(f"{key}: {value}")


if __name__ == "__main__":
    test_compliant_scraper()
