"""AlphaVantage API client for retrieving financial data."""

import os
import json
import time
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Union
import requests
import pandas as pd
from pathlib import Path
import logging

from data_ingestion.config import ALPHAVANTAGE_API_KEY, API_CACHE_DIR
from data_ingestion.api_agent.demo_fallback import (
    create_demo_time_series_response,
    create_demo_earnings_response,
    is_demo_api_key,
    should_use_fallback,
    should_use_fallback_for_response
)

logger = logging.getLogger("alphavantage_client")


class AlphaVantageClient:
    """Client for AlphaVantage API to fetch stock data, earnings, and other financial information."""

    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """Initialize AlphaVantage client with API key and cache directory.

        Args:
            api_key: AlphaVantage API key
            cache_dir: Directory to cache API responses
        """
        self.api_key = api_key or ALPHAVANTAGE_API_KEY
        self.cache_dir = cache_dir or API_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, function: str, symbol: str, **params) -> Path:
        """Generate a cache file path based on function, symbol, and params.

        Args:
            function: AlphaVantage function name
            symbol: Stock symbol
            params: Additional parameters

        Returns:
            Path to cache file
        """
        param_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()) if k != "apikey")
        cache_file = f"{function}_{symbol}_{param_str}.json" if param_str else f"{function}_{symbol}.json"
        return self.cache_dir / cache_file

    def _fetch_data(self, function: str, symbol: str, **params) -> Dict[str, Any]:
        """Fetch data from AlphaVantage API or cache.

        Args:
            function: AlphaVantage function name
            symbol: Stock symbol
            params: Additional parameters

        Returns:
            API response as dictionary
        """
        cache_path = self._get_cache_path(function, symbol, **params)
        
        # Check cache first
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                # Check if cache is still fresh (less than 24h old)
                cache_time = cached_data.get("_cache_timestamp", 0)
                if time.time() - cache_time < 86400:  # 24 hours in seconds
                    return cached_data
        
        # For demo API key, use fallback data directly to prevent rate limit issues
        if is_demo_api_key(self.api_key):
            logger.info(f"Using demo API key - using fallback for {symbol} {function}")
            try:
                fallback_data = self._get_fallback_data(function, symbol)
                # Save to cache
                with open(cache_path, 'w') as f:
                    json.dump(fallback_data, f)
                return fallback_data
            except Exception as e:
                logger.warning(f"Fallback data failed: {e}")
        
        # Fetch fresh data from API
        request_params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            **params
        }
        
        try:
            response = requests.get(self.BASE_URL, params=request_params, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                if should_use_fallback(error_msg):
                    logger.warning(f"API failed, using fallback: {error_msg}")
                    return self._get_fallback_data(function, symbol)
                raise Exception(error_msg)
            
            data = response.json()
            
            # Check for API error messages or rate limits
            if "Error Message" in data or "Note" in data:
                error_msg = data.get("Error Message", data.get("Note", "Unknown API error"))
                if should_use_fallback(error_msg):
                    logger.warning(f"API error, using fallback: {error_msg}")
                    return self._get_fallback_data(function, symbol)
                raise Exception(f"API Error: {error_msg}")
            
            # Check if response structure indicates we should use fallback
            if should_use_fallback_for_response(data):
                info_msg = data.get("Information", "API response missing expected data")
                logger.warning(f"API response incomplete, using fallback: {info_msg}")
                return self._get_fallback_data(function, symbol)
            
            # Add timestamp for cache freshness checking
            data["_cache_timestamp"] = time.time()
            
            # Save to cache
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            
            return data
            
        except (requests.RequestException, json.JSONDecodeError) as e:
            logger.warning(f"API request failed ({e}), using fallback data")
            return self._get_fallback_data(function, symbol)

    def _get_fallback_data(self, function: str, symbol: str) -> Dict[str, Any]:
        """Get fallback data when API is unavailable.
        
        Args:
            function: AlphaVantage function name
            symbol: Stock symbol
            
        Returns:
            Mock API response
        """
        if function == "TIME_SERIES_DAILY_ADJUSTED":
            return create_demo_time_series_response(symbol)
        elif function == "EARNINGS":
            return create_demo_earnings_response(symbol)
        else:
            raise Exception(f"No fallback data available for function: {function}")

    def get_daily_prices(self, symbol: str) -> pd.DataFrame:
        """Get daily adjusted price data for a symbol.

        Args:
            symbol: Stock symbol (e.g., AAPL, MSFT)

        Returns:
            DataFrame with date index and OHLCV columns
        """
        data = self._fetch_data(
            function="TIME_SERIES_DAILY_ADJUSTED",
            symbol=symbol,
            outputsize="compact"
        )
        
        # Parse time series data
        if "Time Series (Daily)" not in data:
            raise Exception(f"No daily data available for {symbol}")
            
        time_series = data["Time Series (Daily)"]
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient="index")
        
        # Convert columns and index
        df.index = pd.to_datetime(df.index)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
            
        # Rename columns for clarity
        df = df.rename(columns={
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. adjusted close": "adjusted_close",
            "6. volume": "volume",
            "7. dividend amount": "dividend",
            "8. split coefficient": "split_coefficient"
        })
        
        return df.sort_index()

    def get_price(self, symbol: str, date_str: Optional[str] = None) -> float:
        """Get closing price for a symbol on a specific date or latest.

        Args:
            symbol: Stock symbol
            date_str: Date string in format 'YYYY-MM-DD', None for latest price

        Returns:
            Adjusted closing price
        """
        prices_df = self.get_daily_prices(symbol)
        
        if date_str:
            target_date = pd.to_datetime(date_str)
            # Find exact date or closest preceding date
            valid_dates = prices_df.index[prices_df.index <= target_date]
            if len(valid_dates) == 0:
                raise ValueError(f"No price data available on or before {date_str}")
            price_date = valid_dates[-1]
        else:
            # Get most recent date
            price_date = prices_df.index[-1]
            
        return float(prices_df.loc[price_date, "adjusted_close"])

    def get_earnings(self, symbol: str) -> pd.DataFrame:
        """Get quarterly earnings data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            DataFrame with earnings data
        """
        data = self._fetch_data(function="EARNINGS", symbol=symbol)
        
        if "quarterlyEarnings" not in data:
            raise Exception(f"No earnings data available for {symbol}")
            
        quarterly_earnings = data["quarterlyEarnings"]
        
        # Convert to DataFrame
        df = pd.DataFrame(quarterly_earnings)
        
        # Convert columns
        df["reportedDate"] = pd.to_datetime(df["reportedDate"])
        df["fiscalDateEnding"] = pd.to_datetime(df["fiscalDateEnding"])
        
        for col in ["reportedEPS", "estimatedEPS", "surprise", "surprisePercentage"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
        return df.sort_values("reportedDate", ascending=False)

    def get_earnings_surprise(self, symbol: str, period: Optional[str] = None) -> float:
        """Get earnings surprise percentage for a symbol in the most recent quarter or specified period.

        Args:
            symbol: Stock symbol
            period: Optional quarter specification (e.g., '2023Q1', or an ISO date in the quarter)

        Returns:
            Earnings surprise percentage (positive = beat, negative = miss)
        """
        earnings_df = self.get_earnings(symbol)
        
        if earnings_df.empty:
            raise ValueError(f"No earnings data available for {symbol}")
        
        if period:
            if "Q" in period:  # Format like '2023Q1'
                year = int(period[:4])
                quarter = int(period[5])
                # Create date ranges for the quarters
                quarter_ranges = {
                    1: (f"{year}-01-01", f"{year}-03-31"),
                    2: (f"{year}-04-01", f"{year}-06-30"),
                    3: (f"{year}-07-01", f"{year}-09-30"),
                    4: (f"{year}-10-01", f"{year}-12-31")
                }
                if quarter not in quarter_ranges:
                    raise ValueError(f"Invalid quarter in period {period}")
                    
                start_date, end_date = quarter_ranges[quarter]
                mask = (earnings_df["fiscalDateEnding"] >= pd.to_datetime(start_date)) & \
                       (earnings_df["fiscalDateEnding"] <= pd.to_datetime(end_date))
                filtered_df = earnings_df[mask]
            else:  # Assume ISO date format
                target_date = pd.to_datetime(period)
                # Get entries from the quarter of the target date
                quarter_start = pd.Timestamp(target_date.year, ((target_date.month - 1) // 3) * 3 + 1, 1)
                quarter_end = pd.Timestamp(quarter_start.year + (quarter_start.month + 2) // 12,
                                          ((quarter_start.month + 2) % 12) + 1,
                                          1) - pd.Timedelta(days=1)
                mask = (earnings_df["fiscalDateEnding"] >= quarter_start) & \
                       (earnings_df["fiscalDateEnding"] <= quarter_end)
                filtered_df = earnings_df[mask]
                
            if filtered_df.empty:
                raise ValueError(f"No earnings data found for period {period}")
            latest_earnings = filtered_df.iloc[0]
        else:
            # Get most recent earnings
            latest_earnings = earnings_df.iloc[0]
            
        return float(latest_earnings["surprisePercentage"])


# Module-level client instance for easy access
client = AlphaVantageClient()

# Convenience functions
def get_price(symbol: str, date_obj: Optional[Union[date, str]] = None) -> float:
    """Get stock price for a symbol on a specific date.
    
    Args:
        symbol: Stock symbol
        date_obj: Date object or string in 'YYYY-MM-DD' format, None for latest
        
    Returns:
        Adjusted closing price
    """
    date_str = date_obj.isoformat() if isinstance(date_obj, date) else date_obj
    return client.get_price(symbol, date_str)

def get_earnings_surprise(symbol: str, period: Optional[str] = None) -> float:
    """Get earnings surprise percentage.
    
    Args:
        symbol: Stock symbol
        period: Quarter specification (e.g., '2023Q1') or None for most recent
        
    Returns:
        Earnings surprise percentage
    """
    return client.get_earnings_surprise(symbol, period) 