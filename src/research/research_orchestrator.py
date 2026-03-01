"""
Research Orchestrator

Coordinates autonomous research across all five decision phases:
  1. Stock fundamentals   (thesis generation)
  2. Strategy selection   (which structure fits this setup?)
  3. Contract selection   (optimal strikes and expirations)
  4. Risk management      (historical patterns and tail risks)
  5. Market conditions    (IV environment, sector trends)
  6. Earnings patterns    (additional phase — only when earnings ≤ 30 days)

Split into three focused modules:
  research_orchestrator.py  — phase coordination (this file)
  question_generators.py    — hardcoded fallback question lists
  autonomous_engine.py      — LLM-powered question generation and adaptive reading
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

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

from src.research.autonomous_researcher import AutonomousResearcher, ResearchReport, ResearchQuestion
from src.research.web_researcher import Article
from src.research.question_generators import QuestionGeneratorMixin
from src.research.autonomous_engine import AutonomousEngineMixin

load_dotenv()


@dataclass
class ComprehensiveResearch:
    """Complete research output across all decision phases."""
    ticker: str

    stock_research:    Optional[ResearchReport] = None
    strategy_research: Optional[ResearchReport] = None
    contract_research: Optional[ResearchReport] = None
    risk_research:     Optional[ResearchReport] = None
    market_research:   Optional[ResearchReport] = None
    earnings_research: Optional[ResearchReport] = None  # Additional — earnings only

    total_questions: int = 0
    total_articles:  int = 0
    total_words:     int = 0
    total_sources:   List[str] = field(default_factory=list)


class ResearchOrchestrator(AutonomousEngineMixin, QuestionGeneratorMixin):
    """
    Orchestrate research across all bot decision points.

    Uses AutonomousEngineMixin for LLM-powered question generation and
    adaptive reading, and QuestionGeneratorMixin for hardcoded fallbacks.
    """

    def __init__(self, provider: str = "auto", enable_autonomous: bool = True):
        self.researcher = AutonomousResearcher()
        self.enable_autonomous = enable_autonomous
        self.llm_client = None
        self.llm_provider = None

        if enable_autonomous:
            if provider == "auto":
                if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
                    self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    self.llm_provider = "openai"
                elif HAS_ANTHROPIC and os.getenv("ANTHROPIC_API_KEY"):
                    self.llm_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                    self.llm_provider = "anthropic"
                else:
                    print("[WARNING] No LLM API key found. Falling back to hardcoded questions.")
                    self.enable_autonomous = False
            else:
                if provider == "openai" and HAS_OPENAI:
                    self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    self.llm_provider = "openai"
                elif provider == "anthropic" and HAS_ANTHROPIC:
                    self.llm_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                    self.llm_provider = "anthropic"
                else:
                    self.enable_autonomous = False

            if self.enable_autonomous:
                print(f"[ResearchOrchestrator] Autonomous research enabled ({self.llm_provider})")
        else:
            print("[ResearchOrchestrator] Using hardcoded questions (autonomous disabled)")

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------

    def research_everything(
        self,
        ticker: str,
        thesis_direction: Optional[str] = None,
        expected_move_pct: Optional[float] = None,
        timeframe_days: Optional[int] = None,
        earnings_info: Optional[Dict] = None,
        articles_per_question: int = 2
    ) -> ComprehensiveResearch:
        """
        Run all research phases and return consolidated findings.

        Phases 2 and 3 are skipped when thesis context is unavailable.
        Phase 6 (earnings) only runs when earnings are within 30 days.
        """
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE AUTONOMOUS RESEARCH: {ticker}")
        print(f"{'='*80}\n")

        comprehensive = ComprehensiveResearch(ticker=ticker)
        global_seen_urls: set = set()  # Shared across all phases to avoid duplicate scraping

        print("\n[PHASE 1: STOCK FUNDAMENTALS]")
        comprehensive.stock_research = self._research_stock_fundamentals(
            ticker, articles_per_question, global_seen_urls
        )

        if thesis_direction:
            print("\n[PHASE 2: STRATEGY SELECTION]")
            comprehensive.strategy_research = self._research_strategy_selection(
                ticker, thesis_direction, expected_move_pct,
                articles_per_question, global_seen_urls
            )

        if thesis_direction and expected_move_pct:
            print("\n[PHASE 3: CONTRACT SELECTION]")
            comprehensive.contract_research = self._research_contract_selection(
                ticker, thesis_direction, expected_move_pct,
                timeframe_days, articles_per_question
            )

        print("\n[PHASE 4: RISK MANAGEMENT]")
        comprehensive.risk_research = self._research_risk_management(
            ticker, articles_per_question
        )

        print("\n[PHASE 5: MARKET CONDITIONS]")
        comprehensive.market_research = self._research_market_conditions(
            ticker, articles_per_question
        )

        if earnings_info and earnings_info.get("days_until", 999) <= 30:
            print(f"\n[PHASE 6: EARNINGS PATTERNS — {earnings_info['days_until']} days to earnings]")
            comprehensive.earnings_research = self._research_earnings_patterns(
                ticker, earnings_info, articles_per_question
            )

        self._calculate_totals(comprehensive)

        print(f"\n{'='*80}")
        print("RESEARCH COMPLETE")
        print(f"  Questions : {comprehensive.total_questions}")
        print(f"  Articles  : {comprehensive.total_articles}")
        print(f"  Words     : {comprehensive.total_words:,}")
        print(f"  Sources   : {', '.join(set(comprehensive.total_sources))}")
        print(f"{'='*80}")

        return comprehensive

    # -------------------------------------------------------------------------
    # Phase implementations
    # -------------------------------------------------------------------------

    def _research_stock_fundamentals(
        self,
        ticker: str,
        articles_per_question: int,
        global_seen_urls: set = None
    ) -> ResearchReport:
        """Phase 1 — stock fundamentals for thesis generation."""
        # SEC filings are always read first (primary source data)
        sec_questions = [
            ResearchQuestion(
                f"What are the key takeaways from {ticker}'s most recent 10-K annual report?",
                "sec_filing", 1
            ),
            ResearchQuestion(
                f"What are the key financial metrics and risks from {ticker}'s most recent 10-Q quarterly report?",
                "sec_filing", 1
            ),
        ]

        if self.enable_autonomous:
            additional = self._generate_questions_dynamically(
                ticker=ticker,
                research_area="stock_fundamentals",
                context=f"""Generate questions to understand {ticker}'s business, financials, and competitive position.
