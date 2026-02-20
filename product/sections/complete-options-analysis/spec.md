# Section 1: Complete Options Analysis & Recommendation - Specification

## Overview

A professional-grade options analysis tool where users enter a stock ticker and receive a complete AI-driven analysis from research to specific contract recommendations. The bot researches the stock, forms an investment thesis with quantitative reasoning, recommends an options strategy, selects specific contracts, and visualizes the risk/reward profile.

**Core Philosophy:** Show the complete reasoning journey (research → thesis → strategy → contracts → risk) so users understand WHY the bot recommends what it does.

---

## User Flows

### Flow 1: Enter Ticker & View Stock Context

**User Actions:**
1. User enters ticker symbol (e.g., "NVDA") in text input
2. Clicks "Analyze" or "Research & Recommend" button

**What Happens:**
1. App fetches stock data from yfinance
2. Displays current stock price (with $ amount and % change today)
3. Shows interactive price chart with timeframe selector (1D, 1W, 1M, 3M, 6M, 1Y)
4. Fetches and displays recent financial news headlines (last 5-10 articles)
5. News items are clickable links that open in new tab

**Information Displayed:**
- **Stock Price Card:** Current price, today's change ($ and %), market cap
- **Price Chart:** Interactive plotly chart with zoom, pan, hover tooltips
- **Timeframe Buttons:** 1D, 1W, 1M, 3M, 6M, 1Y (highlight selected)
- **News Section:**
  - Article headline (clickable)
  - Publisher name
  - Published time (e.g., "2 hours ago")
  - Short snippet if available

---

### Flow 2: AI Research & Thesis Generation

**What Happens (Automated):**
1. Bot collects research data:
   - Stock price history (3-6 months)
   - Key fundamentals (P/E, revenue growth, profit margin)
   - Recent news headlines
   - Analyst ratings/target prices (if available)
   - Options implied volatility

2. Bot sends data to LLM (GPT-4 or Claude) with prompt:
   "Analyze this stock and form an investment thesis. Include:
   - Directional view (BULLISH/BEARISH/NEUTRAL)
   - Conviction level (0-100%)
   - Expected price move (% and timeframe)
   - Bull case (2-3 key reasons)
   - Bear case (2-3 key risks)
   - Key catalysts (upcoming events)
   - Cite SPECIFIC data points (earnings growth %, revenue trends, etc.)"

3. LLM returns structured thesis (Pydantic model)

**Information Displayed:**

**Thesis Summary Card:**
- **Direction Badge:**
  - 🟢 BULLISH (green) / 🔴 BEARISH (red) / ⚪ NEUTRAL (gray)
  - Conviction percentage (e.g., "75% conviction")

- **Expected Move:** "+15% in 45 days" (or "$140 → $162 target")

- **Timeframe:** "30-45 days" or specific date

- **Thesis Statement:** 2-3 sentence summary of WHY
  - Example: "NVDA is positioned for continued growth due to AI chip demand. Recent earnings showed 50% revenue growth YoY and raised guidance. Upcoming GTC conference in March is a positive catalyst."

**Expandable Sections:**
- **📈 Bull Case:**
  - Bullet points with specific data
  - Example: "• Revenue grew 50% YoY to $18.1B (Q3 2025 earnings)"
  - Example: "• Data center revenue up 112% driven by AI demand"

- **📉 Bear Case:**
  - Bullet points with specific risks
  - Example: "• Valuation: P/E of 65x vs sector average of 25x"
  - Example: "• Competitor risk: AMD gaining market share in enterprise"

- **📅 Catalysts:**
  - Upcoming events that support thesis
  - Example: "• GTC Conference (March 18-21) - likely to announce new AI chips"
  - Example: "• Next earnings: May 28 (analyst estimates $1.09 EPS)"

- **⚠️ Key Risks:**
  - What could invalidate thesis
  - Example: "• Export restrictions to China could impact 20% of revenue"
  - Example: "• Market correction would hit high-P/E growth stocks hardest"

**Quantitative Data References:**
- Show specific numbers used in reasoning
- Example metrics box:
  - Current Price: $145.20
  - Target Price: $165 (avg of 35 analyst estimates)
  - P/E Ratio: 65.2x
  - Revenue Growth (YoY): +50%
  - Profit Margin: 55.3%
  - Implied Volatility (30-day): 42%

---

### Flow 3: Strategy Recommendation

