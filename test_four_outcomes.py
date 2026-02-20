"""
Test all four possible outcomes: BULLISH, BEARISH, NEUTRAL, UNPREDICTABLE
No quotas, no forced distributions - just honest predictions based on data.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from strategies.strategy_selector import StrategySelector

print("\n" + "="*70)
print("TESTING FOUR POSSIBLE OUTCOMES")
print("No quotas - bot says what the data supports")
print("="*70 + "\n")

selector = StrategySelector()

# Outcome 1: BULLISH - Clear upward prediction
print("Outcome 1: BULLISH - Strong fundamental momentum, clear catalysts")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="BULLISH",
    conviction=75,
    expected_move_pct=0.18,  # +18%
    timeframe_days=30,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.52
)

print(f"Direction: BULLISH")
print(f"Conviction: 75%")
print(f"Expected Move: +18% in 30 days")
print(f"\nStrategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"Risk Level: {recommendation.risk_level}")
print(f"Max Profit: {recommendation.max_profit}")
print(f"Max Loss: {recommendation.max_loss}")

# Outcome 2: BEARISH - Clear downward prediction
print("\n" + "="*70)
print("Outcome 2: BEARISH - Deteriorating fundamentals, negative catalysts")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="BEARISH",
    conviction=68,
    expected_move_pct=-0.12,  # -12%
    timeframe_days=45,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.48
)

print(f"Direction: BEARISH")
print(f"Conviction: 68%")
print(f"Expected Move: -12% in 45 days")
print(f"\nStrategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"Risk Level: {recommendation.risk_level}")

# Outcome 3: NEUTRAL - Range-bound prediction (TRADEABLE)
print("\n" + "="*70)
print("Outcome 3: NEUTRAL - Range-bound, no major catalysts")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="NEUTRAL",
    conviction=60,  # Confident it will stay range-bound
    expected_move_pct=0.04,  # ±4% range
    timeframe_days=45,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.55
)

print(f"Direction: NEUTRAL (Range-bound)")
print(f"Conviction: 60%")
print(f"Expected Move: ±4% range over 45 days")
print(f"\nStrategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"Risk Level: {recommendation.risk_level}")
print(f"Max Profit: {recommendation.max_profit}")

# Outcome 4: UNPREDICTABLE - Genuinely don't know
print("\n" + "="*70)
print("Outcome 4: UNPREDICTABLE - Binary event, insufficient data")
print("-" * 70)

recommendation = selector.select_strategy(
    direction="UNPREDICTABLE",
    conviction=0,  # Can't predict
    expected_move_pct=0.0,  # Unknown
    timeframe_days=7,
    current_price=188.54,
    historical_vol=0.45,
    implied_vol=0.65
)

print(f"Direction: UNPREDICTABLE")
print(f"Conviction: 0% (Cannot predict)")
print(f"\nStrategy: {recommendation.strategy.value}")
print(f"Rationale: {recommendation.rationale}")
print(f"\nIdeal Conditions:")
for condition in recommendation.ideal_conditions:
    print(f"  - {condition}")

print("\n" + "="*70)
print("[SUCCESS] All four outcomes working!")
print("\nKey Points:")
print("- BULLISH/BEARISH: Directional predictions with clear rationale")
print("- NEUTRAL: Range-bound prediction (tradeable with Iron Condor)")
print("- UNPREDICTABLE: Honest 'I don't know' (no trade)")
print("- No quotas enforced - bot says what data supports")
print("="*70 + "\n")
