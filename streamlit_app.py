import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(page_title="Finance Assistant", page_icon="💰", layout="wide")

st.title("💰 Finance Assistant")
st.subheader("Portfolio Dashboard")

# Sample portfolio data
portfolio_data = {
    'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
    'Shares': [10, 15, 5, 8, 12],
    'Current_Price': [150.00, 280.00, 120.00, 200.00, 400.00],
    'Value': [1500, 4200, 600, 1600, 4800]
}

df = pd.DataFrame(portfolio_data)
df['Total_Value'] = df['Shares'] * df['Current_Price']

st.subheader("📊 Portfolio Overview")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Portfolio Value", f"${df['Total_Value'].sum():,.2f}")
with col2:
    st.metric("Number of Holdings", len(df))
with col3:
    st.metric("Largest Position", df.loc[df['Total_Value'].idxmax(), 'Symbol'])

st.subheader("💼 Holdings")
st.dataframe(df, use_container_width=True)

st.subheader("📈 Portfolio Allocation")
fig = px.pie(df, values='Total_Value', names='Symbol', title="Portfolio Allocation by Value")
st.plotly_chart(fig, use_container_width=True)

st.success("✅ Finance Assistant is running successfully!")
st.info("This is a simplified version for deployment testing. Full features will be added once deployment is stable.") 