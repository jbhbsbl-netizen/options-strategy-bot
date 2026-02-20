"""
Portfolio scanner that autonomously finds best covered call opportunities
across multiple tickers and all expiration dates.
"""
from typing import List, Dict, Optional
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time


@dataclass
class OpportunityScore:
    """Scored covered call opportunity."""
    ticker: str
    stock_price: float
    strike: float
    expiration: str
    days_to_exp: int
    premium: float
    delta: float
    theta: float
    score: float
    annual_return: float
    risk_reward_ratio: float


class PortfolioScanner:
    """Scans multiple tickers to find best covered call opportunities."""

    def __init__(self, data_client, strategy_analyzer):
        self.data_client = data_client
        self.strategy_analyzer = strategy_analyzer

    def scan_ticker(
        self,
        ticker: str,
        risk_preference: str = "balanced"
    ) -> Optional[OpportunityScore]:
        """
        Scan a single ticker for best covered call opportunity.

        Args:
            ticker: Stock symbol
            risk_preference: User's risk preference

        Returns:
            Best opportunity for this ticker, or None if error/no options
        """
        try:
            print(f"Scanning {ticker}...")

            # Get stock data
            stock_price = self.data_client.get_stock_price(ticker)
            volatility = self.data_client.get_historical_volatility(ticker, days=30)

            # Get ALL options (no date restrictions)
            options_chain = self.data_client.get_options_chain(
                ticker,
                option_type="call",
                min_expiration_days=1,
                max_expiration_days=365  # Get all available
            )

            if options_chain.empty:
                print(f"  No options for {ticker}")
                return None

            # Calculate Greeks
            from calculations.greeks import add_greeks_to_chain
            options_with_greeks = add_greeks_to_chain(
                options_chain,
                stock_price=stock_price,
                volatility=volatility
            )

            # Find best opportunity using scoring
            best = self._score_opportunities(
                ticker=ticker,
                stock_price=stock_price,
                options_df=options_with_greeks,
                risk_preference=risk_preference
            )

            print(f"  Best: ${best.strike} exp {best.expiration} (score: {best.score:.2f})")
            return best

        except Exception as e:
            print(f"  Error scanning {ticker}: {e}")
            return None

    def scan_multiple(
        self,
        tickers: List[str],
        risk_preference: str = "balanced",
        max_workers: int = 5
    ) -> List[OpportunityScore]:
        """
        Scan multiple tickers in parallel.

        Args:
            tickers: List of stock symbols
            risk_preference: User's risk preference
            max_workers: Number of parallel workers

        Returns:
            List of opportunities sorted by score (best first)
        """
        opportunities = []

        # Scan in parallel for speed
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scan_ticker, ticker, risk_preference): ticker
                for ticker in tickers
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    opportunities.append(result)

        # Sort by score (highest first)
        opportunities.sort(key=lambda x: x.score, reverse=True)
        return opportunities

    def _score_opportunities(
        self,
        ticker: str,
        stock_price: float,
        options_df: pd.DataFrame,
        risk_preference: str
    ) -> OpportunityScore:
        """
        Score all options for a ticker and return the best one.

        Scoring factors:
        - Premium yield (annual return %)
        - Delta (target ~0.30 for balanced)
        - Time to expiration (prefer 30-60 days)
        - Theta decay rate
        """
        df = options_df.copy()

        # Calculate scoring metrics
        df['premium_yield'] = (df['price'] / stock_price) * 100  # % of stock price
        df['annual_return'] = (df['premium_yield'] / df['days_to_exp']) * 365

        # Delta score (prefer 0.25-0.35 for balanced)
        if risk_preference == "conservative":
            target_delta = 0.15
        elif risk_preference == "aggressive":
            target_delta = 0.45
        else:  # balanced
            target_delta = 0.30

        df['delta_score'] = 1 - abs(df['delta'] - target_delta)
        df['delta_score'] = df['delta_score'].clip(lower=0)

        # Time score (prefer 30-60 day window)
        df['time_score'] = df['days_to_exp'].apply(
            lambda x: 1.0 if 30 <= x <= 60 else
                     0.8 if 20 <= x <= 90 else
                     0.6 if 10 <= x <= 120 else
                     0.4
        )

        # Theta score (higher absolute theta is better)
        df['theta_score'] = abs(df['theta']) / abs(df['theta'].max())

        # Premium score (higher is better, but normalize)
        df['premium_score'] = df['annual_return'] / df['annual_return'].max()

        # Combined score (weighted)
        df['score'] = (
            df['premium_score'] * 0.35 +      # 35% weight on returns
            df['delta_score'] * 0.30 +        # 30% weight on delta
            df['time_score'] * 0.20 +         # 20% weight on time window
            df['theta_score'] * 0.15          # 15% weight on theta
        ) * 100  # Scale to 0-100

        # Get best scored option
        best_idx = df['score'].idxmax()
        best = df.loc[best_idx]

        # Calculate risk/reward ratio
        max_profit = (best['strike'] - stock_price) * 100 + best['price'] * 100
        max_loss = stock_price * 100 - best['price'] * 100
        risk_reward = max_profit / max_loss if max_loss > 0 else 0

        return OpportunityScore(
            ticker=ticker,
            stock_price=stock_price,
            strike=float(best['strike']),
            expiration=str(best['expiration']),
            days_to_exp=int(best['days_to_exp']),
            premium=float(best['price']),
            delta=float(best['delta']),
            theta=float(best['theta']),
            score=float(best['score']),
            annual_return=float(best['annual_return']),
            risk_reward_ratio=risk_reward
        )


# Default watchlist of popular, liquid stocks
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "TSLA", "META", "AMD", "NFLX", "DIS",
    "SPY", "QQQ", "IWM"  # ETFs
]


if __name__ == "__main__":
    from data.alpaca_client import AlpacaClient
    from analysis.strategy_analyzer import StrategyAnalyzer

    print("Testing Portfolio Scanner...\n")

    try:
        client = AlpacaClient()
        analyzer = StrategyAnalyzer()
        scanner = PortfolioScanner(client, analyzer)

        # Test with a few tickers
        test_tickers = ["AAPL", "MSFT", "NVDA"]

        print(f"Scanning {len(test_tickers)} tickers...\n")
        opportunities = scanner.scan_multiple(test_tickers, risk_preference="balanced")

        print(f"\n{'='*80}")
        print("TOP OPPORTUNITIES:")
        print(f"{'='*80}\n")

        for i, opp in enumerate(opportunities[:5], 1):
            print(f"{i}. {opp.ticker} @ ${opp.stock_price:.2f}")
            print(f"   Strike: ${opp.strike:.2f} | Exp: {opp.expiration} ({opp.days_to_exp}d)")
            print(f"   Premium: ${opp.premium:.2f} | Delta: {opp.delta:.3f}")
            print(f"   Annual Return: {opp.annual_return:.1f}% | Score: {opp.score:.1f}")
            print()

    except Exception as e:
        print(f"Error: {e}")
