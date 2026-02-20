"""
yfinance client for fetching stock data, options chains, and news.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List


class YFinanceClient:
    """Client for fetching stock and options data from Yahoo Finance."""

    def __init__(self):
        """Initialize yfinance client (no API key needed)."""
        pass

    def get_stock_price(self, ticker: str) -> float:
        """
        Get current stock price.

        Args:
            ticker: Stock symbol (e.g., "NVDA")

        Returns:
            Current stock price
        """
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        return float(data['Close'].iloc[-1])

    def get_stock_data(self, ticker: str) -> Dict:
        """
        Get comprehensive stock data including price, fundamentals, and info.

        Args:
            ticker: Stock symbol

        Returns:
            Dictionary with stock data
        """
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period="1d")

        if history.empty:
            raise ValueError(f"No data found for ticker {ticker}")

        current_price = float(history['Close'].iloc[-1])
        prev_close = float(info.get('previousClose', current_price))

        return {
            "ticker": ticker,
            "current_price": current_price,
            "previous_close": prev_close,
            "price_change": current_price - prev_close,
            "price_change_pct": ((current_price - prev_close) / prev_close * 100) if prev_close else 0,
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE', None),
            "forward_pe": info.get('forwardPE', None),
            "revenue_growth": info.get('revenueGrowth', None),
            "profit_margin": info.get('profitMargins', None),
            "target_price": info.get('targetMeanPrice', None),
            "52_week_high": info.get('fiftyTwoWeekHigh', None),
            "52_week_low": info.get('fiftyTwoWeekLow', None),
            "volume": int(history['Volume'].iloc[-1]) if 'Volume' in history else 0,
            "avg_volume": info.get('averageVolume', 0),
        }

    def get_price_history(self, ticker: str, period: str = "3mo") -> pd.DataFrame:
        """
        Get historical price data.

        Args:
            ticker: Stock symbol
            period: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max")

        Returns:
            DataFrame with OHLCV data
        """
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)

        if history.empty:
            raise ValueError(f"No historical data found for {ticker}")

        return history

    def get_news(self, ticker: str, max_items: int = 10) -> List[Dict]:
        """
        Get recent news headlines for a stock.

        Args:
            ticker: Stock symbol
            max_items: Maximum number of news items to return

        Returns:
            List of news items with title, summary, publisher, link, publish_time
        """
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            return []

        formatted_news = []
        for item in news[:max_items]:
            content = item.get('content', {})

            # Extract title and summary
            title = content.get('title', 'No title')
            summary = content.get('summary', '')

            # Extract publisher info
            provider = content.get('provider', {})
            publisher = provider.get('displayName', 'Unknown')

            # Extract URL
            canonical = content.get('canonicalUrl', {})
            link = canonical.get('url', '')

            # Extract publish time
            pub_date = content.get('pubDate', '')
            try:
                publish_time = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            except:
                publish_time = datetime.now()

            formatted_news.append({
                "title": title,
                "summary": summary,
                "publisher": publisher,
                "link": link,
                "publish_time": publish_time,
            })

        return formatted_news

    def get_options_chain(
        self,
        ticker: str,
        expiration: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch options chain for a specific expiration date.

        Args:
            ticker: Stock symbol
            expiration: Expiration date (YYYY-MM-DD format). If None, uses nearest expiration.

        Returns:
            DataFrame with options data including strike, bid, ask, volume, OI, IV
        """
        stock = yf.Ticker(ticker)

        # Get available expiration dates
        expirations = stock.options

        if not expirations:
            raise ValueError(f"No options data available for {ticker}")

        # Use provided expiration or first available
        if expiration is None:
            expiration = expirations[0]
        elif expiration not in expirations:
            raise ValueError(f"Expiration {expiration} not available. Available: {expirations}")

        # Get options chain
        chain = stock.option_chain(expiration)

        # Combine calls and puts
        calls = chain.calls.copy()
        calls['type'] = 'call'

        puts = chain.puts.copy()
        puts['type'] = 'put'

        # Combine and clean
        options = pd.concat([calls, puts], ignore_index=True)

        # Rename columns to standard format
        options = options.rename(columns={
            'contractSymbol': 'symbol',
            'lastTradeDate': 'last_trade_date',
            'lastPrice': 'last',
            'openInterest': 'open_interest',
            'impliedVolatility': 'iv',
            'inTheMoney': 'in_the_money'
        })

        # Add expiration date
        options['expiration'] = expiration

        # Calculate days to expiration
        exp_date = datetime.strptime(expiration, '%Y-%m-%d')
        options['days_to_exp'] = (exp_date.date() - datetime.now().date()).days

        # Calculate mid price
        options['mid'] = (options['bid'] + options['ask']) / 2

        # Calculate bid-ask spread percentage
        options['spread_pct'] = ((options['ask'] - options['bid']) / options['mid'] * 100).round(2)

        # Select relevant columns
        columns = [
            'symbol', 'type', 'strike', 'expiration', 'days_to_exp',
            'bid', 'ask', 'mid', 'last', 'volume', 'open_interest',
            'iv', 'spread_pct', 'in_the_money'
        ]

        return options[columns].sort_values(['type', 'strike'])

    def get_all_expirations(self, ticker: str) -> List[str]:
        """
        Get all available expiration dates for options.

        Args:
            ticker: Stock symbol

        Returns:
            List of expiration dates in YYYY-MM-DD format
        """
        stock = yf.Ticker(ticker)
        return list(stock.options)

    def get_options_chain_all_expirations(self, ticker: str, max_expirations: int = 10) -> Dict[str, pd.DataFrame]:
        """
        Get options chain for multiple expirations.

        Args:
            ticker: Stock symbol
            max_expirations: Maximum number of expirations to fetch (default 10)

        Returns:
            Dict mapping expiration dates to DataFrames of options contracts
        """
        stock = yf.Ticker(ticker)
        expirations = stock.options[:max_expirations]  # Limit to avoid too much data

        chains = {}
        for expiration in expirations:
            try:
                chain_df = self.get_options_chain(ticker, expiration)

                # Rename 'type' to 'option_type' for contract picker
                chain_df = chain_df.rename(columns={'type': 'option_type'})

                # Ensure required columns exist
                if 'impliedVolatility' not in chain_df.columns and 'iv' in chain_df.columns:
                    chain_df['impliedVolatility'] = chain_df['iv']

                chains[expiration] = chain_df
            except Exception as e:
                print(f"  Warning: Could not fetch {expiration}: {e}")
                continue

        return chains

    def get_historical_volatility(self, ticker: str, days: int = 30) -> float:
        """
        Calculate historical volatility (annualized).

        Args:
            ticker: Stock symbol
            days: Number of days to look back

        Returns:
            Annualized volatility as decimal (e.g., 0.25 = 25%)
        """
        stock = yf.Ticker(ticker)
        history = stock.history(period=f"{days+10}d")  # Extra buffer

        if history.empty or len(history) < days:
            raise ValueError(f"Insufficient historical data for {ticker}")

        # Calculate daily returns
        returns = history['Close'].pct_change().dropna()

        # Annualize volatility (sqrt(252) for trading days)
        volatility = returns.std() * (252 ** 0.5)

        return float(volatility)

    def get_earnings_date(self, ticker: str) -> Optional[Dict]:
        """
        Get next earnings date and timing information.

        Args:
            ticker: Stock symbol

        Returns:
            Dictionary with:
                - date: Next earnings date (datetime object)
                - date_str: Formatted date string (e.g., "Feb 20, 2026")
                - timing: When earnings announced (BMO/AMC/DMH or None)
                - days_until: Days until earnings
            Returns None if no earnings date available
        """
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar

            if calendar is None:
                return None

            # Handle both dict and DataFrame formats
            if isinstance(calendar, dict):
                earnings_dates = calendar.get('Earnings Date', None)
            elif hasattr(calendar, 'empty') and not calendar.empty and 'Earnings Date' in calendar.index:
                earnings_dates = calendar.loc['Earnings Date']
            else:
                return None

            if earnings_dates is None:
                return None

            # Handle case where there are multiple dates (date range)
            if isinstance(earnings_dates, (list, tuple, pd.Series)):
                # Take the first date (soonest)
                earnings_date = earnings_dates[0] if isinstance(earnings_dates, (list, tuple)) else earnings_dates.iloc[0]
            else:
                earnings_date = earnings_dates

            # Convert to datetime if it's a timestamp
            if isinstance(earnings_date, pd.Timestamp):
                earnings_date = earnings_date.to_pydatetime()
            elif isinstance(earnings_date, str):
                earnings_date = pd.to_datetime(earnings_date).to_pydatetime()

            # Handle both datetime and date objects
            if hasattr(earnings_date, 'date'):
                # It's a datetime object
                earnings_date_only = earnings_date.date()
            else:
                # It's already a date object
                earnings_date_only = earnings_date
                # Convert to datetime for consistency
                earnings_date = datetime.combine(earnings_date, datetime.min.time())

            # Calculate days until earnings
            days_until = (earnings_date_only - datetime.now().date()).days

            # Format date string (e.g., "Feb 20, 2026")
            date_str = earnings_date_only.strftime("%b %d, %Y")

            # Try to determine timing (BMO/AMC/DMH)
            # yfinance doesn't always provide this, so we'll extract from hour if available
            timing = None
            if hasattr(earnings_date, 'hour'):
                hour = earnings_date.hour
                if hour < 9:
                    timing = "BMO"  # Before Market Open
                elif hour >= 16:
                    timing = "AMC"  # After Market Close
                elif 9 <= hour < 16:
                    timing = "DMH"  # During Market Hours

            return {
                "date": earnings_date,
                "date_str": date_str,
                "timing": timing,
                "days_until": days_until
            }

        except Exception as e:
            print(f"Warning: Could not fetch earnings date for {ticker}: {e}")
            return None

    def get_earnings_calendar(self, tickers: List[str]) -> List[Dict]:
        """
        Get earnings dates for multiple tickers (for earnings ticker display).

        Args:
            tickers: List of stock symbols

        Returns:
            List of dicts with ticker, date, date_str, timing, days_until
            Sorted by date (soonest first)
        """
        earnings_list = []

        for ticker in tickers:
            earnings_info = self.get_earnings_date(ticker)
            if earnings_info:
                earnings_list.append({
                    "ticker": ticker,
                    **earnings_info
                })

        # Sort by date (soonest first)
        earnings_list.sort(key=lambda x: x['date'])

        return earnings_list


