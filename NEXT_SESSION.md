# 🚀 Next Session: Build Streamlit UI

**Start Date:** Next session
**Goal:** Build complete Streamlit UI to integrate all components

---

## Quick Start

When you return, say:
> "Let's build the Streamlit UI"

Or:
> "Continue from where we left off"

---

## What We've Completed

✅ **Data Foundation**
- yfinance_client.py - Stock data, options chains, news
- news_scraper.py - Full article content
- sec_filings.py & sec_parser.py - SEC data

✅ **AI Thesis Generator**
- thesis_generator_v2.py - 4 honest outcomes
- 21K+ words of context (news + 10-K)
- Conservative AI (no forced predictions)

✅ **Strategy Selection**
- strategy_selector.py - Maps thesis to strategy
- contract_picker.py - Selects specific strikes/expirations

✅ **P/L Calculator & Visualization** ← JUST COMPLETED!
- pnl_calculator.py - Calculate P/L, max profit/loss, Greeks
- pnl_chart.py - Interactive Plotly charts
- Tested with NVDA Bull Call Spread - ALL TESTS PASSED!

---

## What We're Building Next

### Main Streamlit App (`app_complete.py`)

**Goal:** Integrate all components into a complete user experience.

**User Flow:**
1. User enters ticker (e.g., "NVDA")
2. Click "Analyze" button
3. See complete analysis:
   - Stock context (price, chart, news)
   - AI thesis (bull/bear case, conviction)
   - Strategy recommendation (with explanation)
   - Selected contracts (specific strikes/expirations)
   - P/L chart and risk metrics

---

## UI Sections

### Section 1: Sidebar
```python
# Ticker input
ticker = st.sidebar.text_input("Enter Stock Ticker", "NVDA")

# Analyze button
analyze_button = st.sidebar.button("Analyze", type="primary")

# Filters (optional)
st.sidebar.expander("Advanced Filters")
```

### Section 2: Stock Context
```python
# Price card
col1, col2, col3 = st.columns(3)
col1.metric("Current Price", "$188.54", "+2.3%")
col2.metric("Market Cap", "$4.63T")
col3.metric("Volume", "234.5M")

# Price chart
fig = create_stock_chart(historical_data)
st.plotly_chart(fig)

# News headlines
st.subheader("Recent News")
for article in news:
    st.markdown(f"[{article.title}]({article.url})")
```

### Section 3: AI Thesis
```python
# Direction badge
if thesis.direction == "BULLISH":
    st.success(f"🟢 BULLISH - {thesis.conviction}% conviction")

# Thesis summary
st.markdown(thesis.thesis_summary)

# Expandable sections
with st.expander("📈 Bull Case"):
    for point in thesis.bull_case:
        st.markdown(f"• {point}")

with st.expander("📉 Bear Case"):
    for point in thesis.bear_case:
        st.markdown(f"• {point}")
```

### Section 4: Strategy Recommendation
```python
st.subheader(f"Recommended Strategy: {strategy.strategy}")

# Strategy explanation
st.info(strategy.rationale)

# Contracts table
contracts_df = create_contracts_table(strategy.contracts)
st.dataframe(contracts_df)

# Net position
st.metric("Net Debit", f"${strategy.net_debit_credit:.2f}")
```

### Section 5: P/L Visualization
```python
# Calculate P/L
analysis = pnl_calculator.calculate_complete_analysis(
    contracts=strategy.contracts,
    current_price=current_price,
    volatility=0.40,
    days_to_expiration=35
)

# Display P/L chart
chart = create_pnl_chart(
    pnl_curve=analysis['pnl_curve'],
    current_price=current_price,
    max_profit=analysis['max_profit'],
    max_loss=analysis['max_loss'],
    max_profit_price=analysis['max_profit_price'],
    max_loss_price=analysis['max_loss_price'],
    breakevens=analysis['breakevens'],
    strategy_name=strategy.strategy
)
st.plotly_chart(chart, use_container_width=True)

# Metrics table
st.markdown(create_metrics_table(...), unsafe_allow_html=True)
```

---

## Implementation Steps

### Step 1: Create Basic App Structure
```python
import streamlit as st
from src.data.yfinance_client import YFinanceClient
from src.ai.thesis_generator_v2 import ThesisGenerator
from src.strategies.strategy_selector import StrategySelector
from src.strategies.contract_picker import ContractPicker
from src.analysis.pnl_calculator import PnLCalculator
from src.visualization.pnl_chart import create_pnl_chart, create_metrics_table

st.set_page_config(
    page_title="Options Strategy Bot",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Options Strategy Bot")
st.markdown("AI-powered options analysis and strategy recommendations")
```

### Step 2: Add Ticker Input & Analyze Button
```python
# Sidebar
ticker = st.sidebar.text_input("Stock Ticker", "NVDA").upper()
analyze_button = st.sidebar.button("Analyze", type="primary")

if not analyze_button:
    st.info("Enter a ticker and click Analyze to get started")
    st.stop()
```

