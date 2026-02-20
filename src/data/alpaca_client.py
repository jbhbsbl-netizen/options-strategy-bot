"""
Alpaca API client for fetching options chains and market data.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from dotenv import load_dotenv

load_dotenv()


class AlpacaClient:
    """Client for fetching options and stock data from Alpaca."""

    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        if not self.api_key or not self.secret_key:
            raise ValueError(
                "Missing Alpaca credentials. Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file"
            )

        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)

    def get_stock_price(self, ticker: str) -> float:
        """Get current stock price using yfinance for accuracy."""
        try:
            # Use yfinance for most accurate real-time price
            import yfinance as yf

            stock = yf.Ticker(ticker)
            data = stock.history(period="1d", interval="1m")

            if not data.empty:
                # Get the most recent close price
                current_price = float(data['Close'].iloc[-1])
                print(f"DEBUG: yfinance price for {ticker}: ${current_price:.2f}")
                return current_price
            else:
                print(f"DEBUG: No yfinance data, falling back to Alpaca...")
                # Fallback to Alpaca
                from alpaca.data.requests import StockLatestTradeRequest
                trade_request = StockLatestTradeRequest(symbol_or_symbols=ticker)
                trade = self.data_client.get_stock_latest_trade(trade_request)[ticker]
                print(f"DEBUG: Alpaca trade price: ${trade.price}")
                return float(trade.price)

        except Exception as e:
            print(f"Error fetching stock price: {e}")
            # Final fallback
            try:
                from alpaca.data.requests import StockLatestTradeRequest
                trade_request = StockLatestTradeRequest(symbol_or_symbols=ticker)
                trade = self.data_client.get_stock_latest_trade(trade_request)[ticker]
                return float(trade.price)
            except:
                raise Exception(f"Could not fetch price for {ticker}")

    def get_options_chain(
        self,
        ticker: str,
        option_type: str = "call",
        min_expiration_days: int = 7,
        max_expiration_days: int = 60
    ) -> pd.DataFrame:
        """
        Fetch options chain for a ticker.

        Args:
            ticker: Stock symbol
            option_type: "call" or "put"
            min_expiration_days: Minimum days to expiration
            max_expiration_days: Maximum days to expiration

        Returns:
            DataFrame with columns: symbol, strike, expiration, bid, ask, mid_price
        """
        # Calculate date range
        today = datetime.now().date()
        min_exp = today + timedelta(days=min_expiration_days)
        max_exp = today + timedelta(days=max_expiration_days)

        # Fetch options contracts
        request = GetOptionContractsRequest(
            underlying_symbols=[ticker],
            status="active",
            expiration_date_gte=min_exp.isoformat(),
            expiration_date_lte=max_exp.isoformat(),
            type=option_type
        )

        try:
            contracts = self.trading_client.get_option_contracts(request)
            print(f"DEBUG: Received {type(contracts)} from API")
            print(f"DEBUG: Contracts value: {contracts if not isinstance(contracts, list) or len(contracts) < 3 else f'{len(contracts)} items'}")
        except Exception as e:
            print(f"Error fetching contracts: {e}")
            return pd.DataFrame()

        if not contracts:
            print("DEBUG: No contracts returned")
            return pd.DataFrame()

        # Parse into DataFrame
        data = []

        # Extract the list of contracts from the response object
        if hasattr(contracts, 'option_contracts'):
            contracts_list = contracts.option_contracts
        elif isinstance(contracts, dict):
            contracts_list = contracts.get('option_contracts', [])
        elif isinstance(contracts, list):
            contracts_list = contracts
        else:
            print(f"DEBUG: Unexpected contracts type: {type(contracts)}")
            return pd.DataFrame()

        print(f"DEBUG: Processing {len(contracts_list)} contracts")

        for contract in contracts_list:
            try:
                # Handle both object attributes and dict access
                if hasattr(contract, 'symbol'):
                    data.append({
                        "symbol": contract.symbol,
                        "strike": float(contract.strike_price),
                        "expiration": contract.expiration_date,
                        "type": contract.type,
                        "underlying": contract.underlying_symbol,
                    })
                elif isinstance(contract, dict):
                    data.append({
                        "symbol": contract.get('symbol', ''),
                        "strike": float(contract.get('strike_price', 0)),
                        "expiration": contract.get('expiration_date', ''),
                        "type": contract.get('type', ''),
                        "underlying": contract.get('underlying_symbol', ''),
                    })
            except Exception as e:
                print(f"Error parsing contract: {e}, contract type: {type(contract)}")
                continue

        if not data:
            print("DEBUG: No data parsed from contracts")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        print(f"DEBUG: Created DataFrame with {len(df)} rows and columns: {list(df.columns)}")

        # Get latest quotes for pricing (this would need snapshot API in production)
        # For now, we'll add placeholder bid/ask that we'll populate with real data
        df["bid"] = 0.0  # Placeholder - need to fetch from options quotes API
        df["ask"] = 0.0  # Placeholder
        df["mid_price"] = 0.0

        return df.sort_values(["expiration", "strike"]) if not df.empty else df

    def get_historical_volatility(self, ticker: str, days: int = 30) -> float:
        """
        Calculate historical volatility (annualized).

        Args:
            ticker: Stock symbol
            days: Number of days to look back

        Returns:
            Annualized volatility as decimal (e.g., 0.25 = 25%)
        """
        end = datetime.now()
        start = end - timedelta(days=days + 10)  # Extra buffer

        request = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=TimeFrame.Day,
            start=start,
            end=end
        )

        bars = self.data_client.get_stock_bars(request)[ticker]

        # Calculate daily returns
        prices = [bar.close for bar in bars]
        returns = pd.Series(prices).pct_change().dropna()

        # Annualize volatility (sqrt(252) for trading days)
        volatility = returns.std() * (252 ** 0.5)

        return float(volatility)


if __name__ == "__main__":
    # Test the client
    client = AlpacaClient()

    ticker = "AAPL"
    print(f"\nFetching data for {ticker}...")

    price = client.get_stock_price(ticker)
    print(f"Current price: ${price:.2f}")

    vol = client.get_historical_volatility(ticker)
    print(f"30-day historical volatility: {vol*100:.1f}%")

    chain = client.get_options_chain(ticker, option_type="call")
    print(f"\nFound {len(chain)} call options:")
    print(chain.head(10))
