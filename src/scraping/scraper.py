"""
Web scraper module for opera company websites.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
import logging
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OperaScraper:
    """Simple web scraper for opera company websites."""

    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialize the scraper.

        Args:
            user_agent: Custom user agent string for requests
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (compatible; OperaResearchBot/1.0)'
        })

    def fetch_page(self, url: str, timeout: int = 30) -> Optional[str]:
        """
        Fetch HTML content from a URL.

        Args:
            url: The URL to fetch
            timeout: Request timeout in seconds

        Returns:
            HTML content as string, or None if request fails
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

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
            return {'url': url, 'success': False, 'error': 'Failed to fetch page'}

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


def test_scraper():
    """Test the scraper with a sample URL."""
    scraper = OperaScraper()

    # Test with a well-known opera company
    test_url = "https://www.metopera.org"

    logger.info(f"Testing scraper with {test_url}")
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


if __name__ == "__main__":
    test_scraper()
