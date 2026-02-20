"""
LLM-powered strategy analyzer for covered calls.
Evaluates strikes and explains reasoning.
"""
import os
from typing import Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class CoveredCallRecommendation(BaseModel):
    """Structured output for covered call analysis."""
    recommended_strike: float = Field(description="The recommended strike price")
    confidence: int = Field(description="Confidence level 1-100")
    reasoning: str = Field(description="Why this strike was chosen")
    risk_assessment: str = Field(description="Key risks to be aware of")
    alternatives: List[Dict[str, str]] = Field(
        description="Alternative strikes with brief explanations"
    )
    market_context: str = Field(description="Current market conditions context")


class StrategyAnalyzer:
    """Analyzes covered call opportunities using LLM reasoning."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing LLM API key. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env"
            )

        # For now, we'll use OpenAI. Could add Anthropic support later
        if os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4o-mini"  # Fast and cheap
        else:
            raise ValueError("Only OpenAI supported for now. Set OPENAI_API_KEY")

    def analyze_covered_call_opportunities(
        self,
        ticker: str,
        stock_price: float,
        options_df: pd.DataFrame,
        volatility: float,
        user_preference: str = "balanced"
    ) -> CoveredCallRecommendation:
        """
        Analyze covered call opportunities and recommend best strike.

        Args:
            ticker: Stock symbol
            stock_price: Current stock price
            options_df: DataFrame with options chain and Greeks
            volatility: Historical volatility
            user_preference: "conservative", "balanced", or "aggressive"

        Returns:
            Structured recommendation with reasoning
        """
        # Filter to reasonable strikes (within 20% of current price)
        df = options_df[
            (options_df['strike'] >= stock_price * 0.8) &
            (options_df['strike'] <= stock_price * 1.2)
        ].copy()

        # Build context for LLM
        options_summary = self._build_options_summary(df, stock_price)

        prompt = f"""You are an expert options trader analyzing covered call opportunities.

**Current Situation:**
- Ticker: {ticker}
- Stock Price: ${stock_price:.2f}
- 30-Day Historical Volatility: {volatility*100:.1f}%
- User Risk Preference: {user_preference}

**Available Covered Call Options:**
{options_summary}

**Your Task:**
Analyze these options and recommend the BEST strike for a covered call strategy.

**Consider:**
1. **Premium Income**: How much cash received upfront
2. **Delta/Probability**: Likelihood of being called away (~30 delta is ideal)
3. **Downside Protection**: Premium as cushion against price drops
4. **Upside Potential**: Room for stock to grow before capping gains
5. **Risk Preference**:
   - Conservative = Lower strikes, more protection, less premium
   - Balanced = ~30 delta, good premium/risk tradeoff
   - Aggressive = Higher strikes, more premium, more risk

**Provide:**
- Your recommended strike with clear reasoning
- Risk assessment (what could go wrong)
- 2-3 alternative strikes with brief explanations
- Market context (is volatility high/low, what does that mean)

Be specific, practical, and educational. Explain WHY, not just WHAT.
"""

        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert options trader who explains strategies clearly and educates while recommending."},
                    {"role": "user", "content": prompt}
                ],
                response_format=CoveredCallRecommendation,
                temperature=0.7
            )

            recommendation = response.choices[0].message.parsed
            return recommendation

        except Exception as e:
            # Fallback to simple heuristic if LLM fails
            print(f"LLM analysis failed: {e}, falling back to heuristic")
            return self._fallback_analysis(df, stock_price, volatility)

    def _build_options_summary(self, df: pd.DataFrame, stock_price: float) -> str:
        """Build a concise summary of options for LLM."""
        lines = []
        lines.append("Strike | Days | Premium | Delta | Theta | Return if Called | Downside Protection")
        lines.append("-" * 80)

        for _, row in df.head(10).iterrows():  # Top 10 most relevant
            premium = row['price']
            delta = row['delta']
            theta = row['theta']
            days = row['days_to_exp']

            # Calculate metrics
            profit_if_called = (row['strike'] - stock_price) * 100 + premium * 100
            return_pct = profit_if_called / (stock_price * 100) * 100
            protection_pct = (premium / stock_price) * 100

            lines.append(
                f"${row['strike']:.2f} | {days}d | ${premium:.2f} | "
                f"{delta:.3f} | {theta:.2f} | {return_pct:.1f}% | {protection_pct:.1f}%"
            )

        return "\n".join(lines)

    def _fallback_analysis(
        self,
        df: pd.DataFrame,
        stock_price: float,
        volatility: float
    ) -> CoveredCallRecommendation:
        """Simple heuristic-based analysis if LLM fails."""
        # Find option closest to 0.30 delta (30-delta rule)
        df['delta_diff'] = abs(df['delta'] - 0.30)
        best = df.loc[df['delta_diff'].idxmin()]

        return CoveredCallRecommendation(
            recommended_strike=float(best['strike']),
            confidence=70,
            reasoning=f"Selected ${best['strike']:.2f} strike using the 30-delta rule. "
                     f"This strike has a delta of {best['delta']:.3f}, meaning ~{best['delta']*100:.0f}% "
                     f"probability of being in-the-money at expiration. Provides ${best['price']:.2f} "
                     f"premium while allowing upside to ${best['strike']:.2f}.",
            risk_assessment="Standard covered call risks: capped upside if stock rallies significantly, "
                          "losses if stock drops more than the premium received.",
            alternatives=[
                {
                    "strike": f"${df.iloc[i]['strike']:.2f}",
                    "explanation": f"Delta {df.iloc[i]['delta']:.2f}, ${df.iloc[i]['price']:.2f} premium"
                }
                for i in range(min(2, len(df))) if i != df['delta_diff'].idxmin()
            ],
            market_context=f"Historical volatility is {volatility*100:.1f}%. "
                         f"{'High volatility = higher premiums but more uncertainty.' if volatility > 0.30 else 'Moderate volatility environment.'}"
        )


if __name__ == "__main__":
    # Test the analyzer
    print("Testing Strategy Analyzer...\n")

    # Mock data for testing
    test_df = pd.DataFrame({
        'strike': [175, 180, 185, 190, 195],
        'days_to_exp': [8, 8, 8, 8, 8],
        'price': [7.50, 4.20, 2.10, 0.85, 0.30],
        'delta': [0.65, 0.45, 0.28, 0.12, 0.05],
        'theta': [-0.15, -0.12, -0.08, -0.05, -0.02],
        'gamma': [0.01] * 5,
        'vega': [0.20] * 5
    })

    try:
        analyzer = StrategyAnalyzer()
        result = analyzer.analyze_covered_call_opportunities(
            ticker="AAPL",
            stock_price=182.50,
            options_df=test_df,
            volatility=0.25,
            user_preference="balanced"
        )

        print(f"Recommended Strike: ${result.recommended_strike:.2f}")
        print(f"Confidence: {result.confidence}%")
        print(f"\nReasoning:\n{result.reasoning}")
        print(f"\nRisk Assessment:\n{result.risk_assessment}")
        print(f"\nMarket Context:\n{result.market_context}")
        print(f"\nAlternatives:")
        for alt in result.alternatives:
            print(f"  - {alt['strike']}: {alt['explanation']}")

    except ValueError as e:
        print(f"Error: {e}")
        print("Set OPENAI_API_KEY in .env to test")