if __name__ == "__main__":
    # Test the client
    client = YFinanceClient()

    ticker = "NVDA"
    print(f"\n{'='*60}")
    print(f"Testing yfinance client with {ticker}")
    print(f"{'='*60}\n")

    # Test stock data
    print("1. Stock Data:")
    stock_data = client.get_stock_data(ticker)
    print(f"   Price: ${stock_data['current_price']:.2f}")
    print(f"   Change: ${stock_data['price_change']:.2f} ({stock_data['price_change_pct']:+.2f}%)")
    print(f"   Market Cap: ${stock_data['market_cap']/1e9:.1f}B")
    print(f"   P/E Ratio: {stock_data['pe_ratio']:.2f}" if stock_data['pe_ratio'] else "   P/E Ratio: N/A")

    # Test news
    print("\n2. Recent News:")
    news = client.get_news(ticker, max_items=3)
    for i, item in enumerate(news, 1):
        print(f"   {i}. {item['title'][:60]}...")
        print(f"      {item['publisher']} - {item['publish_time'].strftime('%Y-%m-%d %H:%M')}")

    # Test expirations
    print("\n3. Available Option Expirations:")
    expirations = client.get_all_expirations(ticker)
    print(f"   Found {len(expirations)} expirations")
    print(f"   First 5: {expirations[:5]}")

    # Test options chain
    print(f"\n4. Options Chain (Expiration: {expirations[0]}):")
    chain = client.get_options_chain(ticker, expirations[0])
    print(f"   Total contracts: {len(chain)}")
    print(f"   Calls: {len(chain[chain['type']=='call'])}")
    print(f"   Puts: {len(chain[chain['type']=='put'])}")

    # Show sample calls near ATM
    stock_price = stock_data['current_price']
    calls = chain[chain['type'] == 'call']
    atm_calls = calls[(calls['strike'] >= stock_price * 0.95) & (calls['strike'] <= stock_price * 1.05)]

    print(f"\n5. Sample Calls Near ATM (Stock: ${stock_price:.2f}):")
    print(atm_calls[['strike', 'bid', 'ask', 'mid', 'volume', 'open_interest', 'iv', 'spread_pct']].head(5).to_string(index=False))

    # Test historical volatility
    print(f"\n6. Historical Volatility:")
    hist_vol = client.get_historical_volatility(ticker, days=30)
    print(f"   30-day HV: {hist_vol*100:.1f}%")

    print(f"\n{'='*60}")
    print("[SUCCESS] All tests passed!")
    print(f"{'='*60}\n")
