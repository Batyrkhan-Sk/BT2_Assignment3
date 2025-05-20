import os
from typing import Dict, Any, List
import requests
import asyncio
import json
import time
import re

class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "mistral"
        self.timeout = 120

    def _check_ollama_server(self) -> bool:
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    async def extract_crypto_name(self, query: str) -> str:
        if not self._check_ollama_server():
            raise Exception("Ollama server is not running. Please start it with 'ollama serve'")

        prompt = f"""Task: Extract the cryptocurrency name from the query. Return ONLY the cryptocurrency name in lowercase, nothing else.
Common cryptocurrency names: bitcoin (BTC), ethereum (ETH), solana (SOL), cardano (ADA), polkadot (DOT), ripple (XRP), dogecoin (DOGE), binance coin (BNB), avalanche (AVAX), polygon (MATIC)

Query: {query}
Cryptocurrency name:"""
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 10
            }
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(self.ollama_url, json=data, timeout=self.timeout)
            )
            response.raise_for_status()
            result = response.json()
            crypto_name = result.get("response", "").strip().lower()
            
            if not crypto_name:
                raise Exception("Could not extract cryptocurrency name from query")
            
            name_mapping = {
                "btc": "bitcoin",
                "eth": "ethereum",
                "sol": "solana",
                "ada": "cardano",
                "dot": "polkadot",
                "xrp": "ripple",
                "doge": "dogecoin",
                "bnb": "binancecoin",
                "avax": "avalanche-2",
                "matic": "matic-network"
            }
            
            return name_mapping.get(crypto_name, crypto_name)
        except requests.exceptions.Timeout:
            raise Exception("Ollama server took too long to respond. Please check if the model is loaded correctly.")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Ollama server. Please make sure it's running with 'ollama serve'")
        except Exception as e:
            raise Exception(f"Failed to extract crypto name: {str(e)}")

    async def generate_response(
        self,
        query: str,
        price_data: Dict[str, Any],
        market_data: Dict[str, Any],
        news: List[Dict[str, Any]]
    ) -> str:
        if not self._check_ollama_server():
            raise Exception("Ollama server is not running. Please start it with 'ollama serve'")

        def clean_text(text: str) -> str:
            text = text.replace('"', '').replace('"', '')
            text = text.replace('−', '-')
            
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
            text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
            
            text = text.replace('BTC', ' BTC ').replace('ETH', ' ETH ')
            text = text.replace('USD', ' USD ').replace('$', ' $')
            text = text.replace('M', ' million ').replace('B', ' billion ')
            text = text.replace('K', ' thousand ')
            
            text = ' '.join(text.split())
            
            sentences = [s.strip() for s in text.split('.') if s.strip()]
            unique_sentences = []
            for sentence in sentences:
                if not unique_sentences or unique_sentences[-1] != sentence:
                    unique_sentences.append(sentence)
            
            unique_sentences = [s[0].upper() + s[1:] for s in unique_sentences]
            
            return '. '.join(unique_sentences) + '.'

        data_summary = f"""
Current Price: ${price_data['price']:,.2f}
24h Change: {price_data['price_change_24h']:+.2f}%
24h Volume: ${price_data['volume_24h']:,.2f}

Market Cap: ${market_data['market_cap']:,.2f}
Market Cap Rank: #{market_data['market_cap_rank']}
Circulating Supply: {market_data['circulating_supply']:,.0f}
Total Supply: {market_data['total_supply']:,.0f}

Recent News:
{chr(10).join([f"- {clean_text(item['title'])} ({item['source']})" for item in news[:3]]) if news else "No recent news"}
"""
        prompt = f"""Task: Provide a detailed and well-formatted analysis of the cryptocurrency based on the provided data.
You are a professional cryptocurrency analyst. Your response should be comprehensive, well-structured, and properly formatted.

IMPORTANT FORMATTING RULES:
1. ALWAYS add spaces between words and numbers
2. ALWAYS format numbers with commas for thousands (e.g., 1,234,567)
3. ALWAYS use proper currency symbols with spaces ($ for USD)
4. ALWAYS use proper spacing around cryptocurrency symbols (BTC, ETH)
5. ALWAYS use proper abbreviations (million, billion, thousand)
6. ALWAYS capitalize the first letter of each sentence
7. ALWAYS use proper punctuation
8. NEVER combine words without spaces
9. NEVER combine numbers with words without spaces
10. NEVER combine currency symbols with numbers without spaces
11. NEVER repeat the same information
12. NEVER duplicate sentences or phrases

Example of correct formatting:
"The current price of Ethereum (ETH) is $2,477.97 USD. Its market capitalization stands at $299.18 billion USD, ranking it #2 among all cryptocurrencies. The circulating supply of ETH is 120,727,315 coins."

Question: {query}

Data:
{data_summary}

Provide a detailed analysis with the following structure:

1. MARKET OVERVIEW
   - Current price and 24-hour change
   - Market capitalization and rank
   - Supply metrics (circulating and total supply)
   - Trading volume analysis

2. PRICE PERFORMANCE ANALYSIS
   - Detailed analysis of the 24-hour price change
   - Volume analysis and its implications
   - Market position relative to other cryptocurrencies

3. NEWS ANALYSIS
   - Summarize and analyze each news item
   - Explain how these news events might impact the price
   - Identify any significant trends or developments
   - Connect news events with current market conditions

4. MARKET TRENDS AND OUTLOOK
   - Analyze the overall market sentiment
   - Identify key factors affecting the price
   - Provide insights based on the news and market data

Make sure to:
- Add proper spacing between ALL words and numbers
- Format ALL numbers with commas
- Use proper currency symbols with spaces
- Use proper spacing around cryptocurrency symbols
- Use proper abbreviations for large numbers
- Capitalize the first letter of each sentence
- Use proper punctuation
- Do not repeat any information
- Do not duplicate sentences or phrases
- Provide detailed analysis of each news item
- Connect news events with market data
- Explain the implications of market metrics

Answer:"""
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "num_predict": 300,
                "top_k": 40,
                "top_p": 0.9,
                "stop": ["\n\n", "Question:", "Data:"]
            }
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(self.ollama_url, json=data, timeout=self.timeout)
            )
            response.raise_for_status()
            result = response.json()
            
            response_text = result.get("response", "").strip()
            response_text = clean_text(response_text)
            
            def format_number(match):
                num = match.group(1)
                return f"{int(num):,}"
            
            response_text = re.sub(r'(\d+)(?=\s|$)', format_number, response_text)
            
            return response_text
            
        except requests.exceptions.Timeout:
            raise Exception("Ollama server took too long to respond. Please check if the model is loaded correctly.")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Ollama server. Please make sure it's running with 'ollama serve'")
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}") 