"""
Unit tests for the web scraper module.
"""
import unittest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraping.scraper import OperaScraper


class TestOperaScraper(unittest.TestCase):
    """Test cases for OperaScraper class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scraper = OperaScraper()
        self.sample_html = """
        <html>
            <head>
                <title>Test Opera Company</title>
                <meta name="description" content="A test opera company">
            </head>
            <body>
                <h1>Welcome to Test Opera</h1>
                <a href="/about">About Us</a>
                <a href="https://example.com/contact">Contact</a>
                <p>Some text content here.</p>
            </body>
        </html>
        """

    def test_scraper_initialization(self):
        """Test scraper initializes correctly."""
        scraper = OperaScraper()
        self.assertIsNotNone(scraper.session)
        self.assertIn('User-Agent', scraper.session.headers)

    def test_custom_user_agent(self):
        """Test custom user agent is set."""
        custom_ua = "CustomBot/1.0"
        scraper = OperaScraper(user_agent=custom_ua)
        self.assertEqual(scraper.session.headers['User-Agent'], custom_ua)

    def test_parse_page(self):
        """Test HTML parsing."""
        soup = self.scraper.parse_page(self.sample_html)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertEqual(soup.title.text, "Test Opera Company")

    def test_extract_links(self):
        """Test link extraction."""
        soup = self.scraper.parse_page(self.sample_html)
        base_url = "https://testopera.com"
        links = self.scraper.extract_links(soup, base_url)

        self.assertEqual(len(links), 2)
        self.assertIn("https://testopera.com/about", links)
        self.assertIn("https://example.com/contact", links)

    @patch('scraping.scraper.requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        html = self.scraper.fetch_page("https://testopera.com")
        self.assertEqual(html, self.sample_html)

    @patch('scraping.scraper.requests.Session.get')
    def test_fetch_page_failure(self, mock_get):
        """Test failed page fetch."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        html = self.scraper.fetch_page("https://testopera.com")
        self.assertIsNone(html)

    @patch('scraping.scraper.OperaScraper.fetch_page')
    def test_scrape_basic_info_success(self, mock_fetch):
        """Test successful scraping of basic info."""
        mock_fetch.return_value = self.sample_html

        result = self.scraper.scrape_basic_info("https://testopera.com")

        self.assertTrue(result['success'])
        self.assertEqual(result['title'], "Test Opera Company")
        self.assertEqual(result['description'], "A test opera company")
        self.assertGreater(result['text_length'], 0)
        self.assertEqual(result['link_count'], 2)

    @patch('scraping.scraper.OperaScraper.fetch_page')
    def test_scrape_basic_info_failure(self, mock_fetch):
        """Test scraping when page fetch fails."""
        mock_fetch.return_value = None

        result = self.scraper.scrape_basic_info("https://testopera.com")

        self.assertFalse(result['success'])
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