IMPORTANT: SEC filings (10-K, 10-Q) will be researched separately, so focus on:
- Recent earnings call highlights and management guidance
- Competitive positioning and market share trends
- Growth drivers and strategic initiatives
- Analyst sentiment and price targets""",
                max_questions=3
            )
            questions = sec_questions + additional
        else:
            questions = sec_questions + self._generate_stock_questions(ticker)

        print(f"  {len(questions)} questions (2 SEC filings + {len(questions)-2} supplementary)")
        return self._execute_research_phase(
            ticker, questions, articles_per_question, global_seen_urls
        )

    def _research_strategy_selection(
        self,
        ticker: str,
        direction: str,
        expected_move_pct: Optional[float],
        articles_per_question: int,
        global_seen_urls: set = None
    ) -> ResearchReport:
        """Phase 2 — strategy selection research."""
        if self.enable_autonomous:
            questions = self._generate_questions_dynamically(
                ticker=ticker,
                research_area="strategy_selection",
                context=f"Determine the optimal options strategy for {ticker} with {direction} outlook.",
                max_questions=4
            )
        else:
            questions = self._generate_strategy_questions(ticker, direction, expected_move_pct)

        print(f"  {len(questions)} strategy selection questions")
        return self._execute_research_phase(
            ticker, questions, articles_per_question, global_seen_urls
        )

    def _research_contract_selection(
        self,
        ticker: str,
        direction: str,
        expected_move_pct: float,
        timeframe_days: Optional[int],
        articles_per_question: int
    ) -> ResearchReport:
        """Phase 3 — contract selection research."""
        questions = self._generate_contract_questions(
            ticker, direction, expected_move_pct, timeframe_days
        )
        print(f"  {len(questions)} contract selection questions")
        return self._execute_research_phase(ticker, questions, articles_per_question)

    def _research_risk_management(
        self,
        ticker: str,
        articles_per_question: int
    ) -> ResearchReport:
        """Phase 4 — risk management and historical patterns."""
        questions = self._generate_risk_questions(ticker)
        print(f"  {len(questions)} risk management questions")
        return self._execute_research_phase(ticker, questions, articles_per_question)

    def _research_market_conditions(
        self,
        ticker: str,
        articles_per_question: int
    ) -> ResearchReport:
        """Phase 5 — market conditions and IV environment."""
        questions = self._generate_market_questions(ticker)
        print(f"  {len(questions)} market conditions questions")
        return self._execute_research_phase(ticker, questions, articles_per_question)

    def _research_earnings_patterns(
        self,
        ticker: str,
        earnings_info: Dict,
        articles_per_question: int
    ) -> ResearchReport:
        """Phase 6 — earnings patterns (only when earnings ≤ 30 days)."""
        questions = self._generate_earnings_questions(ticker, earnings_info)
        print(f"  {len(questions)} earnings pattern questions")
        return self._execute_research_phase(ticker, questions, articles_per_question)

    # -------------------------------------------------------------------------
    # Shared execution helper
    # -------------------------------------------------------------------------

    def _execute_research_phase(
        self,
        ticker: str,
        questions: List[ResearchQuestion],
        articles_per_question: int,
        seen_urls: set = None
    ) -> ResearchReport:
        """
        Execute a research phase: route each question to LLM-only or web
        scraping based on content, then aggregate results.
        """
        if seen_urls is None:
            seen_urls = set()

        all_articles = []
        llm_count = web_count = 0

        for i, question in enumerate(questions, 1):
            print(f"\n  Q{i}/{len(questions)}: {question.question}")
            mode = self._categorize_question(question, ticker)
            print(f"    [MODE: {mode.upper()}]")

            if mode == "llm_only":
                article = self._ask_llm_directly(ticker, question)
                all_articles.append(article)
                llm_count += 1

            else:  # web_only or hybrid → fetch real data
                if self.enable_autonomous:
                    articles = self._research_question_until_satisfied(
                        ticker=ticker,
                        question=question,
                        min_articles=2,
                        max_articles=4,
                        seen_urls=seen_urls
                    )
                else:
                    articles = self.researcher.web_researcher.search_and_scrape(
                        query=f"{ticker} {question.question}",
                        max_results=articles_per_question
                    )
                all_articles.extend(articles)
                web_count += len(articles)

        print(f"\n  [Phase complete] LLM-only: {llm_count} | Web: {web_count} | Total: {len(all_articles)}")

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=sum(a.word_count for a in all_articles),
            sources=list(set(a.source for a in all_articles))
        )

    def _calculate_totals(self, comprehensive: ComprehensiveResearch) -> None:
        """Aggregate statistics across all research phases."""
        for report in [
            comprehensive.stock_research,
            comprehensive.strategy_research,
            comprehensive.contract_research,
            comprehensive.risk_research,
            comprehensive.market_research,
            comprehensive.earnings_research,
        ]:
            if report:
                comprehensive.total_questions += len(report.questions)
                comprehensive.total_articles += len(report.articles)
                comprehensive.total_words += report.total_words
                comprehensive.total_sources.extend(report.sources)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING RESEARCH ORCHESTRATOR")
    print("=" * 80)

    orchestrator = ResearchOrchestrator()

    research = orchestrator.research_everything(
        ticker="NVDA",
        articles_per_question=1
    )

    print(f"\n[RESULTS]")
    print(f"  Stock:   {research.stock_research.total_words:,} words, {len(research.stock_research.articles)} articles")
    print(f"  Risk:    {research.risk_research.total_words:,} words, {len(research.risk_research.articles)} articles")
    print(f"  Market:  {research.market_research.total_words:,} words, {len(research.market_research.articles)} articles")
    print(f"  TOTAL:   {research.total_words:,} words from {research.total_articles} articles")
