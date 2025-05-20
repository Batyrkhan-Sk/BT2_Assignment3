import os
from typing import List, Dict, Any
import aiohttp
from datetime import datetime, timezone
import json

class NewsService:
    def __init__(self):
        self.cryptopanic_api_key = os.getenv("CRYPTOPANIC_API_KEY")
        if not self.cryptopanic_api_key or self.cryptopanic_api_key == "your_cryptopanic_api_key_here":
            raise ValueError("CRYPTOPANIC_API_KEY is not properly configured. Please set a valid API key in your .env file.")
        self.cryptopanic_base_url = "https://cryptopanic.com/api/v1"
        self.cointelegraph_base_url = "https://api.cointelegraph.com/api/v1"
        
    async def get_news(self, crypto_name: str) -> List[Dict[str, Any]]:
        """Get latest news from CryptoPanic and Cointelegraph."""
        news_items = []
        errors = []
        
        # Try CryptoPanic first
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "auth_token": self.cryptopanic_api_key,
                    "public": "true",
                    "kind": "news",
                    "filter": "important",
                    "currencies": crypto_name.upper(),
                    "limit": 5
                }
                
                async with session.get(f"{self.cryptopanic_base_url}/posts/", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for post in data.get("results", []):
                            news_items.append({
                                "title": post["title"],
                                "url": post["url"],
                                "source": post["source"]["title"],
                                "published_at": datetime.fromisoformat(
                                    post["published_at"].replace("Z", "+00:00")
                                ),
                                "currencies": [c["code"] for c in post["currencies"]]
                            })
                    else:
                        error_text = await response.text()
                        errors.append(f"CryptoPanic API error (Status {response.status}): {error_text}")
        except Exception as e:
            errors.append(f"Failed to fetch news from CryptoPanic: {str(e)}")
        
        # If we don't have enough news items, try Cointelegraph
        if len(news_items) < 5:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        "query": crypto_name,
                        "limit": 5 - len(news_items)
                    }
                    
                    async with session.get(f"{self.cointelegraph_base_url}/news/search", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for article in data.get("data", []):
                                news_items.append({
                                    "title": article["title"],
                                    "url": article["url"],
                                    "source": "Cointelegraph",
                                    "published_at": datetime.fromisoformat(
                                        article["published_at"].replace("Z", "+00:00")
                                    ),
                                    "currencies": [crypto_name.upper()]
                                })
                        else:
                            error_text = await response.text()
                            errors.append(f"Cointelegraph API error (Status {response.status}): {error_text}")
            except Exception as e:
                errors.append(f"Failed to fetch news from Cointelegraph: {str(e)}")
        
        if not news_items and errors:
            raise Exception("\n".join(errors))
            
        return news_items[:5]  # Return at most 5 news items 