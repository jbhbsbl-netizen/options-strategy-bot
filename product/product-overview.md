# Options Strategy Bot

## The Problem
Options trading requires understanding complex strategies, Greeks, and risk management. Current tools either:
- Don't explain their reasoning (black box)
- Require manual analysis (time-consuming, error-prone)
- Lack intelligent strategy selection based on market conditions

**Pain:** Traders want a system that can think through options strategies, explain its reasoning clearly, manage risk properly, and eventually execute trades autonomously.

## Success Looks Like
**Phase 1 (MVP - Covered Calls):**
- Bot analyzes a stock position and recommends covered call strikes/expirations
- Explains WHY it chose that strike (income vs protection tradeoff)
- Shows risk metrics (max profit, breakeven, Greeks exposure)
- Runs paper trades on Alpaca with positive results

**Phase 2 (Future):**
- Expands to other strategies (credit spreads, iron condors, etc.)
- Adapts strategy selection based on market conditions (IV rank, trend)
- Live trading with real money after proving profitability

**Promising Signs (All Three):**
1. Profitable paper trades
2. Clear, sensible explanations
3. Proper risk management (doesn't blow up account)

## Building On (Existing Foundations)

**Options Pricing & Greeks:**
- **mibian** — Simple Greeks calculations (Delta, Gamma, Theta, Vega)
- **py_vollib** — Black-Scholes pricing, implied volatility (backup option)

**Options Data:**
- **Finnworlds API** — Free tier for development (3-second lag acceptable for covered calls)
- **Theta Data** — Upgrade path when budget allows (real-time, better quality)

**Brokerage API:**
- **Alpaca** — Paper trading (free) → Live trading (commission-free)
  - Ranked #1 for algo trading in US (2026)
  - Simple API, excellent documentation
  - Note: User currently has eTrade but willing to open Alpaca account

**Backtesting:**
- **Optopsy** — Options-specific backtesting framework
- **Backtesting.py** — General framework (fallback)

**LLM Reasoning:**
- Multi-provider support (OpenAI, Anthropic, Groq) like existing AI hedge fund
- Structured output with Pydantic models

## The Unique Part (What We're Actually Building)

**1. LLM Reasoning Engine for Covered Calls:**
- Analyzes stock position, current price, volatility
- Evaluates multiple strike/expiration combinations
- Explains tradeoffs: "30-delta call gives $X premium but caps upside at Y%"
- Considers market conditions (IV percentile, trend, earnings proximity)

**2. Risk Management Layer:**
- Position sizing (don't overcommit)
- Greeks monitoring (avoid excessive negative delta)
- Stop conditions (roll, close, hold decision logic)

**3. Autonomous Trading Loop:**
- Monitor existing positions
- Detect opportunities (assignment, roll timing)
- Execute trades via Alpaca API
- Log decisions with reasoning for review

**4. Explainability Focus:**
- Every decision comes with clear reasoning
- Shows alternatives considered and why rejected
- Educates user on options mechanics

## Tech Stack

**UI:** Streamlit (show-don't-tell, immediate feedback)
**Backend:** Python 3.11+
**Key Libraries:**
- mibian — Greeks calculations
- pandas — Data manipulation
- alpaca-py — Brokerage API
- LangChain/LangGraph — LLM orchestration (optional, evaluate need)
- Pydantic — Data models

**Data Sources:**
- Finnworlds (free tier initially)
- Alpaca (market data + execution)

**Development Path:**
1. Paper trading on Alpaca (free, no risk)
2. Prove profitability over 1-3 months
3. Upgrade data source if needed (Theta Data)
4. Live trading with small capital

## Open Questions

**To resolve during implementation:**
- How much historical data needed for IV percentile calculations?
- What's the minimum position size for covered calls to be worthwhile?
- Should we simulate stock ownership or require actual stock positions?
- How to handle corporate actions (splits, dividends, special dividends)?
- What's the roll/close decision threshold (% of max profit, days to expiration)?

## Starting Strategy: Covered Calls

**Why start here:**
- Lower risk than naked options
- Clear profit mechanics (premium collection)
- Easier to explain to users
- Good for building risk management patterns
- Natural extension: cash-secured puts (same mechanics)

**Core Logic:**
1. Check if user owns 100+ shares
2. Fetch options chain (calls only)
3. Calculate Greeks for each strike/expiration
4. Score options by: premium / max_loss ratio, probability of profit
5. Select optimal strike based on user risk preference
6. Explain reasoning and show alternatives
7. Execute trade (paper trading first)
8. Monitor position, recommend roll/close timing

## Success Metrics

**Paper Trading Phase (1-3 months):**
- Win rate > 70% (covered calls assigned or closed profitably)
- Average return > 1-2% per month on capital at risk
- No catastrophic losses (max drawdown < 10%)
- User understands every decision (explainability test)

**Graduation to Live Trading:**
- Consistent profitability over 50+ paper trades
- User confident in risk management
- Capital allocated: Start small ($5-10K)
