"""
Compliance middleware for ethical and legal web scraping.
Integrates robots.txt checking, rate limiting, and caching.
"""
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from .robots_parser import RobotsChecker
from .rate_limiter import RateLimiter
from .cache import ScraperCache

logger = logging.getLogger(__name__)


class ComplianceMiddleware:
    """
    Middleware that wraps scrapers with compliance features.
    Enforces robots.txt, rate limiting, caching, and logging.
    """

    def __init__(
        self,
        user_agent: str,
        contact_info: str,
        respect_robots_txt: bool,
        enable_rate_limiting: bool,
        enable_caching: bool,
        requests_per_second: float,
        min_delay_seconds: float,
        cache_ttl_seconds: int,
        cache_dir: str = "data/cache",
        log_requests: bool = True,
        log_file: Optional[str] = "data/scraping_log.jsonl"
    ):
        """
        Initialize compliance middleware.

        IMPORTANT: All parameters are mandatory to ensure you consciously
        make decisions about ethical scraping practices.

        Args:
            user_agent: User agent string (e.g., "MyBot/1.0")
            contact_info: Contact URL or email (REQUIRED for ethical scraping)
            respect_robots_txt: Whether to check robots.txt (should be True)
            enable_rate_limiting: Whether to enforce rate limiting (should be True)
            enable_caching: Whether to cache responses (recommended True)
            requests_per_second: Max requests per second per domain (typically 0.5-2.0)
            min_delay_seconds: Minimum delay between requests (typically 1.0-3.0)
            cache_ttl_seconds: Cache time-to-live in seconds (typically 3600-86400)
            cache_dir: Directory for cache files
            log_requests: Whether to log all requests (recommended True)
            log_file: Path to log file (JSONL format)

        Example:
            middleware = ComplianceMiddleware(
                user_agent="OperaResearchBot/1.0",
                contact_info="https://github.com/your-username/your-repo",
                respect_robots_txt=True,
                enable_rate_limiting=True,
                enable_caching=True,
                requests_per_second=1.0,
                min_delay_seconds=2.0,
                cache_ttl_seconds=86400
            )
        """
        # Validate mandatory parameters
        if not user_agent or not user_agent.strip():
            raise ValueError("user_agent is required and cannot be empty")

        if not contact_info or not contact_info.strip():
            raise ValueError(
                "contact_info is required. Provide an email or URL where "
                "website owners can contact you about scraping concerns."
            )

        if not isinstance(respect_robots_txt, bool):
            raise ValueError("respect_robots_txt must be explicitly set to True or False")

        if not isinstance(enable_rate_limiting, bool):
            raise ValueError("enable_rate_limiting must be explicitly set to True or False")

        if not isinstance(enable_caching, bool):
            raise ValueError("enable_caching must be explicitly set to True or False")

        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than 0")

        if min_delay_seconds < 0:
            raise ValueError("min_delay_seconds must be non-negative")

        if cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be greater than 0")

        # Build full user agent with contact info
        self.user_agent = f"{user_agent} (+{contact_info})"
        self.respect_robots_txt = respect_robots_txt
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_caching = enable_caching
        self.log_requests = log_requests
        self.log_file = log_file

        # Initialize components
        self.robots_checker = RobotsChecker(user_agent=user_agent) if respect_robots_txt else None
        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            min_delay_seconds=min_delay_seconds
        ) if enable_rate_limiting else None
        self.cache = ScraperCache(
            cache_dir=cache_dir,
            ttl_seconds=cache_ttl_seconds,
            enabled=enable_caching
        )

        # Request statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'robots_blocked': 0,
            'errors': 0
        }

        # Log compliance configuration
        logger.info(f"ComplianceMiddleware initialized with user-agent: {self.user_agent}")
        logger.info(f"Compliance settings:")
        logger.info(f"  - Respect robots.txt: {respect_robots_txt}")
        logger.info(f"  - Rate limiting: {enable_rate_limiting} ({requests_per_second} req/s, {min_delay_seconds}s delay)")
        logger.info(f"  - Caching: {enable_caching} (TTL: {cache_ttl_seconds}s)")

        if not respect_robots_txt:
            logger.warning("⚠️  robots.txt checking is DISABLED - this may violate website terms")
        if not enable_rate_limiting:
            logger.warning("⚠️  Rate limiting is DISABLED - this may overwhelm servers")

    def _log_request(self, url: str, status: str, details: Optional[Dict] = None):
        """
        Log a request to the log file.

        Args:
            url: URL requested
            status: Status of request (success, blocked, error, cached)
            details: Additional details to log
        """
        if not self.log_requests or not self.log_file:
            return

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'url': url,
            'status': status,
            'user_agent': self.user_agent,
            **(details or {})
        }

        try:
            # Ensure log directory exists
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to JSONL file
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

        except IOError as e:
            logger.error(f"Error writing to log file: {e}")

    def can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False if blocked
        """
        if not self.respect_robots_txt or not self.robots_checker:
            return True

        allowed = self.robots_checker.can_fetch(url)

        if not allowed:
            self.stats['robots_blocked'] += 1
            self._log_request(url, 'blocked_by_robots')
            logger.warning(f"Blocked by robots.txt: {url}")

        return allowed

    def fetch(self, url: str, fetch_function: Callable[[str], Any]) -> Optional[Any]:
        """
        Fetch content with compliance checks.

        Args:
            url: URL to fetch
            fetch_function: Function that performs the actual fetch

        Returns:
            Fetched content or None if blocked/error
        """
        self.stats['total_requests'] += 1

        # Check cache first
        if self.enable_caching:
            cached_content = self.cache.get(url)
            if cached_content is not None:
                self.stats['cache_hits'] += 1
                self._log_request(url, 'cached')
                logger.info(f"Serving from cache: {url}")
                return cached_content
            else:
                self.stats['cache_misses'] += 1

        # Check robots.txt
        if not self.can_fetch(url):
            return None

        # Get crawl delay from robots.txt
        crawl_delay = None
        if self.respect_robots_txt and self.robots_checker:
            crawl_delay = self.robots_checker.get_crawl_delay(url)

        # Apply rate limiting
        if self.enable_rate_limiting and self.rate_limiter:
            self.rate_limiter.wait_if_needed(url, crawl_delay)

        # Perform the fetch
        try:
            logger.info(f"Fetching: {url}")
            content = fetch_function(url)

            # Cache the result
            if self.enable_caching and content is not None:
                self.cache.set(url, content)

            self._log_request(url, 'success', {'cached': self.enable_caching})
            return content

        except Exception as e:
            self.stats['errors'] += 1
            self._log_request(url, 'error', {'error': str(e)})
            logger.error(f"Error fetching {url}: {e}")
            return None

    def get_stats(self) -> Dict:
        """
        Get compliance middleware statistics.

        Returns:
            Dictionary with statistics
        """
        stats = self.stats.copy()

        if self.cache:
            stats['cache_stats'] = self.cache.get_stats()

        if self.rate_limiter:
            stats['rate_limiter_stats'] = self.rate_limiter.get_stats()

        # Calculate cache hit rate
        total_requests = stats['cache_hits'] + stats['cache_misses']
        if total_requests > 0:
            stats['cache_hit_rate'] = round(stats['cache_hits'] / total_requests * 100, 2)
        else:
            stats['cache_hit_rate'] = 0.0

        return stats

    def clear_cache(self) -> int:
        """
        Clear the cache.

        Returns:
            Number of entries cleared
        """
        if self.cache:
            return self.cache.clear()
        return 0

    def clear_expired_cache(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of expired entries cleared
        """
        if self.cache:
            return self.cache.clear_expired()
        return 0


def test_compliance_middleware():
    """Test the compliance middleware."""
    import requests

    def simple_fetch(url: str) -> str:
        """Simple fetch function for testing."""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    print("\n=== Testing Compliance Middleware ===\n")

    middleware = ComplianceMiddleware(
        user_agent="TestBot/1.0",
        contact_info="https://github.com/test/bot",
        respect_robots_txt=True,
        enable_rate_limiting=True,
        enable_caching=True,
        requests_per_second=1.0,
        min_delay_seconds=2.0,
        cache_ttl_seconds=3600
    )

    test_url = "https://www.metopera.org"

    # First fetch (should hit network)
    print(f"First fetch of {test_url}...")
    content1 = middleware.fetch(test_url, simple_fetch)
    print(f"  Fetched {len(content1) if content1 else 0} bytes")

    # Second fetch (should hit cache)
    print(f"\nSecond fetch of {test_url}...")
    content2 = middleware.fetch(test_url, simple_fetch)
    print(f"  Fetched {len(content2) if content2 else 0} bytes")

    # Show stats
    print("\n" + "=" * 50)
    print("Statistics:")
    for key, value in middleware.get_stats().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_compliance_middleware()
