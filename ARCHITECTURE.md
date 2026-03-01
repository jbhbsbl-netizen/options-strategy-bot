# Architecture

This document explains the five-phase pipeline in detail — how data flows through the system, what each module does, and which AI concepts are at work in each layer.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Input                              │
│                    (ticker symbol, depth)                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1: Data Layer                                            │
│  src/data/yfinance_client.py                                    │
│                                                                 │
│  • Current price, 52-week range, beta                           │
│  • Key financials (P/E, market cap, revenue)                    │
│  • Historical price data (volatility calculation)               │
│  • Options chain (all strikes and expirations)                  │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2: Research Layer                                        │
│  src/research/                                                  │
│                                                                 │
│  Step 1 — autonomous_researcher.py                              │
│    LLM generates research questions across 5 categories:        │
│    earnings, competition, industry, catalysts, risks            │
│    (e.g., "What were NVDA's most recent earnings results?")     │
│                                                                 │
│  Step 2 — web_researcher.py                                     │
│    Each question → DuckDuckGo search → fetch top results        │
│    Scrape full article content (BeautifulSoup4)                 │
│    Filter to credible sources (Reuters, Bloomberg, CNBC, etc.)  │
│    Block social media, opinion blogs, low-quality sources       │
│    Truncate at 6,000 chars/article to fit context window        │
│                                                                 │
│  Step 3 — research_orchestrator.py                              │
│    Coordinates the full research loop                           │
│    Aggregates articles, tracks sources, manages rate limits     │
│    Output: 10,000–15,000 words from credible sources            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3: Thesis Layer                                          │
│  src/ai/thesis_generator_v3.py                                  │
│                                                                 │
│  LLM receives: all scraped articles + stock data                │
│  LLM outputs (structured, parsed into Pydantic model):          │
│    • Direction: BULLISH / BEARISH / NEUTRAL / UNPREDICTABLE     │
│    • Conviction: 0–100%                                         │
│    • Expected move: % change + timeframe in days                │
│    • Target price                                               │
│    • Bull case: specific reasons                                 │
│    • Bear case: specific risks                                   │
│    • Thesis summary: 2–3 sentence narrative                     │
│                                                                 │
│  Structured output parsing: raw LLM text → InvestmentThesis     │
│  object via regex extraction (src/models/thesis.py)             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4: Strategy + Contract Layer                             │
│  src/strategies/                                                │
│                                                                 │
│  strategy_selector_v2.py                                        │
│    LLM receives: thesis + volatility metrics (IV, HV, ratio)    │
│    LLM selects from: long call, long put, bull call spread,     │
│    bear put spread, iron condor, straddle, strangle, calendar   │
│    LLM explains why this structure fits this setup              │
│                                                                 │
│  contract_picker_v2.py                                          │
│    LLM specifies: target delta per leg, DTE range               │
│    Code maps delta targets to closest real strikes on chain     │
│    Validates: liquidity (open interest), spread width, Greeks   │
│    Returns: specific contracts with real market data            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 5: Analysis + Presentation Layer                         │
│  src/analysis/ + src/visualization/                             │
│                                                                 │
│  pnl_calculator.py                                              │
│    P&L at expiration across price range                         │
│    Max profit, max loss, breakeven prices                       │
│    Portfolio Greeks (Delta, Gamma, Theta, Vega)                 │
│    Risk/reward ratio, probability of profit estimate            │
│                                                                 │
│  pnl_chart.py                                                   │
│    Interactive Plotly chart — profit/loss zones                 │
│    Color-coded regions (green = profit, red = loss)             │
│    Breakeven and current price markers                          │
│                                                                 │
│  Streamlit UI (app_chat.py / app_professional.py)               │
│    Presents complete analysis with research citations           │
│    Chat interface enables follow-up Q&A via LLM                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### Why research at every decision point?

Early versions (V1) used hardcoded rules: `IF conviction >= 70% THEN long call`. This worked in backtests but had no causal connection to actual market conditions.

