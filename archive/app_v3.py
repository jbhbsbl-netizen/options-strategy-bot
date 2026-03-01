"""
Options Strategy Bot - Autonomous Mode

Section 1: Options Data Engine
Section 2: AI Strategy Analyzer
Section 3: Portfolio Scanner (NEW) - Finds best opportunities across tickers
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
from analysis.portfolio_scanner import PortfolioScanner, DEFAULT_WATCHLIST


st.set_page_config(page_title="Options Strategy Bot - Autonomous", layout="wide")

st.title("🤖 Options Strategy Bot - Autonomous Mode")
st.caption("AI-powered covered call finder that scans multiple tickers")

# Initialize clients
try:
    data_client = AlpacaClient()
    strategy_analyzer = StrategyAnalyzer()
    portfolio_scanner = PortfolioScanner(data_client, strategy_analyzer)
    llm_available = True
except ValueError as e:
    st.error(f"Setup error: {e}")
    st.stop()

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    # Mode selection
    mode = st.radio(
        "Analysis Mode",
        options=["🔍 Autonomous - Find Best Opportunities", "📊 Manual - Analyze Specific Ticker"],
        index=0
    )

    st.divider()

    if mode.startswith("🔍"):
        # Autonomous mode settings
        st.subheader("Watchlist")

        use_default = st.checkbox("Use default watchlist", value=True)

        if use_default:
            st.caption(f"Scanning {len(DEFAULT_WATCHLIST)} tickers:")
            st.caption(", ".join(DEFAULT_WATCHLIST[:8]) + "...")
            watchlist = DEFAULT_WATCHLIST
        else:
            watchlist_input = st.text_area(
                "Enter tickers (comma-separated)",
                value="AAPL,MSFT,GOOGL,NVDA,TSLA",
                height=100
            )
            watchlist = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]
            st.caption(f"Will scan: {', '.join(watchlist[:5])}{'...' if len(watchlist) > 5 else ''}")

        top_n = st.slider("Show top N opportunities", 1, 10, 5)

    else:
        # Manual mode settings
        st.subheader("Ticker Selection")
        ticker = st.text_input("Stock Ticker", "AAPL").upper()

    st.subheader("Strategy Preferences")
    risk_preference = st.select_slider(
        "Risk Tolerance",
        options=["conservative", "balanced", "aggressive"],
        value="balanced"
    )

    risk_free_rate = st.slider("Risk-Free Rate (%)", 0.0, 10.0, 5.0) / 100

    st.divider()
    st.caption("💡 Autonomous mode scans ALL expirations")
    st.caption("💡 Finds best opportunities automatically")

# Main content
if mode.startswith("🔍"):
    # AUTONOMOUS MODE
    st.subheader("🔍 Autonomous Opportunity Finder")
    st.caption("Bot will scan multiple tickers and ALL expiration dates to find best covered calls")

    if st.button("🚀 Find Best Opportunities", type="primary", use_container_width=True):
        with st.spinner(f"Scanning {len(watchlist)} tickers across all expirations..."):
            try:
                opportunities = portfolio_scanner.scan_multiple(
                    tickers=watchlist,
                    risk_preference=risk_preference,
                    max_workers=5
                )

                if not opportunities:
                    st.warning("No opportunities found. Try a different watchlist.")
                    st.stop()

                st.session_state["opportunities"] = opportunities[:top_n]
                st.session_state["mode"] = "autonomous"

            except Exception as e:
                st.error(f"Error scanning: {e}")
                import traceback
                st.code(traceback.format_exc())
                st.stop()

    # Display results
    if "opportunities" in st.session_state and st.session_state.get("mode") == "autonomous":
        opps = st.session_state["opportunities"]

        st.success(f"✅ Found {len(opps)} opportunities! Here are the best:")

        st.divider()

        # Display top opportunities
        for i, opp in enumerate(opps, 1):
            # For #1, get LLM recommendation FIRST to override scanner's pick
            llm_override = None
            if llm_available and i == 1:
                with st.spinner(f"Getting AI analysis for {opp.ticker}..."):
                    try:
                        # Fetch full options data
                        stock_price = data_client.get_stock_price(opp.ticker)
                        volatility = data_client.get_historical_volatility(opp.ticker)
                        options_chain = data_client.get_options_chain(
                            opp.ticker,
                            option_type="call",
                            min_expiration_days=1,
                            max_expiration_days=365
                        )
                        options_with_greeks = add_greeks_to_chain(
                            options_chain, stock_price, volatility
                        )

                        rec = strategy_analyzer.analyze_covered_call_opportunities(
                            ticker=opp.ticker,
                            stock_price=stock_price,
                            options_df=options_with_greeks,
                            volatility=volatility,
                            user_preference=risk_preference
                        )

                        # Find the option that matches LLM's recommendation
                        llm_option = options_with_greeks[
                            options_with_greeks['strike'] == rec.recommended_strike
                        ]

                        if not llm_option.empty:
                            llm_option = llm_option.iloc[0]
                            # Override the opportunity data with LLM's pick
                            llm_override = {
                                'strike': float(llm_option['strike']),
                                'premium': float(llm_option['price']),
                                'delta': float(llm_option['delta']),
                                'theta': float(llm_option['theta']),
                                'expiration': str(llm_option['expiration']),
                                'days_to_exp': int(llm_option['days_to_exp']),
                                'recommendation': rec
                            }

                    except Exception as e:
                        st.caption(f"AI analysis failed: {e}")

            # Use LLM override if available, otherwise use scanner's pick
            display_strike = llm_override['strike'] if llm_override else opp.strike
            display_premium = llm_override['premium'] if llm_override else opp.premium
            display_delta = llm_override['delta'] if llm_override else opp.delta
            display_theta = llm_override['theta'] if llm_override else opp.theta
            display_exp = llm_override['expiration'] if llm_override else opp.expiration
            display_days = llm_override['days_to_exp'] if llm_override else opp.days_to_exp

            # Calculate annual return for display
            premium_yield = (display_premium / opp.stock_price) * 100
            display_annual_return = (premium_yield / display_days) * 365

            title_prefix = "🤖 AI Pick" if llm_override else f"#{i}"

            with st.expander(
                f"{title_prefix}: {opp.ticker} @ ${opp.stock_price:.2f} - "
                f"${display_strike:.2f} strike - {display_annual_return:.1f}% annual",
                expanded=(i == 1)
            ):
                if llm_override:
                    st.success("✨ AI has optimized this recommendation")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Stock Price", f"${opp.stock_price:.2f}")
                    st.metric("Strike", f"${display_strike:.2f}")
                    st.metric("Premium", f"${display_premium:.2f}")

                with col2:
                    st.metric("Expiration", display_exp)
                    st.metric("Days to Exp", f"{display_days}d")
                    st.metric("Delta", f"{display_delta:.3f}")

                with col3:
                    st.metric("Annual Return", f"{display_annual_return:.1f}%")
                    st.metric("Theta", f"{display_theta:.3f}")
                    if not llm_override:
                        st.metric("Score", f"{opp.score:.1f}/100")

                # Calculate full metrics
                from calculations.greeks import calculate_covered_call_metrics
                metrics = calculate_covered_call_metrics(
                    stock_price=opp.stock_price,
                    strike=display_strike,
                    premium=display_premium
                )

                st.markdown("#### 📊 Covered Call Metrics")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Max Profit", f"${metrics['max_profit']:.2f}")
                m2.metric("Return if Called", f"{metrics['return_if_called']*100:.2f}%")
                m3.metric("Breakeven", f"${metrics['breakeven']:.2f}")
                m4.metric("Protection", f"{metrics['downside_protection']*100:.2f}%")

                # Show LLM reasoning if available
                if llm_override:
                    rec = llm_override['recommendation']
                    st.markdown("#### 🤖 AI Analysis")
                    st.info(rec.reasoning)
                    st.caption(f"**Risk Assessment:** {rec.risk_assessment}")
                    st.caption(f"**Market Context:** {rec.market_context}")

else:
    # MANUAL MODE
    st.subheader(f"📊 Analyzing {ticker}")
    st.caption("Manual mode: Analyze a specific ticker with ALL expiration dates")

    if st.button("🔍 Analyze This Ticker", type="primary", use_container_width=True):
        with st.spinner(f"Fetching all options for {ticker}..."):
            try:
                # Get stock data
                stock_price = data_client.get_stock_price(ticker)
                volatility = data_client.get_historical_volatility(ticker, days=30)

                # Get ALL options (no date restrictions)
                options_chain = data_client.get_options_chain(
                    ticker,
                    option_type="call",
                    min_expiration_days=1,
                    max_expiration_days=365  # All available
                )

                if options_chain.empty:
                    st.warning(f"No options found for {ticker}")
                    st.stop()

                # Calculate Greeks
                options_with_greeks = add_greeks_to_chain(
                    options_chain,
                    stock_price=stock_price,
                    volatility=volatility,
                    risk_free_rate=risk_free_rate
                )

                st.session_state["stock_price"] = stock_price
                st.session_state["volatility"] = volatility
                st.session_state["options_data"] = options_with_greeks
                st.session_state["ticker"] = ticker
                st.session_state["mode"] = "manual"

                # LLM Analysis
                with st.spinner("🧠 AI analyzing all expirations..."):
                    recommendation = strategy_analyzer.analyze_covered_call_opportunities(
                        ticker=ticker,
                        stock_price=stock_price,
                        options_df=options_with_greeks,
                        volatility=volatility,
                        user_preference=risk_preference
                    )
                    st.session_state["recommendation"] = recommendation

            except Exception as e:
                st.error(f"Error: {e}")
                import traceback
                st.code(traceback.format_exc())
                st.stop()

    # Display manual mode results
    if "options_data" in st.session_state and st.session_state.get("mode") == "manual":
        stock_price = st.session_state["stock_price"]
        volatility = st.session_state["volatility"]
        df = st.session_state["options_data"]
        ticker = st.session_state["ticker"]

        # Stock info
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${stock_price:.2f}")
        col2.metric("30-Day Vol", f"{volatility*100:.1f}%")
        col3.metric("Total Options", len(df))

        st.divider()

        # AI Recommendation
        if "recommendation" in st.session_state:
            rec = st.session_state["recommendation"]

            st.subheader("🤖 AI Recommendation")
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### ${rec.recommended_strike:.2f} Strike")
                st.info(rec.reasoning)
                st.caption(f"**Risk:** {rec.risk_assessment}")

            with col2:
                st.metric("Confidence", f"{rec.confidence}%")

        st.divider()

        # Show expiration breakdown
        st.subheader("📅 Options by Expiration")
        expirations = df['expiration'].unique()
        st.caption(f"Found {len(expirations)} different expiration dates")

        # Group by expiration
        exp_summary = df.groupby('expiration').agg({
            'strike': 'count',
            'days_to_exp': 'first',
            'price': 'mean',
            'delta': 'mean'
        }).reset_index()
        exp_summary.columns = ['Expiration', 'Num Options', 'Days', 'Avg Premium', 'Avg Delta']
        exp_summary = exp_summary.sort_values('Days')

        st.dataframe(
            exp_summary.style.format({
                'Avg Premium': '${:.2f}',
                'Avg Delta': '{:.3f}'
            }),
            use_container_width=True
        )

# Footer
st.divider()
st.caption("🤖 Autonomous mode scans ALL tickers & expirations | Built with Claude Code + DRIVER")
