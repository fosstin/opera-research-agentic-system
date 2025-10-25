"""
Caching mechanism for web scraping to reduce redundant requests.
"""
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


class ScraperCache:
    """
    File-based cache for scraped content.
    Reduces load on servers and speeds up development/testing.
    """

    def __init__(
        self,
        cache_dir: str = "data/cache",
        ttl_seconds: int = 86400,  # 24 hours default
        enabled: bool = True
    ):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time to live for cache entries in seconds
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cache initialized at {self.cache_dir} with TTL of {ttl_seconds}s")
        else:
            logger.info("Cache is disabled")

    def _generate_cache_key(self, url: str) -> str:
        """
        Generate a cache key from URL.

        Args:
            url: URL to cache

        Returns:
            Cache key (hash of URL)
        """
        return hashlib.sha256(url.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get the file path for a cache key.

        Args:
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def _is_expired(self, cache_entry: Dict) -> bool:
        """
        Check if a cache entry has expired.

        Args:
            cache_entry: Cache entry dictionary

        Returns:
            True if expired, False otherwise
        """
        timestamp = cache_entry.get('timestamp', 0)
        age = time.time() - timestamp
        return age > self.ttl_seconds

    def get(self, url: str) -> Optional[Any]:
        """
        Get cached content for a URL.

        Args:
            url: URL to retrieve from cache

        Returns:
            Cached content or None if not found/expired
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            logger.debug(f"Cache miss for {url}")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_entry = json.load(f)

            if self._is_expired(cache_entry):
                logger.debug(f"Cache expired for {url}")
                cache_path.unlink()  # Delete expired cache
                return None

            logger.info(f"Cache hit for {url}")
            return cache_entry.get('content')

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading cache for {url}: {e}")
            return None

    def set(self, url: str, content: Any) -> bool:
        """
        Store content in cache.

        Args:
            url: URL being cached
            content: Content to cache

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        cache_key = self._generate_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        cache_entry = {
            'url': url,
            'content': content,
            'timestamp': time.time()
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)

            logger.debug(f"Cached content for {url}")
            return True

        except (IOError, TypeError) as e:
            logger.error(f"Error writing cache for {url}: {e}")
            return False

    def delete(self, url: str) -> bool:
        """
        Delete cached content for a URL.

        Args:
            url: URL to remove from cache

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False

        cache_key = self._generate_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.info(f"Deleted cache for {url}")
                return True
            except IOError as e:
                logger.error(f"Error deleting cache for {url}: {e}")
                return False

        return False

    def clear(self) -> int:
        """
        Clear all cached entries.

        Returns:
            Number of entries deleted
        """
        if not self.enabled:
            return 0

        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1

            logger.info(f"Cleared {count} cache entries")
            return count

        except IOError as e:
            logger.error(f"Error clearing cache: {e}")
            return count

    def clear_expired(self) -> int:
        """
        Clear only expired cache entries.

        Returns:
            Number of expired entries deleted
        """
        if not self.enabled:
            return 0

        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_entry = json.load(f)

                    if self._is_expired(cache_entry):
                        cache_file.unlink()
                        count += 1

                except (json.JSONDecodeError, IOError):
                    # Delete corrupted cache files
                    cache_file.unlink()
                    count += 1

            logger.info(f"Cleared {count} expired cache entries")
            return count

        except IOError as e:
            logger.error(f"Error clearing expired cache: {e}")
            return count

    def get_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled:
            return {'enabled': False}

        total_entries = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            'enabled': True,
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir),
            'ttl_seconds': self.ttl_seconds
        }


def test_cache():
    """Test the cache."""
    import tempfile
    import shutil

    # Create temporary cache directory
    temp_dir = tempfile.mkdtemp()

    try:
        cache = ScraperCache(cache_dir=temp_dir, ttl_seconds=2)

        print("\n=== Testing Cache ===\n")

        # Test set and get
        url = "https://www.example.com"
        content = {"title": "Example", "text": "Hello World"}

        print(f"Storing content for {url}")
        cache.set(url, content)

        print(f"Retrieving content for {url}")
        retrieved = cache.get(url)
        print(f"Retrieved: {retrieved}")
        assert retrieved == content, "Cache content mismatch"

        print("\nCache stats:", cache.get_stats())

        # Test expiration
        print("\nWaiting 3 seconds for cache to expire...")
        time.sleep(3)

        print(f"Retrieving expired content for {url}")
        expired = cache.get(url)
        print(f"Result: {expired}")
        assert expired is None, "Expired cache should return None"

        print("\n✓ All cache tests passed")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary cache directory")


if __name__ == "__main__":
    test_cache()
