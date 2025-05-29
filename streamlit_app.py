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
import base64

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging early
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("streamlit_app")

from agents.language.workflow import process_finance_query

# Voice processing (optional for cloud deployment - Python 3.13 compatibility)
try:
    from agents.voice.speech_processor import transcribe_audio, synthesize_speech_edge, record_and_transcribe
    VOICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Voice features unavailable due to import error: {e}")
    VOICE_AVAILABLE = False
    # Create dummy functions for compatibility
    def transcribe_audio(audio_data):
        return "Voice transcription unavailable in cloud deployment"
    def synthesize_speech_edge(text, voice="female"):
        return None
    def record_and_transcribe(timeout=8.0):
        return "Voice recording unavailable in cloud deployment"

from agents.analytics.portfolio import get_portfolio_value, get_risk_exposure

# Vector search (optional - FAISS may not be available in cloud)
try:
    from agents.retriever.vector_store import query as vector_query
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False
    def vector_query(query, k=3):
        return []

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
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

def create_welcome_message():
    """Generate a welcome message with portfolio insights."""
    try:
        portfolio_data = get_portfolio_value()
        if "error" not in portfolio_data:
            total_value = portfolio_data.get('total_value', 0)
            asia_tech = portfolio_data.get('asia_tech', {})
            asia_pct = asia_tech.get('percentage', 0)
            holdings_count = portfolio_data.get('positions_count', 0)
            
            # Determine if Asia tech exposure is high/low
            if asia_pct > 15:
                exposure_status = "high"
            elif asia_pct < 5:
                exposure_status = "low"  
            else:
                exposure_status = "moderate"
            
            welcome_msg = f"""Welcome to your Finance Assistant! 
            Your portfolio is worth ${total_value:,.0f} across {holdings_count} positions. 
            Your Asia tech exposure is {asia_pct:.1f}%, which is {exposure_status}. 
            I'm ready to help with your financial analysis."""
            
            return welcome_msg
        else:
            return "Welcome to your Finance Assistant! I'm ready to help with your financial analysis."
    except Exception:
        return "Welcome to your Finance Assistant! I'm ready to help with your financial analysis."

def play_web_compatible_tts(text: str, element_id: str = "tts_audio"):
    """Play TTS using simple, reliable method."""
    
    # Clean text
    clean_text = text.replace('"', '\\"').replace("'", "\\'").replace('\n', ' ').replace('\r', ' ')
    clean_text = ' '.join(clean_text.split())
    
    # Limit text length
    if len(clean_text) > 500:
        clean_text = clean_text[:500] + "..."
    
    # Try Edge TTS first
    try:
        import tempfile
        import base64
        import edge_tts
        import asyncio
        
        async def generate_audio():
            communicate = edge_tts.Communicate(clean_text, "en-US-AriaNeural")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_path = tmp_file.name
            await communicate.save(tmp_path)
            return tmp_path
        
        # Generate audio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        audio_path = loop.run_until_complete(generate_audio())
        
        # Read audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Clean up
        os.unlink(audio_path)
        
        logger.info("Edge TTS audio generated successfully")
        return audio_data
        
    except Exception as e:
        logger.warning(f"Edge TTS failed: {e}")
        return None

def display_welcome_greeting():
    """Display and play welcome greeting - now manual only."""
    try:
        welcome_text = create_welcome_message()
        
        # Show welcome message
        st.success(f"🎉 {welcome_text}")
        
        # Play welcome audio without showing any media controls
        try:
            audio_data = play_web_compatible_tts(welcome_text, "welcome_auto")
            if audio_data:
                # Use HTML to create a hidden audio element that autoplays
                audio_bytes = base64.b64encode(audio_data).decode()
                audio_html = f"""
                <audio autoplay style="display:none;">
                    <source src="data:audio/mp3;base64,{audio_bytes}" type="audio/mp3">
                </audio>
                <div>🔊 Playing welcome briefing...</div>
                """
                st.components.v1.html(audio_html, height=30)
            else:
                st.warning("🔊 Audio generation failed")
                st.info("💡 **Text version:** " + welcome_text)
        except Exception as e:
            logger.warning(f"Welcome TTS failed: {e}")
            st.warning(f"🔊 Welcome audio error: {e}")
            st.info("💡 **Text version:** " + welcome_text)
            
    except Exception as e:
        logger.error(f"Welcome greeting error: {e}")
        st.error(f"Welcome greeting error: {e}")
        # Fallback welcome message
        fallback_msg = "Welcome to your Finance Assistant! I'm ready to help with your financial analysis."
        st.success(f"🎉 {fallback_msg}")
        try:
            audio_data = play_web_compatible_tts(fallback_msg, "welcome_fallback")
            if audio_data:
                # Use HTML to create a hidden audio element that autoplays
                audio_bytes = base64.b64encode(audio_data).decode()
                audio_html = f"""
                <audio autoplay style="display:none;">
                    <source src="data:audio/mp3;base64,{audio_bytes}" type="audio/mp3">
                </audio>
                """
                st.components.v1.html(audio_html, height=0)
        except:
            pass

