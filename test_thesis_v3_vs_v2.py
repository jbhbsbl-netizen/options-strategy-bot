"""
Test Thesis Generator V3 vs V2

Compares thesis generation with and without autonomous web research.

V2 (Baseline):
- yfinance data
- SEC filings
- News scraping
- ~21,000 words

V3 (Enhanced):
- Everything from V2
- + Autonomous web research
- + Stock fundamentals research
- + Risk management research
- + Market conditions research
- ~36,000 words
"""
import sys
from src.data.yfinance_client import YFinanceClient
from src.ai.thesis_generator_v2 import ThesisGeneratorV2
from src.ai.thesis_generator_v3 import ThesisGeneratorV3


def test_v2_baseline(ticker: str):
    """Test V2 baseline thesis generation."""
    print(f"\n{'='*80}")
    print(f"TESTING V2 (BASELINE): {ticker}")
    print(f"{'='*80}\n")

    # Fetch stock data
    client = YFinanceClient()
    print(f"[1/3] Fetching stock data...")
    stock_data = client.get_stock_data(ticker)

    print(f"[2/3] Fetching news...")
    news = client.get_news(ticker, limit=5)

    # Generate thesis (V2 baseline)
    print(f"[3/3] Generating thesis (V2 baseline)...")
    generator = ThesisGeneratorV2()

    thesis = generator.generate_thesis(
        ticker=ticker,
        stock_data=stock_data,
        news=news,
        historical_vol=0.45,
        scrape_full_articles=True,
        max_articles_to_scrape=2,  # Fewer for testing
        include_10k=False  # Skip SEC for faster testing
    )

    return thesis


def test_v3_enhanced(ticker: str):
    """Test V3 enhanced thesis generation with research."""
    print(f"\n{'='*80}")
    print(f"TESTING V3 (WITH RESEARCH): {ticker}")
    print(f"{'='*80}\n")

    # Fetch stock data
    client = YFinanceClient()
    print(f"[1/3] Fetching stock data...")
    stock_data = client.get_stock_data(ticker)

    print(f"[2/3] Fetching news...")
    news = client.get_news(ticker, limit=5)

    # Generate thesis (V3 with research)
    print(f"[3/3] Generating thesis (V3 with research)...")
    generator = ThesisGeneratorV3(enable_research=True)

    thesis = generator.generate_thesis(
        ticker=ticker,
        stock_data=stock_data,
        news=news,
        historical_vol=0.45,
        scrape_full_articles=True,
        max_articles_to_scrape=2,
        include_10k=False,
        articles_per_question=2  # 2 articles per research question
    )

    return thesis


def compare_results(ticker: str, thesis_v2, thesis_v3):
    """Compare V2 vs V3 results."""
    print(f"\n{'='*80}")
    print(f"COMPARISON: V2 vs V3")
    print(f"{'='*80}\n")

    print(f"[TICKER] {ticker}\n")

    # Direction & Conviction
    print(f"[DIRECTION]")
    print(f"  V2: {thesis_v2.direction} ({thesis_v2.conviction}% conviction)")
    print(f"  V3: {thesis_v3.direction} ({thesis_v3.conviction}% conviction)")

    if thesis_v2.direction == thesis_v3.direction:
        print(f"  Status: SAME direction")
    else:
        print(f"  Status: DIFFERENT direction (research changed thesis!)")

    # Expected Move
    print(f"\n[EXPECTED MOVE]")
    print(f"  V2: {thesis_v2.expected_move} (target: ${thesis_v2.target_price:.2f})")
    print(f"  V3: {thesis_v3.expected_move} (target: ${thesis_v3.target_price:.2f})")

    # Thesis Quality
    print(f"\n[THESIS QUALITY]")
    print(f"  V2 Bull Case: {len(thesis_v2.bull_case)} points")
    print(f"  V3 Bull Case: {len(thesis_v3.bull_case)} points")
    print(f"  V2 Bear Case: {len(thesis_v2.bear_case)} points")
    print(f"  V3 Bear Case: {len(thesis_v3.bear_case)} points")

    # Data Sources
    print(f"\n[DATA SOURCES]")
    print(f"  V2: yfinance, SEC, news scraping (~21,000 words)")

    if thesis_v3.data_references.get("research_enabled"):
        research_articles = thesis_v3.data_references.get("research_articles", 0)
        research_words = thesis_v3.data_references.get("research_words", 0)
        research_sources = thesis_v3.data_references.get("research_sources", [])

        print(f"  V3: yfinance, SEC, news scraping + web research")
        print(f"      Research: {research_articles} articles, {research_words:,} words")
        print(f"      Sources: {', '.join(research_sources[:5])}")
        print(f"      Total: ~{21000 + research_words:,} words")
    else:
        print(f"  V3: Research was not enabled")

    # Research Citations
    if thesis_v3.data_references.get("stock_research_articles"):
        print(f"\n[RESEARCH CITATIONS - Stock Fundamentals]")
        for i, article in enumerate(thesis_v3.data_references["stock_research_articles"][:3], 1):
            print(f"  {i}. {article['title']}")
            print(f"     Source: {article['source']} ({article['words']} words)")

    if thesis_v3.data_references.get("risk_research_articles"):
        print(f"\n[RESEARCH CITATIONS - Risk Management]")
        for i, article in enumerate(thesis_v3.data_references["risk_research_articles"][:3], 1):
            print(f"  {i}. {article['title']}")
            print(f"     Source: {article['source']} ({article['words']} words)")

    # Thesis Summaries
    print(f"\n[THESIS SUMMARY - V2]")
    print(f"{thesis_v2.thesis_summary[:300]}...")

    print(f"\n[THESIS SUMMARY - V3]")
    print(f"{thesis_v3.thesis_summary[:300]}...")


def main():
    """Run comparison test."""
    print("=" * 80)
    print("THESIS GENERATOR V2 vs V3 COMPARISON TEST")
    print("=" * 80)

    ticker = "NVDA"

    try:
        # Test V2
        thesis_v2 = test_v2_baseline(ticker)

        # Test V3
        thesis_v3 = test_v3_enhanced(ticker)

        # Compare
        compare_results(ticker, thesis_v2, thesis_v3)

        print(f"\n{'='*80}")
        print("[SUCCESS] Comparison Complete!")
        print(f"{'='*80}")

        print(f"\n[KEY FINDINGS]")
        print(f"1. V2 uses ~21,000 words of baseline context")
        if thesis_v3.data_references.get("research_enabled"):
            research_words = thesis_v3.data_references.get("research_words", 0)
            total_words = 21000 + research_words
            improvement = (research_words / 21000) * 100
            print(f"2. V3 uses ~{total_words:,} words (+{improvement:.0f}% more context)")
            print(f"3. V3 includes web research from credible sources")
            print(f"4. V3 researches stock fundamentals, risk, and market conditions")

            research_sources = thesis_v3.data_references.get("research_sources", [])
            if research_sources:
                print(f"5. V3 sources: {', '.join(research_sources[:5])}")
        else:
            print(f"2. V3 research was disabled (set enable_research=True)")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
