# Free Data APIs for Options Strategy Bot

## 🆓 Free APIs You Can Use

### 1. **Alpha Vantage** (Recommended)
**What you get:**
- Stock prices (real-time with delays)
- Fundamental data (earnings, income statements, balance sheets)
- Technical indicators
- Economic indicators
- Company overview

**Free Tier:**
- 25 API calls per day
- 5 API calls per minute
- Good for fundamental analysis

**API Key:** https://www.alphavantage.co/support/#api-key

**Example Use:**
```python
import requests

API_KEY = "your_key_here"
symbol = "NVDA"

# Get company overview
url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={API_KEY}"
data = requests.get(url).json()

print(data['MarketCapitalization'])
print(data['EPS'])
print(data['PERatio'])
```

---

### 2. **Financial Modeling Prep (FMP)**
**What you get:**
- Stock prices
- Financial statements (income, balance sheet, cash flow)
- Key metrics (P/E, P/B, ROE, etc.)
- Insider trading data
- SEC filings
- Earnings calendar
- Stock splits & dividends

**Free Tier:**
- 250 requests per day
- Real-time data (15-min delay)
- Very comprehensive

**API Key:** https://site.financialmodelingprep.com/developer/docs

**Example Use:**
```python
API_KEY = "your_key_here"
symbol = "NVDA"

# Get key metrics
url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?apikey={API_KEY}"
data = requests.get(url).json()

print(data[0]['peRatio'])
print(data[0]['revenuePerShare'])
```

---

### 3. **FRED (Federal Reserve Economic Data)**
**What you get:**
- Economic indicators (GDP, unemployment, inflation)
- Interest rates
- Treasury yields
- Market sentiment indicators
- No API limits!

**API Key:** https://fred.stlouisfed.org/docs/api/api_key.html

**Example Use:**
```python
from fredapi import Fred

fred = Fred(api_key='your_key_here')

# Get 10-year treasury yield (risk-free rate for options)
treasury_yield = fred.get_series_latest_release('DGS10')
print(f"10Y Treasury: {treasury_yield.iloc[-1]:.2f}%")

# Get VIX (market volatility)
vix = fred.get_series_latest_release('VIXCLS')
print(f"VIX: {vix.iloc[-1]:.2f}")
```

---

### 4. **SEC EDGAR API** (No key needed!)
**What you get:**
- Company filings (10-K, 10-Q, 8-K)
- Insider transactions
- Company facts
- 100% free, no limits

**API:** https://www.sec.gov/edgar/sec-api-documentation

**Example Use:**
```python
import requests

headers = {'User-Agent': 'your_email@example.com'}
cik = "0001045810"  # NVIDIA CIK

url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
data = requests.get(url, headers=headers).json()

# Get revenue, earnings, etc from official filings
```

---

### 5. **Polygon.io FREE Tier**
**What you get (free):**
- Stocks, options, forex, crypto
- **Delayed data** (15 minutes)
- Historical data
- Aggregates (OHLC bars)

**Free Tier:**
- 5 API calls per minute
- Delayed quotes
- Good for backtesting

**API Key:** https://polygon.io/dashboard/signup

---

### 6. **IEX Cloud**
**What you get:**
- Stock prices
- Company info
- News
- Financials

**Free Tier:**
- 50,000 messages per month
- Core data included

**API Key:** https://iexcloud.io/cloud-login#/register

---

### 7. **Finnhub**
**What you get:**
- Stock prices
- Company news
- Earnings calendar
- Economic calendar
- Insider transactions

**Free Tier:**
- 60 API calls per minute
- Real-time data

**API Key:** https://finnhub.io/register

---

## 🎯 **Recommended Setup for Your Bot:**

### Core Data Stack:
1. **yfinance** - Stock prices, options chains, basic news (FREE, no key)
2. **Alpha Vantage** - Fundamental data, earnings (FREE, 25 calls/day)
3. **FMP** - Financial statements, metrics (FREE, 250 calls/day)
4. **FRED** - Economic indicators, risk-free rate (FREE, unlimited)
5. **News Scraper** - Full article content (FREE, built-in)

### Optional Upgrades:
- **Polygon.io** ($200/mo) - Real-time options data
- **Finnhub Pro** ($60/mo) - More news sources
- **Alpha Vantage Premium** ($50/mo) - More API calls

---

## 📊 **What You Can Add to the Bot:**

### With Alpha Vantage:
- Quarterly earnings data
- Revenue growth trends
- Profit margins over time
- Cash flow analysis

### With FMP:
- Insider buying/selling (bullish/bearish signal)
- Upcoming earnings dates
- Historical P/E trends
- Debt ratios

### With FRED:
- Risk-free rate for Greeks calculation (use 10Y Treasury)
- VIX for market volatility context
- Economic indicators (GDP, unemployment)

### With News Scraper (built):
- Full article analysis (2000+ words vs 100-char summary)
- Sentiment analysis on articles
- Extract key facts, numbers, quotes

---

## 💡 **Implementation Priority:**

**Phase 1 (Now):**
- ✅ yfinance (stock, options, news summaries)
- ✅ News scraper (full articles)
- ✅ Basic fundamentals from yfinance

**Phase 2 (Next):**
- ⏭️ Alpha Vantage (earnings data, better fundamentals)
- ⏭️ FRED (risk-free rate for accurate Greeks)
- ⏭️ FMP (insider trades, earnings calendar)

**Phase 3 (Later):**
- Polygon.io or Alpaca (real-time data when bot proves itself)
- Premium news feeds

---

## 🔑 **How to Get API Keys:**

All free APIs just need email signup:

1. **Alpha Vantage:** https://www.alphavantage.co/support/#api-key
2. **FMP:** https://site.financialmodelingprep.com/developer/docs
3. **FRED:** https://fred.stlouisfed.org/docs/api/api_key.html
4. **Finnhub:** https://finnhub.io/register

Add to your `.env` file:
```
ALPHA_VANTAGE_KEY=your_key_here
FMP_API_KEY=your_key_here
FRED_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
```

---

**Want me to integrate any of these into the bot now?**
