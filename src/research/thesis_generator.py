"""
Thesis Generator - LLM analyzes research and forms investment thesis.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class InvestmentThesis(BaseModel):
    """Structured investment thesis with directional view."""

    direction: str = Field(
        description="Directional view: BULLISH, BEARISH, or NEUTRAL"
    )
    conviction: int = Field(
        description="Conviction level 0-100 (100 = highest confidence)"
    )
    timeframe: str = Field(
        description="Expected timeframe for thesis to play out (e.g., '30-60 days')"
    )
    expected_move: str = Field(
        description="Expected price movement (e.g., '+8-12%' or '-5-10%')"
    )
    thesis_summary: str = Field(
        description="One-paragraph summary of the thesis"
    )
    bull_case: str = Field(
        description="Key bullish factors supporting upside"
    )
    bear_case: str = Field(
        description="Key bearish factors or risks"
    )
    catalysts: list[str] = Field(
        description="Upcoming catalysts that could move the stock"
    )
    key_risks: list[str] = Field(
        description="Main risks to the thesis"
    )


class ThesisGenerator:
    """Generates investment thesis using LLM analysis of research data."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing OPENAI_API_KEY in .env")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Use full GPT-4 for complex reasoning

    def generate_thesis(
        self,
        ticker: str,
        research_summary: str
    ) -> InvestmentThesis:
        """
        Generate investment thesis from research data.

        Args:
            ticker: Stock symbol
            research_summary: Formatted research summary

        Returns:
            InvestmentThesis with directional view and reasoning
        """

        prompt = f"""You are an expert equity analyst forming an investment thesis.

**Your Task:**
Analyze the research data below and form a clear, actionable investment thesis for {ticker}.

**Research Data:**
{research_summary}

**Instructions:**
1. **Direction**: Is this BULLISH, BEARISH, or NEUTRAL? Be decisive.
2. **Conviction**: How confident are you (0-100)? Consider:
   - Strength of fundamentals
   - Technical momentum
   - News sentiment
   - Analyst consensus
   - Risk/reward profile

3. **Timeframe**: What's your time horizon (e.g., "30-60 days", "2-3 months")?

4. **Expected Move**: What % move do you expect? (e.g., "+10-15%" or "-5-8%")

5. **Thesis**: Write a clear, compelling 1-paragraph thesis explaining your view

6. **Bull/Bear Cases**: List key factors for both sides

7. **Catalysts**: What upcoming events could move the stock?

8. **Risks**: What could go wrong with your thesis?

**Be specific, quantitative, and actionable.** This thesis will be used to select options strategies.

**Example of good output:**
- Direction: BULLISH
- Conviction: 75
- Timeframe: "45-60 days"
- Expected Move: "+12-18%"
- Thesis: "Strong buy based on expanding margins, upcoming product launch, and technical breakout above resistance. Earnings in 3 weeks should beat estimates."
"""

        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a top-tier equity analyst known for accurate, well-reasoned investment theses. You think like a professional trader and consider both fundamentals and technicals."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format=InvestmentThesis,
                temperature=0.7
            )

            thesis = response.choices[0].message.parsed
            return thesis

        except Exception as e:
            print(f"Error generating thesis: {e}")
            # Fallback to neutral thesis
            return InvestmentThesis(
                direction="NEUTRAL",
                conviction=50,
                timeframe="30-45 days",
                expected_move="+/-5%",
                thesis_summary=f"Unable to form strong directional view on {ticker} due to mixed signals.",
                bull_case="Some positive factors present",
                bear_case="Some negative factors present",
                catalysts=[],
                key_risks=["Analysis incomplete"]
            )


if __name__ == "__main__":
    from research_agent import ResearchAgent

    print("Testing Thesis Generator...\n")

    try:
        # Get research
        agent = ResearchAgent()
        research = agent.research_ticker("NVDA")
        summary = agent.format_research_summary(research)

        # Generate thesis
        generator = ThesisGenerator()
        thesis = generator.generate_thesis("NVDA", summary)

        print(f"Direction: {thesis.direction}")
        print(f"Conviction: {thesis.conviction}%")
        print(f"Timeframe: {thesis.timeframe}")
        print(f"Expected Move: {thesis.expected_move}")
        print(f"\nThesis:\n{thesis.thesis_summary}")
        print(f"\nBull Case:\n{thesis.bull_case}")
        print(f"\nBear Case:\n{thesis.bear_case}")
        print(f"\nCatalysts: {', '.join(thesis.catalysts)}")

    except Exception as e:
        print(f"Error: {e}")
