"""Tests for the Language Agent (LangGraph workflow) with Gemini."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

# Skip tests if Gemini API key is not available
@pytest.fixture(autouse=True)
def mock_gemini_api():
    """Mock Gemini API calls for testing."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
        with patch("agents.language.gemini_client.genai.GenerativeModel") as mock_model:
            mock_response = Mock()
            mock_response.text = "Test AI response with portfolio insights"
            mock_model.return_value.generate_content.return_value = mock_response
            yield mock_model


class TestLanguageAgent:
    """Test cases for the Language Agent."""
    
    def test_language_agent_initialization(self, mock_gemini_api):
        """Test Language Agent can be initialized."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        
        assert agent.llm_provider == "gemini"
        assert agent.model_name == "gemini-1.5-flash"
        assert agent.workflow is not None

    def test_process_query_integration(self, mock_gemini_api):
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

    def test_workflow_nodes_execution(self, mock_gemini_api):
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

    def test_analytics_node(self, mock_gemini_api):
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

    def test_error_handling(self, mock_gemini_api):
        """Test error handling in workflow."""
        from agents.language.workflow import FinanceLanguageAgent
        from langchain_core.messages import HumanMessage
        
        agent = FinanceLanguageAgent()
        
        # Test retriever node with error
        with patch("agents.language.workflow.vector_query", side_effect=Exception("Test error")):
            initial_state = [HumanMessage(content="test query")]
            result = agent._retriever_node(initial_state)
            
            assert "Error in retrieval" in result[1].content

    def test_format_retrieval_results(self, mock_gemini_api):
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

    def test_format_analytics_results(self, mock_gemini_api):
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

    def test_get_language_agent_singleton(self, mock_gemini_api):
        """Test singleton pattern for language agent."""
        from agents.language.workflow import get_language_agent
        
        agent1 = get_language_agent()
        agent2 = get_language_agent()
        
        assert agent1 is agent2  # Same instance

    def test_workflow_stats(self, mock_gemini_api):
        """Test workflow statistics."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        stats = agent.get_workflow_stats()
        
        assert stats["llm_provider"] == "gemini"
        assert stats["model_name"] == "gemini-1.5-flash"
        assert "retriever" in stats["workflow_nodes"]
        assert "analytics" in stats["workflow_nodes"]
        assert "synthesize" in stats["workflow_nodes"]

    def test_invalid_llm_provider(self):
        """Test initialization with invalid LLM provider."""
        from agents.language.workflow import FinanceLanguageAgent
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            FinanceLanguageAgent(llm_provider="invalid_provider")

    def test_missing_gemini_key(self):
        """Test initialization without Gemini API key."""
        from agents.language.workflow import FinanceLanguageAgent
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable is required"):
                FinanceLanguageAgent()

    def test_workflow_compilation(self, mock_gemini_api):
        """Test that the workflow compiles successfully."""
        from agents.language.workflow import FinanceLanguageAgent
        
        agent = FinanceLanguageAgent()
        
        # Check that workflow is compiled and has expected structure
        assert agent.workflow is not None
        
        # Basic workflow introspection
        assert hasattr(agent.workflow, 'invoke')

    def test_message_graph_flow(self, mock_gemini_api):
        """Test the message graph workflow execution."""
        from agents.language.workflow import FinanceLanguageAgent
        from langchain_core.messages import HumanMessage
        
        agent = FinanceLanguageAgent()
        
        with patch("agents.language.workflow.vector_query") as mock_vector:
            with patch("agents.language.workflow.get_portfolio_value") as mock_portfolio:
                with patch("agents.language.workflow.get_risk_exposure") as mock_risk:
                    with patch("agents.language.workflow.chat_completion") as mock_chat:
                        
                        # Setup mocks
                        mock_vector.return_value = [
                            ({"text": "Test document", "source": "test.txt"}, 0.9)
                        ]
                        mock_portfolio.return_value = {"total_value": 26500.0}
                        mock_risk.return_value = {"risk_level": "moderate"}
                        mock_chat.return_value = "Portfolio: $26,500. Asia-Tech exposure is moderate."
                        
                        # Test workflow execution
                        query = "What's my portfolio status?"
                        response = agent.process_query(query)
                        
                        assert isinstance(response, str)
                        assert len(response) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 