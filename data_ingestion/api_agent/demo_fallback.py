"""
Demo Fallback Data for Alpha Vantage API
Provides realistic mock data when demo API key hits rate limits
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

logger = logging.getLogger("demo_fallback")

# Realistic stock prices (approximately current market levels)
DEMO_STOCK_PRICES = {
    # US Tech Giants
    "AAPL": 175.50,
    "MSFT": 420.30,
    "GOOGL": 140.25,
    "AMZN": 145.80,
    "META": 485.20,  # Meta (Facebook)
    "NVDA": 875.30,  # NVIDIA
    "NFLX": 485.60,  # Netflix
    "ADBE": 565.40,  # Adobe
    
    # Asian Tech
    "TSM": 102.45,   # Taiwan Semiconductor
    "BABA": 85.20,   # Alibaba
    "BIDU": 110.15,  # Baidu
    "SE": 45.30,     # Sea Limited
    "TCEHY": 38.75,  # Tencent (ADR)
    "JD": 28.90,     # JD.com
    "PDD": 125.40,   # PDD Holdings
    "ASML": 785.20,  # ASML (Netherlands)
    
    # Financial Services
    "JPM": 155.75,   # JPMorgan
    "BAC": 38.45,    # Bank of America
    "WFC": 52.30,    # Wells Fargo
    "GS": 385.60,    # Goldman Sachs
    "MS": 95.80,     # Morgan Stanley
    "V": 275.40,     # Visa
    "MA": 445.70,    # Mastercard
    
    # Energy & Commodities
    "XOM": 118.90,   # Exxon
    "CVX": 158.30,   # Chevron
    "COP": 112.45,   # ConocoPhillips
    "SLB": 45.20,    # Schlumberger
    
    # Consumer Goods
    "PG": 158.20,    # Procter & Gamble
    "JNJ": 162.40,   # Johnson & Johnson
    "KO": 62.15,     # Coca-Cola
    "PEP": 175.80,   # PepsiCo
    "WMT": 165.30,   # Walmart
    "HD": 385.90,    # Home Depot
    
    # Healthcare & Pharma
    "UNH": 525.40,   # UnitedHealth
    "PFE": 28.75,    # Pfizer
    "ABBV": 175.60,  # AbbVie
    "MRK": 125.30,   # Merck
    "TMO": 545.20,   # Thermo Fisher
    
    # European Stocks
    "ASML": 785.20,  # ASML (Netherlands)
    "SAP": 185.40,   # SAP (Germany)
    "NESN": 108.50,  # Nestle (Switzerland)
    
    # Indian Market (Popular stocks)
    "RELIANCE.BSE": 2850.75,  # Reliance Industries
    "TCS.BSE": 3950.20,       # Tata Consultancy Services
    "INFY.BSE": 1785.40,      # Infosys
    "HDFCBANK.BSE": 1685.30,  # HDFC Bank
    "ITC.BSE": 485.60,        # ITC Limited
    "WIPRO.BSE": 565.80,      # Wipro
    "BHARTIARTL.BSE": 1245.90, # Bharti Airtel
}

# Realistic earnings surprise data
DEMO_EARNINGS_SURPRISES = {
    # US Tech Giants
    "AAPL": 2.1,    # Beat by 2.1%
    "MSFT": 1.8,    # Beat by 1.8%
    "GOOGL": -0.5,  # Missed by 0.5%
    "AMZN": 3.2,    # Beat by 3.2%
    "META": 5.4,    # Beat by 5.4%
    "NVDA": 8.2,    # Beat by 8.2% (AI boom)
    "NFLX": -1.8,   # Missed by 1.8%
    "ADBE": 2.3,    # Beat by 2.3%
    
    # Asian Tech
    "TSM": 4.1,     # Beat by 4.1% (strong performance)
    "BABA": -1.2,   # Missed by 1.2%
    "BIDU": -2.1,   # Missed by 2.1%
    "SE": 0.8,      # Beat by 0.8%
    "TCEHY": -0.9,  # Missed by 0.9%
    "JD": 1.2,      # Beat by 1.2%
    "PDD": 6.5,     # Beat by 6.5%
    "ASML": 3.8,    # Beat by 3.8%
    
    # Financial Services
    "JPM": 1.5,     # Beat by 1.5%
    "BAC": 0.8,     # Beat by 0.8%
    "WFC": -0.3,    # Missed by 0.3%
    "GS": 2.1,      # Beat by 2.1%
    "MS": 1.4,      # Beat by 1.4%
    "V": 2.8,       # Beat by 2.8%
    "MA": 3.1,      # Beat by 3.1%
    
    # Energy & Commodities
    "XOM": 2.8,     # Beat by 2.8%
    "CVX": 1.9,     # Beat by 1.9%
    "COP": 3.4,     # Beat by 3.4%
    "SLB": 0.6,     # Beat by 0.6%
    
    # Consumer Goods
    "PG": 0.3,      # Beat by 0.3%
    "JNJ": -0.8,    # Missed by 0.8%
    "KO": 1.1,      # Beat by 1.1%
    "PEP": 0.9,     # Beat by 0.9%
    "WMT": 2.2,     # Beat by 2.2%
    "HD": 1.7,      # Beat by 1.7%
    
    # Healthcare & Pharma
    "UNH": 3.5,     # Beat by 3.5%
    "PFE": -2.1,    # Missed by 2.1%
    "ABBV": 1.8,    # Beat by 1.8%
    "MRK": 0.7,     # Beat by 0.7%
    "TMO": 2.4,     # Beat by 2.4%
    
    # European Stocks
    "SAP": 1.3,     # Beat by 1.3%
    "NESN": 0.5,    # Beat by 0.5%
    
    # Indian Market
    "RELIANCE.BSE": 2.8,    # Beat by 2.8%
    "TCS.BSE": 1.9,         # Beat by 1.9%
    "INFY.BSE": 1.2,        # Beat by 1.2%
    "HDFCBANK.BSE": 0.8,    # Beat by 0.8%
    "ITC.BSE": -0.5,        # Missed by 0.5%
    "WIPRO.BSE": 0.3,       # Beat by 0.3%
    "BHARTIARTL.BSE": 1.6,  # Beat by 1.6%
}

def get_demo_price(symbol: str, add_volatility: bool = True) -> float:
    """Get demo price with optional volatility simulation.
    
    Args:
        symbol: Stock symbol
        add_volatility: Whether to add random price variation
        
    Returns:
        Simulated stock price
    """
    base_price = DEMO_STOCK_PRICES.get(symbol.upper(), 100.0)
    
    if add_volatility:
        # Add realistic daily volatility (±2%)
        volatility = random.uniform(-0.02, 0.02)
        return round(base_price * (1 + volatility), 2)
    
    return base_price

def get_demo_earnings_surprise(symbol: str) -> float:
    """Get demo earnings surprise data.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Earnings surprise percentage
    """
    return DEMO_EARNINGS_SURPRISES.get(symbol.upper(), 0.0)

def create_demo_time_series_response(symbol: str) -> Dict[str, Any]:
    """Create a realistic Alpha Vantage time series response for demo purposes.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Mock API response in Alpha Vantage format
    """
    base_price = DEMO_STOCK_PRICES.get(symbol.upper(), 100.0)
    
    # Generate 30 days of mock data
    time_series = {}
    current_date = datetime.now()
    current_price = base_price
    
    for i in range(30):
        date_str = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Simulate realistic price movement
        daily_change = random.uniform(-0.03, 0.03)  # ±3% daily change
        current_price = max(current_price * (1 + daily_change), 1.0)  # Prevent negative prices
        
        # Create OHLCV data
        open_price = current_price * random.uniform(0.99, 1.01)
        high_price = max(open_price, current_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, current_price) * random.uniform(0.98, 1.0)
        volume = random.randint(1000000, 50000000)
        
        time_series[date_str] = {
            "1. open": f"{open_price:.2f}",
            "2. high": f"{high_price:.2f}",
            "3. low": f"{low_price:.2f}",
            "4. close": f"{current_price:.2f}",
            "5. adjusted close": f"{current_price:.2f}",
            "6. volume": str(volume),
            "7. dividend amount": "0.0000",
            "8. split coefficient": "1.0"
        }
    
    return {
        "Meta Data": {
            "1. Information": "Daily Prices (Demo Data)",
            "2. Symbol": symbol.upper(),
            "3. Last Refreshed": datetime.now().strftime('%Y-%m-%d'),
            "4. Output Size": "Compact",
            "5. Time Zone": "US/Eastern"
        },
        "Time Series (Daily)": time_series,
        "_cache_timestamp": datetime.now().timestamp(),
        "_demo_data": True
    }

def create_demo_earnings_response(symbol: str) -> Dict[str, Any]:
    """Create a realistic Alpha Vantage earnings response for demo purposes.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Mock API response in Alpha Vantage format
    """
    surprise_pct = get_demo_earnings_surprise(symbol)
    
    # Generate quarterly earnings data
    quarterly_earnings = []
    current_date = datetime.now()
    
    for i in range(4):  # Last 4 quarters
        quarter_end = current_date - timedelta(days=90 * i)
        reported_date = quarter_end + timedelta(days=15)  # Usually report ~2 weeks after quarter end
        
        # Simulate realistic earnings
        estimated_eps = random.uniform(1.0, 5.0)
        actual_eps = estimated_eps * (1 + surprise_pct / 100)
        surprise = actual_eps - estimated_eps
        
        quarterly_earnings.append({
            "fiscalDateEnding": quarter_end.strftime('%Y-%m-%d'),
            "reportedDate": reported_date.strftime('%Y-%m-%d'),
            "reportedEPS": f"{actual_eps:.2f}",
            "estimatedEPS": f"{estimated_eps:.2f}",
            "surprise": f"{surprise:.2f}",
            "surprisePercentage": f"{surprise_pct:.1f}"
        })
    
    return {
        "symbol": symbol.upper(),
        "quarterlyEarnings": quarterly_earnings,
        "_cache_timestamp": datetime.now().timestamp(),
        "_demo_data": True
    }

def is_demo_api_key(api_key: str) -> bool:
    """Check if the API key is the demo key.
    
    Args:
        api_key: API key to check
        
    Returns:
        True if demo key
    """
    return api_key in ["demo", "DEMO", None, ""]

def should_use_fallback(error_message: str) -> bool:
    """Determine if we should use fallback data based on error message.
    
    Args:
        error_message: Error message from API
        
    Returns:
        True if fallback should be used
    """
    fallback_indicators = [
        "No daily data available",
        "rate limit",
        "API call frequency",
        "premium feature",
        "Thank you for using Alpha Vantage",
        "premium endpoint",
        "Error Message",
        "demo API key is for demo purposes only",
        "claim your free API key",
        "demo purposes only"
    ]
    
    return any(indicator.lower() in error_message.lower() for indicator in fallback_indicators)

def should_use_fallback_for_response(data: dict) -> bool:
    """Determine if we should use fallback data based on API response structure.
    
    Args:
        data: API response dictionary
        
    Returns:
        True if fallback should be used
    """
    # Check for demo API key message
    if "Information" in data and "demo" in data["Information"].lower():
        return True
    
    # Check for rate limit or error messages
    if "Note" in data:
        return should_use_fallback(data["Note"])
    
    if "Error Message" in data:
        return should_use_fallback(data["Error Message"])
    
    # Check if expected data structure is missing
    if "Time Series (Daily)" not in data and "quarterlyEarnings" not in data:
        return True
    
    return False 