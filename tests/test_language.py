"""Tests for the Language Agent (LangGraph workflow)."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

# Skip tests if OpenAI API key is not available
@pytest.fixture(autouse=True)
def mock_openai_api():
    """Mock OpenAI API calls for testing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        with patch("agents.language.workflow.ChatOpenAI") as mock_llm:
            mock_response = Mock()
            mock_response.content = "Test AI response with portfolio insights"
            mock_llm.return_value.invoke.return_value = mock_response
            yield mock_llm


class TestLanguageAgent:
    """Test cases for the Language Agent."""
    
    def test_language_agent_initialization(self, mock_openai_api):
        """Test Language Agent can be initialized."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        
        assert agent.llm_provider == "openai"
        assert agent.model_name == "gpt-4o-mini"
        assert agent.workflow is not None

    def test_process_query_integration(self, mock_openai_api):
        """Test complete query processing workflow."""
        from agents.language.workflow import process_finance_query
        
        # Mock the agent dependencies
        with patch("agents.language.workflow.vector_query") as mock_vector:
            with patch("agents.language.workflow.get_portfolio_value") as mock_portfolio:
                with patch("agents.language.workflow.get_risk_exposure") as mock_risk:
                    
                    # Setup mocks
                    mock_vector.return_value = [
                        ({"text": "Fed interest rates discussion", "source": "fed.txt"}, 0.85),
                        ({"text": "Market volatility analysis", "source": "market.txt"}, 0.78)
                    ]
                    
                    mock_portfolio.return_value = {
                        "total_value": 26500.0,
                        "asia_tech": {"percentage": 26.42, "change_from_previous": 2.5},
                        "holdings": [{"symbol": "AAPL", "value": 15000}],
                        "earnings_surprises": [{"symbol": "AAPL", "surprise_percentage": 5.2}]
                    }
                    
                    mock_risk.return_value = {"risk_level": "moderate"}
                    
                    # Test query processing
                    query = "What's my portfolio performance?"
                    response = process_finance_query(query)
                    
                    # Verify response is generated
                    assert isinstance(response, str)
                    assert len(response) > 0
                    assert "error" not in response.lower() or "Error" not in response

    def test_workflow_nodes_execution(self, mock_openai_api):
        """Test individual workflow nodes."""
        from agents.language.workflow import FinanceLanguageAgent
        from langchain_core.messages import HumanMessage, AIMessage
        
        agent = FinanceLanguageAgent()
        
        # Test retriever node
        with patch("agents.language.workflow.vector_query") as mock_vector:
            mock_vector.return_value = [
                ({"text": "Test document", "source": "test.txt"}, 0.9)
            ]
            
            initial_state = [HumanMessage(content="test query")]
            result = agent._retriever_node(initial_state)
            
            assert len(result) == 2
            assert isinstance(result[1], AIMessage)
            assert "RETRIEVAL_RESULTS:" in result[1].content

    def test_analytics_node(self, mock_openai_api):
        """Test analytics node functionality."""
        from agents.language.workflow import FinanceLanguageAgent
        from langchain_core.messages import HumanMessage
        
        agent = FinanceLanguageAgent()
        
        with patch("agents.language.workflow.get_portfolio_value") as mock_portfolio:
            with patch("agents.language.workflow.get_risk_exposure") as mock_risk:
                
                mock_portfolio.return_value = {"total_value": 26500.0}
                mock_risk.return_value = {"risk_level": "moderate"}
                
                initial_state = [HumanMessage(content="test query")]
                result = agent._analytics_node(initial_state)
                
                assert len(result) == 2
                assert "ANALYTICS_RESULTS:" in result[1].content

    def test_error_handling(self, mock_openai_api):
        """Test error handling in workflow."""
        from agents.language.workflow import FinanceLanguageAgent
        from langchain_core.messages import HumanMessage
        
        agent = FinanceLanguageAgent()
        
        # Test retriever node with error
        with patch("agents.language.workflow.vector_query", side_effect=Exception("Test error")):
            initial_state = [HumanMessage(content="test query")]
            result = agent._retriever_node(initial_state)
            
            assert "Error in retrieval" in result[1].content

    def test_format_retrieval_results(self, mock_openai_api):
        """Test retrieval results formatting."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        
        # Test with results
        results = [
            ({"text": "Long text " * 50, "source": "doc1.txt"}, 0.9),
            ({"text": "Another document", "source": "doc2.txt"}, 0.8)
        ]
        
        formatted = agent._format_retrieval_results(results)
        assert "[doc1.txt]" in formatted
        assert "[doc2.txt]" in formatted
        assert len(formatted) > 0
        
        # Test with no results
        formatted_empty = agent._format_retrieval_results([])
        assert "No relevant documents found" in formatted_empty

    def test_format_analytics_results(self, mock_openai_api):
        """Test analytics results formatting."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        
        # Test with valid data
        portfolio_data = {
            "total_value": 26500.0,
            "asia_tech": {"percentage": 26.42, "change_from_previous": 2.5},
            "earnings_surprises": [{"symbol": "AAPL", "surprise_percentage": 5.2}]
        }
        risk_data = {"risk_level": "moderate"}
        
        formatted = agent._format_analytics_results(portfolio_data, risk_data)
        assert "$26,500" in formatted
        assert "26.4%" in formatted
        assert "AAPL" in formatted
        
        # Test with error
        error_data = {"error": "Portfolio unavailable"}
        formatted_error = agent._format_analytics_results(error_data, risk_data)
        assert "Portfolio data unavailable" in formatted_error

    def test_get_language_agent_singleton(self, mock_openai_api):
        """Test singleton pattern for language agent."""
        from agents.language.workflow import get_language_agent
        
        agent1 = get_language_agent()
        agent2 = get_language_agent()
        
        assert agent1 is agent2  # Same instance

    def test_workflow_stats(self, mock_openai_api):
        """Test workflow statistics."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        stats = agent.get_workflow_stats()
        
        assert stats["llm_provider"] == "openai"
        assert stats["model_name"] == "gpt-4o-mini"
        assert "retriever" in stats["workflow_nodes"]
        assert "analytics" in stats["workflow_nodes"]
        assert "synthesize" in stats["workflow_nodes"]

    def test_invalid_llm_provider(self):
        """Test initialization with invalid LLM provider."""
        from agents.language.workflow import FinanceLanguageAgent
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            FinanceLanguageAgent(llm_provider="invalid_provider")

    def test_missing_openai_key(self):
        """Test initialization without OpenAI API key."""
        from agents.language.workflow import FinanceLanguageAgent
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                FinanceLanguageAgent()


class TestLangGraphIntegration:
    """Test LangGraph integration specifically."""
    
    def test_workflow_compilation(self, mock_openai_api):
        """Test that workflow compiles correctly."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        
        # Workflow should be compiled and ready
        assert agent.workflow is not None
        assert hasattr(agent.workflow, 'invoke')

    def test_message_graph_flow(self, mock_openai_api):
        """Test message flow through the graph."""
        from agents.language.workflow import FinanceLanguageAgent
        from langchain_core.messages import HumanMessage
        
        agent = FinanceLanguageAgent()
        
        with patch("agents.language.workflow.vector_query") as mock_vector:
            with patch("agents.language.workflow.get_portfolio_value") as mock_portfolio:
                with patch("agents.language.workflow.get_risk_exposure") as mock_risk:
                    
                    mock_vector.return_value = [({"text": "test", "source": "test.txt"}, 0.9)]
                    mock_portfolio.return_value = {"total_value": 26500.0}
                    mock_risk.return_value = {"risk_level": "moderate"}
                    
                    # Should not raise exception
                    result = agent.workflow.invoke([HumanMessage(content="test query")])
                    
                    assert isinstance(result, list)
                    assert len(result) >= 1


if __name__ == "__main__":
    pytest.main([__file__]) 