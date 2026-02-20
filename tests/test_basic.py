"""Basic tests to verify core components are working."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that core modules can be imported."""
    try:
        from data.yfinance_client import YFinanceClient
        from models.thesis import InvestmentThesis
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")


def test_yfinance_client():
    """Test that YFinance client can fetch basic data."""
    from data.yfinance_client import YFinanceClient

    client = YFinanceClient()
    price = client.get_stock_price("AAPL")

    # Verify we got a valid price back
    assert price is not None
    assert isinstance(price, float)
    assert price > 0


def test_thesis_model():
    """Test that thesis data model works."""
    from models.thesis import InvestmentThesis

    thesis = InvestmentThesis(
        direction="BULLISH",
        conviction=75,
        expected_move="+15% in 30 days",
        expected_move_pct=15.0,
        target_price=200.0,
        timeframe="30 days",
        timeframe_days=30,
        thesis_summary="Test thesis",
        bull_case=["Bull point 1", "Bull point 2"],
        bear_case=["Bear point 1", "Bear point 2"]
    )

    assert thesis.direction == "BULLISH"
    assert thesis.conviction == 75
    assert thesis.expected_move_pct == 15.0


def test_requirements_installed():
    """Test that key requirements are installed."""
    required_packages = [
        "streamlit",
        "pandas",
        "numpy",
        "yfinance",
        "plotly",
        "openai",
        "anthropic",
        "requests",
        "bs4",  # beautifulsoup4
    ]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            pytest.fail(f"Required package '{package}' is not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
