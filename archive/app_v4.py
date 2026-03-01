"""
Options Strategy Bot - Thesis-Driven Mode

The bot researches stocks, forms investment thesis, and recommends optimal strategy.
"""
import streamlit as st
import sys
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.alpaca_client import AlpacaClient
from research.research_agent import ResearchAgent
from research.thesis_generator import ThesisGenerator
from analysis.strategy_selector import StrategySelector


st.set_page_config(page_title="Thesis-Driven Options Bot", layout="wide")

st.title("🧠 Thesis-Driven Options Bot")
st.caption("AI researches, forms thesis, recommends optimal strategy")

# Initialize
try:
    alpaca_client = AlpacaClient()
    research_agent = ResearchAgent(alpaca_client)
    thesis_generator = ThesisGenerator()
    strategy_selector = StrategySelector()
except Exception as e:
    st.error(f"Setup error: {e}")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("🎯 Thesis-Driven Analysis")

    ticker = st.text_input("Stock Ticker", "NVDA").upper()

    st.divider()

    st.caption("**How it works:**")
    st.caption("1️⃣ Bot researches the stock")
    st.caption("2️⃣ Forms investment thesis")
    st.caption("3️⃣ Recommends best strategy")
    st.caption("4️⃣ Explains reasoning")

# Main
if st.button("🚀 Research & Generate Thesis", type="primary", use_container_width=True):
    with st.spinner(f"📊 Researching {ticker}..."):
        try:
            # Step 1: Research
            research = research_agent.research_ticker(ticker)
            st.session_state["research"] = research

        except Exception as e:
            st.error(f"Research failed: {e}")
            st.stop()

    with st.spinner("🧠 Generating investment thesis..."):
        try:
            # Step 2: Generate thesis
            research_summary = research_agent.format_research_summary(research)
            thesis = thesis_generator.generate_thesis(ticker, research_summary)
            st.session_state["thesis"] = thesis

        except Exception as e:
            st.error(f"Thesis generation failed: {e}")
            st.stop()

    with st.spinner("🎯 Selecting optimal strategy..."):
        try:
            # Step 3: Select strategy
            # Parse expected move
            move_match = re.search(r'([+-]?\d+(?:\.\d+)?)', thesis.expected_move)
            expected_move_pct = float(move_match.group(1)) if move_match else 10.0

            # Parse timeframe to days
            timeframe_match = re.search(r'(\d+)', thesis.timeframe)
            timeframe_days = int(timeframe_match.group(1)) if timeframe_match else 45

            strategy_rec = strategy_selector.select_strategy(
                thesis_direction=thesis.direction,
                conviction=thesis.conviction,
                expected_move_pct=expected_move_pct,
                timeframe_days=timeframe_days,
                stock_price=research.current_price,
                implied_vol=research.implied_volatility
            )
            st.session_state["strategy"] = strategy_rec

        except Exception as e:
            st.error(f"Strategy selection failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

# Display results
if "thesis" in st.session_state:
    research = st.session_state["research"]
    thesis = st.session_state["thesis"]
    strategy = st.session_state["strategy"]

    # Header with key info
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${research.current_price:.2f}")
    col2.metric("1-Month Change", f"{research.price_change_1m:+.1f}%")
    col3.metric("Target Price", f"${research.target_price:.2f}" if research.target_price else "N/A")
    col4.metric("Implied Vol", f"{research.implied_volatility*100:.0f}%")

    st.divider()

    # THESIS
    st.subheader("🧠 Investment Thesis")

    # Direction badge
    if thesis.direction == "BULLISH":
        st.success(f"🟢 {thesis.direction} - {thesis.conviction}% Conviction")
    elif thesis.direction == "BEARISH":
        st.error(f"🔴 {thesis.direction} - {thesis.conviction}% Conviction")
    else:
        st.info(f"⚪ {thesis.direction} - {thesis.conviction}% Conviction")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 📝 Thesis")
        st.info(thesis.thesis_summary)

        with st.expander("🐂 Bull Case"):
            st.write(thesis.bull_case)

        with st.expander("🐻 Bear Case"):
            st.write(thesis.bear_case)

    with col2:
        st.metric("Expected Move", thesis.expected_move)
        st.metric("Timeframe", thesis.timeframe)

        if thesis.catalysts:
            st.markdown("**📅 Catalysts:**")
            for cat in thesis.catalysts:
                st.caption(f"• {cat}")

        if thesis.key_risks:
            st.markdown("**⚠️ Key Risks:**")
            for risk in thesis.key_risks:
                st.caption(f"• {risk}")

    st.divider()

    # STRATEGY RECOMMENDATION
    st.subheader("🎯 Recommended Options Strategy")

    st.success(f"**Strategy: {strategy.strategy.value}**")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 💡 Why This Strategy?")
        st.info(strategy.rationale)

        st.markdown("#### 📊 Strategy Parameters")
        for key, value in strategy.parameters.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    with col2:
        st.markdown("#### 💰 Profit/Loss Profile")
        st.metric("Expected Profit", strategy.expected_profit)
        st.metric("Max Risk", strategy.max_risk, delta_color="inverse")
        st.metric("Breakeven", strategy.breakeven)

    st.divider()

    # RESEARCH DATA
    with st.expander("📊 Full Research Data"):
        st.markdown("### Fundamentals")
        cols = st.columns(3)
        cols[0].metric("Market Cap", f"${research.market_cap/1e9:.1f}B")
        cols[1].metric("P/E Ratio", f"{research.pe_ratio:.1f}" if research.pe_ratio else "N/A")
        cols[2].metric("Profit Margin", f"{research.profit_margin*100:.1f}%" if research.profit_margin else "N/A")

        st.markdown("### Performance")
        cols = st.columns(3)
        cols[0].metric("1-Day", f"{research.price_change_1d:+.2f}%")
        cols[1].metric("1-Week", f"{research.price_change_1w:+.2f}%")
        cols[2].metric("1-Month", f"{research.price_change_1m:+.2f}%")

        if research.recent_news:
            st.markdown("### Recent News")
            for i, news in enumerate(research.recent_news[:3], 1):
                st.caption(f"{i}. **{news['title']}** ({news['publisher']})")

else:
    st.info("👆 Enter a ticker and click 'Research & Generate Thesis' to start")

    st.markdown("""
    ## How This Bot Works:

    **1. Research Phase 📊**
    - Fetches current price, performance, volume
    - Gets fundamentals (P/E, margins, growth)
    - Reads recent news headlines
    - Checks analyst ratings and target prices

    **2. Thesis Generation 🧠**
    - AI analyzes all research data
    - Forms directional view (BULLISH/BEARISH/NEUTRAL)
    - Assigns conviction level (0-100%)
    - Predicts expected move and timeframe
    - Explains bull/bear cases

    **3. Strategy Selection 🎯**
    - Maps thesis → optimal options strategy:
      - Very Bullish (75%+) → Long Call
      - Moderate Bullish (55-75%) → Bull Call Spread
      - Slightly Bullish → Covered Call
      - Neutral + High IV → Iron Condor
      - Bearish → Put strategies
    - Calculates strike prices and expirations
    - Shows profit/loss profile

    **4. Execution Ready**
    - Clear parameters for the trade
    - Defined risk/reward
    - Explainable reasoning

    ---

    **This is true AI-driven options trading: Research → Hypothesis → Strategy**
    """)

# Footer
st.divider()
st.caption("🧠 Thesis-Driven Trading | Built with Claude Code + DRIVER | Powered by GPT-4")
