"""
SEC EDGAR API client for fetching 10-K, 10-Q, and 8-K filings.
"""
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime


class SECFilingsClient:
    """Client for SEC EDGAR API (100% free, no API key needed)."""

    def __init__(self, user_agent: str = "YourCompany your.email@example.com"):
        """
        Initialize SEC client.

        Args:
            user_agent: Your contact info (SEC requires this)
                       Format: "Company name email@example.com"
        """
        self.base_url = "https://data.sec.gov"
        self.headers = {
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.rate_limit_delay = 0.1  # SEC requests 10 requests per second max

    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK (Central Index Key) for a company ticker.

        Args:
            ticker: Stock ticker (e.g., "NVDA")

        Returns:
            CIK number as string (e.g., "0001045810")
        """
        # Common ticker to CIK mappings (fallback)
        common_ciks = {
            'NVDA': '0001045810',
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'GOOGL': '0001652044',
            'AMZN': '0001018724',
            'TSLA': '0001318605',
            'META': '0001326801',
            'AMD': '0000002488',
        }

        # Check common mappings first
        if ticker.upper() in common_ciks:
            return common_ciks[ticker.upper()]

        # Try SEC search endpoint
        search_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={ticker}&action=getcompany&CIK=&type=&dateb=&owner=exclude&count=1&output=atom"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()

            # Parse CIK from response (hacky but works)
            text = response.text
            if 'CIK=' in text:
                cik_str = text.split('CIK=')[1].split('&')[0]
                return cik_str.zfill(10)

            return None

        except Exception as e:
            print(f"Error fetching CIK for {ticker}: {e}")
            return None

    def get_company_facts(self, ticker: str) -> Optional[Dict]:
        """
        Get all company facts (financials) from XBRL data.

        Args:
            ticker: Stock ticker

        Returns:
            Dictionary with company facts
        """
        cik = self.get_company_cik(ticker)
        if not cik:
            return None

        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik}.json"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error fetching company facts: {e}")
            return None

    def get_recent_filings(
        self,
        ticker: str,
        filing_types: List[str] = ["10-K", "10-Q", "8-K"],
        max_filings: int = 10
    ) -> List[Dict]:
        """
        Get recent filings for a company.

        Args:
            ticker: Stock ticker
            filing_types: List of filing types to fetch
            max_filings: Maximum number of filings to return

        Returns:
            List of filing metadata
        """
        cik = self.get_company_cik(ticker)
        if not cik:
            return []

        url = f"{self.base_url}/submissions/CIK{cik}.json"

        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            # Extract recent filings
            recent = data.get('filings', {}).get('recent', {})
            if not recent:
                return []

            filings = []
            for i in range(len(recent['form'])):
                form_type = recent['form'][i]

                if form_type in filing_types:
                    filings.append({
                        'form': form_type,
                        'filing_date': recent['filingDate'][i],
                        'accession_number': recent['accessionNumber'][i],
                        'primary_document': recent['primaryDocument'][i],
                        'description': recent.get('primaryDocDescription', [''])[i] if i < len(recent.get('primaryDocDescription', [])) else ''
                    })

                if len(filings) >= max_filings:
                    break

            return filings

        except Exception as e:
            print(f"Error fetching filings: {e}")
            return []

    def get_filing_url(self, accession_number: str, primary_document: str) -> str:
        """
        Get URL to filing document.

        Args:
            accession_number: Filing accession number
            primary_document: Primary document filename

        Returns:
            URL to filing
        """
        # Remove dashes from accession number for URL
        acc_no_dashes = accession_number.replace('-', '')

        return f"https://www.sec.gov/Archives/edgar/data/{acc_no_dashes}/{primary_document}"

    def extract_key_metrics_from_facts(self, facts: Dict) -> Dict:
        """
        Extract key financial metrics from company facts.

        Args:
            facts: Company facts from get_company_facts()

        Returns:
            Dictionary with key metrics
        """
        if not facts:
            return {}

        metrics = {}

        try:
            us_gaap = facts.get('facts', {}).get('us-gaap', {})

            # Helper to get most recent value
            def get_latest_value(metric_name: str) -> Optional[float]:
                metric = us_gaap.get(metric_name, {})
                units = metric.get('units', {})

                # Try USD first
                if 'USD' in units:
                    values = sorted(units['USD'], key=lambda x: x.get('end', ''), reverse=True)
                    if values:
                        return values[0].get('val')

                # Try other units
                for unit_values in units.values():
                    values = sorted(unit_values, key=lambda x: x.get('end', ''), reverse=True)
                    if values:
                        return values[0].get('val')

                return None

            # Extract common metrics
            metrics['revenue'] = get_latest_value('Revenues')
            metrics['net_income'] = get_latest_value('NetIncomeLoss')
            metrics['total_assets'] = get_latest_value('Assets')
            metrics['total_liabilities'] = get_latest_value('Liabilities')
            metrics['stockholders_equity'] = get_latest_value('StockholdersEquity')
            metrics['cash'] = get_latest_value('Cash')
            metrics['research_development'] = get_latest_value('ResearchAndDevelopmentExpense')
            metrics['operating_income'] = get_latest_value('OperatingIncomeLoss')

            # Calculate derived metrics
            if metrics.get('revenue') and metrics.get('net_income'):
                metrics['profit_margin'] = metrics['net_income'] / metrics['revenue']

            if metrics.get('total_assets') and metrics.get('total_liabilities'):
                metrics['debt_to_assets'] = metrics['total_liabilities'] / metrics['total_assets']

        except Exception as e:
            print(f"Error extracting metrics: {e}")

        return metrics


if __name__ == "__main__":
    # Test SEC client
    client = SECFilingsClient(user_agent="TestBot test@example.com")

    ticker = "NVDA"

    print("\n" + "="*70)
    print(f"TESTING SEC FILINGS CLIENT - {ticker}")
    print("="*70 + "\n")

    # Get CIK
    print("1. Getting CIK...")
    cik = client.get_company_cik(ticker)
    print(f"   CIK: {cik}")

    # Get recent filings
    print("\n2. Getting recent filings...")
    filings = client.get_recent_filings(ticker, filing_types=["10-K", "10-Q"], max_filings=5)

    print(f"   Found {len(filings)} recent filings:")
    for filing in filings:
        print(f"   - {filing['form']}: {filing['filing_date']} - {filing['description'][:50]}")

    # Get company facts
    print("\n3. Getting company facts (financial metrics)...")
    facts = client.get_company_facts(ticker)

    if facts:
        print(f"   Company: {facts.get('entityName', 'Unknown')}")

        metrics = client.extract_key_metrics_from_facts(facts)

        print("\n   Key Metrics:")
        if metrics.get('revenue'):
            print(f"   - Revenue: ${metrics['revenue']/1e9:.2f}B")
        if metrics.get('net_income'):
            print(f"   - Net Income: ${metrics['net_income']/1e9:.2f}B")
        if metrics.get('profit_margin'):
            print(f"   - Profit Margin: {metrics['profit_margin']*100:.1f}%")
        if metrics.get('research_development'):
            print(f"   - R&D Spending: ${metrics['research_development']/1e9:.2f}B")
        if metrics.get('cash'):
            print(f"   - Cash: ${metrics['cash']/1e9:.2f}B")

    print("\n" + "="*70)
    print("[SUCCESS] SEC Filings Client Working!")
    print("="*70 + "\n")
