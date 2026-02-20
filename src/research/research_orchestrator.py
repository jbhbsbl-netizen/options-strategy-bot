"""
Research Orchestrator - Coordinates research across all bot decisions.

This module ensures the bot researches EVERY major decision:
1. Stock fundamentals (for thesis generation)
2. Strategy selection (which strategy is optimal?)
3. Contract selection (optimal strikes/expirations)
4. Risk management (historical patterns)
5. Market conditions (IV environment, sector trends)

V2: TRUE AUTONOMOUS RESEARCH
- Bot generates its own research questions (not hardcoded)
- Bot reads until satisfied (not fixed article count)
- Bot decides when it has enough information
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# LLM imports
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

load_dotenv()


@dataclass
class ComprehensiveResearch:
    """Complete research across all decision points."""
    ticker: str

    # Stock fundamentals research
    stock_research: Optional[ResearchReport] = None

    # Strategy selection research
    strategy_research: Optional[ResearchReport] = None

    # Contract selection research
    contract_research: Optional[ResearchReport] = None

    # Risk management research
    risk_research: Optional[ResearchReport] = None

    # Market conditions research
    market_research: Optional[ResearchReport] = None

    # Earnings patterns research (ADDITIONAL - only when relevant)
    earnings_research: Optional[ResearchReport] = None

    # Summary statistics
    total_questions: int = 0
    total_articles: int = 0
    total_words: int = 0
    total_sources: List[str] = field(default_factory=list)


class ResearchOrchestrator:
    """
    Orchestrate research across all bot decision points.

    V2: TRUE AUTONOMOUS RESEARCH
    - Generates questions dynamically using LLM
    - Reads articles until satisfied
    - No hardcoded limits
    """

    def __init__(self, provider: str = "auto", enable_autonomous: bool = True):
        """
        Initialize research orchestrator.

        Args:
            provider: "openai", "anthropic", or "auto"
            enable_autonomous: True = bot decides everything, False = use hardcoded questions
        """
        self.researcher = AutonomousResearcher()
        self.enable_autonomous = enable_autonomous

        # Initialize LLM for autonomous question generation
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
                    self.llm_client = None
            else:
                # Use specified provider
                if provider == "openai" and HAS_OPENAI:
                    self.llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    self.llm_provider = "openai"
                elif provider == "anthropic" and HAS_ANTHROPIC:
                    self.llm_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                    self.llm_provider = "anthropic"
                else:
                    self.enable_autonomous = False
                    self.llm_client = None

            if self.enable_autonomous:
                print(f"[ResearchOrchestrator] TRUE AUTONOMOUS RESEARCH enabled ({self.llm_provider})")
        else:
            self.llm_client = None
            print("[ResearchOrchestrator] Using hardcoded questions (autonomous disabled)")

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
        Research everything the bot needs to make informed decisions.

        Args:
            ticker: Stock ticker
            thesis_direction: Optional - if known, enables targeted strategy research
            expected_move_pct: Optional - if known, enables targeted contract research
            timeframe_days: Optional - if known, enables targeted expiration research
            earnings_info: Optional - if earnings within 30 days, enables earnings research
            articles_per_question: Articles to scrape per question

        Returns:
            ComprehensiveResearch with all findings
        """
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE AUTONOMOUS RESEARCH: {ticker}")
        print(f"{'='*80}\n")

        comprehensive = ComprehensiveResearch(ticker=ticker)

        # GLOBAL URL DEDUPLICATION: Track ALL URLs across ALL research areas
        global_seen_urls = set()

        # Phase 1: Stock Fundamentals (for thesis generation)
        print("\n[PHASE 1: STOCK FUNDAMENTALS RESEARCH]")
        comprehensive.stock_research = self._research_stock_fundamentals(
            ticker, articles_per_question, global_seen_urls
        )

        # Phase 2: Strategy Selection (if thesis is known)
        if thesis_direction:
            print("\n[PHASE 2: STRATEGY SELECTION RESEARCH]")
            comprehensive.strategy_research = self._research_strategy_selection(
                ticker, thesis_direction, expected_move_pct, articles_per_question, global_seen_urls
            )

        # Phase 3: Contract Selection (if strategy direction is known)
        if thesis_direction and expected_move_pct:
            print("\n[PHASE 3: CONTRACT SELECTION RESEARCH]")
            comprehensive.contract_research = self._research_contract_selection(
                ticker, thesis_direction, expected_move_pct, timeframe_days, articles_per_question
            )

        # Phase 4: Risk Management
        print("\n[PHASE 4: RISK MANAGEMENT RESEARCH]")
        comprehensive.risk_research = self._research_risk_management(
            ticker, articles_per_question
        )

        # Phase 5: Market Conditions
        print("\n[PHASE 5: MARKET CONDITIONS RESEARCH]")
        comprehensive.market_research = self._research_market_conditions(
            ticker, articles_per_question
        )

        # Phase 6: Earnings Patterns (ADDITIONAL - only if earnings within 30 days)
        if earnings_info and earnings_info.get('days_until', 999) <= 30:
            print("\n[PHASE 6: EARNINGS PATTERNS RESEARCH (ADDITIONAL)]")
            print(f"  Earnings in {earnings_info['days_until']} days - researching patterns...")
            comprehensive.earnings_research = self._research_earnings_patterns(
                ticker, earnings_info, articles_per_question
            )

        # Calculate totals
        self._calculate_totals(comprehensive)

        print(f"\n{'='*80}")
        print("COMPREHENSIVE RESEARCH COMPLETE")
        print(f"{'='*80}")
        print(f"Total Questions: {comprehensive.total_questions}")
        print(f"Total Articles: {comprehensive.total_articles}")
        print(f"Total Words: {comprehensive.total_words:,}")
        print(f"Sources: {', '.join(set(comprehensive.total_sources))}")

        return comprehensive

    def _research_stock_fundamentals(
        self,
        ticker: str,
        articles_per_question: int,
        global_seen_urls: set = None
    ) -> ResearchReport:
        """
        Research stock fundamentals for thesis generation.

        V2: Uses autonomous question generation and adaptive article reading.
        V3: GLOBAL deduplication - shares URLs with all research areas.
        V4: ALWAYS includes SEC filing research (10-K and 10-Q)
        """

        # CRITICAL: Always research SEC filings first (most accurate data)
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

        # Generate additional questions (dynamically or hardcoded)
        if self.enable_autonomous:
            additional_questions = self._generate_questions_dynamically(
                ticker=ticker,
                research_area="stock_fundamentals",
                context=f"""Generate questions to understand {ticker}'s business, financials, and competitive position.

IMPORTANT: SEC filings (10-K, 10-Q) will be researched separately, so focus on:
- Recent earnings call highlights and management guidance
- Competitive positioning and market share trends
- Growth drivers and strategic initiatives
- Analyst sentiment and price targets""",
                max_questions=3  # Reduced from 5 (since we're adding 2 SEC questions)
            )
            questions = sec_questions + additional_questions
        else:
            questions = sec_questions + self._generate_stock_questions(ticker)

        print(f"Researching {len(questions)} stock fundamental questions...")
        print(f"  ✅ Guaranteed: 10-K annual report + 10-Q quarterly report")
        print(f"  📊 Additional: {len(questions) - 2} supplementary questions")

        all_articles = []
        llm_count = 0
        web_count = 0
        sec_count = 0  # Track SEC filing articles separately
        # Use GLOBAL seen_urls to avoid reading same articles across ALL research areas
        seen_urls = global_seen_urls if global_seen_urls is not None else set()

        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}/{len(questions)}: {question.question}")

            # Track if this is a SEC filing question
            is_sec_filing = question.category == "sec_filing" or "10-k" in question.question.lower() or "10-q" in question.question.lower()

            # HYBRID MODEL: Categorize question
            mode = self._categorize_question(question, ticker)
            print(f"    [MODE: {mode.upper()}]")

            if mode == "llm_only":
                # Fast: Ask LLM directly (no web scraping)
                llm_article = self._ask_llm_directly(ticker, question)
                all_articles.append(llm_article)
                llm_count += 1

            elif mode == "web_only":
                # Current data: Scrape articles
                if self.enable_autonomous:
                    articles = self._research_question_until_satisfied(
                        ticker=ticker,
                        question=question,
                        min_articles=3,
                        max_articles=4,  # Reduced from 6 for speed
                        seen_urls=seen_urls
                    )
                else:
                    articles = self.researcher.web_researcher.search_and_scrape(
                        query=f"{ticker} {question.question}",
                        max_results=articles_per_question
                    )
                all_articles.extend(articles)
                if is_sec_filing:
                    sec_count += len(articles)
                else:
                    web_count += len(articles)

            else:  # hybrid
                # Both: LLM + web validation (not implemented yet, default to web)
                if self.enable_autonomous:
                    articles = self._research_question_until_satisfied(
                        ticker=ticker,
                        question=question,
                        min_articles=2,
                        max_articles=3,
                        seen_urls=seen_urls
                    )
                else:
                    articles = self.researcher.web_researcher.search_and_scrape(
                        query=f"{ticker} {question.question}",
                        max_results=articles_per_question
                    )
                all_articles.extend(articles)
                if is_sec_filing:
                    sec_count += len(articles)
                else:
                    web_count += len(articles)

        # Print hybrid model stats
        print(f"\n[HYBRID MODEL STATS]")
        print(f"  ✅ SEC Filings (10-K/10-Q): {sec_count} articles")
        print(f"  🤖 LLM-only answers: {llm_count}")
        print(f"  🌐 Web articles: {web_count}")
        print(f"  📊 Total sources: {len(all_articles)}")

        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

    def _research_strategy_selection(
        self,
        ticker: str,
        direction: str,
        expected_move_pct: Optional[float],
        articles_per_question: int,
        global_seen_urls: set = None
    ) -> ResearchReport:
        """Research optimal strategy selection with autonomous research and GLOBAL deduplication."""

        # Generate questions dynamically if autonomous mode enabled
        if self.enable_autonomous:
            questions = self._generate_questions_dynamically(
                ticker=ticker,
                research_area="strategy_selection",
                context=f"Generate questions to determine the optimal options strategy for {ticker} with {direction} outlook.",
                max_questions=4  # HYBRID MODEL: Reduced for speed (was 6)
            )
        else:
            questions = self._generate_strategy_questions(ticker, direction, expected_move_pct)

        print(f"Researching {len(questions)} strategy selection questions...")

        all_articles = []
        llm_count = 0
        web_count = 0
        # Use GLOBAL seen_urls to avoid reading same articles across ALL research areas
        seen_urls = global_seen_urls if global_seen_urls is not None else set()

        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}/{len(questions)}: {question.question}")

            # HYBRID MODEL: Categorize question
            mode = self._categorize_question(question, ticker)
            print(f"    [MODE: {mode.upper()}]")

            if mode == "llm_only":
                # Fast: Ask LLM directly (no web scraping)
                llm_article = self._ask_llm_directly(ticker, question, context=f"{direction} outlook, {expected_move_pct*100:.0f}% expected move")
                all_articles.append(llm_article)
                llm_count += 1

            elif mode == "web_only":
                # Current data: Scrape articles
                if self.enable_autonomous:
                    articles = self._research_question_until_satisfied(
                        ticker=ticker,
                        question=question,
                        min_articles=2,
                        max_articles=4,  # Reduced from 6 for speed
                        seen_urls=seen_urls
                    )
                else:
                    articles = self.researcher.web_researcher.search_and_scrape(
                        query=question.question,
                        max_results=articles_per_question
                    )
                all_articles.extend(articles)
                web_count += len(articles)

            else:  # hybrid
                # Both: LLM + web validation
                if self.enable_autonomous:
                    articles = self._research_question_until_satisfied(
                        ticker=ticker,
                        question=question,
                        min_articles=2,
                        max_articles=3,
                        seen_urls=seen_urls
                    )
                else:
                    articles = self.researcher.web_researcher.search_and_scrape(
                        query=question.question,
                        max_results=articles_per_question
                    )
                all_articles.extend(articles)
                web_count += len(articles)

        # Print hybrid model stats for strategy selection
        print(f"\n[HYBRID MODEL STATS - STRATEGY]")
        print(f"  🤖 LLM-only answers: {llm_count}")
        print(f"  🌐 Web articles: {web_count}")
        print(f"  📊 Total sources: {len(all_articles)}")

        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

    def _research_contract_selection(
        self,
        ticker: str,
        direction: str,
        expected_move_pct: float,
        timeframe_days: Optional[int],
        articles_per_question: int
    ) -> ResearchReport:
        """Research optimal contract selection."""
        questions = self._generate_contract_questions(
            ticker, direction, expected_move_pct, timeframe_days
        )

        print(f"Researching {len(questions)} contract selection questions...")

        all_articles = []
        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}/{len(questions)}: {question.question}")
            articles = self.researcher.web_researcher.search_and_scrape(
                query=question.question,
                max_results=articles_per_question
            )
            all_articles.extend(articles)

        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

    def _research_risk_management(
        self,
        ticker: str,
        articles_per_question: int
    ) -> ResearchReport:
        """Research risk management and historical patterns."""
        questions = self._generate_risk_questions(ticker)

        print(f"Researching {len(questions)} risk management questions...")

        all_articles = []
        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}/{len(questions)}: {question.question}")
            articles = self.researcher.web_researcher.search_and_scrape(
                query=f"{ticker} {question.question}",
                max_results=articles_per_question
            )
            all_articles.extend(articles)

        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

    def _research_market_conditions(
        self,
        ticker: str,
        articles_per_question: int
    ) -> ResearchReport:
        """Research market conditions and IV environment."""
        questions = self._generate_market_questions(ticker)

        print(f"Researching {len(questions)} market condition questions...")

        all_articles = []
        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}/{len(questions)}: {question.question}")
            articles = self.researcher.web_researcher.search_and_scrape(
                query=question.question,
                max_results=articles_per_question
            )
            all_articles.extend(articles)

        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

    def _research_earnings_patterns(
        self,
        ticker: str,
        earnings_info: Dict,
        articles_per_question: int
    ) -> ResearchReport:
        """
        Research earnings patterns (ADDITIONAL - only when earnings within 30 days).

        This is NOT a replacement for fundamental research.
        It's an ADDITIONAL layer to inform earnings-specific strategies.
        """
        questions = self._generate_earnings_questions(ticker, earnings_info)

        print(f"Researching {len(questions)} earnings pattern questions...")

        all_articles = []
        for i, question in enumerate(questions, 1):
            print(f"\n  Question {i}/{len(questions)}: {question.question}")
            articles = self.researcher.web_researcher.search_and_scrape(
                query=f"{ticker} {question.question}",
                max_results=articles_per_question
            )
            all_articles.extend(articles)

        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        return ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

    def _generate_stock_questions(self, ticker: str) -> List[ResearchQuestion]:
        """Generate stock fundamental research questions."""
        return [
            ResearchQuestion(
                f"What were {ticker}'s most recent quarterly earnings results?",
                "earnings", 1
            ),
            ResearchQuestion(
                f"How does {ticker}'s market position compare to competitors?",
                "competitive", 1
            ),
            ResearchQuestion(
                f"What are the key growth drivers for {ticker}?",
                "catalysts", 1
            ),
        ]

    def _generate_strategy_questions(
        self,
        ticker: str,
        direction: str,
        expected_move_pct: Optional[float]
    ) -> List[ResearchQuestion]:
        """Generate strategy selection research questions."""
        questions = []

        # General strategy questions
        if direction == "BULLISH":
            questions.append(ResearchQuestion(
                "Bull call spread vs long call - when to choose which strategy?",
                "strategy", 1
            ))
            questions.append(ResearchQuestion(
                "What is the optimal strike selection for bullish vertical spreads?",
                "strategy", 1
            ))
        elif direction == "BEARISH":
            questions.append(ResearchQuestion(
                "Bear put spread vs long put - which strategy works best?",
                "strategy", 1
            ))
            questions.append(ResearchQuestion(
                "What is the optimal strike selection for bearish vertical spreads?",
                "strategy", 1
            ))
        elif direction == "NEUTRAL":
            questions.append(ResearchQuestion(
                "Iron condor vs iron butterfly - which neutral strategy is better?",
                "strategy", 1
            ))
            questions.append(ResearchQuestion(
                "What is the optimal wing width for iron condors?",
                "strategy", 1
            ))

        # Stock-specific strategy questions
        questions.append(ResearchQuestion(
            f"What options strategies work best for {ticker} stock?",
            "strategy", 1
        ))

        return questions

    def _generate_contract_questions(
        self,
        ticker: str,
        direction: str,
        expected_move_pct: float,
        timeframe_days: Optional[int]
    ) -> List[ResearchQuestion]:
        """Generate contract selection research questions."""
        questions = []

        # Delta selection
        questions.append(ResearchQuestion(
            f"What delta should I target for {direction.lower()} options trades?",
            "contract", 1
        ))

        # Expiration timing
        if timeframe_days:
            questions.append(ResearchQuestion(
                f"What is the optimal expiration for a {timeframe_days}-day trade?",
                "contract", 1
            ))
        else:
            questions.append(ResearchQuestion(
                "What is the optimal option expiration timing for directional trades?",
                "contract", 1
            ))

        # Strike spacing for spreads
        if direction in ["BULLISH", "BEARISH"]:
            questions.append(ResearchQuestion(
                f"What is the optimal spread width for vertical spreads on {ticker}?",
                "contract", 1
            ))

        return questions

    def _generate_risk_questions(self, ticker: str) -> List[ResearchQuestion]:
        """Generate risk management research questions."""
        return [
            ResearchQuestion(
                f"What is {ticker}'s historical volatility pattern?",
                "risk", 1
            ),
            ResearchQuestion(
                f"What are typical post-earnings moves for {ticker}?",
                "risk", 1
            ),
            ResearchQuestion(
                f"What is the risk profile of options on {ticker}?",
                "risk", 1
            ),
        ]

    def _generate_market_questions(self, ticker: str) -> List[ResearchQuestion]:
        """Generate market conditions research questions."""
        return [
            ResearchQuestion(
                f"What is the current implied volatility environment for {ticker}?",
                "market", 1
            ),
            ResearchQuestion(
                "What is the current market regime (bull, bear, or sideways)?",
                "market", 1
            ),
            ResearchQuestion(
                f"What sector trends are affecting {ticker}?",
                "market", 1
            ),
        ]

    def _generate_earnings_questions(
        self,
        ticker: str,
        earnings_info: Dict
    ) -> List[ResearchQuestion]:
        """
        Generate earnings pattern research questions (ADDITIONAL layer).

        Only called when earnings is within 30 days.
        """
        days_until = earnings_info.get('days_until', 0)

        return [
            ResearchQuestion(
                f"What was {ticker}'s typical post-earnings move in the last 4 quarters?",
                "earnings", 1
            ),
            ResearchQuestion(
                f"Does {ticker} usually beat or miss earnings estimates?",
                "earnings", 1
            ),
            ResearchQuestion(
                f"What is the historical IV crush pattern for {ticker} after earnings?",
                "earnings", 1
            ),
            ResearchQuestion(
                f"Best options strategies for {ticker} earnings plays?",
                "earnings", 1
            ),
        ]

    def _calculate_totals(self, comprehensive: ComprehensiveResearch):
        """Calculate total statistics."""
        all_reports = [
            comprehensive.stock_research,
            comprehensive.strategy_research,
            comprehensive.contract_research,
            comprehensive.risk_research,
            comprehensive.market_research,
            comprehensive.earnings_research  # ADDITIONAL layer
        ]

        for report in all_reports:
            if report:
                comprehensive.total_questions += len(report.questions)
                comprehensive.total_articles += len(report.articles)
                comprehensive.total_words += report.total_words
                comprehensive.total_sources.extend(report.sources)

    # ============================================================================
    # TRUE AUTONOMOUS RESEARCH METHODS (V2)
    # ============================================================================

    def _generate_questions_dynamically(
        self,
        ticker: str,
        research_area: str,
        context: str = "",
        max_questions: int = 23
    ) -> List[ResearchQuestion]:
        """
        Use LLM to generate research questions dynamically.

        Instead of hardcoded questions, bot decides what to research based on context.

        Args:
            ticker: Stock ticker
            research_area: "stock_fundamentals", "risk", "market", "earnings", "strategy", "contracts"
            context: Additional context (e.g., thesis direction, timeframe)
            max_questions: Maximum questions to generate (safety limit)

        Returns:
            List of ResearchQuestion objects generated by LLM
        """

        if not self.enable_autonomous or not self.llm_client:
            # Fall back to hardcoded questions
            if research_area == "stock_fundamentals":
                return self._generate_stock_questions(ticker)
            elif research_area == "risk":
                return self._generate_risk_questions(ticker)
            elif research_area == "market":
                return self._generate_market_questions(ticker)
            else:
                return []

        print(f"\n[AUTONOMOUS] Generating research questions for: {research_area}")

        # Build prompt for LLM
        prompt = self._build_question_generation_prompt(ticker, research_area, context, max_questions)

        # Call LLM
        try:
            response_text = self._call_llm(prompt)

            # Parse questions from response
            questions = self._parse_questions_from_response(response_text, research_area)

            print(f"[AUTONOMOUS] Generated {len(questions)} questions")
            return questions

        except Exception as e:
            print(f"[WARNING] LLM question generation failed: {e}")
            print(f"[FALLBACK] Using hardcoded questions")
            # Fall back to hardcoded
            if research_area == "stock_fundamentals":
                return self._generate_stock_questions(ticker)
            elif research_area == "risk":
                return self._generate_risk_questions(ticker)
            elif research_area == "market":
                return self._generate_market_questions(ticker)
            else:
                return []

    def _build_question_generation_prompt(
        self,
        ticker: str,
        research_area: str,
        context: str,
        max_questions: int
    ) -> str:
        """Build prompt for LLM to generate research questions."""

        area_descriptions = {
            "stock_fundamentals": f"stock fundamentals, competitive position, growth drivers, and business model for {ticker}",
            "risk": f"risks, challenges, and volatility patterns for {ticker}",
            "market": f"market conditions, IV environment, and sector trends affecting {ticker}",
            "earnings": f"earnings patterns, historical moves, and IV crush for {ticker}",
            "strategy": f"optimal options strategies for trading {ticker}",
            "contracts": f"optimal strike selection, expiration timing, and contract parameters for {ticker}"
        }

        description = area_descriptions.get(research_area, f"{research_area} for {ticker}")

        prompt = f"""You are researching {description}.

{f'Context: {context}' if context else ''}

Generate research questions that would help you make an informed decision.

IMPORTANT - Mix two types of questions:
1. GENERAL KNOWLEDGE questions (can be answered with trading principles/theory):
   - Example: "What is the optimal delta range for bullish call spreads?"
   - Example: "When should traders exit losing options positions?"

2. CURRENT DATA questions (need recent news/earnings/ratings):
   - Example: "What were {ticker}'s most recent quarterly earnings results?"
   - Example: "What are current analyst price targets for {ticker}?"

Requirements:
- Generate {max_questions//2} general knowledge questions
- Generate {max_questions - max_questions//2} current data questions
- Questions should be clear and specific
- Focus on actionable insights that inform strategy selection

Return ONLY the questions, one per line, numbered.

Generate the questions:"""

        return prompt

    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Call LLM (OpenAI or Anthropic) and return response text."""

        if self.llm_provider == "openai":
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for question generation
                messages=[
                    {"role": "system", "content": "You are a research assistant helping with financial analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content

        elif self.llm_provider == "anthropic":
            response = self.llm_client.messages.create(
                model="claude-3-5-haiku-20241022",  # Fast and cheap
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def _ask_llm_directly(
        self,
        ticker: str,
        question: ResearchQuestion,
        context: str = ""
    ) -> Article:
        """
        Ask LLM directly without web scraping (HYBRID MODEL - LLM-only questions).

        Use for:
        - General strategy concepts ("What's the optimal delta for bull call spreads?")
        - Risk management best practices ("When should I exit a losing trade?")
        - Options theory ("How does IV affect option pricing?")

        Args:
            ticker: Stock ticker (for context)
            question: Research question
            context: Additional context

        Returns:
            Article object with LLM's answer
        """

        prompt = f"""Answer this question about {ticker} using your knowledge of options trading and market principles:

