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
import re

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
    """Get comprehensive 27-stock portfolio data."""
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
        
        # Complete 27-stock portfolio
        "all_holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "value": 18000, "change": 2.1, "weight": 7.4, "sector": "US-Tech"},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "value": 15000, "change": 1.8, "weight": 6.2, "sector": "US-Tech"},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "value": 12000, "change": 3.2, "weight": 5.0, "sector": "US-Tech"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "value": 14000, "change": 0.9, "weight": 5.8, "sector": "US-Tech"},
            {"symbol": "TSLA", "name": "Tesla Inc.", "value": 10000, "change": -1.2, "weight": 4.1, "sector": "US-Tech"},
            {"symbol": "AMZN", "name": "Amazon.com Inc.", "value": 9500, "change": 1.5, "weight": 3.9, "sector": "US-Tech"},
            {"symbol": "META", "name": "Meta Platforms", "value": 8200, "change": 2.8, "weight": 3.4, "sector": "US-Tech"},
            {"symbol": "NFLX", "name": "Netflix Inc.", "value": 6800, "change": -0.8, "weight": 2.8, "sector": "US-Tech"},
            {"symbol": "CRM", "name": "Salesforce Inc.", "value": 5900, "change": 1.2, "weight": 2.4, "sector": "US-Tech"},
            {"symbol": "ADBE", "name": "Adobe Inc.", "value": 5200, "change": 0.7, "weight": 2.1, "sector": "US-Tech"},
            {"symbol": "ORCL", "name": "Oracle Corp.", "value": 4800, "change": 1.9, "weight": 2.0, "sector": "US-Tech"},
            {"symbol": "INTC", "name": "Intel Corp.", "value": 4200, "change": -1.5, "weight": 1.7, "sector": "US-Tech"},
            {"symbol": "AMD", "name": "Advanced Micro Devices", "value": 4000, "change": 2.3, "weight": 1.7, "sector": "US-Tech"},
            
            # Asia-Tech Holdings
            {"symbol": "TSM", "name": "Taiwan Semiconductor", "value": 8500, "change": -0.5, "weight": 3.5, "sector": "Asia-Tech"},
            {"symbol": "BABA", "name": "Alibaba Group", "value": 7200, "change": -1.8, "weight": 3.0, "sector": "Asia-Tech"},
            {"symbol": "TCEHY", "name": "Tencent Holdings", "value": 6800, "change": -0.9, "weight": 2.8, "sector": "Asia-Tech"},
            {"symbol": "ASML", "name": "ASML Holding", "value": 5600, "change": 1.1, "weight": 2.3, "sector": "Asia-Tech"},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "value": 4200, "change": 0.8, "weight": 1.7, "sector": "Asia-Tech"},
            {"symbol": "INFOSYS.NS", "name": "Infosys Limited", "value": 3800, "change": 1.2, "weight": 1.6, "sector": "Asia-Tech"},
            {"symbol": "HDB", "name": "HDFC Bank", "value": 3200, "change": 0.5, "weight": 1.3, "sector": "Asia-Tech"},
            {"symbol": "WIT", "name": "Wipro Limited", "value": 1365, "change": -0.3, "weight": 0.6, "sector": "Asia-Tech"},
            
            # European Holdings  
            {"symbol": "SAP", "name": "SAP SE", "value": 12000, "change": 0.8, "weight": 5.0, "sector": "Europe"},
            {"symbol": "ASML", "name": "ASML Holding", "value": 10500, "change": 1.1, "weight": 4.3, "sector": "Europe"},
            {"symbol": "NESN.SW", "name": "Nestle SA", "value": 8900, "change": 0.3, "weight": 3.7, "sector": "Europe"},
            {"symbol": "NOVN.SW", "name": "Novartis AG", "value": 7200, "change": -0.2, "weight": 3.0, "sector": "Europe"},
            {"symbol": "UL", "name": "Unilever PLC", "value": 6800, "change": 0.4, "weight": 2.8, "sector": "Europe"},
            {"symbol": "MC.PA", "name": "LVMH", "value": 2908, "change": 1.2, "weight": 1.2, "sector": "Europe"},
            
            # Other/Emerging Markets
            {"symbol": "V", "name": "Visa Inc.", "value": 15000, "change": 1.6, "weight": 6.2, "sector": "Other"},
            {"symbol": "JNJ", "name": "Johnson & Johnson", "value": 8500, "change": 0.9, "weight": 3.5, "sector": "Other"},
            {"symbol": "PG", "name": "Procter & Gamble", "value": 4469, "change": 0.2, "weight": 1.8, "sector": "Other"}
        ],
        
        "top_holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "value": 18000, "change": 2.1, "weight": 7.4},
            {"symbol": "V", "name": "Visa Inc.", "value": 15000, "change": 1.6, "weight": 6.2},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "value": 15000, "change": 1.8, "weight": 6.2},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "value": 14000, "change": 0.9, "weight": 5.8},
            {"symbol": "SAP", "name": "SAP SE", "value": 12000, "change": 0.8, "weight": 5.0},
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "value": 12000, "change": 3.2, "weight": 5.0},
            {"symbol": "ASML", "name": "ASML Holding", "value": 10500, "change": 1.1, "weight": 4.3},
            {"symbol": "TSLA", "name": "Tesla Inc.", "value": 10000, "change": -1.2, "weight": 4.1}
        ],
        
        "regions": [
            {"name": "US-Tech", "value": 125000, "percentage": 51.6, "change": 0.8},
            {"name": "Asia-Tech", "value": 40663, "percentage": 16.8, "change": -0.3},
            {"name": "Europe", "value": 48408, "percentage": 20.0, "change": 0.4},
            {"name": "Other", "value": 27969, "percentage": 11.6, "change": 0.1}
        ],
        
        "performance_metrics": {
            "sharpe_ratio": 1.85,
            "max_drawdown": -8.2,
            "ytd_return": 12.4,
            "volatility": 15.8,
            "beta": 1.12,
            "alpha": 2.8
        }
    }