### Step 3: Fetch Data with Progress Indicators
```python
with st.spinner("Fetching stock data..."):
    client = YFinanceClient()
    stock_data = client.get_stock_info(ticker)
    options_chain = client.get_options_chain_all_expirations(ticker)
    news = client.get_news(ticker)

st.success("Data fetched!")
```

### Step 4: Generate Thesis
```python
with st.spinner("Generating investment thesis..."):
    generator = ThesisGenerator()
    thesis = generator.generate_thesis(
        ticker=ticker,
        stock_data=stock_data,
        news=news
    )

# Display thesis
display_thesis(thesis)
```

### Step 5: Select Strategy & Contracts
```python
with st.spinner("Selecting strategy and contracts..."):
    selector = StrategySelector()
    strategy_name = selector.select_strategy(thesis)

    picker = ContractPicker()
    contracts = picker.pick_contracts(
        thesis=thesis,
        strategy=strategy_name,
        options_chain=options_chain,
        current_price=stock_data.current_price
    )

# Display strategy
display_strategy(strategy_name, contracts)
```

### Step 6: Calculate P/L & Display Chart
```python
with st.spinner("Calculating P/L..."):
    calculator = PnLCalculator()
    analysis = calculator.calculate_complete_analysis(
        contracts=contracts,
        current_price=stock_data.current_price,
        volatility=0.40,
        days_to_expiration=35
    )

# Display P/L chart
chart = create_pnl_chart(...)
st.plotly_chart(chart, use_container_width=True)

# Display metrics
st.markdown(create_metrics_table(...), unsafe_allow_html=True)
```

---

## File to Create

```
options-strategy-bot/
├── app_complete.py          ← CREATE THIS
├── src/
│   ├── data/
│   │   └── yfinance_client.py ✅
│   ├── ai/
│   │   └── thesis_generator_v2.py ✅
│   ├── strategies/
│   │   ├── strategy_selector.py ✅
│   │   └── contract_picker.py ✅
│   ├── analysis/
│   │   └── pnl_calculator.py ✅
│   ├── visualization/
│   │   └── pnl_chart.py ✅
│   └── models/
│       └── thesis.py ✅
```

---

## Success Criteria

**How we know the Streamlit UI is working:**

✅ **User can enter ticker and see analysis**
- Input "NVDA" → click Analyze → see results in 10-30 seconds

✅ **Stock context displays correctly**
- Current price, % change, market cap
- Interactive price chart
- Recent news headlines (clickable)

✅ **AI thesis is clear and actionable**
- Direction (BULLISH/BEARISH/NEUTRAL/UNPREDICTABLE)
- Conviction % shown
- Bull/bear cases with specific data
- Expandable sections work

✅ **Strategy recommendation makes sense**
- Strategy name and explanation
- Selected contracts displayed
- Net debit/credit shown

✅ **P/L chart is interactive and clear**
- Shows profit/loss zones (green/red)
- Max profit, max loss, breakevens marked
- Current price line visible
- Hover tooltips work

✅ **Metrics table is readable**
- Risk/reward ratio displayed
- Greeks shown (if available)
- All values formatted correctly

✅ **UI is professional-looking**
- Clean layout with good spacing
- No default Streamlit styling
- Colors and fonts consistent
- Loading indicators during processing

---

## Testing Checklist

After building, test with these tickers:

1. **NVDA** - Tech stock, high volatility
   - Should get BULLISH or NEUTRAL thesis
   - Bull Call Spread or Long Call likely

2. **AAPL** - Large cap, moderate volatility
   - Should get stable thesis
   - Covered Call or Bull Call Spread likely

3. **SPY** - ETF, low volatility
   - Should get NEUTRAL thesis
   - Iron Condor or Strangle likely

4. **TSLA** - High volatility, unpredictable
   - Might get UNPREDICTABLE (and refuse to trade)
   - Good test of conservative AI

---

## Error Handling

**Handle these cases gracefully:**

1. **Invalid ticker** - "Ticker 'XYZ' not found"
2. **No options available** - "No options data for this ticker"
3. **API rate limit** - "Rate limit reached, try again in 60 seconds"
4. **LLM error** - "Error generating thesis, please try again"
5. **Network error** - "Connection error, check your internet"

---

## Performance Optimizations

**For faster experience:**

1. **Cache data fetching** - Use `@st.cache_data` for stock data
2. **Cache LLM calls** - Cache thesis generation (don't regenerate same ticker)
3. **Async loading** - Load data, news, options in parallel if possible
4. **Progress indicators** - Show user what's happening (not just blank screen)

---

## After Streamlit UI

**Once the UI works, we'll have:**
- Complete Section 1: Options Analysis & Recommendation ✅
- End-to-end user experience ✅
- Professional-grade tool ✅

**Then we can:**
- Add Section 2: Earnings Calendar Intelligence
- Add Section 3: Paper Trading Executor
- Add Section 4: Portfolio Dashboard
- Or: Start using it for real analysis!

---

**See SESSION_PROGRESS.md for complete project status.**

**Ready to build the Streamlit UI on next session!** 🚀
