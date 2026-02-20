"""
Parse 10-K and 10-Q filings to extract key sections.
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional, List
import time


class SECFilingParser:
    """Parse 10-K and 10-Q filings to extract narrative sections."""

    def __init__(self, user_agent: str = "OptionsBot research@example.com"):
        """Initialize parser with SEC-compliant headers."""
        self.headers = {
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        self.rate_limit_delay = 0.1

    def get_latest_10k_url(self, cik: str) -> Optional[str]:
        """
        Get URL to the latest 10-K filing.

        Args:
            cik: Company CIK (e.g., "0001045810")

        Returns:
            URL to 10-K HTML file
        """
        # Get company filings
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers={'User-Agent': self.headers['User-Agent']})
            response.raise_for_status()
            data = response.json()

            # Find most recent 10-K
            recent = data.get('filings', {}).get('recent', {})
            forms = recent.get('form', [])
            accessions = recent.get('accessionNumber', [])
            primary_docs = recent.get('primaryDocument', [])

            for i, form in enumerate(forms):
                if form == '10-K':
                    acc_no = accessions[i].replace('-', '')
                    doc = primary_docs[i]
                    # Construct URL to filing
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_no}/{doc}"
                    return filing_url

            return None

        except Exception as e:
            print(f"Error getting 10-K URL: {e}")
            return None

    def get_latest_10q_url(self, cik: str) -> Optional[str]:
        """Get URL to the latest 10-Q filing."""
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers={'User-Agent': self.headers['User-Agent']})
            response.raise_for_status()
            data = response.json()

            recent = data.get('filings', {}).get('recent', {})
            forms = recent.get('form', [])
            accessions = recent.get('accessionNumber', [])
            primary_docs = recent.get('primaryDocument', [])

            for i, form in enumerate(forms):
                if form == '10-Q':
                    acc_no = accessions[i].replace('-', '')
                    doc = primary_docs[i]
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{acc_no}/{doc}"
                    return filing_url

            return None

        except Exception as e:
            print(f"Error getting 10-Q URL: {e}")
            return None

    def fetch_filing_html(self, url: str) -> Optional[str]:
        """
        Fetch the raw HTML of a filing.

        Args:
            url: URL to SEC filing

        Returns:
            HTML content as string
        """
        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text

        except Exception as e:
            print(f"Error fetching filing: {e}")
            return None

    def parse_10k(self, cik: str) -> Dict[str, str]:
        """
        Parse latest 10-K and extract key sections.

        Args:
            cik: Company CIK

        Returns:
            Dictionary with extracted sections
        """
        print(f"  Fetching latest 10-K for CIK {cik}...")

        url = self.get_latest_10k_url(cik)
        if not url:
            print("  Could not find 10-K URL")
            return {}

        print(f"  Downloading 10-K from SEC...")
        html = self.fetch_filing_html(url)
        if not html:
            print("  Could not fetch 10-K content")
            return {}

        print(f"  Parsing 10-K sections...")
        soup = BeautifulSoup(html, 'html.parser')

        # Extract sections
        sections = {}

        # Item 1: Business
        sections['business'] = self._extract_section(
            soup,
            patterns=[
                r'(?i)item\s*1\b[.\s]*business',
                r'(?i)item\s*1[.\s]*$'
            ],
            stop_patterns=[
                r'(?i)item\s*1a',
                r'(?i)item\s*2'
            ],
            max_words=3000
        )

        # Item 1A: Risk Factors
        sections['risk_factors'] = self._extract_section(
            soup,
            patterns=[
                r'(?i)item\s*1a[.\s]*risk\s*factors',
                r'(?i)risk\s*factors'
            ],
            stop_patterns=[
                r'(?i)item\s*1b',
                r'(?i)item\s*2'
            ],
            max_words=5000
        )

        # Item 7: MD&A
        sections['mda'] = self._extract_section(
            soup,
            patterns=[
                r'(?i)item\s*7[.\s]*management',
                r'(?i)management.s\s*discussion\s*and\s*analysis',
                r'(?i)md&a'
            ],
            stop_patterns=[
                r'(?i)item\s*7a',
                r'(?i)item\s*8'
            ],
            max_words=8000
        )

        # Item 7A: Market Risk (often includes volatility discussion)
        sections['market_risk'] = self._extract_section(
            soup,
            patterns=[
                r'(?i)item\s*7a[.\s]*quantitative\s*and\s*qualitative',
                r'(?i)market\s*risk'
            ],
            stop_patterns=[
                r'(?i)item\s*8'
            ],
            max_words=2000
        )

        return sections

    def parse_10q(self, cik: str) -> Dict[str, str]:
        """
        Parse latest 10-Q and extract key sections.

        Args:
            cik: Company CIK

        Returns:
            Dictionary with extracted sections
        """
        print(f"  Fetching latest 10-Q for CIK {cik}...")

        url = self.get_latest_10q_url(cik)
        if not url:
            print("  Could not find 10-Q URL")
            return {}

        print(f"  Downloading 10-Q from SEC...")
        html = self.fetch_filing_html(url)
        if not html:
            print("  Could not fetch 10-Q content")
            return {}

        print(f"  Parsing 10-Q sections...")
        soup = BeautifulSoup(html, 'html.parser')

        sections = {}

        # Item 2: MD&A (10-Q structure)
        sections['mda'] = self._extract_section(
            soup,
            patterns=[
                r'(?i)item\s*2[.\s]*management',
                r'(?i)management.s\s*discussion\s*and\s*analysis'
            ],
            stop_patterns=[
                r'(?i)item\s*3',
                r'(?i)item\s*4'
            ],
            max_words=6000
        )

        # Item 1A: Risk Factors (if updated)
        sections['risk_factors'] = self._extract_section(
            soup,
            patterns=[
                r'(?i)item\s*1a[.\s]*risk\s*factors',
            ],
            stop_patterns=[
                r'(?i)item\s*2',
                r'(?i)item\s*1b'
            ],
            max_words=3000
        )

        return sections

    def _extract_section(
        self,
        soup: BeautifulSoup,
        patterns: List[str],
        stop_patterns: List[str],
        max_words: int = 5000
    ) -> str:
        """
        Extract a section from SEC filing HTML.

        Args:
            soup: BeautifulSoup object
            patterns: Regex patterns to find section start
            stop_patterns: Regex patterns to find section end
            max_words: Maximum words to extract

        Returns:
            Extracted section text
        """
        # Get all text elements (preserving some structure)
        text_elements = soup.find_all(['p', 'div', 'table', 'span'])

        # Build full text with markers
        full_text = ' '.join([elem.get_text(separator=' ', strip=True) for elem in text_elements])

        # Clean up excessive whitespace
        full_text = re.sub(r'\s+', ' ', full_text)

        # Try to find section
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                start_pos = match.start()

                # Look ahead to find actual content start (skip table of contents, headers)
                content_start = match.end()

                # Skip forward past any table of contents or short lines
                next_500 = full_text[content_start:content_start+500]
                if len(next_500.strip()) < 50:  # Likely just whitespace/headers
                    # Look for first substantial paragraph
                    para_match = re.search(r'[A-Z][a-z]{10,}', full_text[content_start:])
                    if para_match:
                        content_start = content_start + para_match.start()

                # Find where section ends
                end_pos = len(full_text)
                for stop_pattern in stop_patterns:
                    stop_match = re.search(stop_pattern, full_text[content_start:], re.IGNORECASE)
                    if stop_match:
                        # Make sure we found a real section boundary
                        potential_end = content_start + stop_match.start()
                        if potential_end - content_start > 200:  # At least 200 chars extracted
                            end_pos = potential_end
                            break

                # Extract section text
                section_text = full_text[content_start:end_pos]

                # Clean up
                section_text = re.sub(r'\s+', ' ', section_text)
                section_text = section_text.strip()

                # Remove common artifacts
                section_text = re.sub(r'Table of Contents', '', section_text, flags=re.IGNORECASE)
                section_text = re.sub(r'\d+', ' ', section_text)  # Remove isolated numbers
                section_text = re.sub(r'\s+', ' ', section_text)

                # Limit words
                if len(section_text) > 100:  # Only return if we got substantial content
                    words = section_text.split()[:max_words]
                    return ' '.join(words)

        return ""

    def get_comprehensive_filing_data(self, cik: str, use_10k: bool = True) -> Dict:
        """
        Get comprehensive data from either 10-K or 10-Q.

        Args:
            cik: Company CIK
            use_10k: If True, use 10-K (annual), else use 10-Q (quarterly)

        Returns:
            Dictionary with all sections and metadata
        """
        if use_10k:
            sections = self.parse_10k(cik)
            filing_type = "10-K"
        else:
            sections = self.parse_10q(cik)
            filing_type = "10-Q"

        # Calculate total words
        total_words = sum(len(text.split()) for text in sections.values() if text)

        print(f"\n  [OK] Extracted {filing_type}:")
        for section_name, text in sections.items():
            if text:
                word_count = len(text.split())
                print(f"    - {section_name}: {word_count:,} words")

        print(f"  Total: {total_words:,} words from {filing_type}\n")

        return {
            'filing_type': filing_type,
            'sections': sections,
            'total_words': total_words
        }


if __name__ == "__main__":
    # Test the parser
    parser = SECFilingParser(user_agent="TestBot test@example.com")

    # Common CIKs
    ciks = {
        'NVDA': '0001045810',
        'AAPL': '0000320193',
    }

    ticker = 'NVDA'
    cik = ciks[ticker]

    print("\n" + "="*70)
    print(f"TESTING SEC FILING PARSER - {ticker}")
    print("="*70 + "\n")

    # Parse 10-K
    print("Parsing latest 10-K...\n")
    filing_data = parser.get_comprehensive_filing_data(cik, use_10k=True)

    # Show sample content
    if filing_data['sections'].get('risk_factors'):
        print("="*70)
        print("SAMPLE: Risk Factors (first 500 chars)")
        print("="*70)
        print(filing_data['sections']['risk_factors'][:500] + "...\n")

    if filing_data['sections'].get('mda'):
        print("="*70)
        print("SAMPLE: MD&A (first 500 chars)")
        print("="*70)
        print(filing_data['sections']['mda'][:500] + "...\n")

    print("="*70)
    print("[SUCCESS] SEC Filing Parser Working!")
    print("="*70 + "\n")
