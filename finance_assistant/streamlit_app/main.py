"""
Finance Assistant - Voice-Enabled Morning Market Brief

This Streamlit app provides:
- Voice query input (microphone or file upload)
- Text query input
- Real-time portfolio analytics
- Market data retrieval
- AI-powered synthesis of morning briefs
"""

import streamlit as st
import os
import sys
import logging
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.language.workflow import process_finance_query
from agents.voice.speech_processor import transcribe_audio, synthesize_speech, get_voice_processor
from agents.analytics.portfolio import get_portfolio_value, get_risk_exposure
from agents.retriever.vector_store import query as vector_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("streamlit_app")

# Streamlit page configuration
st.set_page_config(
    page_title="Finance Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'voice_enabled' not in st.session_state:
        st.session_state.voice_enabled = True
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

def display_header():
    """Display the application header."""
    st.title("🎤 Finance Assistant")
    st.markdown("**Voice-Enabled Morning Market Brief**")
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.openai_api_key:
            st.success("✅ OpenAI Connected")
        else:
            st.error("❌ OpenAI API Key Required")
    
    with col2:
        try:
            get_voice_processor()
            st.success("✅ Voice Ready")
        except Exception:
            st.warning("⚠️ Voice Processing Limited")
    
    with col3:
        st.info(f"🕐 {datetime.now().strftime('%H:%M %Z')}")

def display_sidebar():
    """Display the application sidebar."""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.openai_api_key,
            type="password",
            help="Required for AI processing"
        )
        if api_key != st.session_state.openai_api_key:
            st.session_state.openai_api_key = api_key
            os.environ["OPENAI_API_KEY"] = api_key
        
        st.divider()
        
        # Voice settings
        st.subheader("🎤 Voice Settings")
        st.session_state.voice_enabled = st.checkbox(
            "Enable Voice Input",
            value=st.session_state.voice_enabled
        )
        
        st.divider()
        
        # Portfolio quick stats
        st.subheader("📊 Portfolio Overview")
        try:
            portfolio_data = get_portfolio_value()
            if "error" not in portfolio_data:
                st.metric(
                    "Total Value",
                    f"${portfolio_data.get('total_value', 0):,.0f}"
                )
                asia_tech = portfolio_data.get('asia_tech', {})
                st.metric(
                    "Asia-Tech Exposure",
                    f"{asia_tech.get('percentage', 0):.1f}%",
                    delta=f"{asia_tech.get('change_from_previous', 0):.1f}%"
                )
            else:
                st.error("Portfolio data unavailable")
        except Exception as e:
            st.error(f"Portfolio error: {e}")
        
        st.divider()
        
        # System info
        st.subheader("ℹ️ System Info")
        st.text("Sprint 3: Voice & UI")
        st.text("LangGraph + CrewAI")
        st.text("Whisper STT + TTS")

def process_voice_input():
    """Handle voice input processing."""
    st.subheader("🎤 Voice Input")
    
    tab1, tab2 = st.tabs(["📱 Record", "📁 Upload File"])
    
    with tab1:
        st.write("Click to record your question:")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🎤 Start Recording", type="primary"):
                if not st.session_state.openai_api_key:
                    st.error("Please provide OpenAI API Key in sidebar")
                    return None
                
                with st.spinner("🎧 Listening..."):
                    try:
                        from agents.voice.speech_processor import record_and_transcribe
                        transcribed_text = record_and_transcribe(timeout=8.0)
                        
                        if transcribed_text and not transcribed_text.startswith("Error"):
                            st.success(f"📝 Transcribed: *{transcribed_text}*")
                            return transcribed_text
                        else:
                            st.error(f"❌ {transcribed_text}")
                    except Exception as e:
                        st.error(f"Recording error: {e}")
        
        with col2:
            st.info("💡 **Tips:**\n- Speak clearly\n- Ask about portfolio, markets, or earnings\n- Try: 'What's my Asia tech exposure?'")
    
    with tab2:
        st.write("Upload an audio file:")
        
        uploaded_file = st.file_uploader(
            "Choose audio file",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Supported formats: WAV, MP3, M4A, FLAC"
        )
        
        if uploaded_file is not None:
            if not st.session_state.openai_api_key:
                st.error("Please provide OpenAI API Key in sidebar")
                return None
            
            with st.spinner("🔄 Processing audio..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Transcribe
                    transcribed_text = transcribe_audio(tmp_path)
                    
                    # Clean up
                    os.unlink(tmp_path)
                    
                    if transcribed_text and not transcribed_text.startswith("Error"):
                        st.success(f"📝 Transcribed: *{transcribed_text}*")
                        return transcribed_text
                    else:
                        st.error(f"❌ {transcribed_text}")
                        
                except Exception as e:
                    st.error(f"File processing error: {e}")
    
    return None

def process_text_input():
    """Handle text input processing."""
    st.subheader("✍️ Text Input")
    
    # Suggested queries
    st.write("**Quick queries:**")
    col1, col2, col3 = st.columns(3)
    
    query_suggestions = [
        "What's my portfolio performance?",
        "Show me Asia tech exposure",
        "Any earnings surprises today?"
    ]
    
    selected_query = None
    for i, suggestion in enumerate(query_suggestions):
        col = [col1, col2, col3][i]
        if col.button(f"💡 {suggestion}", key=f"suggest_{i}"):
            selected_query = suggestion
    
    # Text input
    user_query = st.text_area(
        "Your question:",
        value=selected_query or "",
        height=100,
        placeholder="Ask about your portfolio, market conditions, earnings, or any financial topic..."
    )
    
    if st.button("🚀 Submit Query", type="primary", disabled=not user_query.strip()):
        return user_query.strip()
    
    return None

def display_response(query: str, response: str):
    """Display the AI response."""
    st.subheader("🤖 AI Response")
    
    # Add to chat history
    st.session_state.chat_history.append({
        "timestamp": datetime.now(),
        "query": query,
        "response": response
    })
    
    # Display current response
    st.markdown(f"**Query:** *{query}*")
    st.markdown(f"**Response:** {response}")
    
    # TTS option
    if st.button("🔊 Play Response", key="tts_current"):
        with st.spinner("🔄 Generating speech..."):
            tts_result = synthesize_speech(response)
            if tts_result:
                st.info(f"🔊 {tts_result}")
            else:
                st.error("TTS unavailable")

def display_chat_history():
    """Display chat history."""
    if st.session_state.chat_history:
        st.subheader("💬 Chat History")
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()
        
        # Display history in reverse order (newest first)
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):  # Last 5 only
            with st.expander(f"🕐 {chat['timestamp'].strftime('%H:%M:%S')} - {chat['query'][:50]}..."):
                st.markdown(f"**Q:** {chat['query']}")
                st.markdown(f"**A:** {chat['response']}")

