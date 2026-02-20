# Tomorrow's Build Session Plan - February 14, 2026

**Status:** Section 1 Complete (7.8/10 from GPT-4)
**Next:** Add Earnings Awareness + Autonomous Screener

---

## 🎯 Three Main Features to Build

### **1. Earnings Awareness (NOT Earnings-Centric)**

#### **Critical Balance:**
- ✅ **DO:** Make bot aware of earnings as ONE factor
- ✅ **DO:** Research earnings patterns (historical moves, IV crush)
- ✅ **DO:** Suggest earnings strategies IF clear opportunity exists
- ❌ **DON'T:** Make bot earnings-centric or earnings-only
- ❌ **DON'T:** Replace fundamental research with earnings focus
- ❌ **DON'T:** Force earnings plays when no clear edge

#### **Core Principle:**
> "Current research-driven approach ALWAYS happens for every stock.
> Earnings is an ADDITIONAL layer, not a replacement.
> Earnings strategies are presented as OPTIONS when there's clear edge."

#### **Examples of Good Balance:**

**Example A: No Clear Earnings Edge**
```
NVDA Analysis:
Thesis: BULLISH (75% conviction)
Strategy: Bull Call Spread
Max Profit: $1,574

Note: Earnings in 35 days (outside trade window)
```

**Example B: Clear Earnings Opportunity**
```
NVDA Analysis:
Thesis: BULLISH (75% conviction)

PRIMARY RECOMMENDATION:
Bull Call Spread (fundamental play)
Max Profit: $1,574

EARNINGS OPPORTUNITY (5 days away):
Research: ±8% typical move, IV 85th percentile
Alternative: Long Straddle (volatility play)
Max Profit: $3,200

Choose: Fundamental OR Earnings play
```

**Example C: Earnings Present but Not Attractive**
```
AAPL Analysis:
Thesis: NEUTRAL (55% conviction)
Strategy: Iron Condor

Note: Earnings in 7 days. Historical moves ±3% (small).
IV 45th percentile (not elevated). Earnings play not recommended.
```

#### **Implementation:**
```python
# ALWAYS runs (core pipeline - NEVER skip)
thesis = generate_thesis_with_research()
strategy = select_strategy_with_research()
contracts = pick_contracts_with_research()

# ADDITIONAL earnings check
earnings_date = get_earnings_date()
if earnings_within_trade_window(earnings_date):
    earnings_research = research_earnings_patterns()

    if has_clear_earnings_edge(earnings_research):
        earnings_strategy = suggest_earnings_strategy()
        # Present BOTH: normal + earnings alternative
    else:
        # Just mention earnings, proceed normally
```

---

### **2. Earnings Display in Stock Context**

#### **Where:**
Add to the metrics cards at the top (Current Price, Market Cap, P/E, etc.)

#### **What to Show:**
- Next earnings date (e.g., "Feb 20, 2026")
- Time of day:
  - **BMO** = Before Market Open (7:00 AM ET)
  - **AMC** = After Market Close (4:00 PM ET)
  - **DMH** = During Market Hours
- Days until earnings (e.g., "5 days")

#### **Visual Example:**
```
┌──────────────┬──────────────┬───────────┬──────────────┬─────────┬────────────────┐
│ Current Price│  Market Cap  │ P/E Ratio │  52-Wk Range │ Volume  │ Next Earnings  │
├──────────────┼──────────────┼───────────┼──────────────┼─────────┼────────────────┤
│  $182.81     │   $4.6T      │   45.2    │ $108 - $152  │  45.2M  │  Feb 20 (AMC)  │
│  +2.3%       │              │           │              │         │   (5 days)     │
└──────────────┴──────────────┴───────────┴──────────────┴─────────┴────────────────┘
```

#### **Fetch From:**
```python
# yfinance has earnings calendar
ticker = yf.Ticker("NVDA")
earnings_dates = ticker.calendar  # Has dates
next_earnings = earnings_dates['Earnings Date'][0]
```

---

### **3. Cool Homepage UI - Earnings Ticker**

#### **What:**
Moving/scrolling bar showing upcoming earnings across multiple stocks

#### **Visual:**
```
═══════════════════════════════════════════════════════════════
📅 Upcoming Earnings: NVDA (Feb 20) | AAPL (Feb 22) | TSLA (Feb 25) | GOOGL (Feb 27) | MSFT (Mar 1) →
═══════════════════════════════════════════════════════════════
```