**What Happens (Automated):**
1. Bot maps thesis to appropriate options strategy:
   - Very Bullish (70%+ conviction) → Long Call or Bull Call Spread
   - Moderately Bullish (55-70%) → Bull Call Spread or Covered Call
   - Slightly Bullish (50-55%) → Covered Call or Cash-Secured Put
   - Neutral + High IV → Iron Condor or Strangle
   - Bearish → Put strategies (Long Put, Bear Put Spread)

2. Bot considers:
   - Conviction level
   - Expected move size
   - Timeframe
   - Current IV (high IV → credit strategies, low IV → debit strategies)
   - Risk tolerance (assume moderate for MVP)

3. Selects strategy and generates explanation

**Information Displayed:**

**Strategy Card:**
- **Strategy Name (Bold):** "Bull Call Spread"
- **Strategy Type Badge:** "Debit Spread" or "Credit Spread" or "Directional"

**Why This Strategy?**
- Plain English explanation of reasoning
- Example: "Your thesis expects a +15% move in 45 days with 75% conviction. A Bull Call Spread is ideal here because:
  - You're moderately bullish (not extremely bullish)
  - You have a specific price target ($162)
  - You want to cap cost while maintaining upside to target
  - Lower breakeven than buying calls outright"

**How It Works:**
- Simple explanation for users who don't know the strategy
- Example: "A Bull Call Spread means:
  1. Buy a call at lower strike (e.g., $140) - gives you upside
  2. Sell a call at higher strike (e.g., $150) - reduces your cost
  3. Max profit = spread width - net cost
  4. Max loss = net cost (debit paid)
  5. Best for: Moderate bullish moves to specific target"

**What Types of Price Movements Fit This Strategy:**
- Visual or text explanation
- Example: "This strategy profits if:
  ✅ Stock rises moderately (best case: lands between $141-150)
  ✅ Stock rises to target or higher (max profit at $150+)
  ❌ Stock stays flat or falls (lose debit paid)
  ❌ Stock skyrockets past $150 (profit capped)"

---

### Flow 4: Contract Selection & Options Chain Display

**What Happens (Automated):**
1. Bot fetches ALL available options contracts from yfinance:
   - All expirations (next 1-12 months)
   - All strikes (ITM, ATM, OTM)
   - Calls and Puts

2. Bot calculates Greeks for each contract using py_vollib:
   - Delta, Gamma, Theta, Vega, Rho
   - Uses stock price, strike, DTE, IV, risk-free rate

3. Bot scores contracts based on strategy + thesis:
   - For Bull Call Spread targeting $162 in 45 days:
     - Find expirations 30-60 DTE
     - Buy call: Strike near ATM or slightly ITM (0.60-0.75 delta)
     - Sell call: Strike near target price (0.30-0.45 delta)
     - Optimize spread width vs cost

4. Bot selects SPECIFIC contracts and calculates P&L

**Information Displayed:**

**Selected Contracts Card (Highlighted):**
- **"Recommended Trade" banner (green highlight)**

**Buy Side:**
- Contract symbol: NVDA Mar21'25 $140 Call
- Premium: $8.50 (mid of bid/ask)
- Delta: 0.68
- Quantity: 1 contract (100 shares)
- Cost: $850

**Sell Side:**
- Contract symbol: NVDA Mar21'25 $150 Call
- Premium: $3.20 (mid of bid/ask)
- Delta: 0.32
- Quantity: 1 contract (100 shares)
- Credit: $320

**Net Position:**
- **Net Debit:** $530 ($850 - $320)
- **Max Profit:** $470 ($1000 spread - $530 cost)
- **Max Loss:** $530 (debit paid)
- **Breakeven:** $145.30 ($140 + $5.30 debit)
- **Risk/Reward:** 0.89:1 (max profit / max loss)

**Stock Requirement:**
- "No stock position required" (for debit spreads)
- OR "Must own 100 shares of NVDA" (for covered calls)
- OR "Must short 100 shares" (for married puts)

---

**Full Options Chain Table:**

Display ALL contracts in expandable sections by expiration:

**Expiration Tabs:** Mar 21 '25 (30 DTE) | Apr 18 '25 (58 DTE) | May 16 '25 (86 DTE) | ...

**For selected expiration, show table:**

