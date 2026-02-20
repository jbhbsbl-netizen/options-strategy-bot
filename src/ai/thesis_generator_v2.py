"""
AI-powered investment thesis generator using GPT-4 or Claude.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try OpenAI first, fall back to Anthropic
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from models.thesis import InvestmentThesis
from data.news_scraper import NewsArticleScraper
from data.sec_parser import SECFilingParser

load_dotenv()


class ThesisGeneratorV2:
    """Generate investment thesis using LLM."""

    def __init__(self, provider: str = "auto"):
        """
        Initialize thesis generator.

        Args:
            provider: "openai", "anthropic", or "auto" (try OpenAI first)
        """
        self.provider = provider

        if provider == "auto":
            if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
                self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            elif HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
                self.provider = "anthropic"
                self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            else:
                raise ValueError("No API keys found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

        elif provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("openai package not installed")
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        elif provider == "anthropic":
            if not HAS_ANTHROPIC:
                raise ImportError("anthropic package not installed")
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate_thesis(
        self,
        ticker: str,
        stock_data: dict,
        news: list,
        historical_vol: float,
        scrape_full_articles: bool = True,
        max_articles_to_scrape: int = 3,
        include_10k: bool = True,
        cik: str = None
    ) -> InvestmentThesis:
        """
        Generate investment thesis from stock data and news.

        Args:
            ticker: Stock ticker
            stock_data: Dictionary with price, fundamentals, etc.
            news: List of news items
            historical_vol: Historical volatility (decimal)
            scrape_full_articles: Whether to scrape full article content (default True)
            max_articles_to_scrape: Maximum number of articles to scrape (default 3)
            include_10k: Whether to include 10-K/10-Q data (default True)
            cik: Company CIK (will look up if not provided)

        Returns:
            InvestmentThesis with structured analysis
        """

        # Optionally scrape full article content
        if scrape_full_articles and news:
            print(f"  Scraping full articles (max {max_articles_to_scrape})...")
            scraper = NewsArticleScraper()
            urls = [item['link'] for item in news[:max_articles_to_scrape] if item.get('link')]

            full_articles = scraper.scrape_multiple_articles(urls, max_articles=max_articles_to_scrape, delay=1.0)

            # Merge full content back into news items
            for i, article in enumerate(full_articles):
                if i < len(news):
                    news[i]['full_content'] = article['content']
                    news[i]['word_count'] = article['word_count']

        # Optionally include 10-K/10-Q data
        sec_data = {}
        if include_10k:
            print(f"  Fetching SEC 10-K data...")
            sec_parser = SECFilingParser()

            # Get CIK if not provided
            if not cik:
                from data.sec_filings import SECFilingsClient
                sec_client = SECFilingsClient()
                cik = sec_client.get_company_cik(ticker)

            if cik:
                try:
                    # Try to get 10-K (annual report)
                    sec_data = sec_parser.get_comprehensive_filing_data(cik, use_10k=True)
                except Exception as e:
                    print(f"  Warning: Could not fetch 10-K: {e}")
                    # Fall back to 10-Q (quarterly)
                    try:
                        sec_data = sec_parser.get_comprehensive_filing_data(cik, use_10k=False)
                    except:
                        print(f"  Warning: Could not fetch 10-Q either")

        # Build research summary
        research_summary = self._build_research_summary(ticker, stock_data, news, historical_vol, sec_data)

        # Build prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(ticker, research_summary)

        # Call LLM
        if self.provider == "openai":
            response = self._call_openai(system_prompt, user_prompt)
        else:
            response = self._call_anthropic(system_prompt, user_prompt)

        # Parse response into Pydantic model
        thesis_data = json.loads(response)
        thesis = InvestmentThesis(**thesis_data)

        return thesis

    def _build_research_summary(self, ticker: str, stock_data: dict, news: list, historical_vol: float, sec_data: dict = None) -> str:
        """Build formatted research summary for LLM."""

        # Format optional fields
        pe_ratio = f"{stock_data['pe_ratio']:.2f}" if stock_data['pe_ratio'] else "N/A"
        forward_pe = f"{stock_data['forward_pe']:.2f}" if stock_data['forward_pe'] else "N/A"
        revenue_growth = f"{stock_data['revenue_growth']*100:.1f}%" if stock_data['revenue_growth'] else "N/A"
        profit_margin = f"{stock_data['profit_margin']*100:.1f}%" if stock_data['profit_margin'] else "N/A"
        target_price = f"${stock_data['target_price']:.2f}" if stock_data['target_price'] else "N/A"

        upside = "N/A"
        if stock_data['target_price']:
            upside = f"{((stock_data['target_price']/stock_data['current_price']-1)*100):+.1f}%"

        week_low = f"${stock_data['52_week_low']:.2f}" if stock_data['52_week_low'] else "N/A"
        week_high = f"${stock_data['52_week_high']:.2f}" if stock_data['52_week_high'] else "N/A"

        summary = f"""# {ticker} Research Summary

