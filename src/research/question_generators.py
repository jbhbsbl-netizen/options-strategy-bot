"""
Question Generators Mixin

Provides hardcoded fallback research questions for each decision phase.
Used by ResearchOrchestrator when autonomous LLM question generation is
disabled or unavailable.
"""
from typing import List, Optional

from src.research.autonomous_researcher import ResearchQuestion


class QuestionGeneratorMixin:
    """Mixin providing hardcoded research question generators for each phase."""

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

        questions.append(ResearchQuestion(
            f"What delta should I target for {direction.lower()} options trades?",
            "contract", 1
        ))

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
        earnings_info: dict
    ) -> List[ResearchQuestion]:
        """
        Generate earnings pattern research questions.
        Only called when earnings is within 30 days.
        """
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
