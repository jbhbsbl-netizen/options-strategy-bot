"""
Professional Options Strategy Bot - Clean, Clear UI

This version focuses on:
- Clear visual hierarchy
- Professional styling
- Earnings ticker with company logos
- Easy-to-understand layout
"""
import streamlit as st
import streamlit.components.v1 as components
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import time

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
    page_title="Options Strategy Bot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Styling
st.markdown("""
<style>
    /* Main Layout */
    .main {
        background-color: #f8f9fa;
    }

    /* Header */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
        text-align: center;
    }

    .subtitle {
        font-size: 1.1rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Cards */
    .info-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }

    .card-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Thesis Direction Badges */
    .thesis-bullish {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1.2rem;
        font-weight: 600;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
    }

    .thesis-bearish {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1.2rem;
        font-weight: 600;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3);
    }

    .thesis-neutral {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1.2rem;
        font-weight: 600;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
    }

    /* Strategy Box */
    .strategy-box {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(139, 92, 246, 0.3);
    }

    .strategy-name {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .metric-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }

    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e293b;
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        background: white;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 1rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        border-radius: 8px;
        font-weight: 600;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
    st.session_state.ticker = ""
    st.session_state.thesis = None
    st.session_state.research = None
    st.session_state.strategy = None
    st.session_state.earnings_strategy = None
    st.session_state.contracts = None
    st.session_state.pnl_analysis = None
    st.session_state.stock_data = None
    st.session_state.earnings_info = None
    st.session_state.current_page = "home"  # Track which page to show: "home", "loading", "results"

# ============================================================================
# EARNINGS TICKER (Top Bar)
# ============================================================================

def get_company_domain(ticker: str) -> str:
    """Get company domain for logo fetching."""
    ticker_to_domain = {
        # Tech Giants
        "NVDA": "nvidia.com", "AAPL": "apple.com", "TSLA": "tesla.com", "MSFT": "microsoft.com",
        "GOOGL": "google.com", "AMZN": "amazon.com", "META": "meta.com", "NFLX": "netflix.com",
        # Tech & Software
        "AMD": "amd.com", "INTC": "intel.com", "ORCL": "oracle.com", "CSCO": "cisco.com",
        "ADBE": "adobe.com", "CRM": "salesforce.com", "SNOW": "snowflake.com", "SHOP": "shopify.com",
        "SQ": "block.xyz", "BLOCK": "block.xyz", "SPOT": "spotify.com", "UBER": "uber.com", "PLTR": "palantir.com",
        "RBLX": "roblox.com", "U": "unity.com", "DDOG": "datadoghq.com", "NET": "cloudflare.com",
        "CRWD": "crowdstrike.com", "ZS": "zscaler.com", "OKTA": "okta.com", "MDB": "mongodb.com",
        "TWLO": "twilio.com",
        # Consumer
        "NKE": "nike.com", "SBUX": "starbucks.com", "MCD": "mcdonalds.com", "DIS": "disney.com",
        "BKNG": "booking.com", "ABNB": "airbnb.com", "LYFT": "lyft.com", "DASH": "doordash.com",
        # Retail
        "WMT": "walmart.com", "TGT": "target.com", "COST": "costco.com", "HD": "homedepot.com",
        "LOW": "lowes.com", "ETSY": "etsy.com", "W": "wayfair.com",
        # Finance
        "JPM": "jpmorganchase.com", "BAC": "bankofamerica.com", "GS": "goldmansachs.com",
        "MS": "morganstanley.com", "C": "citigroup.com", "WFC": "wellsfargo.com",
        "V": "visa.com", "MA": "mastercard.com", "PYPL": "paypal.com", "COIN": "coinbase.com",
        # Healthcare
        "JNJ": "jnj.com", "PFE": "pfizer.com", "UNH": "unitedhealthgroup.com",
        "CVS": "cvshealth.com", "MRNA": "modernatx.com", "ABBV": "abbvie.com", "LLY": "lilly.com",
        # Industrials
        "BA": "boeing.com", "CAT": "caterpillar.com", "GE": "ge.com", "DE": "deere.com",
        "UPS": "ups.com", "FDX": "fedex.com",
        # Energy
        "XOM": "exxonmobil.com", "CVX": "chevron.com", "COP": "conocophillips.com", "SLB": "slb.com",
        # Communication
        "T": "att.com", "VZ": "verizon.com", "TMUS": "t-mobile.com", "CMCSA": "comcast.com",
        # Consumer Goods
        "PG": "pg.com", "KO": "coca-cola.com", "PEP": "pepsico.com", "LULU": "lululemon.com",
        # Semiconductors
        "AVGO": "broadcom.com", "QCOM": "qualcomm.com", "MU": "micron.com",
        "AMAT": "appliedmaterials.com", "KLAC": "kla.com", "LRCX": "lamresearch.com",
        "MRVL": "marvell.com", "ON": "onsemi.com",
        # Other
        "RIVN": "rivian.com", "LCID": "lucidmotors.com", "ZM": "zoom.us",
        "DOCU": "docusign.com", "PTON": "onepeloton.com", "BYND": "beyondmeat.com",
        "CHGG": "chegg.com",
    }
    return ticker_to_domain.get(ticker, f"{ticker.lower()}.com")

def get_ticker_color(ticker: str) -> str:
    """Get vibrant, professional color for ticker badge."""
    colors = {
        'A': '#3b82f6', 'B': '#8b5cf6', 'C': '#06b6d4', 'D': '#f97316',
        'E': '#10b981', 'F': '#ec4899', 'G': '#f59e0b', 'H': '#6366f1',
        'I': '#14b8a6', 'J': '#a855f7', 'K': '#84cc16', 'L': '#ef4444',
        'M': '#8b5cf6', 'N': '#10b981', 'O': '#f59e0b', 'P': '#ec4899',
        'Q': '#06b6d4', 'R': '#ef4444', 'S': '#84cc16', 'T': '#f97316',
        'U': '#6366f1', 'V': '#14b8a6', 'W': '#a855f7', 'X': '#3b82f6',
        'Y': '#f59e0b', 'Z': '#10b981',
    }
    return colors.get(ticker[0], '#64748b')

def create_earnings_ticker():
    """Create scrolling earnings ticker - AUTONOMOUS selection of companies with upcoming earnings."""
    try:
        client = YFinanceClient()

        # CLEANED universe - removed delisted/acquired/problematic tickers (250+ active stocks)
        # This allows the bot to find ALL relevant companies with upcoming earnings
        tickers = [
            # Mega Cap Tech
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ORCL",
            # Tech & Software
            "AMD", "INTC", "CSCO", "ADBE", "CRM", "SNOW", "SHOP", "SPOT", "UBER",
            "PLTR", "RBLX", "U", "DDOG", "NET", "CRWD", "ZS", "OKTA", "MDB", "TWLO",
            "NOW", "WDAY", "TEAM", "ZM", "DOCU", "MNDY", "PATH", "S", "BILL", "GTLB",
            "HUBS", "VEEV", "ESTC", "CFLT", "ASAN", "PD", "IOT",
            # Semiconductors
            "QCOM", "TXN", "MU", "AMAT", "LRCX", "KLAC", "MRVL", "NXPI", "MCHP", "ON",
            "ADI", "MPWR", "SWKS", "QRVO", "ALGM",
            # Consumer Tech
            "NFLX", "SPOT", "RBLX", "MTCH", "PINS", "SNAP", "LYFT", "DASH", "ABNB",
            # E-commerce & Retail
            "WMT", "TGT", "COST", "HD", "LOW", "DG", "DLTR", "BBY", "BURL", "ROST",
            "TJX", "M", "KSS", "DKS", "BBWI", "ANF", "AEO", "URBN",
            "ETSY", "W", "CHWY", "RH",
            # Consumer Brands
            "NKE", "LULU", "SBUX", "MCD", "YUM", "CMG", "QSR", "WEN", "JACK", "PZZA",
            "DPZ", "DRI", "BLMN", "TXRH", "WING", "SHAK", "CAKE",
            # Entertainment & Media
            "DIS", "NFLX", "FOXA", "FOX", "LYV", "IMAX",
            # Finance - Banks
            "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "USB", "PNC",
            "TFC", "COF", "BK", "STT", "NTRS", "CFG", "KEY", "RF", "FITB", "HBAN",
            # Finance - Payments & Fintech
            "V", "MA", "PYPL", "AXP", "AFRM", "COIN", "SOFI", "UPST", "LC",
            "NU", "MELI", "STNE", "PAGS",
            # Finance - Insurance
            "PGR", "CB", "TRV", "ALL", "AIG", "MET", "PRU", "AFL", "HIG",
            # Healthcare - Pharma
            "JNJ", "PFE", "ABBV", "LLY", "MRK", "BMY", "AMGN", "GILD", "BIIB", "VRTX",
            "REGN", "ISRG", "MRNA", "EXAS", "IONS", "ALNY", "INCY",
            # Healthcare - Biotech
            "CRSP", "VCYT", "TDOC",
            # Healthcare - Services
            "UNH", "CVS", "CI", "ELV", "HUM", "CNC", "MOH", "HCA", "THC", "UHS",
            # Industrials
            "BA", "CAT", "DE", "GE", "HON", "UPS", "FDX", "LMT", "RTX", "NOC",
            "GD", "LHX", "TDG", "ETN", "EMR", "ITW", "PH", "ROK", "DOV", "XYL",
            # Auto & EV
            "TSLA", "F", "GM", "RIVN", "LCID",
            # Energy
            "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "DVN",
            "FANG", "OXY", "APA", "HAL", "BKR", "NOV",
            # Telecom
            "T", "VZ", "TMUS", "CMCSA", "CHTR", "LUMN",
            # Consumer Goods
            "PG", "KO", "PEP", "COST", "WMT", "CL", "KMB", "CHD", "CLX", "EL",
            "TAP", "STZ", "CELH", "KDP", "KHC", "GIS", "CPB",
            # Materials & Chemicals
            "LIN", "APD", "ECL", "SHW", "DD", "DOW", "PPG", "NEM", "FCX", "GOLD",
            # Real Estate & REITs
            "AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "SPG", "O", "WELL", "AVB",
            # Other Growth
            "ROKU", "FVRR", "UPWK", "ZG", "OPEN", "HOOD", "DKNG", "PENN", "MGM",
            "WYNN", "LVS", "CZR", "BKNG", "EXPE", "TRIP", "ABNB", "MAR", "HLT",
            # More Tech
            "IBM", "HPQ", "NTAP", "WDC", "STX", "PSTG", "SMCI", "DELL", "HPE",
            # Retail Specialty
            "ULTA", "ELF", "COTY", "TPR", "CPRI", "RL", "PVH", "VFC", "UAA",
        ]

        # Fetch earnings for ALL tickers
        earnings_calendar = client.get_earnings_calendar(tickers)

        if not earnings_calendar:
            return None

        # AUTONOMOUS FILTERING: Only show companies with actual upcoming earnings in next 90 days
        upcoming_earnings = [
            item for item in earnings_calendar
            if item['days_until'] >= 0 and item['days_until'] <= 90
        ]

        if not upcoming_earnings:
            return None

        # Sort by date (soonest first) and show MORE companies (50 instead of 25)
        upcoming_earnings = sorted(upcoming_earnings, key=lambda x: x['days_until'])[:50]

        # Build ticker items with HIGH QUALITY logos
        ticker_items = []
        for item in upcoming_earnings:
            ticker = item['ticker']
            date_str = item['date_str']
            days = item['days_until']

            domain = get_company_domain(ticker)
            color = get_ticker_color(ticker)
            first_letter = ticker[0]

            # HIGH QUALITY LOGOS - Google favicons (most reliable, high quality)
            # Much higher resolution (sz=256) then downscale for crisp rendering
            logo_html = f'''<img
                src="https://www.google.com/s2/favicons?domain={domain}&sz=256"
                style="width:36px;height:36px;border-radius:6px;background:white;padding:3px;box-shadow:0 2px 4px rgba(0,0,0,0.3);margin-right:10px;vertical-align:middle;object-fit:contain;"
                onerror="this.outerHTML='<span style=\\'display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;background:linear-gradient(135deg,{color} 0%,{color}dd 100%);color:white;border-radius:6px;margin-right:10px;font-weight:700;font-size:16px;vertical-align:middle;box-shadow:0 2px 4px rgba(0,0,0,0.3);border:2px solid rgba(255,255,255,0.2);\\'>{first_letter}</span>';"
            />'''

            ticker_items.append(f'{logo_html}<strong style="font-size:18px;font-weight:600;">{ticker}</strong> <span style="font-size:17px;opacity:0.9;">{date_str} • {days}d</span>')

        # Duplicate for seamless loop
        all_items = " | ".join(ticker_items) * 3

        # Complete HTML with inline styles - BIGGER, FULL-BLEED, CRYSTAL CLEAR
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            html, body {{
                width: 100%;
                overflow: hidden;
            }}
            .earnings-ticker {{
                background: #000000;
                color: white;
                padding: 22px 0;
                overflow: hidden;
                width: 100vw;
                position: relative;
                left: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
                box-shadow: 0 6px 12px rgba(0,0,0,0.5);
                border-bottom: 2px solid #1a1a1a;
            }}
            .ticker-content {{
                display: inline-block;
                white-space: nowrap;
                animation: scroll 200s linear infinite;
                padding-left: 100%;
                font-size: 18px;
                font-weight: 500;
                letter-spacing: 0.5px;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }}
            @keyframes scroll {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(-50%); }}
            }}
        </style>
        </head>
        <body>
            <div class="earnings-ticker">
                <div class="ticker-content">
                    📅 UPCOMING EARNINGS: {all_items}
                </div>
            </div>
        </body>
        </html>
        """

        return html

    except Exception as e:
        print(f"Ticker error: {e}")
        return None

# Build earnings ticker with AUTONOMOUS RESEARCH and inject via st.markdown for edge-to-edge
# DISABLED FOR TESTING - Uncomment to re-enable
# try:
#     client = YFinanceClient()
#
#     # Full 250+ ticker list (AUTONOMOUS RESEARCH)
#     tickers = [
#         "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ORCL",
#         "AMD", "INTC", "CSCO", "ADBE", "CRM", "SNOW", "SHOP", "SPOT", "UBER",
#         "PLTR", "RBLX", "U", "DDOG", "NET", "CRWD", "ZS", "OKTA", "MDB", "TWLO",
#         "NOW", "WDAY", "TEAM", "ZM", "DOCU", "MNDY", "PATH", "S", "BILL", "GTLB",
#         "HUBS", "VEEV", "ESTC", "CFLT", "ASAN", "PD", "IOT",
#         "QCOM", "TXN", "MU", "AMAT", "LRCX", "KLAC", "MRVL", "NXPI", "MCHP", "ON",
#         "ADI", "MPWR", "SWKS", "QRVO", "ALGM",
#         "NFLX", "MTCH", "PINS", "SNAP", "LYFT", "DASH", "ABNB",
#         "WMT", "TGT", "COST", "HD", "LOW", "DG", "DLTR", "BBY", "BURL", "ROST",
#         "TJX", "M", "KSS", "DKS", "BBWI", "ANF", "AEO", "URBN", "ETSY", "W", "CHWY", "RH",
#         "NKE", "LULU", "SBUX", "MCD", "YUM", "CMG", "QSR", "WEN", "JACK", "PZZA",
#         "DPZ", "DRI", "BLMN", "TXRH", "WING", "SHAK", "CAKE",
#         "DIS", "FOXA", "FOX", "LYV", "IMAX",
#         "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "USB", "PNC",
#         "TFC", "COF", "BK", "STT", "NTRS", "CFG", "KEY", "RF", "FITB", "HBAN",
#         "V", "MA", "PYPL", "AXP", "AFRM", "COIN", "SOFI", "UPST", "LC", "NU", "MELI", "STNE", "PAGS",
#         "PGR", "CB", "TRV", "ALL", "AIG", "MET", "PRU", "AFL", "HIG",
#         "JNJ", "PFE", "ABBV", "LLY", "MRK", "BMY", "AMGN", "GILD", "BIIB", "VRTX",
#         "REGN", "ISRG", "MRNA", "EXAS", "IONS", "ALNY", "INCY", "CRSP", "VCYT", "TDOC",
#         "UNH", "CVS", "CI", "ELV", "HUM", "CNC", "MOH", "HCA", "THC", "UHS",
#         "BA", "CAT", "DE", "GE", "HON", "UPS", "FDX", "LMT", "RTX", "NOC",
#         "GD", "LHX", "TDG", "ETN", "EMR", "ITW", "PH", "ROK", "DOV", "XYL",
#         "TSLA", "F", "GM", "RIVN", "LCID",
#         "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "DVN", "FANG", "OXY", "APA", "HAL", "BKR", "NOV",
#         "T", "VZ", "TMUS", "CMCSA", "CHTR", "LUMN",
#         "PG", "KO", "PEP", "CL", "KMB", "CHD", "CLX", "EL", "TAP", "STZ", "CELH", "KDP", "KHC", "GIS", "CPB",
#         "LIN", "APD", "ECL", "SHW", "DD", "DOW", "PPG", "NEM", "FCX", "GOLD",
#         "AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "SPG", "O", "WELL", "AVB",
#         "ROKU", "FVRR", "UPWK", "ZG", "OPEN", "HOOD", "DKNG", "PENN", "MGM", "WYNN", "LVS", "CZR",
#         "BKNG", "EXPE", "TRIP", "MAR", "HLT",
#         "IBM", "HPQ", "NTAP", "WDC", "STX", "PSTG", "SMCI", "DELL", "HPE",
#         "ULTA", "ELF", "COTY", "TPR", "CPRI", "RL", "PVH", "VFC", "UAA",
#     ]
#
#     earnings_calendar = client.get_earnings_calendar(tickers)
#
#     if earnings_calendar:
#         upcoming_earnings = [item for item in earnings_calendar if item['days_until'] >= 0 and item['days_until'] <= 90]
#
#         if upcoming_earnings:
#             upcoming_earnings = sorted(upcoming_earnings, key=lambda x: x['days_until'])[:50]
#
#             ticker_items = []
#             for item in upcoming_earnings:
#                 ticker = item['ticker']
#                 date_str = item['date_str']
#                 days = item['days_until']
#                 domain = get_company_domain(ticker)
#                 color = get_ticker_color(ticker)
#                 first_letter = ticker[0]
#
#                 # Logo with fallback badge
#                 logo = f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz=256" style="width:42px;height:42px;border-radius:6px;background:white;padding:4px;box-shadow:0 2px 6px rgba(0,0,0,0.4);margin-right:12px;vertical-align:middle;object-fit:contain;" onerror="this.outerHTML=\'<span style=&quot;display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;background:linear-gradient(135deg,{color},{color}dd);color:white;border-radius:6px;margin-right:12px;font-weight:700;font-size:18px;vertical-align:middle;box-shadow:0 2px 6px rgba(0,0,0,0.4);border:2px solid rgba(255,255,255,0.2);&#39;>{first_letter}</span>\';" />'
#
#                 ticker_items.append(f'{logo}<strong style="font-size:20px;font-weight:600;">{ticker}</strong> <span style="font-size:19px;opacity:0.9;">{date_str} • {days}d</span>')
#
#             all_items = " | ".join(ticker_items) * 3
#
#             # Inject with edge-to-edge CSS - BIGGER and FASTER
#             st.markdown(f"""
#             <style>
#                 .main .block-container {{
#                     padding-top: 0rem !important;
#                 }}
#                 .ticker-wrapper {{
#                     width: 100vw;
#                     position: relative;
#                     left: 50%;
#                     right: 50%;
#                     margin-left: -50vw;
#                     margin-right: -50vw;
#                     margin-top: -1rem;
#                     margin-bottom: 2rem;
#                 }}
#                 @keyframes scroll {{
#                     0% {{ transform: translateX(0); }}
#                     100% {{ transform: translateX(-50%); }}
#                 }}
#             </style>
#             <div class="ticker-wrapper">
#                 <div style="background:#000;color:white;padding:28px 0;overflow:hidden;width:100%;box-shadow:0 8px 16px rgba(0,0,0,0.6);border-bottom:3px solid #1a1a1a;">
#                     <div style="display:inline-block;white-space:nowrap;animation:scroll 100s linear infinite;padding-left:100%;font-size:20px;font-weight:500;letter-spacing:0.5px;-webkit-font-smoothing:antialiased;">
#                         📅 UPCOMING EARNINGS: {all_items}
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)
#
# except Exception as e:
#     print(f"Ticker error: {e}")

