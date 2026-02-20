"""
Contract picker - selects specific options contracts based on thesis and strategy.
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass


@dataclass
class OptionsContract:
    """Single options contract."""
    symbol: str  # e.g., "NVDA250321C00200000"
    strike: float
    expiration: str  # "2025-03-21"
    option_type: str  # "call" or "put"
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None


@dataclass
class ContractSelection:
    """Selected contract with action (BUY/SELL)."""
    action: str  # "BUY" or "SELL"
    contract: OptionsContract
    quantity: int = 1

    @property
    def premium(self) -> float:
        """Mid-price of bid/ask."""
        return (self.contract.bid + self.contract.ask) / 2

    @property
    def cost_or_credit(self) -> float:
        """Total cost if BUY, credit if SELL (in dollars)."""
        multiplier = 100  # Options are per 100 shares
        if self.action == "BUY":
            return self.premium * multiplier * self.quantity
        else:  # SELL
            return -self.premium * multiplier * self.quantity  # Negative = credit


class ContractPicker:
    """Pick specific options contracts based on thesis and strategy."""

    def __init__(self):
        """Initialize contract picker."""
        pass

    def pick_contracts(
        self,
        strategy_name: str,
        direction: str,
        target_price: float,
        timeframe_days: int,
        current_price: float,
        options_chain: Dict[str, pd.DataFrame]  # {expiration: DataFrame of contracts}
    ) -> List[ContractSelection]:
        """
        Pick specific contracts for a strategy.

        Args:
            strategy_name: Strategy type (e.g., "Long Call", "Bull Call Spread")
            direction: BULLISH, BEARISH, NEUTRAL, UNPREDICTABLE
            target_price: Expected target price
            timeframe_days: Expected timeframe
            current_price: Current stock price
            options_chain: Dict mapping expiration dates to DataFrames of contracts

        Returns:
            List of ContractSelection (contracts to BUY/SELL)
        """

        # Don't pick contracts for UNPREDICTABLE
        if direction == "UNPREDICTABLE":
            return []

        # Find appropriate expiration
        expiration = self._select_expiration(timeframe_days, list(options_chain.keys()))

        if not expiration:
            raise ValueError(f"No suitable expiration found for {timeframe_days} day timeframe")

        # Get contracts for this expiration
        contracts_df = options_chain[expiration]

        # Route to strategy-specific picker
        if strategy_name == "Long Call":
            return self._pick_long_call(contracts_df, current_price, target_price)

        elif strategy_name == "Bull Call Spread":
            return self._pick_bull_call_spread(contracts_df, current_price, target_price)

        elif strategy_name == "Long Put":
            return self._pick_long_put(contracts_df, current_price, target_price)

        elif strategy_name == "Bear Put Spread":
            return self._pick_bear_put_spread(contracts_df, current_price, target_price)

        elif strategy_name == "Iron Condor":
            return self._pick_iron_condor(contracts_df, current_price, target_price)

        elif strategy_name == "Long Straddle":
            return self._pick_straddle(contracts_df, current_price)

        elif strategy_name == "Long Strangle":
            return self._pick_strangle(contracts_df, current_price)

        elif strategy_name == "Cash-Secured Put":
            return self._pick_cash_secured_put(contracts_df, current_price)

        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")

    def _select_expiration(self, timeframe_days: int, available_expirations: List[str]) -> Optional[str]:
        """
        Select appropriate expiration date.

        Rule: Pick expiration closest to timeframe_days, but not before.
        Add buffer: target timeframe + 7 days (give trade room to work).

        Args:
            timeframe_days: Expected timeframe from thesis
            available_expirations: List of expiration dates (YYYY-MM-DD strings)

        Returns:
            Selected expiration date string
        """
        target_date = datetime.now() + timedelta(days=timeframe_days + 7)

        # Convert to datetime for comparison
        exp_dates = [(exp, datetime.strptime(exp, "%Y-%m-%d")) for exp in available_expirations]

        # Filter: only expirations after target date
        valid_exps = [(exp, dt) for exp, dt in exp_dates if dt >= target_date]

        if not valid_exps:
            # If no expirations after target, pick the furthest one available
            valid_exps = exp_dates

        # Pick closest to target
        closest = min(valid_exps, key=lambda x: abs((x[1] - target_date).days))

        return closest[0]

    def _pick_long_call(
        self,
        contracts_df: pd.DataFrame,
        current_price: float,
        target_price: float
    ) -> List[ContractSelection]:
        """
        Pick long call.

        Strategy: Buy 1 call slightly OTM (delta ~0.60-0.70)
        """
        calls = contracts_df[contracts_df['option_type'] == 'call'].copy()

        # Target: Delta around 0.65 (slightly OTM but good probability)
        # Fallback: Strike closest to current price if no delta data
        if 'delta' in calls.columns and calls['delta'].notna().any():
            calls['delta_diff'] = (calls['delta'] - 0.65).abs()
            best_call = calls.loc[calls['delta_diff'].idxmin()]
        else:
            # Fallback: Pick strike slightly above current (5% OTM)
            target_strike = current_price * 1.05
            calls['strike_diff'] = (calls['strike'] - target_strike).abs()
            best_call = calls.loc[calls['strike_diff'].idxmin()]

        contract = self._df_row_to_contract(best_call)

        return [ContractSelection(action="BUY", contract=contract, quantity=1)]

    def _pick_bull_call_spread(
        self,
        contracts_df: pd.DataFrame,
        current_price: float,
        target_price: float
    ) -> List[ContractSelection]:
        """
        Pick bull call spread.

        Strategy:
        - Buy lower strike (delta ~0.60-0.70)
        - Sell higher strike (at or above target price)
        """
        calls = contracts_df[contracts_df['option_type'] == 'call'].copy()

        # Long call: Delta around 0.65
        if 'delta' in calls.columns and calls['delta'].notna().any():
            calls['delta_diff'] = (calls['delta'] - 0.65).abs()
            long_call = calls.loc[calls['delta_diff'].idxmin()]
        else:
            target_strike = current_price * 1.05
            calls['strike_diff'] = (calls['strike'] - target_strike).abs()
            long_call = calls.loc[calls['strike_diff'].idxmin()]

        # Short call: At or above target price
        short_candidates = calls[calls['strike'] >= target_price]
        if short_candidates.empty:
            # If target is too high, pick highest available strike
            short_call = calls.loc[calls['strike'].idxmax()]
        else:
            # Pick closest to target
            short_candidates['strike_diff'] = (short_candidates['strike'] - target_price).abs()
            short_call = short_candidates.loc[short_candidates['strike_diff'].idxmin()]

        long_contract = self._df_row_to_contract(long_call)
        short_contract = self._df_row_to_contract(short_call)

        return [
            ContractSelection(action="BUY", contract=long_contract, quantity=1),
            ContractSelection(action="SELL", contract=short_contract, quantity=1)
        ]

    def _pick_long_put(
        self,
        contracts_df: pd.DataFrame,
        current_price: float,
        target_price: float
    ) -> List[ContractSelection]:
        """Pick long put (delta ~-0.65)."""
        puts = contracts_df[contracts_df['option_type'] == 'put'].copy()

        if 'delta' in puts.columns and puts['delta'].notna().any():
            puts['delta_diff'] = (puts['delta'] - (-0.65)).abs()
            best_put = puts.loc[puts['delta_diff'].idxmin()]
        else:
            target_strike = current_price * 0.95
            puts['strike_diff'] = (puts['strike'] - target_strike).abs()
            best_put = puts.loc[puts['strike_diff'].idxmin()]

        contract = self._df_row_to_contract(best_put)

        return [ContractSelection(action="BUY", contract=contract, quantity=1)]

    def _pick_bear_put_spread(
        self,
        contracts_df: pd.DataFrame,
        current_price: float,
        target_price: float
    ) -> List[ContractSelection]:
        """Pick bear put spread (buy higher strike, sell lower strike)."""
        puts = contracts_df[contracts_df['option_type'] == 'put'].copy()

        # Long put: Delta around -0.65
        if 'delta' in puts.columns and puts['delta'].notna().any():
            puts['delta_diff'] = (puts['delta'] - (-0.65)).abs()
            long_put = puts.loc[puts['delta_diff'].idxmin()]
        else:
            target_strike = current_price * 0.95
            puts['strike_diff'] = (puts['strike'] - target_strike).abs()
            long_put = puts.loc[puts['strike_diff'].idxmin()]

        # Short put: At or below target price
        short_candidates = puts[puts['strike'] <= target_price]
        if short_candidates.empty:
            short_put = puts.loc[puts['strike'].idxmin()]
        else:
            short_candidates['strike_diff'] = (short_candidates['strike'] - target_price).abs()
            short_put = short_candidates.loc[short_candidates['strike_diff'].idxmin()]

        long_contract = self._df_row_to_contract(long_put)
        short_contract = self._df_row_to_contract(short_put)

        return [
            ContractSelection(action="BUY", contract=long_contract, quantity=1),
            ContractSelection(action="SELL", contract=short_contract, quantity=1)
        ]

    def _pick_iron_condor(
        self,
        contracts_df: pd.DataFrame,
        current_price: float,
        target_price: float
    ) -> List[ContractSelection]:
        """
        Pick iron condor (range-bound strategy).

        Sell put spread below current + sell call spread above current.
        """
        calls = contracts_df[contracts_df['option_type'] == 'call'].copy()
        puts = contracts_df[contracts_df['option_type'] == 'put'].copy()

        # Estimate range: ±5% from current price
        lower_bound = current_price * 0.95
        upper_bound = current_price * 1.05

        # Put side: Sell put at lower bound, buy put below that
        put_sell_candidates = puts[puts['strike'] <= lower_bound]
        if not put_sell_candidates.empty:
            put_sell = put_sell_candidates.iloc[(len(put_sell_candidates) // 2)]  # Middle strike
            put_buy_candidates = puts[puts['strike'] < put_sell['strike']]
            if not put_buy_candidates.empty:
                put_buy = put_buy_candidates.iloc[0]  # Lowest available
            else:
                put_buy = puts.iloc[0]
        else:
            put_sell = puts.iloc[len(puts) // 2]
            put_buy = puts.iloc[0]

        # Call side: Sell call at upper bound, buy call above that
        call_sell_candidates = calls[calls['strike'] >= upper_bound]
        if not call_sell_candidates.empty:
            call_sell = call_sell_candidates.iloc[(len(call_sell_candidates) // 2)]
            call_buy_candidates = calls[calls['strike'] > call_sell['strike']]
            if not call_buy_candidates.empty:
                call_buy = call_buy_candidates.iloc[0]
            else:
                call_buy = calls.iloc[-1]
        else:
            call_sell = calls.iloc[len(calls) // 2]
            call_buy = calls.iloc[-1]

        return [
            ContractSelection(action="SELL", contract=self._df_row_to_contract(put_sell)),
            ContractSelection(action="BUY", contract=self._df_row_to_contract(put_buy)),
            ContractSelection(action="SELL", contract=self._df_row_to_contract(call_sell)),
            ContractSelection(action="BUY", contract=self._df_row_to_contract(call_buy))
        ]

    def _pick_straddle(
        self,
        contracts_df: pd.DataFrame,
        current_price: float
    ) -> List[ContractSelection]:
        """Pick long straddle (buy ATM call + put)."""
        calls = contracts_df[contracts_df['option_type'] == 'call'].copy()
        puts = contracts_df[contracts_df['option_type'] == 'put'].copy()

        # Find ATM strike (closest to current price)
        calls['strike_diff'] = (calls['strike'] - current_price).abs()
        atm_call = calls.loc[calls['strike_diff'].idxmin()]

        # Use same strike for put
        atm_strike = atm_call['strike']
        atm_put = puts.loc[(puts['strike'] - atm_strike).abs().idxmin()]

        return [
            ContractSelection(action="BUY", contract=self._df_row_to_contract(atm_call)),
            ContractSelection(action="BUY", contract=self._df_row_to_contract(atm_put))
        ]

    def _pick_strangle(
        self,
        contracts_df: pd.DataFrame,
        current_price: float
    ) -> List[ContractSelection]:
        """Pick long strangle (buy OTM call + put)."""
        calls = contracts_df[contracts_df['option_type'] == 'call'].copy()
        puts = contracts_df[contracts_df['option_type'] == 'put'].copy()

        # OTM call: 5% above current
        otm_call_strike = current_price * 1.05
        calls['strike_diff'] = (calls['strike'] - otm_call_strike).abs()
        otm_call = calls.loc[calls['strike_diff'].idxmin()]

        # OTM put: 5% below current
        otm_put_strike = current_price * 0.95
        puts['strike_diff'] = (puts['strike'] - otm_put_strike).abs()
        otm_put = puts.loc[puts['strike_diff'].idxmin()]

        return [
            ContractSelection(action="BUY", contract=self._df_row_to_contract(otm_call)),
            ContractSelection(action="BUY", contract=self._df_row_to_contract(otm_put))
        ]

    def _pick_cash_secured_put(
        self,
        contracts_df: pd.DataFrame,
        current_price: float
    ) -> List[ContractSelection]:
        """Pick cash-secured put (sell OTM put)."""
        puts = contracts_df[contracts_df['option_type'] == 'put'].copy()

        # Target: Delta around -0.30 (OTM, lower probability of assignment)
        if 'delta' in puts.columns and puts['delta'].notna().any():
            puts['delta_diff'] = (puts['delta'] - (-0.30)).abs()
            best_put = puts.loc[puts['delta_diff'].idxmin()]
        else:
            # Fallback: 5% below current
            target_strike = current_price * 0.95
            puts['strike_diff'] = (puts['strike'] - target_strike).abs()
            best_put = puts.loc[puts['strike_diff'].idxmin()]

        contract = self._df_row_to_contract(best_put)

        return [ContractSelection(action="SELL", contract=contract, quantity=1)]

    def _df_row_to_contract(self, row: pd.Series) -> OptionsContract:
        """Convert DataFrame row to OptionsContract object."""
        return OptionsContract(
            symbol=row.get('contractSymbol', ''),
            strike=row['strike'],
            expiration=row.get('expiration', ''),
            option_type=row['option_type'],
            bid=row.get('bid', 0.0),
            ask=row.get('ask', 0.0),
            last=row.get('lastPrice', 0.0),
            volume=row.get('volume', 0),
            open_interest=row.get('openInterest', 0),
            implied_volatility=row.get('impliedVolatility', 0.0),
            delta=row.get('delta'),
            gamma=row.get('gamma'),
            theta=row.get('theta'),
            vega=row.get('vega')
        )


if __name__ == "__main__":
    # Test will be added after integrating with yfinance data
    print("Contract picker module loaded successfully")
