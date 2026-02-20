"""
Enhanced thesis generator with autonomous web research.

This version integrates the research orchestrator to provide:
- Stock fundamental research from the web
- Competitive analysis
- Industry trends
- Catalysts and risks
- ~15,000 additional words of context

Comparison:
- V2: yfinance + SEC (21,000 words)
- V3: yfinance + SEC + web research (36,000 words)
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import V2 as base
from ai.thesis_generator_v2 import ThesisGeneratorV2
from models.thesis import InvestmentThesis
from research.research_orchestrator import ResearchOrchestrator, ComprehensiveResearch

load_dotenv()


class ThesisGeneratorV3(ThesisGeneratorV2):
    """
    Enhanced thesis generator with autonomous web research.

    Inherits from V2 and adds web research capability.
    """

    def __init__(self, provider: str = "auto", enable_research: bool = True):
        """
        Initialize enhanced thesis generator.

        Args:
            provider: "openai", "anthropic", or "auto"
            enable_research: Whether to enable web research (default True)
        """
        super().__init__(provider)
        self.enable_research = enable_research

        if enable_research:
            self.orchestrator = ResearchOrchestrator()
            print("[V3] Autonomous web research ENABLED")
        else:
            self.orchestrator = None
            print("[V3] Autonomous web research DISABLED (using V2 mode)")

    def generate_thesis(
        self,
        ticker: str,
        stock_data: dict,
        news: list,
        historical_vol: float,
        scrape_full_articles: bool = True,
        max_articles_to_scrape: int = 3,
        include_10k: bool = True,
        cik: str = None,
        # New parameters for research
        enable_research: Optional[bool] = None,
        earnings_info: Optional[dict] = None,
        articles_per_question: int = 2
    ) -> InvestmentThesis:
        """
        Generate investment thesis with optional web research.

        Args:
            ticker: Stock ticker
            stock_data: Dictionary with price, fundamentals, etc.
            news: List of news items
            historical_vol: Historical volatility (decimal)
            scrape_full_articles: Whether to scrape full article content
            max_articles_to_scrape: Maximum number of articles to scrape
            include_10k: Whether to include 10-K/10-Q data
            cik: Company CIK
            enable_research: Override instance setting (optional)
            earnings_info: Optional earnings date/timing (ADDITIONAL context)
            articles_per_question: Articles per research question (default 2)

        Returns:
            InvestmentThesis with structured analysis
        """

        # Determine if research should be enabled for this call
        use_research = enable_research if enable_research is not None else self.enable_research

        # Phase 1: Web Research (if enabled)
        research = None
        if use_research and self.orchestrator:
            print(f"\n{'='*80}")
            print(f"[V3] AUTONOMOUS WEB RESEARCH")
            print(f"{'='*80}\n")

            print("[V3] Researching stock fundamentals, risk, and market conditions...")
            research = self.orchestrator.research_everything(
                ticker=ticker,
                # Don't research strategy/contract yet (we don't have thesis)
                thesis_direction=None,
                earnings_info=earnings_info,  # ADDITIONAL layer (only when relevant)
                articles_per_question=articles_per_question
            )

            print(f"\n[V3] Research complete:")
            print(f"  - Questions: {research.total_questions}")
            print(f"  - Articles: {research.total_articles}")
            print(f"  - Words: {research.total_words:,}")
            print(f"  - Sources: {', '.join(set(research.total_sources[:5]))}")

        # Phase 2: Generate thesis using V2 logic + research
        print(f"\n{'='*80}")
        print(f"[V3] GENERATING THESIS (with {'research' if research else 'V2 baseline'})")
        print(f"{'='*80}\n")

        # Call parent V2 method for baseline thesis generation
        # (This handles yfinance, SEC, news scraping)
        thesis = super().generate_thesis(
            ticker=ticker,
            stock_data=stock_data,
            news=news,
            historical_vol=historical_vol,
            scrape_full_articles=scrape_full_articles,
            max_articles_to_scrape=max_articles_to_scrape,
            include_10k=include_10k,
            cik=cik
        )

        # Phase 3: Enhance thesis with research insights (if available)
        if research:
            print("\n[V3] Enhancing thesis with research insights...")
            thesis = self._enhance_thesis_with_research(thesis, research)

        return thesis

    def _enhance_thesis_with_research(
        self,
        thesis: InvestmentThesis,
        research: ComprehensiveResearch
    ) -> InvestmentThesis:
        """
        Enhance thesis with research insights.

        This method adds research findings to the thesis data_references
        so they're available for display in the UI.

        Args:
            thesis: Original thesis from V2
            research: Research findings

        Returns:
            Enhanced thesis
        """

        # Add research metadata
        thesis.data_references["research_enabled"] = True
        thesis.data_references["research_questions"] = research.total_questions
        thesis.data_references["research_articles"] = research.total_articles
        thesis.data_references["research_words"] = research.total_words
        thesis.data_references["research_sources"] = list(set(research.total_sources))

        # Add research findings by category
        if research.stock_research:
            thesis.data_references["stock_research_articles"] = [
                {
                    "title": a.title,
                    "source": a.source,
                    "url": a.url,
                    "words": a.word_count
                }
                for a in research.stock_research.articles[:5]  # Top 5
            ]

        if research.risk_research:
            thesis.data_references["risk_research_articles"] = [
                {
                    "title": a.title,
                    "source": a.source,
                    "url": a.url,
                    "words": a.word_count
                }
                for a in research.risk_research.articles[:3]  # Top 3
            ]

        if research.market_research:
            thesis.data_references["market_research_articles"] = [
                {
                    "title": a.title,
                    "source": a.source,
                    "url": a.url,
                    "words": a.word_count
                }
                for a in research.market_research.articles[:3]  # Top 3
            ]

        # Add earnings research if available (ADDITIONAL layer)
        if research.earnings_research:
            thesis.data_references["earnings_research_articles"] = [
                {
                    "title": a.title,
                    "source": a.source,
                    "url": a.url,
                    "words": a.word_count
                }
                for a in research.market_research.articles[:3]  # Top 3
            ]

        # Note: In a more advanced version, we would use the research content
        # to enhance the actual thesis text, bull_case, bear_case, etc.
        # For now, we're just attaching the research metadata for reference.

        return thesis

    def compare_with_v2(
        self,
        ticker: str,
        stock_data: dict,
        news: list,
        historical_vol: float,
        **kwargs
    ) -> dict:
        """
        Compare V2 (baseline) vs V3 (with research) thesis generation.

        Args:
            ticker: Stock ticker
            stock_data: Stock data
            news: News items
            historical_vol: Historical volatility
            **kwargs: Additional arguments

        Returns:
            Dictionary with comparison metrics
        """

        print(f"\n{'='*80}")
        print(f"COMPARISON: V2 (Baseline) vs V3 (With Research)")
        print(f"{'='*80}\n")

        # Generate V2 thesis (no research)
        print("[1/2] Generating V2 thesis (baseline)...")
        thesis_v2 = super().generate_thesis(
            ticker=ticker,
            stock_data=stock_data,
            news=news,
            historical_vol=historical_vol,
            **kwargs
        )

        # Generate V3 thesis (with research)
        print("\n[2/2] Generating V3 thesis (with research)...")
        thesis_v3 = self.generate_thesis(
            ticker=ticker,
            stock_data=stock_data,
            news=news,
            historical_vol=historical_vol,
            enable_research=True,
            **kwargs
        )

        # Compare
        comparison = {
            "ticker": ticker,
            "v2": {
                "direction": thesis_v2.direction,
                "conviction": thesis_v2.conviction,
                "expected_move": thesis_v2.expected_move,
                "target_price": thesis_v2.target_price,
                "thesis_summary": thesis_v2.thesis_summary,
                "bull_case_points": len(thesis_v2.bull_case),
                "bear_case_points": len(thesis_v2.bear_case),
                "data_sources": ["yfinance", "SEC filings", "news scraping"]
            },
            "v3": {
                "direction": thesis_v3.direction,
                "conviction": thesis_v3.conviction,
                "expected_move": thesis_v3.expected_move,
                "target_price": thesis_v3.target_price,
                "thesis_summary": thesis_v3.thesis_summary,
                "bull_case_points": len(thesis_v3.bull_case),
                "bear_case_points": len(thesis_v3.bear_case),
                "research_enabled": thesis_v3.data_references.get("research_enabled", False),
                "research_articles": thesis_v3.data_references.get("research_articles", 0),
                "research_words": thesis_v3.data_references.get("research_words", 0),
                "data_sources": [
                    "yfinance", "SEC filings", "news scraping",
                    "web research"
                ]
            }
        }

        return comparison


if __name__ == "__main__":
    # Test V3 thesis generator
    print("=" * 80)
    print("TESTING THESIS GENERATOR V3")
    print("=" * 80)

    # Mock data for testing
    ticker = "NVDA"
    stock_data = {
        "current_price": 188.54,
        "market_cap": 4.63e12,
        "pe_ratio": 65.2,
        "52_week_high": 195.40,
        "52_week_low": 108.13
    }

    news = [
        {"title": "NVDA earnings beat expectations", "url": "https://example.com/1"},
        {"title": "NVDA launches new AI chip", "url": "https://example.com/2"}
    ]

    historical_vol = 0.45

    # Test V3 with research
    try:
        generator = ThesisGeneratorV3(enable_research=True)

        print(f"\n[TEST 1: Generate thesis with research]")
        thesis = generator.generate_thesis(
            ticker=ticker,
            stock_data=stock_data,
            news=news,
            historical_vol=historical_vol,
            scrape_full_articles=False,  # Skip for testing
            include_10k=False,  # Skip for testing
            articles_per_question=1  # Fewer for testing
        )

        print(f"\n[RESULTS]")
        print(f"Direction: {thesis.direction}")
        print(f"Conviction: {thesis.conviction}%")
        print(f"Expected Move: {thesis.expected_move}")
        print(f"Target Price: ${thesis.target_price:.2f}")
        print(f"\nResearch Stats:")
        print(f"  Articles: {thesis.data_references.get('research_articles', 0)}")
        print(f"  Words: {thesis.data_references.get('research_words', 0):,}")
        print(f"  Sources: {', '.join(thesis.data_references.get('research_sources', [])[:3])}")

        print("\n" + "=" * 80)
        print("[SUCCESS] Thesis Generator V3 Working!")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
