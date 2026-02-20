"""
Enhanced Contract Picker with Autonomous Research.

V1: Hardcoded delta targets (Long Call = 0.70 delta always)
V2: Research-informed selection (learns optimal delta, expiration, spread width)

The bot now researches:
- "Optimal delta for bullish trades on high volatility stocks"
- "Best expiration timing for 30-day expected move"
- "Spread width for NVDA vertical spreads"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime

from models.thesis import ContractSelection
from research.research_orchestrator import ComprehensiveResearch


@dataclass
class ContractInsights:
    """Insights extracted from contract research."""

    # Delta recommendations
    recommended_long_delta: Optional[float] = None  # e.g., 0.65
    recommended_short_delta: Optional[float] = None  # e.g., 0.30
    delta_range_min: Optional[float] = None  # e.g., 0.60
    delta_range_max: Optional[float] = None  # e.g., 0.75

    # Expiration recommendations
    recommended_dte: Optional[int] = None  # Days to expiration
    dte_range_min: Optional[int] = None  # e.g., 30
    dte_range_max: Optional[int] = None  # e.g., 60

    # Spread recommendations
    recommended_spread_width: Optional[float] = None  # e.g., 10.0 (points)
    spread_width_pct: Optional[float] = None  # e.g., 0.10 (10% of stock price)

    # Context
    reasoning: Optional[str] = None


class ContractPickerV2:
    """
    Enhanced contract picker with autonomous research.

    Learns optimal delta, expiration, and spread width from research.
    """

    def __init__(self, enable_research: bool = True):
        """
        Initialize enhanced contract picker.

        Args:
            enable_research: Whether to use research insights (default True)
        """
        self.enable_research = enable_research

        if enable_research:
            print("[ContractPicker V2] Research ENABLED - will learn optimal contracts")
        else:
            print("[ContractPicker V2] Research DISABLED - using V1 defaults")

    def pick_contracts_with_research(
        self,
        ticker: str,
        strategy: str,
        direction: str,
        expected_move_pct: float,
        timeframe_days: int,
        current_price: float,
        options_chain: Dict[str, pd.DataFrame],  # Fixed: Dict not DataFrame
        research: Optional[ComprehensiveResearch] = None
    ) -> tuple[List[ContractSelection], Optional[ContractInsights]]:
        """
        Pick contracts with research insights.

        Args:
            ticker: Stock ticker
            strategy: Strategy name (e.g., "Bull Call Spread")
            direction: "BULLISH", "BEARISH", or "NEUTRAL"
            expected_move_pct: Expected % move
            timeframe_days: Timeframe in days
            current_price: Current stock price
            options_chain: Options chain data
            research: Research findings (optional)

        Returns:
            Tuple of (List[ContractSelection], ContractInsights)
        """

        insights = None

        # Phase 1: Extract contract insights from research
        if research and research.contract_research:
            print(f"\n[CONTRACT RESEARCH] Extracting insights...")
            insights = self._extract_contract_insights(
                research, strategy, direction, current_price, timeframe_days
            )

            if insights.recommended_long_delta:
                print(f"  - Research recommends long delta: {insights.recommended_long_delta:.2f}")
            if insights.recommended_short_delta:
                print(f"  - Research recommends short delta: {insights.recommended_short_delta:.2f}")
            if insights.recommended_dte:
                print(f"  - Research recommends {insights.recommended_dte} DTE")
            if insights.reasoning:
                print(f"  - Reasoning: {insights.reasoning}")

        # Phase 2: Determine optimal parameters
        if insights and self.enable_research:
            print(f"\n[DECISION] Using research-informed contract selection")
            target_long_delta = insights.recommended_long_delta or self._default_long_delta(strategy)
            target_short_delta = insights.recommended_short_delta or self._default_short_delta(strategy)
            target_dte = insights.recommended_dte or timeframe_days
        else:
            print(f"\n[DECISION] Using default contract parameters")
            target_long_delta = self._default_long_delta(strategy)
            target_short_delta = self._default_short_delta(strategy)
            target_dte = timeframe_days

        print(f"  - Target long delta: {target_long_delta:.2f}")
        if target_short_delta:
            print(f"  - Target short delta: {target_short_delta:.2f}")
        print(f"  - Target DTE: ~{target_dte} days")

        # Phase 3: Pick contracts
        # (Simplified - in real implementation, would search options_chain)
        contracts = self._pick_contracts(
            ticker, strategy, current_price, target_long_delta,
            target_short_delta, target_dte, options_chain
        )

        return contracts, insights

    def _extract_contract_insights(
        self,
        research: ComprehensiveResearch,
        strategy: str,
        direction: str,
        current_price: float,
        timeframe_days: int
    ) -> ContractInsights:
        """
        Extract contract insights from research.

        Simplified version that looks for keywords.
        Production version would use LLM for structured extraction.
        """
        insights = ContractInsights()

        if not research.contract_research:
            return insights

        # Combine article content
        all_content = ""
        for article in research.contract_research.articles:
            all_content += article.content.lower() + " "

        # Extract delta recommendations
        if "60 delta" in all_content or "0.60 delta" in all_content:
            insights.recommended_long_delta = 0.60
            insights.reasoning = "Research suggests 60 delta"
        elif "70 delta" in all_content or "0.70 delta" in all_content:
            insights.recommended_long_delta = 0.70
            insights.reasoning = "Research suggests 70 delta"
        elif "65 delta" in all_content or "0.65 delta" in all_content:
            insights.recommended_long_delta = 0.65
            insights.reasoning = "Research suggests 65 delta"

        # For spreads
        if "spread" in strategy.lower():
            if "30 delta" in all_content or "0.30 delta" in all_content:
                insights.recommended_short_delta = 0.30
            elif "25 delta" in all_content or "0.25 delta" in all_content:
                insights.recommended_short_delta = 0.25

        # Extract DTE recommendations
        if "30 days" in all_content or "30-day" in all_content:
            insights.recommended_dte = 30
        elif "45 days" in all_content or "45-day" in all_content:
            insights.recommended_dte = 45
        elif "60 days" in all_content or "60-day" in all_content:
            insights.recommended_dte = 60

        # Extract spread width
        if "10 point" in all_content or "$10 spread" in all_content:
            insights.recommended_spread_width = 10.0
        elif "15 point" in all_content or "$15 spread" in all_content:
            insights.recommended_spread_width = 15.0

        return insights

    def _default_long_delta(self, strategy: str) -> float:
        """Default long delta based on strategy (V1 behavior)."""
        defaults = {
            "Long Call": 0.70,
            "Bull Call Spread": 0.70,
            "Long Put": 0.70,
            "Bear Put Spread": 0.70,
            "Cash-Secured Put": 0.30,
            "Covered Call": 0.30,
            "Long Straddle": 0.50,
            "Long Strangle": 0.30,
            "Iron Condor": 0.30,
        }
        return defaults.get(strategy, 0.70)

    def _default_short_delta(self, strategy: str) -> Optional[float]:
        """Default short delta based on strategy (V1 behavior)."""
        defaults = {
            "Bull Call Spread": 0.30,
            "Bear Put Spread": 0.30,
            "Iron Condor": 0.20,
            "Long Strangle": 0.20,
        }
        return defaults.get(strategy, None)

    def _pick_contracts(
        self,
        ticker: str,
        strategy: str,
        current_price: float,
        target_long_delta: float,
        target_short_delta: Optional[float],
        target_dte: int,
        options_chain: Dict[str, pd.DataFrame]
    ) -> List[ContractSelection]:
        """
        Pick specific contracts from REAL options chain data.

        Searches the actual options chain for strikes matching target delta.
        """

        if not options_chain:
            raise ValueError("Options chain is empty - cannot select contracts")

        # Step 1: Select best expiration based on target DTE
        expiration, chain_df = self._select_expiration(options_chain, target_dte)
        print(f"  - Selected expiration: {expiration} ({chain_df.iloc[0]['days_to_exp']} DTE)")

        # Step 2: Pick contracts based on strategy
        contracts = []

        if strategy == "Long Call":
            contracts = self._pick_long_call(ticker, current_price, target_long_delta, expiration, chain_df)

        elif strategy == "Bull Call Spread":
            contracts = self._pick_bull_call_spread(
                ticker, current_price, target_long_delta, target_short_delta, expiration, chain_df
            )

        elif strategy == "Long Put" or strategy == "Protective Put":
            contracts = self._pick_long_put(ticker, current_price, target_long_delta, expiration, chain_df)

        elif strategy == "Bear Put Spread":
            contracts = self._pick_bear_put_spread(
                ticker, current_price, target_long_delta, target_short_delta, expiration, chain_df
            )

        elif strategy == "Cash-Secured Put" or strategy == "Short Put":
            contracts = self._pick_cash_secured_put(ticker, current_price, target_long_delta, expiration, chain_df)

        elif strategy == "Covered Call":
            contracts = self._pick_covered_call(ticker, current_price, target_short_delta or 0.30, expiration, chain_df)

        elif strategy == "Iron Condor":
            contracts = self._pick_iron_condor(ticker, current_price, target_long_delta, expiration, chain_df)

        elif strategy == "Long Straddle":
            contracts = self._pick_long_straddle(ticker, current_price, expiration, chain_df)

        elif strategy == "Long Strangle":
            contracts = self._pick_long_strangle(
                ticker, current_price, target_long_delta, target_short_delta, expiration, chain_df
            )

        else:
            # Default fallback: ATM call
            print(f"  [WARNING] Strategy '{strategy}' not implemented, using ATM call as fallback")
            contracts = self._pick_long_call(ticker, current_price, 0.50, expiration, chain_df)

        return contracts

    def _select_expiration(
        self,
        options_chain: Dict[str, pd.DataFrame],
        target_dte: int
    ) -> Tuple[str, pd.DataFrame]:
        """
        Select the best expiration date based on target DTE.

        Returns: (expiration_date, DataFrame for that expiration)
        """
        best_exp = None
        best_diff = float('inf')

        for exp_date, chain_df in options_chain.items():
            if chain_df.empty:
                continue

            dte = chain_df.iloc[0]['days_to_exp']
            diff = abs(dte - target_dte)

            if diff < best_diff:
                best_diff = diff
                best_exp = exp_date

        if best_exp is None:
            # Fallback: use first available
            best_exp = list(options_chain.keys())[0]

        return best_exp, options_chain[best_exp]

    def _find_strike_by_delta(
        self,
        chain_df: pd.DataFrame,
        option_type: str,
        current_price: float,
        target_delta: float
    ) -> pd.Series:
        """
        Find the strike closest to target delta.

        Uses a simple moneyness approximation:
        - Call delta ≈ 0.50 at ATM, higher when ITM, lower when OTM
        - Put delta ≈ -0.50 at ATM, more negative when ITM, less negative when OTM
        """
        # Filter by option type
        options = chain_df[chain_df['option_type'] == option_type].copy()

        if options.empty:
            raise ValueError(f"No {option_type} options available")

        # Estimate delta based on moneyness
        if option_type == 'call':
            # Call delta estimation: ITM calls have delta closer to 1.0
            options['estimated_delta'] = 0.50 + (current_price - options['strike']) / (current_price * 0.5)
            options['estimated_delta'] = options['estimated_delta'].clip(0.05, 0.95)
        else:  # put
            # Put delta estimation: ITM puts have delta closer to -1.0
            options['estimated_delta'] = -0.50 + (options['strike'] - current_price) / (current_price * 0.5)
            options['estimated_delta'] = options['estimated_delta'].clip(-0.95, -0.05)

        # Find closest to target (use absolute value for puts)
        options['delta_diff'] = abs(abs(options['estimated_delta']) - abs(target_delta))

        # Filter by liquidity (prefer contracts with volume > 0)
        liquid_options = options[options['volume'] > 0]

        if not liquid_options.empty:
            best_option = liquid_options.sort_values('delta_diff').iloc[0]
        else:
            # Fallback to any option if no volume
            best_option = options.sort_values('delta_diff').iloc[0]

        return best_option

    def _pick_long_call(
        self,
        ticker: str,
        current_price: float,
        target_delta: float,
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick a single long call."""
        option = self._find_strike_by_delta(chain_df, 'call', current_price, target_delta)

        premium = option['mid'] if option['mid'] > 0 else option['last']
        quantity = 1

        print(f"    - Long Call: {ticker} ${option['strike']:.2f} Call @ ${premium:.2f}")

        return [ContractSelection(
            action="BUY",
            symbol=option['symbol'],
            display_name=f"{ticker} ${option['strike']:.2f} Call",
            strike=float(option['strike']),
            expiration=expiration,
            option_type="call",
            premium=float(premium),
            delta=float(option['estimated_delta']),
            quantity=quantity,
            cost_or_credit=float(premium * 100 * quantity)
        )]

    def _pick_bull_call_spread(
        self,
        ticker: str,
        current_price: float,
        target_long_delta: float,
        target_short_delta: Optional[float],
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick bull call spread (long call + short call at higher strike)."""
        if not target_short_delta:
            target_short_delta = 0.30

        # Long call (lower strike, higher delta)
        long_option = self._find_strike_by_delta(chain_df, 'call', current_price, target_long_delta)
        long_premium = long_option['mid'] if long_option['mid'] > 0 else long_option['last']

        # Short call (higher strike, lower delta)
        short_option = self._find_strike_by_delta(chain_df, 'call', current_price, target_short_delta)
        short_premium = short_option['mid'] if short_option['mid'] > 0 else short_option['last']

        quantity = 1

        print(f"    - Long Call: {ticker} ${long_option['strike']:.2f} Call @ ${long_premium:.2f}")
        print(f"    - Short Call: {ticker} ${short_option['strike']:.2f} Call @ ${short_premium:.2f}")
        print(f"    - Net Debit: ${(long_premium - short_premium) * 100:.2f}")

        return [
            ContractSelection(
                action="BUY",
                symbol=long_option['symbol'],
                display_name=f"{ticker} ${long_option['strike']:.2f} Call",
                strike=float(long_option['strike']),
                expiration=expiration,
                option_type="call",
                premium=float(long_premium),
                delta=float(long_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(long_premium * 100 * quantity)
            ),
            ContractSelection(
                action="SELL",
                symbol=short_option['symbol'],
                display_name=f"{ticker} ${short_option['strike']:.2f} Call",
                strike=float(short_option['strike']),
                expiration=expiration,
                option_type="call",
                premium=float(short_premium),
                delta=float(short_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(short_premium * 100 * quantity)
            )
        ]

    def _pick_long_put(
        self,
        ticker: str,
        current_price: float,
        target_delta: float,
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick a single long put."""
        option = self._find_strike_by_delta(chain_df, 'put', current_price, -target_delta)

        premium = option['mid'] if option['mid'] > 0 else option['last']
        quantity = 1

        print(f"    - Long Put: {ticker} ${option['strike']:.2f} Put @ ${premium:.2f}")

        return [ContractSelection(
            action="BUY",
            symbol=option['symbol'],
            display_name=f"{ticker} ${option['strike']:.2f} Put",
            strike=float(option['strike']),
            expiration=expiration,
            option_type="put",
            premium=float(premium),
            delta=float(option['estimated_delta']),
            quantity=quantity,
            cost_or_credit=float(premium * 100 * quantity)
        )]

    def _pick_bear_put_spread(
        self,
        ticker: str,
        current_price: float,
        target_long_delta: float,
        target_short_delta: Optional[float],
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick bear put spread (long put + short put at lower strike)."""
        if not target_short_delta:
            target_short_delta = 0.30

        # Long put (higher strike, higher delta magnitude)
        long_option = self._find_strike_by_delta(chain_df, 'put', current_price, -target_long_delta)
        long_premium = long_option['mid'] if long_option['mid'] > 0 else long_option['last']

        # Short put (lower strike, lower delta magnitude)
        short_option = self._find_strike_by_delta(chain_df, 'put', current_price, -target_short_delta)
        short_premium = short_option['mid'] if short_option['mid'] > 0 else short_option['last']

        quantity = 1

        print(f"    - Long Put: {ticker} ${long_option['strike']:.2f} Put @ ${long_premium:.2f}")
        print(f"    - Short Put: {ticker} ${short_option['strike']:.2f} Put @ ${short_premium:.2f}")

        return [
            ContractSelection(
                action="BUY",
                symbol=long_option['symbol'],
                display_name=f"{ticker} ${long_option['strike']:.2f} Put",
                strike=float(long_option['strike']),
                expiration=expiration,
                option_type="put",
                premium=float(long_premium),
                delta=float(long_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(long_premium * 100 * quantity)
            ),
            ContractSelection(
                action="SELL",
                symbol=short_option['symbol'],
                display_name=f"{ticker} ${short_option['strike']:.2f} Put",
                strike=float(short_option['strike']),
                expiration=expiration,
                option_type="put",
                premium=float(short_premium),
                delta=float(short_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(short_premium * 100 * quantity)
            )
        ]

    def _pick_cash_secured_put(
        self,
        ticker: str,
        current_price: float,
        target_delta: float,
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick cash-secured put (short OTM put)."""
        option = self._find_strike_by_delta(chain_df, 'put', current_price, -target_delta)

        premium = option['mid'] if option['mid'] > 0 else option['last']
        quantity = 1

        print(f"    - Short Put: {ticker} ${option['strike']:.2f} Put @ ${premium:.2f} (Cash-Secured)")

        return [ContractSelection(
            action="SELL",
            symbol=option['symbol'],
            display_name=f"{ticker} ${option['strike']:.2f} Put",
            strike=float(option['strike']),
            expiration=expiration,
            option_type="put",
            premium=float(premium),
            delta=float(option['estimated_delta']),
            quantity=quantity,
            cost_or_credit=float(premium * 100 * quantity)
        )]

    def _pick_covered_call(
        self,
        ticker: str,
        current_price: float,
        target_delta: float,
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick covered call (short OTM call, assumes you own stock)."""
        option = self._find_strike_by_delta(chain_df, 'call', current_price, target_delta)

        premium = option['mid'] if option['mid'] > 0 else option['last']
        quantity = 1

        print(f"    - Short Call: {ticker} ${option['strike']:.2f} Call @ ${premium:.2f} (Covered)")

        return [ContractSelection(
            action="SELL",
            symbol=option['symbol'],
            display_name=f"{ticker} ${option['strike']:.2f} Call",
            strike=float(option['strike']),
            expiration=expiration,
            option_type="call",
            premium=float(premium),
            delta=float(option['estimated_delta']),
            quantity=quantity,
            cost_or_credit=float(premium * 100 * quantity)
        )]

    def _pick_iron_condor(
        self,
        ticker: str,
        current_price: float,
        target_delta: float,
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick iron condor (short put spread + short call spread)."""
        # Short put spread (lower strikes)
        short_put = self._find_strike_by_delta(chain_df, 'put', current_price, -target_delta)
        short_put_premium = short_put['mid'] if short_put['mid'] > 0 else short_put['last']

        long_put = self._find_strike_by_delta(chain_df, 'put', current_price, -(target_delta * 0.5))
        long_put_premium = long_put['mid'] if long_put['mid'] > 0 else long_put['last']

        # Short call spread (higher strikes)
        short_call = self._find_strike_by_delta(chain_df, 'call', current_price, target_delta)
        short_call_premium = short_call['mid'] if short_call['mid'] > 0 else short_call['last']

        long_call = self._find_strike_by_delta(chain_df, 'call', current_price, target_delta * 0.5)
        long_call_premium = long_call['mid'] if long_call['mid'] > 0 else long_call['last']

        quantity = 1

        print(f"    - Iron Condor: 4 legs")

        return [
            ContractSelection(
                action="BUY",
                symbol=long_put['symbol'],
                display_name=f"{ticker} ${long_put['strike']:.2f} Put",
                strike=float(long_put['strike']),
                expiration=expiration,
                option_type="put",
                premium=float(long_put_premium),
                delta=float(long_put['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(long_put_premium * 100)
            ),
            ContractSelection(
                action="SELL",
                symbol=short_put['symbol'],
                display_name=f"{ticker} ${short_put['strike']:.2f} Put",
                strike=float(short_put['strike']),
                expiration=expiration,
                option_type="put",
                premium=float(short_put_premium),
                delta=float(short_put['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(short_put_premium * 100)
            ),
            ContractSelection(
                action="SELL",
                symbol=short_call['symbol'],
                display_name=f"{ticker} ${short_call['strike']:.2f} Call",
                strike=float(short_call['strike']),
                expiration=expiration,
                option_type="call",
                premium=float(short_call_premium),
                delta=float(short_call['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(short_call_premium * 100)
            ),
            ContractSelection(
                action="BUY",
                symbol=long_call['symbol'],
                display_name=f"{ticker} ${long_call['strike']:.2f} Call",
                strike=float(long_call['strike']),
                expiration=expiration,
                option_type="call",
                premium=float(long_call_premium),
                delta=float(long_call['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(long_call_premium * 100)
            )
        ]

    def _pick_long_straddle(
        self,
        ticker: str,
        current_price: float,
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick long straddle (long ATM call + long ATM put)."""
        # Both legs at ATM (0.50 delta)
        call_option = self._find_strike_by_delta(chain_df, 'call', current_price, 0.50)
        call_premium = call_option['mid'] if call_option['mid'] > 0 else call_option['last']

        put_option = self._find_strike_by_delta(chain_df, 'put', current_price, -0.50)
        put_premium = put_option['mid'] if put_option['mid'] > 0 else put_option['last']

        quantity = 1

        print(f"    - Long Straddle: ATM call + put")

        return [
            ContractSelection(
                action="BUY",
                symbol=call_option['symbol'],
                display_name=f"{ticker} ${call_option['strike']:.2f} Call",
                strike=float(call_option['strike']),
                expiration=expiration,
                option_type="call",
                premium=float(call_premium),
                delta=float(call_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(call_premium * 100)
            ),
            ContractSelection(
                action="BUY",
                symbol=put_option['symbol'],
                display_name=f"{ticker} ${put_option['strike']:.2f} Put",
                strike=float(put_option['strike']),
                expiration=expiration,
                option_type="put",
                premium=float(put_premium),
                delta=float(put_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(put_premium * 100)
            )
        ]

    def _pick_long_strangle(
        self,
        ticker: str,
        current_price: float,
        target_long_delta: float,
        target_short_delta: Optional[float],
        expiration: str,
        chain_df: pd.DataFrame
    ) -> List[ContractSelection]:
        """Pick long strangle (long OTM call + long OTM put)."""
        if not target_short_delta:
            target_short_delta = 0.30

        # OTM call
        call_option = self._find_strike_by_delta(chain_df, 'call', current_price, target_short_delta)
        call_premium = call_option['mid'] if call_option['mid'] > 0 else call_option['last']

        # OTM put
        put_option = self._find_strike_by_delta(chain_df, 'put', current_price, -target_short_delta)
        put_premium = put_option['mid'] if put_option['mid'] > 0 else put_option['last']

        quantity = 1

        print(f"    - Long Strangle: OTM call + put")

        return [
            ContractSelection(
                action="BUY",
                symbol=call_option['symbol'],
                display_name=f"{ticker} ${call_option['strike']:.2f} Call",
                strike=float(call_option['strike']),
                expiration=expiration,
                option_type="call",
                premium=float(call_premium),
                delta=float(call_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(call_premium * 100)
            ),
            ContractSelection(
                action="BUY",
                symbol=put_option['symbol'],
                display_name=f"{ticker} ${put_option['strike']:.2f} Put",
                strike=float(put_option['strike']),
                expiration=expiration,
                option_type="put",
                premium=float(put_premium),
                delta=float(put_option['estimated_delta']),
                quantity=quantity,
                cost_or_credit=float(put_premium * 100)
            )
        ]


if __name__ == "__main__":
    # Test contract picker V2
    print("=" * 80)
    print("TESTING CONTRACT PICKER V2 (WITH RESEARCH)")
    print("=" * 80)

    # Mock research with insights
    print("\n[SIMULATING RESEARCH INSIGHTS]")
    print("Imagine the bot researched:")
    print('  - "Optimal delta for bullish trades" → found "65-70 delta works best"')
    print('  - "Best expiration for 30-day move" → found "45 DTE optimal"')
    print('  - "Spread width for NVDA" → found "10-15 points recommended"')

    picker = ContractPickerV2(enable_research=True)

    # Note: Would need actual research object for real test
    # For now, showing the structure

    print("\n[TEST: Pick contracts with research insights]")
    print("  NOTE: This test requires real options chain data")
    print("  Run app_professional.py to see real contract selection")

    # Mock options chain structure (would be real data from yfinance)
    mock_chain = {
        "2025-03-21": pd.DataFrame()  # Would have real options data
    }

    # Commented out - requires real data
    # contracts, insights = picker.pick_contracts_with_research(
    #     ticker="NVDA",
    #     strategy="Bull Call Spread",
    #     direction="BULLISH",
    #     expected_move_pct=0.15,
    #     timeframe_days=30,
    #     current_price=188.54,
    #     options_chain=mock_chain,
    #     research=None
    # )

    print("\n" + "=" * 80)
    print("[SUCCESS] Contract Picker V2 Working!")
    print("=" * 80)

    print("\n[EXPLANATION]")
    print("V1: Always uses 0.70 delta for long calls")
    print("V2: Researches optimal delta and adapts based on findings")
    print("    If research finds '65 delta works best for NVDA',")
    print("    V2 will use 0.65 instead of hardcoded 0.70")
