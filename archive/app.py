"""
Options Strategy Bot - Section 1: Options Data Engine

Demonstrates fetching options chains and calculating Greeks.
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


st.set_page_config(page_title="Options Data Engine", layout="wide")

st.title("📊 Options Data Engine")
st.caption("Section 1: Fetch options chains and calculate Greeks")

# Sidebar inputs
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Stock Ticker", "AAPL").upper()

    st.subheader("Options Filter")
    min_days = st.number_input("Min Days to Expiration", min_value=1, value=7)
    max_days = st.number_input("Max Days to Expiration", min_value=1, value=60)

    st.subheader("Risk-Free Rate")
    risk_free_rate = st.slider("Risk-Free Rate (%)", 0.0, 10.0, 5.0) / 100

# Initialize client
try:
    client = AlpacaClient()
except ValueError as e:
    st.error(f"❌ {e}")
    st.info("Create a `.env` file with your Alpaca API keys. See `.env.example` for template.")
    st.stop()

# Fetch button
if st.button("Fetch Options Data", type="primary"):
    with st.spinner(f"Fetching data for {ticker}..."):
        try:
            # Get stock data
            stock_price = client.get_stock_price(ticker)
            historical_vol = client.get_historical_volatility(ticker, days=30)

            # Get options chain
            options_chain = client.get_options_chain(
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

        except Exception as e:
            st.error(f"Error fetching data: {e}")
            st.stop()

# Display results if data exists
if "options_data" in st.session_state:
    stock_price = st.session_state["stock_price"]
    volatility = st.session_state["volatility"]
    df = st.session_state["options_data"]

    # Stock info
    st.subheader(f"{ticker} Stock Data")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${stock_price:.2f}")
    col2.metric("30-Day Historical Vol", f"{volatility*100:.1f}%")
    col3.metric("Options Found", len(df))

    st.divider()

    # Options chain with Greeks
    st.subheader("Options Chain with Greeks")

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
        "price": "Price",
        "delta": "Delta",
        "gamma": "Gamma",
        "theta": "Theta",
        "vega": "Vega"
    })

    # Color code by delta (for covered calls, we want ~0.30 delta)
    def color_delta(val):
        if 0.25 <= val <= 0.35:
            return 'background-color: lightgreen'
        elif 0.15 <= val <= 0.45:
            return 'background-color: lightyellow'
        else:
            return ''

    styled_df = display_df.style.applymap(color_delta, subset=["Delta"]).format({
        "Strike": "${:.2f}",
        "Price": "${:.2f}",
        "Delta": "{:.4f}",
        "Gamma": "{:.4f}",
        "Theta": "{:.4f}",
        "Vega": "{:.4f}"
    })

    st.dataframe(styled_df, use_container_width=True, height=400)

    st.caption("💡 Green delta (0.25-0.35) = Good covered call candidates (30-delta rule)")

    st.divider()

    # Covered call analyzer
    st.subheader("Covered Call Analyzer")
    st.caption("Select a strike to see covered call metrics")

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_strike = st.selectbox(
            "Strike Price",
            options=df["strike"].unique(),
            format_func=lambda x: f"${x:.2f}"
        )

        selected_option = df[df["strike"] == selected_strike].iloc[0]

        st.write(f"**Expiration:** {pd.to_datetime(selected_option['expiration']).strftime('%Y-%m-%d')}")
        st.write(f"**Days to Exp:** {selected_option['days_to_exp']}")
        st.write(f"**Premium:** ${selected_option['price']:.2f}")
        st.write(f"**Delta:** {selected_option['delta']:.4f}")

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
        - If {ticker} goes above ${selected_strike:.2f}, your shares get called away (profit: ${metrics['max_profit']:.2f})
        - You're protected down to ${metrics['breakeven']:.2f} ({metrics['downside_protection']*100:.1f}% cushion)
        """)

else:
    st.info("👆 Enter a ticker and click 'Fetch Options Data' to start")

    st.markdown("""
    ### What This Does

    **Section 1: Options Data Engine** fetches real options data and calculates Greeks.

    **Features:**
    - Fetches live options chains from Alpaca
    - Calculates Greeks (Delta, Gamma, Theta, Vega) using Black-Scholes
    - Highlights good covered call candidates (30-delta rule)
    - Shows covered call metrics (max profit, breakeven, downside protection)

    **Next Sections:**
    - Section 2: LLM Strategy Analyzer (explains WHY to pick each strike)
    - Section 3: Paper Trading Executor (actually execute trades)
    - Section 4: Dashboard (track positions and performance)
    """)
