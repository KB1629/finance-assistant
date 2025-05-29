"""
Finance Assistant - Cloud-Ready Finance Analytics

This Streamlit app provides:
- Real-time portfolio analytics  
- Market data retrieval
- AI-powered financial analysis
- Text query input

Voice features are available in local deployment only.
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
import time

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("streamlit_app")

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core finance modules
try:
    from agents.analytics.portfolio import get_portfolio_value, get_risk_exposure, get_positions
    PORTFOLIO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Portfolio analytics unavailable: {e}")
    PORTFOLIO_AVAILABLE = False

# Voice processing (optional - local deployment only)
try:
    from agents.voice.speech_processor import transcribe_audio, synthesize_speech_edge, record_and_transcribe
    VOICE_AVAILABLE = True
    VOICE_METHOD = "system"
except ImportError as e:
    logger.warning(f"System voice features unavailable: {e}")
    VOICE_AVAILABLE = False
    VOICE_METHOD = "none"
    # Create dummy functions for compatibility
    def transcribe_audio(audio_data):
        return "Voice transcription unavailable in cloud deployment"
    def synthesize_speech_edge(text, voice="female"):
        return None
    def record_and_transcribe():
        return "Voice features unavailable in cloud deployment"

# AI workflow (optional)
try:
    from agents.language.workflow import process_finance_query
    AI_WORKFLOW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI workflow unavailable: {e}")
    AI_WORKFLOW_AVAILABLE = False
    def process_finance_query(query):
        return "AI analysis temporarily unavailable. Please check back later."

# Vector store (optional)
try:
    from agents.retriever.vector_store import query as vector_query
    VECTOR_STORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vector store unavailable: {e}")
    VECTOR_STORE_AVAILABLE = False
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
    
    # Use pre-configured API key for public deployment
    if 'gemini_api_key' not in st.session_state:
        # Check if API key is pre-configured
        env_key = ""
        
        # Check Streamlit secrets first (for Cloud deployment)
        try:
            env_key = st.secrets["GEMINI_API_KEY"]
        except:
            # Fallback to environment variable
            env_key = os.getenv("GEMINI_API_KEY", "")
        
        st.session_state.gemini_api_key = env_key

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
            
            welcome_msg = f"""Welcome to the AI Finance Assistant! 
            This demo portfolio is worth ${total_value:,.0f} across {holdings_count} positions. 
            Asia tech exposure is {asia_pct:.1f}%, which is {exposure_status}. 
            Ask me anything about financial analysis, market trends, or portfolio insights!"""
            
            return welcome_msg
        else:
            return "Welcome to the AI Finance Assistant! I'm ready to help with financial analysis, market insights, and portfolio management. Ask me anything!"
    except Exception:
        return "Welcome to the AI Finance Assistant! I'm ready to help with financial analysis, market insights, and portfolio management. Ask me anything!"

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
    """Display the application header with real-time clock."""
    # Real-time clock
    current_time = datetime.now()
    time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("📊 Finance Assistant")
        st.markdown("**Real-Time Portfolio Analytics & Market Insights**")
    
    with col2:
        st.metric("🕒 Current Time", time_str)
        # Auto-refresh every 30 seconds
        time.sleep(0.1)
        if st.button("🔄 Refresh", key="refresh_time"):
            st.rerun()
    
    # Welcome briefing button
    st.markdown("---")
    if st.button("📊 Portfolio Overview", type="primary", help="Get current portfolio analysis"):
        if PORTFOLIO_AVAILABLE:
            try:
                welcome_text = create_welcome_message()
                st.success(f"📈 {welcome_text}")
                
                # Only try TTS if voice is available (local deployment)
                if VOICE_AVAILABLE and VOICE_METHOD == "system":
                    audio_data = play_web_compatible_tts(welcome_text, "welcome_auto")
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3", autoplay=True)
            except Exception as e:
                st.error(f"Error generating portfolio overview: {e}")
        else:
            st.warning("Portfolio analytics temporarily unavailable")
    
    st.markdown("---")

def display_sidebar():
    """Display the application sidebar."""
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Check if API key is pre-configured
        env_key = ""
        
        # Check Streamlit secrets first (for Cloud deployment)
        try:
            env_key = st.secrets["GEMINI_API_KEY"]
        except:
            # Fallback to environment variable
            env_key = os.getenv("GEMINI_API_KEY", "")
        
        if env_key:
            # Show that API is pre-configured for public use
            st.success("✅ API Key Pre-configured")
            st.info("🎉 Ready to use! No setup required.")
            st.session_state.gemini_api_key = env_key
            os.environ["GEMINI_API_KEY"] = env_key
        else:
            # Show API key input for manual configuration
            st.subheader("🔑 API Configuration")
            api_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.gemini_api_key,
                type="password",
                help="Enter your Google Gemini API key"
            )
            
            if api_key:
                st.session_state.gemini_api_key = api_key
                os.environ["GEMINI_API_KEY"] = api_key
                st.success("✅ API Key Configured")
            else:
                st.warning("⚠️ API key required for AI analysis")
        
        st.markdown("---")
        
        # System Status
        st.subheader("📊 System Status")
        
        # API Status
        if st.session_state.gemini_api_key:
            st.success("🤖 AI Analysis: Ready")
        else:
            st.error("🤖 AI Analysis: No API Key")
        
        # Portfolio Status
        if PORTFOLIO_AVAILABLE:
            st.success("📈 Portfolio Analytics: Active")
        else:
            st.error("📈 Portfolio Analytics: Unavailable")
        
        # Voice Status
        if VOICE_AVAILABLE and VOICE_METHOD == "system":
            st.success("🎤 Voice Input: Local Only")
        else:
            st.info("💬 Text Input: Available")
        
        # Deployment Status
        if env_key:
            st.info("☁️ Cloud Deployment: Public")
        else:
            st.info("🏠 Local Deployment: Private")
        
        st.markdown("---")
        
        # Quick Stats
        if PORTFOLIO_AVAILABLE:
            try:
                portfolio_data = get_portfolio_value()
                if "error" not in portfolio_data:
                    total_value = portfolio_data.get('total_value', 0)
                    st.metric("💰 Portfolio Value", f"${total_value:,.2f}")
                    
                    positions_count = portfolio_data.get('positions_count', 0)
                    st.metric("📊 Positions", f"{positions_count}")
            except Exception as e:
                st.warning("Quick stats temporarily unavailable")

def process_voice_input():
    """Handle voice input processing."""
    st.subheader("🎤 Voice Input")
    
    if VOICE_AVAILABLE and VOICE_METHOD == "system":
        # System-based voice recording (local deployment only)
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🎙️ Start Recording", key="voice_button"):
                with st.spinner("🎧 Recording for 8 seconds..."):
                    try:
                        transcribed_text = record_and_transcribe()
                        
                        if transcribed_text and not transcribed_text.startswith("Error") and transcribed_text.strip() != "..." and len(transcribed_text.strip()) > 3:
                            st.success(f"🎙️ **Transcribed:** {transcribed_text}")
                            
                            # Process the query
                            with st.spinner("🤖 Analyzing your request..."):
                                response = process_finance_query(transcribed_text)
                                
                                # Add to chat history
                                st.session_state.chat_history.append({
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "query": transcribed_text,
                                    "response": response,
                                    "type": "voice"
                                })
                                
                                # Display response
                                st.markdown("### 🤖 AI Response")
                                st.markdown(response)
                                
                                # Audio response
                                if st.session_state.voice_enabled:
                                    with st.spinner("🗣️ Generating audio response..."):
                                        audio_content = synthesize_speech_edge(response, voice="female")
                                        if audio_content:
                                            st.audio(audio_content, format="audio/mp3")
                                            logger.info("Edge TTS audio generated successfully")
                        else:
                            st.warning("⚠️ Could not understand the audio. Please try again or speak more clearly.")
                            
                    except Exception as e:
                        st.error(f"❌ Error in voice recording: {str(e)}")
                        logger.error(f"Voice recording error: {e}")
        
        with col2:
            # File upload option
            uploaded_file = st.file_uploader("📁 Upload Audio File", type=['wav', 'mp3', 'm4a'])
            if uploaded_file is not None:
                with st.spinner("🔄 Processing uploaded audio..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_file_path = tmp_file.name
                        
                        # Transcribe the uploaded audio
                        transcribed_text = transcribe_audio(tmp_file_path)
                        
                        # Clean up
                        os.unlink(tmp_file_path)
                        
                        if transcribed_text and len(transcribed_text.strip()) > 3:
                            st.success(f"🎙️ **Transcribed:** {transcribed_text}")
                            
                            # Process the query
                            with st.spinner("🤖 Analyzing your request..."):
                                response = process_finance_query(transcribed_text)
                                
                                # Add to chat history
                                st.session_state.chat_history.append({
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "query": transcribed_text,
                                    "response": response,
                                    "type": "voice"
                                })
                                
                                # Display response
                                st.markdown("### 🤖 AI Response")
                                st.markdown(response)
                                
                                # Audio response
                                if st.session_state.voice_enabled:
                                    with st.spinner("🗣️ Generating audio response..."):
                                        audio_content = synthesize_speech_edge(response, voice="female")
                                        if audio_content:
                                            st.audio(audio_content, format="audio/mp3")
                                            logger.info("Edge TTS audio generated successfully")
                        else:
                            st.warning("⚠️ Could not transcribe the uploaded audio. Please try a different file.")
                            
                    except Exception as e:
                        st.error(f"❌ Error processing uploaded audio: {str(e)}")
                        logger.error(f"Audio upload processing error: {e}")
    else:
        # Cloud deployment - voice features disabled
        st.info("💬 **Voice features are disabled in cloud deployment for stability**")
        st.markdown("""
        **Note:** Voice recording requires system-level audio access that's not available in cloud environments.
        
        **💡 Use Text Input below** for full functionality:
        - ✅ Portfolio analysis 
        - ✅ Market insights
        - ✅ AI-powered responses
        - ✅ Real-time data
        - ✅ Pre-built query options
        """)
        
        # Show text input redirect
        st.markdown("👇 **Use the Text Input section below for all queries**")

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
    # Set page config
    st.set_page_config(
        page_title="Finance Assistant",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    display_header()
    display_sidebar()
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬 Chat Query", 
        "📊 Analytics", 
        "💼 Portfolio",
        "📈 History"
    ])
    
    with tab1:
        # Text Input (always available)
        st.subheader("💬 Ask Questions About Your Portfolio")
        
        # Text query input
        text_query = process_text_input()
        
        # Voice input (local only)
        if VOICE_AVAILABLE and VOICE_METHOD == "system":
            st.markdown("---")
            st.subheader("🎤 Voice Input (Local Only)")
            voice_query = process_voice_input()
            
            # Use voice query if provided
            if voice_query:
                text_query = voice_query
        else:
            st.info("🎤 Voice input available in local deployment only")
        
        # Process query if provided
        if text_query:
            if not st.session_state.gemini_api_key:
                st.error("❌ Please provide Gemini API Key in the sidebar to process queries")
            else:
                with st.spinner("🧠 Processing your query..."):
                    try:
                        if AI_WORKFLOW_AVAILABLE:
                            response = process_finance_query(text_query)
                        else:
                            response = "AI analysis temporarily unavailable. Please check back later."
                        display_response(text_query, response)
                    except Exception as e:
                        st.error(f"Processing error: {e}")
                        logger.error(f"Query processing error: {e}")
    
    with tab2:
        display_analytics_dashboard()
    
    with tab3:
        display_full_portfolio()
    
    with tab4:
        display_chat_history()
    
    # Status footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕒 {current_time}")
    
    with col2:
        if st.session_state.gemini_api_key:
            st.success("🤖 AI Ready")
        else:
            st.error("🤖 API Key Required")
    
    with col3:
        if PORTFOLIO_AVAILABLE:
            st.success("📊 Analytics Active")
        else:
            st.error("📊 Analytics Error")


if __name__ == "__main__":
    main() 