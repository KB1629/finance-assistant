"""
FastAPI orchestrator service - Implementation for Sprint 2
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from data_ingestion.api_agent.alphavantage_client import get_price, get_earnings_surprise
from data_ingestion.scraper_agent.sec_scraper import get_filings_for_ticker, get_latest_asian_tech_filings
from agents.retriever.vector_store import query as vector_query, add_texts
from agents.retriever.document_loader import load_ticker_filings, load_asian_tech_filings, load_from_text_files
from agents.analytics.portfolio import get_portfolio_value, get_risk_exposure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("orchestrator")

app = FastAPI(
    title="Finance Assistant Orchestrator",
    description="Multi-Agent Finance Assistant API Gateway",
    version="0.2.0"
)


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    message: str


class QueryRequest(BaseModel):
    """Query request model"""
    text: str


class QueryResponse(BaseModel):
    """Query response model"""
    response: str
    status: str


class StockPriceRequest(BaseModel):
    """Stock price request model"""
    symbol: str
    date: Optional[str] = None


class StockPriceResponse(BaseModel):
    """Stock price response model"""
    symbol: str
    price: float
    date: str
    status: str


class EarningsRequest(BaseModel):
    """Earnings request model"""
    symbol: str
    period: Optional[str] = None


class EarningsResponse(BaseModel):
    """Earnings response model"""
    symbol: str
    surprise_percentage: float
    period: Optional[str]
    status: str


class FilingRequest(BaseModel):
    """Filing request model"""
    symbol: str
    count: int = 3


class FilingResponse(BaseModel):
    """Filing response model"""
    symbol: str
    filings: List[Dict[str, Any]]
    status: str


class AsianFilingsRequest(BaseModel):
    """Asian filings request model"""
    days_back: int = 30


class AsianFilingsResponse(BaseModel):
    """Asian filings response model"""
    filings_count: int
    filings: List[Dict[str, Any]]
    status: str


class VectorQueryRequest(BaseModel):
    """Vector query request model"""
    query: str
    k: int = 5


class VectorQueryResponse(BaseModel):
    """Vector query response model"""
    results: List[Dict[str, Any]]
    status: str


class IndexRequest(BaseModel):
    """Index request model for document ingestion"""
    source_type: str  # "ticker", "asian", "file"
    ticker: Optional[str] = None
    count: int = 3
    days_back: int = 90
    directory: Optional[str] = None


class IndexResponse(BaseModel):
    """Index response model"""
    documents_indexed: int
    status: str


class PortfolioRequest(BaseModel):
    """Portfolio request model"""
    region: Optional[str] = None


class PortfolioResponse(BaseModel):
    """Portfolio response model"""
    portfolio_data: Dict[str, Any]
    status: str


class RiskExposureRequest(BaseModel):
    """Risk exposure request model"""
    region: Optional[str] = None


class RiskExposureResponse(BaseModel):
    """Risk exposure response model"""
    risk_data: Dict[str, Any]
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Finance Assistant Orchestrator v0.2.0 is running"
    )


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint"""
    return HealthResponse(
        status="running",
        message="Finance Assistant Orchestrator - Use /docs for API documentation"
    )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a text query"""
    try:
        # Check for risk exposure query
        query_text = request.text.lower()
        
        if "risk" in query_text and "exposure" in query_text:
            # Extract region if mentioned
            region = None
            if "asia" in query_text or "asian" in query_text:
                region = "Asia-Tech"
            elif "us" in query_text or "america" in query_text:
                region = "US-Tech"
                
            # Get risk exposure
            risk_data = get_risk_exposure(region)
            
            # Format response
            if region:
                response = f"Risk exposure for {region}: {risk_data['asia_tech_exposure']['percentage']:.1f}% of portfolio."
            else:
                response = "Portfolio risk exposure: "
                for exposure in risk_data["exposures"]:
                    response += f"{exposure['geo_tag']}: {exposure['percentage']:.1f}%, "
                    
            # Add earnings surprises
            if risk_data["earnings_surprises"]:
                response += " Recent earnings surprises: "
                for surprise in risk_data["earnings_surprises"][:3]:  # Top 3
                    direction = "beat" if surprise["surprise_percentage"] > 0 else "missed"
                    response += f"{surprise['symbol']} {direction} by {abs(surprise['surprise_percentage']):.1f}%, "
                    
            return QueryResponse(
                response=response.strip(", "),
                status="success"
            )
        
        # Default to vector search if not a risk query
        results = vector_query(request.text, k=3)
        
        if results:
            # Format response from vector search
            response = "I found the following relevant information:\n"
            for doc, score in results:
                response += f"- {doc['text'][:150]}...\n"
        else:
            # Fallback response
            response = "I don't have specific information about that query. You can ask about stock prices, earnings, or risk exposure."
            
        return QueryResponse(
            response=response,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return QueryResponse(
            response=f"Error processing your query: {str(e)}",
            status="error"
        )


@app.post("/stock/price", response_model=StockPriceResponse)
async def stock_price(request: StockPriceRequest):
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
        logger.error(f"Error getting stock price: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stock/earnings", response_model=EarningsResponse)
async def earnings_surprise(request: EarningsRequest):
    """Get earnings surprise for a symbol"""
    try:
        surprise = get_earnings_surprise(request.symbol, request.period)
        return EarningsResponse(
            symbol=request.symbol,
            surprise_percentage=surprise,
            period=request.period or "latest",
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting earnings surprise: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/filings/ticker", response_model=FilingResponse)
async def filings_for_ticker(request: FilingRequest):
    """Get SEC filings for a ticker"""
    try:
        filings = get_filings_for_ticker(request.symbol, request.count)
        return FilingResponse(
            symbol=request.symbol,
            filings=filings,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting filings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/filings/asian-tech", response_model=AsianFilingsResponse)
async def asian_tech_filings(request: AsianFilingsRequest):
    """Get SEC filings for Asian tech companies"""
    try:
        filings = get_latest_asian_tech_filings(request.days_back)
        return AsianFilingsResponse(
            filings_count=len(filings),
            filings=filings,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting Asian tech filings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retriever/query", response_model=VectorQueryResponse)
async def retriever_query(request: VectorQueryRequest):
    """Query the vector store"""
    try:
        results = vector_query(request.query, request.k)
        
        # Format results to remove non-serializable elements
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.get("text", ""),
                "metadata": {k: v for k, v in doc.items() if k != "text"},
                "score": float(score)
            })
            
        return VectorQueryResponse(
            results=formatted_results,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error querying vector store: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retriever/index", response_model=IndexResponse)
async def retriever_index(request: IndexRequest):
    """Index documents in the vector store"""
    try:
        documents = []
        
        if request.source_type == "ticker" and request.ticker:
            # Index SEC filings for a specific ticker
            documents = load_ticker_filings(request.ticker, request.count)
            
        elif request.source_type == "asian":
            # Index SEC filings for Asian tech companies
            documents = load_asian_tech_filings(request.days_back)
            
        elif request.source_type == "file" and request.directory:
            # Index documents from text files
            documents = load_from_text_files(request.directory)
            
        else:
            raise ValueError("Invalid source type or missing required parameters")
        
        return IndexResponse(
            documents_indexed=len(documents),
            status="success"
        )
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/value", response_model=PortfolioResponse)
async def portfolio_value(request: PortfolioRequest):
    """Get portfolio value and analytics"""
    try:
        portfolio_data = get_portfolio_value()
        return PortfolioResponse(
            portfolio_data=portfolio_data,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting portfolio value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/risk", response_model=RiskExposureResponse)
async def risk_exposure(request: RiskExposureRequest):
    """Get portfolio risk exposure"""
    try:
        risk_data = get_risk_exposure(request.region)
        return RiskExposureResponse(
            risk_data=risk_data,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error getting risk exposure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 