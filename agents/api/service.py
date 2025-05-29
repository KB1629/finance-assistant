"""
API Agent Microservice - Market Data API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from data_ingestion.api_agent.alphavantage_client import get_price, get_earnings_surprise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api_agent_service")

app = FastAPI(
    title="API Agent - Market Data Service",
    description="Microservice for real-time and historical market data",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str


class StockPriceRequest(BaseModel):
    """Stock price request"""
    symbol: str
    date: Optional[str] = None


class StockPriceResponse(BaseModel):
    """Stock price response"""
    symbol: str
    price: float
    date: str
    status: str


class EarningsRequest(BaseModel):
    """Earnings request"""
    symbol: str
    period: Optional[str] = None


class EarningsResponse(BaseModel):
    """Earnings response"""
    symbol: str
    surprise_percentage: float
    period: Optional[str]
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", service="api-agent")


@app.post("/price", response_model=StockPriceResponse)
async def get_stock_price(request: StockPriceRequest):
    """Get stock price for a symbol"""
    try:
        price = get_price(request.symbol, request.date)
        return StockPriceResponse(
            symbol=request.symbol,
            price=price,
            date=request.date or "latest",
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting price for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/earnings", response_model=EarningsResponse)
async def get_earnings_data(request: EarningsRequest):
    """Get earnings surprise data for a symbol"""
    try:
        surprise = get_earnings_surprise(request.symbol, request.period)
        return EarningsResponse(
            symbol=request.symbol,
            surprise_percentage=surprise,
            period=request.period,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting earnings for {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 