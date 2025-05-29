"""
API Agent FastAPI Microservice
Polls real-time & historical market data via AlphaVantage or Yahoo Finance
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from .alphavantage_client import get_price, get_earnings_surprise, get_company_overview
from .yahoo_client import get_real_time_price, get_historical_data, get_market_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_agent")

app = FastAPI(
    title="API Agent",
    description="Real-time & historical market data microservice",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    data_sources: List[str]


class PriceRequest(BaseModel):
    """Stock price request"""
    symbol: str
    source: Optional[str] = "alphavantage"  # "alphavantage" or "yahoo"


class PriceResponse(BaseModel):
    """Stock price response"""
    symbol: str
    price: float
    currency: str
    timestamp: str
    source: str
    status: str


class EarningsRequest(BaseModel):
    """Earnings surprise request"""
    symbol: str
    periods: Optional[int] = 4


class EarningsResponse(BaseModel):
    """Earnings surprise response"""
    symbol: str
    earnings_data: List[Dict[str, Any]]
    status: str


class HistoricalRequest(BaseModel):
    """Historical data request"""
    symbol: str
    period: Optional[str] = "1y"  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval: Optional[str] = "1d"  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo


class HistoricalResponse(BaseModel):
    """Historical data response"""
    symbol: str
    data: List[Dict[str, Any]]
    period: str
    interval: str
    status: str


class MarketSummaryResponse(BaseModel):
    """Market summary response"""
    indices: Dict[str, Dict[str, Any]]
    currencies: Dict[str, Dict[str, Any]]
    commodities: Dict[str, Dict[str, Any]]
    timestamp: str
    status: str


class CompanyRequest(BaseModel):
    """Company overview request"""
    symbol: str


class CompanyResponse(BaseModel):
    """Company overview response"""
    symbol: str
    company_data: Dict[str, Any]
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="api_agent",
        version="1.0.0",
        data_sources=["AlphaVantage", "Yahoo Finance"]
    )


@app.post("/price", response_model=PriceResponse)
async def get_stock_price(request: PriceRequest):
    """Get real-time stock price"""
    try:
        if request.source == "alphavantage":
            data = get_price(request.symbol)
            return PriceResponse(
                symbol=request.symbol,
                price=data["price"],
                currency=data.get("currency", "USD"),
                timestamp=data.get("timestamp", ""),
                source="AlphaVantage",
                status="success"
            )
        elif request.source == "yahoo":
            data = get_real_time_price(request.symbol)
            return PriceResponse(
                symbol=request.symbol,
                price=data["price"],
                currency=data.get("currency", "USD"),
                timestamp=data.get("timestamp", ""),
                source="Yahoo Finance",
                status="success"
            )
        else:
            raise ValueError(f"Unsupported data source: {request.source}")
            
    except Exception as e:
        logger.error(f"Price fetch error for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch price for {request.symbol}: {str(e)}")


@app.post("/earnings", response_model=EarningsResponse)
async def get_earnings_data(request: EarningsRequest):
    """Get earnings surprise data"""
    try:
        data = get_earnings_surprise(request.symbol, request.periods)
        
        return EarningsResponse(
            symbol=request.symbol,
            earnings_data=data,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Earnings fetch error for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch earnings for {request.symbol}: {str(e)}")


@app.post("/historical", response_model=HistoricalResponse)
async def get_historical_prices(request: HistoricalRequest):
    """Get historical price data"""
    try:
        data = get_historical_data(request.symbol, request.period, request.interval)
        
        return HistoricalResponse(
            symbol=request.symbol,
            data=data,
            period=request.period,
            interval=request.interval,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Historical data fetch error for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch historical data for {request.symbol}: {str(e)}")


@app.get("/market-summary", response_model=MarketSummaryResponse)
async def get_market_overview():
    """Get overall market summary"""
    try:
        data = get_market_summary()
        
        return MarketSummaryResponse(
            indices=data.get("indices", {}),
            currencies=data.get("currencies", {}),
            commodities=data.get("commodities", {}),
            timestamp=data.get("timestamp", ""),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Market summary fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch market summary: {str(e)}")


@app.post("/company", response_model=CompanyResponse)
async def get_company_info(request: CompanyRequest):
    """Get company overview data"""
    try:
        data = get_company_overview(request.symbol)
        
        return CompanyResponse(
            symbol=request.symbol,
            company_data=data,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Company data fetch error for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch company data for {request.symbol}: {str(e)}")


@app.get("/symbols/asian-tech")
async def get_asian_tech_symbols():
    """Get list of Asian tech stock symbols"""
    try:
        # Common Asian tech stocks
        symbols = [
            "TSM",     # Taiwan Semiconductor
            "ASML",    # ASML Holding
            "005930.KS", # Samsung Electronics
            "6758.T",  # Sony
            "9984.T",  # SoftBank
            "BABA",    # Alibaba
            "JD",      # JD.com
            "BIDU",    # Baidu
            "PDD",     # PDD Holdings
            "NTES"     # NetEase
        ]
        
        return {
            "symbols": symbols,
            "count": len(symbols),
            "region": "Asia-Tech",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Symbol list error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get symbol list: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 