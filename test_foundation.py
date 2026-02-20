"""
Test the foundation: yfinance data + Greeks calculation
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.yfinance_client import YFinanceClient
from calculations.greeks import calculate_greeks, add_greeks_to_chain


def test_complete_pipeline(ticker: str = "NVDA"):
    """Test complete data pipeline from fetch to Greeks."""

    print(f"\n{'='*70}")
    print(f"FOUNDATION TEST: {ticker}")
    print(f"{'='*70}\n")

    client = YFinanceClient()

    # Step 1: Get stock data
    print("Step 1: Fetching stock data...")
    stock_data = client.get_stock_data(ticker)

    print(f"  Current Price: ${stock_data['current_price']:.2f}")
    print(f"  Change: ${stock_data['price_change']:.2f} ({stock_data['price_change_pct']:+.2f}%)")
    print(f"  Market Cap: ${stock_data['market_cap']/1e9:.1f}B")
    print(f"  P/E Ratio: {stock_data['pe_ratio']:.2f}" if stock_data['pe_ratio'] else "  P/E Ratio: N/A")
    print(f"  Target Price: ${stock_data['target_price']:.2f}" if stock_data['target_price'] else "  Target Price: N/A")

    # Step 2: Get historical volatility
    print("\nStep 2: Calculating historical volatility...")
    hist_vol = client.get_historical_volatility(ticker, days=30)
    print(f"  30-day Historical Vol: {hist_vol*100:.1f}%")

    # Step 3: Get options expirations
    print("\nStep 3: Fetching available option expirations...")
    expirations = client.get_all_expirations(ticker)
    print(f"  Found {len(expirations)} expirations")
    print(f"  Nearest 3: {expirations[:3]}")

    # Step 4: Get options chain for nearest expiration
    print(f"\nStep 4: Fetching options chain (expiration: {expirations[0]})...")
    chain = client.get_options_chain(ticker, expirations[0])
    print(f"  Total contracts: {len(chain)}")
    print(f"  Calls: {len(chain[chain['type']=='call'])}")
    print(f"  Puts: {len(chain[chain['type']=='put'])}")

    # Step 5: Calculate Greeks for options chain
    print("\nStep 5: Calculating Greeks for all contracts...")

    stock_price = stock_data['current_price']

    # Use the existing add_greeks_to_chain function
    chain_with_greeks = add_greeks_to_chain(
        chain,
        stock_price=stock_price,
        volatility=hist_vol,
        risk_free_rate=0.05
    )

    print(f"  Greeks calculated for {len(chain_with_greeks)} contracts")

    # Step 6: Show sample contracts near ATM
    print(f"\nStep 6: Sample CALL options near ATM (Stock: ${stock_price:.2f}):")
    print("-" * 120)

    calls = chain_with_greeks[chain_with_greeks['type'] == 'call'].copy()
    atm_calls = calls[
        (calls['strike'] >= stock_price * 0.95) &
        (calls['strike'] <= stock_price * 1.05)
    ].sort_values('strike')

    # Display relevant columns
    display_cols = ['strike', 'bid', 'ask', 'mid', 'volume', 'open_interest', 'iv', 'delta', 'gamma', 'theta', 'vega']
    print(atm_calls[display_cols].head(8).to_string(index=False))

    # Step 7: Test single contract Greeks calculation
    print(f"\nStep 7: Detailed Greeks for one contract...")
    print("-" * 70)

    if not atm_calls.empty:
        sample = atm_calls.iloc[len(atm_calls)//2]  # Middle strike

        print(f"  Contract: {ticker} {sample['expiration']} ${sample['strike']:.0f} Call")
        print(f"  Stock Price: ${stock_price:.2f}")
        print(f"  Strike: ${sample['strike']:.2f}")
        print(f"  DTE: {sample['days_to_exp']} days")
        print(f"  IV: {sample['iv']*100:.1f}%")
        print(f"  Market Price: ${sample['mid']:.2f} (bid: ${sample['bid']:.2f}, ask: ${sample['ask']:.2f})")
        print(f"\n  GREEKS:")
        print(f"    Delta: {sample['delta']:.4f}")
        print(f"    Gamma: {sample['gamma']:.4f}")
        print(f"    Theta: {sample['theta']:.4f}")
        print(f"    Vega: {sample['vega']:.4f}")
        print(f"    Theoretical Price: ${sample['price']:.2f}")
        print(f"\n  LIQUIDITY:")
        print(f"    Volume: {int(sample['volume']):,}")
        print(f"    Open Interest: {int(sample['open_interest']):,}")
        print(f"    Bid-Ask Spread: {sample['spread_pct']:.2f}%")

    # Step 8: Summary
    print(f"\n{'='*70}")
    print("FOUNDATION TEST COMPLETE")
    print(f"{'='*70}")
    print(f"\n[SUCCESS] All components working:")
    print(f"  [OK] Stock data fetching (yfinance)")
    print(f"  [OK] Options chain fetching (yfinance)")
    print(f"  [OK] Historical volatility calculation")
    print(f"  [OK] Greeks calculation (mibian)")
    print(f"  [OK] Data integration (stock + options + Greeks)")
    print(f"\nReady to build the Streamlit UI!\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test options data foundation')
    parser.add_argument('ticker', nargs='?', default='NVDA', help='Stock ticker to test (default: NVDA)')

    args = parser.parse_args()

    test_complete_pipeline(args.ticker)
