import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(page_title="Finance Assistant", page_icon="💰", layout="wide")

st.title("💰 Finance Assistant")
st.markdown("**Portfolio Dashboard** - Deployment Working!")

# Static portfolio data that mimics your real portfolio
portfolio_data = {
    'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META'],
    'Company': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.', 'Tesla Inc.', 'NVIDIA Corp.', 'Meta Platforms'],
    'Shares': [25, 30, 10, 15, 20, 12],
    'Price': [175.00, 330.00, 135.00, 205.00, 450.00, 285.00],
}

df = pd.DataFrame(portfolio_data)
df['Value'] = df['Shares'] * df['Price']
df['Weight'] = (df['Value'] / df['Value'].sum() * 100).round(2)

st.subheader("📊 Portfolio Overview")
col1, col2, col3, col4 = st.columns(4)

total_value = df['Value'].sum()
best_performer = df.loc[df['Value'].idxmax(), 'Symbol']
total_stocks = len(df)
avg_value = df['Value'].mean()

with col1:
    st.metric("Total Value", f"${total_value:,.0f}")
with col2:
    st.metric("Best Position", best_performer)
with col3:
    st.metric("Total Stocks", total_stocks)
with col4:
    st.metric("Avg Position", f"${avg_value:,.0f}")

# Portfolio table
st.subheader("📈 Holdings")
st.dataframe(df[['Symbol', 'Company', 'Shares', 'Price', 'Value', 'Weight']], use_container_width=True)

# Charts
col1, col2 = st.columns(2)

with col1:
    fig_pie = px.pie(df, values='Value', names='Symbol', title='Portfolio Allocation')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    fig_bar = px.bar(df, x='Symbol', y='Value', title='Position Values')
    st.plotly_chart(fig_bar, use_container_width=True)

# Success message
st.success("🎉 **DEPLOYMENT SUCCESSFUL!** Your Finance Assistant is now live on Streamlit Cloud!")
st.info("💡 This simplified version shows your portfolio data. The full AI features will be added once deployment is stable.")

# Additional info
with st.expander("📋 Deployment Details"):
    st.write(f"""
    - **Total Portfolio Value**: ${total_value:,.0f}
    - **Number of Holdings**: {total_stocks}
    - **Largest Position**: {best_performer} (${df.loc[df['Value'].idxmax(), 'Value']:,.0f})
    - **Platform**: Streamlit Cloud
    - **Status**: ✅ Successfully Deployed
    """) 