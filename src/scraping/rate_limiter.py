"""
Rate limiter for ethical and responsible web scraping.
"""
import time
from collections import defaultdict, deque
from typing import Dict, Optional
from urllib.parse import urlparse
import logging
import threading

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter for web scraping.
    Implements both per-domain and global rate limiting.
    """

    def __init__(
        self,
        requests_per_second: float = 1.0,
        min_delay_seconds: float = 1.0,
        max_concurrent_requests: int = 5,
        respect_crawl_delay: bool = True
    ):
        """
        Initialize the rate limiter.

        Args:
            requests_per_second: Maximum requests per second per domain
            min_delay_seconds: Minimum delay between requests to same domain
            max_concurrent_requests: Maximum concurrent requests across all domains
            respect_crawl_delay: Whether to respect Crawl-delay from robots.txt
        """
        self.requests_per_second = requests_per_second
        self.min_delay_seconds = min_delay_seconds
        self.max_concurrent_requests = max_concurrent_requests
        self.respect_crawl_delay = respect_crawl_delay

        # Track last request time per domain
        self.last_request_time: Dict[str, float] = defaultdict(float)

        # Track request timestamps per domain for sliding window rate limiting
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Semaphore for concurrent request limiting
        self.concurrent_semaphore = threading.Semaphore(max_concurrent_requests)

        # Lock for thread safety
        self.lock = threading.Lock()

        logger.info(
            f"RateLimiter initialized: {requests_per_second} req/s, "
            f"{min_delay_seconds}s min delay, "
            f"{max_concurrent_requests} max concurrent"
        )

    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: URL to parse

        Returns:
            Domain name
        """
        parsed = urlparse(url)
        return parsed.netloc

    def _calculate_delay(self, domain: str, crawl_delay: Optional[float] = None) -> float:
        """
        Calculate how long to wait before making a request.

        Args:
            domain: Domain name
            crawl_delay: Optional crawl delay from robots.txt

        Returns:
            Seconds to wait
        """
        current_time = time.time()

        with self.lock:
            last_request = self.last_request_time[domain]

            # Calculate delay based on minimum delay
            time_since_last = current_time - last_request
            delay_needed = max(0, self.min_delay_seconds - time_since_last)

            # Respect crawl delay from robots.txt if specified
            if self.respect_crawl_delay and crawl_delay:
                crawl_delay_needed = max(0, crawl_delay - time_since_last)
                delay_needed = max(delay_needed, crawl_delay_needed)
                logger.debug(f"Respecting robots.txt crawl delay of {crawl_delay}s for {domain}")

            # Check sliding window rate limit
            request_history = self.request_history[domain]
            window_start = current_time - 1.0  # 1 second window

            # Remove old requests outside the window
            while request_history and request_history[0] < window_start:
                request_history.popleft()

            # Check if we've hit the rate limit
            if len(request_history) >= self.requests_per_second:
                # Need to wait until oldest request falls outside window
                oldest_request = request_history[0]
                rate_limit_delay = 1.0 - (current_time - oldest_request)
                delay_needed = max(delay_needed, rate_limit_delay)

            return delay_needed

    def wait_if_needed(self, url: str, crawl_delay: Optional[float] = None):
        """
        Wait if necessary to respect rate limits.

        Args:
            url: URL to be requested
            crawl_delay: Optional crawl delay from robots.txt
        """
        domain = self._get_domain(url)
        delay = self._calculate_delay(domain, crawl_delay)

        if delay > 0:
            logger.debug(f"Rate limiting: waiting {delay:.2f}s before requesting {domain}")
            time.sleep(delay)

        # Update request tracking
        current_time = time.time()
        with self.lock:
            self.last_request_time[domain] = current_time
            self.request_history[domain].append(current_time)

        logger.debug(f"Request allowed for {domain}")

    def acquire(self, url: str, crawl_delay: Optional[float] = None):
        """
        Acquire permission to make a request (for use with context manager).

        Args:
            url: URL to be requested
            crawl_delay: Optional crawl delay from robots.txt
        """
        # Acquire semaphore for concurrent request limiting
        self.concurrent_semaphore.acquire()
        logger.debug(f"Acquired concurrent request slot for {url}")

        # Apply rate limiting
        self.wait_if_needed(url, crawl_delay)

    def release(self):
        """Release the concurrent request slot."""
        self.concurrent_semaphore.release()
        logger.debug("Released concurrent request slot")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()

    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            return {
                'domains_tracked': len(self.last_request_time),
                'requests_per_second': self.requests_per_second,
                'min_delay_seconds': self.min_delay_seconds,
                'max_concurrent_requests': self.max_concurrent_requests,
                'available_slots': self.concurrent_semaphore._value
            }


class PoliteDelay:
    """Simple polite delay between requests."""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """
        Initialize polite delay.

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds (for randomization)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.lock = threading.Lock()

    def wait(self):
        """Wait with a polite delay."""
        import random

        current_time = time.time()

        with self.lock:
            time_since_last = current_time - self.last_request_time

            if self.last_request_time > 0:  # Skip delay for first request
                # Random delay between min and max
                delay = random.uniform(self.min_delay, self.max_delay)
                needed_delay = max(0, delay - time_since_last)

                if needed_delay > 0:
                    logger.debug(f"Polite delay: waiting {needed_delay:.2f}s")
                    time.sleep(needed_delay)

            self.last_request_time = time.time()


def test_rate_limiter():
    """Test the rate limiter."""
    limiter = RateLimiter(requests_per_second=2.0, min_delay_seconds=0.5)

    test_url = "https://www.example.com/page1"

    print("\n=== Testing Rate Limiter ===\n")
    print(f"Making 5 requests to {test_url}...")
    print(f"Expected: ~0.5s between requests\n")

    for i in range(5):
        start_time = time.time()
        limiter.acquire(test_url)
        elapsed = time.time() - start_time

        print(f"Request {i+1}: waited {elapsed:.2f}s")
        limiter.release()

    print("\n" + "=" * 40)
    print("Stats:", limiter.get_stats())


if __name__ == "__main__":
    test_rate_limiter()
