import os
from typing import List, Dict, Any
import aiohttp
from datetime import datetime, timezone
import json
import feedparser
import asyncio
import time
from bs4 import BeautifulSoup
import re

class NewsService:
    def __init__(self):
        self.rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://coindesk.com/arc/outboundfeeds/rss/",
            "https://decrypt.co/feed"
        ]
        
    
        self.crypto_aliases = {
            "bitcoin": ["btc", "bitcoin", "bitcoin price", "bitcoin news"],
            "ethereum": ["eth", "ethereum", "ethereum price", "ethereum news", "eth2", "eth 2.0"],
            "solana": ["sol", "solana", "solana price", "solana news"],
            "cardano": ["ada", "cardano", "cardano price", "cardano news"],
            "polkadot": ["dot", "polkadot", "polkadot price", "polkadot news"],
            "ripple": ["xrp", "ripple", "ripple price", "ripple news"],
            "dogecoin": ["doge", "dogecoin", "dogecoin price", "dogecoin news"],
            "binance coin": ["bnb", "binance coin", "binance coin price", "binance coin news"],
            "avalanche": ["avax", "avalanche", "avalanche price", "avalanche news"],
            "polygon": ["matic", "polygon", "polygon price", "polygon news"]
        }
        
    async def get_news(self, crypto_name: str, user_prompt: str = None) -> List[Dict[str, Any]]:
        """Get latest news from multiple crypto RSS feeds."""
        try:
            news_items = []
            tasks = []
            
        
            search_terms = self._get_search_terms(crypto_name)
        
            prompt_keywords = self._extract_keywords(user_prompt) if user_prompt else []
            
            for feed_url in self.rss_feeds:
                tasks.append(self._fetch_feed(feed_url, search_terms, prompt_keywords))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for feed_results in results:
                if isinstance(feed_results, list):
                    news_items.extend(feed_results)
            
            news_items.sort(key=lambda x: x['published_at'], reverse=True)
            
            print(f"Found {len(news_items)} news items")
            return news_items[:10]
            
        except Exception as e:
            print(f"Failed to fetch news: {str(e)}")
            return []
            
    def _get_search_terms(self, crypto_name: str) -> List[str]:
        """Get relevant search terms for a cryptocurrency."""
        crypto_name = crypto_name.lower()
        
        for main_name, aliases in self.crypto_aliases.items():
            if crypto_name in aliases:
                return aliases
        
        return [
            crypto_name,
            crypto_name.upper(),
            crypto_name.capitalize(),
            f"{crypto_name} price",
            f"{crypto_name} news"
        ]

    def _extract_keywords(self, prompt: str) -> List[str]:
        """Extract relevant keywords from user prompt."""
        if not prompt:
            return []
            
        words = re.findall(r'\b\w+\b', prompt.lower())
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'as', 'of', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must', 'what', 'when', 'where', 'who', 'whom', 'which', 'why', 'how'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
            
    async def _fetch_feed(self, feed_url: str, search_terms: List[str], prompt_keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed."""
        try:
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, lambda: feedparser.parse(feed_url))
            
            news_items = []
            async with aiohttp.ClientSession() as session:
                for entry in feed.entries[:30]:  
                    title_lower = entry.title.lower()
                    desc_lower = entry.description.lower()
                    
                    is_relevant = False
                    main_crypto = search_terms[0].split()[0].upper()
                    
                    requested_mentions = sum(1 for term in search_terms if term.lower() in title_lower + desc_lower)
                    
                    if 'cointelegraph.com' in feed_url and prompt_keywords:
                        try:
                            async with session.get(entry.link) as response:
                                if response.status == 200:
                                    html = await response.text()
                                    soup = BeautifulSoup(html, 'html.parser')
                                    
                                    article_content = soup.find('div', {'class': 'post__content'})
                                    if article_content:
                                        article_text = article_content.get_text().lower()
                                        
                                        keyword_matches = sum(1 for keyword in prompt_keywords if keyword in article_text)
                                        if keyword_matches >= 2:  
                                            is_relevant = True
                        except Exception as e:
                            print(f"Failed to fetch article content: {str(e)}")
                    
                    if not is_relevant:
                        is_relevant = (any(term.lower() in title_lower for term in search_terms) or 
                                     requested_mentions >= 2)
                    
                    if is_relevant:
                        try:
                            published_time = datetime.fromtimestamp(
                                time.mktime(entry.published_parsed)
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        except (AttributeError, TypeError):
                            published_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        news_items.append({
                            "title": entry.title,
                            "url": entry.link,
                            "source": feed_url.split("//")[1].split("/")[0],
                            "published_at": published_time,
                            "currencies": [main_crypto]
                        })
            
            return news_items
            
        except Exception as e:
            print(f"Failed to fetch feed {feed_url}: {str(e)}")
            return [] 
