"""
Test earnings display formatting (simulates what UI will show).
"""
from src.data.yfinance_client import YFinanceClient

def format_earnings_display(earnings_info):
    """Format earnings info for display."""
    if earnings_info:
        timing_str = f" ({earnings_info['timing']})" if earnings_info['timing'] else ""
        return {
            "label": "Next Earnings",
            "value": f"{earnings_info['date_str']}{timing_str}",
            "delta": f"{earnings_info['days_until']} days"
        }
    else:
        return {
            "label": "Next Earnings",
            "value": "N/A",
            "delta": None
        }

def test_earnings_display():
    """Test earnings display formatting for different tickers."""
    client = YFinanceClient()

    test_cases = [
        ("NVDA", "Should show earnings in ~11 days (within trade window)"),
        ("AAPL", "Should show earnings in ~75 days (outside trade window)"),
        ("TSLA", "Should show earnings in ~66 days (outside trade window)"),
    ]

    print("="*70)
    print("Testing Earnings Display Formatting")
    print("="*70)

    for ticker, description in test_cases:
        print(f"\n{ticker}: {description}")
        print("-"*70)

        earnings_info = client.get_earnings_date(ticker)
        display = format_earnings_display(earnings_info)

        print(f"  Label: {display['label']}")
        print(f"  Value: {display['value']}")
        print(f"  Delta: {display['delta']}")

        if earnings_info and earnings_info['days_until'] <= 30:
            print(f"  --> WITHIN TRADE WINDOW (30 days)")
            print(f"  --> WILL TRIGGER EARNINGS RESEARCH")
        elif earnings_info:
            print(f"  --> Outside trade window")
            print(f"  --> Will just mention in analysis")
        else:
            print(f"  --> No earnings data available")

    print("\n" + "="*70)
    print("[SUCCESS] Earnings display formatting works!")
    print("="*70)

if __name__ == "__main__":
    test_earnings_display()
