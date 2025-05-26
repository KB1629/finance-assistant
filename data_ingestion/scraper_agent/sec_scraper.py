"""SEC filings scraper for retrieving and parsing financial documents."""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import requests
import pandas as pd
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

from data_ingestion.config import SCRAPER_CACHE_DIR, SEC_API_BASE_URL, USER_AGENT, REQUEST_DELAY_SEC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sec_scraper")


class SECFilingScraper:
    """Scraper for SEC EDGAR filings."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize SEC scraper with cache directory.
        
        Args:
            cache_dir: Directory to cache scraped SEC filings
        """
        self.cache_dir = cache_dir or SCRAPER_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Track last request time to respect rate limits
        self.last_request_time = 0
        
        # Headers for SEC requests (they require a user-agent)
        self.headers = {
            "User-Agent": USER_AGENT
        }

    def _respect_rate_limit(self):
        """Ensure requests are spaced out to respect SEC rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY_SEC:
            time.sleep(REQUEST_DELAY_SEC - elapsed)
        self.last_request_time = time.time()

    def _get_cache_path(self, filing_type: str, company_name: str, cik: str, filing_date: str, accession_number: Optional[str] = None) -> Path:
        """Generate a cache file path for a SEC filing.
        
        Args:
            filing_type: Filing type (e.g., '10-K', '10-Q')
            company_name: Company name
            cik: Company CIK number
            filing_date: Filing date (YYYY-MM-DD)
            accession_number: Filing accession number
            
        Returns:
            Path to cache file
        """
        # Clean company name to use as filename
        clean_name = "".join(c if c.isalnum() else "_" for c in company_name)
        
        if accession_number:
            filename = f"{clean_name}_{cik}_{filing_type}_{filing_date}_{accession_number}.json"
        else:
            filename = f"{clean_name}_{cik}_{filing_type}_{filing_date}.json"
            
        return self.cache_dir / filename

    def search_filings(
        self, 
        company_name: Optional[str] = None,
        ticker_symbol: Optional[str] = None,
        cik: Optional[str] = None,
        filing_type: Optional[str] = None,
        before_date: Optional[Union[str, datetime]] = None,
        after_date: Optional[Union[str, datetime]] = None,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for SEC filings matching criteria.
        
        Args:
            company_name: Company name
            ticker_symbol: Stock symbol
            cik: Company CIK number
            filing_type: Filing type (e.g., '10-K', '10-Q', '8-K')
            before_date: Only return filings before this date
            after_date: Only return filings after this date
            count: Maximum number of results to return
            
        Returns:
            List of filing metadata dictionaries
        """
        if not any([company_name, ticker_symbol, cik]):
            raise ValueError("Must provide at least one of: company_name, ticker_symbol, or cik")
            
        # Prepare search parameters
        params = {
            "action": "getcompany",
            "output": "atom",
            "count": str(count),
        }
        
        # Add optional parameters
        if company_name:
            params["company"] = company_name
        if ticker_symbol:
            params["ticker"] = ticker_symbol
        if cik:
            params["CIK"] = cik
        if filing_type:
            params["type"] = filing_type
            
        # Handle date filtering
        if before_date:
            if isinstance(before_date, str):
                before_date = datetime.strptime(before_date, "%Y-%m-%d")
            params["dateb"] = before_date.strftime("%Y%m%d")
            
        if after_date:
            if isinstance(after_date, str):
                after_date = datetime.strptime(after_date, "%Y-%m-%d")
            params["datea"] = after_date.strftime("%Y%m%d")
            
        # Respect rate limits
        self._respect_rate_limit()
        
        # Make request to SEC
        response = requests.get(SEC_API_BASE_URL, params=params, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"SEC API request failed with status {response.status_code}: {response.text}")
            
        # Parse XML response
        filings = []
        try:
            root = ET.fromstring(response.content)
            
            # Define XML namespaces
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "edgar": "http://www.sec.gov/Archives/edgar"
            }
            
            # Extract company info
            company_info = {
                "name": root.find(".//atom:company-name", ns).text if root.find(".//atom:company-name", ns) is not None else "",
                "cik": root.find(".//atom:cik", ns).text if root.find(".//atom:cik", ns) is not None else "",
            }
            
            # Extract filings
            entries = root.findall(".//atom:entry", ns)
            
            for entry in entries:
                # Extract category/filing type
                category = entry.find("./atom:category", ns)
                filing_type_elem = category.get("term") if category is not None else None
                
                # Extract date
                updated = entry.find("./atom:updated", ns)
                filing_date = updated.text[:10] if updated is not None else None  # YYYY-MM-DD
                
                # Extract title and link
                title = entry.find("./atom:title", ns)
                title_text = title.text if title is not None else None
                
                link = entry.find("./atom:link", ns)
                url = link.get("href") if link is not None else None
                
                # Extract accession number from id
                entry_id = entry.find("./atom:id", ns)
                accession_number = None
                if entry_id is not None and entry_id.text:
                    # Format: tag:accession-number
                    parts = entry_id.text.split(":")
                    if len(parts) > 1:
                        accession_number = parts[1]
                
                filings.append({
                    "company": company_info["name"],
                    "cik": company_info["cik"],
                    "filing_type": filing_type_elem,
                    "filing_date": filing_date,
                    "title": title_text,
                    "url": url,
                    "accession_number": accession_number
                })
                
            return filings
            
        except ET.ParseError as e:
            raise Exception(f"Failed to parse SEC API response: {e}")
            
    def get_filing_text(self, filing_url: str, filing_type: str, company_name: str, cik: str, filing_date: str, accession_number: Optional[str] = None) -> Dict[str, Any]:
        """Fetch and parse an SEC filing document.
        
        Args:
            filing_url: URL to the SEC filing
            filing_type: Filing type
            company_name: Company name
            cik: Company CIK number
            filing_date: Filing date (YYYY-MM-DD)
            accession_number: Filing accession number
            
        Returns:
            Dictionary with filing metadata and text content
        """
        cache_path = self._get_cache_path(filing_type, company_name, cik, filing_date, accession_number)
        
        # Check cache first
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
                
        # Respect rate limits
        self._respect_rate_limit()
        
        # Make request to SEC
        response = requests.get(filing_url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch filing: {response.status_code}")
            
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract text content - different filings have different structures
        # We'll get the full text and also try to extract key sections
        full_text = soup.get_text(separator="\n", strip=True)
        
        # Try to find important sections based on common headers
        sections = {}
        
        # Look for common section headers in tables, divs, and h tags
        section_headers = [
            "Risk Factors",
            "Management's Discussion",
            "Financial Statements",
            "Results of Operations",
            "Liquidity and Capital Resources",
            "Controls and Procedures"
        ]
        
        for header in section_headers:
            # Find elements containing this header text
            elements = soup.find_all(string=lambda text: text and header in text)
            
            if elements:
                # For each match, get the parent element and extract its text
                for element in elements:
                    parent = element.parent
                    # Get the next sibling or parent's next sibling that likely contains content
                    content = None
                    
                    # Check if parent is a header, if so look at next siblings
                    if parent.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        # Collect text from next siblings until we hit another header
                        content_parts = []
                        sibling = parent.next_sibling
                        
                        while sibling and sibling.name not in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                            if hasattr(sibling, "get_text"):
                                content_parts.append(sibling.get_text(separator="\n", strip=True))
                            sibling = sibling.next_sibling
                            
                        content = "\n".join(content_parts)
                    
                    # If we couldn't get content from siblings, use the parent's text
                    if not content:
                        # Go up to find a container
                        container = parent
                        for _ in range(3):  # Try up to 3 levels up
                            if container.name in ["div", "section", "table", "td"]:
                                content = container.get_text(separator="\n", strip=True)
                                break
                            if container.parent:
                                container = container.parent
                                
                    if content and len(content) > len(header) + 20:  # Ensure we have meaningful content
                        sections[header] = content
                        break  # Use first good match for this header
        
        # Prepare filing data
        filing_data = {
            "company": company_name,
            "cik": cik,
            "filing_type": filing_type,
            "filing_date": filing_date,
            "accession_number": accession_number,
            "url": filing_url,
            "full_text": full_text[:500000],  # Limit size
            "sections": sections,
            "_cache_timestamp": time.time()
        }
        
        # Save to cache
        with open(cache_path, 'w') as f:
            json.dump(filing_data, f)
            
        return filing_data
    
    def get_latest_filings(self, 
                           ticker_symbol: str, 
                           filing_types: Optional[List[str]] = None,
                           count: int = 5) -> List[Dict[str, Any]]:
        """Get latest SEC filings for a company.
        
        Args:
            ticker_symbol: Stock ticker symbol
            filing_types: List of filing types to fetch (default: ['10-K', '10-Q', '8-K', '6-K', '20-F'])
            count: Maximum number of filings to return
            
        Returns:
            List of filings with metadata and content
        """
        if filing_types is None:
            filing_types = ['10-K', '10-Q', '8-K', '6-K', '20-F']
            
        # Search for filings
        try:
            filings_meta = self.search_filings(
                ticker_symbol=ticker_symbol,
                filing_type="|".join(filing_types),  # OR search
                count=count
            )
        except Exception as e:
            logger.error(f"Error searching for filings: {e}")
            return []
            
        # Fetch full text for each filing
        filings_with_text = []
        
        for filing in filings_meta:
            if not filing.get("url"):
                continue
                
            try:
                filing_text = self.get_filing_text(
                    filing_url=filing["url"],
                    filing_type=filing["filing_type"],
                    company_name=filing["company"],
                    cik=filing["cik"],
                    filing_date=filing["filing_date"],
                    accession_number=filing["accession_number"]
                )
                filings_with_text.append(filing_text)
            except Exception as e:
                logger.error(f"Error fetching filing text: {e}")
                
        return filings_with_text
    
    def get_asian_tech_filings(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent SEC filings for Asian tech companies.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of filings with metadata and content
        """
        # Asian tech ticker symbols
        asian_tech_tickers = [
            "TSM",   # Taiwan Semiconductor
            "BABA",  # Alibaba
            "9988.HK",  # Alibaba (Hong Kong)
            "BIDU",  # Baidu
            "SE",    # Sea Limited
            "GRAB",  # Grab
            "9618.HK",  # JD.com
            "BILI"   # Bilibili
        ]
        
        # Calculate date range
        after_date = datetime.now() - timedelta(days=days_back)
        
        all_filings = []
        
        # Get filings for each ticker
        for ticker in asian_tech_tickers:
            try:
                ticker_filings = self.get_latest_filings(
                    ticker_symbol=ticker,
                    filing_types=['6-K', '20-F'],  # Focus on international filings
                    count=3  # Limit per company
                )
                
                # Filter by date if needed
                if days_back:
                    ticker_filings = [
                        f for f in ticker_filings 
                        if f.get("filing_date") and datetime.strptime(f["filing_date"], "%Y-%m-%d") >= after_date
                    ]
                    
                all_filings.extend(ticker_filings)
                
            except Exception as e:
                logger.error(f"Error fetching filings for {ticker}: {e}")
                
        return all_filings
    

# Module-level scraper instance for easy access
scraper = SECFilingScraper()

# Convenience functions
def get_latest_asian_tech_filings(days_back: int = 30) -> List[Dict[str, Any]]:
    """Get recent SEC filings for Asian tech companies.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        List of filings with metadata and content
    """
    return scraper.get_asian_tech_filings(days_back)


def get_filings_for_ticker(ticker: str, count: int = 3) -> List[Dict[str, Any]]:
    """Get recent SEC filings for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        count: Maximum number of filings to return
        
    Returns:
        List of filings with metadata and content
    """
    return scraper.get_latest_filings(ticker_symbol=ticker, count=count) 