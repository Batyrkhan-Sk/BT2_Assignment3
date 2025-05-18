# AI Crypto Assistant 🤖

A modern web application that provides real-time cryptocurrency information, news, and AI-powered insights using Streamlit.

## Features ✨

- 📊 Real-time price and market data from CoinGecko
- 📰 Latest news from CryptoPanic
- 🤖 AI-powered analysis using OpenAI GPT
- 💡 User-friendly interface with Streamlit
- 🔄 Automatic data updates
- 📱 Responsive design

## Setup 🛠️

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   COINGECKO_API_KEY=your_coingecko_api_key
   COINMARKETCAP_API_KEY=your_coinmarketcap_api_key
   CRYPTOPANIC_API_KEY=your_cryptopanic_api_key
   ```

## Running the Application 🚀

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to `http://localhost:8501`

## Example Queries 💭

- "What's the latest news about Ethereum?"
- "What's the current price and market cap of Solana?"
- "Tell me about Bitcoin's recent performance"

## Technologies Used 🛠️

- **Frontend**: Streamlit
- **Backend**: Python
- **APIs**:
  - OpenAI GPT for AI analysis
  - CoinGecko for market data
  - CryptoPanic for news
- **Data Processing**: Python with async support

## Error Handling 🚨

The application includes comprehensive error handling for:
- API rate limits
- Network connectivity issues
- Invalid cryptocurrency names
- Missing API keys
- Data parsing errors

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details. 