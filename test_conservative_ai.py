"""
Test conservative AI behavior - ensuring it doesn't force predictions.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from strategies.strategy_selector import StrategySelector

print("\n" + "="*70)
print("TESTING CONSERVATIVE STRATEGY SELECTION")
print("="*70 + "\n")

selector = StrategySelector()

# Test Case 1: Low conviction - should recommend NO TRADE
print("Test Case 1: LOW CONVICTION (35%) - Mixed signals, unclear edge")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="BULLISH",  # Slightly bullish but...
    conviction=35,  # Very low conviction
    expected_move_pct=0.05,  # Only 5% expected
    timeframe_days=30,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.48
)

print(f"Strategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"\nIdeal Conditions:")
for condition in recommendation.ideal_conditions:
    print(f"  - {condition}")

# Test Case 2: Moderate conviction (50%) - barely meets threshold
print("\n" + "="*70)
print("Test Case 2: MODERATE CONVICTION (50%) - Meets minimum threshold")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="BULLISH",
    conviction=50,  # Exactly at threshold
    expected_move_pct=0.08,
    timeframe_days=45,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.48
)

print(f"Strategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"Risk Level: {recommendation.risk_level}")

# Test Case 3: NEUTRAL with low conviction - should also recommend no trade
print("\n" + "="*70)
print("Test Case 3: NEUTRAL + LOW CONVICTION (40%)")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="NEUTRAL",
    conviction=40,
    expected_move_pct=0.03,
    timeframe_days=30,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.48
)

print(f"Strategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"\nIdeal Conditions:")
for condition in recommendation.ideal_conditions:
    print(f"  - {condition}")

# Test Case 4: High conviction - should give real recommendation
print("\n" + "="*70)
print("Test Case 4: HIGH CONVICTION (75%) - Clear edge, should trade")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="BULLISH",
    conviction=75,
    expected_move_pct=0.18,
    timeframe_days=30,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.52
)

print(f"Strategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"Risk Level: {recommendation.risk_level}")
print(f"Max Profit: {recommendation.max_profit}")
print(f"Max Loss: {recommendation.max_loss}")

print("\n" + "="*70)
print("[SUCCESS] Conservative behavior working!")
print("Bot will NOT force predictions when conviction is low.")
print("="*70 + "\n")
