"""
🎤💰 Finance Assistant - Cloud Optimized Version
Simple finance portfolio tracker without voice features for cloud deployment
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Finance Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stock-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_portfolio():
    """Load sample portfolio data"""
    return {
        'AAPL': {'shares': 50, 'avg_cost': 150.00},
        'GOOGL': {'shares': 25, 'avg_cost': 2500.00},
        'MSFT': {'shares': 40, 'avg_cost': 300.00},
        'TSLA': {'shares': 30, 'avg_cost': 200.00},
        'RELIANCE.NS': {'shares': 100, 'avg_cost': 2500.00},
        'TCS.NS': {'shares': 50, 'avg_cost': 3200.00}
    }

def get_stock_data(symbol):
    """Get current stock data"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1d")
        
        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        return {
            'symbol': symbol,
            'name': info.get('longName', symbol),
            'current_price': current_price,
            'currency': info.get('currency', 'USD'),
            'market_cap': info.get('marketCap', 0),
            'sector': info.get('sector', 'Unknown')
        }
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

def calculate_portfolio_metrics(portfolio):
    """Calculate portfolio metrics"""
    total_value = 0
    total_cost = 0
    stocks_data = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (symbol, holding) in enumerate(portfolio.items()):
        status_text.text(f"Loading {symbol}...")
        progress_bar.progress((i + 1) / len(portfolio))
        
        stock_data = get_stock_data(symbol)
        if stock_data:
            shares = holding['shares']
            avg_cost = holding['avg_cost']
            current_value = shares * stock_data['current_price']
            cost_basis = shares * avg_cost
            
            stocks_data.append({
                'Symbol': symbol,
                'Name': stock_data['name'],
                'Shares': shares,
                'Avg Cost': avg_cost,
                'Current Price': stock_data['current_price'],
                'Current Value': current_value,
                'Cost Basis': cost_basis,
                'P&L': current_value - cost_basis,
                'P&L %': ((current_value - cost_basis) / cost_basis) * 100,
                'Sector': stock_data['sector']
            })
            
            total_value += current_value
            total_cost += cost_basis
    
    progress_bar.empty()
    status_text.empty()
    
    return stocks_data, total_value, total_cost

def setup_gemini():
    """Setup Gemini AI"""
    try:
        # Try to get API key from secrets first, then environment
        api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-flash')
        return None
    except Exception:
        return None

def get_ai_analysis(portfolio_data, query):
    """Get AI analysis using Gemini"""
    model = setup_gemini()
    if not model:
        return "AI analysis unavailable. Please configure GEMINI_API_KEY in secrets."
    
    try:
        # Prepare portfolio summary
        df = pd.DataFrame(portfolio_data)
        portfolio_summary = f"""
        Portfolio Summary:
        Total Stocks: {len(df)}
        Top Performers: {df.nlargest(3, 'P&L %')[['Symbol', 'P&L %']].to_string(index=False)}
        Sectors: {df['Sector'].value_counts().to_string()}
        
        Query: {query}
        """
        
        response = model.generate_content(f"As a financial advisor, analyze this portfolio data and answer the query: {portfolio_summary}")
        return response.text
    except Exception as e:
        return f"AI analysis error: {str(e)}"

def main():
    st.markdown('<h1 class="main-header">💰 Finance Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎯 Portfolio Settings")
    
    # Load portfolio
    portfolio = load_sample_portfolio()
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Portfolio Overview")
        
        # Calculate metrics
        with st.spinner("Loading portfolio data..."):
            stocks_data, total_value, total_cost = calculate_portfolio_metrics(portfolio)
        
        if stocks_data:
            df = pd.DataFrame(stocks_data)
            
            # Key metrics
            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
            
            # Display metrics
            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("Total Value", f"${total_value:,.2f}")
            with metric_cols[1]:
                st.metric("Total Cost", f"${total_cost:,.2f}")
            with metric_cols[2]:
                st.metric("P&L", f"${total_pnl:,.2f}", f"{total_pnl_pct:.2f}%")
            with metric_cols[3]:
                st.metric("Positions", len(stocks_data))
            
            # Portfolio table
            st.subheader("📈 Holdings")
            formatted_df = df.copy()
            formatted_df['Current Value'] = formatted_df['Current Value'].apply(lambda x: f"${x:,.2f}")
            formatted_df['Cost Basis'] = formatted_df['Cost Basis'].apply(lambda x: f"${x:,.2f}")
            formatted_df['P&L'] = formatted_df['P&L'].apply(lambda x: f"${x:,.2f}")
            formatted_df['P&L %'] = formatted_df['P&L %'].apply(lambda x: f"{x:.2f}%")
            formatted_df['Current Price'] = formatted_df['Current Price'].apply(lambda x: f"${x:.2f}")
            formatted_df['Avg Cost'] = formatted_df['Avg Cost'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(formatted_df, use_container_width=True)
            
            # Charts
            st.subheader("📊 Portfolio Analysis")
            
            chart_cols = st.columns(2)
            
            with chart_cols[0]:
                # Sector allocation
                sector_data = df.groupby('Sector')['Current Value'].sum().reset_index()
                fig_sector = px.pie(sector_data, values='Current Value', names='Sector', 
                                  title="Portfolio by Sector")
                st.plotly_chart(fig_sector, use_container_width=True)
            
            with chart_cols[1]:
                # Top performers
                top_performers = df.nlargest(5, 'P&L %')
                fig_performers = px.bar(top_performers, x='Symbol', y='P&L %', 
                                      title="Top Performers by P&L %")
                st.plotly_chart(fig_performers, use_container_width=True)
    
    with col2:
        st.subheader("🤖 AI Assistant")
        
        # Predefined queries
        query_options = [
            "What's my portfolio performance summary?",
            "Which stocks should I consider selling?",
            "What's my risk exposure?",
            "How diversified is my portfolio?",
            "Which sectors am I overweight in?"
        ]
        
        selected_query = st.selectbox("Quick Questions:", [""] + query_options)
        custom_query = st.text_area("Or ask your own question:")
        
        query = selected_query if selected_query else custom_query
        
        if st.button("🚀 Get AI Analysis") and query:
            with st.spinner("Analyzing..."):
                if stocks_data:
                    analysis = get_ai_analysis(stocks_data, query)
                    st.write("### Analysis:")
                    st.write(analysis)
                else:
                    st.warning("Please wait for portfolio data to load first.")
        
        # Market summary
        st.subheader("📈 Market Summary")
        st.info("Real-time market data and analysis powered by Yahoo Finance and Google AI")
        
        # Tips
        st.subheader("💡 Quick Tips")
        tips = [
            "💼 Diversify across sectors and geographies",
            "📊 Review your portfolio monthly",
            "🎯 Set clear investment goals",
            "⚖️ Balance risk and reward",
            "📚 Stay informed about market trends"
        ]
        
        for tip in tips:
            st.write(tip)

if __name__ == "__main__":
    main() 