"""Language Agent workflow using LangGraph for finance brief synthesis."""

import os
import json
import logging
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import Graph, END
from langgraph.graph.message import MessageGraph

from agents.retriever.vector_store import query as vector_query
from agents.analytics.portfolio import get_portfolio_value, get_risk_exposure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("language.workflow")


class WorkflowState(TypedDict):
    """State for the language agent workflow."""
    query: str
    retrieval_results: List[Dict[str, Any]]
    portfolio_data: Dict[str, Any]
    risk_data: Dict[str, Any]
    final_response: str
    errors: List[str]


class FinanceLanguageAgent:
    """Language agent for synthesizing finance briefs using LangGraph."""

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4o-mini"):
        """Initialize the language agent.
        
        Args:
            llm_provider: LLM provider to use
            model_name: Model name
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        
        # Initialize LLM
        if llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=0.1,
                max_tokens=500
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        logger.info(f"Initialized Language Agent with {llm_provider}:{model_name}")

    def _create_workflow(self) -> Graph:
        """Create the LangGraph workflow for finance brief synthesis.
        
        Returns:
            Configured LangGraph workflow
        """
        # Create message graph
        workflow = MessageGraph()
        
        # Add nodes
        workflow.add_node("retriever", self._retriever_node)
        workflow.add_node("analytics", self._analytics_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Add edges
        workflow.add_edge("retriever", "analytics")
        workflow.add_edge("analytics", "synthesize")
        workflow.add_edge("synthesize", END)
        
        # Set entry point
        workflow.set_entry_point("retriever")
        
        return workflow.compile()

    def _retriever_node(self, state: List[BaseMessage]) -> List[BaseMessage]:
        """Node for retrieving relevant documents."""
        try:
            # Get the query from the last human message
            query = ""
            for msg in reversed(state):
                if isinstance(msg, HumanMessage):
                    query = msg.content
                    break
            
            if not query:
                logger.warning("No query found in messages")
                return state + [AIMessage(content="Error: No query provided")]
            
            # Perform vector search
            results = vector_query(query, k=3)
            
            # Format results for next node
            retrieval_summary = self._format_retrieval_results(results)
            
            logger.info(f"Retrieved {len(results)} documents for query: {query}")
            
            return state + [AIMessage(content=f"RETRIEVAL_RESULTS: {retrieval_summary}")]
            
        except Exception as e:
            logger.error(f"Error in retriever node: {e}")
            return state + [AIMessage(content=f"Error in retrieval: {str(e)}")]

    def _analytics_node(self, state: List[BaseMessage]) -> List[BaseMessage]:
        """Node for getting portfolio analytics."""
        try:
            # Get portfolio and risk data
            portfolio_data = get_portfolio_value()
            risk_data = get_risk_exposure()
            
            # Format analytics for synthesis
            analytics_summary = self._format_analytics_results(portfolio_data, risk_data)
            
            logger.info("Retrieved portfolio analytics")
            
            return state + [AIMessage(content=f"ANALYTICS_RESULTS: {analytics_summary}")]
            
        except Exception as e:
            logger.error(f"Error in analytics node: {e}")
            return state + [AIMessage(content=f"Error in analytics: {str(e)}")]

    def _synthesize_node(self, state: List[BaseMessage]) -> List[BaseMessage]:
        """Node for synthesizing the final response."""
        try:
            # Extract information from previous nodes
            query = ""
            retrieval_data = ""
            analytics_data = ""
            
            for msg in state:
                if isinstance(msg, HumanMessage):
                    query = msg.content
                elif isinstance(msg, AIMessage):
                    if msg.content.startswith("RETRIEVAL_RESULTS:"):
                        retrieval_data = msg.content.replace("RETRIEVAL_RESULTS: ", "")
                    elif msg.content.startswith("ANALYTICS_RESULTS:"):
                        analytics_data = msg.content.replace("ANALYTICS_RESULTS: ", "")
            
            # Create synthesis prompt
            prompt = ChatPromptTemplate.from_template("""
You are a professional financial advisor providing a morning market brief. 
Synthesize the following information into a clear, concise response (≤60 words):

