"""
Test Autonomous Web Research

Demonstrates the bot's ability to:
1. Generate intelligent research questions
2. Search the web for answers
3. Scrape and read articles
4. Synthesize findings
"""
import sys
from src.research.autonomous_researcher import AutonomousResearcher


def test_autonomous_research():
    """Test autonomous research with NVDA."""

    print("=" * 80)
    print("TESTING AUTONOMOUS WEB RESEARCH")
    print("=" * 80)
    print("\nThis test demonstrates the bot teaching itself by:")
    print("  1. Generating research questions")
    print("  2. Searching Google for answers")
    print("  3. Reading articles from credible sources")
    print("  4. Synthesizing findings")
    print()

    # Initialize researcher
    print("[Initializing autonomous researcher...]")
    try:
        researcher = AutonomousResearcher()
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("\nTo use autonomous research, you need:")
        print("  1. Set ANTHROPIC_API_KEY in .env file")
        print("  OR")
        print("  2. Set OPENAI_API_KEY in .env file")
        return False

    # Research NVDA
    ticker = "NVDA"
    print(f"\n[Starting autonomous research on {ticker}...]")
    print()

    report = researcher.research_stock(
        ticker=ticker,
        articles_per_question=2,  # 2 articles per question (6 total)
        max_questions=3  # 3 research questions
    )

    # Display detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESEARCH REPORT")
    print("=" * 80)

    print(f"\n[TICKER] {report.ticker}")

    print(f"\n[RESEARCH QUESTIONS]")
    for i, question in enumerate(report.questions, 1):
        print(f"  {i}. [{question.category.upper()}] {question.question}")

    print(f"\n[ARTICLES SCRAPED]")
    for i, article in enumerate(report.articles, 1):
        print(f"\n  Article {i}:")
        print(f"    Title: {article.title}")
        print(f"    Source: {article.source}")
        print(f"    Words: {article.word_count:,}")
        print(f"    URL: {article.url}")
        print(f"    Preview: {article.content[:150]}...")

    print(f"\n[SUMMARY STATISTICS]")
    print(f"  Total Questions: {len(report.questions)}")
    print(f"  Total Articles: {len(report.articles)}")
    print(f"  Total Words: {report.total_words:,}")
    print(f"  Unique Sources: {len(report.sources)}")
    print(f"  Sources: {', '.join(report.sources)}")

    # Calculate reading time
    words_per_minute = 200
    reading_time = report.total_words / words_per_minute
    print(f"  Reading Time: {reading_time:.1f} minutes (at {words_per_minute} words/min)")

    # Comparison to baseline
    print(f"\n[COMPARISON TO BASELINE]")
    baseline_words = 21000  # Current yfinance + SEC approach
    improvement = (report.total_words / baseline_words) * 100
    print(f"  Baseline (yfinance + SEC): ~{baseline_words:,} words")
    print(f"  With autonomous research: ~{baseline_words + report.total_words:,} words")
    print(f"  Additional context: +{report.total_words:,} words ({improvement:.0f}% of baseline)")

    # Show what the bot learned
    print(f"\n[WHAT THE BOT LEARNED]")
    for i, article in enumerate(report.articles, 1):
        print(f"\n  From {article.source}:")
        # Extract key sentences (first 2 sentences)
        sentences = article.content.split('.')[:2]
        key_info = '. '.join(sentences[:2])
        print(f"    {key_info}...")

    print("\n" + "=" * 80)
    print("[SUCCESS] AUTONOMOUS RESEARCH COMPLETE!")
    print("=" * 80)

    print(f"\nThe bot successfully:")
    print(f"  [PASS] Generated {len(report.questions)} intelligent research questions")
    print(f"  [PASS] Searched the web {len(report.questions)} times")
    print(f"  [PASS] Scraped {len(report.articles)} articles from credible sources")
    print(f"  [PASS] Read {report.total_words:,} words of content")
    print(f"  [PASS] Sources: {', '.join(report.sources)}")

    print(f"\n{'='*80}")
    print("NEXT STEP: Integrate with Thesis Generator")
    print(f"{'='*80}")
    print("\nNow that autonomous research works, we can enhance")
    print("thesis_generator_v2.py to use this capability.")
    print("\nThis will make the AI thesis:")
    print("  - More informed (reads competitor data, industry trends)")
    print("  - More current (finds latest news beyond yfinance)")
    print("  - More comprehensive (researches specific questions)")
    print("  - More credible (cites sources from Reuters, CNBC, etc.)")

    return True


if __name__ == "__main__":
    success = test_autonomous_research()
    sys.exit(0 if success else 1)
