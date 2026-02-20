"""
Web Researcher - Search and scrape web content for stock research.

Uses DuckDuckGo for searching (no API key needed) and BeautifulSoup for scraping.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
from urllib.parse import urlparse

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False
        print("Warning: ddgs/duckduckgo_search not available. Web research disabled.")


@dataclass
class SearchResult:
    """Search result from web search."""
    title: str
    url: str
    snippet: str
    source: str  # Domain name (e.g., "reuters.com")


@dataclass
class Article:
    """Scraped article content."""
    url: str
    title: str
    content: str
    source: str
    word_count: int


class WebResearcher:
    """Search the web and scrape article content."""

    # Credible financial news sources
    CREDIBLE_SOURCES = {
        'reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com',
        'cnbc.com', 'marketwatch.com', 'yahoo.com', 'finance.yahoo.com',
        'seekingalpha.com', 'fool.com', 'benzinga.com',
        'investing.com', 'barrons.com', 'forbes.com',
        'sec.gov', 'investor.com', 'investopedia.com',
        'tastytrade.com', 'tastylive.com', 'optionsplaybook.com',
        'marketchameleon.com', 'tradingview.com', 'barchart.com',
        'finviz.com', 'stockcharts.com', 'zacks.com',
        'gurufocus.com', 'nasdaq.com', 'morningstar.com'
    }

    # Sources to avoid (unreliable or spam)
    BLOCKED_SOURCES = {
        'reddit.com', 'twitter.com', 'facebook.com',
        'pinterest.com', 'instagram.com', 'tiktok.com'
    }

    def __init__(self, max_results: int = 10):
        """
        Initialize web researcher.

        Args:
            max_results: Maximum search results to return per query
        """
        self.max_results = max_results
        self.session = requests.Session()

        # Set browser-like headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        filter_credible: bool = True
    ) -> List[SearchResult]:
        """
        Search the web using DuckDuckGo.

        Args:
            query: Search query
            max_results: Max results to return (default: self.max_results)
            filter_credible: Only return results from credible sources

        Returns:
            List of SearchResult objects
        """
        if not DDGS_AVAILABLE:
            print("Warning: DuckDuckGo search not available")
            return []

        max_results = max_results or self.max_results
        results = []

        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    query,
                    max_results=max_results * 2  # Get extra to filter
                )

                for result in search_results:
                    if len(results) >= max_results:
                        break

                    url = result.get('href', '')
                    title = result.get('title', '')
                    snippet = result.get('body', '')

                    # Extract source domain
                    source = self._extract_domain(url)

                    # Filter if requested
                    if filter_credible:
                        if not self._is_credible_source(source):
                            continue

                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source=source
                    ))

        except Exception as e:
            print(f"Search error for query '{query}': {e}")

        return results

    def scrape_article(self, url: str, timeout: int = 10, max_retries: int = 2) -> Optional[Article]:
        """
        Scrape article content from URL with retry logic.

        Args:
            url: URL to scrape
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Returns:
            Article object or None if scraping fails
        """
        for attempt in range(max_retries + 1):
            try:
                # Add slight delay for retries
                if attempt > 0:
                    time.sleep(2 * attempt)  # Exponential backoff

                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract title
                title = self._extract_title(soup, url)

                # Extract main content
                content = self._extract_content(soup)

                if not content or len(content) < 100:
                    return None

                source = self._extract_domain(url)
                word_count = len(content.split())

                return Article(
                    url=url,
                    title=title,
                    content=content,
                    source=source,
                    word_count=word_count
                )

            except requests.Timeout:
                if attempt == max_retries:
                    print(f"Timeout scraping {url}")
                return None
            except requests.HTTPError as e:
                if e.response.status_code == 403:
                    print(f"Access forbidden (403) for {url} - site blocks scrapers")
                elif e.response.status_code == 404:
                    print(f"Page not found (404): {url}")
                else:
                    print(f"HTTP error {e.response.status_code} for {url}")
                return None
            except requests.RequestException as e:
                if attempt == max_retries:
                    print(f"Error scraping {url}: {e}")
                return None
            except Exception as e:
                if attempt == max_retries:
                    print(f"Unexpected error scraping {url}: {e}")
                return None

        return None

    def scrape_multiple(
        self,
        urls: List[str],
        max_articles: int = 5,
        delay: float = 2.0
    ) -> List[Article]:
        """
        Scrape multiple articles with rate limiting.

        Args:
            urls: List of URLs to scrape
            max_articles: Maximum articles to return
            delay: Delay between requests (seconds)

        Returns:
            List of Article objects
        """
        articles = []

        for i, url in enumerate(urls):
            if len(articles) >= max_articles:
                break

            article = self.scrape_article(url)
            if article:
                articles.append(article)
                print(f"[{i+1}/{min(len(urls), max_articles)}] Scraped: {article.title[:60]}... ({article.word_count} words)")

            # Rate limiting
            if i < len(urls) - 1:
                time.sleep(delay)

        return articles

    def search_and_scrape(
        self,
        query: str,
        max_results: int = 5,
        filter_credible: bool = True
    ) -> List[Article]:
        """
        Search and scrape articles in one step.

        Args:
            query: Search query
            max_results: Max articles to scrape
            filter_credible: Only scrape credible sources

        Returns:
            List of Article objects
        """
        print(f"\nSearching: '{query}'")
        search_results = self.search(query, max_results * 2, filter_credible)

        if not search_results:
            print("No search results found")
            return []

        print(f"Found {len(search_results)} results, scraping top {max_results}...")

        urls = [r.url for r in search_results[:max_results]]
        articles = self.scrape_multiple(urls, max_articles=max_results)

        return articles

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove 'www.' prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''

    def _is_credible_source(self, domain: str) -> bool:
        """Check if source is credible."""
        # Check if blocked
        if domain in self.BLOCKED_SOURCES:
            return False

        # Check if in credible list
        if domain in self.CREDIBLE_SOURCES:
            return True

        # Check if subdomain of credible source
        for credible in self.CREDIBLE_SOURCES:
            if domain.endswith('.' + credible):
                return True

        # Default: allow if not blocked
        return True

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract article title."""
        # Try various title selectors
        title_selectors = [
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
            ('h1', {}),
            ('title', {})
        ]

        for tag, attrs in title_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    title = element.get('content', '')
                else:
                    title = element.get_text()

                if title and len(title.strip()) > 0:
                    return title.strip()

        return url

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
            element.decompose()

        # Try to find article tag first
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            if paragraphs:
                text = '\n\n'.join(p.get_text().strip() for p in paragraphs)
                if len(text) > 200:
                    return text

        # Try div with article/content classes
        for class_keyword in ['article', 'content', 'story', 'post']:
            divs = soup.find_all('div', class_=lambda x: x and class_keyword in str(x).lower())
            for div in divs:
                paragraphs = div.find_all('p')
                if paragraphs:
                    text = '\n\n'.join(p.get_text().strip() for p in paragraphs)
                    if len(text) > 200:
                        return text

        # Fallback: Get all paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs and len(paragraphs) > 3:  # At least 3 paragraphs
            text = '\n\n'.join(p.get_text().strip() for p in paragraphs)
            if len(text) > 200:
                return text

        # Last resort: Get all text
        return soup.get_text(separator='\n\n', strip=True)


if __name__ == "__main__":
    # Test web researcher
    print("=" * 80)
    print("TESTING WEB RESEARCHER")
    print("=" * 80)

    researcher = WebResearcher()

    # Test search
    print("\n[TEST 1: Search NVDA earnings]")
    query = "NVDA Q4 2025 earnings results"
    results = researcher.search(query, max_results=5)

    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   Source: {result.source}")
        print(f"   URL: {result.url}")
        print(f"   Snippet: {result.snippet[:100]}...")

    # Test search and scrape
    print("\n" + "=" * 80)
    print("[TEST 2: Search and scrape]")
    print("=" * 80)

    query = "NVDA artificial intelligence chip market share"
    articles = researcher.search_and_scrape(query, max_results=3)

    print(f"\n\nScraped {len(articles)} articles:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article.title}")
        print(f"   Source: {article.source}")
        print(f"   Words: {article.word_count}")
        print(f"   Preview: {article.content[:200]}...")

    print("\n" + "=" * 80)
    print("[SUCCESS] Web Researcher Working!")
    print("=" * 80)
