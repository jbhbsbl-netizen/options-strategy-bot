"""
Test P/L Calculator with NVDA Bull Call Spread

Expected Results:
- Max Profit: $2,427.50 (at $230+)
- Max Loss: $572.50 (at $200-)
- Breakeven: $205.72
- Current P/L at $188.54: -$572.50 (not yet profitable)
"""
from src.models.thesis import ContractSelection
from src.analysis.pnl_calculator import PnLCalculator
from src.visualization.pnl_chart import create_pnl_chart, create_metrics_table


def test_nvda_bull_call_spread():
    """Test with NVDA Bull Call Spread example."""

    print("=" * 80)
    print("TESTING P/L CALCULATOR: NVDA Bull Call Spread")
    print("=" * 80)

    # Create test contracts (NVDA Bull Call Spread)
    contracts = [
        ContractSelection(
            action="BUY",
            symbol="NVDA250320C00200000",
            display_name="NVDA Mar20 $200 Call",
            strike=200.0,
            expiration="2025-03-20",
            option_type="call",
            premium=6.90,
            delta=0.55,
            quantity=1,
            cost_or_credit=690.0
        ),
        ContractSelection(
            action="SELL",
            symbol="NVDA250320C00230000",
            display_name="NVDA Mar20 $230 Call",
            strike=230.0,
            expiration="2025-03-20",
            option_type="call",
            premium=1.17,
            delta=0.25,
            quantity=1,
            cost_or_credit=117.0
        )
    ]

    # Current stock price
    current_price = 188.54

    # Initialize calculator
    calculator = PnLCalculator()

    print("\n[CONTRACTS]")
    print("-" * 80)
    for c in contracts:
        print(f"{c.action:4s} {c.display_name:25s} @ ${c.premium:6.2f} (Delta: {c.delta:.2f})")
        if c.action == "BUY":
            print(f"     Cost: ${c.cost_or_credit:.2f}")
        else:
            print(f"     Credit: ${c.cost_or_credit:.2f}")

    net_debit = 690.0 - 117.0
    print(f"\n     Net Debit: ${net_debit:.2f}")

    # Calculate complete analysis
    print("\n[CALCULATING P/L ANALYSIS...]")
    analysis = calculator.calculate_complete_analysis(
        contracts=contracts,
        current_price=current_price,
        volatility=0.40,
        days_to_expiration=35
    )

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\n[MAX PROFIT]    ${analysis['max_profit']:,.2f}")
    print(f"   At price >= ${analysis['max_profit_price']:.2f}")

    print(f"\n[MAX LOSS]      ${analysis['max_loss']:,.2f}")
    print(f"   At price <= ${analysis['max_loss_price']:.2f}")

    print(f"\n[BREAKEVEN(S)]")
    for i, be in enumerate(analysis['breakevens'], 1):
        print(f"   Breakeven {i}: ${be:.2f}")

    print(f"\n[RISK/REWARD]   {analysis['risk_reward_ratio']:.2f}:1")

    print(f"\n[NET DEBIT]     ${analysis['net_debit_credit']:.2f}")

    print(f"\n[CURRENT P/L]   ${analysis['current_pnl']:,.2f}")
    print(f"   (at current price ${current_price:.2f})")

    # Greeks
    if analysis['greeks']:
        print(f"\n[PORTFOLIO GREEKS]")
        greeks = analysis['greeks']
        print(f"   Delta:  {greeks['portfolio_delta']:7.2f} (directional exposure)")
        print(f"   Theta:  {greeks['portfolio_theta']:7.2f} (time decay per day)")
        print(f"   Vega:   {greeks['portfolio_vega']:7.2f} (IV sensitivity)")
        print(f"   Gamma:  {greeks['portfolio_gamma']:7.4f} (delta acceleration)")

    # Test specific price points
    print("\n" + "=" * 80)
    print("P/L AT VARIOUS PRICES")
    print("=" * 80)

    test_prices = [180, 200, 205.72, 210, 220, 230, 250]
    print(f"\n{'Price':>8s} | {'P/L':>12s} | Notes")
    print("-" * 50)

    for price in test_prices:
        pnl = calculator.calculate_pnl_at_price(contracts, price)

        if price <= 200:
            note = "Max loss zone"
        elif price >= 230:
            note = "Max profit zone"
        elif abs(price - 205.72) < 0.5:
            note = "Breakeven"
        else:
            note = "Profit zone"

        print(f"${price:7.2f} | ${pnl:11,.2f} | {note}")

    # Verify against expected values
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    expected_max_profit = 2427.50
    expected_max_loss = -572.50
    expected_breakeven = 205.72
    expected_net_debit = 572.50

    errors = []

    # Check max profit (within $1)
    if abs(analysis['max_profit'] - expected_max_profit) > 1.0:
        errors.append(f"Max Profit: Expected ${expected_max_profit:.2f}, got ${analysis['max_profit']:.2f}")
    else:
        print(f"[PASS] Max Profit: ${analysis['max_profit']:,.2f} (expected ${expected_max_profit:,.2f})")

    # Check max loss (within $1)
    if abs(analysis['max_loss'] - expected_max_loss) > 1.0:
        errors.append(f"Max Loss: Expected ${expected_max_loss:.2f}, got ${analysis['max_loss']:.2f}")
    else:
        print(f"[PASS] Max Loss: ${analysis['max_loss']:,.2f} (expected ${expected_max_loss:,.2f})")

    # Check breakeven (within $0.10)
    if analysis['breakevens']:
        be = analysis['breakevens'][0]
        if abs(be - expected_breakeven) > 0.10:
            errors.append(f"Breakeven: Expected ${expected_breakeven:.2f}, got ${be:.2f}")
        else:
            print(f"[PASS] Breakeven: ${be:.2f} (expected ${expected_breakeven:.2f})")
    else:
        errors.append("No breakeven found!")

    # Check net debit
    if abs(analysis['net_debit_credit'] - expected_net_debit) > 1.0:
        errors.append(f"Net Debit: Expected ${expected_net_debit:.2f}, got ${analysis['net_debit_credit']:.2f}")
    else:
        print(f"[PASS] Net Debit: ${analysis['net_debit_credit']:.2f} (expected ${expected_net_debit:.2f})")

    # Check P/L curve has data
    if len(analysis['pnl_curve']) > 0:
        print(f"[PASS] P/L Curve: {len(analysis['pnl_curve'])} price points generated")
    else:
        errors.append("P/L curve is empty!")

    # Check Greeks were calculated
    if analysis['greeks']:
        print(f"[PASS] Greeks: Portfolio Delta = {analysis['greeks']['portfolio_delta']:.2f}")
    else:
        print("[WARN]  Greeks: Not calculated (mibian not available)")

    # Report errors
    if errors:
        print("\n[FAIL] ERRORS FOUND:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("\n[PASS] ALL CHECKS PASSED!")

    # Generate chart
    print("\n" + "=" * 80)
    print("GENERATING P/L CHART")
    print("=" * 80)

    try:
        chart = create_pnl_chart(
            pnl_curve=analysis['pnl_curve'],
            current_price=current_price,
            max_profit=analysis['max_profit'],
            max_loss=analysis['max_loss'],
            max_profit_price=analysis['max_profit_price'],
            max_loss_price=analysis['max_loss_price'],
            breakevens=analysis['breakevens'],
            strategy_name="NVDA Bull Call Spread",
            target_price=226.0  # From thesis
        )

        # Save chart
        chart.write_html("test_pnl_chart.html")
        print("[PASS] Chart saved to: test_pnl_chart.html")
        print("   Open this file in a browser to view the interactive chart!")

        # Generate metrics table
        metrics_html = create_metrics_table(
            max_profit=analysis['max_profit'],
            max_loss=analysis['max_loss'],
            breakevens=analysis['breakevens'],
            current_price=current_price,
            net_debit_credit=analysis['net_debit_credit'],
            risk_reward_ratio=analysis['risk_reward_ratio'],
            current_pnl=analysis['current_pnl'],
            greeks=analysis['greeks']
        )

        # Save metrics table
        with open("test_metrics_table.html", "w") as f:
            f.write("<html><head><style>body { font-family: Arial, sans-serif; padding: 20px; }</style></head><body>")
            f.write("<h2>NVDA Bull Call Spread - Risk Metrics</h2>")
            f.write(metrics_html)
            f.write("</body></html>")

        print("[PASS] Metrics table saved to: test_metrics_table.html")

    except Exception as e:
        print(f"[FAIL] Error generating chart: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_nvda_bull_call_spread()
    exit(0 if success else 1)