| Type | Strike | Bid | Ask | Last | Volume | OI | IV | Delta | Gamma | Theta | Vega | Spread % |
|------|--------|-----|-----|------|--------|----|----|-------|-------|-------|------|----------|
| Call | $130 | 18.20 | 18.60 | 18.40 | 450 | 1.2K | 41% | 0.85 | 0.03 | -0.15 | 0.22 | 2.2% |
| Call | $135 | 13.80 | 14.10 | 13.95 | 780 | 2.1K | 40% | 0.77 | 0.04 | -0.18 | 0.25 | 2.1% |
| **Call** | **$140** | **8.40** | **8.60** | **8.50** | **1.2K** | **3.5K** | **39%** | **0.68** | **0.05** | **-0.20** | **0.28** | **2.4%** | ← **BUY** |
| Call | $145 | 5.10 | 5.30 | 5.20 | 890 | 2.8K | 38% | 0.55 | 0.06 | -0.21 | 0.29 | 3.9% |
| **Call** | **$150** | **3.15** | **3.25** | **3.20** | **950** | **4.1K** | **37%** | **0.42** | **0.06** | **-0.19** | **0.28** | **3.2%** | ← **SELL** |
| Call | $155 | 1.85 | 1.95 | 1.90 | 420 | 1.9K | 36% | 0.28 | 0.05 | -0.15 | 0.24 | 5.4% |

**Color Coding:**
- **Green highlight:** Bot-selected contracts (BUY/SELL)
- **Green background:** High liquidity (Volume > 500, Spread < 3%)
- **Yellow background:** Medium liquidity (Volume 100-500, Spread 3-5%)
- **Red background:** Low liquidity (Volume < 100, Spread > 5%)
- **Bold text:** ITM options
- **Normal text:** OTM options

**Sortable Columns:**
- Click column header to sort (strike, volume, delta, etc.)

**Filters (Sidebar or Top):**
- Option Type: [Calls] [Puts] [Both]
- Moneyness: [ITM] [ATM] [OTM] [All]
- Min Volume: slider (0-1000+)
- DTE Range: slider (7-365 days)

---

### Flow 5: Risk Visualization (P&L Graph)

**What Happens (Automated):**
1. Bot calculates P&L at expiration for range of stock prices
2. For Bull Call Spread example:
   - Stock prices from $120 to $170 (±20% from current)
   - At each price, calculate:
     - Long $140 Call value: max(0, price - 140) * 100 - $850
     - Short $150 Call value: max(0, price - 150) * -100 + $320
     - Net P/L = sum of both

3. Identify key points:
   - Max Loss: $530 (at $140 or below)
   - Max Profit: $470 (at $150 or above)
   - Breakeven: $145.30

4. Generate interactive plotly chart

**Information Displayed:**

**P&L Diagram (Interactive Plotly Chart):**

**X-Axis:** Stock Price at Expiration ($120 → $170)
**Y-Axis:** Profit/Loss ($)

**Plot:**
- Green line above $0 (profit zone)
- Red line below $0 (loss zone)
- Gray horizontal line at $0 (break-even line)

**Labeled Points:**
- 🔴 **Max Loss:** -$530 at $140 and below (red dot)
- 🟢 **Max Profit:** +$470 at $150 and above (green dot)
- ⚪ **Breakeven:** $0 at $145.30 (white dot)
- 📍 **Current Stock Price:** Vertical dashed line at $145.20

**Hover Tooltips:**
- When hovering over line: "At $147: Profit = $170"

**Summary Metrics (Below Chart):**

| Metric | Value | Notes |
|--------|-------|-------|
| **Max Profit** | $470 | If NVDA ≥ $150 at expiration |
| **Max Loss** | $530 | If NVDA ≤ $140 at expiration |
| **Breakeven** | $145.30 | Need +0.07% move to breakeven |
| **Risk/Reward** | 0.89:1 | Risk $530 to make $470 |
| **Probability of Profit** | ~58% | Based on IV and delta |
| **Capital Required** | $530 | Net debit paid |
| **Return if Max Profit** | +89% | $470 / $530 |

**What If Scenarios (Optional Expandable):**
- "What if NVDA hits target ($162)?" → Profit: $470 (max profit)
- "What if NVDA stays flat ($145)?" → Loss: -$30
- "What if NVDA drops 10% ($130)?" → Loss: -$530 (max loss)

---

## Key Information

### Inputs
- **Ticker Symbol:** User enters (e.g., "NVDA", "AAPL", "TSLA")
- **Timeframe Selector:** Buttons for price chart (1D, 1W, 1M, 3M, 6M, 1Y)
- **Expiration Selector:** Tabs or dropdown for options chain (Mar 21, Apr 18, May 16, etc.)

### Data Fetched
- Stock price (current, historical)
- Stock fundamentals (P/E, revenue growth, profit margin, market cap)
- News headlines (last 5-10 articles with links)
- Analyst ratings & target prices
- Options chain (all strikes, all expirations)
- Implied volatility (per option and average)