def display_header():
    """Display the application header."""
    # Title
    st.title("🎤 Finance Assistant")
    st.markdown("**Voice-Enabled Morning Market Brief - Speak Clearly for Best Results**")
    
    # Welcome briefing button directly below title - much closer
    if st.button("🔊 Welcome Briefing", type="secondary", help="Portfolio briefing with voice"):
        try:
            welcome_text = create_welcome_message()
            st.success(f"🎉 {welcome_text}")
            
            # Auto-generate and play audio without showing controls
            audio_data = play_web_compatible_tts(welcome_text, "welcome_auto")
            if audio_data:
                # Use HTML to create a hidden audio element that autoplays
                audio_bytes = base64.b64encode(audio_data).decode()
                audio_html = f"""
                <audio autoplay style="display:none;">
                    <source src="data:audio/mp3;base64,{audio_bytes}" type="audio/mp3">
                </audio>
                <div>🔊 Playing welcome briefing...</div>
                """
                st.components.v1.html(audio_html, height=30)
            else:
                st.warning("🔊 Audio generation failed")
        except Exception as e:
            st.error(f"Welcome briefing error: {e}")
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.gemini_api_key:
            st.success("✅ Gemini AI Connected")
        else:
            st.error("❌ Gemini API Key Required")
    
    with col2:
        if VOICE_AVAILABLE:
            st.success("✅ Voice Ready")
        else:
            st.warning("⚠️ Voice Processing Limited")
    
    with col3:
        # Show time with seconds to indicate it's working
        st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

