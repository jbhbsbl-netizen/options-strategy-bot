"""
Automated Bot Evaluator

Runs the research-enhanced options bot and sends the output to ChatGPT for evaluation.
Generates a comprehensive report comparing the bot's analysis with GPT's critique.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import os
from datetime import datetime
from dotenv import load_dotenv
import openai

from data.yfinance_client import YFinanceClient
from ai.thesis_generator_v3 import ThesisGeneratorV3
from strategies.strategy_selector_v2 import StrategySelectV2
from strategies.contract_picker_v2 import ContractPickerV2
from analysis.pnl_calculator import PnLCalculator

# Load environment variables
load_dotenv()

class BotEvaluator:
    """Evaluates bot output using ChatGPT."""

    def __init__(self, api_key: str = None):
        """Initialize evaluator with OpenAI API key."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY in .env file")

        openai.api_key = self.api_key

        # Initialize bot components
        self.yfinance_client = YFinanceClient()
        self.thesis_generator = ThesisGeneratorV3(enable_research=True)
        self.strategy_selector = StrategySelectV2(enable_research=True)
        self.contract_picker = ContractPickerV2(enable_research=True)
        self.pnl_calculator = PnLCalculator()

    def run_bot_analysis(self, ticker: str, articles_per_question: int = 1):
        """
        Run complete bot analysis on a ticker.

        Args:
            ticker: Stock symbol
            articles_per_question: Research depth (1-3)

        Returns:
            Dictionary with complete analysis results
        """
        print(f"\n{'='*80}")
        print(f"RUNNING BOT ANALYSIS: {ticker}")
        print(f"{'='*80}\n")

        # Phase 1: Fetch data
        print("📊 Phase 1: Fetching stock data...")
        stock_data = self.yfinance_client.get_stock_data(ticker)
        news = self.yfinance_client.get_news(ticker, max_items=5)

        try:
            historical_vol = self.yfinance_client.get_historical_volatility(ticker, days=30)
        except:
            historical_vol = 0.40

        current_price = stock_data['current_price']
        print(f"   ✅ Current price: ${current_price:.2f}")

        # Phase 2: Generate thesis
        print("\n🧠 Phase 2: Generating thesis with research...")
        thesis = self.thesis_generator.generate_thesis(
            ticker=ticker,
            stock_data=stock_data,
            news=news,
            historical_vol=historical_vol,
            enable_research=True,
            articles_per_question=articles_per_question
        )
        print(f"   ✅ Thesis: {thesis.direction} ({thesis.conviction}% conviction)")

        # Extract research metadata
        research_meta = {
            "articles": thesis.data_references.get("research_articles", 0),
            "words": thesis.data_references.get("research_words", 0),
            "sources": thesis.data_references.get("research_sources", [])
        }

        # Phase 3: Select strategy
        print("\n🎯 Phase 3: Selecting strategy with research...")

        import re
        move_match = re.search(r'([+-]?\d+(?:\.\d+)?)', thesis.expected_move)
        expected_move_pct = float(move_match.group(1)) / 100 if move_match else 0.15

        timeframe_match = re.search(r'(\d+)', thesis.timeframe)
        timeframe_days = int(timeframe_match.group(1)) if timeframe_match else 30

        try:
            options_data = self.yfinance_client.get_options_chain(ticker)
            implied_vol = options_data.get('implied_volatility', historical_vol)
        except:
            implied_vol = historical_vol

        strategy, research = self.strategy_selector.select_strategy_with_research(
            ticker=ticker,
            direction=thesis.direction,
            conviction=thesis.conviction,
            expected_move_pct=expected_move_pct,
            timeframe_days=timeframe_days,
            current_price=current_price,
            historical_vol=historical_vol,
            implied_vol=implied_vol,
            articles_per_question=articles_per_question
        )
        print(f"   ✅ Strategy: {strategy.strategy.value}")

        # Phase 4: Pick contracts
        print("\n📋 Phase 4: Selecting contracts with research...")

        try:
            options_chain = self.yfinance_client.get_options_chain_all_expirations(ticker)
        except:
            import pandas as pd
            options_chain = pd.DataFrame()

        contracts, contract_insights = self.contract_picker.pick_contracts_with_research(
            ticker=ticker,
            strategy=strategy.strategy.value,
            direction=thesis.direction,
            expected_move_pct=expected_move_pct,
            timeframe_days=timeframe_days,
            current_price=current_price,
            options_chain=options_chain,
            research=research
        )
        print(f"   ✅ Contracts: {len(contracts)} selected")

        # Phase 5: Calculate P/L
        print("\n💰 Phase 5: Calculating risk/reward...")
        pnl_analysis = self.pnl_calculator.calculate_complete_analysis(
            contracts=contracts,
            current_price=current_price,
            volatility=implied_vol,
            days_to_expiration=timeframe_days
        )
        print(f"   ✅ Max profit: ${pnl_analysis['max_profit']:,.2f}")
        print(f"   ✅ Max loss: ${abs(pnl_analysis['max_loss']):,.2f}")
        print(f"   ✅ R/R ratio: {pnl_analysis['risk_reward_ratio']:.2f}:1")

        # Compile results
        results = {
            "ticker": ticker,
            "timestamp": datetime.now(),
            "stock_data": stock_data,
            "thesis": thesis,
            "strategy": strategy,
            "contracts": contracts,
            "pnl_analysis": pnl_analysis,
            "research_meta": research_meta,
            "research": research
        }

        print(f"\n{'='*80}")
        print("✅ BOT ANALYSIS COMPLETE")
        print(f"{'='*80}\n")

        return results

    def format_for_evaluation(self, results):
        """Format bot results for ChatGPT evaluation."""

        thesis = results["thesis"]
        strategy = results["strategy"]
        contracts = results["contracts"]
        pnl = results["pnl_analysis"]
        research_meta = results["research_meta"]
        research = results["research"]
        stock = results["stock_data"]

        # Build formatted output
        output = f"""
# AI Options Strategy Bot Analysis: {results['ticker']}

**Analysis Date:** {results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
**Current Price:** ${stock['current_price']:.2f}

---

## 1. RESEARCH CONDUCTED

**Research Depth:**
- Total Questions Generated: {research.total_questions if research else 'N/A'}
- Total Articles Scraped: {research_meta['articles']}
- Total Words Analyzed: {research_meta['words']:,}
- Unique Sources: {len(research_meta['sources'])}

**Sources Used:**
"""
        for i, source in enumerate(research_meta['sources'][:10], 1):
            output += f"{i}. {source}\n"

        if research:
            output += f"\n**Research Questions by Phase:**\n\n"

            if research.stock_research:
                output += "**Stock Fundamentals:**\n"
                for q in research.stock_research.questions[:3]:
                    output += f"- {q.question}\n"

            if research.strategy_research:
                output += "\n**Strategy Selection:**\n"
                for q in research.strategy_research.questions[:3]:
                    output += f"- {q.question}\n"

            if research.contract_research:
                output += "\n**Contract Selection:**\n"
                for q in research.contract_research.questions[:3]:
                    output += f"- {q.question}\n"

        output += f"""

---

## 2. INVESTMENT THESIS

**Direction:** {thesis.direction}
**Conviction:** {thesis.conviction}%
**Expected Move:** {thesis.expected_move}
**Timeframe:** {thesis.timeframe}
**Target Price:** ${thesis.target_price:.2f} (current: ${stock['current_price']:.2f})

**Thesis Summary:**
{thesis.thesis_summary}

**Bull Case:**
{thesis.bull_case}

**Bear Case:**
{thesis.bear_case}

**Catalysts:**
"""
        for catalyst in thesis.catalysts:
            output += f"- {catalyst}\n"

        output += "\n**Key Risks:**\n"
        for risk in thesis.key_risks:
            output += f"- {risk}\n"

        output += f"""

---

## 3. STRATEGY RECOMMENDATION

**Strategy:** {strategy.strategy.value}

**Rationale:**
{strategy.rationale}

**Strategy Characteristics:**
- Risk Level: {strategy.risk_level}
- Capital Required: {strategy.capital_required}
- Max Profit: {strategy.max_profit}
- Max Loss: {strategy.max_loss}
- Breakeven: {strategy.breakeven}

**Ideal Conditions:**
"""
        for cond in strategy.ideal_conditions:
            output += f"- {cond}\n"

        output += f"""

---

## 4. SELECTED CONTRACTS

"""
        for i, contract in enumerate(contracts, 1):
            output += f"""**Contract {i}:**
- Action: {contract.action}
- Contract: {contract.display_name}
- Strike: ${contract.strike:.2f}
- Premium: ${contract.premium:.2f}
- Delta: {contract.delta:.2f}
- Expiration: {contract.expiration}
- Cost/Credit: ${contract.cost_or_credit:.2f}

"""

        output += f"""
---

## 5. RISK/REWARD ANALYSIS

**Profit/Loss Metrics:**
- Max Profit: ${pnl['max_profit']:,.2f}
- Max Loss: ${abs(pnl['max_loss']):,.2f}
- Risk/Reward Ratio: {pnl['risk_reward_ratio']:.2f}:1
- Net Debit/Credit: ${pnl['net_debit_credit']:,.2f}
"""

        if pnl['breakevens']:
            output += f"- Breakeven Price: ${pnl['breakevens'][0]:.2f}\n"

        if pnl.get('greeks'):
            greeks = pnl['greeks']
            output += f"""
**Portfolio Greeks:**
- Delta: {greeks.get('portfolio_delta', 0):.3f}
- Gamma: {greeks.get('portfolio_gamma', 0):.3f}
- Theta: {greeks.get('portfolio_theta', 0):.3f}
- Vega: {greeks.get('portfolio_vega', 0):.3f}
"""

        output += "\n---\n"

        return output

    def get_gpt_evaluation(self, formatted_output: str):
        """Send to ChatGPT for evaluation."""

        print("\n🤖 Sending to ChatGPT for evaluation...")

        evaluation_prompt = f"""
You are an expert options trader and financial analyst with 20+ years of experience.

I've built an AI-powered options strategy bot that:
1. Researches stocks by autonomously searching and reading financial articles
2. Generates investment theses with conviction levels
3. Recommends specific options strategies
4. Selects exact contracts (strikes, expirations)
5. Provides complete risk/reward analysis

Below is the bot's complete analysis of a stock. Please evaluate it comprehensively.

{formatted_output}

---

# YOUR EVALUATION TASK

Please provide a detailed, critical evaluation covering:

## 1. RESEARCH QUALITY (Score: /10)
- Are the research questions intelligent and relevant?
- Are the sources credible and diverse?
- Is the research depth sufficient for the decision?
- What research is missing?

## 2. THESIS QUALITY (Score: /10)
- Is the directional view (BULLISH/BEARISH/NEUTRAL) well-supported?
- Is the conviction level (%) justified by the evidence?
- Are the bull/bear cases balanced and thorough?
- Are the catalysts and risks realistic?
- Is the target price reasonable?

## 3. STRATEGY SELECTION (Score: /10)
- Is the recommended strategy appropriate for the thesis?
- Does the rationale make sense?
- Would you choose this strategy in this situation?
- Are there better alternatives?

## 4. CONTRACT SELECTION (Score: /10)
- Are the strike prices appropriate?
- Is the expiration timing optimal?
- Are the deltas suitable for the thesis?
- Would you pick different strikes/expirations?

## 5. RISK/REWARD PROFILE (Score: /10)
- Is the risk/reward ratio attractive?
- Is the max loss acceptable?
- Is the max profit realistic?
- Are the Greeks favorable?

## 6. OVERALL ASSESSMENT

**Strengths:** (3-5 bullet points)

**Weaknesses:** (3-5 bullet points)

**Missing Elements:** (What should the bot add?)

**Overall Quality Score:** X/10

**Would you trade this?** (Yes/No and why)

**Bottom Line:** (2-3 sentences summarizing your opinion)

---

Be honest, critical, and specific. Point out both strengths and real weaknesses. Compare to what a professional options trader would produce.
"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4",  # Use GPT-4 for best evaluation
                messages=[
                    {"role": "system", "content": "You are an expert options trader with 20+ years of experience. Provide honest, critical, and detailed evaluations."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            evaluation = response.choices[0].message.content
            print("   ✅ Evaluation received from ChatGPT")

            return evaluation

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return f"Error getting evaluation: {e}"

    def save_report(self, ticker: str, formatted_output: str, evaluation: str):
        """Save evaluation report to markdown file."""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"evaluation_{ticker}_{timestamp}.md"

        report = f"""# Bot Evaluation Report: {ticker}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

