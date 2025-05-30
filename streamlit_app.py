"""
AI Finance Studio - Streamlit Cloud Production Version
Clean, lightweight, and reliable for cloud deployment.
"""

import streamlit as st

# MUST be first - configure page
st.set_page_config(
    page_title="AI Finance Studio",
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz
import yfinance as yf
import requests
import logging

# Simple logging for cloud
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🌟 AI Finance Studio - Cloud Production Version Starting")

def get_time_based_greeting():
    """Get time-based greeting using IST."""
    try:
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        hour = current_time.hour
        
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        else:
            return "Good evening"
    except Exception:
        return "Hello"

def get_portfolio_data():
    """Get realistic portfolio data."""
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    
    return {
        "total_value": 242040,
        "cost_basis": 235000,
        "positions_count": 27,
        "daily_change": 1250,
        "daily_change_percent": 0.52,
        "total_gain_loss": 7040,
        "total_gain_loss_percent": 2.99,
        "date": current_time.strftime("%Y-%m-%d"),
        "last_updated": current_time.strftime("%H:%M:%S IST"),
        "asia_tech_exposure": 16.8,
        "top_holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "value": 15000, "change": 2.1, "weight": 6.2},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "value": 18000, "change": 1.8, "weight": 7.4},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "value": 12000, "change": 3.2, "weight": 5.0},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "value": 14000, "change": 0.9, "weight": 5.8},
            {"symbol": "TSLA", "name": "Tesla Inc.", "value": 10000, "change": -1.2, "weight": 4.1}
        ],
        "regions": [
            {"name": "US-Tech", "value": 125000, "percentage": 51.6, "change": 0.8},
            {"name": "Asia-Tech", "value": 40663, "percentage": 16.8, "change": -0.3},
            {"name": "Europe", "value": 48408, "percentage": 20.0, "change": 0.4},
            {"name": "Other", "value": 27969, "percentage": 11.6, "change": 0.1}
        ]
    }

def ai_query_processor(query):
    """Process queries with Gemini AI - cloud optimized."""
    try:
        import google.generativeai as genai
        
        # Get API key from secrets or environment
        api_key = ""
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            api_key = os.getenv("GEMINI_API_KEY", "")
        
        if not api_key:
            return "🔑 Please configure your Gemini API key in Streamlit secrets to enable AI analysis."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        portfolio = get_portfolio_data()
        greeting = get_time_based_greeting()
        
        prompt = f"""{greeting}! I'm your AI financial advisor.

PORTFOLIO CONTEXT:
- Total Value: ${portfolio['total_value']:,}
- Positions: {portfolio['positions_count']} stocks  
- Today's Performance: ${portfolio['daily_change']:+,} ({portfolio['daily_change_percent']:+.2f}%)
- Total P&L: ${portfolio['total_gain_loss']:,} ({portfolio['total_gain_loss_percent']:+.2f}%)
- Asia-Tech Exposure: {portfolio['asia_tech_exposure']}%

USER QUERY: {query}

Provide professional financial analysis including:
1. Direct answer to the query
2. Portfolio-specific insights when relevant
3. Market context and recommendations
4. Risk assessment if applicable

Keep response concise but comprehensive."""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return f"🚫 AI analysis temporarily unavailable: {str(e)}"

def create_welcome_message():
    """Create comprehensive welcome message."""
    try:
        greeting = get_time_based_greeting()
        portfolio = get_portfolio_data()
        
        total_value = portfolio['total_value']
        daily_change = portfolio['daily_change']
        daily_pct = portfolio['daily_change_percent']
        total_gain = portfolio['total_gain_loss']
        total_gain_pct = portfolio['total_gain_loss_percent']
        asia_pct = portfolio['asia_tech_exposure']
        
        # Performance indicators
        daily_emoji = "🟢" if daily_change >= 0 else "🔴"
        total_emoji = "📈" if total_gain >= 0 else "📉"
        
        welcome_msg = f"""{greeting}! Welcome to AI Finance Studio!

💰 Portfolio Value: ${total_value:,} across {portfolio['positions_count']} positions
{total_emoji} Total P&L: ${total_gain:,} ({total_gain_pct:+.1f}%)
{daily_emoji} Today: ${daily_change:+,} ({daily_pct:+.1f}%)
🌏 Asia-Tech Exposure: {asia_pct}% (High Risk Alert)

Ready for portfolio analysis and market insights!"""
        
        return welcome_msg
        
    except Exception as e:
        logger.error(f"Welcome message error: {e}")
        return f"{get_time_based_greeting()}! Welcome to AI Finance Studio! Ready for financial analysis."

