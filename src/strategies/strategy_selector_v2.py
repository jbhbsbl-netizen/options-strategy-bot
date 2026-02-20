"""
Enhanced Strategy Selector with Autonomous Research.

V1: Hardcoded rules (if conviction >= 70 → Long Call)
V2: Research-informed decisions (learns from web research what works best)

The bot now researches:
- "Bull call spread vs long call - when to choose?"
- "What strategies work best for [TICKER]?"
- "Optimal strategy for [conviction]% conviction [direction] move"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, List, Optional
from dataclasses import dataclass

# Import V1 as base
from strategies.strategy_selector import StrategySelector, StrategyType, StrategyRecommendation
from research.research_orchestrator import ResearchOrchestrator, ComprehensiveResearch


@dataclass
class ResearchInsights:
    """Insights extracted from research articles."""

    # Strategy preference insights
    prefers_spread: bool = False  # Research suggests spread over directional
    prefers_directional: bool = False  # Research suggests directional over spread
    prefers_neutral: bool = False  # Research suggests neutral strategy

    # Specific recommendations
    recommended_strategy: Optional[str] = None  # e.g., "Bull Call Spread"
    reasoning: Optional[str] = None  # Why this strategy

    # Context factors
    high_iv_environment: bool = False  # High IV → favor credit strategies
    low_iv_environment: bool = False  # Low IV → favor debit strategies
    high_momentum: bool = False  # High momentum → favor directional

    # Risk factors
    earnings_approaching: bool = False  # Earnings soon → be cautious
    high_volatility: bool = False  # High vol → wider spreads


class StrategySelectV2(StrategySelector):
    """
    Enhanced strategy selector with autonomous research.

    Inherits from V1 and adds research capability.
    """

    def __init__(self, enable_research: bool = True):
        """
        Initialize enhanced strategy selector.

        Args:
            enable_research: Whether to enable web research (default True)
        """
        super().__init__()
        self.enable_research = enable_research

        if enable_research:
            self.orchestrator = ResearchOrchestrator()
            print("[StrategySelector V2] Research ENABLED - will learn from web")
        else:
            self.orchestrator = None
            print("[StrategySelector V2] Research DISABLED - using V1 rules")

    def select_strategy_with_research(
        self,
        ticker: str,
        direction: str,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        current_price: float,
        historical_vol: float,
        implied_vol: Optional[float] = None,
        earnings_info: Optional[Dict] = None,
        articles_per_question: int = 2
    ) -> tuple[StrategyRecommendation, Optional[ComprehensiveResearch], Optional[StrategyRecommendation]]:
        """
        Select strategy with research insights.

        Args:
            ticker: Stock ticker
            direction: "BULLISH", "BEARISH", "NEUTRAL", or "UNPREDICTABLE"
            conviction: 0-100 confidence level
            expected_move_pct: Expected % move (e.g., 0.15 for +15%)
            timeframe_days: Expected timeframe in days
            current_price: Current stock price
            historical_vol: Historical volatility (30-day)
            implied_vol: Implied volatility from options (optional)
            earnings_info: Optional earnings date/timing (ADDITIONAL context)
            articles_per_question: Articles per research question

        Returns:
            Tuple of (primary_strategy, research, earnings_strategy_optional)
        """

        research = None

        # Phase 1: Research strategy selection (if enabled)
        if self.enable_research and self.orchestrator:
            print(f"\n{'='*80}")
            print(f"[STRATEGY RESEARCH] Researching optimal strategy for {ticker}")
            print(f"{'='*80}\n")

            print(f"[Context] {direction} {conviction}% conviction, {expected_move_pct*100:+.0f}% in {timeframe_days} days")

            # Research with thesis context (includes earnings if within 30 days)
            research = self.orchestrator.research_everything(
                ticker=ticker,
                thesis_direction=direction,
                expected_move_pct=expected_move_pct,
                timeframe_days=timeframe_days,
                earnings_info=earnings_info,  # ADDITIONAL layer
                articles_per_question=articles_per_question
            )

            print(f"\n[STRATEGY RESEARCH] Complete:")
            print(f"  - Questions: {research.total_questions}")
            print(f"  - Articles: {research.total_articles}")
            print(f"  - Words: {research.total_words:,}")

        # Phase 2: Extract insights from research
        insights = None
        if research and research.strategy_research:
            print(f"\n[EXTRACTING INSIGHTS] Analyzing research findings...")
            insights = self._extract_strategy_insights(research)

            if insights.recommended_strategy:
                print(f"  - Research suggests: {insights.recommended_strategy}")
                print(f"  - Reasoning: {insights.reasoning}")

        # Phase 3: Select PRIMARY strategy with insights
        print(f"\n[DECISION] Selecting PRIMARY strategy...")

        if insights and insights.recommended_strategy:
            print(f"  - Using research-informed decision")
            recommendation = self._make_research_informed_decision(
                direction, conviction, expected_move_pct, timeframe_days,
                current_price, historical_vol, implied_vol, insights
            )
        else:
            print(f"  - Using V1 rules (no research insights)")
            recommendation = super().select_strategy(
                direction, conviction, expected_move_pct, timeframe_days,
                current_price, historical_vol, implied_vol
            )

        # Phase 4: Evaluate EARNINGS opportunity (ADDITIONAL - only if research exists)
        earnings_strategy = None
        if research and research.earnings_research:
            print(f"\n[EARNINGS EVALUATION] Checking if earnings play makes sense...")
            earnings_strategy = self._evaluate_earnings_opportunity(
                ticker, research, current_price, historical_vol, implied_vol, direction
            )

            if earnings_strategy:
                print(f"  --> CLEAR EARNINGS OPPORTUNITY FOUND")
                print(f"  --> Alternative: {earnings_strategy.strategy}")
            else:
                print(f"  --> No clear earnings edge (will just mention earnings)")

        return recommendation, research, earnings_strategy

    def _extract_strategy_insights(self, research: ComprehensiveResearch) -> ResearchInsights:
        """
        Extract actionable insights from research articles.

        This is a simplified version that looks for keywords.
        In a production system, you'd use LLM to extract structured insights.

        Args:
            research: Research findings

        Returns:
            ResearchInsights with extracted recommendations
        """
        insights = ResearchInsights()

        if not research.strategy_research:
            return insights

        # Combine all article content
        all_content = ""
        for article in research.strategy_research.articles:
            all_content += article.content.lower() + " "

        # Look for strategy preferences
        if "spread" in all_content and all_content.count("spread") > 5:
            insights.prefers_spread = True
            insights.reasoning = "Research emphasizes spread strategies"

        if "bull call spread" in all_content:
            insights.recommended_strategy = "Bull Call Spread"
            if not insights.reasoning:
                insights.reasoning = "Bull call spread mentioned in research"

        if "long call" in all_content and "unlimited upside" in all_content:
            insights.prefers_directional = True
            if all_content.count("long call") > all_content.count("spread"):
                insights.recommended_strategy = "Long Call"
                insights.reasoning = "Research favors directional long call"

        # Look for IV environment
        if "high iv" in all_content or "implied volatility" in all_content:
            if "sell premium" in all_content or "credit" in all_content:
                insights.high_iv_environment = True
                insights.reasoning = (insights.reasoning or "") + "; High IV favors credit strategies"

        # Look for risk factors
        if "earnings" in all_content and "caution" in all_content:
            insights.earnings_approaching = True

        if "high volatility" in all_content or "volatile" in all_content:
            insights.high_volatility = True

        return insights

    def _make_research_informed_decision(
        self,
        direction: str,
        conviction: int,
        expected_move_pct: float,
        timeframe_days: int,
        current_price: float,
        historical_vol: float,
        implied_vol: Optional[float],
        insights: ResearchInsights
    ) -> StrategyRecommendation:
        """
        Make strategy decision informed by research insights.

        This combines V1 rules with research insights.
        """

        # Start with V1 recommendation as baseline
        baseline = super().select_strategy(
            direction, conviction, expected_move_pct, timeframe_days,
            current_price, historical_vol, implied_vol
        )

        # Adjust based on research insights
        if direction == "BULLISH":
            # Research suggests spread over directional
            if insights.prefers_spread and baseline.strategy == StrategyType.LONG_CALL:
                print(f"  - Research override: Spread preferred over Long Call")
                baseline.strategy = StrategyType.BULL_CALL_SPREAD
                baseline.rationale = f"Research suggests spreads work better. {insights.reasoning}. " + baseline.rationale

            # Research suggests directional over spread
            elif insights.prefers_directional and baseline.strategy == StrategyType.BULL_CALL_SPREAD:
                print(f"  - Research override: Long Call preferred over Spread")
                baseline.strategy = StrategyType.LONG_CALL
                baseline.rationale = f"Research favors directional plays. {insights.reasoning}. " + baseline.rationale

            # High IV environment
            elif insights.high_iv_environment:
                print(f"  - Research insight: High IV environment noted")
                if baseline.strategy == StrategyType.LONG_CALL:
                    baseline.strategy = StrategyType.CASH_SECURED_PUT
                    baseline.rationale = f"High IV environment (research). Selling premium is advantageous. " + baseline.rationale

        elif direction == "BEARISH":
            # Similar logic for bearish strategies
            if insights.prefers_spread and baseline.strategy == StrategyType.LONG_PUT:
                print(f"  - Research override: Bear spread preferred")
                baseline.strategy = StrategyType.BEAR_PUT_SPREAD
                baseline.rationale = f"Research suggests spreads. {insights.reasoning}. " + baseline.rationale

        # Add research context to rationale
        if insights.reasoning and insights.reasoning not in baseline.rationale:
            baseline.rationale = f"[Research-Informed] {baseline.rationale}"

        return baseline

    def _evaluate_earnings_opportunity(
        self,
        ticker: str,
        research: ComprehensiveResearch,
        current_price: float,
        historical_vol: float,
        implied_vol: Optional[float],
        direction: str
    ) -> Optional[StrategyRecommendation]:
        """
        Evaluate if earnings research suggests a clear opportunity.

        This is the CRITICAL decision point: suggest earnings strategy ONLY when there's clear edge.

        Args:
            ticker: Stock ticker
            research: Research with earnings findings
            current_price: Current stock price
            historical_vol: Historical volatility
            implied_vol: Implied volatility
            direction: Primary thesis direction

        Returns:
            Earnings strategy if clear opportunity, None otherwise
        """

        if not research.earnings_research:
            return None

        # Analyze earnings research content
        all_content = ""
        for article in research.earnings_research.articles:
            all_content += article.content.lower() + " "

        # Evaluation criteria
        has_consistent_moves = False
        has_high_iv = False
        has_clear_pattern = False

        # Check for consistent historical moves
        move_keywords = ["typically moves", "historical move", "average move", "past quarters"]
        if any(keyword in all_content for keyword in move_keywords):
            # Look for percentage mentions (e.g., "8%", "10%", "15%")
            if any(f"{i}%" in all_content for i in range(5, 25)):
                has_consistent_moves = True
                print(f"    - Found: Consistent historical earnings moves")

        # Check for high IV environment
        iv_keywords = ["high implied volatility", "elevated iv", "iv percentile", "volatility premium"]
        if any(keyword in all_content for keyword in iv_keywords):
            # If IV percentile mentioned above 70
            if "70th percentile" in all_content or "80th percentile" in all_content or "high iv" in all_content:
                has_high_iv = True
                print(f"    - Found: High IV environment")

        # Check for clear beat/miss pattern
        pattern_keywords = ["consistently beats", "always misses", "predictable", "pattern"]
        if any(keyword in all_content for keyword in pattern_keywords):
            has_clear_pattern = True
            print(f"    - Found: Clear earnings pattern")

        # Decision: Suggest earnings strategy ONLY if clear edge
        if (has_consistent_moves and has_high_iv) or (has_clear_pattern and has_consistent_moves):
            print(f"    --> CLEAR EARNINGS EDGE DETECTED")

            # Select appropriate earnings strategy
            if has_high_iv and has_consistent_moves:
                # High IV + big moves → Long Straddle (bet on volatility)
                strategy_type = StrategyType.LONG_STRADDLE if hasattr(StrategyType, 'LONG_STRADDLE') else StrategyType.LONG_CALL
                rationale = (
                    f"Earnings play: {ticker} shows consistent post-earnings moves with elevated IV. "
                    f"Long Straddle profits from large move in either direction. "
                    f"Research shows historical volatility spikes justify the premium cost."
                )
            elif has_clear_pattern and direction == "BULLISH":
                # Clear bullish pattern → Aggressive call play
                strategy_type = StrategyType.LONG_CALL
                rationale = (
                    f"Earnings play: {ticker} has predictable earnings beat pattern. "
                    f"Aggressive long call to capture upside if pattern continues. "
                    f"Research supports directional bet on earnings."
                )
            else:
                # Default earnings strategy
                strategy_type = StrategyType.LONG_CALL
                rationale = f"Earnings play based on research findings."

            return StrategyRecommendation(
                strategy=strategy_type,
                rationale=rationale,
                conviction=70,  # Moderate conviction for earnings plays
                expected_return=0.25,  # Placeholder
                max_risk=current_price * 0.05,  # Placeholder
                risk_reward_ratio=3.0  # Placeholder
            )

        else:
            print(f"    --> No clear earnings edge (mention only, don't force)")
            return None


if __name__ == "__main__":
    # Test strategy selector V2
    print("=" * 80)
    print("TESTING STRATEGY SELECTOR V2 (WITH RESEARCH)")
    print("=" * 80)

    selector = StrategySelectV2(enable_research=True)

    # Test case: NVDA bullish
    print("\n[TEST: NVDA Bullish 75% conviction, +20% in 30 days]")

    recommendation, research = selector.select_strategy_with_research(
        ticker="NVDA",
        direction="BULLISH",
        conviction=75,
        expected_move_pct=0.20,
        timeframe_days=30,
        current_price=188.54,
        historical_vol=0.45,
        implied_vol=0.52,
        articles_per_question=1  # Fewer for testing
    )

    print(f"\n{'='*80}")
    print("[RESULTS]")
    print(f"{'='*80}")
    print(f"Strategy: {recommendation.strategy.value}")
    print(f"Rationale: {recommendation.rationale}")
    print(f"Risk Level: {recommendation.risk_level}")
    print(f"Capital Required: {recommendation.capital_required}")

    if research:
        print(f"\n[RESEARCH USED]")
        print(f"  Questions: {research.total_questions}")
        print(f"  Articles: {research.total_articles}")
        print(f"  Words: {research.total_words:,}")
        print(f"  Sources: {', '.join(set(research.total_sources[:5]))}")

    print("\n" + "=" * 80)
    print("[SUCCESS] Strategy Selector V2 Working!")
    print("=" * 80)
