import os
from typing import List, Dict, Any
import aiohttp
from datetime import datetime, timezone
import json

class NewsService:
    def __init__(self):
        self.cryptopanic_api_key = os.getenv("CRYPTOPANIC_API_KEY")
        self.cryptopanic_base_url = "https://cryptopanic.com/api/v1"
        self.cointelegraph_base_url = "https://api.cointelegraph.com/api/v1"
        
    async def get_news(self, crypto_name: str) -> List[Dict[str, Any]]:
        """Get latest news from CryptoPanic and Cointelegraph."""
        news_items = []
        
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
        except Exception as e:
            print(f"Warning: Failed to fetch news from CryptoPanic: {str(e)}")
        
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
            except Exception as e:
                print(f"Warning: Failed to fetch news from Cointelegraph: {str(e)}")
        
        return news_items[:5]  # Return at most 5 news items 