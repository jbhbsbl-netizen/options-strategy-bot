"""
Research Agent - Fetches news, fundamentals, and market data for thesis generation.
"""
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import yfinance as yf


@dataclass
class CompanyResearch:
    """Comprehensive research data for a company."""
    ticker: str
    company_name: str
    current_price: float

    # Recent performance
    price_change_1d: float
    price_change_1w: float
    price_change_1m: float
    volume_avg_10d: float

    # Fundamentals
    market_cap: float
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    revenue_growth: Optional[float]
    profit_margin: Optional[float]
    debt_to_equity: Optional[float]

    # News and sentiment
    recent_news: List[Dict]
    analyst_recommendation: Optional[str]
    target_price: Optional[float]

    # Upcoming events
    next_earnings_date: Optional[str]

    # Options market signals
    implied_volatility: float
    put_call_ratio: Optional[float]


class ResearchAgent:
    """Fetches comprehensive research data for stock analysis."""

    def __init__(self, alpaca_client=None):
        self.alpaca_client = alpaca_client

    def research_ticker(self, ticker: str) -> CompanyResearch:
        """
        Gather comprehensive research data for a ticker.

        Args:
            ticker: Stock symbol

        Returns:
            CompanyResearch object with all gathered data
        """
        print(f"Researching {ticker}...")

        # Get stock data from yfinance
        stock = yf.Ticker(ticker)
        info = stock.info

        # Recent price action
        hist = stock.history(period="1mo")
        current_price = float(hist['Close'].iloc[-1])

        price_change_1d = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        price_change_1w = ((current_price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100 if len(hist) >= 5 else 0
        price_change_1m = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100

        volume_avg = hist['Volume'].tail(10).mean()

        # Fundamentals
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE')
        forward_pe = info.get('forwardPE')
        peg_ratio = info.get('pegRatio')
        profit_margin = info.get('profitMargins')
        revenue_growth = info.get('revenueGrowth')
        debt_to_equity = info.get('debtToEquity')

        # Analyst data
        target_price = info.get('targetMeanPrice')
        recommendation = info.get('recommendationKey', '').upper()

        # News (yfinance has limited news, but we'll use what's available)
        try:
            news = stock.news[:5] if hasattr(stock, 'news') else []
            recent_news = [
                {
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', ''),
                    'published': item.get('providerPublishTime', 0)
                }
                for item in news
            ]
        except:
            recent_news = []

        # Earnings date
        try:
            earnings_dates = stock.earnings_dates
            if earnings_dates is not None and not earnings_dates.empty:
                next_earnings = earnings_dates.index[0].strftime('%Y-%m-%d')
            else:
                next_earnings = None
        except:
            next_earnings = None

        # IV from our alpaca client
        if self.alpaca_client:
            try:
                iv = self.alpaca_client.get_historical_volatility(ticker, days=30)
            except:
                iv = 0.25  # default
        else:
            iv = 0.25

        # Put/call ratio (would need options data - placeholder for now)
        put_call_ratio = None

        return CompanyResearch(
            ticker=ticker,
            company_name=info.get('longName', ticker),
            current_price=current_price,
            price_change_1d=price_change_1d,
            price_change_1w=price_change_1w,
            price_change_1m=price_change_1m,
            volume_avg_10d=volume_avg,
            market_cap=market_cap,
            pe_ratio=pe_ratio,
            forward_pe=forward_pe,
            peg_ratio=peg_ratio,
            revenue_growth=revenue_growth,
            profit_margin=profit_margin,
            debt_to_equity=debt_to_equity,
            recent_news=recent_news,
            analyst_recommendation=recommendation,
            target_price=target_price,
            next_earnings_date=next_earnings,
            implied_volatility=iv,
            put_call_ratio=put_call_ratio
        )

    def format_research_summary(self, research: CompanyResearch) -> str:
        """Format research into a readable summary for LLM."""

        summary = f"""
# Research Summary: {research.ticker} ({research.company_name})

## Current Price & Performance
- Current Price: ${research.current_price:.2f}
- 1-Day Change: {research.price_change_1d:+.2f}%
- 1-Week Change: {research.price_change_1w:+.2f}%
- 1-Month Change: {research.price_change_1m:+.2f}%
- Average Volume (10d): {research.volume_avg_10d:,.0f}

## Fundamentals
- Market Cap: ${research.market_cap/1e9:.1f}B
- P/E Ratio: {f"{research.pe_ratio:.2f}" if research.pe_ratio else "N/A"}
- Forward P/E: {f"{research.forward_pe:.2f}" if research.forward_pe else "N/A"}
- PEG Ratio: {f"{research.peg_ratio:.2f}" if research.peg_ratio else "N/A"}
- Profit Margin: {f"{research.profit_margin*100:.1f}%" if research.profit_margin else "N/A"}
- Revenue Growth: {f"{research.revenue_growth*100:.1f}%" if research.revenue_growth else "N/A"}
- Debt/Equity: {f"{research.debt_to_equity:.2f}" if research.debt_to_equity else "N/A"}

## Analyst View
- Recommendation: {research.analyst_recommendation or 'N/A'}
- Target Price: {f"${research.target_price:.2f}" if research.target_price else "N/A"}
- Upside to Target: {f"{((research.target_price/research.current_price - 1)*100):+.1f}%" if research.target_price else "N/A"}

## Options Market
- Implied Volatility: {research.implied_volatility*100:.1f}%
- Put/Call Ratio: {f"{research.put_call_ratio:.2f}" if research.put_call_ratio else "N/A"}

## Recent News Headlines
"""

        if research.recent_news:
            for i, news in enumerate(research.recent_news[:3], 1):
                summary += f"{i}. {news['title']} ({news['publisher']})\n"
        else:
            summary += "No recent news available\n"

        if research.next_earnings_date:
            summary += f"\n## Upcoming Events\n- Next Earnings: {research.next_earnings_date}\n"

        return summary


if __name__ == "__main__":
    print("Testing Research Agent...\n")

    agent = ResearchAgent()
    research = agent.research_ticker("AAPL")

    print(agent.format_research_summary(research))
