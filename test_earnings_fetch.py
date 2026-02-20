"""
Test earnings date fetching functionality.
"""
from src.data.yfinance_client import YFinanceClient

def test_earnings_single_ticker():
    """Test fetching earnings date for a single ticker."""
    client = YFinanceClient()

    tickers = ["NVDA", "AAPL", "TSLA"]

    print("="*60)
    print("Testing Earnings Date Fetching")
    print("="*60)

    for ticker in tickers:
        print(f"\n{ticker}:")
        print("-" * 40)

        earnings = client.get_earnings_date(ticker)

        if earnings:
            print(f"  [OK] Next Earnings: {earnings['date_str']}")
            print(f"  [OK] Timing: {earnings['timing'] if earnings['timing'] else 'Unknown'}")
            print(f"  [OK] Days Until: {earnings['days_until']} days")
            print(f"  [OK] Full Date: {earnings['date']}")
        else:
            print(f"  [X] No earnings date available")

    print("\n" + "="*60)

def test_earnings_calendar():
    """Test fetching earnings calendar for multiple tickers."""
    client = YFinanceClient()

    # Popular tickers
    tickers = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "META"]

    print("\nTesting Earnings Calendar (Multiple Tickers)")
    print("="*60)

    calendar = client.get_earnings_calendar(tickers)

    print(f"\nFound {len(calendar)} upcoming earnings:\n")

    for item in calendar[:10]:  # Show first 10
        timing_str = f" ({item['timing']})" if item['timing'] else ""
        print(f"  {item['ticker']:<6} - {item['date_str']}{timing_str} - {item['days_until']} days")

    print("\n" + "="*60)

if __name__ == "__main__":
    test_earnings_single_ticker()
    test_earnings_calendar()
    print("\n[SUCCESS] Earnings fetching tests complete!\n")
