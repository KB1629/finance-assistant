"""Portfolio analytics agent for financial analysis and insights."""

import os
import csv
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from data_ingestion.api_agent.alphavantage_client import get_price, get_earnings_surprise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("analytics.portfolio")

# Default paths
DEFAULT_PORTFOLIO_FILE = Path("./data/portfolio.csv")
DEFAULT_CACHE_DIR = Path("./cache/analytics")

class PortfolioAnalytics:
    """Portfolio analytics engine for financial analysis."""

    def __init__(
        self,
        portfolio_file: Optional[Path] = None,
        cache_dir: Optional[Path] = None
    ):
        """Initialize the portfolio analytics engine.
        
        Args:
            portfolio_file: Path to portfolio CSV file
            cache_dir: Directory to cache analytics results
        """
        self.portfolio_file = portfolio_file or DEFAULT_PORTFOLIO_FILE
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize portfolio data
        self.portfolio_df = None
        self.previous_data = None
        self.load_portfolio()
        
        # Cache file for daily analytics
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.cache_file = self.cache_dir / f"portfolio_analytics_{self.date_str}.json"
        
        # Load cached results if available
        self._load_cached_results()
    
    def load_portfolio(self) -> None:
        """Load portfolio data from CSV file."""
        
        # Try to read previous analysis for comparison
        yesterday_str = (datetime.now().date() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_cache = self.cache_dir / f"portfolio_analytics_{yesterday_str}.json"
        
        if yesterday_cache.exists():
            try:
                with open(yesterday_cache, 'r') as f:
                    self.previous_data = json.load(f)
                logger.info(f"Loaded previous analytics from {yesterday_str}")
            except Exception as e:
                logger.error(f"Error loading previous analytics: {e}")
                self.previous_data = None
        
        # Check if portfolio file exists
        if not self.portfolio_file.exists():
            # Create a sample portfolio if file doesn't exist
            logger.warning(f"Portfolio file {self.portfolio_file} not found, creating sample")
            self._create_sample_portfolio()
        
        try:
            # Load portfolio CSV
            self.portfolio_df = pd.read_csv(self.portfolio_file)
            
            # Validate required columns
            required_cols = ['symbol', 'shares']
            missing_cols = [col for col in required_cols if col not in self.portfolio_df.columns]
            
            if missing_cols:
                raise ValueError(f"Portfolio CSV missing required columns: {missing_cols}")
                
            # Add geo_tag column if missing
            if 'geo_tag' not in self.portfolio_df.columns:
                self.portfolio_df['geo_tag'] = 'Unclassified'
                
            logger.info(f"Loaded portfolio with {len(self.portfolio_df)} positions")
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            # Create sample portfolio as fallback
            self._create_sample_portfolio()
    
    def _create_sample_portfolio(self) -> None:
        """Create a sample portfolio for testing."""
        # Asian tech stocks
        asian_tech = [
            {"symbol": "TSM", "shares": 100, "geo_tag": "Asia-Tech"},
            {"symbol": "BABA", "shares": 50, "geo_tag": "Asia-Tech"},
            {"symbol": "BIDU", "shares": 30, "geo_tag": "Asia-Tech"},
            {"symbol": "SE", "shares": 40, "geo_tag": "Asia-Tech"},
        ]
        
        # US tech stocks
        us_tech = [
            {"symbol": "AAPL", "shares": 200, "geo_tag": "US-Tech"},
            {"symbol": "MSFT", "shares": 100, "geo_tag": "US-Tech"},
            {"symbol": "GOOGL", "shares": 20, "geo_tag": "US-Tech"},
            {"symbol": "AMZN", "shares": 30, "geo_tag": "US-Tech"},
        ]
        
        # Other sectors
        other = [
            {"symbol": "JPM", "shares": 50, "geo_tag": "US-Finance"},
            {"symbol": "XOM", "shares": 80, "geo_tag": "Energy"},
            {"symbol": "PG", "shares": 60, "geo_tag": "Consumer"},
            {"symbol": "JNJ", "shares": 40, "geo_tag": "Healthcare"},
        ]
        
        # Create DataFrame
        self.portfolio_df = pd.DataFrame(asian_tech + us_tech + other)
        
        # Save to CSV
        os.makedirs(self.portfolio_file.parent, exist_ok=True)
        self.portfolio_df.to_csv(self.portfolio_file, index=False)
        
        logger.info(f"Created sample portfolio with {len(self.portfolio_df)} positions")
    
    def _load_cached_results(self) -> None:
        """Load cached analytics results if available."""
        self.cached_results = None
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cached_results = json.load(f)
                logger.info(f"Loaded cached analytics from {self.date_str}")
            except Exception as e:
                logger.error(f"Error loading cached analytics: {e}")
    
    def _save_cached_results(self, results: Dict[str, Any]) -> None:
        """Save analytics results to cache.
        
        Args:
            results: Analytics results dictionary
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved analytics to {self.cache_file}")
        except Exception as e:
            logger.error(f"Error saving analytics: {e}")
    
    def get_portfolio_value(self) -> Dict[str, Any]:
        """Calculate current portfolio value and analytics.
        
        Returns:
            Dictionary with portfolio analytics
        """
        # Check for cached results
        if self.cached_results:
            logger.info("Using cached portfolio analytics")
            return self.cached_results
        
        if self.portfolio_df is None or self.portfolio_df.empty:
            logger.error("Portfolio is empty or not loaded")
            return {
                "error": "Portfolio data not available",
                "date": self.date_str
            }
        
        try:
            # Create copy of portfolio for analysis
            portfolio = self.portfolio_df.copy()
            
            # Get latest prices
            prices = {}
            for symbol in portfolio['symbol'].unique():
                try:
                    price = get_price(symbol)
                    prices[symbol] = price
                except Exception as e:
                    logger.error(f"Error getting price for {symbol}: {e}")
                    prices[symbol] = np.nan
            
            # Add price and market value columns
            portfolio['price'] = portfolio['symbol'].map(prices)
            portfolio['market_value'] = portfolio['shares'] * portfolio['price']
            
            # Filter out rows with NaN prices
            portfolio = portfolio.dropna(subset=['price'])
            
            if portfolio.empty:
                logger.error("No valid prices found for any symbols")
                return {
                    "error": "No valid prices available",
                    "date": self.date_str
                }
            
            # Calculate total portfolio value
            total_value = portfolio['market_value'].sum()
            
            # Group by geo_tag
            geo_analysis = portfolio.groupby('geo_tag').agg({
                'market_value': 'sum'
            }).reset_index()
            
            # Calculate percentage of total
            geo_analysis['percentage'] = (geo_analysis['market_value'] / total_value) * 100
            
            # Convert to dictionary
            geo_analysis_dict = geo_analysis.to_dict(orient='records')
            
            # Get Asia-Tech percentage
            asia_tech_pct = 0
            asia_tech_value = 0
            for item in geo_analysis_dict:
                if item['geo_tag'] == 'Asia-Tech':
                    asia_tech_pct = item['percentage']
                    asia_tech_value = item['market_value']
                    break
            
            # Compare with previous day if available
            asia_tech_change = None
            if self.previous_data and 'asia_tech' in self.previous_data:
                prev_pct = self.previous_data['asia_tech']['percentage']
                asia_tech_change = asia_tech_pct - prev_pct
            
            # Get earnings surprises
            earnings_surprises = []
            for symbol in portfolio['symbol'].unique():
                try:
                    surprise = get_earnings_surprise(symbol)
                    # Only include significant surprises (>1% absolute)
                    if abs(surprise) > 1.0:
                        earnings_surprises.append({
                            "symbol": symbol,
                            "surprise_percentage": surprise,
                            "type": "beat" if surprise > 0 else "miss"
                        })
                except Exception as e:
                    logger.debug(f"No earnings surprise for {symbol}: {e}")
            
            # Sort surprises by absolute magnitude
            earnings_surprises.sort(key=lambda x: abs(x['surprise_percentage']), reverse=True)
            
            # Prepare results
            results = {
                "date": self.date_str,
                "total_value": total_value,
                "positions_count": len(portfolio),
                "geo_allocation": geo_analysis_dict,
                "asia_tech": {
                    "percentage": asia_tech_pct,
                    "value": asia_tech_value,
                    "change_from_previous": asia_tech_change
                },
                "earnings_surprises": earnings_surprises
            }
            
            # Cache results
            self._save_cached_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating portfolio value: {e}")
            return {
                "error": str(e),
                "date": self.date_str
            }
    
    def get_risk_exposure(self, region: Optional[str] = None) -> Dict[str, Any]:
        """Get risk exposure analysis for the portfolio.
        
        Args:
            region: Optional filter by region/tag
            
        Returns:
            Dictionary with risk analysis
        """
        # First get portfolio value
        portfolio_data = self.get_portfolio_value()
        
        if "error" in portfolio_data:
            return portfolio_data
        
        try:
            # Filter geo allocation by region if specified
            geo_allocation = portfolio_data["geo_allocation"]
            
            if region:
                geo_allocation = [g for g in geo_allocation if g["geo_tag"] == region]
            
            # Get Asia tech allocation
            asia_tech = portfolio_data["asia_tech"]
            
            # Get earnings surprises
            earnings_surprises = portfolio_data["earnings_surprises"]
            
            # Prepare risk report
            risk_report = {
                "date": portfolio_data["date"],
                "exposures": geo_allocation,
                "asia_tech_exposure": asia_tech,
                "earnings_surprises": earnings_surprises
            }
            
            return risk_report
            
        except Exception as e:
            logger.error(f"Error calculating risk exposure: {e}")
            return {
                "error": str(e),
                "date": self.date_str
            }


# Module-level analytics instance for easy access
_portfolio_analytics = None

def get_portfolio_analytics() -> PortfolioAnalytics:
    """Get the global portfolio analytics instance.
    
    Returns:
        PortfolioAnalytics instance
    """
    global _portfolio_analytics
    if _portfolio_analytics is None:
        _portfolio_analytics = PortfolioAnalytics()
    return _portfolio_analytics

def get_portfolio_value() -> Dict[str, Any]:
    """Get current portfolio value and analytics.
    
    Returns:
        Dictionary with portfolio analytics
    """
    return get_portfolio_analytics().get_portfolio_value()

def get_risk_exposure(region: Optional[str] = None) -> Dict[str, Any]:
    """Get risk exposure analysis for the portfolio.
    
    Args:
        region: Optional filter by region/tag
        
    Returns:
        Dictionary with risk analysis
    """
    return get_portfolio_analytics().get_risk_exposure(region) 