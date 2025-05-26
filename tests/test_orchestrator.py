"""
Tests for the orchestrator service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from orchestrator.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Finance Assistant Orchestrator" in data["message"]


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "running" == data["status"]
    assert "Finance Assistant Orchestrator" in data["message"]


@patch("orchestrator.main.vector_query")
@patch("orchestrator.main.get_risk_exposure")
def test_query_endpoint(mock_risk_exposure, mock_vector_query):
    """Test query endpoint"""
    # Mock risk exposure data
    mock_risk_data = {
        "exposures": [
            {"geo_tag": "Asia-Tech", "percentage": 25.5},
            {"geo_tag": "US-Tech", "percentage": 40.2}
        ],
        "asia_tech_exposure": {
            "percentage": 25.5
        },
        "earnings_surprises": [
            {"symbol": "TSM", "surprise_percentage": 3.2, "type": "beat"},
            {"symbol": "BABA", "surprise_percentage": -2.1, "type": "miss"}
        ]
    }
    mock_risk_exposure.return_value = mock_risk_data
    
    # Mock vector query results
    mock_vector_results = [
        ({"text": "Apple reported strong earnings with revenue growth of 15%."}, 0.95),
        ({"text": "Microsoft cloud services saw increased adoption among enterprises."}, 0.85)
    ]
    mock_vector_query.return_value = mock_vector_results
    
    # Test risk exposure query
    query_data = {"text": "What's our risk exposure in Asia tech?"}
    response = client.post("/query", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Asia-Tech" in data["response"]
    assert "25.5%" in data["response"]
    mock_risk_exposure.assert_called_once_with("Asia-Tech")
    
    # Reset mocks
    mock_risk_exposure.reset_mock()
    
    # Test vector search query
    query_data = {"text": "Tell me about Apple's earnings"}
    response = client.post("/query", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "I found the following relevant information" in data["response"]
    assert "Apple reported strong earnings" in data["response"]
    mock_vector_query.assert_called_once_with("Tell me about Apple's earnings", k=3)


@patch("orchestrator.main.get_price")
def test_stock_price_endpoint(mock_get_price):
    """Test stock price endpoint"""
    # Mock the get_price function
    mock_get_price.return_value = 150.25
    
    # Test with symbol only
    request_data = {"symbol": "AAPL"}
    response = client.post("/stock/price", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["price"] == 150.25
    assert data["date"] == "latest"
    assert data["status"] == "success"
    
    # Test with symbol and date
    request_data = {"symbol": "MSFT", "date": "2023-05-01"}
    response = client.post("/stock/price", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "MSFT"
    assert data["price"] == 150.25  # Using our mocked value
    assert data["date"] == "2023-05-01"
    assert data["status"] == "success"
    
    # Test error handling
    mock_get_price.side_effect = Exception("API Error")
    response = client.post("/stock/price", json={"symbol": "INVALID"})
    assert response.status_code == 500
    assert "API Error" in response.json()["detail"]


@patch("orchestrator.main.get_earnings_surprise")
def test_earnings_endpoint(mock_get_earnings):
    """Test earnings endpoint"""
    # Mock the get_earnings_surprise function
    mock_get_earnings.return_value = 5.75
    
    # Test with symbol only
    request_data = {"symbol": "AAPL"}
    response = client.post("/stock/earnings", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["surprise_percentage"] == 5.75
    assert data["period"] == "latest"
    assert data["status"] == "success"
    
    # Test with symbol and period
    request_data = {"symbol": "MSFT", "period": "2023Q1"}
    response = client.post("/stock/earnings", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "MSFT"
    assert data["surprise_percentage"] == 5.75  # Using our mocked value
    assert data["period"] == "2023Q1"
    assert data["status"] == "success"


@patch("orchestrator.main.get_filings_for_ticker")
def test_filings_ticker_endpoint(mock_get_filings):
    """Test filings ticker endpoint"""
    # Mock the get_filings_for_ticker function
    mock_filings = [
        {"company": "Apple Inc.", "filing_type": "10-K", "filing_date": "2023-10-27"},
        {"company": "Apple Inc.", "filing_type": "10-Q", "filing_date": "2023-07-28"}
    ]
    mock_get_filings.return_value = mock_filings
    
    # Test with default count
    request_data = {"symbol": "AAPL"}
    response = client.post("/filings/ticker", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["filings"] == mock_filings
    assert data["status"] == "success"
    
    # Test with custom count
    request_data = {"symbol": "MSFT", "count": 5}
    response = client.post("/filings/ticker", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "MSFT"
    assert data["filings"] == mock_filings
    assert data["status"] == "success"


@patch("orchestrator.main.get_latest_asian_tech_filings")
def test_asian_tech_filings_endpoint(mock_get_asian_filings):
    """Test Asian tech filings endpoint"""
    # Mock the get_latest_asian_tech_filings function
    mock_filings = [
        {"company": "Taiwan Semiconductor", "filing_type": "20-F", "filing_date": "2023-04-14"},
        {"company": "Alibaba Group", "filing_type": "6-K", "filing_date": "2023-08-10"}
    ]
    mock_get_asian_filings.return_value = mock_filings
    
    # Test with default days_back
    request_data = {"days_back": 30}
    response = client.post("/filings/asian-tech", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["filings_count"] == 2
    assert data["filings"] == mock_filings
    assert data["status"] == "success"


@patch("orchestrator.main.vector_query")
def test_retriever_query_endpoint(mock_vector_query):
    """Test retriever query endpoint"""
    # Mock vector query results
    mock_results = [
        ({"text": "Apple reported strong earnings.", "source": "news"}, 0.95),
        ({"text": "Microsoft cloud services saw increased adoption.", "source": "filing"}, 0.85)
    ]
    mock_vector_query.return_value = mock_results
    
    # Test query
    request_data = {"query": "Apple earnings", "k": 2}
    response = client.post("/retriever/query", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    # Check results
    assert data["status"] == "success"
    assert len(data["results"]) == 2
    assert data["results"][0]["text"] == "Apple reported strong earnings."
    assert data["results"][0]["metadata"]["source"] == "news"
    assert data["results"][0]["score"] == 0.95
    
    # Verify mock was called correctly
    mock_vector_query.assert_called_once_with("Apple earnings", 2)


@patch("orchestrator.main.load_ticker_filings")
@patch("orchestrator.main.load_asian_tech_filings")
@patch("orchestrator.main.load_from_text_files")
def test_retriever_index_endpoint(mock_load_files, mock_load_asian, mock_load_ticker):
    """Test retriever index endpoint"""
    # Mock document loading results
    mock_docs = [{"text": "Document 1"}, {"text": "Document 2"}]
    mock_load_ticker.return_value = mock_docs
    mock_load_asian.return_value = mock_docs
    mock_load_files.return_value = mock_docs
    
    # Test ticker indexing
    request_data = {"source_type": "ticker", "ticker": "AAPL", "count": 3}
    response = client.post("/retriever/index", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["documents_indexed"] == 2
    mock_load_ticker.assert_called_once_with("AAPL", 3)
    
    # Test Asian tech indexing
    request_data = {"source_type": "asian", "days_back": 60}
    response = client.post("/retriever/index", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["documents_indexed"] == 2
    mock_load_asian.assert_called_once_with(60)
    
    # Test file indexing
    request_data = {"source_type": "file", "directory": "/path/to/files"}
    response = client.post("/retriever/index", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["documents_indexed"] == 2
    mock_load_files.assert_called_once_with("/path/to/files")
    
    # Test invalid request
    request_data = {"source_type": "invalid"}
    response = client.post("/retriever/index", json=request_data)
    assert response.status_code == 500
    assert "Invalid source type" in response.json()["detail"]


@patch("orchestrator.main.get_portfolio_value")
def test_portfolio_value_endpoint(mock_get_portfolio):
    """Test portfolio value endpoint"""
    # Mock portfolio data
    mock_portfolio = {
        "total_value": 100000.0,
        "positions_count": 10,
        "geo_allocation": [
            {"geo_tag": "Asia-Tech", "market_value": 25000.0, "percentage": 25.0},
            {"geo_tag": "US-Tech", "market_value": 40000.0, "percentage": 40.0}
        ]
    }
    mock_get_portfolio.return_value = mock_portfolio
    
    # Test endpoint
    response = client.post("/portfolio/value", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["portfolio_data"] == mock_portfolio
    mock_get_portfolio.assert_called_once()


@patch("orchestrator.main.get_risk_exposure")
def test_risk_exposure_endpoint(mock_get_risk):
    """Test risk exposure endpoint"""
    # Mock risk data
    mock_risk = {
        "exposures": [
            {"geo_tag": "Asia-Tech", "market_value": 25000.0, "percentage": 25.0}
        ],
        "asia_tech_exposure": {
            "percentage": 25.0,
            "value": 25000.0,
            "change_from_previous": 2.5
        },
        "earnings_surprises": [
            {"symbol": "TSM", "surprise_percentage": 3.2, "type": "beat"}
        ]
    }
    mock_get_risk.return_value = mock_risk
    
    # Test with no region
    response = client.post("/portfolio/risk", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["risk_data"] == mock_risk
    mock_get_risk.assert_called_once_with(None)
    
    # Reset mock
    mock_get_risk.reset_mock()
    
    # Test with region
    response = client.post("/portfolio/risk", json={"region": "Asia-Tech"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["risk_data"] == mock_risk
    mock_get_risk.assert_called_once_with("Asia-Tech") 