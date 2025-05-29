"""
Scraping Agent FastAPI Microservice
Crawls filings using Python loaders
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from .sec_scraper import get_filings_for_ticker, get_latest_asian_tech_filings, search_filings
from .earnings_scraper import scrape_earnings_calendar, scrape_earnings_surprises

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper_agent")

app = FastAPI(
    title="Scraper Agent",
    description="SEC filings and financial data scraping microservice",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    scrapers: List[str]


class FilingRequest(BaseModel):
    """Filing scraping request"""
    ticker: Optional[str] = None
    filing_type: Optional[str] = None  # "10-K", "10-Q", "8-K", etc.
    count: Optional[int] = 10
    days_back: Optional[int] = 90


class FilingResponse(BaseModel):
    """Filing scraping response"""
    ticker: str
    filings: List[Dict[str, Any]]
    total_found: int
    status: str


class AsianTechFilingRequest(BaseModel):
    """Asian tech filing request"""
    days_back: Optional[int] = 30
    companies: Optional[List[str]] = []


class AsianTechFilingResponse(BaseModel):
    """Asian tech filing response"""
    filings: List[Dict[str, Any]]
    companies_covered: List[str]
    total_found: int
    status: str


class EarningsCalendarRequest(BaseModel):
    """Earnings calendar request"""
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    region: Optional[str] = None


class EarningsCalendarResponse(BaseModel):
    """Earnings calendar response"""
    earnings_events: List[Dict[str, Any]]
    date_range: Dict[str, str]
    total_events: int
    status: str


class EarningsSurpriseRequest(BaseModel):
    """Earnings surprise request"""
    symbols: Optional[List[str]] = []
    region: Optional[str] = None
    periods: Optional[int] = 4


class EarningsSurpriseResponse(BaseModel):
    """Earnings surprise response"""
    surprises: List[Dict[str, Any]]
    symbols_covered: List[str]
    total_surprises: int
    status: str


class SearchRequest(BaseModel):
    """General search request"""
    query: str
    source: Optional[str] = "sec"  # "sec", "earnings", "news"
    limit: Optional[int] = 20


class SearchResponse(BaseModel):
    """General search response"""
    results: List[Dict[str, Any]]
    query: str
    source: str
    total_results: int
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="scraper_agent",
        version="1.0.0",
        scrapers=["SEC EDGAR", "Earnings Calendar", "Financial News"]
    )


@app.post("/filings/ticker", response_model=FilingResponse)
async def scrape_ticker_filings(request: FilingRequest):
    """Scrape SEC filings for a specific ticker"""
    try:
        if not request.ticker:
            raise ValueError("Ticker symbol is required")
            
        filings = get_filings_for_ticker(
            ticker=request.ticker,
            filing_type=request.filing_type,
            count=request.count or 10,
            days_back=request.days_back or 90
        )
        
        return FilingResponse(
            ticker=request.ticker,
            filings=filings,
            total_found=len(filings),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Filing scrape error for {request.ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape filings for {request.ticker}: {str(e)}")


@app.post("/filings/asian-tech", response_model=AsianTechFilingResponse)
async def scrape_asian_tech_filings(request: AsianTechFilingRequest):
    """Scrape latest Asian tech company filings"""
    try:
        filings = get_latest_asian_tech_filings(
            days_back=request.days_back or 30,
            companies=request.companies or []
        )
        
        companies_covered = list(set([f.get("company", "") for f in filings if f.get("company")]))
        
        return AsianTechFilingResponse(
            filings=filings,
            companies_covered=companies_covered,
            total_found=len(filings),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Asian tech filing scrape error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape Asian tech filings: {str(e)}")


@app.post("/earnings/calendar", response_model=EarningsCalendarResponse)
async def scrape_earnings_calendar_data(request: EarningsCalendarRequest):
    """Scrape earnings calendar data"""
    try:
        earnings_events = scrape_earnings_calendar(
            date_from=request.date_from,
            date_to=request.date_to,
            region=request.region
        )
        
        return EarningsCalendarResponse(
            earnings_events=earnings_events,
            date_range={
                "from": request.date_from or "auto",
                "to": request.date_to or "auto"
            },
            total_events=len(earnings_events),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Earnings calendar scrape error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape earnings calendar: {str(e)}")


@app.post("/earnings/surprises", response_model=EarningsSurpriseResponse)
async def scrape_earnings_surprise_data(request: EarningsSurpriseRequest):
    """Scrape earnings surprise data"""
    try:
        surprises = scrape_earnings_surprises(
            symbols=request.symbols or [],
            region=request.region,
            periods=request.periods or 4
        )
        
        symbols_covered = list(set([s.get("symbol", "") for s in surprises if s.get("symbol")]))
        
        return EarningsSurpriseResponse(
            surprises=surprises,
            symbols_covered=symbols_covered,
            total_surprises=len(surprises),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Earnings surprise scrape error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape earnings surprises: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_financial_data(request: SearchRequest):
    """General search across financial data sources"""
    try:
        if request.source == "sec":
            results = search_filings(request.query, limit=request.limit or 20)
        elif request.source == "earnings":
            # Search earnings-related data
            results = scrape_earnings_surprises(symbols=[], region=None, periods=4)
            # Filter results based on query
            results = [r for r in results if request.query.lower() in str(r).lower()][:request.limit or 20]
        else:
            raise ValueError(f"Unsupported search source: {request.source}")
        
        return SearchResponse(
            results=results,
            query=request.query,
            source=request.source,
            total_results=len(results),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Search error for '{request.query}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/sources")
async def get_data_sources():
    """Get available data sources and their status"""
    try:
        sources = {
            "sec_edgar": {
                "status": "active",
                "description": "SEC EDGAR filing database",
                "supported_filings": ["10-K", "10-Q", "8-K", "DEF 14A"]
            },
            "earnings_calendar": {
                "status": "active", 
                "description": "Earnings announcement calendar",
                "regions": ["US", "Asia", "Europe"]
            },
            "financial_news": {
                "status": "development",
                "description": "Financial news aggregation",
                "sources": ["Reuters", "Bloomberg", "MarketWatch"]
            }
        }
        
        return {
            "sources": sources,
            "total_sources": len(sources),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Sources list error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 