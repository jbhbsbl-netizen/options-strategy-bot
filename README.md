# Options Strategy Bot

An AI-powered options trading research assistant that autonomously researches market conditions, generates investment theses, and recommends options strategies with full reasoning transparency.

Built as a final project for an AI course, this system demonstrates multi-step LLM agent design, autonomous web research, structured output parsing, and a conversational interface — all applied to a real financial domain.

> **Disclaimer:** Educational project only. Not financial advice. Options trading involves substantial risk of loss.

---

## What It Does

Enter a stock ticker and the bot:

1. Fetches fundamentals and price data (yfinance)
2. Generates research questions and searches the web (DuckDuckGo)
3. Scrapes and reads full articles from credible financial sources
4. Synthesizes 10,000–15,000 words of research into an investment thesis
5. Selects an appropriate options strategy based on the thesis and volatility
6. Picks specific contracts (strikes, expirations, Greeks)
7. Calculates P&L curves, breakevens, and risk metrics
8. Explains every decision with citations

---

## Interfaces

### Chat Interface (primary)
A conversational LLM-powered interface. The bot walks you through the analysis in a natural dialogue and answers follow-up questions about the results.

```bash
streamlit run app_chat.py
```

### Professional Form UI
A structured form-based interface with multi-tab results, interactive P&L charts, and detailed research citations.

```bash
streamlit run app_professional.py
```

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add API keys
cp .env.example .env
# Edit .env — add at least one of OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Run
streamlit run app_chat.py
```

The app opens at `http://localhost:8501`.

Web research (DuckDuckGo + article scraping) works without API keys. LLM-powered thesis generation and chat require an OpenAI or Anthropic key.

---

## AI Concepts Demonstrated

| Concept | Where |
|---|---|
| Multi-step LLM agent | `src/research/research_orchestrator.py` — coordinates research, thesis, strategy, contracts as a sequential reasoning chain |
| Autonomous question generation | `src/research/autonomous_researcher.py` — LLM generates its own research questions across 5 categories |
| Tool use / function calling | Research loop calls web search, article scraper, and data APIs as external tools |
| Structured output parsing | `src/models/thesis.py` — LLM outputs are parsed into typed Pydantic models |
| RAG-style synthesis | Articles are retrieved, chunked, and fed to LLM for synthesis (without a vector store — simpler retrieval via targeted search) |
| Streaming chat interface | `app_chat.py` — real-time typewriter output via `st.write_stream` |
| Multi-provider LLM support | OpenAI and Anthropic Claude both supported, swappable via config |
| Conversation state management | Multi-stage chat flow with persistent context for Q&A after analysis |

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for a full walkthrough of the five-phase pipeline.

```
User Input (ticker)
      |
      v
  Data Layer         yfinance — price, fundamentals, options chain
      |
      v
  Research Layer     LLM generates questions → DuckDuckGo search
                     → article scraping → credibility filtering
      |
      v
  Thesis Layer       LLM synthesizes research → direction + conviction
                     → bull/bear cases → target price
      |
      v
  Strategy Layer     LLM selects options strategy based on thesis
                     and volatility data (IV/HV ratio, term structure)
      |
      v
  Contract Layer     Options chain filtered by delta targets
                     → specific strikes and expirations selected
      |
      v
  Analysis Layer     P&L curves, Greeks, breakevens, risk metrics
      |
      v
  Presentation       Streamlit UI or conversational chat output
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit, Plotly |
| LLM | OpenAI GPT-4o-mini / Anthropic Claude Haiku |
| Data | yfinance (stock data, options chains) |
| Web research | DuckDuckGo search, BeautifulSoup4 scraping |
| Options math | mibian (Black-Scholes Greeks) |
| Data models | Pydantic |
| Testing | pytest, GitHub Actions CI/CD |
| Config | python-dotenv |

---

## Testing & CI/CD

```bash
# Run tests locally
pytest tests/ -v
```

GitHub Actions runs tests automatically on every push across Python 3.9, 3.10, and 3.11. See the Actions tab for the latest run status.

Configuration: `.github/workflows/ci.yml`

---

## Project Structure

```
options-strategy-bot/
├── app_chat.py              # Conversational LLM chat interface
├── app_professional.py      # Form-based professional UI
├── app_research.py          # Research-focused UI
├── src/
│   ├── data/
│   │   └── yfinance_client.py       # Stock data, options chains
│   ├── research/
│   │   ├── autonomous_researcher.py  # LLM question generation
│   │   ├── web_researcher.py         # DuckDuckGo + scraping
│   │   └── research_orchestrator.py  # Research coordination
│   ├── ai/
│   │   ├── thesis_generator_v2.py    # Baseline thesis (no research)
│   │   └── thesis_generator_v3.py    # Research-enhanced thesis
│   ├── strategies/
│   │   ├── strategy_selector_v2.py   # Research-driven strategy selection
│   │   └── contract_picker_v2.py     # Adaptive contract selection
│   ├── analysis/
│   │   └── pnl_calculator.py         # P&L, Greeks, risk metrics
│   ├── visualization/
│   │   └── pnl_chart.py              # Interactive Plotly charts
│   └── models/
│       └── thesis.py                 # Pydantic data models
├── tests/
│   └── test_basic.py                 # Core component tests
├── .github/workflows/ci.yml          # GitHub Actions pipeline
├── .env.example                      # API key template
└── requirements.txt
```

---

## Example Output (NVDA)

**Research:** 15 questions generated, 11 articles read, 10,184 words analyzed

**Thesis:** BULLISH — 75% conviction
- Expected move: +15% in 30 days
- Bull case: Data center demand accelerating, AI capex expanding
- Bear case: Export restrictions, valuation premium compression

**Strategy:** Bull Call Spread
- Rationale: Elevated IV (55%) favors spread over naked long to reduce premium cost

**Contracts:**
- Long NVDA Mar $194C @ $8.00 (0.70 delta)
- Short NVDA Mar $215C @ $3.00 (0.30 delta)
- Max profit: $1,574 | Max loss: $500 | Breakeven: $199.00