### Calculations
- **Greeks:** Delta, Gamma, Theta, Vega, Rho (using py_vollib Black-Scholes)
- **Bid-Ask Spread %:** (Ask - Bid) / Mid * 100
- **P/L at Expiration:** For each stock price point, calculate option values
- **Breakeven Price:** Strike + Net Debit (for debit spreads)
- **Max Profit/Loss:** Based on strategy payoff diagram
- **Probability of Profit:** Estimated from delta (delta ≈ probability ITM)

### AI/LLM Processing
- **Input to LLM:**
  - Stock data (price, fundamentals, news)
  - Historical performance
  - Options IV levels

- **LLM Output (Structured Pydantic Model):**
  ```python
  class InvestmentThesis:
      direction: str  # "BULLISH" | "BEARISH" | "NEUTRAL"
      conviction: int  # 0-100
      expected_move: str  # "+15% in 45 days"
      target_price: float  # 162.00
      timeframe: str  # "30-45 days"
      thesis_summary: str  # 2-3 sentences
      bull_case: list[str]  # ["Revenue grew 50%...", ...]
      bear_case: list[str]  # ["High valuation...", ...]
      catalysts: list[str]  # ["GTC Conference March 18", ...]
      key_risks: list[str]  # ["Export restrictions", ...]
      data_references: dict  # {"revenue_growth": "50%", "pe_ratio": "65.2x"}

  class StrategyRecommendation:
      strategy: str  # "Bull Call Spread"
      rationale: str  # Why this strategy fits the thesis
      explanation: str  # How the strategy works
      price_movements: str  # What price action this strategy fits
      contracts: list[ContractSelection]  # Specific contracts to trade

  class ContractSelection:
      action: str  # "BUY" | "SELL"
      symbol: str  # "NVDA Mar21'25 $140 Call"
      strike: float  # 140.00
      expiration: str  # "2025-03-21"
      option_type: str  # "call" | "put"
      premium: float  # 8.50
      delta: float  # 0.68
      quantity: int  # 1
  ```

---

## UI Layout (Streamlit)

### Sidebar
- **Ticker Input:** Text box with "Enter ticker (e.g., NVDA)"
- **Analyze Button:** Primary CTA button
- **Filters (Collapsible):**
  - Option Type: Radio buttons (Calls | Puts | Both)
  - DTE Range: Slider (7-365 days)
  - Min Volume: Slider (0-1000+)

### Main Content (Scrollable)

**Section 1: Stock Context**
- Row 1: Stock price card (current price, % change, market cap)
- Row 2: Interactive price chart with timeframe buttons
- Row 3: Recent news headlines (5-10 cards with clickable links)

**Divider**

**Section 2: AI Thesis**
- Direction badge + conviction %
- Thesis summary card (2-3 sentences)
- Two-column layout:
  - Left: Bull case (expandable), Bear case (expandable)
  - Right: Expected move metrics, Catalysts, Key risks
- Quantitative data references box

**Divider**

**Section 3: Strategy Recommendation**
- Strategy name + type badge
- "Why this strategy?" explanation
- "How it works" explanation
- "Price movements that fit" explanation

**Divider**

**Section 4: Recommended Contracts**
- Highlighted card with green border
- Buy side: Contract details, premium, delta, cost
- Sell side: Contract details, premium, delta, credit
- Net position: Debit/credit, max profit, max loss, breakeven, R/R ratio
- Stock requirement note

**Section 5: Full Options Chain**
- Expiration tabs (Mar 21, Apr 18, May 16, ...)
- Sortable table with all strikes
- Color-coded by liquidity
- Highlighted rows for bot-selected contracts

**Divider**

**Section 6: Risk Visualization**
- Interactive P&L graph (plotly)
- Labeled max profit, max loss, breakeven points
- Current stock price vertical line
- Summary metrics table below chart
- "What if" scenarios (expandable)

---

## Out of Scope (For Section 1)

