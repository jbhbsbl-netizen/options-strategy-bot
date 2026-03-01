"""
Autonomous Research Engine Mixin

Provides LLM-powered autonomous research capabilities:
- Dynamic question generation via LLM
- Adaptive article reading until satisfied
- Hybrid routing (LLM-only vs web scraping vs both)
- Alternative search query generation to escape duplicate results

Used as a mixin by ResearchOrchestrator.
"""
import os
from typing import List, Optional

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

from src.research.autonomous_researcher import ResearchQuestion
from src.research.web_researcher import Article


class AutonomousEngineMixin:
    """
    Mixin providing LLM-powered autonomous research methods.

    Expects the following attributes to be set on self by the host class:
        llm_client:       OpenAI or Anthropic client instance (or None)
        llm_provider:     "openai" | "anthropic"
        enable_autonomous: bool
        researcher:       AutonomousResearcher instance
    """

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    def _generate_questions_dynamically(
        self,
        ticker: str,
        research_area: str,
        context: str = "",
        max_questions: int = 23
    ) -> List[ResearchQuestion]:
        """
        Use LLM to generate research questions dynamically.

        Falls back to hardcoded questions if LLM is unavailable.
        """
        if not self.enable_autonomous or not self.llm_client:
            if research_area == "stock_fundamentals":
                return self._generate_stock_questions(ticker)
            elif research_area == "risk":
                return self._generate_risk_questions(ticker)
            elif research_area == "market":
                return self._generate_market_questions(ticker)
            else:
                return []

        print(f"\n[AUTONOMOUS] Generating research questions for: {research_area}")
        prompt = self._build_question_generation_prompt(
            ticker, research_area, context, max_questions
        )

        try:
            response_text = self._call_llm(prompt)
            questions = self._parse_questions_from_response(response_text, research_area)
            print(f"[AUTONOMOUS] Generated {len(questions)} questions")
            return questions

        except Exception as e:
            print(f"[WARNING] LLM question generation failed: {e}")
            print("[FALLBACK] Using hardcoded questions")
            if research_area == "stock_fundamentals":
                return self._generate_stock_questions(ticker)
            elif research_area == "risk":
                return self._generate_risk_questions(ticker)
            elif research_area == "market":
                return self._generate_market_questions(ticker)
            else:
                return []

    def _research_question_until_satisfied(
        self,
        ticker: str,
        question: ResearchQuestion,
        min_articles: int = 2,
        max_articles: int = 16,
        seen_urls: Optional[set] = None
    ) -> List:
        """
        Read articles for a question until the LLM is satisfied with coverage.

        Tracks seen URLs globally to avoid re-scraping across research phases.
        """
        if seen_urls is None:
            seen_urls = set()

        if not self.enable_autonomous or not self.llm_client:
            articles = self.researcher.web_researcher.search_and_scrape(
                query=f"{ticker} {question.question}",
                max_results=2
            )
            return articles

        print("  [AUTONOMOUS] Researching until satisfied...")

        articles = []
        attempts = 0
        max_attempts = max_articles * 2
        previous_queries: List[str] = []

        while len(articles) < max_articles and attempts < max_attempts:
            attempts += 1

            if attempts == 1:
                search_query = f"{ticker} {question.question}".strip()
            else:
                print("    [LLM] Generating alternative search query...")
                search_query = self._generate_alternative_search_query(
                    ticker=ticker,
                    question=question,
                    articles_read=articles,
                    previous_queries=previous_queries
                )
                print(f"    [LLM] New query: '{search_query[:80]}...'")

            previous_queries.append(search_query)

            print(f"    Searching: '{search_query[:80]}...'")
            search_results = self.researcher.web_researcher.search(
                query=search_query,
                max_results=15
            )

            if not search_results:
                print("    [No search results found]")
                break

            unique_urls = []
            for result in search_results:
                if result.url not in seen_urls:
                    unique_urls.append(result.url)
                    seen_urls.add(result.url)
                else:
                    print(f"    [SKIP DUPLICATE URL] {result.title[:50]}...")

            if not unique_urls:
                print("    [All URLs were duplicates, trying different query...]")
                continue

            print(f"    Scraping {len(unique_urls)} new articles...")
            unique_articles = self.researcher.web_researcher.scrape_multiple(
                urls=unique_urls[:3],
                max_articles=3
            )

            if not unique_articles:
                print("    [Scraping failed, trying different query...]")
                continue

            articles.extend(unique_articles)
            for article in unique_articles:
                print(f"    Article {len(articles)}: {article.title[:60]}...")

            if len(articles) >= min_articles:
                if self._check_satisfaction(question, articles):
                    print(f"    [SATISFIED] {len(articles)} articles sufficient")
                    break

        if len(articles) >= max_articles:
            print(f"    [MAX REACHED] Stopping at {max_articles} articles")

        return articles

    # -------------------------------------------------------------------------
    # LLM call helpers
    # -------------------------------------------------------------------------

    def _call_llm(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Call the configured LLM and return the response text."""
        if self.llm_provider == "openai":
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
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
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
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
        Answer a question using LLM knowledge without web scraping.

        Used for general options theory and best-practice questions where
        current data isn't needed (e.g., "What is the optimal delta range
        for bull call spreads?").
        """
        prompt = f"""Answer this question about {ticker} using your knowledge of options trading and market principles:

Question: {question.question}

{f"Context: {context}" if context else ""}

Provide a clear, concise answer (3-5 sentences) based on:
- General options trading principles
- Risk management best practices
- Market mechanics and patterns
- Industry standard approaches

Focus on actionable insights. Be specific with numbers when relevant.

Answer:"""

        print("    [LLM-ONLY] Asking LLM directly (no web scraping)...")
        answer = self._call_llm(prompt, temperature=0.7, max_tokens=500)
        print(f"    [LLM-ONLY] Got answer ({len(answer)} chars)")

        return Article(
            url="llm://knowledge-base",
            title=f"LLM Answer: {question.question}",
            content=answer,
            source="LLM Knowledge Base",
            word_count=len(answer.split())
        )

    # -------------------------------------------------------------------------
    # Routing and parsing
    # -------------------------------------------------------------------------

    def _categorize_question(self, question: ResearchQuestion, ticker: str) -> str:
        """
        Route a question to the appropriate research mode.

        Returns:
            "llm_only"  — general knowledge, no current data needed
            "web_only"  — requires recent/current information
            "hybrid"    — LLM framework + web validation
        """
        question_lower = question.question.lower()

        # SEC filings always require web scraping
        if (
            "10-k" in question_lower
            or "10-q" in question_lower
            or "sec filing" in question_lower
            or question.category == "sec_filing"
        ):
            return "web_only"

        llm_keywords = [
            "optimal delta", "best strike", "spread width", "risk management",
            "when to exit", "position sizing", "how does", "what is the",
            "strategy comparison", "which strategy", "iron condor vs",
            "bull call spread vs", "optimal expiration", "dte for",
            "how to select", "what delta", "typical", "generally",
            "best practice", "rule of thumb"
        ]

        web_keywords = [
            "recent", "latest", "current", "this week", "this month",
            "quarterly earnings", "analyst rating", "price target",
            "breaking news", "announcement", "guidance", "just released",
            "yesterday", "last week", ticker.lower()
        ]

        for keyword in llm_keywords:
            if keyword in question_lower:
                return "llm_only"

        for keyword in web_keywords:
            if keyword in question_lower:
                return "web_only"

        return "web_only"  # Default: fetch real data when unsure

    def _parse_questions_from_response(
        self,
        response_text: str,
        research_area: str
    ) -> List[ResearchQuestion]:
        """Parse numbered or bulleted questions from an LLM response."""
        questions = []
        lines = response_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Strip numbering (1., 2., 1), etc.)
            if line[0].isdigit() and ("." in line[:5] or ")" in line[:5]):
                line = line.split(".", 1)[-1].split(")", 1)[-1].strip()

            # Strip bullet markers
            if line.startswith("-") or line.startswith("•"):
                line = line[1:].strip()

            if not line or not line.endswith("?"):
                continue

            questions.append(ResearchQuestion(
                question=line,
                category=research_area,
                priority=1
            ))

        return questions

    # -------------------------------------------------------------------------
    # Satisfaction checking
    # -------------------------------------------------------------------------

    def _check_satisfaction(
        self,
        question: ResearchQuestion,
        articles: List
    ) -> bool:
        """Ask the LLM whether the articles collected are sufficient."""
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
            response = self._call_llm(prompt, temperature=0.3)
            return response.strip().upper().startswith("YES")
        except Exception as e:
            print(f"    [WARNING] Satisfaction check failed: {e}")
            return True  # Default satisfied to avoid infinite loop

    def _generate_alternative_search_query(
        self,
        ticker: str,
        question: ResearchQuestion,
        articles_read: List,
        previous_queries: List[str]
    ) -> str:
        """Generate a different search query to escape duplicate results."""
        articles_summary = (
            "\n".join([f"- {a.title[:80]}..." for a in articles_read])
            if articles_read else "None yet"
        )
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
- Should approach from a new perspective (analyst reports, SEC filings, competitor analysis, etc.)
- Keep it concise (under 100 characters)
- Include {ticker} for context

