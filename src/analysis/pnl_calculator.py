"""
P/L Calculator for Options Strategies

Calculates profit/loss at various stock prices, max profit/loss, breakevens,
and portfolio Greeks for options positions.
"""
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from src.models.thesis import ContractSelection

try:
    import mibian
    MIBIAN_AVAILABLE = True
except ImportError:
    MIBIAN_AVAILABLE = False
    print("Warning: mibian not available. Greeks calculations will be disabled.")


class PnLCalculator:
    """Calculate P/L and Greeks for options strategies."""

    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize P/L calculator.

        Args:
            risk_free_rate: Risk-free rate for Greeks calculation (default 5%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_option_value_at_price(
        self,
        contract: ContractSelection,
        stock_price: float
    ) -> float:
        """
        Calculate option intrinsic value at expiration for a given stock price.

        Args:
            contract: ContractSelection with strike, option_type
            stock_price: Stock price to evaluate at

        Returns:
            Option intrinsic value (before premium cost)
        """
        if contract.option_type == "call":
            return max(stock_price - contract.strike, 0)
        else:  # put
            return max(contract.strike - stock_price, 0)

    def calculate_pnl_at_price(
        self,
        contracts: List[ContractSelection],
        stock_price: float
    ) -> float:
        """
        Calculate total P/L for all contracts at a given stock price (at expiration).

        Args:
            contracts: List of ContractSelection (BUY/SELL)
            stock_price: Stock price to evaluate at

        Returns:
            Total P/L in dollars
        """
        total_pnl = 0.0

        for contract in contracts:
            # Calculate option value at this price
            option_value = self.calculate_option_value_at_price(contract, stock_price)

            # Calculate P/L for this contract
            if contract.action == "BUY":
                # Bought option: profit = (value - premium) * 100
                pnl = (option_value - contract.premium) * 100 * contract.quantity
            else:  # SELL
                # Sold option: profit = (premium - value) * 100
                pnl = (contract.premium - option_value) * 100 * contract.quantity

            total_pnl += pnl

        return total_pnl

    def calculate_max_profit_loss(
        self,
        contracts: List[ContractSelection],
        current_price: float,
        price_range_pct: float = 0.5
    ) -> Dict[str, float]:
        """
        Calculate max profit, max loss, and breakevens.

        Args:
            contracts: List of ContractSelection
            current_price: Current stock price
            price_range_pct: % range to scan (0.5 = ±50%)

        Returns:
            Dict with max_profit, max_loss, breakeven(s), max_profit_price, max_loss_price
        """
        # Generate price range to scan
        min_price = current_price * (1 - price_range_pct)
        max_price = current_price * (1 + price_range_pct)

        # Include all strikes in range
        strikes = [c.strike for c in contracts]
        min_price = min(min_price, min(strikes) * 0.8)
        max_price = max(max_price, max(strikes) * 1.2)

        prices = np.linspace(min_price, max_price, 200)

        # Calculate P/L at each price
        pnls = [self.calculate_pnl_at_price(contracts, p) for p in prices]

        # Find max profit/loss
        max_profit = max(pnls)
        max_loss = min(pnls)

        max_profit_idx = pnls.index(max_profit)
        max_loss_idx = pnls.index(max_loss)

        max_profit_price = prices[max_profit_idx]
        max_loss_price = prices[max_loss_idx]

        # Find breakevens (where P/L crosses 0)
        breakevens = []
        for i in range(len(pnls) - 1):
            if (pnls[i] <= 0 and pnls[i+1] > 0) or (pnls[i] >= 0 and pnls[i+1] < 0):
                # Linear interpolation to find exact breakeven
                price_diff = prices[i+1] - prices[i]
                pnl_diff = pnls[i+1] - pnls[i]
                if pnl_diff != 0:
                    breakeven = prices[i] - pnls[i] * (price_diff / pnl_diff)
                    breakevens.append(breakeven)

        return {
            "max_profit": max_profit,
            "max_loss": max_loss,
            "max_profit_price": max_profit_price,
            "max_loss_price": max_loss_price,
            "breakevens": breakevens,
            "num_breakevens": len(breakevens)
        }

    def calculate_portfolio_greeks(
        self,
        contracts: List[ContractSelection],
        stock_price: float,
        volatility: float,
        days_to_expiration: int
    ) -> Optional[Dict[str, float]]:
        """
        Calculate portfolio Greeks (Delta, Theta, Vega, Gamma).

        Args:
            contracts: List of ContractSelection
            stock_price: Current stock price
            volatility: Implied volatility (as decimal, e.g., 0.40 for 40%)
            days_to_expiration: Days until expiration

        Returns:
            Dict with portfolio_delta, portfolio_theta, portfolio_vega, portfolio_gamma
            or None if mibian not available
        """
        if not MIBIAN_AVAILABLE:
            return None

        portfolio_delta = 0.0
        portfolio_theta = 0.0
        portfolio_vega = 0.0
        portfolio_gamma = 0.0

        for contract in contracts:
            try:
                # mibian expects volatility as percentage
                bs = mibian.BS(
                    [stock_price, contract.strike, self.risk_free_rate * 100, days_to_expiration],
                    volatility=volatility * 100
                )

                # Get Greeks based on option type.
                # mibian returns per-share values:
                #   callDelta/putDelta: already 0-1 decimal (no division needed)
                #   callTheta/putTheta: annual theta — divide by 365 for daily
                #   vega: per 1% IV change per share (no division needed)
                #   gamma: per $1 stock move per share (no division needed)
                if contract.option_type == "call":
                    delta = bs.callDelta            # Already 0-1 decimal
                    theta = bs.callTheta / 365      # Annual → daily
                    vega = bs.vega                  # Per 1% IV change, per share
                    gamma = bs.gamma                # Per $1 move, per share
                else:  # put
                    delta = bs.putDelta             # Already -1 to 0 decimal
                    theta = bs.putTheta / 365
                    vega = bs.vega
                    gamma = bs.gamma

                # Apply sign based on BUY/SELL
                multiplier = 1 if contract.action == "BUY" else -1

                # Multiply by 100 (shares per contract) to get portfolio-level Greeks
                portfolio_delta += delta * multiplier * contract.quantity * 100
                portfolio_theta += theta * multiplier * contract.quantity * 100
                portfolio_vega += vega * multiplier * contract.quantity * 100
                portfolio_gamma += gamma * multiplier * contract.quantity * 100

            except Exception as e:
                print(f"Warning: Could not calculate Greeks for {contract.display_name}: {e}")
                continue

        return {
            "portfolio_delta": portfolio_delta,
            "portfolio_theta": portfolio_theta,
            "portfolio_vega": portfolio_vega,
            "portfolio_gamma": portfolio_gamma
        }

    def generate_pnl_curve(
        self,
        contracts: List[ContractSelection],
        current_price: float,
        price_range_pct: float = 0.5,
        num_points: int = 100
    ) -> pd.DataFrame:
        """
        Generate P/L curve data for visualization.

        Args:
            contracts: List of ContractSelection
            current_price: Current stock price
            price_range_pct: % range to show (0.5 = ±50%)
            num_points: Number of price points to calculate

        Returns:
            DataFrame with columns: stock_price, pnl
        """
        # Determine price range including strikes
        strikes = [c.strike for c in contracts]
        min_strike = min(strikes)
        max_strike = max(strikes)

        # Extend range beyond strikes
        min_price = min(current_price * (1 - price_range_pct), min_strike * 0.8)
        max_price = max(current_price * (1 + price_range_pct), max_strike * 1.2)

        # Generate price points
        prices = np.linspace(min_price, max_price, num_points)

        # Calculate P/L at each price
        pnls = [self.calculate_pnl_at_price(contracts, p) for p in prices]

        return pd.DataFrame({
            "stock_price": prices,
            "pnl": pnls
        })

    def calculate_complete_analysis(
        self,
        contracts: List[ContractSelection],
        current_price: float,
        volatility: float = 0.40,
        days_to_expiration: int = 30
    ) -> Dict:
        """
        Calculate complete P/L analysis including all metrics.

        Args:
            contracts: List of ContractSelection
            current_price: Current stock price
            volatility: Implied volatility (default 40%)
            days_to_expiration: Days until expiration

        Returns:
            Dict with all P/L metrics, Greeks, and curve data
        """
        # Calculate max profit/loss and breakevens
        max_pl = self.calculate_max_profit_loss(contracts, current_price)

        # Calculate current P/L
        current_pnl = self.calculate_pnl_at_price(contracts, current_price)

        # Calculate portfolio Greeks
        greeks = self.calculate_portfolio_greeks(
            contracts, current_price, volatility, days_to_expiration
        )

        # Generate P/L curve
        pnl_curve = self.generate_pnl_curve(contracts, current_price)

        # Calculate net debit/credit
        net_debit_credit = sum(
            c.cost_or_credit if c.action == "BUY" else -c.cost_or_credit
            for c in contracts
        )

        # Calculate risk/reward ratio
        if max_pl["max_loss"] != 0:
            risk_reward_ratio = abs(max_pl["max_profit"] / max_pl["max_loss"])
        else:
            risk_reward_ratio = float('inf')

        return {
            "current_pnl": current_pnl,
            "max_profit": max_pl["max_profit"],
            "max_loss": max_pl["max_loss"],
            "max_profit_price": max_pl["max_profit_price"],
            "max_loss_price": max_pl["max_loss_price"],
            "breakevens": max_pl["breakevens"],
            "num_breakevens": max_pl["num_breakevens"],
            "net_debit_credit": net_debit_credit,
            "risk_reward_ratio": risk_reward_ratio,
            "greeks": greeks,
            "pnl_curve": pnl_curve,
            "current_price": current_price
        }
