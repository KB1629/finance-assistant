"""Tests for analytics agent."""

import os
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from agents.analytics.portfolio import (
    PortfolioAnalytics, get_portfolio_value, get_risk_exposure
)


class TestPortfolioAnalytics:
    """Test portfolio analytics functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Use a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.portfolio_dir = Path(self.temp_dir) / "portfolio"
        self.cache_dir = Path(self.temp_dir) / "cache"
        os.makedirs(self.portfolio_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create a test portfolio file
        self.portfolio_file = self.portfolio_dir / "portfolio.csv"
        
        # Create a simple portfolio
        self.portfolio_data = [
            {"symbol": "AAPL", "shares": 100, "geo_tag": "US-Tech"},
            {"symbol": "TSM", "shares": 50, "geo_tag": "Asia-Tech"},
            {"symbol": "BABA", "shares": 25, "geo_tag": "Asia-Tech"},
            {"symbol": "XOM", "shares": 75, "geo_tag": "Energy"}
        ]
        
        # Save to CSV
        pd.DataFrame(self.portfolio_data).to_csv(self.portfolio_file, index=False)
        
        # Mock prices for testing
        self.mock_prices = {
            "AAPL": 150.0,
            "TSM": 100.0,
            "BABA": 80.0,
            "XOM": 60.0
        }
        
        # Mock earnings surprises
        self.mock_earnings = {
            "AAPL": 0.5,
            "TSM": 4.2,
            "BABA": -2.1,
            "XOM": 0.3
        }
    
    def teardown_method(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    @patch("agents.analytics.portfolio.get_price")
    @patch("agents.analytics.portfolio.get_earnings_surprise")
    def test_get_portfolio_value(self, mock_earnings, mock_price):
        """Test getting portfolio value."""
        # Configure mocks
        mock_price.side_effect = lambda symbol: self.mock_prices.get(symbol, 0)
        mock_earnings.side_effect = lambda symbol: self.mock_earnings.get(symbol, 0)
        
        # Initialize analytics
        analytics = PortfolioAnalytics(
            portfolio_file=self.portfolio_file,
            cache_dir=self.cache_dir
        )
        
        # Get portfolio value
        result = analytics.get_portfolio_value()
        
        # Verify the result structure
        assert "date" in result
        assert "total_value" in result
        assert "positions_count" in result
        assert "geo_allocation" in result
        assert "asia_tech" in result
        assert "earnings_surprises" in result
        
        # Check total value calculation (100*150 + 50*100 + 25*80 + 75*60 = 26500)
        assert result["total_value"] == 26500.0
        
        # Check positions count
        assert result["positions_count"] == 4
        
        # Check geo allocation
        geo = {item["geo_tag"]: item["percentage"] for item in result["geo_allocation"]}
        assert "US-Tech" in geo
        assert "Asia-Tech" in geo
        assert "Energy" in geo
        
        # Check Asia-Tech percentage (50*100 + 25*80 = 7000, 7000/26500*100 ≈ 26.42%)
        assert round(result["asia_tech"]["percentage"], 2) == round(7000 / 26500 * 100, 2)
        
        # Check earnings surprises
        surprises = {item["symbol"]: item["surprise_percentage"] for item in result["earnings_surprises"]}
        assert "TSM" in surprises
        assert surprises["TSM"] == 4.2
        assert "BABA" in surprises
        assert surprises["BABA"] == -2.1
        
        # Verify cache was created
        assert os.path.exists(analytics.cache_file)
    
    @patch("agents.analytics.portfolio.get_price")
    @patch("agents.analytics.portfolio.get_earnings_surprise")
    def test_risk_exposure(self, mock_earnings, mock_price):
        """Test getting risk exposure."""
        # Configure mocks
        mock_price.side_effect = lambda symbol: self.mock_prices.get(symbol, 0)
        mock_earnings.side_effect = lambda symbol: self.mock_earnings.get(symbol, 0)
        
        # Initialize analytics
        analytics = PortfolioAnalytics(
            portfolio_file=self.portfolio_file,
            cache_dir=self.cache_dir
        )
        
        # Get risk exposure
        result = analytics.get_risk_exposure()
        
        # Verify the result structure
        assert "date" in result
        assert "exposures" in result
        assert "asia_tech_exposure" in result
        assert "earnings_surprises" in result
        
        # Check filtering by region
        asia_result = analytics.get_risk_exposure("Asia-Tech")
        assert len(asia_result["exposures"]) == 1
        assert asia_result["exposures"][0]["geo_tag"] == "Asia-Tech"
    
    def test_sample_portfolio_creation(self):
        """Test creating a sample portfolio."""
        # Use a non-existent file path
        non_existent = self.portfolio_dir / "non_existent.csv"
        
        # Initialize analytics with non-existent file
        analytics = PortfolioAnalytics(
            portfolio_file=non_existent,
            cache_dir=self.cache_dir
        )
        
        # Should create a sample portfolio
        assert analytics.portfolio_df is not None
        assert len(analytics.portfolio_df) > 0
        
        # Check that the file was created
        assert os.path.exists(non_existent)
    
    @patch("agents.analytics.portfolio.get_price")
    def test_cache_loading(self, mock_price):
        """Test loading results from cache."""
        # Configure mock
        mock_price.side_effect = lambda symbol: self.mock_prices.get(symbol, 0)
        
        # Create a cache file with mock results
        analytics = PortfolioAnalytics(
            portfolio_file=self.portfolio_file,
            cache_dir=self.cache_dir
        )
        
        mock_results = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_value": 10000.0,
            "positions_count": 3,
            "geo_allocation": [
                {"geo_tag": "Asia-Tech", "market_value": 5000.0, "percentage": 50.0}
            ],
            "asia_tech": {
                "percentage": 50.0,
                "value": 5000.0,
                "change_from_previous": 5.0
            },
            "earnings_surprises": [
                {"symbol": "TSM", "surprise_percentage": 3.0, "type": "beat"}
            ]
        }
        
        # Save to cache
        with open(analytics.cache_file, 'w') as f:
            json.dump(mock_results, f)
        
        # Load new instance that should use cache
        analytics2 = PortfolioAnalytics(
            portfolio_file=self.portfolio_file,
            cache_dir=self.cache_dir
        )
        
        # Get results (should use cache)
        result = analytics2.get_portfolio_value()
        
        # Should match the mock results
        assert result == mock_results
        assert result["total_value"] == 10000.0
        assert result["asia_tech"]["percentage"] == 50.0


# Test module-level convenience functions
@patch("agents.analytics.portfolio.get_portfolio_analytics")
def test_module_functions(mock_get_analytics):
    """Test module-level convenience functions."""
    # Create mock portfolio analytics
    mock_analytics = MagicMock()
    mock_analytics.get_portfolio_value.return_value = {"result": "portfolio_value"}
    mock_analytics.get_risk_exposure.return_value = {"result": "risk_exposure"}
    
    # Set up the mock to return our mock analytics
    mock_get_analytics.return_value = mock_analytics
    
    # Test get_portfolio_value
    result = get_portfolio_value()
    assert result == {"result": "portfolio_value"}
    
    # Test get_risk_exposure
    result = get_risk_exposure("Asia-Tech")
    assert result == {"result": "risk_exposure"}
    mock_analytics.get_risk_exposure.assert_called_with("Asia-Tech") 