"""
Analysis Agent FastAPI Microservice  
Performs portfolio analysis and quantitative analysis
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from .portfolio import get_portfolio_value, get_risk_exposure, calculate_portfolio_metrics, analyze_performance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analysis_agent")

app = FastAPI(
    title="Analysis Agent",
    description="Portfolio analysis and quantitative analysis microservice",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    analysis_types: List[str]


class PortfolioAnalysisRequest(BaseModel):
    """Portfolio analysis request"""
    portfolio_id: Optional[str] = None
    region: Optional[str] = None
    asset_class: Optional[str] = None
    analysis_type: str = "risk_exposure"  # "risk_exposure", "performance", "allocation", "metrics"


class PortfolioAnalysisResponse(BaseModel):
    """Portfolio analysis response"""
    analysis_type: str
    portfolio_data: Dict[str, Any]
    metrics: Dict[str, Any]
    recommendations: List[str]
    status: str


class RiskAnalysisRequest(BaseModel):
    """Risk analysis request"""
    symbols: List[str]
    portfolio_weights: Optional[List[float]] = []
    time_horizon: Optional[str] = "1Y"
    confidence_level: Optional[float] = 0.95


class RiskAnalysisResponse(BaseModel):
    """Risk analysis response"""
    var_estimates: Dict[str, float]
    risk_metrics: Dict[str, Any]
    correlation_matrix: List[List[float]]
    recommendations: List[str]
    status: str


class PerformanceAnalysisRequest(BaseModel):
    """Performance analysis request"""
    portfolio_id: Optional[str] = None
    benchmark: Optional[str] = "SPY"
    period: Optional[str] = "1Y"
    metrics: Optional[List[str]] = ["returns", "volatility", "sharpe", "max_drawdown"]


class PerformanceAnalysisResponse(BaseModel):
    """Performance analysis response"""
    performance_metrics: Dict[str, Any]
    benchmark_comparison: Dict[str, Any]
    period_analysis: Dict[str, Any]
    status: str


class MarketAnalysisRequest(BaseModel):
    """Market analysis request"""
    region: Optional[str] = None
    sector: Optional[str] = None
    analysis_focus: List[str] = ["sentiment", "volatility", "trends"]


class MarketAnalysisResponse(BaseModel):
    """Market analysis response"""
    market_metrics: Dict[str, Any]
    sector_analysis: Dict[str, Any]
    sentiment_indicators: Dict[str, Any]
    market_trends: List[Dict[str, Any]]
    status: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="analysis_agent",
        version="1.0.0",
        analysis_types=["Portfolio", "Risk", "Performance", "Market", "Quantitative"]
    )


@app.post("/portfolio/analyze", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(request: PortfolioAnalysisRequest):
    """Perform comprehensive portfolio analysis"""
    try:
        if request.analysis_type == "risk_exposure":
            data = get_risk_exposure(request.region)
            metrics = calculate_portfolio_metrics(data)
            recommendations = generate_risk_recommendations(data)
            
        elif request.analysis_type == "performance":
            data = analyze_performance(
                portfolio_id=request.portfolio_id,
                region=request.region
            )
            metrics = data.get("performance_metrics", {})
            recommendations = generate_performance_recommendations(data)
            
        elif request.analysis_type == "allocation":
            data = get_portfolio_value(request.region)
            metrics = calculate_allocation_metrics(data)
            recommendations = generate_allocation_recommendations(data)
            
        else:
            raise ValueError(f"Unsupported analysis type: {request.analysis_type}")
            
        return PortfolioAnalysisResponse(
            analysis_type=request.analysis_type,
            portfolio_data=data,
            metrics=metrics,
            recommendations=recommendations,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Portfolio analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Portfolio analysis failed: {str(e)}")


@app.post("/risk/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest):
    """Perform risk analysis on portfolio or securities"""
    try:
        # Calculate Value at Risk (VaR)
        var_estimates = calculate_var(
            symbols=request.symbols,
            weights=request.portfolio_weights,
            confidence_level=request.confidence_level,
            time_horizon=request.time_horizon
        )
        
        # Calculate risk metrics
        risk_metrics = calculate_risk_metrics(request.symbols, request.portfolio_weights)
        
        # Generate correlation matrix
        correlation_matrix = calculate_correlation_matrix(request.symbols)
        
        # Generate recommendations
        recommendations = generate_risk_recommendations({
            "var": var_estimates,
            "metrics": risk_metrics,
            "correlations": correlation_matrix
        })
        
        return RiskAnalysisResponse(
            var_estimates=var_estimates,
            risk_metrics=risk_metrics,
            correlation_matrix=correlation_matrix,
            recommendations=recommendations,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Risk analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {str(e)}")


@app.post("/performance/analyze", response_model=PerformanceAnalysisResponse)
async def analyze_performance_endpoint(request: PerformanceAnalysisRequest):
    """Perform performance analysis"""
    try:
        # Get performance data
        performance_data = analyze_performance(
            portfolio_id=request.portfolio_id,
            period=request.period
        )
        
        # Calculate performance metrics
        performance_metrics = calculate_performance_metrics(
            performance_data,
            metrics=request.metrics
        )
        
        # Benchmark comparison
        benchmark_comparison = compare_to_benchmark(
            performance_data,
            benchmark=request.benchmark
        )
        
        # Period analysis
        period_analysis = analyze_periods(performance_data, request.period)
        
        return PerformanceAnalysisResponse(
            performance_metrics=performance_metrics,
            benchmark_comparison=benchmark_comparison,
            period_analysis=period_analysis,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Performance analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")


@app.post("/market/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(request: MarketAnalysisRequest):
    """Perform market analysis"""
    try:
        # Get market data
        market_data = get_market_data(
            region=request.region,
            sector=request.sector
        )
        
        # Calculate market metrics
        market_metrics = calculate_market_metrics(market_data)
        
        # Sector analysis
        sector_analysis = analyze_sectors(market_data, request.sector)
        
        # Sentiment indicators
        sentiment_indicators = calculate_sentiment_indicators(market_data)
        
        # Market trends
        market_trends = identify_market_trends(market_data)
        
        return MarketAnalysisResponse(
            market_metrics=market_metrics,
            sector_analysis=sector_analysis,
            sentiment_indicators=sentiment_indicators,
            market_trends=market_trends,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Market analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Market analysis failed: {str(e)}")


# Helper functions (these would typically be in separate modules)

def generate_risk_recommendations(data: Dict[str, Any]) -> List[str]:
    """Generate risk management recommendations"""
    recommendations = [
        "Consider diversification across asset classes",
        "Monitor correlation levels during market stress",
        "Implement stop-loss strategies for high-risk positions"
    ]
    return recommendations


def generate_performance_recommendations(data: Dict[str, Any]) -> List[str]:
    """Generate performance improvement recommendations"""
    recommendations = [
        "Review underperforming positions",
        "Consider rebalancing portfolio allocation",
        "Evaluate risk-adjusted returns"
    ]
    return recommendations


def generate_allocation_recommendations(data: Dict[str, Any]) -> List[str]:
    """Generate allocation recommendations"""
    recommendations = [
        "Maintain balanced exposure across regions",
        "Consider market cap diversification",
        "Review sector concentration"
    ]
    return recommendations


def calculate_var(symbols: List[str], weights: List[float], confidence_level: float, time_horizon: str) -> Dict[str, float]:
    """Calculate Value at Risk"""
    # Mock implementation
    return {
        "portfolio_var": 0.05,
        "individual_vars": {symbol: 0.03 for symbol in symbols}
    }


def calculate_risk_metrics(symbols: List[str], weights: List[float]) -> Dict[str, Any]:
    """Calculate comprehensive risk metrics"""
    # Mock implementation
    return {
        "portfolio_volatility": 0.18,
        "beta": 1.2,
        "sharpe_ratio": 1.5,
        "max_drawdown": 0.12
    }


def calculate_correlation_matrix(symbols: List[str]) -> List[List[float]]:
    """Calculate correlation matrix"""
    # Mock implementation - would use actual price data
    n = len(symbols)
    import random
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                row.append(random.uniform(0.3, 0.8))
        matrix.append(row)
    return matrix


def calculate_performance_metrics(data: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
    """Calculate performance metrics"""
    # Mock implementation
    return {
        "returns": 0.12,
        "volatility": 0.18,
        "sharpe": 1.5,
        "max_drawdown": 0.08
    }


def compare_to_benchmark(data: Dict[str, Any], benchmark: str) -> Dict[str, Any]:
    """Compare performance to benchmark"""
    # Mock implementation
    return {
        "alpha": 0.02,
        "beta": 1.1,
        "tracking_error": 0.05,
        "information_ratio": 0.8
    }


def analyze_periods(data: Dict[str, Any], period: str) -> Dict[str, Any]:
    """Analyze performance across different periods"""
    # Mock implementation
    return {
        "monthly_returns": [0.01, 0.02, -0.01, 0.03],
        "quarterly_performance": [0.05, 0.03, 0.04],
        "rolling_volatility": [0.15, 0.18, 0.16]
    }


def get_market_data(region: Optional[str], sector: Optional[str]) -> Dict[str, Any]:
    """Get market data"""
    # Mock implementation
    return {
        "indices": {"SPY": 450.0, "QQQ": 380.0},
        "volatility": 0.20,
        "volume": 1000000
    }


def calculate_market_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate market metrics"""
    return {
        "market_cap": 2500000000,
        "pe_ratio": 18.5,
        "dividend_yield": 0.018
    }


def analyze_sectors(data: Dict[str, Any], sector: Optional[str]) -> Dict[str, Any]:
    """Analyze sector performance"""
    return {
        "technology": 0.15,
        "healthcare": 0.08,
        "financials": 0.05
    }


def calculate_sentiment_indicators(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate sentiment indicators"""
    return {
        "fear_greed_index": 65,
        "vix": 18.5,
        "put_call_ratio": 0.8
    }


def identify_market_trends(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify market trends"""
    return [
        {"trend": "bullish", "strength": 0.7, "duration": "3M"},
        {"trend": "consolidation", "strength": 0.5, "duration": "1M"}
    ]


def calculate_allocation_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate allocation metrics"""
    return {
        "diversification_ratio": 0.85,
        "concentration_risk": 0.15,
        "geographic_exposure": {"US": 0.6, "Asia": 0.25, "Europe": 0.15}
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 