def display_sidebar():
    """Display the application sidebar."""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.gemini_api_key,
            type="password",
            help="Required for AI processing"
        )
        if api_key != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = api_key
            os.environ["GEMINI_API_KEY"] = api_key
        
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
                asia_pct = asia_tech.get('percentage', 0)
                asia_change = asia_tech.get('change_from_previous', 0)
                # Only show delta if change_from_previous is not None
                if asia_change is not None:
                    st.metric(
                        "Asia-Tech Exposure",
                        f"{asia_pct:.1f}%",
                        delta=f"{asia_change:.1f}%"
                    )
                else:
                    st.metric(
                        "Asia-Tech Exposure",
                        f"{asia_pct:.1f}%"
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
        st.text("Female Voice: Edge TTS")

def process_voice_input():
    """Handle voice input processing."""
    st.subheader("🎤 Voice Input")
    
    # Check if voice is available
    if not VOICE_AVAILABLE:
        st.info("🔊 **Voice features unavailable in cloud deployment**")
        st.markdown("""
        Voice transcription requires system audio libraries that are not available in cloud deployment.
        Please use **Text Input** tab instead.
        """)
        return None
    
    tab1, tab2 = st.tabs(["📱 Record", "📁 Upload File"])
    
    with tab1:
        st.write("**Click to record your question:**")
        
        # Simple recording interface
        if st.button("🎤 Start Recording", type="primary", key="mic_button", help="8-second recording"):
            if not st.session_state.gemini_api_key:
                st.error("Please provide Gemini API Key in sidebar")
                return None
            
            with st.spinner("🎧 Recording for 8 seconds..."):
                try:
                    transcribed_text = record_and_transcribe(timeout=8.0)
                    
                    if transcribed_text and not transcribed_text.startswith("Error") and transcribed_text.strip() != "..." and len(transcribed_text.strip()) > 3:
                        st.success(f"✅ **Transcribed:** {transcribed_text}")
                        return transcribed_text
                    else:
                        st.warning(f"⚠️ **Poor quality transcription:** {transcribed_text}")
                        st.info("💡 Try speaking louder and clearer, closer to microphone")
                        
                except Exception as e:
                    st.error(f"❌ Recording error: {e}")
    
    with tab2:
        st.write("Upload an audio file:")
        
        uploaded_file = st.file_uploader(
            "Choose audio file",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Supported formats: WAV, MP3, M4A, FLAC"
        )
        
        if uploaded_file is not None:
            if not st.session_state.gemini_api_key:
                st.error("Please provide Gemini API Key in sidebar")
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
                        st.error(f"❌ File processing failed: {transcribed_text}")
                        
                except Exception as e:
                    st.error(f"❌ File processing error: {e}")
    
    return None

def process_text_input():
    """Handle text input processing."""
    st.subheader("✍️ Text Input")
    
    # Quick queries dropdown
    st.write("**Quick queries:**")
    
    # Comprehensive list of financial queries that work well with the system
    query_options = [
        "Select a quick query...",
        # Portfolio Analysis
        "What's my portfolio performance today?",
        "Show me Asia tech exposure breakdown",
        "What's my total portfolio value?",
        "Which region has the highest allocation?",
        "What's my risk exposure analysis?",
        
        # Earnings & Market Data
        "Any earnings surprises today?",
        "Show me recent earnings beats and misses",
        "Which stocks beat earnings estimates?",
        "What are the market trends today?",
        
        # Specific Stock Queries
        "How is TSMC performing today?",
        "Tell me about Alibaba (BABA) stock",
        "How are my Indian stocks doing?",
        "What's the performance of ITC stock?",
        "Give me TCS stock analysis",
        "How is Reliance performing?",
        
        # Risk & Strategy
        "What's our risk exposure in Asia tech stocks?",
        "Should I rebalance my portfolio?",
        "Which stocks are underperforming?",
        "What's the best performing stock today?",
        
        # Market Brief (Main Use Case)
        "Give me a morning market brief",
        "What's happening in Asian markets?",
        "Summarize today's portfolio performance",
        "Any important market news for my holdings?"
    ]
    
    # Initialize session state for selected query
    if 'selected_quick_query' not in st.session_state:
        st.session_state.selected_quick_query = query_options[0]
    
    # Dropdown selection
    selected_option = st.selectbox(
        "Choose a pre-built query:",
        query_options,
        index=0,
        help="Select from common financial queries or type your own below"
    )
    
    # Update session state and text area when selection changes
    query_text = ""
    if selected_option != query_options[0]:  # Not the default "Select..."
        query_text = selected_option
        st.session_state.selected_quick_query = selected_option
    
    # Text input area
    user_query = st.text_area(
        "Your question:",
        value=query_text,
        height=100,
        placeholder="Ask about your portfolio, market conditions, earnings, or any financial topic...",
        help="You can select from the dropdown above or type your own question"
    )
    
    # Submit button
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

def display_full_portfolio():
    """Display detailed portfolio breakdown with all stocks."""
    st.subheader("🧮 Complete Portfolio Breakdown")
    
    try:
        # Get portfolio data
        portfolio_data = get_portfolio_value()
        
        if "error" in portfolio_data:
            st.error(f"Portfolio data unavailable: {portfolio_data['error']}")
            return
            
        # Check if positions data is available
        if "positions" not in portfolio_data:
            st.error("Detailed position data not available")
            return
            
        positions = portfolio_data["positions"]
        
        if not positions:
            st.warning("No positions found in portfolio")
            return
            
        # Create a DataFrame with all positions
        df = pd.DataFrame(positions)
        
        # Format currency columns
        currency_cols = ['price', 'market_value']
        for col in currency_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}")
                
        # Calculate and add performance metrics if available
        if 'previous_price' in df.columns:
            df['change'] = ((df['price'] - df['previous_price']) / df['previous_price'] * 100)
            df['change'] = df['change'].apply(lambda x: f"{x:+.2f}%" if not pd.isna(x) else "N/A")
        
        # Reorder and rename columns for display
        display_cols = ['symbol', 'shares', 'price', 'market_value', 'geo_tag']
        if 'change' in df.columns:
            display_cols.append('change')
            
        display_df = df[display_cols].rename(columns={
            'symbol': 'Symbol',
            'shares': 'Shares',
            'price': 'Price',
            'market_value': 'Value',
            'geo_tag': 'Region/Sector',
            'change': 'Change (%)'
        })
        
        # Display full portfolio table
        st.dataframe(display_df, use_container_width=True)
        
        # Summary information
        total_value = portfolio_data.get('total_value', 0)
        positions_count = len(positions)
        st.info(f"📊 Total portfolio value: ${total_value:,.2f} across {positions_count} positions")
        
    except Exception as e:
        st.error(f"Error displaying portfolio: {e}")
        logger.error(f"Portfolio display error: {e}")

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
                portfolio_data.get('positions_count', 0)
            )
        
        with col4:
            surprises = portfolio_data.get('earnings_surprises', [])
            positive_surprises = sum(1 for s in surprises if s['surprise_percentage'] > 0)
            st.metric(
                "Earnings Beats",
                f"{positive_surprises}/{len(surprises)}"
            )
        
        # "View Full Portfolio" button
        if st.button("🔍 View Full Portfolio", help="Click to see detailed breakdown of all positions"):
            display_full_portfolio()
        
        # Portfolio allocation breakdown
        if 'geo_allocation' in portfolio_data:
            st.write("**Portfolio Allocation:**")
            allocation_df = pd.DataFrame(portfolio_data['geo_allocation'])
            allocation_df['value'] = allocation_df['market_value'].apply(lambda x: f"${x:,.0f}")
            allocation_df['percentage'] = allocation_df['percentage'].apply(lambda x: f"{x:.1f}%")
            display_df = allocation_df[['geo_tag', 'value', 'percentage']].rename(columns={
                'geo_tag': 'Region/Sector',
                'value': 'Market Value',
                'percentage': 'Allocation %'
            })
            st.dataframe(display_df, use_container_width=True)
        
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
    main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs([
        "🎤 Voice Query", 
        "📊 Analytics", 
        "💼 Portfolio",
        "💬 History"
    ])
    
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
            if not st.session_state.gemini_api_key:
                st.error("❌ Please provide Gemini API Key in the sidebar to process queries")
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
        # Dedicated portfolio tab shows the full portfolio by default
        display_full_portfolio()
    
    with main_tab4:
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