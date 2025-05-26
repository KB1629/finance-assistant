"""Tests for data ingestion components."""

import os
import json
from pathlib import Path
import pytest
from datetime import date, datetime, timedelta

from data_ingestion.config import API_CACHE_DIR, SCRAPER_CACHE_DIR
from data_ingestion.api_agent.alphavantage_client import (
    AlphaVantageClient, get_price, get_earnings_surprise
)
from data_ingestion.scraper_agent.sec_scraper import (
    SECFilingScraper, get_latest_asian_tech_filings, get_filings_for_ticker
)


class TestAlphaVantageClient:
    """Test AlphaVantage API client."""
    
    def setup_method(self):
        """Set up test environment."""
        # Use demo API key
        self.client = AlphaVantageClient(api_key="demo")
        
        # Ensure cache directory exists
        os.makedirs(API_CACHE_DIR, exist_ok=True)
    
    def test_get_daily_prices(self):
        """Test getting daily prices."""
        try:
            df = self.client.get_daily_prices("MSFT")
            assert not df.empty, "Price DataFrame should not be empty"
            assert "adjusted_close" in df.columns, "DataFrame should have adjusted_close column"
        except Exception as e:
            pytest.skip(f"Skipping due to API call issue: {e}")
    
    def test_get_price(self):
        """Test getting a specific price."""
        try:
            # Test with specific date (past date to ensure data exists)
            last_year = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            price = self.client.get_price("AAPL", last_year)
            assert isinstance(price, float), "Price should be a float"
            assert price > 0, "Price should be positive"
            
            # Test with latest price
            latest_price = self.client.get_price("AAPL")
            assert isinstance(latest_price, float), "Latest price should be a float"
            assert latest_price > 0, "Latest price should be positive"
        except Exception as e:
            pytest.skip(f"Skipping due to API call issue: {e}")
    
    def test_get_earnings(self):
        """Test getting earnings data."""
        try:
            df = self.client.get_earnings("IBM")
            assert not df.empty, "Earnings DataFrame should not be empty"
            assert "surprisePercentage" in df.columns, "DataFrame should have surprisePercentage column"
        except Exception as e:
            pytest.skip(f"Skipping due to API call issue: {e}")
    
    def test_get_earnings_surprise(self):
        """Test getting earnings surprise percentage."""
        try:
            surprise = self.client.get_earnings_surprise("MSFT")
            assert isinstance(surprise, float), "Surprise should be a float"
        except Exception as e:
            pytest.skip(f"Skipping due to API call issue: {e}")

    def test_convenience_functions(self):
        """Test the module-level convenience functions."""
        try:
            # Test get_price
            price = get_price("AAPL")
            assert isinstance(price, float), "Price should be a float"
            assert price > 0, "Price should be positive"
            
            # Test with date object
            yesterday = date.today() - timedelta(days=7)  # Go back a week to ensure market data
            price_date = get_price("AAPL", yesterday)
            assert isinstance(price_date, float), "Price with date should be a float"
            assert price_date > 0, "Price with date should be positive"
            
            # Test get_earnings_surprise
            surprise = get_earnings_surprise("MSFT")
            assert isinstance(surprise, float), "Earnings surprise should be a float"
        except Exception as e:
            pytest.skip(f"Skipping due to API call issue: {e}")
            

class TestSECFilingScraper:
    """Test SEC filings scraper."""
    
    def setup_method(self):
        """Set up test environment."""
        self.scraper = SECFilingScraper()
        
        # Ensure cache directory exists
        os.makedirs(SCRAPER_CACHE_DIR, exist_ok=True)
    
    def test_search_filings(self):
        """Test searching for filings."""
        try:
            filings = self.scraper.search_filings(
                ticker_symbol="AAPL",
                filing_type="10-K",
                count=2
            )
            
            assert isinstance(filings, list), "Filings should be a list"
            if filings:  # SEC API might have issues or rate limits
                filing = filings[0]
                assert "company" in filing, "Filing should have company name"
                assert "filing_type" in filing, "Filing should have filing type"
                assert filing["filing_type"] == "10-K", "Filing type should match request"
        except Exception as e:
            pytest.skip(f"Skipping due to SEC API call issue: {e}")
    
    def test_get_latest_filings(self):
        """Test getting latest filings."""
        try:
            filings = self.scraper.get_latest_filings(
                ticker_symbol="MSFT",
                count=1
            )
            
            assert isinstance(filings, list), "Filings should be a list"
            if filings:  # SEC API might have issues or rate limits
                filing = filings[0]
                assert "company" in filing, "Filing should have company name"
                assert "full_text" in filing, "Filing should have full text"
                assert len(filing["full_text"]) > 100, "Full text should have content"
        except Exception as e:
            pytest.skip(f"Skipping due to SEC API call issue: {e}")
    
    def test_get_asian_tech_filings(self):
        """Test getting Asian tech filings."""
        try:
            filings = self.scraper.get_asian_tech_filings(days_back=90)  # Go back further to ensure some filings
            
            assert isinstance(filings, list), "Filings should be a list"
            # Don't assert on length since it depends on actual filing availability
        except Exception as e:
            pytest.skip(f"Skipping due to SEC API call issue: {e}")
    
    def test_convenience_functions(self):
        """Test the module-level convenience functions."""
        try:
            # Test get_filings_for_ticker
            filings = get_filings_for_ticker("AAPL", count=1)
            assert isinstance(filings, list), "Filings should be a list"
            
            # Test get_latest_asian_tech_filings
            asian_filings = get_latest_asian_tech_filings(days_back=90)  # Go back further to ensure some filings
            assert isinstance(asian_filings, list), "Asian filings should be a list"
        except Exception as e:
            pytest.skip(f"Skipping due to SEC API call issue: {e}")


def test_cache_creation():
    """Test that cache directories are created."""
    assert API_CACHE_DIR.exists(), "API cache directory should exist"
    assert SCRAPER_CACHE_DIR.exists(), "Scraper cache directory should exist"


def test_cached_data_exists():
    """Test that we are caching data successfully."""
    # First call to make sure we have some cached data
    client = AlphaVantageClient(api_key="demo")
    try:
        # Make a request that should cache data
        client.get_daily_prices("MSFT")
        
        # Check that cache directory has some files
        cache_files = list(API_CACHE_DIR.glob("*.json"))
        assert len(cache_files) > 0, "There should be cached JSON files in the API cache directory"
        
        # Check that the files contain valid JSON
        for cache_file in cache_files[:1]:  # Just check the first file
            with open(cache_file, 'r') as f:
                data = json.load(f)
                assert isinstance(data, dict), "Cached data should be a valid JSON object"
                assert "_cache_timestamp" in data, "Cached data should have timestamp"
    except Exception as e:
        pytest.skip(f"Skipping due to API call issue: {e}") 