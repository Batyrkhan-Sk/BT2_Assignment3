import streamlit as st
import os
from dotenv import load_dotenv
from services.market_service import MarketService
from services.news_service import NewsService
from services.ai_service import AIService
import asyncio
from datetime import datetime

st.set_page_config(
    page_title="AI Crypto Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv(override=True)

st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: var(--background-color);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: var(--text-color);
    }
    .news-card {
        background-color: var(--background-color);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border: 1px solid var(--border-color);
        color: var(--text-color);
    }
    .metric-card h3, .news-card h4 {
        color: var(--text-color);
    }
    .metric-card p, .news-card p {
        color: var(--text-color);
    }
    .news-card a {
        color: var(--link-color);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_services():
    return MarketService(), NewsService(), AIService()

market_service, news_service, ai_service = init_services()

with st.sidebar:
    st.title("🤖 AI Crypto Assistant")
    st.markdown("---")
    st.markdown("""
    ### How to use
    1. Enter your question about any cryptocurrency
    2. Get real-time data about:
       - Current price and market data
       - Latest news
       - AI-powered analysis
    """)
    st.markdown("---")
    st.markdown("### Example queries")
    st.markdown("""
    - What's the latest news about Ethereum?
    - What's the current price and market cap of Solana?
    - Tell me about Bitcoin's recent performance
    """)

st.title("AI Crypto Assistant")
st.markdown("Ask any question about cryptocurrencies in the top 50 by market cap.")

query = st.text_input("Enter your question:", placeholder="e.g., What's the latest news about Ethereum?")

async def process_query():
    if query:
        try:
            with st.spinner("Analyzing your query..."):
                crypto_name = await ai_service.extract_crypto_name(query)
                
                price_data = await market_service.get_price(crypto_name)
                market_data = await market_service.get_market_data(crypto_name)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Market Data")
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Price Information</h3>
                        <p>Current Price: ${price_data['price']:,.2f}</p>
                        <p>24h Change: {price_data['price_change_24h']:+.2f}%</p>
                        <p>24h Volume: ${price_data['volume_24h']:,.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>Market Information</h3>
                        <p>Market Cap: ${market_data['market_cap']:,.2f}</p>
                        <p>Market Cap Rank: #{market_data['market_cap_rank']}</p>
                        <p>Circulating Supply: {market_data['circulating_supply']:,.0f}</p>
                        <p>Total Supply: {market_data['total_supply']:,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.subheader("📰 Latest News")
                    try:
                        news = await asyncio.wait_for(news_service.get_news(crypto_name), timeout=10.0)
                        if news and len(news) > 0:
                            for item in news:
                                st.markdown(f"""
                                <div class="news-card">
                                    <h4>{item['title']}</h4>
                                    <p><strong>Source:</strong> {item['source']}</p>
                                    <p><strong>Published:</strong> {item['published_at']}</p>
                                    <p><strong>Related Cryptocurrencies:</strong> {', '.join(item['currencies'])}</p>
                                    <a href="{item['url']}" target="_blank">Read full article</a>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info(f"No recent news found for {crypto_name.upper()}. Try searching for a different cryptocurrency.")
                    except asyncio.TimeoutError:
                        st.error("News service timed out. Please try again in a few moments.")
                    except Exception as e:
                        st.error(f"Error fetching news: {str(e)}")
                        st.info("Please try again later or try a different cryptocurrency.")
                
                try:
                    ai_response = await ai_service.generate_response(
                        query, price_data, market_data, news if 'news' in locals() else []
                    )
                    st.subheader("🤖 AI Analysis")
                    st.markdown(ai_response)
                except Exception as e:
                    st.error(f"Failed to generate AI analysis: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please try again with a different query.")

if query:
    asyncio.run(process_query())