Question: {question.question}

{f"Context: {context}" if context else ""}

Provide a clear, concise answer (3-5 sentences) based on:
- General options trading principles
- Risk management best practices
- Market mechanics and patterns
- Industry standard approaches

Focus on actionable insights. Be specific with numbers when relevant (e.g., "typically 60-70 delta" not "moderate delta").

Answer:"""

        print(f"    [LLM-ONLY] Asking LLM directly (no web scraping)...")
        answer = self._call_llm(prompt, temperature=0.7, max_tokens=500)
        print(f"    [LLM-ONLY] Got answer ({len(answer)} chars)")

        # Convert to Article format so it can be used by thesis generator
        return Article(
            url="llm://knowledge-base",
            title=f"LLM Answer: {question.question}",
            content=answer,
            source="LLM Knowledge Base",
            word_count=len(answer.split())
        )

    def _categorize_question(self, question: ResearchQuestion, ticker: str) -> str:
        """
        Categorize question into research mode.

        Returns:
            "llm_only" - General knowledge, no current data needed
            "web_only" - Requires current/recent information
            "hybrid" - LLM framework + web validation
        """

        question_lower = question.question.lower()

        # CRITICAL: SEC filings ALWAYS require web scraping
        if "10-k" in question_lower or "10-q" in question_lower or "sec filing" in question_lower or question.category == "sec_filing":
            return "web_only"

        # LLM-ONLY: General strategy/risk concepts (no current data needed)
        llm_keywords = [
            "optimal delta", "best strike", "spread width", "risk management",
            "when to exit", "position sizing", "how does", "what is the",
            "strategy comparison", "which strategy", "iron condor vs",
            "bull call spread vs", "optimal expiration", "dte for",
            "how to select", "what delta", "typical", "generally",
            "best practice", "rule of thumb"
        ]

        # WEB-ONLY: Requires current information
        web_keywords = [
            "recent", "latest", "current", "this week", "this month",
            "quarterly earnings", "analyst rating", "price target",
            "breaking news", "announcement", "guidance", "just released",
            "yesterday", "last week", ticker.lower()
        ]

        # Check for LLM-only
        for keyword in llm_keywords:
            if keyword in question_lower:
                return "llm_only"

        # Check for web-only (ticker-specific or time-sensitive)
        for keyword in web_keywords:
            if keyword in question_lower:
                return "web_only"

        # Default: web-only (safer to scrape real data when unsure)
        return "web_only"

    def _parse_questions_from_response(self, response_text: str, research_area: str) -> List[ResearchQuestion]:
        """Parse questions from LLM response."""

        questions = []
        lines = response_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering (1., 2., etc.)
            if line[0].isdigit() and ('.' in line[:5] or ')' in line[:5]):
                line = line.split('.', 1)[-1].split(')', 1)[-1].strip()

            # Remove bullet points
            if line.startswith('-') or line.startswith('•'):
                line = line[1:].strip()

            # Skip if not a question
            if not line or not line.endswith('?'):
                continue

            questions.append(ResearchQuestion(
                question=line,
                category=research_area,
                priority=1
            ))

        return questions

    def _research_question_until_satisfied(
        self,
        ticker: str,
        question: ResearchQuestion,
        min_articles: int = 2,
        max_articles: int = 16,
        seen_urls: Optional[set] = None
    ) -> List:
        """
        Research a question by reading articles until bot is satisfied.
        DEDUPLICATION: Tracks URLs to avoid rereading same articles.

        Args:
            ticker: Stock ticker
            question: Question to research
            min_articles: Minimum articles to read before checking satisfaction
            max_articles: Maximum articles (safety limit)
            seen_urls: Set of URLs already read (for deduplication)

        Returns:
            List of articles
        """

        if seen_urls is None:
            seen_urls = set()

        if not self.enable_autonomous or not self.llm_client:
            # Fall back to fixed count
            articles = self.researcher.web_researcher.search_and_scrape(
                query=f"{ticker} {question.question}",
                max_results=2
            )
            return articles

        print(f"  [AUTONOMOUS] Researching until satisfied...")

        articles = []
        attempts = 0
        max_attempts = max_articles * 2  # Safety limit
        previous_queries = []  # Track queries to avoid repeating

        while len(articles) < max_articles and attempts < max_attempts:
            attempts += 1

            # Generate search query
            if attempts == 1:
                # First attempt: Use the question as-is
                search_query = f"{ticker} {question.question}".strip()
            else:
                # Subsequent attempts: Ask LLM to generate alternative query
                print(f"    [LLM] Generating alternative search query...")
                search_query = self._generate_alternative_search_query(
                    ticker=ticker,
                    question=question,
                    articles_read=articles,
                    previous_queries=previous_queries
                )
                print(f"    [LLM] New query: '{search_query[:80]}...'")

            previous_queries.append(search_query)

            # EFFICIENT: Search first, filter URLs, THEN scrape only new ones
            print(f"    Searching: '{search_query[:80]}...'")
            search_results = self.researcher.web_researcher.search(
                query=search_query,
                max_results=15  # Get extra to compensate for duplicates
            )

            if not search_results:
                print(f"    [No search results found]")
                break

            # Filter out duplicate URLs BEFORE scraping (saves bandwidth!)
            unique_urls = []
            for result in search_results:
                if result.url not in seen_urls:
                    unique_urls.append(result.url)
                    seen_urls.add(result.url)
                else:
                    print(f"    [SKIP DUPLICATE URL] {result.title[:50]}...")

            if not unique_urls:
                print(f"    [All URLs were duplicates, trying different query...]")
                continue  # All were duplicates, try next query variation

            # Now scrape only the unique URLs (efficient!)
            print(f"    Scraping {len(unique_urls)} new articles...")
            unique_articles = self.researcher.web_researcher.scrape_multiple(
                urls=unique_urls[:3],  # Scrape top 3 unique URLs
                max_articles=3
            )

            if not unique_articles:
                print(f"    [Scraping failed, trying different query...]")
                continue

            articles.extend(unique_articles)
            for article in unique_articles:
                print(f"    Article {len(articles)}: {article.title[:60]}...")

            # Check satisfaction after minimum articles
            if len(articles) >= min_articles:
                # Ask LLM: "Do I have enough information?"
                satisfied = self._check_satisfaction(question, articles)

                if satisfied:
                    print(f"    [SATISFIED] {len(articles)} articles sufficient")
                    break

        if len(articles) >= max_articles:
            print(f"    [MAX REACHED] Stopping at {max_articles} articles")

        return articles

    def _check_satisfaction(self, question: ResearchQuestion, articles: List) -> bool:
        """
        Ask LLM if we have enough information to answer the question.

        Args:
            question: Research question
            articles: Articles read so far

        Returns:
            True if satisfied, False if need more research
        """

        # Summarize article content (just titles and snippets to save tokens)
        articles_summary = "\n".join([
            f"- {a.title} ({a.word_count} words)"
            for a in articles
        ])

        prompt = f"""Research Question: {question.question}