# ============================================================================
# HELPER FUNCTIONS (must be defined before page functions use them)
# ============================================================================

def show_loading_screen(overall_progress, current_step, step_progress, step_details, steps_status):
    """Display loading screen with dual progress bars using native Streamlit components."""

    # Title
    st.title(f"🎯 Analyzing {st.session_state.ticker}...")

    st.markdown("---")

    # Overall progress
    st.subheader("Overall Progress")
    st.progress(overall_progress / 100)
    st.write(f"**{overall_progress}%** complete")

    st.markdown("---")

    # Current steps
    st.subheader("Current Steps")

    for i, (step_name, status) in enumerate(steps_status.items(), 1):
        if status == "complete":
            icon = "✅"
        elif status == "in_progress":
            icon = "🔄"
        else:
            icon = "⏳"

        st.write(f"{icon} **{step_name}**")

        # Show progress bar for current step
        if status == "in_progress" and step_progress > 0:
            st.progress(step_progress / 100)
            if step_details:
                st.caption(f"{step_progress}% - {step_details}")


# ============================================================================
# PAGE FUNCTIONS
# ============================================================================

def show_home_page():
    """Page 1: Home - Ticker input and analyze button."""

    # Title and subtitle (only on home page)
    st.markdown('<h1 class="main-title">🎯 Options Strategy Bot</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Research & Strategy Recommendations</p>', unsafe_allow_html=True)

    # Earnings ticker at top (DISABLED FOR TESTING)
    # ticker_html_home = create_earnings_ticker()
    # if ticker_html_home:
    #     components.html(ticker_html_home, height=80, scrolling=False)

    # Welcome content
    st.markdown("""
    <div class="info-card">
        <h3 style="color: #1e293b; margin-bottom: 1rem;">👋 Welcome to the Options Strategy Bot</h3>
        <p style="color: #64748b; font-size: 1.1rem; line-height: 1.6;">
            This bot autonomously researches stocks and recommends options strategies.
            It reads articles, analyzes fundamentals, evaluates risks, and selects
            the optimal strategy for you.
        </p>
        <p style="color: #64748b; margin-top: 1rem;">
            <strong>Get started:</strong> Enter a ticker below and click "Analyze Stock"
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Research</div>
            <div class="metric-value">15-20</div>
            <div style="color: #64748b; font-size: 0.875rem; margin-top: 0.5rem;">Questions Asked</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Articles</div>
            <div class="metric-value">40-100</div>
            <div style="color: #64748b; font-size: 0.875rem; margin-top: 0.5rem;">Web Articles Read</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-label">Analysis</div>
            <div class="metric-value">30K+</div>
            <div style="color: #64748b; font-size: 0.875rem; margin-top: 0.5rem;">Words Analyzed</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Input form (centered)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🎯 Analyze a Stock")
        ticker_input = st.text_input(
            "Stock Ticker",
            value="NVDA",
            help="Enter a stock ticker to analyze",
            key="home_ticker"
        ).upper()

        enable_research = st.checkbox(
            "🔬 Enable Autonomous Research",
            value=True,
            help="Bot decides what to research and reads until satisfied",
            key="home_research"
        )

        if enable_research:
            st.info("🤖 Bot will generate its own questions and read until satisfied")
        else:
            st.warning("📋 Using hardcoded questions")

        analyze_clicked = st.button("🚀 Analyze Stock", type="primary", use_container_width=True)

        if analyze_clicked and ticker_input:
            # Save settings and switch to loading page
            st.session_state.ticker = ticker_input
            st.session_state.enable_research = enable_research
            st.session_state.current_page = "loading"
            st.rerun()

# ============================================================================
# SIDEBAR
# ============================================================================

def show_loading_page():
    """Page 2: Loading - Shows progress while analysis runs."""

    # Hide sidebar on loading page
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Show earnings ticker at top (DISABLED FOR TESTING)
    # ticker_html_loading = create_earnings_ticker()
    # if ticker_html_loading:
    #     components.html(ticker_html_loading, height=80, scrolling=False)

    # Get settings from session state
    ticker_input = st.session_state.ticker
    enable_research = st.session_state.enable_research
    articles_per_question = 2  # Default minimum for satisfaction check

    # Initialize progress tracking
    if 'progress' not in st.session_state:
        st.session_state.progress = {
            'overall': 0,
            'current_step': '',
            'step_progress': 0,
            'step_details': '',
            'steps_status': {
                'Fetching stock data': 'pending',
                'Generating investment thesis': 'pending',
                'Researching fundamentals': 'pending',
                'Selecting optimal strategy': 'pending',
                'Picking best contracts': 'pending',
                'Calculating risk/reward': 'pending'
            }
        }

    # Create placeholder for loading screen
    loading_placeholder = st.empty()

    # Initialize clients
    try:
        yfinance_client = YFinanceClient()
        thesis_generator = ThesisGeneratorV3(enable_research=enable_research)
        strategy_selector = StrategySelectV2(enable_research=enable_research)
        contract_picker = ContractPickerV2()
        pnl_calculator = PnLCalculator()
    except Exception as e:
        st.error(f"Initialization error: {e}")
        st.stop()

    # Phase 1: Fetch data
    with loading_placeholder.container():
        st.session_state.progress['overall'] = 5
        st.session_state.progress['steps_status']['Fetching stock data'] = 'in_progress'
        st.session_state.progress['step_progress'] = 0
        show_loading_screen(
            st.session_state.progress['overall'],
            'Fetching stock data',
            st.session_state.progress['step_progress'],
            '',
            st.session_state.progress['steps_status']
        )

    try:
        st.session_state.progress['step_progress'] = 30
        with loading_placeholder.container():
            show_loading_screen(5, 'Fetching stock data', 30, '(Getting stock info...)', st.session_state.progress['steps_status'])

        stock_data = yfinance_client.get_stock_data(ticker_input)
        news = yfinance_client.get_news(ticker_input, max_items=5)
        current_price = stock_data['current_price']

        st.session_state.progress['step_progress'] = 60
        with loading_placeholder.container():
            show_loading_screen(5, 'Fetching stock data', 60, '(Getting news...)', st.session_state.progress['steps_status'])

        try:
            historical_vol = yfinance_client.get_historical_volatility(ticker_input, days=30)
        except:
            historical_vol = 0.40

        st.session_state.progress['step_progress'] = 90
        with loading_placeholder.container():
            show_loading_screen(5, 'Fetching stock data', 90, '(Getting earnings...)', st.session_state.progress['steps_status'])

        try:
            earnings_info = yfinance_client.get_earnings_date(ticker_input)
            st.session_state.earnings_info = earnings_info
        except:
            st.session_state.earnings_info = None

        st.session_state.stock_data = stock_data

        # Complete phase 1
        st.session_state.progress['steps_status']['Fetching stock data'] = 'complete'
        st.session_state.progress['overall'] = 15
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        st.stop()

    # Phase 2: Generate thesis
    with loading_placeholder.container():
        st.session_state.progress['steps_status']['Generating investment thesis'] = 'in_progress'
        st.session_state.progress['step_progress'] = 0
        st.session_state.progress['overall'] = 20
        show_loading_screen(20, 'Generating investment thesis', 0, '(Starting...)', st.session_state.progress['steps_status'])

    try:
        st.session_state.progress['step_progress'] = 50
        with loading_placeholder.container():
            show_loading_screen(25, 'Generating investment thesis', 50, '(Analyzing...)', st.session_state.progress['steps_status'])

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

        # Complete phase 2
        st.session_state.progress['steps_status']['Generating investment thesis'] = 'complete'
        st.session_state.progress['overall'] = 40
    except Exception as e:
        st.error(f"Thesis generation failed: {e}")
        st.stop()

    # Phase 3: Select strategy
    with loading_placeholder.container():
        st.session_state.progress['steps_status']['Selecting optimal strategy'] = 'in_progress'
        st.session_state.progress['step_progress'] = 0
        st.session_state.progress['overall'] = 45
        show_loading_screen(45, 'Selecting optimal strategy', 0, '(Evaluating...)', st.session_state.progress['steps_status'])

    try:
        import re
        move_match = re.search(r'([+-]?\d+(?:\.\d+)?)', thesis.expected_move)
        expected_move_pct = float(move_match.group(1)) / 100 if move_match else 0.15

        timeframe_match = re.search(r'(\d+)', thesis.timeframe)
        timeframe_days = int(timeframe_match.group(1)) if timeframe_match else 30

        try:
            options_data = yfinance_client.get_options_chain(ticker_input)
            implied_vol = options_data.get('implied_volatility', historical_vol)
        except:
            implied_vol = historical_vol

        st.session_state.progress['step_progress'] = 50
        with loading_placeholder.container():
            show_loading_screen(50, 'Selecting optimal strategy', 50, '(Analyzing spreads...)', st.session_state.progress['steps_status'])

        strategy, research, earnings_strategy = strategy_selector.select_strategy_with_research(
            ticker=ticker_input,
            direction=thesis.direction,
            conviction=thesis.conviction,
            expected_move_pct=expected_move_pct,
            timeframe_days=timeframe_days,
            current_price=current_price,
            historical_vol=historical_vol,
            implied_vol=implied_vol,
            earnings_info=st.session_state.earnings_info,
            articles_per_question=articles_per_question
        )

        st.session_state.strategy = strategy
        st.session_state.earnings_strategy = earnings_strategy
        st.session_state.research = research

        # Complete phase 3
        st.session_state.progress['steps_status']['Selecting optimal strategy'] = 'complete'
        st.session_state.progress['overall'] = 65
    except Exception as e:
        st.error(f"Strategy selection failed: {e}")
        st.stop()

    # Phase 4: Pick contracts
    with loading_placeholder.container():
        st.session_state.progress['steps_status']['Picking best contracts'] = 'in_progress'
        st.session_state.progress['step_progress'] = 0
        st.session_state.progress['overall'] = 70
        show_loading_screen(70, 'Picking best contracts', 0, '(Finding optimal strikes...)', st.session_state.progress['steps_status'])

    try:
        options_chain = yfinance_client.get_options_chain_all_expirations(ticker_input, max_expirations=10)

        st.session_state.progress['step_progress'] = 50
        with loading_placeholder.container():
            show_loading_screen(75, 'Picking best contracts', 50, '(Analyzing options...)', st.session_state.progress['steps_status'])

        contracts, contract_insights = contract_picker.pick_contracts_with_research(
            ticker=ticker_input,
            strategy=strategy.strategy.value if hasattr(strategy.strategy, 'value') else strategy.strategy,
            direction=thesis.direction,
            current_price=current_price,
            expected_move_pct=expected_move_pct,
            timeframe_days=timeframe_days,
            options_chain=options_chain,
            research=research if enable_research else None
        )

        st.session_state.contracts = contracts

        # Complete phase 4
        st.session_state.progress['steps_status']['Picking best contracts'] = 'complete'
        st.session_state.progress['overall'] = 85
    except Exception as e:
        st.error(f"Contract selection failed: {e}")
        st.stop()

    # Phase 5: Calculate P/L
    with loading_placeholder.container():
        st.session_state.progress['steps_status']['Calculating risk/reward'] = 'in_progress'
        st.session_state.progress['step_progress'] = 0
        st.session_state.progress['overall'] = 90
        show_loading_screen(90, 'Calculating risk/reward', 0, '(Running scenarios...)', st.session_state.progress['steps_status'])

    try:
        st.session_state.progress['step_progress'] = 50
        with loading_placeholder.container():
            show_loading_screen(92, 'Calculating risk/reward', 50, '(Computing P&L...)', st.session_state.progress['steps_status'])

        pnl_analysis = pnl_calculator.calculate_complete_analysis(
            contracts=contracts,
            current_price=current_price,
            volatility=implied_vol,
            days_to_expiration=timeframe_days
        )

        st.session_state.pnl_analysis = pnl_analysis

        # Complete phase 5
        st.session_state.progress['steps_status']['Calculating risk/reward'] = 'complete'
        st.session_state.progress['overall'] = 100

        with loading_placeholder.container():
            show_loading_screen(100, 'Complete!', 100, '✅', st.session_state.progress['steps_status'])

        st.session_state.analysis_complete = True
        st.balloons()  # Celebration!

        # Switch to results page
        time.sleep(1)  # Brief pause to see completion
        st.session_state.current_page = "results"
        st.rerun()

    except Exception as e:
        st.error(f"P/L calculation failed: {e}")
        st.stop()


def show_results_page():
    """Page 3: Results - Shows complete analysis output."""

    # Hide sidebar on results page
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # Show earnings ticker at top (DISABLED FOR TESTING)
    # ticker_html_results = create_earnings_ticker()
    # if ticker_html_results:
    #     components.html(ticker_html_results, height=80, scrolling=False)

    # Get results from session state
    thesis = st.session_state.thesis
    strategy = st.session_state.strategy
    earnings_strategy = st.session_state.earnings_strategy
    contracts = st.session_state.contracts
    pnl_analysis = st.session_state.pnl_analysis
    stock_data = st.session_state.stock_data
    earnings_info = st.session_state.earnings_info
    research = st.session_state.research

    # "Analyze Another Stock" button at top
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🏠 Analyze Another Stock", type="primary", key="analyze_another_top"):
            # Reset state and go back to home
            st.session_state.analysis_complete = False
            st.session_state.current_page = "home"
            st.rerun()

    st.markdown("---")

    # Stock Context
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">📊 {st.session_state.ticker} Stock Overview</div>', unsafe_allow_html=True)

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

    if earnings_info:
        # Only show timing if we have it, otherwise "TBD" (yfinance timing often inaccurate)
        timing = earnings_info.get('timing')
        timing_str = f" ({timing})" if timing else " (TBD)"
        col6.metric(
            "Next Earnings",
            f"{earnings_info['date_str']}{timing_str}",
            delta=f"{earnings_info['days_until']} days"
        )
    else:
        col6.metric("Next Earnings", "N/A")

    st.markdown('</div>', unsafe_allow_html=True)

    # Investment Thesis
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🧠 Investment Thesis</div>', unsafe_allow_html=True)

    # Direction badge
    if thesis.direction == "BULLISH":
        st.markdown(f'<div class="thesis-bullish">🟢 BULLISH - {thesis.conviction}% Conviction</div>', unsafe_allow_html=True)
    elif thesis.direction == "BEARISH":
        st.markdown(f'<div class="thesis-bearish">🔴 BEARISH - {thesis.conviction}% Conviction</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="thesis-neutral">🔵 {thesis.direction} - {thesis.conviction}% Conviction</div>', unsafe_allow_html=True)

    st.markdown(f"**{thesis.thesis_summary}**")

    # Research Insights - Show what the bot learned
    if hasattr(thesis, 'research_insights') and thesis.research_insights:
        st.markdown("---")
        st.markdown("**🔍 Research Findings:**")
        st.markdown(thesis.research_insights)

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("📈 Bull Case", expanded=False):
            for point in thesis.bull_case:
                st.markdown(f"• {point}")

    with col2:
        with st.expander("📉 Bear Case", expanded=False):
            for point in thesis.bear_case:
                st.markdown(f"• {point}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Strategy Recommendation
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🎯 Recommended Strategy</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="strategy-box">
        <div class="strategy-name">{strategy.strategy.value}</div>
        <div style="margin-top: 0.5rem;">{strategy.rationale}</div>
    </div>
    """, unsafe_allow_html=True)

    # Research Summary - Why this strategy
    if hasattr(strategy, 'research_summary') and strategy.research_summary:
        st.markdown("**📊 Research Behind This Choice:**")
        st.markdown(strategy.research_summary)
        st.markdown("---")

    # Strategy Explanation - How it works
    if hasattr(strategy, 'how_it_works') and strategy.how_it_works:
        st.markdown("**📚 How This Strategy Works:**")
        st.markdown(strategy.how_it_works)
        st.markdown("---")

    # Risk/Reward Metrics
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
    st.markdown("**Profit/Loss Diagram:**")

    try:
        chart = create_pnl_chart(
            pnl_curve=pnl_analysis['pnl_curve'],
            current_price=stock_data['current_price'],
            max_profit=pnl_analysis['max_profit'],
            max_loss=pnl_analysis['max_loss'],
            max_profit_price=pnl_analysis.get('max_profit_price'),
            max_loss_price=pnl_analysis.get('max_loss_price'),
            breakevens=pnl_analysis['breakevens'],
            strategy_name=strategy.strategy.value
        )
        st.plotly_chart(chart, use_container_width=True)
    except Exception as e:
        st.error(f"Chart generation failed: {e}")

    # Selected Contracts
    with st.expander("📋 Selected Contracts", expanded=False):
        for i, contract in enumerate(contracts, 1):
            st.markdown(f"""
            **Contract {i}:** {contract.action} {contract.display_name}
            Strike: ${contract.strike:.2f} | Premium: ${contract.premium:.2f} | Delta: {contract.delta:.2f} | Exp: {contract.expiration}
            """)

    st.markdown('</div>', unsafe_allow_html=True)

    # Earnings Alternative (if exists)
    if earnings_strategy:
        st.markdown('<div class="info-card" style="border-left: 4px solid #f59e0b;">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📅 Earnings Alternative Strategy</div>', unsafe_allow_html=True)

        st.warning(f"**{earnings_strategy.strategy.value}** (Earnings Play)")
        st.info(earnings_strategy.rationale)

        st.markdown("""
        **Choose Based on Preference:**
        - **Primary Strategy** → Fundamental play based on research
        - **Earnings Alternative** → Volatility play based on earnings patterns
        """)

        st.markdown('</div>', unsafe_allow_html=True)

    # Research Summary (Collapsible)
    if research and research.total_questions > 0:
        with st.expander(f"🔬 Research Summary: {research.total_questions} questions, {research.total_articles} articles, {research.total_words:,} words"):
            if research.stock_research:
                st.markdown("**Stock Fundamentals:**")
                for q in research.stock_research.questions[:5]:
                    st.caption(f"• {q.question}")

            if research.earnings_research:
                st.markdown("**Earnings Patterns:**")
                for q in research.earnings_research.questions:
                    st.caption(f"• {q.question}")

    # "Analyze Another Stock" button at bottom too
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🏠 Back to Home", type="secondary", key="back_to_home_bottom"):
            st.session_state.analysis_complete = False
            st.session_state.current_page = "home"
            st.rerun()


# ============================================================================
# MAIN CONTENT - TRUE PAGE SEPARATION
# ============================================================================

# CRITICAL: Only render ONE page at a time
# The page routing ensures only the current page's function executes
if st.session_state.current_page == "home":
    show_home_page()
elif st.session_state.current_page == "loading":
    show_loading_page()
elif st.session_state.current_page == "results":
    show_results_page()

