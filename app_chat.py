"""
Options Strategy Bot - Conversational Interface
Full LLM-powered chat experience for class project
"""
import streamlit as st
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
import os

# Import existing bot components
from data.yfinance_client import YFinanceClient
from research.research_orchestrator import ResearchOrchestrator
from ai.thesis_generator_v3 import ThesisGeneratorV3
from strategies.strategy_selector_v2 import StrategySelectV2
from strategies.strategy_selector import StrategySelector
from strategies.contract_picker_v2 import ContractPickerV2
from strategies.contract_picker import ContractPicker
from analysis.pnl_calculator import PnLCalculator
from visualization.pnl_chart import create_pnl_chart

load_dotenv()

# Page config
st.set_page_config(
    page_title="Options Bot - Chat Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize LLM clients
@st.cache_resource
def get_llm_client(provider: str):
    """Get LLM client (OpenAI or Anthropic)."""
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("⚠️ OPENAI_API_KEY not found in .env file")
            return None
        return OpenAI(api_key=api_key)
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            st.error("⚠️ ANTHROPIC_API_KEY not found in .env file")
            return None
        return Anthropic(api_key=api_key)
    return None


# Initialize session state
def initialize_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "conversation_stage" not in st.session_state:
        st.session_state.conversation_stage = "greeting"

    if "ticker" not in st.session_state:
        st.session_state.ticker = None

    if "research_depth" not in st.session_state:
        st.session_state.research_depth = None

    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None

    if "llm_provider" not in st.session_state:
        st.session_state.llm_provider = "openai"  # Default to OpenAI


def send_llm_message(messages: list, provider: str = "openai", stream: bool = True):
    """
    Send messages to LLM and get response.

    Args:
        messages: List of message dicts with role and content
        provider: "openai" or "anthropic"
        stream: Whether to stream the response

    Returns:
        Response text or stream generator
    """
    client = get_llm_client(provider)

    if client is None:
        return "Error: LLM client not available. Please check your API keys."

    try:
        if provider == "openai":
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cheap for conversation
                messages=messages,
                stream=stream,
                temperature=0.7
            )

            if stream:
                # Return generator for streaming
                def generate():
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                return generate()
            else:
                return response.choices[0].message.content

        elif provider == "anthropic":
            # Convert messages to Anthropic format
            system_msg = None
            claude_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    claude_messages.append(msg)

            if stream:
                with client.messages.stream(
                    model="claude-3-5-haiku-20241022",  # Fast and cheap
                    max_tokens=1024,
                    messages=claude_messages,
                    system=system_msg if system_msg else None,
                ) as stream:
                    response_text = ""
                    for text in stream.text_stream:
                        response_text += text
                        yield text
                    return response_text
            else:
                response = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=1024,
                    messages=claude_messages,
                    system=system_msg if system_msg else None,
                )
                return response.content[0].text

    except Exception as e:
        return f"Error communicating with LLM: {str(e)}"


def get_system_prompt() -> str:
    """Get system prompt for the LLM."""
    return """You are a helpful AI assistant for an options trading strategy bot. Your role is to:

1. Help users analyze stocks for options trading
2. Guide them through the analysis process
3. Explain the bot's research and recommendations
4. Answer questions about the analysis results

Be conversational, friendly, and clear. Use emojis sparingly for emphasis.

Current conversation stages:
- greeting: Welcome user, ask for ticker
- configure: Ask about research depth
- analyzing: Bot is running analysis (provide progress updates)
- results: Show results, answer questions
- followup: Answer questions about specific aspects

Keep responses concise (2-4 sentences) unless explaining complex topics."""


