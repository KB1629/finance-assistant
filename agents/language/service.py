"""
Language Agent FastAPI Microservice
Handles LLM synthesis using LangGraph workflow
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from .workflow import FinanceWorkflow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("language_agent")

app = FastAPI(
    title="Language Agent",
    description="LLM synthesis microservice using LangGraph",
    version="1.0.0"
)

# Initialize workflow
workflow = FinanceWorkflow()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str


class SynthesizeRequest(BaseModel):
    """Language synthesis request"""
    query: str
    context: Optional[List[Dict[str, Any]]] = []
    portfolio_data: Optional[Dict[str, Any]] = {}
    market_data: Optional[Dict[str, Any]] = {}


class SynthesizeResponse(BaseModel):
    """Language synthesis response"""
    response: str
    confidence: float
    sources_used: List[str]
    status: str


class MarketBriefRequest(BaseModel):
    """Market brief request"""
    region: Optional[str] = None
    focus_areas: Optional[List[str]] = ["risk", "earnings", "sentiment"]


class MarketBriefResponse(BaseModel):
    """Market brief response"""
    brief: str
    key_metrics: Dict[str, Any]
    confidence: float
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="language_agent",
        version="1.0.0"
    )


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_response(request: SynthesizeRequest):
    """Synthesize natural language response from structured data"""
    try:
        # Prepare workflow state
        workflow_state = {
            "query": request.query,
            "context": request.context,
            "portfolio_data": request.portfolio_data,
            "market_data": request.market_data
        }
        
        # Run workflow
        result = workflow.run(workflow_state)
        
        return SynthesizeResponse(
            response=result["synthesized_response"],
            confidence=result.get("confidence", 0.8),
            sources_used=result.get("sources_used", []),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Language synthesis failed: {str(e)}")


@app.post("/market-brief", response_model=MarketBriefResponse)
async def generate_market_brief(request: MarketBriefRequest):
    """Generate comprehensive market brief"""
    try:
        # Build market brief query
        if request.region:
            query = f"Generate a market brief for {request.region} focusing on {', '.join(request.focus_areas)}"
        else:
            query = f"Generate a comprehensive market brief focusing on {', '.join(request.focus_areas)}"
        
        # Prepare workflow state for market brief
        workflow_state = {
            "query": query,
            "context": [],
            "portfolio_data": {},
            "market_data": {},
            "brief_type": "market_brief",
            "region": request.region,
            "focus_areas": request.focus_areas
        }
        
        # Run workflow
        result = workflow.run(workflow_state)
        
        return MarketBriefResponse(
            brief=result["synthesized_response"],
            key_metrics=result.get("key_metrics", {}),
            confidence=result.get("confidence", 0.8),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Market brief error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Market brief generation failed: {str(e)}")


@app.post("/analyze", response_model=SynthesizeResponse)
async def analyze_portfolio_query(request: SynthesizeRequest):
    """Analyze portfolio-specific queries"""
    try:
        # Enhanced workflow state for analysis
        workflow_state = {
            "query": request.query,
            "context": request.context,
            "portfolio_data": request.portfolio_data,
            "market_data": request.market_data,
            "analysis_type": "portfolio_analysis"
        }
        
        # Run analytical workflow
        result = workflow.run(workflow_state)
        
        return SynthesizeResponse(
            response=result["synthesized_response"],
            confidence=result.get("confidence", 0.8),
            sources_used=result.get("sources_used", []),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Portfolio analysis failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 