#### **Features:**
- Scrolls horizontally (animated)
- Shows 10-20 upcoming earnings
- Clickable? (maybe - click to analyze that stock)
- Updates daily
- Professional look

#### **Implementation:**
- Use Streamlit's `st.markdown()` with CSS animation
- Or use `st.components.v1.html()` for custom scrolling
- Fetch from yfinance earnings calendar for multiple tickers

---

### **4. Proactive High-Conviction Ideas (Autonomous Screener)**

#### **Concept:**
Bot doesn't wait for user to ask. It proactively shows best opportunities.

#### **User mentioned:**
> "What happened to the idea that the bot should display its most high-conviction
> ideas without having to be prompted?"

#### **The Vision:**

**Homepage displays:**
```
🧠 Today's High-Conviction Ideas

1. NVDA - 85% BULLISH ⬆️
   Bull Call Spread | Max Profit: $1,574 | R/R: 3.15:1
   [View Full Analysis]

2. AAPL - 80% BEARISH ⬇️
   Bear Put Spread | Max Profit: $2,100 | R/R: 4.2:1
   [View Full Analysis]

3. TSLA - 75% NEUTRAL ⚪
   Iron Condor | Max Profit: $850 | R/R: 2.1:1
   [View Full Analysis]
```

#### **How it Works:**
1. Bot analyzes 20-50 stocks (watchlist or popular tickers)
2. Runs complete research + thesis on each
3. Ranks by conviction level
4. Surfaces top 3-5 ideas
5. User can click to see full analysis

#### **This was:** "Top 100 screener" from original roadmap

---

## 🗓️ Tomorrow's Build Order

### **Morning Session (3-4 hours):**

**Task 1: Earnings Date Fetching (30 min)**
- Add method to `yfinance_client.py`:
  - `get_earnings_date(ticker)` → returns date + time
- Test with NVDA, AAPL, TSLA

**Task 2: Display Earnings in Stock Context (30 min)**
- Add earnings metric card to `app_research.py`
- Show: "Feb 20 (AMC) - 5 days"
- Make it prominent

**Task 3: Earnings Research Questions (1 hour)**
- Add to `research_orchestrator.py`:
  - "What was [TICKER]'s typical post-earnings move in last 4 quarters?"
  - "Does [TICKER] usually beat or miss earnings estimates?"
  - "Historical IV crush pattern after [TICKER] earnings?"
- Generate these questions when earnings is within 30 days

**Task 4: Earnings Awareness in Thesis (1 hour)**
- Modify `thesis_generator_v3.py`:
  - Check if earnings upcoming
  - Include earnings research in thesis
  - Mention earnings in thesis summary
- **But keep fundamental research as primary!**

### **Afternoon Session (3-4 hours):**

**Task 5: Earnings Strategy Logic (1.5 hours)**
- Add to `strategy_selector_v2.py`:
  - Check earnings timing
  - Evaluate if earnings play makes sense:
    - Is IV elevated? (>70th percentile)
    - Are historical moves consistent?
    - Is there clear edge?
  - IF YES: Suggest earnings strategy AS ALTERNATIVE
  - IF NO: Just mention earnings, proceed normally

**Task 6: Earnings-Specific Strategies (1 hour)**
- Add strategies for earnings plays:
  - Long Straddle (bet on big move)
  - Long Strangle (bet on big move, cheaper)
  - Iron Condor (bet on small move, sell high IV)
  - Calendar Spread (profit from IV crush)

**Task 7: Earnings Ticker UI (1 hour)**
- Add scrolling earnings bar to homepage
- Fetch upcoming earnings for 20 stocks
- Display: "NVDA (Feb 20) | AAPL (Feb 22) | ..."
- Make it look cool

**Task 8: Test Complete Flow (30 min)**
- Analyze stock with earnings in 5 days
- Verify: Primary strategy + Earnings alternative shown
- Analyze stock with earnings in 40 days
- Verify: Just mentioned, normal strategy

---

## 📋 Files to Modify

### **Data Layer:**
- `src/data/yfinance_client.py`
  - Add `get_earnings_date(ticker)`
  - Add `get_earnings_calendar(tickers)` for multiple

### **Research Layer:**
- `src/research/research_orchestrator.py`
  - Add earnings research phase (conditional)
  - Generate earnings-specific questions

### **AI Layer:**
- `src/ai/thesis_generator_v3.py`
  - Factor earnings into thesis
  - Include earnings research