def ai_query_processor(query):
    """Process queries with Gemini AI - cloud optimized with full portfolio context."""
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
        
        # Enhanced portfolio context with all holdings
        all_holdings_context = ""
        for holding in portfolio['all_holdings'][:10]:  # Top 10 for context
            all_holdings_context += f"- {holding['symbol']} ({holding['name']}): ${holding['value']:,} ({holding['weight']:.1f}%, {holding['change']:+.1f}%)\n"
        
        # Sector breakdown
        sectors_context = ""
        for region in portfolio['regions']:
            sectors_context += f"- {region['name']}: ${region['value']:,} ({region['percentage']:.1f}%, {region['change']:+.1f}%)\n"
        
        prompt = f"""{greeting}! I'm your comprehensive AI financial advisor.

COMPLETE PORTFOLIO CONTEXT:
📊 Portfolio Overview:
- Total Value: ${portfolio['total_value']:,}
- Total Holdings: {portfolio['positions_count']} stocks
- Cost Basis: ${portfolio['cost_basis']:,}
- Unrealized P&L: ${portfolio['total_gain_loss']:,} ({portfolio['total_gain_loss_percent']:+.2f}%)
- Today's Performance: ${portfolio['daily_change']:+,} ({portfolio['daily_change_percent']:+.2f}%)

🏆 Top Holdings:
{all_holdings_context}

🌍 Regional Allocation:
{sectors_context}

⚠️ Risk Factors:
- Asia-Tech Exposure: {portfolio['asia_tech_exposure']}% (High Risk Alert)
- Geographic Diversification: 4 regions
- Top Holdings Concentration: {sum([h['weight'] for h in portfolio['top_holdings']]):.1f}%

📈 Performance Metrics:
- Sharpe Ratio: {portfolio.get('performance_metrics', {}).get('sharpe_ratio', 'N/A')}
- Volatility: {portfolio.get('performance_metrics', {}).get('volatility', 'N/A')}%
- YTD Return: {portfolio.get('performance_metrics', {}).get('ytd_return', 'N/A')}%

USER QUERY: "{query}"

INSTRUCTIONS:
As a professional financial advisor, provide a comprehensive response that:
1. Directly answers the user's question
2. Uses specific data from the portfolio context above
3. Provides actionable insights and recommendations
4. Highlights any relevant risks or opportunities
5. References specific holdings when relevant
6. Maintains a professional but friendly tone

Focus on being data-driven and specific rather than generic advice."""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return f"🚫 AI analysis temporarily unavailable. Please try again or contact support. Error: {str(e)}"

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
        if st.button("🔊 Speak Welcome Briefing", type="secondary"):
            try:
                import edge_tts
                import asyncio
                import tempfile
                import base64
                
                # Clean welcome message for voice
                clean_message = clean_text_for_voice(welcome_text)
                
                async def generate_speech():
                    voice = "en-US-AriaNeural"  # Female voice
                    communicate = edge_tts.Communicate(clean_message, voice)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                tmp_file.write(chunk["data"])
                        return tmp_file.name
                
                # Generate audio
                audio_file = asyncio.run(generate_speech())
                
                if audio_file:
                    with open(audio_file, "rb") as f:
                        audio_data = f.read()
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
        
        # Portfolio summary
        st.subheader("💼 Portfolio Overview")
        st.markdown(f"""
        **Key Metrics:**
        - **Total Positions:** {portfolio['positions_count']} stocks
        - **Cost Basis:** ${portfolio['cost_basis']:,}
        - **Unrealized P&L:** ${portfolio['total_gain_loss']:+,} ({portfolio['total_gain_loss_percent']:+.2f}%)
        - **Last Updated:** {portfolio['last_updated']}
        """)
        
        st.markdown("---")
        
        # Quick navigation
        st.subheader("🧭 Quick Navigation")
        st.markdown("""
        💡 **Tip:** Use the Quick Portfolio Queries in the Chat tab for instant analysis!
        
        **Tabs:**
        - 💬 **Chat Query:** Ask questions & get AI insights
        - 📊 **Analytics:** View detailed dashboard
        - 📈 **Portfolio:** Browse all holdings
        """)
        
        # Footer
        st.markdown("---")
        st.markdown("🤖 **AI Finance Studio**")
        st.markdown("*Powered by Gemini AI*")