def display_analytics_dashboard():
    """Display real-time analytics dashboard."""
    st.subheader("📈 Real-Time Analytics")
    
    try:
        # Get portfolio data
        portfolio_data = get_portfolio_value()
        
        if "error" in portfolio_data:
            st.error(f"Analytics unavailable: {portfolio_data['error']}")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Portfolio",
                f"${portfolio_data.get('total_value', 0):,.0f}"
            )
        
        with col2:
            asia_tech = portfolio_data.get('asia_tech', {})
            st.metric(
                "Asia-Tech %",
                f"{asia_tech.get('percentage', 0):.1f}%",
                delta=f"{asia_tech.get('change_from_previous', 0):+.1f}%"
            )
        
        with col3:
            st.metric(
                "Holdings",
                len(portfolio_data.get('holdings', []))
            )
        
        with col4:
            surprises = portfolio_data.get('earnings_surprises', [])
            positive_surprises = sum(1 for s in surprises if s['surprise_percentage'] > 0)
            st.metric(
                "Earnings Beats",
                f"{positive_surprises}/{len(surprises)}"
            )
        
        # Holdings breakdown
        if 'holdings' in portfolio_data:
            st.write("**Portfolio Holdings:**")
            holdings_df = pd.DataFrame(portfolio_data['holdings'])
            st.dataframe(holdings_df, use_container_width=True)
        
        # Earnings surprises
        if surprises:
            st.write("**Recent Earnings Surprises:**")
            surprises_df = pd.DataFrame(surprises)
            st.dataframe(surprises_df, use_container_width=True)
            
    except Exception as e:
        st.error(f"Analytics error: {e}")

def main():
    """Main application function."""
    initialize_session_state()
    display_header()
    display_sidebar()
    
    # Main content area
    main_tab1, main_tab2, main_tab3 = st.tabs(["🎤 Voice Query", "📊 Analytics", "💬 History"])
    
    with main_tab1:
        # Input section
        input_col1, input_col2 = st.columns([1, 1])
        
        query = None
        
        with input_col1:
            if st.session_state.voice_enabled:
                voice_query = process_voice_input()
                if voice_query:
                    query = voice_query
        
        with input_col2:
            text_query = process_text_input()
            if text_query:
                query = text_query
        
        # Process query if provided
        if query:
            if not st.session_state.openai_api_key:
                st.error("❌ Please provide OpenAI API Key in the sidebar to process queries")
            else:
                with st.spinner("🧠 Processing your query..."):
                    try:
                        response = process_finance_query(query)
                        display_response(query, response)
                    except Exception as e:
                        st.error(f"Processing error: {e}")
                        logger.error(f"Query processing error: {e}")
    
    with main_tab2:
        display_analytics_dashboard()
    
    with main_tab3:
        display_chat_history()
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
        Finance Assistant v0.1.0 | Sprint 3: Voice & UI | 
        Powered by LangGraph + CrewAI + Whisper + Streamlit
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 