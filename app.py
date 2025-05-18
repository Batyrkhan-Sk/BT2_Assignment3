import streamlit as st
import os
from dotenv import load_dotenv
from services.market_service import MarketService
from services.news_service import NewsService
from services.ai_service import AIService
import asyncio
from datetime import datetime

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="AI Crypto Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv(override=True)

# Debug: Print environment variables (without sensitive values)
st.write("Environment Variables Status:")
env_vars = {
    "OPENAI_API_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Not Set",
    "COINGECKO_API_KEY": "Set" if os.getenv("COINGECKO_API_KEY") else "Not Set",
    "COINMARKETCAP_API_KEY": "Set" if os.getenv("COINMARKETCAP_API_KEY") else "Not Set",
    "CRYPTOPANIC_API_KEY": "Set" if os.getenv("CRYPTOPANIC_API_KEY") else "Not Set",
    "OLLAMA_URL": os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
    "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "mistral")
}
st.json(env_vars)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .news-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def init_services():
    return MarketService(), NewsService(), AIService()

market_service, news_service, ai_service = init_services()

# Sidebar
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

# Main content
st.title("AI Crypto Assistant")
st.markdown("Ask any question about cryptocurrencies in the top 50 by market cap.")

# Query input
query = st.text_input("Enter your question:", placeholder="e.g., What's the latest news about Ethereum?")

async def process_query():
    if query:
        try:
            with st.spinner("Analyzing your query..."):
                # Extract crypto name using AI
                crypto_name = await ai_service.extract_crypto_name(query)
                
                # Fetch data
                price_data = await market_service.get_price(crypto_name)
                market_data = await market_service.get_market_data(crypto_name)
                news = await news_service.get_news(crypto_name)
                
                # Generate AI response
                ai_response = await ai_service.generate_response(
                    query, price_data, market_data, news
                )
                
                # Display results in two columns
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
                    for item in news:
                        st.markdown(f"""
                        <div class="news-card">
                            <h4>{item['title']}</h4>
                            <p>Source: {item['source']}</p>
                            <p>Published: {item['published_at']}</p>
                            <a href="{item['url']}" target="_blank">Read more</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                # AI Analysis
                st.subheader("🤖 AI Analysis")
                st.markdown(ai_response)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center'>
    <p>Powered by OpenAI GPT, CoinGecko, and CryptoPanic APIs</p>
    <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

# Run the async function
if query:
    asyncio.run(process_query()) 