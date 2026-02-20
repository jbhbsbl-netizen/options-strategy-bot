# Options Data Providers Research (开题调研)

**Research Date:** February 10, 2026
**Purpose:** Find professional-grade options data for real-time quotes, Greeks, IV, volume, open interest

---

## 🎯 What We Need (Minimum Requirements)

To build a **professional-level** options chain, we need:

✅ **Real-Time Quotes:** Live bid/ask prices (not $0.00 placeholders)
✅ **Volume & Open Interest:** Liquidity indicators
✅ **Implied Volatility per Strike:** Market-derived IV (not single historical vol)
✅ **Greeks at Market Prices:** Delta, Gamma, Theta, Vega from actual quotes
✅ **Last Trade Data:** Price, time, size

**Nice to Have:**
- Historical options data for backtesting
- Options chain snapshots (all strikes at once)
- IV rank/percentile calculations
- Multi-leg strategy pricing

---

## 📊 Provider Comparison Matrix

| Provider | Real-Time? | Free Tier? | Cost | Greeks | IV | Volume/OI | Python SDK | Best For |
|----------|-----------|-----------|------|--------|----|-----------|-----------|----- |
| **Alpaca** | ✅ Yes (OPRA) | ⚠️ Limited | $0-$99+/mo | ❌ Calculate | ❌ Calculate | ✅ Yes | ✅ Excellent | All-in-one (data + trading) |
| **Polygon/Massive** | ✅ Yes | ❌ No | ~$200/mo | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Good | Professional analytics |
| **Tradier** | ✅ Yes | ✅ Yes* | Free* | ✅ Yes (ORATS) | ✅ Yes | ✅ Yes | ✅ Good | Free if brokerage account |
| **Interactive Brokers** | ✅ Yes | ⚠️ 100 quotes | $1-10/mo + | ❌ Calculate | ❌ Calculate | ✅ Yes | ✅ Excellent | Serious traders |
| **TastyTrade** | ✅ Yes | ✅ Yes* | Free* | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Unofficial | Free with funded account |
| **yfinance (Yahoo)** | ⚠️ Delayed | ✅ Yes | Free | ❌ No | ⚠️ Per chain | ⚠️ Spotty | ✅ Native | Quick prototypes |
| **Schwab API** | ✅ Yes | ❌ No | Account req | ❌ Calculate | ❌ Calculate | ✅ Yes | ⚠️ New | Schwab clients |

\* = Requires opening brokerage account

---

## 🔬 Detailed Provider Analysis

### 1. Alpaca (Current Provider)