def create_portfolio_charts():
    """Create portfolio visualization charts."""
    try:
        portfolio = get_portfolio_data()
        
        # Regional allocation pie chart
        regions_df = pd.DataFrame(portfolio['regions'])
        
        fig_pie = px.pie(
            regions_df, 
            values='percentage', 
            names='name',
            title="Portfolio Allocation by Region",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=True, height=400)
        
        # Top holdings bar chart
        holdings_df = pd.DataFrame(portfolio['top_holdings'])
        
        # Color map for positive/negative changes
        colors = ['green' if x >= 0 else 'red' for x in holdings_df['change']]
        
        fig_bar = go.Figure(data=[
            go.Bar(
                x=holdings_df['symbol'],
                y=holdings_df['value'],
                marker_color=colors,
                text=[f"${x:,}" for x in holdings_df['value']],
                textposition='auto',
            )
        ])
        
        fig_bar.update_layout(
            title="Top 5 Holdings by Value",
            xaxis_title="Stock Symbol",
            yaxis_title="Value ($)",
            height=400
        )
        
        return fig_pie, fig_bar
        
    except Exception as e:
        logger.error(f"Chart creation error: {e}")
        return None, None

def initialize_session_state():
    """Initialize session state variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def display_header():
    """Display application header with IST time."""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    time_str = current_time.strftime("%Y-%m-%d %H:%M:%S IST")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("📈 AI Finance Studio")
        st.markdown("**Real-Time Portfolio Analytics & Market Insights**")
    
    with col2:
        st.markdown(f"**🕐 Current Time**")
        st.markdown(f"`{time_str}`")

def display_welcome():
    """Display welcome section."""
    welcome_text = create_welcome_message()
    st.success(f"🎉 {welcome_text}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Detailed Portfolio Analysis", type="primary"):
            portfolio = get_portfolio_data()
            
            # Detailed metrics
            st.subheader("📈 Portfolio Metrics")
            
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Total Value", f"${portfolio['total_value']:,}")
            with col_b:
                st.metric("Positions", portfolio['positions_count'])
            with col_c:
                st.metric("Daily P&L", f"${portfolio['daily_change']:+,}", f"{portfolio['daily_change_percent']:+.2f}%")
            with col_d:
                st.metric("Total P&L", f"${portfolio['total_gain_loss']:+,}", f"{portfolio['total_gain_loss_percent']:+.2f}%")
            
            # Charts
            fig_pie, fig_bar = create_portfolio_charts()
            if fig_pie and fig_bar:
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col_chart2:
                    st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        if st.button("🔊 Voice Synthesis"):
            try:
                import edge_tts
                import asyncio
                import tempfile
                
                async def generate_audio():
                    communicate = edge_tts.Communicate(welcome_text, "en-US-JennyNeural")
                    audio_data = b""
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_data += chunk["data"]
                    return audio_data
                
                with st.spinner("🗣️ Generating audio..."):
                    audio_data = asyncio.run(generate_audio())
                    if audio_data:
                        st.audio(audio_data, format="audio/mp3")
                        st.success("✅ Audio generated successfully!")
                    else:
                        st.warning("🚫 Audio generation failed")
                        
            except ImportError:
                st.info("🔊 Voice synthesis requires Edge TTS package")
            except Exception as e:
                st.warning(f"🚫 Voice synthesis not available: {str(e)}")

def display_sidebar():
    """Display sidebar with system status."""
    with st.sidebar:
        st.header("🎛️ System Status")
        
        portfolio = get_portfolio_data()
        
        # System status indicators
        st.success("✅ AI Analysis: Ready")
        st.success("✅ Portfolio Data: Active") 
        st.success("✅ Cloud Deployment: Active")
        st.info("☁️ Streamlit Cloud Optimized")
        
        st.markdown("---")
        
        # Quick portfolio stats
        st.subheader("📊 Quick Stats")
        st.metric("Portfolio Value", f"${portfolio['total_value']:,}")
        st.metric("Daily Change", f"${portfolio['daily_change']:+,}", f"{portfolio['daily_change_percent']:+.2f}%")
        st.metric("Asia-Tech Risk", f"{portfolio['asia_tech_exposure']}%")
        
        st.markdown("---")
        
        # Market quick links
        st.subheader("🔗 Quick Actions")
        
        quick_queries = [
            "What's my portfolio performance today?",
            "Show me Asia tech exposure analysis", 
            "Give me a market brief",
            "What's my risk exposure?"
        ]
        
        for query in quick_queries:
            if st.button(query, key=f"quick_{query[:20]}"):
                st.session_state.quick_query = query

def main():
    """Main application function."""
    initialize_session_state()
    display_header()
    display_sidebar()
    
    # Welcome section
    display_welcome()
    
    st.markdown("---")
    
    # Main interaction tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat Query", "📊 Analytics", "📈 Portfolio"])
    
    with tab1:
        st.subheader("💬 Ask Your Financial Questions")
        
        # Check for quick query from sidebar
        default_query = ""
        if hasattr(st.session_state, 'quick_query'):
            default_query = st.session_state.quick_query
            del st.session_state.quick_query
        
        # Text input
        user_query = st.text_input(
            "Enter your financial question:",
            value=default_query,
            placeholder="e.g., What's my portfolio performance today?",
            key="user_input"
        )
        
        if st.button("🔍 Analyze", type="primary") and user_query:
            with st.spinner("🧠 Processing your query..."):
                response = ai_query_processor(user_query)
                
                # Display response
                st.markdown("### 🤖 AI Response")
                st.markdown(response)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "query": user_query,
                    "response": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
        
        # Chat history
        if st.session_state.chat_history:
            st.markdown("### 📝 Recent Conversations")
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
                with st.expander(f"💬 {chat['timestamp']}: {chat['query'][:50]}..."):
                    st.markdown(f"**Question:** {chat['query']}")
                    st.markdown(f"**Answer:** {chat['response']}")
    
    with tab2:
        st.subheader("📊 Portfolio Analytics Dashboard")
        
        portfolio = get_portfolio_data()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Portfolio", f"${portfolio['total_value']:,}")
        with col2:
            st.metric("Daily Performance", f"${portfolio['daily_change']:+,}", f"{portfolio['daily_change_percent']:+.2f}%")
        with col3:
            st.metric("Total Gain/Loss", f"${portfolio['total_gain_loss']:+,}", f"{portfolio['total_gain_loss_percent']:+.2f}%")
        with col4:
            st.metric("Asia-Tech Exposure", f"{portfolio['asia_tech_exposure']}%", "High Risk")
        
        # Charts
        fig_pie, fig_bar = create_portfolio_charts()
        if fig_pie and fig_bar:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Regional allocation table
        st.subheader("🌍 Regional Allocation")
        regions_df = pd.DataFrame(portfolio['regions'])
        regions_df['Value'] = regions_df['value'].apply(lambda x: f"${x:,}")
        regions_df['Percentage'] = regions_df['percentage'].apply(lambda x: f"{x:.1f}%")
        regions_df['Change'] = regions_df['change'].apply(lambda x: f"{x:+.1f}%")
        
        display_df = regions_df[['name', 'Value', 'Percentage', 'Change']].rename(columns={
            'name': 'Region',
            'Value': 'Market Value',
            'Percentage': 'Allocation %',
            'Change': 'Daily Change'
        })
        
        st.dataframe(display_df, use_container_width=True)
    
    with tab3:
        st.subheader("📈 Portfolio Holdings")
        
        portfolio = get_portfolio_data()
        
        # Top holdings
        st.subheader("🏆 Top Holdings")
        holdings_df = pd.DataFrame(portfolio['top_holdings'])
        holdings_df['Value'] = holdings_df['value'].apply(lambda x: f"${x:,}")
        holdings_df['Weight'] = holdings_df['weight'].apply(lambda x: f"{x:.1f}%")
        holdings_df['Change'] = holdings_df['change'].apply(lambda x: f"{x:+.1f}%")
        
        display_holdings = holdings_df[['symbol', 'name', 'Value', 'Weight', 'Change']].rename(columns={
            'symbol': 'Symbol',
            'name': 'Company Name',
            'Value': 'Market Value',
            'Weight': 'Portfolio Weight',
            'Change': 'Daily Change'
        })
        
        st.dataframe(display_holdings, use_container_width=True)
        
        # Portfolio summary
        st.subheader("📋 Portfolio Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Portfolio Overview:**
            - **Total Positions:** {portfolio['positions_count']} stocks
            - **Total Value:** ${portfolio['total_value']:,}
            - **Cost Basis:** ${portfolio['cost_basis']:,}
            - **Unrealized P&L:** ${portfolio['total_gain_loss']:,} ({portfolio['total_gain_loss_percent']:+.2f}%)
            """)
        
        with col2:
            st.markdown(f"""
            **Risk Analysis:**
            - **Asia-Tech Exposure:** {portfolio['asia_tech_exposure']}% (High Risk)
            - **Geographic Diversification:** 4 regions
            - **Top 5 Concentration:** {sum([h['weight'] for h in portfolio['top_holdings']]):.1f}%
            - **Daily Volatility:** {abs(portfolio['daily_change_percent']):.2f}%
            """)

    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"🕐 Last Updated: {portfolio['last_updated']}")
    with col2:
        st.markdown("☁️ Streamlit Cloud Production")
    with col3:
        st.markdown("🤖 Powered by Gemini AI")

if __name__ == "__main__":
    main() 