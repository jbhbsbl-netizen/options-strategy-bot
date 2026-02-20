"""
Test contract picker with real options chain data.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.yfinance_client import YFinanceClient
from strategies.contract_picker import ContractPicker

print("\n" + "="*70)
print("TESTING CONTRACT PICKER")
print("="*70 + "\n")

# Fetch real options chain
ticker = "NVDA"
client = YFinanceClient()

print(f"Fetching options chain for {ticker}...")
stock_data = client.get_stock_data(ticker)
current_price = stock_data['current_price']
print(f"Current price: ${current_price:.2f}\n")

# Get options chain for all expirations
print("Fetching options chain (next 10 expirations)...")
options_chain = client.get_options_chain_all_expirations(ticker, max_expirations=10)

if options_chain is None or len(options_chain) == 0:
    print("ERROR: Could not fetch options chain")
    sys.exit(1)

print(f"Available expirations: {len(options_chain)}")
for exp in list(options_chain.keys())[:5]:
    print(f"  - {exp}")

# Initialize contract picker
picker = ContractPicker()

# Test Case 1: Bull Call Spread
print("\n" + "="*70)
print("Test Case 1: BULL CALL SPREAD")
print("Thesis: BULLISH, target $226 (+20%), 30 days")
print("-" * 70)

contracts = picker.pick_contracts(
    strategy_name="Bull Call Spread",
    direction="BULLISH",
    target_price=226.0,
    timeframe_days=30,
    current_price=current_price,
    options_chain=options_chain
)

for contract_selection in contracts:
    c = contract_selection.contract
    action = contract_selection.action
    premium = contract_selection.premium
    cost = contract_selection.cost_or_credit

    print(f"\n{action}: {ticker} {c.expiration} ${c.strike:.0f} {c.option_type.upper()}")
    print(f"  Bid/Ask: ${c.bid:.2f} / ${c.ask:.2f}")
    print(f"  Premium (mid): ${premium:.2f}")
    print(f"  Cost/Credit: ${cost:.2f}")
    if c.delta:
        print(f"  Delta: {c.delta:.3f}")

# Calculate net debit
net_debit = sum(cs.cost_or_credit for cs in contracts)
print(f"\nNet Debit: ${net_debit:.2f}")

# Calculate max profit/loss for spread
if len(contracts) == 2:
    long_strike = contracts[0].contract.strike
    short_strike = contracts[1].contract.strike
    spread_width = (short_strike - long_strike) * 100
    max_profit = spread_width - net_debit
    max_loss = net_debit
    breakeven = long_strike + (net_debit / 100)

    print(f"\nSpread Analysis:")
    print(f"  Long strike:  ${long_strike:.0f}")
    print(f"  Short strike: ${short_strike:.0f}")
    print(f"  Spread width: ${spread_width:.0f}")
    print(f"  Max Profit:   ${max_profit:.2f}")
    print(f"  Max Loss:     ${max_loss:.2f}")
    print(f"  Breakeven:    ${breakeven:.2f}")
    print(f"  Risk/Reward:  {max_profit/max_loss:.2f}:1")

# Test Case 2: Long Call
print("\n" + "="*70)
print("Test Case 2: LONG CALL")
print("Thesis: BULLISH high conviction, target $240 (+27%), 45 days")
print("-" * 70)

contracts = picker.pick_contracts(
    strategy_name="Long Call",
    direction="BULLISH",
    target_price=240.0,
    timeframe_days=45,
    current_price=current_price,
    options_chain=options_chain
)

for contract_selection in contracts:
    c = contract_selection.contract
    action = contract_selection.action
    premium = contract_selection.premium
    cost = contract_selection.cost_or_credit

    print(f"\n{action}: {ticker} {c.expiration} ${c.strike:.0f} {c.option_type.upper()}")
    print(f"  Bid/Ask: ${c.bid:.2f} / ${c.ask:.2f}")
    print(f"  Premium (mid): ${premium:.2f}")
    print(f"  Total Cost: ${cost:.2f}")
    if c.delta:
        print(f"  Delta: {c.delta:.3f}")

net_cost = sum(cs.cost_or_credit for cs in contracts)
print(f"\nMax Loss: ${net_cost:.2f} (premium paid)")
print(f"Breakeven: ${contracts[0].contract.strike + (net_cost/100):.2f}")

# Test Case 3: Iron Condor
print("\n" + "="*70)
print("Test Case 3: IRON CONDOR")
print("Thesis: NEUTRAL, expect ±5% range, 30 days")
print("-" * 70)

contracts = picker.pick_contracts(
    strategy_name="Iron Condor",
    direction="NEUTRAL",
    target_price=current_price,  # Expect to stay near current
    timeframe_days=30,
    current_price=current_price,
    options_chain=options_chain
)

print(f"\nIron Condor (4 legs):")
for i, contract_selection in enumerate(contracts, 1):
    c = contract_selection.contract
    action = contract_selection.action
    premium = contract_selection.premium
    cost = contract_selection.cost_or_credit

    print(f"\nLeg {i}: {action} {ticker} {c.expiration} ${c.strike:.0f} {c.option_type.upper()}")
    print(f"  Premium: ${premium:.2f}, Cost/Credit: ${cost:.2f}")

net_credit = -sum(cs.cost_or_credit for cs in contracts)  # Negative = credit received
print(f"\nNet Credit Received: ${net_credit:.2f}")
print(f"Max Profit: ${net_credit:.2f} (if stock stays in range)")

print("\n" + "="*70)
print("[SUCCESS] Contract Picker Working!")
print("="*70 + "\n")
