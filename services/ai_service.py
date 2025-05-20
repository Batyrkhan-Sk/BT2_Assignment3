import os
from typing import Dict, Any, List
import requests
import asyncio
import json
import time

class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "llama2"  # Using llama2 model
        self.timeout = 90  # Adjusted timeout for llama2

    def _check_ollama_server(self) -> bool:
        """Check if Ollama server is running."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    async def extract_crypto_name(self, query: str) -> str:
        """Extract cryptocurrency name from user query using Ollama."""
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
                "temperature": 0.1,  # Lower temperature for more focused responses
                "num_predict": 10    # Limit response length
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
            
            # Handle common cases
            if not crypto_name:
                raise Exception("Could not extract cryptocurrency name from query")
            
            # Map common variations to CoinGecko IDs
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
        """Generate a natural language response using Ollama."""
        if not self._check_ollama_server():
            raise Exception("Ollama server is not running. Please start it with 'ollama serve'")

        # Format the data in a more readable way
        data_summary = f"""
Current Price: ${price_data['price']:,.2f}
24h Change: {price_data['price_change_24h']:+.2f}%
24h Volume: ${price_data['volume_24h']:,.2f}

Market Cap: ${market_data['market_cap']:,.2f}
Market Cap Rank: #{market_data['market_cap_rank']}
Circulating Supply: {market_data['circulating_supply']:,.0f}
Total Supply: {market_data['total_supply']:,.0f}

Recent News:
{chr(10).join([f"- {item['title']} ({item['source']})" for item in news[:3]]) if news else "No recent news"}
"""
        prompt = f"""Task: Provide a clear and well-formatted analysis of the cryptocurrency based on the provided data.
Format the response with proper spacing and line breaks. Include price information, market data, and summarize the most relevant news.

Question: {query}

Data:
{data_summary}

Provide a well-formatted response with the following structure:
1. Current market overview (price, market cap, supply)
2. Recent price performance
3. Summary of relevant news

Answer:"""
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500  # Increased for longer responses
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
            return result.get("response", "").strip()
        except requests.exceptions.Timeout:
            raise Exception("Ollama server took too long to respond. Please check if the model is loaded correctly.")
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to Ollama server. Please make sure it's running with 'ollama serve'")
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}") 