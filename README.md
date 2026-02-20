# 🧠 Research-Enhanced Options Strategy Bot

**An AI-powered options trading bot that researches every decision it makes.**

The bot autonomously searches the web, reads articles, and makes data-driven decisions about options strategies. It doesn't just follow hardcoded rules—it genuinely learns from current market information.

---

## ✨ Features

### **Autonomous Web Research**
- Generates intelligent research questions with LLM
- Searches DuckDuckGo for relevant articles
- Scrapes content from credible financial sources
- Analyzes 10,000-15,000 words per ticker
- Cites sources for transparency

### **Complete Analysis Pipeline**
1. **Stock Context** - Price, fundamentals, news, trends
2. **AI Thesis** - BULLISH/BEARISH/NEUTRAL/UNPREDICTABLE with conviction
3. **Strategy Selection** - Data-driven recommendation (not rules)
4. **Contract Selection** - Adaptive strikes and expirations
5. **Risk Analysis** - P/L curves, Greeks, metrics

### **Professional UI**
- Clean Streamlit interface
- Interactive Plotly charts
- Research transparency (shows all sources)
- User controls for research depth
- Mobile-responsive design

---

## 🚀 Quick Start

### **Installation**

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API keys (optional - only for OpenAI/Anthropic LLMs)
cp .env.example .env
# Edit .env and add your API keys
```

### **Run the App**

```bash
python -m streamlit run app_research.py
```

App will open at: **http://localhost:8501**

### **Usage**

1. Enter a stock ticker (e.g., "NVDA")
2. Configure research settings:
   - Toggle "Enable Web Research" on/off
   - Select articles per question (1-3)
3. Click "Analyze Stock"
4. Wait 2-3 minutes for complete analysis
5. Review complete results with research citations

---

## 📊 How It Works

### **Traditional Approach (V1)**
```
IF conviction >= 70% THEN recommend Long Call
  → Hardcoded rule
  → No learning
  → No explanation
```

### **Research-Enhanced Approach (V2/V3)**
```
Research: "Bull call spread vs long call - when to choose?"
  → Bot reads 3 articles from Fidelity, TastyLive, MarketChameleon
  → Learns: "Spreads work better in high IV environments"
  → Checks: Current IV is 55% (elevated)
  → Decides: Recommend Bull Call Spread
  → Explains: "Based on research from [sources], spreads work better..."
```

### **Research at Every Decision Point**

#### **1. Thesis Generation**
- **Researches:** Stock fundamentals, earnings, competitive position
- **Questions:** "What were NVDA's earnings?", "Market position?", "Growth drivers?"
- **Output:** BULLISH with 75% conviction based on 30K+ words

#### **2. Strategy Selection**
- **Researches:** Which strategies work best for this stock
- **Questions:** "Bull call spread vs long call?", "What works for NVDA?"
- **Output:** Bull Call Spread (research-informed, not rule-based)

#### **3. Contract Selection**
- **Researches:** Optimal delta, expiration timing, spread width
- **Questions:** "Optimal delta for bullish trades?", "Best expiration?"
- **Output:** 0.70 delta, 30 DTE (research-optimized)

#### **4. Risk Analysis**
- Calculates P/L at all price points
- Shows max profit, max loss, breakevens
- Interactive chart with profit/loss zones
- Portfolio Greeks (Delta, Theta, Vega, Gamma)

---

## 🎯 Example Analysis (NVDA)

### **Research Generated:**
- **15 questions** across 5 categories
- **11 articles** scraped from credible sources
- **10,184 words** analyzed
- **11 unique sources:** Fidelity, TastyLive, MarketChameleon, etc.

### **Thesis:**
- Direction: BULLISH
- Conviction: 75%
- Expected Move: +15% in 30 days
- Target Price: $216.82

### **Strategy:**
- Selected: Bull Call Spread (research-informed)
- Why: "Research found spreads work better in elevated IV (current: 55%)"

### **Contracts:**
- Long: NVDA Mar20 $194C @ $8.00 (0.70 delta)
- Short: NVDA Mar20 $215C @ $3.00 (0.30 delta)
- Research: "Optimal delta 60-70 for high volatility stocks"

### **Risk/Reward:**
- Max Profit: $1,574
- Max Loss: $500
- Breakeven: $199.00
- Risk/Reward: 3.15:1

---

## 📁 Project Structure

```
options-strategy-bot/
├── app_research.py              # Main Streamlit UI
├── src/
│   ├── data/
│   │   └── yfinance_client.py   # Stock data fetching
│   ├── ai/
│   │   ├── thesis_generator_v2.py   # Baseline thesis
│   │   └── thesis_generator_v3.py   # With research
│   ├── strategies/
│   │   ├── strategy_selector.py     # V1 (rules)
│   │   ├── strategy_selector_v2.py  # V2 (research)
│   │   ├── contract_picker.py       # V1 (fixed)
│   │   └── contract_picker_v2.py    # V2 (adaptive)
│   ├── analysis/
│   │   └── pnl_calculator.py    # P/L and Greeks
│   ├── visualization/
│   │   └── pnl_chart.py         # Interactive charts
│   ├── research/
│   │   ├── web_researcher.py    # DuckDuckGo + scraping
│   │   ├── autonomous_researcher.py  # LLM questions
│   │   └── research_orchestrator.py  # Coordinator
│   └── models/
│       └── thesis.py            # Data models
├── tests/                       # Test files
└── docs/                        # Documentation
```

---

## ⚙️ Configuration

### **Research Settings**

```python
# In app_research.py sidebar:

