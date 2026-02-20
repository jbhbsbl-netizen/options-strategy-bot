"""
Strategy Selector - Maps investment thesis to optimal options strategy.
"""
from typing import Dict, List
from enum import Enum
import pandas as pd


class OptionsStrategy(Enum):
    """Available options strategies."""
    LONG_CALL = "Long Call"
    BULL_CALL_SPREAD = "Bull Call Spread"
    COVERED_CALL = "Covered Call"
    IRON_CONDOR = "Iron Condor"
    STRADDLE = "Long Straddle"
    PUT_CREDIT_SPREAD = "Put Credit Spread"
    LONG_PUT = "Long Put"
    BEAR_PUT_SPREAD = "Bear Put Spread"


class StrategyRecommendation:
    """Recommended options strategy with parameters."""

    def __init__(
        self,
        strategy: OptionsStrategy,
        rationale: str,
        parameters: Dict,
        expected_profit: str,
        max_risk: str,
        breakeven: str
    ):
        self.strategy = strategy
        self.rationale = rationale
        self.parameters = parameters
        self.expected_profit = expected_profit
        self.max_risk = max_risk
        self.breakeven = breakeven


class StrategySelector:
    """Selects optimal options strategy based on investment thesis."""

    def select_strategy(
        self,
        thesis_direction: str,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        stock_price: float,
        implied_vol: float
    ) -> StrategyRecommendation:
        """
        Select best options strategy based on thesis.

        Args:
            thesis_direction: BULLISH, BEARISH, or NEUTRAL
            conviction: 0-100 confidence level
            expected_move_pct: Expected % move (e.g., 12.5 for +12.5%)
            timeframe_days: Days for thesis to play out
            stock_price: Current stock price
            implied_vol: Implied volatility

        Returns:
            StrategyRecommendation with strategy and parameters
        """

        if thesis_direction == "BULLISH":
            return self._bullish_strategy(
                conviction, expected_move_pct, timeframe_days,
                stock_price, implied_vol
            )
        elif thesis_direction == "BEARISH":
            return self._bearish_strategy(
                conviction, expected_move_pct, timeframe_days,
                stock_price, implied_vol
            )
        else:  # NEUTRAL
            return self._neutral_strategy(
                conviction, timeframe_days, stock_price, implied_vol
            )

    def _bullish_strategy(
        self,
        conviction: int,
        expected_move: float,
        days: int,
        price: float,
        iv: float
    ) -> StrategyRecommendation:
        """Select best bullish strategy."""

        # Very bullish + high conviction → Long Call
        if conviction >= 75 and expected_move >= 10:
            target_price = price * (1 + expected_move / 100)
            strike = round(price * 1.05 / 5) * 5  # 5% OTM, round to nearest $5

            return StrategyRecommendation(
                strategy=OptionsStrategy.LONG_CALL,
                rationale=f"High conviction ({conviction}%) bullish thesis with {expected_move:+.1f}% expected move warrants aggressive long call position. Unlimited upside potential.",
                parameters={
                    "strike": strike,
                    "expiration_days": min(days + 15, 60),  # Give extra time
                    "contracts": 1
                },
                expected_profit=f"Unlimited (breakeven at ${strike + 3:.2f})",
                max_risk=f"Premium paid (~${price * 0.03:.2f} per share)",
                breakeven=f"${strike + 3:.2f} (+{((strike + 3)/price - 1)*100:.1f}%)"
            )

        # Moderate bullish → Bull Call Spread
        elif conviction >= 55 and expected_move >= 5:
            long_strike = round(price * 1.03 / 5) * 5  # 3% OTM
            short_strike = round(price * (1 + expected_move/100) / 5) * 5

            return StrategyRecommendation(
                strategy=OptionsStrategy.BULL_CALL_SPREAD,
                rationale=f"Moderate bullish conviction ({conviction}%) with {expected_move:+.1f}% target. Bull call spread offers defined risk/reward with lower cost than long call.",
                parameters={
                    "long_strike": long_strike,
                    "short_strike": short_strike,
                    "expiration_days": days + 10,
                    "contracts": 1
                },
                expected_profit=f"${(short_strike - long_strike) * 100 * 0.7:.0f} (width minus cost)",
                max_risk=f"~${(short_strike - long_strike) * 100 * 0.3:.0f} (net debit)",
                breakeven=f"${long_strike + 1.5:.2f}"
            )

        # Slightly bullish → Covered Call
        else:
            strike = round(price * 1.05 / 5) * 5  # 5% OTM

            return StrategyRecommendation(
                strategy=OptionsStrategy.COVERED_CALL,
                rationale=f"Mild bullish view ({conviction}% conviction) best suited for income generation via covered call. Caps upside but collects premium.",
                parameters={
                    "strike": strike,
                    "expiration_days": min(45, days),
                    "shares_owned": 100
                },
                expected_profit=f"Premium + stock appreciation to ${strike:.2f}",
                max_risk=f"Stock decline (protected by premium)",
                breakeven=f"${price * 0.98:.2f} (cost - premium)"
            )

    def _bearish_strategy(
        self,
        conviction: int,
        expected_move: float,
        days: int,
        price: float,
        iv: float
    ) -> StrategyRecommendation:
        """Select best bearish strategy."""

        expected_move = abs(expected_move)  # Make positive for calculations

        # Very bearish → Long Put
        if conviction >= 75 and expected_move >= 10:
            strike = round(price * 0.95 / 5) * 5  # 5% OTM

            return StrategyRecommendation(
                strategy=OptionsStrategy.LONG_PUT,
                rationale=f"High conviction ({conviction}%) bearish thesis with {expected_move:.1f}% expected decline. Long put offers substantial profit potential.",
                parameters={
                    "strike": strike,
                    "expiration_days": min(days + 15, 60),
                    "contracts": 1
                },
                expected_profit=f"Substantial if stock falls below ${strike * 0.9:.2f}",
                max_risk=f"Premium paid (~${price * 0.025:.2f} per share)",
                breakeven=f"${strike - 2.5:.2f} (-{(1 - (strike - 2.5)/price)*100:.1f}%)"
            )

        # Moderate bearish → Bear Put Spread
        else:
            long_strike = round(price * 0.97 / 5) * 5  # 3% OTM
            short_strike = round(price * (1 - expected_move/100) / 5) * 5

            return StrategyRecommendation(
                strategy=OptionsStrategy.BEAR_PUT_SPREAD,
                rationale=f"Moderate bearish view ({conviction}% conviction). Bear put spread provides defined risk/reward.",
                parameters={
                    "long_strike": long_strike,
                    "short_strike": short_strike,
                    "expiration_days": days + 10,
                    "contracts": 1
                },
                expected_profit=f"${(long_strike - short_strike) * 100 * 0.7:.0f}",
                max_risk=f"~${(long_strike - short_strike) * 100 * 0.3:.0f}",
                breakeven=f"${long_strike - 1.5:.2f}"
            )

    def _neutral_strategy(
        self,
        conviction: int,
        days: int,
        price: float,
        iv: float
    ) -> StrategyRecommendation:
        """Select best neutral strategy."""

        # High IV + neutral → Iron Condor
        if iv > 0.35:
            lower_put = round(price * 0.92 / 5) * 5
            upper_call = round(price * 1.08 / 5) * 5

            return StrategyRecommendation(
                strategy=OptionsStrategy.IRON_CONDOR,
                rationale=f"Neutral thesis with high IV ({iv*100:.0f}%). Iron condor profits from range-bound price action and volatility contraction.",
                parameters={
                    "put_strikes": f"${lower_put - 5:.0f}/${lower_put:.0f}",
                    "call_strikes": f"${upper_call:.0f}/${upper_call + 5:.0f}",
                    "expiration_days": min(45, days),
                    "contracts": 1
                },
                expected_profit=f"~${price * 0.03 * 100:.0f} if stays between ${lower_put:.0f}-${upper_call:.0f}",
                max_risk=f"~${500:.0f} (wing width minus credit)",
                breakeven=f"Two points: ~${lower_put - 2:.0f} and ${upper_call + 2:.0f}"
            )

        # Standard neutral → Covered Call
        else:
            strike = round(price * 1.05 / 5) * 5

            return StrategyRecommendation(
                strategy=OptionsStrategy.COVERED_CALL,
                rationale=f"Neutral outlook best monetized through covered call income strategy. Collect premium while waiting for direction.",
                parameters={
                    "strike": strike,
                    "expiration_days": min(45, days),
                    "shares_owned": 100
                },
                expected_profit=f"Premium income (${price * 0.02 * 100:.0f}-${price * 0.03 * 100:.0f})",
                max_risk=f"Stock decline (partially offset by premium)",
                breakeven=f"${price * 0.98:.2f}"
            )


if __name__ == "__main__":
    print("Testing Strategy Selector...\n")

    selector = StrategySelector()

    # Test bullish thesis
    rec = selector.select_strategy(
        thesis_direction="BULLISH",
        conviction=80,
        expected_move_pct=15.0,
        timeframe_days=45,
        stock_price=250.0,
        implied_vol=0.30
    )

    print(f"Strategy: {rec.strategy.value}")
    print(f"Rationale: {rec.rationale}")
    print(f"Parameters: {rec.parameters}")
    print(f"Expected Profit: {rec.expected_profit}")
    print(f"Max Risk: {rec.max_risk}")
    print(f"Breakeven: {rec.breakeven}")
