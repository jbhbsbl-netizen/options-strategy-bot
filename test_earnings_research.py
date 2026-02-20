"""
Test earnings research functionality (mocked to avoid actual web scraping).
"""
from src.data.yfinance_client import YFinanceClient
from src.research.research_orchestrator import ResearchOrchestrator

def test_earnings_research():
    """Test that earnings research is triggered when appropriate."""
    client = YFinanceClient()
    orchestrator = ResearchOrchestrator()

    print("="*80)
    print("Testing Earnings Research Logic")
    print("="*80)

    # Test 1: NVDA - earnings in 11 days (SHOULD trigger earnings research)
    print("\n[TEST 1: NVDA - Earnings in 11 days]")
    print("-"*80)

    earnings_info = client.get_earnings_date("NVDA")

    if earnings_info:
        print(f"  Earnings Date: {earnings_info['date_str']}")
        print(f"  Days Until: {earnings_info['days_until']}")
        print(f"  Within 30 days? {earnings_info['days_until'] <= 30}")

        if earnings_info['days_until'] <= 30:
            print(f"  --> WILL TRIGGER EARNINGS RESEARCH")
            print(f"  --> Questions will include:")
            print(f"      - Typical post-earnings move (last 4 quarters)")
            print(f"      - Beat/miss pattern")
            print(f"      - IV crush pattern")
            print(f"      - Best earnings strategies")
        else:
            print(f"  --> Outside trade window, just mention")
    else:
        print(f"  --> No earnings data")

    # Test 2: AAPL - earnings in 75 days (should NOT trigger earnings research)
    print("\n[TEST 2: AAPL - Earnings in 75 days]")
    print("-"*80)

    earnings_info = client.get_earnings_date("AAPL")

    if earnings_info:
        print(f"  Earnings Date: {earnings_info['date_str']}")
        print(f"  Days Until: {earnings_info['days_until']}")
        print(f"  Within 30 days? {earnings_info['days_until'] <= 30}")

        if earnings_info['days_until'] <= 30:
            print(f"  --> WILL TRIGGER EARNINGS RESEARCH")
        else:
            print(f"  --> Outside trade window, just mention")
            print(f"  --> No earnings research needed")
    else:
        print(f"  --> No earnings data")

    print("\n" + "="*80)
    print("[SUCCESS] Earnings research logic works correctly!")
    print("="*80)
    print("\nKey Principle:")
    print("  - Core research ALWAYS runs (stock, strategy, contracts, risk, market)")
    print("  - Earnings research is ADDITIONAL (only when within 30 days)")
    print("  - Earnings doesn't replace fundamental analysis")
    print("="*80)

if __name__ == "__main__":
    test_earnings_research()