def extract_ticker_from_message(message: str) -> Optional[str]:
    """
    Extract stock ticker from user message.
    Returns uppercase ticker or None.
    """
    # Simple extraction - look for 2-5 uppercase letters (avoid single letters like "I")
    import re

    # Try to find ticker pattern
    patterns = [
        r'\$([A-Z]{2,5})\b',  # With $ prefix (highest priority)
        r'\b([A-Z]{2,5})\b',  # Standalone uppercase 2-5 chars
    ]

    for pattern in patterns:
        matches = re.findall(pattern, message.upper())
        if matches:
            # Filter out common English words
            excluded = ['THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'MAN', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY', 'WHO', 'BOY', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE']
            for match in matches:
                if match not in excluded:
                    return match

    return None


def extract_research_depth(message: str) -> Optional[str]:
    """Extract research depth preference from message."""
    message_lower = message.lower()

    if "quick" in message_lower or "fast" in message_lower or "90" in message_lower:
        return "quick"
    elif "deep" in message_lower or "thorough" in message_lower or "detailed" in message_lower:
        return "deep"
    elif "moderate" in message_lower or "medium" in message_lower or "2" in message_lower:
        return "moderate"

    return None


def run_analysis(ticker: str, research_depth: str) -> Dict[str, Any]:
    """
    Run the complete analysis pipeline.
    Returns dict with all results.
    """
    results = {}

    try:
        # Map research depth to articles per question
        articles_map = {
            "quick": 1,
            "moderate": 2,
            "deep": 3
        }
        articles_per_question = articles_map.get(research_depth, 2)

        # 1. Get stock data
        with st.status("[1/6] Gathering stock data...") as status:
            client = YFinanceClient()
            stock_data = client.get_stock_data(ticker)
            news = client.get_news(ticker)
            historical_vol = client.get_historical_volatility(ticker)
            results["stock_data"] = stock_data
            results["news"] = news
            results["historical_vol"] = historical_vol
            status.update(label="[DONE] Stock data gathered", state="complete")

        # 2 & 3. Generate thesis with research
        with st.status(f"[2/6] Generating investment thesis (with research, 2-5 min)...") as status:
            thesis_gen = ThesisGeneratorV3()
            thesis = thesis_gen.generate_thesis(
                ticker=ticker,
                stock_data=stock_data,
                news=news,
                historical_vol=historical_vol,
                enable_research=True,
                articles_per_question=articles_per_question
            )
            results["thesis"] = thesis
            status.update(label="[DONE] Thesis generated", state="complete")

        # 4. Select strategy (fast - using rules, no additional research)
        with st.status("[3/5] Selecting optimal strategy...") as status:
            strategy_selector = StrategySelector()
            # Use non-research method - thesis already did comprehensive research
            strategy_rec = strategy_selector.select_strategy(
                direction=thesis.direction,
                conviction=thesis.conviction,
                expected_move_pct=thesis.expected_move_pct,
                timeframe_days=thesis.timeframe_days,
                current_price=stock_data["current_price"],
                historical_vol=historical_vol,
                implied_vol=stock_data.get("implied_volatility")
            )
            results["strategy"] = strategy_rec
            status.update(label="[DONE] Strategy selected", state="complete")

        # 5. Pick contracts (fast - using rules, no additional research)
        with st.status("[4/5] Finding optimal contracts...") as status:
            # Get options chain
            options_chain = client.get_options_chain_all_expirations(ticker, max_expirations=5)

            picker = ContractPicker()
            # Use non-research method - thesis already did comprehensive research
            contracts = picker.pick_contracts(
                strategy_name=strategy_rec.strategy.value,
                direction=thesis.direction,
                target_price=thesis.target_price,
                timeframe_days=thesis.timeframe_days,
                current_price=stock_data["current_price"],
                options_chain=options_chain
            )
            results["contracts"] = contracts
            status.update(label="[DONE] Contracts selected", state="complete")

        # 6. Calculate P/L
        with st.status("[5/5] Calculating risk/reward...") as status:
            calculator = PnLCalculator()
            pnl = calculator.calculate_complete_analysis(
                contracts=contracts,
                current_price=stock_data["current_price"],
                volatility=historical_vol,
                days_to_expiration=thesis.timeframe_days
            )
            results["pnl"] = pnl
            status.update(label="[DONE] Analysis complete!", state="complete")

        return results

    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        return None


def display_results_summary(results: Dict[str, Any]) -> str:
    """
    Display analysis results and return summary text for LLM.
    """
    thesis = results["thesis"]
    strategy = results["strategy"]
    contracts = results["contracts"]
    pnl = results["pnl"]
    research = results["research"]

    # Display in columns
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Investment Thesis")
        direction_emoji = {
            "BULLISH": "🟢",
            "BEARISH": "🔴",
            "NEUTRAL": "⚪",
            "UNPREDICTABLE": "🟡"
        }
        st.markdown(f"### {direction_emoji.get(thesis.direction, '')} {thesis.direction}")
        st.metric("Conviction", f"{thesis.conviction}%")
        st.metric("Expected Move", thesis.expected_move)
        st.metric("Target Price", f"${thesis.target_price:.2f}")

        with st.expander("📝 Thesis Summary"):
            st.write(thesis.thesis_summary)

        if thesis.research_insights:
            with st.expander("🔬 Research Insights"):
                st.write(thesis.research_insights)

    with col2:
        st.subheader("📈 Recommended Strategy")
        st.markdown(f"**Strategy:** {strategy.strategy.value}")
        st.markdown(f"**Rationale:** {strategy.rationale}")

        # Strategy explanation from rationale
        with st.expander("💡 Strategy Details"):
            st.write(f"**Risk Level:** {strategy.risk_level}")
            st.write(f"**Capital Required:** {strategy.capital_required}")
            st.write(f"**Ideal Conditions:**")
            for condition in strategy.ideal_conditions:
                st.write(f"  - {condition}")

    # Contracts
    st.subheader("🎯 Selected Contracts")
    for i, contract in enumerate(contracts, 1):
        st.markdown(f"**Leg {i}:** {contract.action} {contract.ticker} {contract.strike}C @ ${contract.premium:.2f}")

    # P/L Chart
    st.subheader("💰 Risk/Reward Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("Max Profit", f"${pnl['max_profit']:,.0f}")
    col2.metric("Max Loss", f"${pnl['max_loss']:,.0f}")
    col3.metric("Risk/Reward", f"{pnl['risk_reward_ratio']:.2f}:1")

    # Create P/L chart
    fig = create_pnl_chart(
        pnl_curve=pnl['pnl_curve'],
        current_price=results["stock_data"]["current_price"],
        max_profit=pnl['max_profit'],
        max_loss=pnl['max_loss'],
        max_profit_price=pnl['max_profit_price'],
        max_loss_price=pnl['max_loss_price'],
        breakevens=pnl['breakevens'],
        strategy_name=strategy.strategy.value
    )
    st.plotly_chart(fig, use_container_width=True)

    # Research summary
    st.subheader("📚 Research Summary")
    st.markdown(f"**Articles Read:** {research.stock_research.article_count + research.strategy_research.article_count}")
    st.markdown(f"**Words Analyzed:** {research.stock_research.total_words + research.strategy_research.total_words:,}")

    # Generate summary for LLM
    summary = f"""Analysis complete for {contracts[0].ticker}!

📊 **Thesis:** {thesis.direction} with {thesis.conviction}% conviction
🎯 **Expected Move:** {thesis.expected_move}
📈 **Strategy:** {strategy.strategy.value}
💰 **Risk/Reward:** Max profit ${pnl['max_profit']:,.0f} / Max loss ${pnl['max_loss']:,.0f}
🔬 **Research:** Analyzed {research.stock_research.article_count + research.strategy_research.article_count} articles

You can now ask me questions about:
- Why I chose this thesis
- How the strategy works
- What the research revealed
- Risk management
- Alternative strategies"""

    return summary


# Main app
def main():
    st.title("🤖 Options Strategy Bot - Chat Interface")
    st.caption("💬 AI-Powered Conversational Analysis")

    # Initialize
    initialize_session_state()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # LLM Provider
        provider = st.radio(
            "LLM Provider",
            ["openai", "anthropic"],
            index=0 if st.session_state.llm_provider == "openai" else 1,
            help="Choose which LLM to use for conversation"
        )
        st.session_state.llm_provider = provider

        # Show API key status
        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        if api_key:
            st.success(f"[DONE] {provider.title()} API key found")
        else:
            st.error(f"❌ {provider.upper()}_API_KEY not found in .env")

        st.divider()

        # Debug info
        with st.expander("🐛 Debug Info"):
            st.write("**Stage:**", st.session_state.conversation_stage)
            st.write("**Ticker:**", st.session_state.ticker)
            st.write("**Depth:**", st.session_state.research_depth)

        # Reset button
        if st.button("🔄 New Analysis"):
            st.session_state.messages = []
            st.session_state.conversation_stage = "greeting"
            st.session_state.ticker = None
            st.session_state.research_depth = None
            st.session_state.analysis_results = None
            st.rerun()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Initial greeting
    if len(st.session_state.messages) == 0:
        greeting = "Hi! 👋 I'm your AI options strategy assistant. I can help you analyze stocks and recommend options strategies.\n\n**What stock would you like to analyze?** (Just type the ticker, like NVDA or AAPL)"

        st.session_state.messages.append({
            "role": "assistant",
            "content": greeting
        })

        with st.chat_message("assistant"):
            st.markdown(greeting)

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Process based on stage
        with st.chat_message("assistant"):
            if st.session_state.conversation_stage == "greeting":
                # Extract ticker
                ticker = extract_ticker_from_message(prompt)

                if ticker:
                    st.session_state.ticker = ticker
                    st.session_state.conversation_stage = "configure"

                    response = f"Great! I'll analyze **{ticker}** for you. 📊\n\nHow deep should I research? Choose one:\n- **Quick** (~90 seconds, 1 article per question)\n- **Moderate** (~2-3 minutes, 2 articles per question)\n- **Deep** (~4-5 minutes, 3 articles per question)\n\nJust type 'quick', 'moderate', or 'deep'."
                else:
                    response = "I didn't catch that ticker. Could you please provide a stock symbol? (e.g., NVDA, AAPL, TSLA)"

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            elif st.session_state.conversation_stage == "configure":
                # Extract research depth
                depth = extract_research_depth(prompt)

                if depth:
                    st.session_state.research_depth = depth
                    st.session_state.conversation_stage = "analyzing"

                    response = f"Perfect! Starting **{depth}** analysis for **{st.session_state.ticker}**...\n\nThis will take a few minutes. Watch the progress below! ⏳"
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # Run analysis
                    results = run_analysis(st.session_state.ticker, depth)

                    if results:
                        st.session_state.analysis_results = results
                        st.session_state.conversation_stage = "results"

                        # Display results
                        summary = display_results_summary(results)
                        st.session_state.messages.append({"role": "assistant", "content": summary})
                    else:
                        error_msg = "Sorry, something went wrong during analysis. Please try again."
                        st.markdown(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        st.session_state.conversation_stage = "greeting"
                else:
                    response = "Please choose: **quick**, **moderate**, or **deep**"
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

            elif st.session_state.conversation_stage == "results":
                # Q&A mode - use LLM with context
                results = st.session_state.analysis_results

                # Build context for LLM
                context_messages = [
                    {"role": "system", "content": get_system_prompt()},
                    {"role": "system", "content": f"""
Current analysis results for {st.session_state.ticker}:

**Thesis:**
- Direction: {results['thesis'].direction}
- Conviction: {results['thesis'].conviction}%
- Summary: {results['thesis'].thesis_summary}
- Research Insights: {results['thesis'].research_insights}

**Strategy:**
- Name: {results['strategy'].strategy_name}
- Rationale: {results['strategy'].strategy_rationale}
- Explanation: {results['strategy'].strategy_explanation}

**Risk/Reward:**
- Max Profit: ${results['pnl'].max_profit:,.0f}
- Max Loss: ${results['pnl'].max_loss:,.0f}

Use this context to answer the user's question."""}
                ]

                # Add recent conversation history
                recent_messages = st.session_state.messages[-6:]  # Last 6 messages
                context_messages.extend(recent_messages)

                # Get LLM response
                response_stream = send_llm_message(
                    context_messages,
                    provider=st.session_state.llm_provider,
                    stream=True
                )

                response = st.write_stream(response_stream)
                st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
