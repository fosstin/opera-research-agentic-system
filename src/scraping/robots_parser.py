"""
Robots.txt parser and compliance checker for ethical web scraping.
"""
import urllib.robotparser
from urllib.parse import urlparse, urljoin
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Handles robots.txt parsing and compliance checking."""

    def __init__(self, user_agent: str = "*", cache_duration_hours: int = 24):
        """
        Initialize the robots.txt checker.

        Args:
            user_agent: User agent to check permissions for
            cache_duration_hours: How long to cache robots.txt files
        """
        self.user_agent = user_agent
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache: Dict[str, Dict] = {}

    def _get_robots_url(self, url: str) -> str:
        """
        Get the robots.txt URL for a given website URL.

        Args:
            url: Website URL

        Returns:
            robots.txt URL
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _fetch_robots_txt(self, robots_url: str) -> Optional[str]:
        """
        Fetch robots.txt content.

        Args:
            robots_url: URL to robots.txt

        Returns:
            robots.txt content or None if not found
        """
        try:
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully fetched robots.txt from {robots_url}")
                return response.text
            elif response.status_code == 404:
                logger.info(f"No robots.txt found at {robots_url} (404) - all crawling allowed")
                return None
            else:
                logger.warning(f"Unexpected status {response.status_code} for robots.txt at {robots_url}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error fetching robots.txt from {robots_url}: {e}")
            return None

    def _parse_robots_txt(self, robots_url: str, content: Optional[str]) -> urllib.robotparser.RobotFileParser:
        """
        Parse robots.txt content.

        Args:
            robots_url: URL to robots.txt
            content: robots.txt content

        Returns:
            RobotFileParser object
        """
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)

        if content:
            # Parse the content directly
            parser.parse(content.splitlines())
        else:
            # No robots.txt found - allow everything
            parser.parse([])

        return parser

    def _get_cached_parser(self, robots_url: str) -> Optional[urllib.robotparser.RobotFileParser]:
        """
        Get cached robots.txt parser if still valid.

        Args:
            robots_url: URL to robots.txt

        Returns:
            Cached parser or None if expired/not found
        """
        if robots_url in self.cache:
            cached = self.cache[robots_url]
            if datetime.now() - cached['timestamp'] < self.cache_duration:
                logger.debug(f"Using cached robots.txt for {robots_url}")
                return cached['parser']
            else:
                logger.debug(f"Cache expired for {robots_url}")
                del self.cache[robots_url]
        return None

    def get_parser(self, url: str) -> urllib.robotparser.RobotFileParser:
        """
        Get robots.txt parser for a URL, using cache if available.

        Args:
            url: Website URL to check

        Returns:
            RobotFileParser object
        """
        robots_url = self._get_robots_url(url)

        # Check cache first
        cached_parser = self._get_cached_parser(robots_url)
        if cached_parser:
            return cached_parser

        # Fetch and parse robots.txt
        content = self._fetch_robots_txt(robots_url)
        parser = self._parse_robots_txt(robots_url, content)

        # Cache the parser
        self.cache[robots_url] = {
            'parser': parser,
            'timestamp': datetime.now()
        }

        return parser

    def can_fetch(self, url: str) -> bool:
        """
        Check if the URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed to fetch, False otherwise
        """
        try:
            parser = self.get_parser(url)
            can_fetch = parser.can_fetch(self.user_agent, url)

            if not can_fetch:
                logger.warning(f"robots.txt disallows fetching {url} for user-agent '{self.user_agent}'")
            else:
                logger.debug(f"robots.txt allows fetching {url}")

            return can_fetch
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # Fail open - if we can't check, assume allowed but log it
            logger.warning(f"Proceeding with caution for {url} due to robots.txt check error")
            return True

    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt.

        Args:
            url: URL to check

        Returns:
            Crawl delay in seconds, or None if not specified
        """
        try:
            parser = self.get_parser(url)
            delay = parser.crawl_delay(self.user_agent)

            if delay:
                logger.info(f"robots.txt specifies crawl delay of {delay}s for {url}")

            return delay
        except Exception as e:
            logger.error(f"Error getting crawl delay for {url}: {e}")
            return None

    def get_request_rate(self, url: str) -> Optional[tuple]:
        """
        Get the request rate specified in robots.txt.

        Args:
            url: URL to check

        Returns:
            Tuple of (requests, seconds) or None if not specified
        """
        try:
            parser = self.get_parser(url)
            rate = parser.request_rate(self.user_agent)

            if rate:
                logger.info(f"robots.txt specifies request rate of {rate.requests}/{rate.seconds}s for {url}")
                return (rate.requests, rate.seconds)

            return None
        except Exception as e:
            logger.error(f"Error getting request rate for {url}: {e}")
            return None

    def clear_cache(self):
        """Clear the robots.txt cache."""
        self.cache.clear()
        logger.info("Cleared robots.txt cache")


def test_robots_checker():
    """Test the robots checker."""
    checker = RobotsChecker(user_agent="OperaResearchBot/1.0")

    test_urls = [
        "https://www.metopera.org/",
        "https://www.metopera.org/about/",
        "https://www.roh.org.uk/",
    ]

    print("\n=== Testing Robots.txt Checker ===\n")

    for url in test_urls:
        print(f"URL: {url}")
        can_fetch = checker.can_fetch(url)
        print(f"  Can fetch: {can_fetch}")

        delay = checker.get_crawl_delay(url)
        if delay:
            print(f"  Crawl delay: {delay}s")

        rate = checker.get_request_rate(url)
        if rate:
            print(f"  Request rate: {rate[0]} requests per {rate[1]}s")

        print()


if __name__ == "__main__":
    test_robots_checker()