### **Strategy Layer:**
- `src/strategies/strategy_selector_v2.py`
  - Add earnings strategy evaluation logic
  - Present primary + alternative when appropriate
  - Add earnings-specific strategies

### **UI Layer:**
- `app_research.py`
  - Add earnings metric card
  - Add earnings ticker bar
  - Display both primary and earnings strategies

---

## 🎯 Success Criteria

### **Earnings Awareness:**
✅ Bot knows when earnings is coming
✅ Bot researches earnings patterns
✅ Bot mentions earnings in analysis
✅ Earnings is context, not the whole strategy

### **Earnings Strategies:**
✅ Suggested ONLY when clear opportunity
✅ Presented AS ALTERNATIVE to primary recommendation
✅ Not forced when no edge exists
✅ User can choose: fundamental OR earnings play

### **Display:**
✅ Earnings date shown in stock context
✅ Earnings ticker scrolling on homepage
✅ Clean, professional look

### **Core Preserved:**
✅ Fundamental research ALWAYS runs
✅ Thesis quality maintained
✅ Strategy selection still data-driven
✅ Bot doesn't become "earnings bot"

---

## 🚨 Critical Reminders

### **The Balance:**
- Earnings is **additive**, not **replacement**
- Core pipeline always runs (research → thesis → strategy)
- Earnings strategies only when there's edge
- Present as OPTIONS, not mandates

### **Don't Over-Engineer:**
- Keep it simple tomorrow
- Get basic earnings awareness working first
- Can always enhance later

### **Test With:**
- Stock with earnings in 5 days (e.g., NVDA if timing works)
- Stock with earnings in 40 days (outside window)
- Stock with no upcoming earnings

---

## 📊 Expected Outcome

### **After Tomorrow:**

**User analyzes NVDA (earnings in 5 days):**

```
Stock Context:
Current Price: $182.81 | Next Earnings: Feb 20 (AMC) - 5 days

Thesis: BULLISH (75% conviction)
[Normal research + thesis generation]

PRIMARY RECOMMENDATION:
Bull Call Spread (fundamental play)
Max Profit: $1,574 | R/R: 3.15:1

EARNINGS OPPORTUNITY:
I researched NVDA's earnings patterns:
- Typical move: ±8% (last 4 quarters)
- IV currently: 85th percentile (elevated)
- Historical IV crush: 30-40% next day

Alternative Strategy: Long Straddle
Bet on volatility, profit from ±8% move
Max Profit: $3,200 | Breakevens: $174 / $192

Choose based on preference:
→ Fundamental play (Bull Call Spread)
→ Earnings volatility play (Long Straddle)
```

---

## 💾 Files Created This Session

### **Complete:**
- `app_research.py` - Main Streamlit UI (630 lines)
- `evaluate_bot.py` - ChatGPT evaluator (400 lines)
- `src/research/web_researcher.py` - Improved scraper (400 lines)
- `RESEARCH_ENHANCED_UI_COMPLETE.md` - Documentation
- `SECTION_1_COMPLETE.md` - Summary
- `README.md` - Updated user guide

### **Need to Modify Tomorrow:**
- `src/data/yfinance_client.py` - Add earnings methods
- `src/research/research_orchestrator.py` - Add earnings research
- `src/ai/thesis_generator_v3.py` - Factor in earnings
- `src/strategies/strategy_selector_v2.py` - Earnings strategy logic
- `app_research.py` - Add earnings display + ticker

---

## 🎉 Current Status

**What Works:**
- Complete research pipeline (15 questions, 10+ articles)
- Thesis generation with autonomous research
- Strategy selection with research
- Contract selection with research
- P/L calculator with Greeks
- Interactive Plotly charts
- Professional Streamlit UI
- ChatGPT evaluator (scored 7.8/10)

**What's Next:**
- Earnings awareness (additive, not replacement)
- Earnings ticker UI
- Autonomous screener (proactive ideas)

---

## ⚠️ Important Notes

1. **Don't break what works** - Core pipeline is solid (7.8/10)
2. **Earnings is enhancement** - Not a pivot to earnings-only bot
3. **Keep it simple** - Get basic version working, enhance later
4. **Test thoroughly** - Try different earnings scenarios
5. **User choice** - Present options, let them decide

---

**This document captures everything discussed for tomorrow's session.**

When we start tomorrow, read this file first to pick up exactly where we left off! 🚀

---

**Last Updated:** February 14, 2026 00:45 AM
**Ready for:** Morning build session
