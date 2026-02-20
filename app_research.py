"""
Research-Enhanced Options Strategy Bot - Complete Pipeline

This version integrates autonomous web research at every decision point:
1. Thesis Generation - researches stock fundamentals, risk, market conditions
2. Strategy Selection - researches which strategies work best
3. Contract Selection - researches optimal delta, expiration, spread width
4. P/L Analysis - displays risk metrics with interactive charts

The bot genuinely teaches itself by searching and reading articles from the web.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data.yfinance_client import YFinanceClient
from ai.thesis_generator_v3 import ThesisGeneratorV3
from strategies.strategy_selector_v2 import StrategySelectV2
from strategies.contract_picker_v2 import ContractPickerV2
from analysis.pnl_calculator import PnLCalculator
from visualization.pnl_chart import create_pnl_chart, create_metrics_table

# Page config
st.set_page_config(
    page_title="Research-Enhanced Options Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
    st.session_state.ticker = ""
    st.session_state.thesis = None
    st.session_state.research = None
    st.session_state.strategy = None
    st.session_state.earnings_strategy = None  # ADDITIONAL earnings alternative
    st.session_state.contracts = None
    st.session_state.pnl_analysis = None
    st.session_state.stock_data = None
    st.session_state.earnings_info = None

# Sidebar
with st.sidebar:
    st.markdown("### 🧠 Research-Enhanced Bot")
    st.caption("The bot researches EVERY decision it makes")

    st.divider()

    # Input
    ticker_input = st.text_input(
        "Stock Ticker",
        value="NVDA",
        help="Enter a stock ticker to analyze"
    ).upper()

    # Research settings
    st.markdown("#### Research Settings")

    enable_research = st.checkbox(
        "Enable Web Research",
        value=True,
        help="Bot will search and read articles from the web"
    )

    if enable_research:
        articles_per_question = st.slider(
            "Articles per Question",
            min_value=1,
            max_value=3,
            value=1,
            help="More articles = deeper research (slower)"
        )
    else:
        articles_per_question = 1

    st.divider()

    # Analyze button
    analyze_btn = st.button(
        "🚀 Analyze Stock",
        type="primary",
        use_container_width=True,
        disabled=not ticker_input
    )

    st.divider()

    st.caption("**How it works:**")
    st.caption("1️⃣ Researches stock fundamentals")
    st.caption("2️⃣ Generates AI thesis")
    st.caption("3️⃣ Researches optimal strategy")
    st.caption("4️⃣ Researches contract parameters")
    st.caption("5️⃣ Calculates risk/reward")

# Main content
st.markdown('<div class="main-header">🧠 Research-Enhanced Options Strategy Bot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Autonomous intelligence that researches every decision</div>', unsafe_allow_html=True)

# Run analysis
if analyze_btn and ticker_input:
    st.session_state.ticker = ticker_input
    st.session_state.analysis_complete = False

    # Initialize clients
    try:
        yfinance_client = YFinanceClient()
        thesis_generator = ThesisGeneratorV3(enable_research=enable_research)
        strategy_selector = StrategySelectV2(enable_research=enable_research)
        contract_picker = ContractPickerV2(enable_research=enable_research)
        pnl_calculator = PnLCalculator()
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

    # Phase 1: Fetch baseline data
    with st.spinner(f"📊 Fetching data for {ticker_input}..."):
        try:
            stock_data = yfinance_client.get_stock_data(ticker_input)
            news = yfinance_client.get_news(ticker_input, max_items=5)
            current_price = stock_data['current_price']

            # Calculate historical volatility
            try:
                historical_vol = yfinance_client.get_historical_volatility(ticker_input, days=30)
            except:
                historical_vol = 0.40  # Default fallback

            # Fetch earnings date (ADDITIONAL layer - not required for core analysis)
            try:
                earnings_info = yfinance_client.get_earnings_date(ticker_input)
                st.session_state.earnings_info = earnings_info
            except:
                st.session_state.earnings_info = None

            st.session_state.stock_data = stock_data
            st.success(f"✅ Fetched stock data - Current price: ${current_price:.2f}")
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

    # Phase 2: Generate thesis with research
    with st.spinner(f"🧠 Generating investment thesis (with research: {enable_research})..."):
        try:
            # Pass earnings_info (ADDITIONAL context - not required)
            thesis = thesis_generator.generate_thesis(
                ticker=ticker_input,
                stock_data=stock_data,
                news=news,
                historical_vol=historical_vol,
                enable_research=enable_research,
                earnings_info=st.session_state.earnings_info,
                articles_per_question=articles_per_question
            )
            st.session_state.thesis = thesis

            # Extract research metadata
            if enable_research and thesis.data_references.get("research_enabled"):
                research_articles = thesis.data_references.get("research_articles", 0)
                research_words = thesis.data_references.get("research_words", 0)
                research_sources = thesis.data_references.get("research_sources", [])
                st.success(f"✅ Thesis generated - Research: {research_articles} articles, {research_words:,} words")
            else:
                st.success(f"✅ Thesis generated (no research)")
        except Exception as e:
            st.error(f"Thesis generation failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

    # Phase 3: Select strategy with research
    with st.spinner(f"🎯 Selecting optimal strategy (with research: {enable_research})..."):
        try:
            # Parse expected move
            import re
            move_match = re.search(r'([+-]?\d+(?:\.\d+)?)', thesis.expected_move)
            expected_move_pct = float(move_match.group(1)) / 100 if move_match else 0.15

            # Parse timeframe
            timeframe_match = re.search(r'(\d+)', thesis.timeframe)
            timeframe_days = int(timeframe_match.group(1)) if timeframe_match else 30

            # Calculate implied vol from options (if available)
            try:
                options_data = yfinance_client.get_options_chain(ticker_input)
                implied_vol = options_data.get('implied_volatility', historical_vol)
            except:
                implied_vol = historical_vol

            # Pass earnings_info (ADDITIONAL context)
            strategy, research, earnings_strategy = strategy_selector.select_strategy_with_research(
                ticker=ticker_input,
                direction=thesis.direction,
                conviction=thesis.conviction,
                expected_move_pct=expected_move_pct,
                timeframe_days=timeframe_days,
                current_price=current_price,
                historical_vol=historical_vol,
                implied_vol=implied_vol,
                earnings_info=st.session_state.earnings_info,  # ADDITIONAL layer
                articles_per_question=articles_per_question
            )

            st.session_state.strategy = strategy
            st.session_state.earnings_strategy = earnings_strategy  # Store earnings alternative
            st.session_state.research = research

            if earnings_strategy:
                st.success(f"✅ Primary: {strategy.strategy.value} + Earnings Alternative: {earnings_strategy.strategy.value}")
            else:
                st.success(f"✅ Strategy selected: {strategy.strategy.value}")
        except Exception as e:
            st.error(f"Strategy selection failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

    # Phase 4: Pick contracts with research
    with st.spinner(f"📋 Selecting contracts (with research: {enable_research})..."):
        try:
            # Get options chain
            try:
                options_chain = yfinance_client.get_options_chain_all_expirations(ticker_input)
            except:
                options_chain = pd.DataFrame()

            contracts, contract_insights = contract_picker.pick_contracts_with_research(
                ticker=ticker_input,
                strategy=strategy.strategy.value,
                direction=thesis.direction,
                expected_move_pct=expected_move_pct,
                timeframe_days=timeframe_days,
                current_price=current_price,
                options_chain=options_chain,
                research=research
            )

            st.session_state.contracts = contracts
            st.success(f"✅ Contracts selected: {len(contracts)} contracts")
        except Exception as e:
            st.error(f"Contract selection failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

    # Phase 5: Calculate P/L
    with st.spinner("💰 Calculating risk/reward analysis..."):
        try:
            pnl_analysis = pnl_calculator.calculate_complete_analysis(
                contracts=contracts,
                current_price=current_price,
                volatility=implied_vol,
                days_to_expiration=timeframe_days
            )

            st.session_state.pnl_analysis = pnl_analysis
            st.success(f"✅ P/L analysis complete")
        except Exception as e:
            st.error(f"P/L calculation failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

    st.session_state.analysis_complete = True
    st.balloons()

# Display results
if st.session_state.analysis_complete and st.session_state.thesis:
    ticker = st.session_state.ticker
    thesis = st.session_state.thesis
    strategy = st.session_state.strategy
    contracts = st.session_state.contracts
    pnl_analysis = st.session_state.pnl_analysis
    stock_data = st.session_state.stock_data
    research = st.session_state.research

    # ===== SECTION 1: STOCK CONTEXT =====
    st.markdown("---")
    st.markdown("### 📊 Stock Context")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric(
        "Current Price",
        f"${stock_data['current_price']:.2f}",
        delta=f"{stock_data.get('price_change_pct', 0):.2f}%"
    )

    col2.metric(
        "Market Cap",
        f"${stock_data.get('market_cap', 0) / 1e9:.1f}B"
    )

    col3.metric(
        "P/E Ratio",
        f"{stock_data.get('pe_ratio', 0):.1f}" if stock_data.get('pe_ratio') else "N/A"
    )

    col4.metric(
        "52-Week Range",
        f"${stock_data.get('52_week_low', 0):.0f} - ${stock_data.get('52_week_high', 0):.0f}"
    )

    col5.metric(
        "Volume",
        f"{stock_data.get('volume', 0) / 1e6:.1f}M"
    )

    # Earnings info (ADDITIONAL context - not required)
    earnings_info = st.session_state.earnings_info
    if earnings_info:
        timing_str = f" ({earnings_info['timing']})" if earnings_info['timing'] else ""
        col6.metric(
            "Next Earnings",
            f"{earnings_info['date_str']}{timing_str}",
            delta=f"{earnings_info['days_until']} days"
        )
    else:
        col6.metric(
            "Next Earnings",
            "N/A"
        )

    # ===== SECTION 2: AI THESIS =====
    st.markdown("---")
    st.markdown("### 🧠 AI Investment Thesis")

    # Direction badge
    if thesis.direction == "BULLISH":
        st.success(f"🟢 **{thesis.direction}** - {thesis.conviction}% Conviction")
    elif thesis.direction == "BEARISH":
        st.error(f"🔴 **{thesis.direction}** - {thesis.conviction}% Conviction")
    elif thesis.direction == "NEUTRAL":
        st.info(f"⚪ **{thesis.direction}** - {thesis.conviction}% Conviction")
    else:
        st.warning(f"⚠️ **{thesis.direction}** - {thesis.conviction}% Conviction")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 📝 Thesis Summary")
        st.info(thesis.thesis_summary)

        with st.expander("🐂 Bull Case"):
            st.write(thesis.bull_case)

        with st.expander("🐻 Bear Case"):
            st.write(thesis.bear_case)

        with st.expander("📊 Data References"):
            if thesis.data_references:
                for key, value in thesis.data_references.items():
                    if key not in ["research_enabled", "research_articles", "research_words", "research_sources"]:
                        st.write(f"**{key}:** {value}")

    with col2:
        st.metric("Expected Move", thesis.expected_move)
        st.metric("Timeframe", thesis.timeframe)
        st.metric("Target Price", f"${thesis.target_price:.2f}" if thesis.target_price else "N/A")

        if thesis.catalysts:
            st.markdown("**📅 Catalysts:**")
            for cat in thesis.catalysts:
                st.caption(f"• {cat}")

        if thesis.key_risks:
            st.markdown("**⚠️ Key Risks:**")
            for risk in thesis.key_risks:
                st.caption(f"• {risk}")

    # Research metadata
    if thesis.data_references.get("research_enabled"):
        st.info(f"🔬 **Research Used:** {thesis.data_references.get('research_articles', 0)} articles, "
                f"{thesis.data_references.get('research_words', 0):,} words from "
                f"{len(thesis.data_references.get('research_sources', []))} sources")

        with st.expander("📚 Research Sources"):
            sources = thesis.data_references.get('research_sources', [])
            for i, source in enumerate(sources[:10], 1):
                st.caption(f"{i}. {source}")

    # ===== SECTION 3: STRATEGY RECOMMENDATION =====
    st.markdown("---")
    st.markdown("### 🎯 Recommended Options Strategy")

    st.success(f"**Strategy: {strategy.strategy.value}**")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 💡 Why This Strategy?")
        st.info(strategy.rationale)

        st.markdown("#### ⚙️ Strategy Characteristics")
        st.write(f"**Risk Level:** {strategy.risk_level}")
        st.write(f"**Capital Required:** {strategy.capital_required}")
        st.write(f"**Max Profit:** {strategy.max_profit}")
        st.write(f"**Max Loss:** {strategy.max_loss}")
        st.write(f"**Breakeven:** {strategy.breakeven}")

        if strategy.ideal_conditions:
            st.markdown("**✅ Ideal When:**")
            for cond in strategy.ideal_conditions:
                st.caption(f"• {cond}")

    with col2:
        st.markdown("#### 📋 Selected Contracts")
        for i, contract in enumerate(contracts, 1):
            st.markdown(f"**Contract {i}:**")
            st.write(f"🔹 **{contract.action}** {contract.display_name}")
            st.write(f"   Strike: ${contract.strike:.2f}")
            st.write(f"   Premium: ${contract.premium:.2f}")
            st.write(f"   Delta: {contract.delta:.2f}")
            st.write(f"   Exp: {contract.expiration}")
            st.divider()

    # Research metadata for strategy/contracts
    if research and research.total_questions > 0:
        st.info(f"🔬 **Strategy Research:** {research.total_articles} articles, "
                f"{research.total_words:,} words analyzed")

        with st.expander("📚 Strategy Research Questions"):
            if research.strategy_research:
                st.markdown("**Strategy Selection:**")
                for q in research.strategy_research.questions:
                    st.caption(f"• {q.question}")

            if research.contract_research:
                st.markdown("**Contract Selection:**")
                for q in research.contract_research.questions:
                    st.caption(f"• {q.question}")

            # Show earnings research if available (ADDITIONAL layer)
            if research.earnings_research:
                st.markdown("**Earnings Patterns (ADDITIONAL):**")
                for q in research.earnings_research.questions:
                    st.caption(f"• {q.question}")

    # EARNINGS ALTERNATIVE (if clear opportunity found)
    earnings_strategy = st.session_state.earnings_strategy
    if earnings_strategy:
        st.markdown("---")
        st.markdown("### 📅 Earnings Alternative Strategy (OPTIONAL)")

        st.warning(f"**Alternative for Earnings Play: {earnings_strategy.strategy.value}**")

        st.markdown("#### 💡 Why Consider This Earnings Play?")
        st.info(earnings_strategy.rationale)

        st.markdown("**Choose Based on Preference:**")
        st.write("- **Primary Strategy** → Fundamental play based on research")
        st.write("- **Earnings Alternative** → Volatility play based on earnings patterns")

        if st.session_state.earnings_info:
            earnings = st.session_state.earnings_info
            st.caption(f"Earnings: {earnings['date_str']} ({earnings['timing']}) - {earnings['days_until']} days")

    # ===== SECTION 4: RISK/REWARD ANALYSIS =====
    st.markdown("---")
    st.markdown("### 💰 Risk/Reward Analysis")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Max Profit",
        f"${pnl_analysis['max_profit']:,.2f}",
        delta="Upside"
    )

    col2.metric(
        "Max Loss",
        f"${abs(pnl_analysis['max_loss']):,.2f}",
        delta="Risk",
        delta_color="inverse"
    )

    col3.metric(
        "Risk/Reward",
        f"{pnl_analysis['risk_reward_ratio']:.2f}:1"
    )

    if pnl_analysis['breakevens']:
        col4.metric(
            "Breakeven",
            f"${pnl_analysis['breakevens'][0]:.2f}"
        )
    else:
        col4.metric("Breakeven", "N/A")

    # P/L Chart
    st.markdown("#### 📈 Profit/Loss Diagram")

    try:
        # Calculate target price for chart
        import re
        move_match = re.search(r'([+-]?\d+(?:\.\d+)?)', thesis.expected_move)
        expected_move_pct = float(move_match.group(1)) / 100 if move_match else 0.15
        target_price = stock_data['current_price'] * (1 + expected_move_pct)

        fig = create_pnl_chart(
            pnl_curve=pnl_analysis['pnl_curve'],
            current_price=stock_data['current_price'],
            max_profit=pnl_analysis['max_profit'],
            max_loss=pnl_analysis['max_loss'],
            max_profit_price=pnl_analysis['max_profit_price'],
            max_loss_price=pnl_analysis['max_loss_price'],
            breakevens=pnl_analysis['breakevens'],
            strategy_name=strategy.strategy.value,
            target_price=target_price
        )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create P/L chart: {e}")

    # Metrics Table
    st.markdown("#### 📊 Detailed Metrics")

    try:
        metrics_html = create_metrics_table(
            max_profit=pnl_analysis['max_profit'],
            max_loss=pnl_analysis['max_loss'],
            breakevens=pnl_analysis['breakevens'],
            current_price=stock_data['current_price'],
            net_debit_credit=pnl_analysis['net_debit_credit'],
            risk_reward_ratio=pnl_analysis['risk_reward_ratio'],
            current_pnl=pnl_analysis.get('current_pnl', 0),
            greeks=pnl_analysis.get('greeks')
        )

        st.markdown(metrics_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Failed to create metrics table: {e}")

    # Greeks breakdown
    if pnl_analysis.get('greeks'):
        st.markdown("#### 🔢 Portfolio Greeks")

        greeks = pnl_analysis['greeks']
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Delta", f"{greeks.get('portfolio_delta', 0):.3f}")
        col2.metric("Gamma", f"{greeks.get('portfolio_gamma', 0):.3f}")
        col3.metric("Theta", f"{greeks.get('portfolio_theta', 0):.3f}")
        col4.metric("Vega", f"{greeks.get('portfolio_vega', 0):.3f}")

    # ===== RESEARCH SUMMARY =====
    if research and research.total_questions > 0:
        st.markdown("---")
        st.markdown("### 🔬 Complete Research Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Questions", research.total_questions)
        col2.metric("Total Articles", research.total_articles)
        col3.metric("Total Words", f"{research.total_words:,}")
        col4.metric("Unique Sources", len(set(research.total_sources)))

        with st.expander("📚 All Research Questions"):
            if research.stock_research:
                st.markdown("**Stock Fundamentals:**")
                for q in research.stock_research.questions:
                    st.caption(f"• {q.question}")

            if research.strategy_research:
                st.markdown("**Strategy Selection:**")
                for q in research.strategy_research.questions:
                    st.caption(f"• {q.question}")

            if research.contract_research:
                st.markdown("**Contract Selection:**")
                for q in research.contract_research.questions:
                    st.caption(f"• {q.question}")

            if research.risk_research:
                st.markdown("**Risk Management:**")
                for q in research.risk_research.questions:
                    st.caption(f"• {q.question}")

            if research.market_research:
                st.markdown("**Market Conditions:**")
                for q in research.market_research.questions:
                    st.caption(f"• {q.question}")

        with st.expander("🌐 All Sources"):
            sources = set(research.total_sources)
            for i, source in enumerate(sorted(sources), 1):
                st.caption(f"{i}. {source}")

else:
    # Welcome screen
    st.info("👈 Enter a ticker in the sidebar and click 'Analyze Stock' to begin")

    st.markdown("""
    ## 🧠 How This Research-Enhanced Bot Works

    ### **Traditional Approach (V1):**
    - Hardcoded rules: "IF conviction >= 70% THEN Long Call"
    - Fixed parameters: Always use 0.70 delta
    - Static knowledge: Can't learn new strategies
    - Black box: No explanation of decisions

    ### **Research-Enhanced Approach (V2/V3):**

    #### **1. Thesis Generation 📊**
    - Fetches stock data (price, fundamentals, news)
    - **Researches web articles:** "What were NVDA's earnings?", "Market position?", "Growth drivers?"
    - **Generates AI thesis** with direction, conviction, expected move
    - **Research output:** ~30,000+ words of context (vs 21,000 without research)

    #### **2. Strategy Selection 🎯**
    - **Researches optimal strategy:** "Bull call spread vs long call - when to choose?"
    - Learns from articles about what works in current market conditions
    - **Data-driven decision** instead of hardcoded rule
    - Example: Research finds "spreads work better in high IV" → recommends spread

    #### **3. Contract Selection 📋**
    - **Researches optimal parameters:** "What delta for bullish trades?", "Best expiration?"
    - Adapts based on findings instead of using fixed parameters
    - Example: Research finds "65-70 delta optimal for volatile stocks" → uses 0.65

    #### **4. Risk Analysis 💰**
    - Calculates P/L at expiration for all price scenarios
    - Shows max profit, max loss, breakevens
    - Interactive chart with profit/loss zones
    - Portfolio Greeks (Delta, Theta, Vega, Gamma)

    ---

    ### **What Makes This Powerful:**

    ✅ **Truly Autonomous** - Bot teaches itself by reading articles
    ✅ **Data-Driven** - Decisions based on research, not rules
    ✅ **Transparent** - Can cite sources for every decision
    ✅ **Adaptive** - Learns what works for each stock specifically
    ✅ **Complete** - Research at EVERY decision point

    ---

    ### **Research Example (NVDA):**

    **15 Questions Generated:**
    - Stock: "NVDA earnings?", "Market position?", "Growth drivers?"
    - Strategy: "Bull call spread vs long call?", "When to use spreads?"
    - Contracts: "Optimal delta?", "Best expiration timing?"
    - Risk: "Historical volatility?", "Post-earnings moves?"
    - Market: "IV environment?", "Sector trends?"

    **11 Articles Scraped:**
    - Fidelity, TastyLive, MarketChameleon, TradingView, etc.

    **10,184 Words Analyzed:**
    - Bot reads and learns from all articles
    - Extracts insights for decision-making

    **Result:**
    - Recommends Bull Call Spread (research-informed)
    - Selects optimal strikes based on research
    - Explains reasoning with citations

    ---

    **This is true AI-powered options trading with autonomous research! 🚀**
    """)

# Footer
st.markdown("---")
st.caption("🧠 Research-Enhanced Options Bot | Built with Claude Code + DRIVER | V3 Research Pipeline")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