## Current Price & Performance
- Current Price: ${stock_data['current_price']:.2f}
- Today's Change: ${stock_data['price_change']:.2f} ({stock_data['price_change_pct']:+.2f}%)
- Previous Close: ${stock_data['previous_close']:.2f}

## Fundamentals
- Market Cap: ${stock_data['market_cap']/1e9:.2f}B
- P/E Ratio: {pe_ratio}
- Forward P/E: {forward_pe}
- Revenue Growth (YoY): {revenue_growth}
- Profit Margin: {profit_margin}

## Analyst Expectations
- Analyst Target Price: {target_price}
- Upside to Target: {upside}

## Volatility & Risk
- 30-Day Historical Volatility: {historical_vol*100:.1f}%
- 52-Week Range: {week_low} - {week_high}

## Recent News Headlines
"""

        for i, item in enumerate(news[:5], 1):
            # Handle potential missing title
            title = item.get('title', 'No title available')
            publisher = item.get('publisher', 'Unknown source')
            pub_time = item.get('publish_time', datetime.now())

            # Format timestamp
            if isinstance(pub_time, datetime):
                time_str = pub_time.strftime('%Y-%m-%d')
            else:
                time_str = 'Recent'

            summary += f"{i}. {title} ({publisher}, {time_str})\n"

            # Include full article content if scraped, otherwise use summary
            if item.get('full_content'):
                # Limit to first 1500 words to avoid token limits
                full_content = item['full_content']
                words = full_content.split()[:1500]
                truncated_content = ' '.join(words)
                summary += f"   Article Content ({item.get('word_count', 0)} words):\n"
                summary += f"   {truncated_content}\n\n"
            elif item.get('summary'):
                summary += f"   Summary: {item['summary']}\n"

        summary += "\n---\n"

        # Add SEC filing data if available
        if sec_data and sec_data.get('sections'):
            sections = sec_data['sections']
            filing_type = sec_data.get('filing_type', '10-K')

            summary += f"\n## SEC {filing_type} Filing Analysis\n\n"

            # Add Business section
            if sections.get('business'):
                business_text = sections['business'][:2000]  # Limit to 2000 words
                summary += f"### Business Overview\n{business_text}\n\n"

            # Add Risk Factors (very important for investment thesis)
            if sections.get('risk_factors'):
                risk_text = sections['risk_factors'][:3000]  # Limit to 3000 words
                summary += f"### Risk Factors\n{risk_text}\n\n"

            # Add MD&A (Management's perspective)
            if sections.get('mda'):
                mda_text = sections['mda'][:4000]  # Limit to 4000 words
                summary += f"### Management's Discussion & Analysis\n{mda_text}\n\n"

            # Add Market Risk
            if sections.get('market_risk'):
                market_risk_text = sections['market_risk'][:1000]  # Limit to 1000 words
                summary += f"### Market Risk Disclosures\n{market_risk_text}\n\n"

            summary += "---\n"

        return summary

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM."""

        return """You are a professional equity analyst specializing in options trading. Your job is to analyze stocks and form investment theses based on quantitative data.

CRITICAL REQUIREMENTS:
1. ALWAYS cite specific numbers from the research data
2. Be precise with percentages, dollar amounts, and growth rates
3. Your thesis must be defensible with the data provided
4. Consider both bullish AND bearish factors (be balanced)
5. Expected moves should be realistic (not extreme like "500% in 1 week")
6. Timeframes should align with options expirations (7-90 days typical)
7. **ONLY MAKE PREDICTIONS WITH HIGH CONVICTION** - If the data doesn't support a clear directional view, say NEUTRAL
8. **BE CONSERVATIVE** - Don't force large expected moves if the evidence is weak
9. **IT'S OK TO SAY "NO OPINION"** - If conviction is below 50%, default to NEUTRAL and recommend waiting for better setup

OUTPUT FORMAT:
You must return a valid JSON object matching this exact schema:

{
  "direction": "BULLISH" | "BEARISH" | "NEUTRAL" | "UNPREDICTABLE",
  "conviction": <0-100>,
  "expected_move": "<+/-X% in Y days>",
  "expected_move_pct": <float>,
  "target_price": <float>,
  "timeframe": "<X-Y days>",
  "timeframe_days": <int>,
  "thesis_summary": "<2-3 sentences with specific data>",
  "bull_case": ["<specific reason with data>", "..."],
  "bear_case": ["<specific risk with data>", "..."],
  "catalysts": ["<upcoming event>", "..."],
  "key_risks": ["<what could go wrong>", "..."],
  "data_references": {
    "current_price": "<value>",
    "pe_ratio": "<value>",
    "revenue_growth": "<value>",
    ...
  }
}

DIRECTION OPTIONS EXPLAINED:
- **BULLISH**: You predict the stock will RISE (cite specific reasons why)
- **BEARISH**: You predict the stock will FALL (cite specific reasons why)
- **NEUTRAL**: You predict the stock will stay RANGE-BOUND (no major moves up or down)
  - This IS a valid prediction and IS tradeable (Iron Condor, Butterfly, etc.)
  - Example: "Stock will trade between $180-$200 (±5%) over next 30 days"
- **UNPREDICTABLE**: You genuinely cannot form a prediction given available data
  - Use this when: binary events pending, insufficient data, unprecedented situation
  - Recommendation will be: "Do not trade - wait for clarity"
  - BE HONEST: If you don't know, say so. Don't force a prediction.
  - Still provide rationale explaining WHY it's unpredictable

EXAMPLES OF GOOD ANALYSIS:

Bull Case:
- "Revenue grew 50% YoY to $18.1B in Q3 2025, beating estimates by 12%"
- "Data center revenue up 112% driven by AI chip demand, now 80% of total revenue"
- "Forward P/E of 32x vs sector average of 25x, but justified by 40%+ growth rate"

Bear Case:
- "Valuation: Current P/E of 65x vs 5-year average of 45x, implying 44% premium"
- "Competitor risk: AMD gaining 3% market share in enterprise GPU segment"
- "Export restrictions to China could impact 20% of revenue ($3.6B annually)"

EXAMPLES BY DIRECTION:

**NEUTRAL (Range-bound prediction - this IS tradeable):**
- "Bull and bear factors roughly balanced - expect sideways movement"
- "Stock will likely trade between $180-$200 over next 30 days"
- "No major catalysts until earnings in 60 days, range-bound expected"
- "Valuation fair, no clear edge, predict ±5% range"

**UNPREDICTABLE (Genuinely cannot predict - do not trade):**
- "FDA approval decision in 7 days - binary outcome, cannot model"
- "Major lawsuit verdict pending - outcome determines +40% or -30%"
- "Unprecedented regulatory situation with no historical precedent"
- "Data is contradictory and insufficient to form coherent thesis"

CONVICTION GUIDELINES:
- 70-100%: Strong evidence for directional move (BULLISH/BEARISH)
- 50-69%: Moderate evidence, supportable prediction
- Below 50%: Weak evidence → Consider NEUTRAL or UNPREDICTABLE
- For UNPREDICTABLE: Set conviction to 0 or omit

EXPECTED MOVE GUIDELINES:
- Be conservative: If unsure, estimate SMALLER moves
- NEUTRAL: Small ranges (±3-8% for 30-60 days)
- BULLISH/BEARISH: Typical 8-20% for 30-60 days
- Only predict >20% moves with very strong catalysts
- For UNPREDICTABLE: State range of possible outcomes

CRITICAL: Be honest about what the data supports. If you genuinely don't know, say UNPREDICTABLE. Don't force predictions to avoid saying "I don't know"."""

    def _build_user_prompt(self, ticker: str, research_summary: str) -> str:
        """Build user prompt with research data."""

        return f"""Analyze {ticker} and generate an investment thesis.

{research_summary}

Based on this data:
1. Form a directional view (BULLISH/BEARISH/NEUTRAL) with conviction level
2. Estimate expected price move and timeframe (be realistic, 30-60 days typical)
3. List 3-5 specific bullish factors citing exact data
4. List 3-5 specific bearish risks citing exact data
5. Identify upcoming catalysts (earnings dates, product launches, conferences)
6. Identify key risks that could invalidate the thesis

**IMPORTANT - FOUR POSSIBLE OUTCOMES:**

1. **BULLISH**: You predict stock will RISE (explain why with data)
2. **BEARISH**: You predict stock will FALL (explain why with data)
3. **NEUTRAL**: You predict stock will stay RANGE-BOUND (explain expected range)
   - Example: "Stock will trade between $180-$200 (±5%) over next 30 days"
   - This IS a valid, tradeable prediction (Iron Condor, etc.)
4. **UNPREDICTABLE**: You genuinely cannot predict (explain what's uncertain)
   - Example: "FDA decision pending - binary outcome, cannot model"
   - Recommendation: Do not trade, wait for clarity

**HONESTY OVER EVERYTHING:**
- Don't force BULLISH/BEARISH if the data doesn't support it
- Don't force NEUTRAL if the situation is genuinely unpredictable
- If you don't know, say UNPREDICTABLE and explain why
- Be conservative with expected moves - smaller is better if unsure
- Your job is to be ACCURATE, not to always have an opinion

Return a valid JSON object matching the schema provided in the system prompt.

Remember:
- Use SPECIFIC numbers from the research data
- Be balanced (acknowledge both sides)
- Expected moves should be realistic and defensible
- Explain your reasoning clearly, even for NEUTRAL or UNPREDICTABLE
- Cite sources of data in your reasoning"""

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API."""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4o" for better quality
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower temperature for more consistent analysis
        )

        return response.choices[0].message.content

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        # Extract JSON from response
        content = response.content[0].text

        # If response is wrapped in markdown code blocks, extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return content


if __name__ == "__main__":
    # Test the thesis generator
    import sys
    from pathlib import Path

    # Add src to path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from data.yfinance_client import YFinanceClient

    print("\n" + "="*70)
    print("TESTING AI THESIS GENERATOR")
    print("="*70 + "\n")

    ticker = "NVDA"

    # Fetch data
    print(f"Fetching data for {ticker}...")
    client = YFinanceClient()
    stock_data = client.get_stock_data(ticker)
    news = client.get_news(ticker, max_items=5)
    hist_vol = client.get_historical_volatility(ticker, days=30)

    print(f"  Current Price: ${stock_data['current_price']:.2f}")
    if stock_data['target_price']:
        print(f"  Target Price: ${stock_data['target_price']:.2f}")
    else:
        print(f"  Target Price: N/A")
    print(f"  Historical Vol: {hist_vol*100:.1f}%")
    print(f"  News Items: {len(news)}")

    # Generate thesis
    print(f"\nGenerating investment thesis with 10-K data...")
    generator = ThesisGeneratorV2(provider="auto")

    # CIK for NVDA
    cik = "0001045810"

    thesis = generator.generate_thesis(
        ticker,
        stock_data,
        news,
        hist_vol,
        scrape_full_articles=True,
        include_10k=True,
        cik=cik
    )

    print(f"\n{'='*70}")
    print("INVESTMENT THESIS")
    print(f"{'='*70}\n")

    print(f"Direction: {thesis.direction} ({thesis.conviction}% conviction)")
    print(f"Expected Move: {thesis.expected_move}")
    print(f"Target Price: ${thesis.target_price:.2f}")
    print(f"Timeframe: {thesis.timeframe}")

    print(f"\nThesis Summary:")
    print(f"  {thesis.thesis_summary}")

    print(f"\nBull Case:")
    for i, point in enumerate(thesis.bull_case, 1):
        print(f"  {i}. {point}")

    print(f"\nBear Case:")
    for i, point in enumerate(thesis.bear_case, 1):
        print(f"  {i}. {point}")

    if thesis.catalysts:
        print(f"\nCatalysts:")
        for catalyst in thesis.catalysts:
            print(f"  - {catalyst}")

    if thesis.key_risks:
        print(f"\nKey Risks:")
        for risk in thesis.key_risks:
            print(f"  - {risk}")

    print(f"\n{'='*70}")
    print("[SUCCESS] AI Thesis Generator Working!")
    print(f"{'='*70}\n")
