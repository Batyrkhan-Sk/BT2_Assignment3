import os
from typing import Dict, Any, List
import requests
import asyncio

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

class AIService:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.model = OLLAMA_MODEL

    async def extract_crypto_name(self, query: str) -> str:
        """Extract cryptocurrency name from user query using Ollama."""
        prompt = (
            "Extract the cryptocurrency name from the user's query. "
            "Return only the name, nothing else."
        )
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        }
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(self.ollama_url, json=data, timeout=60))
        response.raise_for_status()
        result = response.json()
        # Ollama returns the response in 'message' or 'response'
        content = result.get("message", {}).get("content") or result.get("response")
        return content.strip().lower()

    async def generate_response(
        self,
        query: str,
        price_data: Dict[str, Any],
        market_data: Dict[str, Any],
        news: List[Dict[str, Any]]
    ) -> str:
        """Generate a natural language response using Ollama."""
        data_summary = f"""
Price Data:
- Current Price: ${price_data['price']:.2f}
- 24h Change: {price_data['price_change_24h']:.2f}%
- 24h Volume: ${price_data['volume_24h']:.2f}

Market Data:
- Market Cap: ${market_data['market_cap']:.2f}
- Market Cap Rank: #{market_data['market_cap_rank']}
- Circulating Supply: {market_data['circulating_supply']:.0f}
- Total Supply: {market_data['total_supply']:.0f}

Latest News:
{chr(10).join([f"- {item['title']} (Source: {item['source']})" for item in news]) if news else "No recent news available"}
"""
        prompt = (
            "You are a helpful crypto assistant. Provide clear, concise, and informative responses based on the data provided."
        )
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Query: {query}\n\nData:\n{data_summary}"}
            ]
        }
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(self.ollama_url, json=data, timeout=120))
        response.raise_for_status()
        result = response.json()
        content = result.get("message", {}).get("content") or result.get("response")
        return content.strip() 