Return ONLY the search query, nothing else."""

        try:
            response = self._call_llm(prompt, temperature=0.7, max_tokens=100)
            alternative = response.strip().strip('"').strip("'")

            if alternative.lower() in [q.lower() for q in previous_queries]:
                return f"{ticker} {question.category} analysis report"

            return alternative

        except Exception as e:
            print(f"    [WARNING] Alternative query generation failed: {e}")
            return f"{ticker} {question.category} detailed analysis"

    # -------------------------------------------------------------------------
    # Prompt builder
    # -------------------------------------------------------------------------

    def _build_question_generation_prompt(
        self,
        ticker: str,
        research_area: str,
        context: str,
        max_questions: int
    ) -> str:
        """Build the prompt used to generate research questions via LLM."""
        area_descriptions = {
            "stock_fundamentals": f"stock fundamentals, competitive position, growth drivers, and business model for {ticker}",
            "risk": f"risks, challenges, and volatility patterns for {ticker}",
            "market": f"market conditions, IV environment, and sector trends affecting {ticker}",
            "earnings": f"earnings patterns, historical moves, and IV crush for {ticker}",
            "strategy": f"optimal options strategies for trading {ticker}",
            "contracts": f"optimal strike selection, expiration timing, and contract parameters for {ticker}"
        }

        description = area_descriptions.get(research_area, f"{research_area} for {ticker}")

        return f"""You are researching {description}.

{f"Context: {context}" if context else ""}

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