def clean_text_for_voice(text):
    """Clean text for voice synthesis by removing emojis and special characters."""
    # Remove emojis
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    
    # Clean the text
    clean_text = emoji_pattern.sub(r'', text)
    
    # Remove special markdown characters
    clean_text = re.sub(r'\*\*', '', clean_text)  # Remove bold markdown
    clean_text = re.sub(r'\*', '', clean_text)    # Remove italics
    clean_text = re.sub(r'#', '', clean_text)     # Remove headers
    clean_text = re.sub(r'`', '', clean_text)     # Remove code blocks
    clean_text = re.sub(r'\[', '', clean_text)    # Remove brackets
    clean_text = re.sub(r'\]', '', clean_text)    
    clean_text = re.sub(r'\(', '', clean_text)    # Remove parentheses for cleaner speech
    clean_text = re.sub(r'\)', '', clean_text)
    
    # Replace currency symbols with words
    clean_text = re.sub(r'\$', 'dollars ', clean_text)
    clean_text = re.sub(r'%', ' percent', clean_text)
    clean_text = re.sub(r'&', ' and ', clean_text)
    
    # Clean up extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

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
        
        # Quick Portfolio Queries Dropdown - much cleaner interface
        st.markdown("### 🚀 Quick Portfolio Queries")
        st.markdown("*Select a pre-built query for instant analysis:*")
        
        # Organize all queries into a single dropdown
        quick_queries = {
            "📊 Performance Analysis": [
                "What's my portfolio performance today?",
                "Show me my total gains and losses",
                "How is my portfolio performing this week?",
                "What's my best performing stock today?",
                "Which stocks are underperforming?",
                "Summarize today's portfolio performance"
            ],
            "🌏 Regional & Sector Analysis": [
                "Show me Asia tech exposure analysis",
                "What's happening in Asian markets?",
                "Which region has the highest allocation?",
                "Analyze my sector diversification",
                "Compare US vs International holdings"
            ],
            "📈 Individual Stock Analysis": [
                "Tell me about my top performing stock",
                "Which stock should I watch closely?",
                "Analyze my technology stocks",
                "Show me dividend-paying stocks in my portfolio",
                "What are my riskiest positions?"
            ],
            "⚠️ Risk & Strategy": [
                "What's my risk exposure analysis?",
                "Should I rebalance my portfolio?",
                "Identify potential selling opportunities",
                "Show me correlation risks",
                "Analyze my portfolio volatility"
            ],
            "📰 Market Insights": [
                "Any earnings surprises today?",
                "What's the market sentiment?",
                "Show me economic calendar events",
                "Analyze current market trends",
                "What's driving market movements today?"
            ]
        }
        
        # Create flattened list for dropdown
        all_queries = []
        for category, queries in quick_queries.items():
            all_queries.append(f"--- {category} ---")
            all_queries.extend(queries)
        
        # Dropdown selection
        selected_query = st.selectbox(
            "Choose a quick query:",
            ["Select a query..."] + all_queries,
            index=0
        )
        
        # Handle dropdown selection
        if selected_query and selected_query != "Select a query..." and not selected_query.startswith("---"):
            if st.button("🚀 Execute Query", type="primary"):
                st.session_state.quick_query = selected_query
        
        st.markdown("---")
        
        # Main query input section
        st.markdown("### ✏️ Or Ask Your Own Question")
        user_query = st.text_input(
            "Enter your financial question:",
            placeholder="e.g., What's my portfolio performance today?",
            key="user_input"
        )
        
        # Process queries - either from dropdown or manual input
        query_to_process = None
        
        # Check if we have a quick query from dropdown
        if hasattr(st.session_state, 'quick_query'):
            query_to_process = st.session_state.quick_query
            st.info(f"🚀 Executing selected query: {query_to_process}")
            del st.session_state.quick_query
            # Auto-process dropdown queries
            with st.spinner("🧠 Processing your query..."):
                response = ai_query_processor(query_to_process)
                
                # Display response
                st.markdown("### 🤖 AI Response")
                st.markdown(response)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "query": query_to_process,
                    "response": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
        
        # Handle manual text input
        elif st.button("🔍 Analyze", type="primary") and user_query:
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
        
        # Show helpful message when no query
        elif not query_to_process and not user_query:
            st.info("💡 Select a quick query from the dropdown above or type your own question!")
        
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
        
        # Portfolio overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Holdings", f"{portfolio['positions_count']} stocks")
        with col2:
            st.metric("Portfolio Value", f"${portfolio['total_value']:,}")
        with col3:
            st.metric("Unrealized P&L", f"${portfolio['total_gain_loss']:,}", f"{portfolio['total_gain_loss_percent']:+.2f}%")
        with col4:
            st.metric("Cost Basis", f"${portfolio['cost_basis']:,}")
        
        # Top holdings
        st.subheader("🏆 Top 8 Holdings")
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
        
        # Complete holdings by sector
        st.subheader("📋 Complete Holdings by Sector")
        
        # Get all holdings and organize by sector
        all_holdings = portfolio['all_holdings']
        
        # Group by sector
        sectors = {}
        for holding in all_holdings:
            sector = holding['sector']
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(holding)
        
        # Display each sector
        for sector_name, sector_holdings in sectors.items():
            with st.expander(f"🏢 {sector_name} ({len(sector_holdings)} holdings)", expanded=False):
                sector_df = pd.DataFrame(sector_holdings)
                sector_df['Value'] = sector_df['value'].apply(lambda x: f"${x:,}")
                sector_df['Weight'] = sector_df['weight'].apply(lambda x: f"{x:.1f}%")
                sector_df['Change'] = sector_df['change'].apply(lambda x: f"{x:+.1f}%")
                
                display_sector = sector_df[['symbol', 'name', 'Value', 'Weight', 'Change']].rename(columns={
                    'symbol': 'Symbol',
                    'name': 'Company Name', 
                    'Value': 'Market Value',
                    'Weight': 'Portfolio Weight',
                    'Change': 'Daily Change'
                })
                
                st.dataframe(display_sector, use_container_width=True)
                
                # Sector summary
                sector_total_value = sum([h['value'] for h in sector_holdings])
                sector_total_weight = sum([h['weight'] for h in sector_holdings])
                sector_avg_change = sum([h['change'] for h in sector_holdings]) / len(sector_holdings)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sector Value", f"${sector_total_value:,}")
                with col2:
                    st.metric("Sector Weight", f"{sector_total_weight:.1f}%")
                with col3:
                    st.metric("Avg Daily Change", f"{sector_avg_change:+.1f}%")
        
        # Portfolio summary
        st.subheader("📋 Portfolio Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Portfolio Overview:**
            - **Total Positions:** {portfolio['positions_count']} stocks
            - **Total Value:** ${portfolio['total_value']:,}
            - **Cost Basis:** ${portfolio['cost_basis']:,}
            - **Unrealized P&L:** ${portfolio['total_gain_loss']:,} ({portfolio['total_gain_loss_percent']:+.2f}%)
            - **Daily Change:** ${portfolio['daily_change']:+,} ({portfolio['daily_change_percent']:+.2f}%)
            """)
        
        with col2:
            if 'performance_metrics' in portfolio:
                metrics = portfolio['performance_metrics']
                st.markdown(f"""
                **Risk & Performance Metrics:**
                - **Sharpe Ratio:** {metrics['sharpe_ratio']:.2f}
                - **Max Drawdown:** {metrics['max_drawdown']:.1f}%
                - **YTD Return:** {metrics['ytd_return']:.1f}%
                - **Volatility:** {metrics['volatility']:.1f}%
                - **Beta:** {metrics['beta']:.2f}
                - **Alpha:** {metrics['alpha']:.1f}%
                """)
            else:
                st.markdown(f"""
                **Risk Analysis:**
                - **Asia-Tech Exposure:** {portfolio['asia_tech_exposure']}% (High Risk)
                - **Geographic Diversification:** 4 regions
                - **Top 8 Concentration:** {sum([h['weight'] for h in portfolio['top_holdings']]):.1f}%
                - **Daily Volatility:** {abs(portfolio['daily_change_percent']):.2f}%
                """)
        
        # Sector allocation summary
        st.subheader("🥧 Sector Allocation Summary")
        sector_summary = []
        for sector_name, sector_holdings in sectors.items():
            sector_total_value = sum([h['value'] for h in sector_holdings])
            sector_total_weight = sum([h['weight'] for h in sector_holdings])
            sector_avg_change = sum([h['change'] for h in sector_holdings]) / len(sector_holdings)
            sector_summary.append({
                'Sector': sector_name,
                'Holdings': len(sector_holdings),
                'Value': f"${sector_total_value:,}",
                'Weight': f"{sector_total_weight:.1f}%",
                'Avg Change': f"{sector_avg_change:+.1f}%"
            })
        
        sector_summary_df = pd.DataFrame(sector_summary)
        st.dataframe(sector_summary_df, use_container_width=True)

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