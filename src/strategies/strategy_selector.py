"""
Strategy selector that maps investment thesis to specific options strategies.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class StrategyType(Enum):
    """Available options strategies."""
    # Bullish strategies
    LONG_CALL = "Long Call"
    BULL_CALL_SPREAD = "Bull Call Spread"
    CASH_SECURED_PUT = "Cash-Secured Put"

    # Bearish strategies
    LONG_PUT = "Long Put"
    BEAR_PUT_SPREAD = "Bear Put Spread"
    COVERED_CALL = "Covered Call"

    # Neutral/Income strategies
    IRON_CONDOR = "Iron Condor"
    STRADDLE = "Long Straddle"
    STRANGLE = "Long Strangle"
    BUTTERFLY = "Iron Butterfly"


@dataclass
class StrategyRecommendation:
    """Recommended strategy with rationale."""
    strategy: StrategyType
    rationale: str
    risk_level: str  # "Low", "Medium", "High"
    capital_required: str  # "Low", "Medium", "High"
    max_profit: str
    max_loss: str
    breakeven: str
    ideal_conditions: List[str]


class StrategySelector:
    """Select optimal options strategy based on investment thesis."""

    def __init__(self):
        """Initialize strategy selector."""
        pass

    def select_strategy(
        self,
        direction: str,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        current_price: float,
        historical_vol: float,
        implied_vol: Optional[float] = None
    ) -> StrategyRecommendation:
        """
        Select optimal strategy based on thesis parameters.

        Args:
            direction: "BULLISH", "BEARISH", or "NEUTRAL"
            conviction: 0-100 confidence level
            expected_move_pct: Expected % move (e.g., 0.15 for +15%)
            timeframe_days: Expected timeframe in days
            current_price: Current stock price
            historical_vol: Historical volatility (30-day)
            implied_vol: Implied volatility from options (optional)

        Returns:
            StrategyRecommendation with selected strategy and details
        """

        # Handle UNPREDICTABLE - the bot genuinely doesn't know
        if direction == "UNPREDICTABLE":
            return StrategyRecommendation(
                strategy=StrategyType.IRON_CONDOR,  # Placeholder (not actually recommending trade)
                rationale="**DO NOT TRADE** - Situation is genuinely unpredictable. The bot has determined it cannot reliably predict price movement given available data. Wait for clarity before trading.",
                risk_level="N/A",
                capital_required="N/A",
                max_profit="N/A - No trade recommended",
                max_loss="N/A - No trade recommended",
                breakeven="N/A - No trade recommended",
                ideal_conditions=[
                    "Wait for binary event resolution (FDA decision, lawsuit verdict, etc.)",
                    "Wait for more data to form coherent thesis",
                    "Situation is unpredictable - avoid trading in uncertainty"
                ]
            )

        # Determine volatility environment
        iv_rank = self._calculate_iv_rank(historical_vol, implied_vol)

        # Select strategy based on directional view and conviction
        if direction == "BULLISH":
            return self._select_bullish_strategy(
                conviction, expected_move_pct, timeframe_days, iv_rank, current_price
            )
        elif direction == "BEARISH":
            return self._select_bearish_strategy(
                conviction, expected_move_pct, timeframe_days, iv_rank, current_price
            )
        else:  # NEUTRAL
            return self._select_neutral_strategy(
                conviction, expected_move_pct, timeframe_days, iv_rank, current_price
            )

    def _select_bullish_strategy(
        self,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        iv_rank: str,
        current_price: float
    ) -> StrategyRecommendation:
        """Select bullish strategy."""

        # High conviction + large expected move → Long Call
        if conviction >= 70 and abs(expected_move_pct) >= 0.10:
            return StrategyRecommendation(
                strategy=StrategyType.LONG_CALL,
                rationale=f"High conviction ({conviction}%) with significant expected move ({expected_move_pct*100:+.1f}%). Long call provides unlimited upside.",
                risk_level="High",
                capital_required="Low",
                max_profit="Unlimited",
                max_loss="Premium paid",
                breakeven="Strike + Premium",
                ideal_conditions=[
                    f"Stock rallies above ${current_price * (1 + expected_move_pct):.2f}",
                    "Implied volatility increases (vega positive)",
                    f"Movement happens within {timeframe_days} days (theta decay)"
                ]
            )

        # Moderate conviction + moderate move → Bull Call Spread
        elif conviction >= 50 and abs(expected_move_pct) >= 0.05:
            return StrategyRecommendation(
                strategy=StrategyType.BULL_CALL_SPREAD,
                rationale=f"Moderate conviction ({conviction}%) with {expected_move_pct*100:+.1f}% expected move. Bull call spread limits risk and reduces cost.",
                risk_level="Medium",
                capital_required="Low",
                max_profit="Spread width - Premium paid",
                max_loss="Premium paid (net debit)",
                breakeven="Long strike + Net premium",
                ideal_conditions=[
                    f"Stock rises to ${current_price * (1 + expected_move_pct):.2f} or higher",
                    "Movement happens before expiration",
                    "Defined risk makes position sizing easier"
                ]
            )

        # Lower conviction or high IV → Cash-Secured Put
        else:
            return StrategyRecommendation(
                strategy=StrategyType.CASH_SECURED_PUT,
                rationale=f"Moderate bullish view ({conviction}%) with willingness to own stock. Selling puts generates income in high IV environment.",
                risk_level="Medium",
                capital_required="High",
                max_profit="Premium collected",
                max_loss="Strike - Premium (if stock goes to $0)",
                breakeven="Strike - Premium",
                ideal_conditions=[
                    f"Stock stays above ${current_price * 0.95:.2f}",
                    "Willing to own stock at strike price",
                    "High implied volatility boosts premium collected"
                ]
            )

    def _select_bearish_strategy(
        self,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        iv_rank: str,
        current_price: float
    ) -> StrategyRecommendation:
        """Select bearish strategy."""

        # High conviction + large expected move → Long Put
        if conviction >= 70 and abs(expected_move_pct) >= 0.10:
            return StrategyRecommendation(
                strategy=StrategyType.LONG_PUT,
                rationale=f"High conviction ({conviction}%) bearish view with {expected_move_pct*100:.1f}% expected decline. Long put provides significant downside profit.",
                risk_level="High",
                capital_required="Low",
                max_profit="Strike - Premium (if stock goes to $0)",
                max_loss="Premium paid",
                breakeven="Strike - Premium",
                ideal_conditions=[
                    f"Stock falls below ${current_price * (1 + expected_move_pct):.2f}",
                    "Implied volatility increases",
                    f"Movement happens within {timeframe_days} days"
                ]
            )

        # Moderate conviction → Bear Put Spread
        elif conviction >= 50:
            return StrategyRecommendation(
                strategy=StrategyType.BEAR_PUT_SPREAD,
                rationale=f"Moderate bearish conviction ({conviction}%) with {expected_move_pct*100:.1f}% expected decline. Bear put spread limits cost and defines risk.",
                risk_level="Medium",
                capital_required="Low",
                max_profit="Spread width - Premium paid",
                max_loss="Premium paid (net debit)",
                breakeven="Long strike - Net premium",
                ideal_conditions=[
                    f"Stock declines to ${current_price * (1 + expected_move_pct):.2f} or lower",
                    "Movement happens before expiration",
                    "Cheaper than long put"
                ]
            )

        # Own stock + want income → Covered Call
        else:
            return StrategyRecommendation(
                strategy=StrategyType.COVERED_CALL,
                rationale=f"Mildly bearish/neutral view ({conviction}%). If you own stock, selling covered calls generates income.",
                risk_level="Low",
                capital_required="High",
                max_profit="Premium + (Strike - Stock price)",
                max_loss="Stock price - Premium (if stock goes to $0)",
                breakeven="Stock cost basis - Premium",
                ideal_conditions=[
                    f"Stock stays below ${current_price * 1.05:.2f}",
                    "Already own 100 shares",
                    "High IV boosts premium collected"
                ]
            )

    def _select_neutral_strategy(
        self,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        iv_rank: str,
        current_price: float
    ) -> StrategyRecommendation:
        """Select neutral strategy."""

        # Expecting big move but unsure of direction → Straddle
        if abs(expected_move_pct) >= 0.10:
            return StrategyRecommendation(
                strategy=StrategyType.STRADDLE,
                rationale=f"Expecting significant volatility ({abs(expected_move_pct)*100:.1f}% move) but uncertain of direction. Straddle profits from large moves either way.",
                risk_level="High",
                capital_required="Medium",
                max_profit="Unlimited",
                max_loss="Total premium paid",
                breakeven="Strike +/- Total premium",
                ideal_conditions=[
                    f"Stock moves beyond ${current_price * (1 - abs(expected_move_pct)):.2f} or ${current_price * (1 + abs(expected_move_pct)):.2f}",
                    "Implied volatility increases",
                    "Major catalyst expected (earnings, FDA approval, etc.)"
                ]
            )

        # Expecting moderate move, unsure direction → Strangle
        elif abs(expected_move_pct) >= 0.05:
            return StrategyRecommendation(
                strategy=StrategyType.STRANGLE,
                rationale=f"Expecting moderate volatility but uncertain of direction. Strangle is cheaper than straddle with similar payoff profile.",
                risk_level="Medium",
                capital_required="Low-Medium",
                max_profit="Unlimited",
                max_loss="Total premium paid",
                breakeven="Strikes +/- Total premium",
                ideal_conditions=[
                    "Stock makes significant move in either direction",
                    "Lower cost than straddle",
                    "Catalyst expected but direction unclear"
                ]
            )

        # Expecting low volatility → Iron Condor
        else:
            return StrategyRecommendation(
                strategy=StrategyType.IRON_CONDOR,
                rationale=f"Low expected volatility ({abs(expected_move_pct)*100:.1f}%). Iron condor profits from range-bound movement and time decay.",
                risk_level="Medium",
                capital_required="Medium",
                max_profit="Net premium collected",
                max_loss="Spread width - Premium",
                breakeven="Short strikes +/- Net premium",
                ideal_conditions=[
                    f"Stock stays between ${current_price * 0.95:.2f} and ${current_price * 1.05:.2f}",
                    "High implied volatility (sell premium)",
                    "Time decay works in your favor"
                ]
            )

    def _calculate_iv_rank(self, historical_vol: float, implied_vol: Optional[float]) -> str:
        """
        Calculate IV rank (simplified).

        Returns:
            "High", "Medium", or "Low"
        """
        if implied_vol is None:
            return "Medium"  # Unknown

        # Compare IV to HV
        ratio = implied_vol / historical_vol

        if ratio >= 1.5:
            return "High"
        elif ratio <= 0.8:
            return "Low"
        else:
            return "Medium"


if __name__ == "__main__":
    # Test strategy selector
    print("\n" + "="*70)
    print("TESTING STRATEGY SELECTOR")
    print("="*70 + "\n")

    selector = StrategySelector()

    # Test Case 1: High conviction bullish
    print("Test Case 1: High conviction bullish (NVDA example)")
    print("-" * 70)

    recommendation = selector.select_strategy(
        direction="BULLISH",
        conviction=75,
        expected_move_pct=0.20,  # +20%
        timeframe_days=30,
        current_price=188.54,
        historical_vol=0.45,
        implied_vol=0.52
    )

    print(f"Strategy: {recommendation.strategy.value}")
    print(f"Rationale: {recommendation.rationale}")
    print(f"Risk Level: {recommendation.risk_level}")
    print(f"Capital Required: {recommendation.capital_required}")
    print(f"Max Profit: {recommendation.max_profit}")
    print(f"Max Loss: {recommendation.max_loss}")
    print(f"Breakeven: {recommendation.breakeven}")
    print(f"\nIdeal Conditions:")
    for condition in recommendation.ideal_conditions:
        print(f"  - {condition}")

    # Test Case 2: Moderate bearish
    print("\n" + "="*70)
    print("Test Case 2: Moderate conviction bearish")
    print("-" * 70)

    recommendation = selector.select_strategy(
        direction="BEARISH",
        conviction=60,
        expected_move_pct=-0.08,  # -8%
        timeframe_days=45,
        current_price=188.54,
        historical_vol=0.45,
        implied_vol=0.48
    )

    print(f"Strategy: {recommendation.strategy.value}")
    print(f"Rationale: {recommendation.rationale}")
    print(f"Risk Level: {recommendation.risk_level}")
    print(f"Max Profit: {recommendation.max_profit}")
    print(f"Max Loss: {recommendation.max_loss}")

    # Test Case 3: Neutral, expecting big move
    print("\n" + "="*70)
    print("Test Case 3: Neutral with high volatility expectation")
    print("-" * 70)

    recommendation = selector.select_strategy(
        direction="NEUTRAL",
        conviction=50,
        expected_move_pct=0.12,  # Expecting 12% move but unsure direction
        timeframe_days=7,
        current_price=188.54,
        historical_vol=0.45,
        implied_vol=0.40
    )

    print(f"Strategy: {recommendation.strategy.value}")
    print(f"Rationale: {recommendation.rationale}")
    print(f"Risk Level: {recommendation.risk_level}")
    print(f"Max Profit: {recommendation.max_profit}")

    print("\n" + "="*70)
    print("[SUCCESS] Strategy Selector Working!")
    print("="*70 + "\n")
