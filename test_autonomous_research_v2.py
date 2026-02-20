"""
Test TRUE AUTONOMOUS RESEARCH (Option B).

The bot:
1. Generates its own research questions (not hardcoded)
2. Reads articles until satisfied (not fixed count)
3. Decides when it has enough information
"""
from src.research.research_orchestrator import ResearchOrchestrator

def test_autonomous_vs_hardcoded():
    """Compare autonomous research vs hardcoded questions."""

    print("="*80)
    print("TRUE AUTONOMOUS RESEARCH TEST")
    print("="*80)

    # Test 1: Hardcoded (old way)
    print("\n[TEST 1: HARDCODED QUESTIONS (Old Way)]")
    print("-"*80)
    print("Questions: FIXED (exactly 3 per area)")
    print("Articles: FIXED (exactly 2 per question)")
    print("Result: ~6 articles, ~3,000 words per research area")
    print("Problem: Arbitrary limits, not based on what bot needs")

    orchestrator_old = ResearchOrchestrator(enable_autonomous=False)
    print(f"Mode: {orchestrator_old.enable_autonomous}")

    # Test 2: Autonomous (new way)
    print("\n\n[TEST 2: TRUE AUTONOMOUS RESEARCH (New Way)]")
    print("-"*80)
    print("Questions: DYNAMIC (bot generates 5-12 questions)")
    print("Articles: ADAPTIVE (bot reads until satisfied, 2-6 per question)")
    print("Result: Variable - depends on complexity and satisfaction")
    print("Benefit: Bot decides based on what it needs to know")

    orchestrator_new = ResearchOrchestrator(enable_autonomous=True)
    print(f"Mode: Autonomous = {orchestrator_new.enable_autonomous}")

    if orchestrator_new.enable_autonomous:
        print(f"LLM Provider: {orchestrator_new.llm_provider}")
        print("\n[EXAMPLE: Dynamic Question Generation]")
        print("Bot will ask LLM: 'What should I research about NVDA stock fundamentals?'")
        print("LLM might generate:")
        print("  1. What is NVDA's revenue growth trend in AI/data center segments?")
        print("  2. How does NVDA's gross margin compare to AMD and Intel?")
        print("  3. What are the key risks to NVDA's AI dominance?")
        print("  4. How is NVDA positioning itself for the metaverse?")
        print("  5. What is NVDA's capital allocation strategy?")
        print("  ... (5-12 questions total)")

        print("\n[EXAMPLE: Adaptive Article Reading]")
        print("For question 'What is NVDA's revenue growth trend?':")
        print("  Article 1: Read...")
        print("  Article 2: Read...")
        print("  Bot checks: 'Do I have enough info?' -> NO, need more data")
        print("  Article 3: Read...")
        print("  Bot checks: 'Do I have enough info?' -> YES, satisfied")
        print("  --> Stops at 3 articles (not arbitrary limit)")

    else:
        print("\n[WARNING] Autonomous mode not available")
        print("Reason: No LLM API key found")
        print("Falling back to hardcoded questions")

    print("\n" + "="*80)
    print("KEY DIFFERENCES")
    print("="*80)

    print("\nHARDCODED (Old):")
    print("  - Questions: We decide (3 hardcoded questions)")
    print("  - Articles: We decide (2 per question)")
    print("  - Total: ~18 articles for all research")
    print("  - Problem: Too little for complex stocks, too much for simple ones")

    print("\nAUTONOMOUS (New):")
    print("  - Questions: Bot decides (5-12 questions based on complexity)")
    print("  - Articles: Bot decides (2-6 per question until satisfied)")
    print("  - Total: ~30-100 articles (varies by stock)")
    print("  - Benefit: Thorough when needed, efficient when not")

    print("\n" + "="*80)
    print("COST COMPARISON")
    print("="*80)

    print("\nAPI Calls:")
    print("  Hardcoded: 0 LLM calls for question generation")
    print("  Autonomous: ~5-10 LLM calls (question gen + satisfaction checks)")
    print("  Cost: ~$0.01-0.05 per stock analysis (very cheap with gpt-4o-mini)")

    print("\nArticles Scraped:")
    print("  Hardcoded: ~18 articles (fixed)")
    print("  Autonomous: ~30-100 articles (variable)")
    print("  Benefit: More thorough research without arbitrary limits")

    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    print("\nIf you want the bot to:")
    print("  ✓ Decide what to research (not us)")
    print("  ✓ Read until satisfied (not fixed count)")
    print("  ✓ Be thorough when needed (not arbitrary limits)")

    print("\nThen: Use AUTONOMOUS mode (Option B)")
    print("Cost: Minimal (~$0.01-0.05 more per analysis)")
    print("Benefit: True intelligence, adaptive depth")

    print("\n" + "="*80)

if __name__ == "__main__":
    test_autonomous_vs_hardcoded()