**Status:** ✅ Already integrated
**Sources:** [Alpaca Options Data](https://alpaca.markets/options), [Real-time Options API](https://docs.alpaca.markets/docs/real-time-option-data), [Latest Quotes Endpoint](https://docs.alpaca.markets/reference/optionlatestquotes)

**What You Get:**
- OPRA feed (Options Price Reporting Authority - authoritative source)
- Real-time bid/ask quotes via WebSocket or HTTP
- Volume, open interest, last trade data
- Options contract metadata (strike, expiration, type)

**What You DON'T Get:**
- ❌ Pre-calculated Greeks (you must calculate with Black-Scholes)
- ❌ Implied volatility per option (you must reverse-calculate)
- ❌ Historical options data on free tier

**Pricing:**
- **Free:** Delayed data, limited real-time (IEX feed only)
- **Algo Trader Plus:** $99/mo - Full OPRA real-time for options
- **Enterprise:** Custom pricing for institutional needs

**Python Integration:**
```python
from alpaca.data import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest

# Already have this working!
client = OptionHistoricalDataClient(api_key, secret_key)
request = OptionLatestQuoteRequest(symbol_or_symbols=["AAPL250221C00150000"])
quotes = client.get_option_latest_quote(request)
# Returns: bid, ask, bid_size, ask_size, timestamp
```

**Verdict:**
- ✅ Best if staying with Alpaca for trading execution
- ⚠️ Need to add Greeks calculation layer (use py_vollib)
- ⚠️ Need to calculate IV per strike (reverse Black-Scholes)
- 💰 $99/mo for real-time is reasonable

---

### 2. Polygon.io (now Massive.com)

**Status:** 🆕 Not integrated
**Sources:** [Options Market Data](https://polygon.io/options), [Greeks & IV Blog](https://polygon.io/blog/greeks-and-implied-volatility), [Options Chain Snapshot](https://polygon.io/blog/announcing-options-chain-snapshot-api)

**What You Get:**
- **Full OPRA feed** with real-time quotes
- **Pre-calculated Greeks** (Delta, Gamma, Theta, Vega, Rho)
- **Implied Volatility** per option (market-derived)
- **Options Chain Snapshot** - All strikes at once
- **Historical data** back to 2014 (tick-level)
- Open interest, volume, premium changes

**Pricing:**
- **Starter:** ~$89/mo - Delayed data
- **Developer:** ~$199/mo - Real-time stocks + options
- **Advanced:** ~$399/mo - Full historical + aggregates
- (Exact 2026 pricing not found - check massive.com/pricing)

**Python Integration:**
```python
# Using polygon SDK
from polygon import RESTClient

client = RESTClient(api_key)
snapshot = client.get_snapshot_option(underlying_ticker="AAPL", option_contract="AAPL250221C00150000")
# Returns: greeks (delta, gamma, theta, vega), implied_volatility, bid, ask, last, volume, oi
```

**Verdict:**
- ✅ **Best for analytics** - Greeks & IV pre-calculated
- ✅ Historical data for backtesting
- ⚠️ More expensive than Alpaca alone ($200 vs $99)
- ❌ Still need separate broker for execution (Alpaca, IBKR, etc.)

---

### 3. Tradier (Dark Horse Option)

**Status:** 🆕 Not integrated
**Sources:** [Tradier API Docs](https://docs.tradier.com/), [Market Data](https://docs.tradier.com/docs/market-data), [Options Chains](https://docs.tradier.com/reference/brokerage-api-markets-get-options-chains)

**What You Get:**
- **Real-time** bid/ask/last for options
- **Greeks & IV from ORATS** (Options Research & Technology Services - industry standard)
- Volume, open interest, trade history
- Options chain endpoints
- **Free for brokerage account holders** (no monthly fees)

**The Catch:**
- ⚠️ **Must open Tradier brokerage account** (free to open, no minimum)
- Real-time data ONLY available to account holders
- Non-account holders get no real-time access

**Pricing:**
- **Free** if you have a Tradier brokerage account
- Commission: $0.35/contract (comparable to others)
- No monthly market data fees

**Python Integration:**
```python
import requests

headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}
response = requests.get('https://api.tradier.com/v1/markets/options/chains',
    params={'symbol': 'AAPL', 'expiration': '2025-02-21', 'greeks': 'true'},
    headers=headers
)
# Returns: options with greeks, IV, bid, ask, volume, open_interest
```

**Verdict:**
- ✅ **Best value** - Free real-time data + Greeks if you open account
- ✅ ORATS Greeks (professional quality)
- ⚠️ Requires managing two brokers (Tradier for data, Alpaca for trading?)
- 🤔 Or... use Tradier for both data AND trading?

---

### 4. Interactive Brokers (IBKR)

**Status:** 🆕 Not integrated
**Sources:** [IBKR API](https://www.interactivebrokers.com/en/trading/ib-api.php), [Market Data Pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php), [TWS API](https://interactivebrokers.github.io/tws-api/market_data.html)

**What You Get:**
- **Industry gold standard** for API trading
- Real-time quotes via TWS API
- Options chains with volume/OI
- **100 free snapshot quotes/month**
- Always minimum 100 concurrent streaming lines
- Full cross-asset support (stocks, futures, forex, crypto)

**What You DON'T Get:**
- ❌ No pre-calculated Greeks in API (calculate yourself)
- ❌ No IV per option (reverse-calculate from prices)

**Pricing:**
- **Free tier:** 100 snapshots/month + 100 streaming lines
- **OPRA (US Options):** ~$1-10/month depending on usage
- Professional subscriptions: Higher fees

**Python Integration:**
```python
from ibapi.client import EClient
from ibapi.wrapper import EWrapper

# More complex setup - requires TWS or IB Gateway running
# Can request options data, but Greeks not included
```

**Verdict:**
- ✅ Best for **serious traders** with multi-asset needs
- ✅ Extremely reliable execution
- ⚠️ More complex API (steeper learning curve)
- ⚠️ Still need to calculate Greeks/IV yourself
- 💰 Cheap market data fees if you're trading actively

---

### 5. TastyTrade API

**Status:** 🆕 Not integrated
**Sources:** [TastyTrade API](https://tastytrade.com/api/), [Developer Docs](https://developer.tastytrade.com/), [Market Data](https://developer.tastytrade.com/open-api-spec/market-data/)

**What You Get:**
- Real-time options quotes (equity, index, futures options)
- Options chains via REST API
- Market data for Greeks calculation
- **Free for personal funded accounts**
- Unofficial Python SDK available

**Pricing:**
- **Free** for personal tastytrade funded accounts
- Professional accounts may have fees

**Python Integration:**
```python
# Using unofficial tastytrade SDK
from tastytrade import Session, Account
from tastytrade.instruments import get_option_chain

session = Session(login, password)
chain = get_option_chain(session, 'AAPL')
```

**Verdict:**
- ✅ Free if you fund an account
- ✅ Known for options-focused platform
- ⚠️ Unofficial SDK (not officially supported)
- 🤔 Similar to Tradier model (free data with account)

---

### 6. yfinance (Yahoo Finance)

**Status:** ✅ Easy to use
**Sources:** [Options Data Tutorial](https://www.codearmo.com/python-tutorial/options-trading-getting-options-data-yahoo-finance), [yfinance Limitations](https://medium.com/@txlian13/webscrapping-options-data-with-python-and-yfinance-e4deb0124613)

**What You Get:**
- Options chains with strikes, bid, ask, volume, OI
- **Implied volatility** per option (included!)
- Last price, change, percent change
- **Completely free** - no API key needed
- Simple Python interface

**What You DON'T Get:**
- ❌ **No Greeks** (must calculate with py_vollib or mibian)
- ⚠️ 15-minute delayed data (not real-time)
- ⚠️ Unofficial API (Yahoo can break it anytime)
- ⚠️ Rate limiting, reliability issues

**Python Integration:**
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
options_dates = ticker.options  # List of expiration dates
chain = ticker.option_chain('2025-02-21')  # Get specific expiration

calls = chain.calls  # DataFrame with: strike, bid, ask, volume, openInterest, impliedVolatility
puts = chain.puts
```

**Verdict:**
- ✅ **Perfect for prototyping** - zero cost, easy setup
- ✅ Includes IV (huge time-saver)
- ❌ **Not professional-grade** - delayed, unreliable
- ⚠️ Okay for development, not for production trading

---

### 7. Charles Schwab API

**Status:** 🆕 Recently launched
**Sources:** [Schwab Developer Portal](https://developer.schwab.com/products/trader-api--individual), [TD Ameritrade Transition](https://tda-api.readthedocs.io/en/latest/schwab.html), [Unofficial Guide](https://medium.com/@carstensavage/the-unofficial-guide-to-charles-schwabs-trader-apis-14c1f5bc1d57)

**What You Get:**
- Real-time options quotes
- Options chains, account data, order placement
- Replaces old TD Ameritrade API
- Free for Schwab account holders

**Status:**
- ⚠️ **Very new** (launched late 2025)
- thinkorswim platform still exists but no public API
- API primarily for third-party fintech apps
- Individual developers CAN get access via developer portal

**Verdict:**
- ⚠️ Too new, limited community support
- ✅ Good if you're already a Schwab client
- ⚠️ Still need to calculate Greeks yourself

---

## 🏆 Recommendations by Use Case

### 🥇 **Best All-Around: Alpaca ($99/mo) + py_vollib**

**Why:**
- You're already using Alpaca for trading
- $99/mo for real-time OPRA feed is reasonable
- Single vendor for data + execution (simpler)
- Add Greeks layer with py_vollib (fast, accurate)

**What to build:**
1. Upgrade to Alpaca Algo Trader Plus ($99/mo)
2. Fetch real-time quotes via Options Latest Quote API
3. Calculate Greeks using `py_vollib` (Black-Scholes)
4. Calculate IV per strike using reverse Black-Scholes
5. Build your own options chain with full data

**Pros:**
- ✅ One vendor (less complexity)
- ✅ Real-time OPRA data (authoritative)
- ✅ Seamless trading execution
- ✅ Good Python SDK

**Cons:**
- ⚠️ $99/mo recurring cost
- ⚠️ Must calculate Greeks yourself (not hard)

---

### 🥈 **Best for Analytics: Polygon/Massive ($199/mo)**

**Why:**
- Pre-calculated Greeks & IV (saves dev time)
- Historical data for backtesting
- Options Chain Snapshot (get all strikes at once)
- Professional-grade analytics

**Use if:**
- You want to skip Greeks calculation
- You need historical options data
- You're building analytics/research tools
- Budget allows ~$200/mo

**Trade-off:**
- ⚠️ More expensive
- ⚠️ Still need separate broker (Alpaca for execution)

---

### 🥉 **Best Value: Tradier (Free)**

**Why:**
- **Free real-time data** if you open brokerage account
- ORATS Greeks & IV included (professional quality)
- No monthly market data fees
- $0.35/contract (competitive commission)

**Use if:**
- Want to minimize costs
- Willing to open Tradier account
- Okay with using Tradier for both data AND trading

**Consideration:**
- 🤔 Switch from Alpaca to Tradier entirely?
- 🤔 Or use Tradier data + Alpaca execution? (more complex)

---

### 🎓 **Best for Learning: yfinance (Free)**

**Why:**
- Zero cost, zero setup
- Includes IV (rare for free APIs)
- Perfect for prototyping
- Easy Python interface

**Use for:**
- Initial development
- Testing algorithms
- Learning options mechanics
- Non-time-sensitive analysis

**Don't use for:**
- Real trading (delayed data)
- Production systems (unreliable)

---

## 🔧 Technical Implementation Path

### Option A: Upgrade Current Alpaca Setup (RECOMMENDED)

```python
# 1. Upgrade to real-time quotes
from alpaca.data import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest

client = OptionHistoricalDataClient(api_key, secret_key)
request = OptionLatestQuoteRequest(symbol_or_symbols=["AAPL250221C00150000"])
quotes = client.get_option_latest_quote(request)

# 2. Add Greeks calculation layer
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

# Calculate Greeks from market prices
option_price = (quotes['AAPL250221C00150000'].ask_price +
                quotes['AAPL250221C00150000'].bid_price) / 2

greeks = {
    'delta': delta('c', stock_price, strike, days_to_exp, risk_free_rate, iv),
    'gamma': gamma('c', stock_price, strike, days_to_exp, risk_free_rate, iv),
    'theta': theta('c', stock_price, strike, days_to_exp, risk_free_rate, iv),
    'vega': vega('c', stock_price, strike, days_to_exp, risk_free_rate, iv)
}

# 3. Calculate IV from market price (reverse Black-Scholes)
from py_vollib.black_scholes.implied_volatility import implied_volatility

iv = implied_volatility(market_price, stock_price, strike, days_to_exp, risk_free_rate, 'c')
```

**Cost:** $99/mo + development time
**Complexity:** Medium (need to build Greeks layer)
**Quality:** Professional-grade

---

### Option B: Switch to Polygon for Pre-Calculated Data

```python
from polygon import RESTClient

client = RESTClient(api_key)

# Get full options chain with Greeks & IV included
snapshot = client.get_snapshot_option_chain(underlying_ticker="AAPL")

for option in snapshot:
    print(f"Strike: {option.strike}")
    print(f"Bid/Ask: {option.bid}/{option.ask}")
    print(f"Greeks: Delta={option.greeks.delta}, Gamma={option.greeks.gamma}")
    print(f"IV: {option.implied_volatility}")
    print(f"Volume: {option.volume}, OI: {option.open_interest}")
```

**Cost:** ~$199/mo + Alpaca for execution
**Complexity:** Low (data ready to use)
**Quality:** Professional-grade

---

### Option C: Tradier for Free Data + Trading

```python
import requests

headers = {
    'Authorization': f'Bearer {tradier_token}',
    'Accept': 'application/json'
}

# Get options chain with Greeks
response = requests.get('https://api.tradier.com/v1/markets/options/chains',
    params={
        'symbol': 'AAPL',
        'expiration': '2025-02-21',
        'greeks': 'true'  # ORATS Greeks included
    },
    headers=headers
)

chain = response.json()
for option in chain['options']['option']:
    print(f"Strike: {option['strike']}")
    print(f"Greeks: Delta={option['greeks']['delta']}")
    print(f"IV: {option['greeks']['mid_iv']}")
```

**Cost:** Free (with Tradier account)
**Complexity:** Low-Medium (new broker integration)
**Quality:** Professional-grade (ORATS Greeks)

---

## 📚 Python Libraries for Greeks Calculation

### py_vollib (RECOMMENDED)

**Sources:** [GitHub](https://github.com/vollib/py_vollib), [Docs](https://vollib.org/)

**Why use it:**
- Fast (wraps Peter Jäckel's C code)
- Black-Scholes, Black-Scholes-Merton, Black76 models
- Analytical + numerical Greeks
- Optional Numba acceleration
- Vectorized version available (py_vollib_vectorized)

```python
from py_vollib.black_scholes import black_scholes as bs
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega
from py_vollib.black_scholes.implied_volatility import implied_volatility

# Calculate option price
price = bs('c', S=100, K=105, t=0.1, r=0.05, sigma=0.25)

# Calculate Greeks
d = delta('c', S=100, K=105, t=0.1, r=0.05, sigma=0.25)
g = gamma('c', S=100, K=105, t=0.1, r=0.05, sigma=0.25)

# Reverse-calculate IV from market price
iv = implied_volatility(market_price=5.50, S=100, K=105, t=0.1, r=0.05, flag='c')
```

---

### mibian (CURRENT)

**Sources:** [GitHub](https://github.com/yassinemaaroufi/MibianLib)

**Why you're using it:**
- Simple, straightforward API
- Black-Scholes, Garman-Kohlhagen, Merton models
- Works well for basic needs

**Limitation:**
- Slower than py_vollib (pure Python)
- No vectorization support
- Less maintained

**Recommendation:** Stick with mibian for now, consider py_vollib if performance matters

---

## 💰 Cost Summary

| Approach | Monthly Cost | Setup Time | Data Quality | Best For |
|----------|--------------|------------|--------------|----------|
| Alpaca + py_vollib | $99 | Medium | ⭐⭐⭐⭐ | All-in-one solution |
| Polygon/Massive | $199 | Low | ⭐⭐⭐⭐⭐ | Analytics focus |
| Tradier | $0* | Medium | ⭐⭐⭐⭐ | Budget-conscious |
| IBKR | $1-10 | High | ⭐⭐⭐⭐ | Multi-asset traders |
| yfinance | $0 | Low | ⭐⭐ | Learning/prototyping |

\* Requires opening brokerage account

---

## 🎯 My Recommendation for YOU

Based on your requirements for **professional-grade, genuinely good** options data:

### **Phase 1: Upgrade Alpaca (Next 2 weeks)**

1. **Subscribe to Alpaca Algo Trader Plus** - $99/mo
   - Get real-time OPRA options quotes
   - Keep using Alpaca for execution (already integrated)

2. **Build Options Data Layer**
   - Fetch real-time bid/ask via Options Latest Quote API
   - Calculate Greeks with py_vollib (faster than mibian)
   - Reverse-calculate IV per strike from market prices
   - Store in clean data structure

3. **Upgrade UI to Show Real Data**
   - Real bid/ask spreads (not $0.00)
   - Market-derived IV per strike (not single historical vol)
   - Accurate Greeks from actual prices
   - Liquidity metrics (volume, OI, bid-ask spread %)

**Outcome:** Professional options chain in 1-2 weeks, $99/mo cost

---

### **Phase 2: Evaluate Polygon (Month 2-3)**

After you have Alpaca working well:

1. **Trial Polygon.io** - Try their developer tier
   - See if pre-calculated Greeks save development time
   - Test historical data for backtesting
   - Compare data quality vs Alpaca

2. **Decision Point:**
   - If Greeks calculation is annoying → Switch to Polygon
   - If Alpaca + py_vollib works great → Stay with Alpaca
   - Budget allows → Use both (Polygon for research, Alpaca for execution)

---

### **Alternative: Tradier for Free**

If budget is tight:

1. Open Tradier brokerage account (free, no minimum)
2. Get free real-time options data with ORATS Greeks
3. Use for data only, keep Alpaca for execution
4. OR migrate fully to Tradier (data + trading)

**Trade-off:** Managing two systems vs saving $99/mo

---

## 🚀 Next Steps

Once you decide on data provider, we move to **REPRESENT** stage:

1. Design the professional options chain UI
2. Plan the data architecture (how to store/cache options data)
3. Build the "thesis → contract selector" logic
4. Create advanced analytics (IV surface, probability analysis, P&L diagrams)

**Ready to create the roadmap?**

---

## Sources

### Alpaca
- [Alpaca Options Trading](https://alpaca.markets/options)
- [Real-time Options Data](https://docs.alpaca.markets/docs/real-time-option-data)
- [Latest Quotes API](https://docs.alpaca.markets/reference/optionlatestquotes)
- [Market Data Overview](https://docs.alpaca.markets/docs/about-market-data-api)

### Polygon/Massive
- [Options Market Data API](https://polygon.io/options)
- [Greeks and Implied Volatility](https://polygon.io/blog/greeks-and-implied-volatility)
- [Options Chain Snapshot API](https://polygon.io/blog/announcing-options-chain-snapshot-api)
- [Options REST API](https://massive.com/docs/rest/options/overview)

### Tradier
- [Tradier API Documentation](https://docs.tradier.com/)
- [Market Data Endpoints](https://docs.tradier.com/docs/market-data)
- [Options Chains](https://docs.tradier.com/reference/brokerage-api-markets-get-options-chains)

### Interactive Brokers
- [IBKR Trading API](https://www.interactivebrokers.com/en/trading/ib-api.php)
- [Market Data Pricing](https://www.interactivebrokers.com/en/pricing/market-data-pricing.php)
- [TWS API Market Data](https://interactivebrokers.github.io/tws-api/market_data.html)

### TastyTrade
- [TastyTrade API](https://tastytrade.com/api/)
- [Developer Documentation](https://developer.tastytrade.com/)
- [Market Data Endpoints](https://developer.tastytrade.com/open-api-spec/market-data/)

### Other
- [yfinance Options Tutorial](https://www.codearmo.com/python-tutorial/options-trading-getting-options-data-yahoo-finance)
- [Schwab Developer Portal](https://developer.schwab.com/products/trader-api--individual)
- [OPRA Feed Costs & Licensing](https://www.marketdata.app/education/options/opra-fees)
- [Best Options APIs 2026](https://steadyapi.com/blogs/10-best-stock-options-data-apis-2026)
- [py_vollib GitHub](https://github.com/vollib/py_vollib)
- [py_vollib Documentation](https://vollib.org/)