**Not included in this section:**
- Actual trade execution (deferred to Section 2: Paper Trading)
- Portfolio tracking (deferred to Section 3: Portfolio Dashboard)
- Real-time data (using 15-min delayed yfinance for now)
- Multi-ticker analysis (one ticker at a time for MVP)
- Custom strategy builder (bot selects strategy, user can't customize yet)
- Historical backtesting (future enhancement)
- Alerts/notifications (future enhancement)
- User accounts/authentication (future enhancement)
- Saved analyses (future enhancement)

**Assumptions:**
- User understands basic options concepts (calls, puts, strikes, expirations)
- User has modest risk tolerance (bot assumes moderate strategies)
- Data is 15-min delayed (acceptable for analysis, not execution)
- Using free data sources (yfinance, no premium subscriptions)

---

## Success Criteria

**How we know Section 1 is working:**

✅ **Data Quality:**
- Stock price matches Yahoo Finance within 15 minutes
- Options chain shows 50+ contracts per expiration
- Greeks are calculated correctly (Delta 0-1 for calls, etc.)
- News headlines are recent (within 24 hours)

✅ **AI Thesis Quality:**
- Direction makes sense given data (not random)
- Conviction correlates with strength of data
- Bull/bear cases cite SPECIFIC numbers (not vague)
- Catalysts are real events (not hallucinated)
- Expected move is reasonable (not "500% in 1 week")

✅ **Strategy Selection:**
- Strategy aligns with thesis (bullish thesis → bullish strategy)
- Risk/reward is appropriate (not extreme)
- Contracts have decent liquidity (volume > 100, spread < 5%)
- Strikes make sense (not way OTM for directional bet)

✅ **User Experience:**
- Load time < 10 seconds for full analysis
- Charts are interactive and responsive
- News links work (open in new tab)
- P/L graph is clear and labeled
- UI is professional-looking (not amateur Streamlit default)

✅ **Explainability:**
- User can understand WHY bot picked this strategy
- User can see WHAT data influenced the thesis
- User can evaluate if they agree with reasoning
- No black box — everything is transparent

**Red Flags (If these happen, something is wrong):**
- ❌ Bot is always bullish (or always bearish)
- ❌ Recommendations have terrible liquidity (volume < 10)
- ❌ Greeks don't make sense (Delta > 1.0)
- ❌ P/L graph shows wrong values
- ❌ News is old or irrelevant
- ❌ LLM hallucinates data (cites earnings that didn't happen)

---

## Technical Notes

**Data Sources:**
- `yfinance` for stock data, options chains, news
- Free (no API key required)
- 15-minute delayed (acceptable for analysis)
- Unofficial API (could break, but widely used)

**Greeks Calculation:**
- `py_vollib` for Black-Scholes
- Inputs: stock_price, strike, DTE, risk_free_rate (use 5%), IV
- IV source: yfinance provides IV per option (use that)
- Fallback: Calculate historical volatility if IV missing

**LLM Integration:**
- OpenAI GPT-4 or Anthropic Claude Sonnet
- Use Pydantic for structured output
- System prompt defines output schema
- Include examples of good thesis (few-shot learning)
- Estimate cost: ~$0.05-0.10 per analysis (GPT-4 pricing)

**Chart Library:**
- Plotly for interactive charts (price chart, P&L graph)
- Streamlit has native plotly support
- Allows zoom, pan, hover tooltips

**UI Framework:**
- Streamlit for rapid development
- Use `st.columns()` for layouts
- Use `st.expander()` for collapsible sections
- Use `st.dataframe()` for options chain table
- Style with custom CSS if needed

---

## File Structure

```
options-strategy-bot/
├── app_v5.py                    # Main Streamlit app (Section 1)
├── src/
│   ├── data/
│   │   └── yfinance_client.py   # Fetch stock/options data
│   ├── calculations/
│   │   └── greeks.py            # Calculate Greeks (py_vollib)
│   │   └── pnl.py               # P&L calculations
│   ├── ai/
│   │   └── thesis_generator.py  # LLM thesis generation
│   │   └── strategy_selector.py # Map thesis → strategy
│   │   └── contract_picker.py   # Select specific contracts
│   ├── models/
│   │   └── thesis.py            # Pydantic models
│   └── ui/
│       └── charts.py            # Plotly chart functions
│       └── tables.py            # Options chain table formatting
├── .env                         # API keys (OPENAI_API_KEY)
└── requirements.txt             # Dependencies
```

**Dependencies:**
```
streamlit>=1.30.0
yfinance>=0.2.30
py_vollib>=1.0.1
plotly>=5.17.0
pandas>=2.0.0
openai>=1.10.0  # or anthropic>=0.18.0
pydantic>=2.0.0
```

---

## Next Steps

**After spec approval:**
1. Set up project structure
2. Build data fetching layer (yfinance client)
3. Build Greeks calculation layer (py_vollib)
4. Build AI thesis generator (LLM integration)
5. Build strategy selector logic
6. Build contract picker logic
7. Build P/L calculator
8. Build Streamlit UI (wire everything together)
9. Test with multiple tickers (NVDA, AAPL, TSLA, SPY)
10. Iterate based on results

**Ready to build?**
