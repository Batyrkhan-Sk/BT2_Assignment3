import os
from typing import Dict, Any, List
import requests
import asyncio
import json
import time

class AIService:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "mistral"  # Changed to mistral model
        self.timeout = 90  # Adjusted timeout for mistral

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

        prompt = f"""Task: Extract cryptocurrency name from query.
Query: {query}
Name:"""
        
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
            return result.get("response", "").strip().lower()
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

        data_summary = f"""
Price: ${price_data['price']:.2f} (24h change: {price_data['price_change_24h']:+.2f}%)
Market Cap: ${market_data['market_cap']:.2f} (Rank: #{market_data['market_cap_rank']})
Supply: {market_data['circulating_supply']:.0f} circulating / {market_data['total_supply']:.0f} total

News:
{chr(10).join([f"- {item['title']} ({item['source']})" for item in news[:3]]) if news else "No recent news"}
"""
        prompt = f"""Task: Answer crypto question based on data.
Question: {query}

Data:
{data_summary}

Answer:"""
        
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 200
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