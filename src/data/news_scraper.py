"""
Web scraper for extracting full article content from news URLs.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import time
from urllib.parse import urlparse


class NewsArticleScraper:
    """Scrape full article content from news URLs."""

    def __init__(self):
        """Initialize scraper with headers to mimic browser."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.timeout = 10

    def scrape_article(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape full article content from URL.

        Args:
            url: Article URL

        Returns:
            Dictionary with title, content, or None if scraping fails
        """
        try:
            # Fetch the page
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract based on common news site patterns
            domain = urlparse(url).netloc

            if 'yahoo' in domain or 'finance.yahoo' in domain:
                return self._scrape_yahoo_finance(soup)
            elif 'bloomberg' in domain:
                return self._scrape_bloomberg(soup)
            elif 'reuters' in domain:
                return self._scrape_reuters(soup)
            elif 'cnbc' in domain:
                return self._scrape_cnbc(soup)
            elif 'marketwatch' in domain:
                return self._scrape_marketwatch(soup)
            elif 'seekingalpha' in domain:
                return self._scrape_seeking_alpha(soup)
            else:
                # Generic fallback
                return self._scrape_generic(soup)

        except requests.exceptions.Timeout:
            print(f"Timeout scraping {url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
            return None

    def _scrape_yahoo_finance(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract article from Yahoo Finance."""
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # Yahoo Finance uses caas-body for article content
        content_div = soup.find('div', {'class': 'caas-body'})

        if not content_div:
            # Try alternative selectors
            content_div = soup.find('article') or soup.find('div', {'class': 'article-body'})

        if content_div:
            # Extract all paragraphs
            paragraphs = content_div.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            content = "Could not extract article content"

        return {
            'title': title_text,
            'content': content,
            'word_count': len(content.split())
        }

    def _scrape_bloomberg(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract article from Bloomberg."""
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # Bloomberg often uses article tag
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            content = "Could not extract article content (may be paywalled)"

        return {
            'title': title_text,
            'content': content,
            'word_count': len(content.split())
        }

    def _scrape_reuters(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract article from Reuters."""
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # Reuters uses article__body
        content_div = soup.find('div', {'class': 'article__body'}) or soup.find('article')

        if content_div:
            paragraphs = content_div.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            content = "Could not extract article content"

        return {
            'title': title_text,
            'content': content,
            'word_count': len(content.split())
        }

    def _scrape_cnbc(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract article from CNBC."""
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # CNBC uses ArticleBody-articleBody
        content_div = soup.find('div', {'class': 'ArticleBody-articleBody'}) or soup.find('div', {'class': 'group'})

        if content_div:
            paragraphs = content_div.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            content = "Could not extract article content"

        return {
            'title': title_text,
            'content': content,
            'word_count': len(content.split())
        }

    def _scrape_marketwatch(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract article from MarketWatch."""
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # MarketWatch uses article__body
        content_div = soup.find('div', {'class': 'article__body'}) or soup.find('article')

        if content_div:
            paragraphs = content_div.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            content = "Could not extract article content"

        return {
            'title': title_text,
            'content': content,
            'word_count': len(content.split())
        }

    def _scrape_seeking_alpha(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract article from Seeking Alpha."""
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # Seeking Alpha often requires login for full content
        content_div = soup.find('div', {'data-test-id': 'content-container'}) or soup.find('article')

        if content_div:
            paragraphs = content_div.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            content = "Could not extract article content (may require login)"

        return {
            'title': title_text,
            'content': content,
            'word_count': len(content.split())
        }

    def _scrape_generic(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Generic article extraction for unknown sites."""
        # Try to find title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title"

        # Try common article containers
        content_div = (
            soup.find('article') or
            soup.find('div', {'class': 'article-body'}) or
            soup.find('div', {'class': 'article-content'}) or
            soup.find('div', {'class': 'post-content'}) or
            soup.find('main')
        )

        if content_div:
            paragraphs = content_div.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        else:
            # Last resort: get all paragraphs
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs[:10] if p.get_text(strip=True)])

        return {
            'title': title_text,
            'content': content if content else "Could not extract article content",
            'word_count': len(content.split()) if content else 0
        }

    def scrape_multiple_articles(self, urls: list, max_articles: int = 5, delay: float = 1.0) -> list:
        """
        Scrape multiple articles with rate limiting.

        Args:
            urls: List of article URLs
            max_articles: Maximum number of articles to scrape
            delay: Delay between requests (seconds)

        Returns:
            List of article dictionaries
        """
        articles = []

        for i, url in enumerate(urls[:max_articles]):
            if i > 0:
                time.sleep(delay)  # Rate limiting

            article = self.scrape_article(url)
            if article and article['word_count'] > 50:  # Only keep articles with substantial content
                article['url'] = url
                articles.append(article)
                print(f"  Scraped: {article['title'][:60]}... ({article['word_count']} words)")

        return articles


if __name__ == "__main__":
    # Test the scraper
    scraper = NewsArticleScraper()

    test_urls = [
        "https://finance.yahoo.com/news/live/stock-market-today-dow-ekes-out-third-straight-record-sp-500-nasdaq-slide-with-jobs-report-on-deck-210303932.html",
        "https://finance.yahoo.com/news/goldman-sachs-ceo-solomon-calls-software-rout-too-broad-as-wall-street-looks-to-steady-investor-nerves-195453018.html",
    ]

    print("\n" + "="*70)
    print("TESTING NEWS ARTICLE SCRAPER")
    print("="*70 + "\n")

    for url in test_urls:
        print(f"\nScraping: {url[:60]}...")
        article = scraper.scrape_article(url)

        if article:
            print(f"\nTitle: {article['title']}")
            print(f"Word Count: {article['word_count']}")
            print(f"\nFirst 300 characters of content:")
            print(f"{article['content'][:300]}...")
            print(f"\n{'-'*70}")
        else:
            print("Failed to scrape article")

    print(f"\n{'='*70}")
    print("[SUCCESS] News scraper working!")
    print(f"{'='*70}\n")
