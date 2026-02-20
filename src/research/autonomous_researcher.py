"""
Autonomous Researcher - Generates research questions and synthesizes findings.

This module uses LLM to:
1. Generate intelligent research questions about a stock
2. Search the web for each question
3. Synthesize findings into a structured research report
"""
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from src.research.web_researcher import WebResearcher, Article

# Load environment variables
load_dotenv()

# Check for LLM availability
try:
    import anthropic
    ANTHROPIC_AVAILABLE = bool(os.getenv('ANTHROPIC_API_KEY'))
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = bool(os.getenv('OPENAI_API_KEY'))
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class ResearchQuestion:
    """Research question with category."""
    question: str
    category: str  # "earnings", "competitive", "industry", "catalysts", "risks"
    priority: int  # 1 (high) to 3 (low)


@dataclass
class ResearchReport:
    """Complete research report for a stock."""
    ticker: str
    questions: List[ResearchQuestion]
    articles: List[Article]
    total_words: int
    sources: List[str]
    summary: Optional[str] = None
    key_findings: List[str] = field(default_factory=list)


class AutonomousResearcher:
    """Autonomous researcher that generates questions and searches the web."""

    def __init__(self, use_anthropic: bool = True, model: str = None):
        """
        Initialize autonomous researcher.

        Args:
            use_anthropic: Use Anthropic Claude (else OpenAI GPT)
            model: Specific model to use (default: claude-3-5-sonnet for Anthropic, gpt-4 for OpenAI)
        """
        self.web_researcher = WebResearcher()
        self.use_anthropic = use_anthropic and ANTHROPIC_AVAILABLE

        if self.use_anthropic:
            self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            self.model = model or "claude-3-5-sonnet-20241022"
        elif OPENAI_AVAILABLE:
            self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = model or "gpt-4"
        else:
            raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")

    def research_stock(
        self,
        ticker: str,
        articles_per_question: int = 3,
        max_questions: int = 5
    ) -> ResearchReport:
        """
        Conduct autonomous research on a stock.

        Args:
            ticker: Stock ticker symbol
            articles_per_question: Articles to scrape per question
            max_questions: Maximum research questions to generate

        Returns:
            ResearchReport with all findings
        """
        print(f"\n{'='*80}")
        print(f"AUTONOMOUS RESEARCH: {ticker}")
        print(f"{'='*80}\n")

        # Step 1: Generate research questions
        print("[Step 1/3] Generating research questions...")
        questions = self._generate_research_questions(ticker, max_questions)

        print(f"\nGenerated {len(questions)} research questions:")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. [{q.category}] {q.question}")

        # Step 2: Search and scrape for each question
        print(f"\n[Step 2/3] Searching and scraping articles...")
        all_articles = []
        for i, question in enumerate(questions, 1):
            print(f"\n--- Question {i}/{len(questions)}: {question.question} ---")
            articles = self.web_researcher.search_and_scrape(
                query=f"{ticker} {question.question}",
                max_results=articles_per_question
            )
            all_articles.extend(articles)

        # Step 3: Synthesize findings
        print(f"\n[Step 3/3] Synthesizing research findings...")
        total_words = sum(a.word_count for a in all_articles)
        sources = list(set(a.source for a in all_articles))

        print(f"\nResearch complete:")
        print(f"  - Questions: {len(questions)}")
        print(f"  - Articles scraped: {len(all_articles)}")
        print(f"  - Total words: {total_words:,}")
        print(f"  - Sources: {', '.join(sources)}")

        report = ResearchReport(
            ticker=ticker,
            questions=questions,
            articles=all_articles,
            total_words=total_words,
            sources=sources
        )

        # Generate summary (optional, costs tokens)
        # report.summary = self._synthesize_findings(ticker, all_articles)

        return report

    def _generate_research_questions(
        self,
        ticker: str,
        max_questions: int = 5
    ) -> List[ResearchQuestion]:
        """
        Use LLM to generate intelligent research questions.

        Args:
            ticker: Stock ticker
            max_questions: Maximum questions to generate

        Returns:
            List of ResearchQuestion objects
        """
        prompt = f"""Generate {max_questions} focused research questions to analyze {ticker} stock for options trading.

Questions should cover:
1. Recent earnings and financial performance
2. Competitive landscape and market share
3. Industry trends and growth prospects
4. Upcoming catalysts (product launches, events, etc.)
5. Key risks and headwinds

Return ONLY a numbered list of questions, one per line.
Example format:
1. What were {ticker}'s most recent quarterly earnings results?
2. How does {ticker}'s market share compare to competitors?
3. What are the key industry trends affecting {ticker}?
4. What upcoming catalysts could impact {ticker}'s stock price?
5. What are the main risks facing {ticker}?"""

        try:
            if self.use_anthropic:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                text = response.choices[0].message.content

            # Parse questions
            questions = []
            categories = ["earnings", "competitive", "industry", "catalysts", "risks"]

            for line in text.strip().split('\n'):
                line = line.strip()
                if not line or not line[0].isdigit():
                    continue

                # Remove number prefix
                question = line.split('.', 1)[1].strip() if '.' in line else line

                # Assign category based on keywords
                category = "general"
                if any(word in question.lower() for word in ['earnings', 'revenue', 'profit', 'financial']):
                    category = "earnings"
                elif any(word in question.lower() for word in ['competitor', 'market share', 'vs', 'versus']):
                    category = "competitive"
                elif any(word in question.lower() for word in ['industry', 'sector', 'trend', 'market']):
                    category = "industry"
                elif any(word in question.lower() for word in ['catalyst', 'event', 'launch', 'conference', 'upcoming']):
                    category = "catalysts"
                elif any(word in question.lower() for word in ['risk', 'threat', 'challenge', 'concern']):
                    category = "risks"

                questions.append(ResearchQuestion(
                    question=question,
                    category=category,
                    priority=1  # All high priority for now
                ))

            return questions[:max_questions]

        except Exception as e:
            print(f"Error generating questions: {e}")
            # Fallback questions
            return [
                ResearchQuestion(f"What are {ticker}'s latest earnings results?", "earnings", 1),
                ResearchQuestion(f"What is {ticker}'s competitive position?", "competitive", 1),
                ResearchQuestion(f"What are the key trends in {ticker}'s industry?", "industry", 1),
                ResearchQuestion(f"What catalysts could impact {ticker}'s stock price?", "catalysts", 1),
                ResearchQuestion(f"What are the main risks facing {ticker}?", "risks", 1),
            ]

    def _synthesize_findings(
        self,
        ticker: str,
        articles: List[Article]
    ) -> str:
        """
        Use LLM to synthesize research findings.

        Args:
            ticker: Stock ticker
            articles: List of Article objects

        Returns:
            Synthesized summary
        """
        # Combine article content (limit to avoid token limits)
        content = []
        total_words = 0
        max_words = 10000  # Limit to avoid token overflow

        for article in articles:
            if total_words + article.word_count > max_words:
                break
            content.append(f"### {article.title} ({article.source})\n{article.content[:2000]}")
            total_words += article.word_count

        combined_content = "\n\n".join(content)

        prompt = f"""Synthesize the following research articles about {ticker} into a concise investment research summary.

Focus on:
1. Recent financial performance
2. Competitive positioning
3. Industry trends
4. Upcoming catalysts
5. Key risks

Articles:
{combined_content}

Provide a structured summary (500 words max)."""

        try:
            if self.use_anthropic:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return response.choices[0].message.content

        except Exception as e:
            print(f"Error synthesizing findings: {e}")
            return ""


if __name__ == "__main__":
    # Test autonomous researcher
    print("=" * 80)
    print("TESTING AUTONOMOUS RESEARCHER")
    print("=" * 80)

    try:
        researcher = AutonomousResearcher()

        # Research NVDA
        report = researcher.research_stock(
            ticker="NVDA",
            articles_per_question=2,  # Fewer articles for testing
            max_questions=3  # Fewer questions for testing
        )

        print(f"\n{'='*80}")
        print("RESEARCH REPORT SUMMARY")
        print(f"{'='*80}")
        print(f"Ticker: {report.ticker}")
        print(f"Questions: {len(report.questions)}")
        print(f"Articles: {len(report.articles)}")
        print(f"Total Words: {report.total_words:,}")
        print(f"Sources: {', '.join(report.sources)}")

        print(f"\n{'='*80}")
        print("[SUCCESS] Autonomous Researcher Working!")
        print(f"{'='*80}")

    except ValueError as e:
        print(f"\n[ERROR] {e}")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file")