enable_research = True  # Toggle research on/off

articles_per_question = 1  # 1 = fast (90s)
                          # 2 = moderate (2-3 min)
                          # 3 = deep (4-5 min)
```

### **API Keys (Optional)**

For LLM-powered question generation, add to `.env`:

```bash
# OpenAI
OPENAI_API_KEY=your_key_here

# OR Anthropic
ANTHROPIC_API_KEY=your_key_here
```

Note: Research still works without API keys (uses default questions).

---

## 📈 Performance

### **Time:**
- Fast mode (1 article/question): ~90 seconds
- Moderate mode (2 articles/question): ~2-3 minutes
- Deep mode (3 articles/question): ~4-5 minutes

### **Cost:**
- Web search: FREE (DuckDuckGo)
- Article scraping: FREE
- LLM (question generation): ~$0.015
- **Total: ~$0.015 per analysis**

### **Data Volume:**
- Baseline: 21,000 words (yfinance + SEC)
- Research: 10,000-15,000 words (web articles)
- **Total: 31,000-36,000 words per analysis**

---

## 🧪 Testing

Run tests to verify all components:

```bash
# Test complete pipeline
python test_complete_pipeline_v2.py

# Test P/L calculator
python test_pnl.py

# Test research system
python test_autonomous_research.py

# Test V3 vs V2 comparison
python test_thesis_v3_vs_v2.py
```

---

## 📚 Documentation

- **OPTION_A_COMPLETE.md** - Research integration into thesis
- **OPTION_2_COMPLETE.md** - Extended research to all decisions
- **RESEARCH_ENHANCED_UI_COMPLETE.md** - Complete UI documentation
- **SESSION_PROGRESS.md** - Development progress tracker

---

## ⚠️ Disclaimer

**This bot is for educational purposes only.**

- Not financial advice
- Research is from public sources (accuracy not guaranteed)
- Options trading involves substantial risk
- Past performance doesn't indicate future results
- Always do your own due diligence
- Consult a licensed financial advisor

**Use at your own risk.**

---

## 🎉 Status

**Section 1: COMPLETE**

✅ Stock context
✅ AI thesis with research
✅ Strategy selection with research
✅ Contract selection with research
✅ P/L visualization
✅ Streamlit UI

**The bot now:**
- Researches every decision it makes
- Learns from the web autonomously
- Explains reasoning with citations
- Adapts to each stock's characteristics
- Provides complete risk analysis

**This is true AI-powered options trading with autonomous intelligence!** 🚀

---

**Ready to analyze your first stock?**

```bash
python -m streamlit run app_research.py
```

**Happy Trading! 📈**