Articles Read ({len(articles)}):
{articles_summary}

Do we have enough information to form a reasonable opinion on this question?

Consider:
- Do we have some specific data or concrete examples?
- Can we form an informed view based on what we've read?
- Is there enough substance to make a decision?

You DON'T need perfect information - just enough to form a reasonable opinion.

Answer with ONLY "YES" or "NO" followed by brief reasoning.

Example:
YES - We have enough data points and examples to form an informed view.
NO - Articles are too vague, need at least one article with concrete information."""

        try:
            response = self._call_llm(prompt, temperature=0.3)  # Lower temp for binary decision

            # Check if response starts with YES
            return response.strip().upper().startswith("YES")

        except Exception as e:
            print(f"    [WARNING] Satisfaction check failed: {e}")
            # Default to satisfied after min_articles to avoid infinite loop
            return True

    def _generate_alternative_search_query(
        self,
        ticker: str,
        question: ResearchQuestion,
        articles_read: List,
        previous_queries: List[str]
    ) -> str:
        """
        Use LLM to generate a DIFFERENT search query to find more diverse articles.

        Args:
            ticker: Stock ticker
            question: Original research question
            articles_read: Articles found so far
            previous_queries: Queries already tried

        Returns:
            Alternative search query string
        """

        # Summarize what we already found
        articles_summary = "\n".join([
            f"- {a.title[:80]}..." for a in articles_read
        ]) if articles_read else "None yet"

        queries_tried = "\n".join([f"- {q}" for q in previous_queries])

        prompt = f"""I'm researching this question about {ticker}:
"{question.question}"

Search queries already tried:
{queries_tried}

Articles already found:
{articles_summary}

These searches are returning the same articles. Generate a DIFFERENT search query that will find NEW articles from a completely different angle or source.

Requirements:
- Must be genuinely different (not just adding "latest" or "news")
- Should approach from a new perspective (e.g., analyst reports, SEC filings, competitor analysis, etc.)
- Keep it concise (under 100 characters)
- Include {ticker} for context

Return ONLY the search query, nothing else."""

        try:
            response = self._call_llm(prompt, temperature=0.7, max_tokens=100)  # Higher temp for creativity
            alternative_query = response.strip().strip('"').strip("'")  # Remove quotes if present

            # Validate it's different
            if alternative_query.lower() in [q.lower() for q in previous_queries]:
                # LLM returned same query, fallback to generic alternative
                return f"{ticker} {question.category} analysis report"

            return alternative_query

        except Exception as e:
            print(f"    [WARNING] Alternative query generation failed: {e}")
            # Fallback to generic alternative
            return f"{ticker} {question.category} detailed analysis"


if __name__ == "__main__":
    # Test research orchestrator
    print("=" * 80)
    print("TESTING RESEARCH ORCHESTRATOR")
    print("=" * 80)

    orchestrator = ResearchOrchestrator()

    # Phase 1: Research stock fundamentals only
    print("\n[TEST 1: Stock Fundamentals Only]")
    research = orchestrator.research_everything(
        ticker="NVDA",
        articles_per_question=1  # Fewer for testing
    )

    print(f"\n[RESULTS]")
    print(f"  Stock Research: {research.stock_research.total_words:,} words from {len(research.stock_research.articles)} articles")
    print(f"  Risk Research: {research.risk_research.total_words:,} words from {len(research.risk_research.articles)} articles")
    print(f"  Market Research: {research.market_research.total_words:,} words from {len(research.market_research.articles)} articles")

    # Phase 2: Full research with thesis context
    print("\n" + "=" * 80)
    print("[TEST 2: Full Research with Thesis Context]")
    research = orchestrator.research_everything(
        ticker="NVDA",
        thesis_direction="BULLISH",
        expected_move_pct=0.15,
        timeframe_days=30,
        articles_per_question=1
    )

    print(f"\n[RESULTS]")
    print(f"  Stock Research: {research.stock_research.total_words:,} words")
    print(f"  Strategy Research: {research.strategy_research.total_words:,} words")
    print(f"  Contract Research: {research.contract_research.total_words:,} words")
    print(f"  Risk Research: {research.risk_research.total_words:,} words")
    print(f"  Market Research: {research.market_research.total_words:,} words")
    print(f"  TOTAL: {research.total_words:,} words from {research.total_articles} articles")

    print("\n" + "=" * 80)
    print("[SUCCESS] Research Orchestrator Working!")
    print("=" * 80)