# PART 1: BOT'S ANALYSIS

{formatted_output}

---

# PART 2: CHATGPT'S EVALUATION

{evaluation}

---

# END OF REPORT

**Note:** This evaluation was generated by GPT-4 analyzing the bot's output.
The bot uses autonomous web research to make data-driven decisions.
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ Report saved: {filename}")
        return filename

    def evaluate(self, ticker: str, articles_per_question: int = 1):
        """
        Run complete evaluation pipeline.

        Args:
            ticker: Stock symbol to analyze
            articles_per_question: Research depth (1-3)

        Returns:
            Path to evaluation report
        """
        print("\n" + "="*80)
        print("BOT EVALUATOR - Automated Analysis & ChatGPT Critique")
        print("="*80)

        # Step 1: Run bot analysis
        results = self.run_bot_analysis(ticker, articles_per_question)

        # Step 2: Format for evaluation
        print("\n📝 Formatting analysis for evaluation...")
        formatted_output = self.format_for_evaluation(results)
        print("   ✅ Formatted")

        # Step 3: Get ChatGPT evaluation
        evaluation = self.get_gpt_evaluation(formatted_output)

        # Step 4: Save report
        report_path = self.save_report(ticker, formatted_output, evaluation)

        print("\n" + "="*80)
        print("✅ EVALUATION COMPLETE")
        print("="*80)
        print(f"\nReport saved to: {report_path}")
        print("\nYou can now:")
        print("1. Read the report to see ChatGPT's opinion")
        print("2. Compare bot's analysis with GPT's critique")
        print("3. Identify areas for improvement")

        return report_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate options bot with ChatGPT")
    parser.add_argument("ticker", type=str, help="Stock ticker to analyze")
    parser.add_argument("--depth", type=int, default=1, choices=[1, 2, 3],
                       help="Research depth: 1=fast, 2=moderate, 3=deep (default: 1)")

    args = parser.parse_args()

    try:
        evaluator = BotEvaluator()
        report_path = evaluator.evaluate(args.ticker.upper(), args.depth)

        print(f"\n🎉 Done! Open the report to see ChatGPT's evaluation:")
        print(f"   {report_path}")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have OPENAI_API_KEY in your .env file:")
        print("   OPENAI_API_KEY=sk-...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
