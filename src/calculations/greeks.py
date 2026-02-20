"""
Options Greeks calculations using mibian library.
"""
import mibian
import pandas as pd
from datetime import datetime
from typing import Dict


def calculate_greeks(
    stock_price: float,
    strike: float,
    days_to_expiration: int,
    volatility: float,
    risk_free_rate: float = 0.05,
    option_type: str = "call"
) -> Dict[str, float]:
    """
    Calculate option Greeks using Black-Scholes model.

    Args:
        stock_price: Current stock price
        strike: Option strike price
        days_to_expiration: Days until expiration
        volatility: Implied volatility (as decimal, e.g., 0.25 = 25%)
        risk_free_rate: Risk-free interest rate (default 5%)
        option_type: "call" or "put"

    Returns:
        Dictionary with Greeks: delta, gamma, theta, vega, price
    """
    # Convert volatility to percentage for mibian
    vol_pct = volatility * 100
    rate_pct = risk_free_rate * 100

    # Calculate using Black-Scholes
    bs = mibian.BS(
        [stock_price, strike, rate_pct, days_to_expiration],
        volatility=vol_pct
    )

    if option_type.lower() == "call":
        return {
            "price": bs.callPrice,
            "delta": bs.callDelta,
            "gamma": bs.gamma,
            "theta": bs.callTheta,
            "vega": bs.vega,
        }
    else:  # put
        return {
            "price": bs.putPrice,
            "delta": bs.putDelta,
            "gamma": bs.gamma,
            "theta": bs.putTheta,
            "vega": bs.vega,
        }


def add_greeks_to_chain(
    options_df: pd.DataFrame,
    stock_price: float,
    volatility: float,
    risk_free_rate: float = 0.05
) -> pd.DataFrame:
    """
    Add Greeks to an options chain DataFrame.

    Args:
        options_df: DataFrame with columns: strike, expiration, type
        stock_price: Current stock price
        volatility: Implied volatility estimate
        risk_free_rate: Risk-free rate (default 5%)

    Returns:
        DataFrame with added columns: price, delta, gamma, theta, vega
    """
    if options_df.empty:
        raise ValueError("Options DataFrame is empty - no options data available")

    if 'expiration' not in options_df.columns:
        raise ValueError(f"Missing 'expiration' column. Available columns: {list(options_df.columns)}")

    df = options_df.copy()

    # Calculate days to expiration
    today = datetime.now().date()
    df["days_to_exp"] = df["expiration"].apply(
        lambda x: (x - today).days if hasattr(x, 'days') else (pd.to_datetime(x).date() - today).days
    )

    # Calculate Greeks for each option
    greeks_data = []
    for _, row in df.iterrows():
        greeks = calculate_greeks(
            stock_price=stock_price,
            strike=row["strike"],
            days_to_expiration=row["days_to_exp"],
            volatility=volatility,
            risk_free_rate=risk_free_rate,
            option_type=row["type"]
        )
        greeks_data.append(greeks)

    # Add Greeks to DataFrame
    greeks_df = pd.DataFrame(greeks_data)
    df = pd.concat([df, greeks_df], axis=1)

    return df


def calculate_covered_call_metrics(
    stock_price: float,
    strike: float,
    premium: float,
    shares: int = 100
) -> Dict[str, float]:
    """
    Calculate key metrics for a covered call position.

    Args:
        stock_price: Current stock price
        strike: Call option strike
        premium: Option premium received
        shares: Number of shares (default 100)

    Returns:
        Dictionary with metrics: max_profit, max_loss, breakeven, return_if_called
    """
    cost_basis = stock_price * shares
    premium_received = premium * shares

    # If called away
    profit_if_called = (strike - stock_price) * shares + premium_received
    return_if_called = profit_if_called / cost_basis

    # Max loss (stock goes to zero, keep premium)
    max_loss = cost_basis - premium_received

    # Breakeven (stock price where you break even)
    breakeven = stock_price - premium

    return {
        "max_profit": profit_if_called,
        "max_loss": max_loss,
        "breakeven": breakeven,
        "return_if_called": return_if_called,
        "premium_received": premium_received,
        "downside_protection": premium / stock_price,  # % protected
    }


if __name__ == "__main__":
    # Test Greeks calculation
    print("Testing Greeks calculation...\n")

    stock_price = 180.0
    strike = 185.0
    days = 30
    vol = 0.25

    greeks = calculate_greeks(stock_price, strike, days, vol, option_type="call")

    print(f"Stock: ${stock_price}, Strike: ${strike}, DTE: {days}, IV: {vol*100}%")
    print(f"Call Price: ${greeks['price']:.2f}")
    print(f"Delta: {greeks['delta']:.4f}")
    print(f"Gamma: {greeks['gamma']:.4f}")
    print(f"Theta: {greeks['theta']:.4f}")
    print(f"Vega: {greeks['vega']:.4f}")

    # Test covered call metrics
    print("\n\nTesting Covered Call Metrics...\n")
    metrics = calculate_covered_call_metrics(
        stock_price=180.0,
        strike=185.0,
        premium=3.50
    )

    print(f"Premium received: ${metrics['premium_received']:.2f}")
    print(f"Max profit: ${metrics['max_profit']:.2f}")
    print(f"Return if called: {metrics['return_if_called']*100:.2f}%")
    print(f"Breakeven: ${metrics['breakeven']:.2f}")
    print(f"Downside protection: {metrics['downside_protection']*100:.2f}%")
