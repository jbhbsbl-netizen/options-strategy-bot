"""
Options Strategy Bot - Enhanced with LLM Strategy Analyzer

Section 1: Options Data Engine (fetch data, calculate Greeks)
Section 2: Strategy Analyzer (LLM explains reasoning)
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.alpaca_client import AlpacaClient
from calculations.greeks import add_greeks_to_chain, calculate_covered_call_metrics
from analysis.strategy_analyzer import StrategyAnalyzer


st.set_page_config(page_title="Options Strategy Bot", layout="wide")

st.title("🤖 Options Strategy Bot")
st.caption("AI-powered covered call analysis with explainable reasoning")

# Sidebar inputs
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Stock Ticker", "AAPL").upper()

    st.subheader("Options Filter")
    min_days = st.number_input("Min Days to Expiration", min_value=1, value=7)
    max_days = st.number_input("Max Days to Expiration", min_value=1, value=60)

    st.subheader("Strategy Preferences")
    risk_preference = st.select_slider(
        "Risk Tolerance",
        options=["conservative", "balanced", "aggressive"],
        value="balanced"
    )

    st.subheader("Parameters")
    risk_free_rate = st.slider("Risk-Free Rate (%)", 0.0, 10.0, 5.0) / 100

    st.divider()
    st.caption("💡 Conservative = More protection, less premium")
    st.caption("💡 Balanced = 30-delta rule, good tradeoff")
    st.caption("💡 Aggressive = Higher premium, more risk")

# Initialize clients
try:
    data_client = AlpacaClient()
    strategy_analyzer = StrategyAnalyzer()
    llm_available = True
except ValueError as e:
    data_client = AlpacaClient()
    llm_available = False
    st.warning("⚠️ LLM not configured. Add OPENAI_API_KEY to .env for AI analysis.")

# Fetch button
if st.button("🔍 Analyze Covered Call Opportunities", type="primary"):
    with st.spinner(f"Fetching data and analyzing {ticker}..."):
        try:
            # Get stock data
            stock_price = data_client.get_stock_price(ticker)
            historical_vol = data_client.get_historical_volatility(ticker, days=30)

            # Get options chain
            options_chain = data_client.get_options_chain(
                ticker,
                option_type="call",
                min_expiration_days=min_days,
                max_expiration_days=max_days
            )

            if options_chain.empty:
                st.warning(f"No options found for {ticker} in the specified date range.")
                st.stop()

            # Calculate Greeks
            options_with_greeks = add_greeks_to_chain(
                options_chain,
                stock_price=stock_price,
                volatility=historical_vol,
                risk_free_rate=risk_free_rate
            )

            # Store in session state
            st.session_state["stock_price"] = stock_price
            st.session_state["volatility"] = historical_vol
            st.session_state["options_data"] = options_with_greeks
            st.session_state["ticker"] = ticker

            # LLM Analysis
            if llm_available:
                with st.spinner("🧠 AI is analyzing strategies..."):
                    recommendation = strategy_analyzer.analyze_covered_call_opportunities(
                        ticker=ticker,
                        stock_price=stock_price,
                        options_df=options_with_greeks,
                        volatility=historical_vol,
                        user_preference=risk_preference
                    )
                    st.session_state["recommendation"] = recommendation

        except Exception as e:
            st.error(f"❌ Error: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

# Display results if data exists
if "options_data" in st.session_state:
    stock_price = st.session_state["stock_price"]
    volatility = st.session_state["volatility"]
    df = st.session_state["options_data"]
    ticker = st.session_state["ticker"]

    # Stock info
    st.subheader(f"📊 {ticker} Stock Data")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${stock_price:.2f}")
    col2.metric("30-Day Historical Vol", f"{volatility*100:.1f}%")
    col3.metric("Options Found", len(df))

    st.divider()

    # AI Recommendation (if available)
    if "recommendation" in st.session_state and llm_available:
        rec = st.session_state["recommendation"]

        st.subheader("🤖 AI Strategy Recommendation")

        # Main recommendation
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"### Recommended Strike: **${rec.recommended_strike:.2f}**")
            st.markdown(f"**Confidence:** {rec.confidence}%")

            st.markdown("#### 💡 Why This Strike?")
            st.info(rec.reasoning)

            st.markdown("#### ⚠️ Risk Assessment")
            st.warning(rec.risk_assessment)

            st.markdown("#### 📈 Market Context")
            st.caption(rec.market_context)

        with col2:
            st.markdown("#### 🔄 Alternatives")
            for alt in rec.alternatives:
                with st.expander(alt['strike']):
                    st.write(alt['explanation'])

        st.divider()

    # Options chain with Greeks
    st.subheader("📋 Options Chain with Greeks")

    # Format DataFrame for display
    display_df = df[[
        "strike", "expiration", "days_to_exp",
        "price", "delta", "gamma", "theta", "vega"
    ]].copy()

    display_df["expiration"] = pd.to_datetime(display_df["expiration"]).dt.strftime("%Y-%m-%d")
    display_df = display_df.rename(columns={
        "strike": "Strike",
        "expiration": "Expiration",
        "days_to_exp": "DTE",
        "price": "Premium",
        "delta": "Delta",
        "gamma": "Gamma",
        "theta": "Theta",
        "vega": "Vega"
    })

    # Highlight recommended strike if available
    def highlight_recommended(row):
        if "recommendation" in st.session_state:
            rec_strike = st.session_state["recommendation"].recommended_strike
            if abs(row["Strike"] - rec_strike) < 0.01:
                return ['background-color: lightgreen'] * len(row)
        # Also highlight good delta range
        if 0.25 <= row["Delta"] <= 0.35:
            return ['background-color: lightyellow'] * len(row)
        return [''] * len(row)

    styled_df = display_df.style.apply(highlight_recommended, axis=1).format({
        "Strike": "${:.2f}",
        "Premium": "${:.2f}",
        "Delta": "{:.4f}",
        "Gamma": "{:.4f}",
        "Theta": "{:.4f}",
        "Vega": "{:.4f}"
    })

    st.dataframe(styled_df, use_container_width=True, height=400)

    st.caption("💚 Green = AI recommended | 💛 Yellow = Good delta range (0.25-0.35)")

    st.divider()

    # Covered call analyzer
    st.subheader("🔧 Covered Call Calculator")
    st.caption("Select any strike to see detailed metrics")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Default to recommended strike if available
        default_strike = st.session_state.get("recommendation", None)
        if default_strike:
            default_idx = (df['strike'] - default_strike.recommended_strike).abs().idxmin()
            default_strike_val = df.loc[default_idx, 'strike']
        else:
            default_strike_val = df['strike'].iloc[0]

        selected_strike = st.selectbox(
            "Strike Price",
            options=df["strike"].unique(),
            format_func=lambda x: f"${x:.2f}",
            index=int((df['strike'] == default_strike_val).idxmax()) if default_strike else 0
        )

        selected_option = df[df["strike"] == selected_strike].iloc[0]

        st.write(f"**Expiration:** {pd.to_datetime(selected_option['expiration']).strftime('%Y-%m-%d')}")
        st.write(f"**Days to Exp:** {selected_option['days_to_exp']}")
        st.write(f"**Premium:** ${selected_option['price']:.2f}")
        st.write(f"**Delta:** {selected_option['delta']:.4f}")
        st.write(f"**Theta:** {selected_option['theta']:.4f}")

    with col2:
        metrics = calculate_covered_call_metrics(
            stock_price=stock_price,
            strike=selected_strike,
            premium=selected_option["price"]
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Premium Received", f"${metrics['premium_received']:.2f}")
        m2.metric("Max Profit", f"${metrics['max_profit']:.2f}")
        m3.metric("Return if Called", f"{metrics['return_if_called']*100:.2f}%")

        m4, m5, m6 = st.columns(3)
        m4.metric("Breakeven", f"${metrics['breakeven']:.2f}")
        m5.metric("Downside Protection", f"{metrics['downside_protection']*100:.2f}%")
        m6.metric("Max Loss", f"${metrics['max_loss']:.0f}", delta_color="inverse")

        # Explanation
        st.info(f"""
        **What this means:**
        - You sell a call at ${selected_strike:.2f} strike for ${metrics['premium_received']:.2f}
        - If {ticker} stays below ${selected_strike:.2f}, you keep the premium (profit: ${metrics['premium_received']:.2f})
        - If {ticker} goes above ${selected_strike:.2f}, shares get called away (profit: ${metrics['max_profit']:.2f})
        - You're protected down to ${metrics['breakeven']:.2f} ({metrics['downside_protection']*100:.1f}% cushion)
        """)

else:
    st.info("👆 Enter a ticker and click 'Analyze Covered Call Opportunities' to start")

    st.markdown("""
    ### What This Does

    **Section 1: Options Data Engine**
    - Fetches live options chains from Alpaca
    - Calculates Greeks (Delta, Gamma, Theta, Vega)

    **Section 2: AI Strategy Analyzer** ⭐ NEW!
    - LLM analyzes all available strikes
    - Explains WHY it recommends specific strikes
    - Provides risk assessment and alternatives
    - Considers your risk preference (conservative/balanced/aggressive)
    - Educational: Learn options strategy while it works

    **Coming Soon:**
    - Section 3: Paper Trading Executor (auto-execute trades)
    - Section 4: Performance Dashboard (track results)
    """)

# Footer
st.divider()
st.caption("Built with Claude Code + DRIVER methodology | Data: Alpaca Markets | AI: OpenAI GPT-4")
