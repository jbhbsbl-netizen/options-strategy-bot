# Roadmap

Building on: yfinance (free options data + news), py_vollib (Greeks), plotly (charts), Streamlit (UI), LLM providers (OpenAI/Anthropic for thesis generation)

---

## 🎯 The Complete Vision

**End-to-end flow:** User enters ticker → Bot researches stock → Generates investment thesis → Recommends specific options strategy → Shows exact contracts to trade → Visualizes risk/reward

**Philosophy:** Build the complete integrated experience (not disconnected pieces) because the value is in the AI's reasoning journey from research → thesis → execution.

---

## Sections

### 1. Complete Options Analysis & Recommendation ⭐ **THE CORE PRODUCT**

**What it does:** User enters ticker, bot does complete analysis from research to specific contract recommendations with full risk visualization.

**User Experience:**
1. **Stock Context** - Price, interactive chart, recent financial headlines
2. **AI Research & Thesis** - Bot analyzes data/news, forms directional thesis with quantitative reasoning
3. **Strategy Recommendation** - Bot selects options strategy that fits thesis, explains how it works
4. **Contract Selection** - Displays ALL available contracts, highlights SPECIFIC ones to buy/sell
5. **Risk Visualization** - P&L graph showing max profit/loss, breakevens, labeled numbers

**Success looks like:**
- Enter "NVDA" → See price chart, read recent news
- Bot says "BULLISH 75% conviction, expecting +15% move in 45 days due to [specific data]"
- Bot recommends "Bull Call Spread" and explains what that means
- Bot highlights: "Buy NVDA Mar21 $140C @ $8.50, Sell NVDA Mar21 $150C @ $3.20"
- See P&L graph: Max profit $680, Max loss $170, Breakeven at $141.70

---

### 2. Earnings Calendar Intelligence 📅 **CATALYST TRACKER**

**What it does:** Bot tracks all earnings dates, uses historical earnings patterns to predict post-earnings movement, and displays visual earnings calendar to help users identify catalysts.

**UI Components:**
1. **Moving ticker bar** - Shows company logo + next earnings date countdown
   - Example: "[NVDA logo] NVDA - Feb 26, 2025 (7 days) | After Market"
2. **Historical earnings data** - Past 4-8 quarters: beat/miss rate, typical post-earnings move
3. **Earnings intelligence** - Bot factors earnings into predictions

**Bot Intelligence:**
- **Before earnings (7+ days):** Factor into prediction
  - "Earnings on Feb 26. Historical beat rate: 85% (last 8 qtrs). Avg post-earnings move: +6.2%"
- **Before earnings (<7 days):** Often recommend UNPREDICTABLE
  - "Earnings in 3 days - binary catalyst. IV at 95th percentile (70% vs 45% avg) = IV crush risk. Wait for results."
- **After earnings:** Use actual results + guidance as major thesis inputs

**Data Sources (Free):**
- yfinance: `stock.calendar` (next earnings date), `stock.earnings` (historical)
- Financial Modeling Prep (FMP): Earnings calendar API (250 req/day free)
- Alpha Vantage: Earnings data (25 req/day free)
- SEC EDGAR: 8-K filings for actual earnings releases

**Success Looks Like:**
- User sees: "NVDA earnings in 7 days - historical avg post-earnings move +7.3%"
- Bot factors this into thesis: "Upcoming catalyst with positive historical pattern"
- Bot recognizes high-risk periods: "Earnings in 2 days → UNPREDICTABLE, wait for clarity"
- Visual calendar helps users plan around earnings events

**Why This Matters:**
- Earnings = #1 catalyst for options movement
- Historical patterns are genuinely predictive
- Helps bot make smarter UNPREDICTABLE decisions (know when uncertainty is too high)
- IV crush awareness (high IV before earnings → drops after, kills option value)

**Deferred until Section 1 core works (need thesis generation working first).**

---

### 3. Paper Trading Executor

Connect to Alpaca paper account, execute the bot's recommended trades, track positions and P&L over time.

**Deferred until Section 1 proves the bot can make smart recommendations.**

---

### 4. Portfolio Dashboard

Track multiple positions, monitor Greeks exposure, see overall portfolio performance, get alerts for roll/close timing.

**Deferred until Section 3 works (need positions to track).**

---

### 5. Production Upgrade Path

Swap yfinance (15-min delayed) for Alpaca real-time data ($99/mo), add live trading capability, implement advanced risk management.

**Only when bot proves profitability in paper trading.**

---

## 🔥 Current Focus

**Building:** Section 1 - Complete Options Analysis & Recommendation

**Progress:**
- ✅ Data foundation (yfinance, news scraper, SEC parser)
- ✅ AI thesis generator (21K words context, 4 honest outcomes)
- ✅ Strategy selector (9 strategies)
- ✅ Contract picker (specific strikes/expirations)
- ⏭️ **NEXT: P/L calculator & visualization**
- ⏭️ Streamlit UI (complete user experience)

**Why this order:**
- Section 1 is the entire value proposition (AI research → thesis → contracts)
- Can't paper trade (Section 3) until we have smart recommendations
- Can't track portfolio (Section 4) without positions
- Don't pay for real-time data (Section 5) until bot proves itself

**See SESSION_PROGRESS.md for detailed status and next steps.**

---

## Notes

**Integrated vs Modular:**
We're building Section 1 as ONE integrated flow (not breaking into tiny pieces) because:
- The user experience is a narrative: research → thesis → strategy → contracts → risk
- Breaking it into disconnected pieces ruins the story
- Faster to prove the concept works end-to-end

**Data Strategy:**
- **Phase 1 (Now):** Use yfinance (free, 15-min delayed) - good enough to prove concept
- **Phase 2 (Later):** Upgrade to Alpaca Algo Trader Plus ($99/mo) when bot demonstrates value

**Tech Stack:**
- `yfinance` - Stock data, options chains, news headlines
- `py_vollib` - Greeks calculations (Delta, Gamma, Theta, Vega)
- `plotly` - Interactive charts (price chart, P&L graph)
- `streamlit` - UI framework (show-don't-tell, fast iteration)
- `openai` or `anthropic` - AI thesis generation (GPT-4 or Claude)
- `pydantic` - Structured data models for thesis/strategy

**Philosophy:**
Build with free tools, prove it works, then invest in premium infrastructure.