V2/V3 generate research questions at each decision point — thesis generation, strategy selection, and contract selection each make their own queries. The bot forms its own view from primary source material rather than following a rule tree.

The tradeoff: ~2–5 minutes per analysis vs. instant rules. For a decision involving real risk, the latency is acceptable.

### Why DuckDuckGo instead of a premium news API?

Cost. DuckDuckGo is free with no API key. For a research project demonstrating the architecture, it works well. A production system would use a paid financial news API with better coverage and reliability.

### Why structured output parsing instead of JSON mode?

The thesis fields are extracted from natural language output using regex patterns. This is intentional — it forces the LLM to reason in prose first, then extracts the structured fields. JSON mode can cause the model to fill in required fields without sufficient reasoning behind them.

### Why Pydantic for data models?

Type safety across the pipeline. When thesis data passes through 5 modules, a `str` where a `float` is expected would fail silently. Pydantic catches this at the boundary.

### Chat interface design

`app_chat.py` implements a 4-stage conversation FSM:
1. `GREETING` — collect ticker
2. `CONFIGURATION` — research depth preference
3. `ANALYSIS` — run pipeline with live progress updates
4. `RESULTS_QA` — LLM has full analysis context for follow-up questions

The LLM in stage 4 receives the complete analysis (thesis, strategy, contracts, risk metrics) as a system prompt, enabling context-aware answers without re-running the analysis.

---

## Data Flow Diagram

```
ticker
  │
  ├──► yfinance ──────────────────────► stock_data (dict)
  │                                          │
  └──► LLM generates questions               │
           │                                 │
           ▼                                 │
       DuckDuckGo search                     │
           │                                 │
           ▼                                 │
       scrape articles ──────────────► research_text (str, ~12k words)
                                             │
                                             ▼
                                     LLM synthesis
                                             │
                                             ▼
                                     InvestmentThesis (Pydantic)
                                      .direction
                                      .conviction
                                      .expected_move_pct
                                      .bull_case
                                      .bear_case
                                             │
                                             ▼
                                     LLM strategy selection
                                             │
                                             ▼
                                     StrategyRecommendation (Pydantic)
                                      .strategy_name
                                      .legs [{action, option_type,
                                              target_delta, dte}]
                                      .rationale
                                             │
                                             ▼
                                     options chain lookup
                                             │
                                             ▼
                                     ContractSelection list
                                      [{strike, expiration,
                                        delta, premium, OI}]
                                             │
                                             ▼
                                     P&L calculator
                                             │
                                             ▼
                                     PnLAnalysis
                                      .max_profit
                                      .max_loss
                                      .breakeven_prices
                                      .greeks
                                             │
                                             ▼
                                     Streamlit UI / Chat output
```

---

## Module Reference

| Module | Responsibility |
|---|---|
| `src/data/yfinance_client.py` | All market data fetching — price, fundamentals, options chain, historical vol |
| `src/research/autonomous_researcher.py` | LLM question generation across 5 research categories |
| `src/research/web_researcher.py` | DuckDuckGo search, article scraping, source credibility filtering |
| `src/research/research_orchestrator.py` | Coordinates research loop, aggregates output, manages state |
| `src/ai/thesis_generator_v3.py` | Research-enhanced thesis generation via LLM |
| `src/ai/thesis_generator_v2.py` | Baseline (no web research) for comparison |
| `src/strategies/strategy_selector_v2.py` | LLM-driven strategy selection from thesis + vol data |
| `src/strategies/contract_picker_v2.py` | Maps delta targets to real options chain contracts |
| `src/analysis/pnl_calculator.py` | P&L curves, Greeks, breakevens, risk metrics |
| `src/visualization/pnl_chart.py` | Interactive Plotly P&L chart |
| `src/models/thesis.py` | Pydantic data models for the full pipeline |
| `app_chat.py` | Conversational LLM chat interface (primary) |
| `app_professional.py` | Multi-tab form-based professional UI |
| `tests/test_basic.py` | Core component tests (imports, data fetching, models) |