Query: {query}

Portfolio Analytics: {analytics_data}

Relevant Market Information: {retrieval_data}

Provide a professional, actionable summary that directly answers the query.
Focus on key numbers, percentages, and actionable insights.
""")
            
            # Generate response using LLM
            messages = prompt.format_messages(
                query=query,
                analytics_data=analytics_data,
                retrieval_data=retrieval_data
            )
            
            response = self.llm.invoke(messages)
            final_response = response.content
            
            logger.info("Generated final synthesis response")
            
            return state + [AIMessage(content=final_response)]
            
        except Exception as e:
            logger.error(f"Error in synthesis node: {e}")
            return state + [AIMessage(content=f"Error in synthesis: {str(e)}")]

    def _format_retrieval_results(self, results: List[tuple]) -> str:
        """Format retrieval results for LLM consumption.
        
        Args:
            results: List of (document, score) tuples
            
        Returns:
            Formatted string
        """
        if not results:
            return "No relevant documents found."
        
        formatted = []
        for doc, score in results[:3]:  # Top 3 results
            text = doc.get("text", "")[:200]  # Truncate to 200 chars
            source = doc.get("source", "unknown")
            formatted.append(f"[{source}] {text}...")
        
        return " | ".join(formatted)

    def _format_analytics_results(self, portfolio_data: Dict, risk_data: Dict) -> str:
        """Format analytics results for LLM consumption.
        
        Args:
            portfolio_data: Portfolio analytics data
            risk_data: Risk exposure data
            
        Returns:
            Formatted string
        """
        if "error" in portfolio_data:
            return f"Portfolio data unavailable: {portfolio_data.get('error')}"
        
        # Extract key metrics
        total_value = portfolio_data.get("total_value", 0)
        asia_tech_pct = portfolio_data.get("asia_tech", {}).get("percentage", 0)
        asia_tech_change = portfolio_data.get("asia_tech", {}).get("change_from_previous")
        
        # Format earnings surprises
        surprises = portfolio_data.get("earnings_surprises", [])
        surprise_text = ""
        if surprises:
            top_surprises = surprises[:2]  # Top 2 surprises
            surprise_parts = []
            for s in top_surprises:
                direction = "beat" if s["surprise_percentage"] > 0 else "missed"
                surprise_parts.append(f"{s['symbol']} {direction} by {abs(s['surprise_percentage']):.1f}%")
            surprise_text = f" Earnings: {', '.join(surprise_parts)}."
        
        # Format change information
        change_text = ""
        if asia_tech_change is not None:
            direction = "up" if asia_tech_change > 0 else "down"
            change_text = f" ({direction} {abs(asia_tech_change):.1f}% from yesterday)"
        
        return f"Portfolio: ${total_value:,.0f}, Asia-Tech: {asia_tech_pct:.1f}%{change_text}.{surprise_text}"

    def process_query(self, query: str) -> str:
        """Process a finance query through the complete workflow.
        
        Args:
            query: User query
            
        Returns:
            Generated response
        """
        try:
            # Create initial message
            initial_message = HumanMessage(content=query)
            
            # Run the workflow
            result = self.workflow.invoke([initial_message])
            
            # Extract final response
            if result and len(result) > 0:
                last_message = result[-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
            
            return "Unable to generate response"
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing your request: {str(e)}"

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics.
        
        Returns:
            Dictionary with workflow stats
        """
        return {
            "llm_provider": self.llm_provider,
            "model_name": self.model_name,
            "workflow_nodes": ["retriever", "analytics", "synthesize"]
        }


# Global instance
_language_agent = None

def get_language_agent() -> FinanceLanguageAgent:
    """Get the global language agent instance.
    
    Returns:
        FinanceLanguageAgent instance
    """
    global _language_agent
    if _language_agent is None:
        _language_agent = FinanceLanguageAgent()
    return _language_agent

def process_finance_query(query: str) -> str:
    """Process a finance query using the language agent.
    
    Args:
        query: User query
        
    Returns:
        Generated response
    """
    return get_language_agent().process_query(query) 