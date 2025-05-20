import os
from typing import Dict, Any
from pycoingecko import CoinGeckoAPI

class MarketService:
    def __init__(self):
        # Initialize CoinGecko client
        self.coingecko_client = CoinGeckoAPI()
        
    async def get_price(self, crypto_name: str) -> Dict[str, Any]:
        """Get current price and 24h change from CoinGecko."""
        try:
            data = self.coingecko_client.get_price(
                ids=crypto_name.lower(),
                vs_currencies="usd",
                include_24hr_change=True,
                include_24hr_vol=True
            )
            
            if not data or crypto_name.lower() not in data:
                raise Exception(f"Could not find data for {crypto_name}")
            
            return {
                "symbol": crypto_name.upper(),
                "price": data[crypto_name.lower()]["usd"],
                "price_change_24h": data[crypto_name.lower()]["usd_24h_change"],
                "volume_24h": data[crypto_name.lower()]["usd_24h_vol"]
            }
        except Exception as e:
            raise Exception(f"Failed to get price data: {str(e)}")
    
    async def get_market_data(self, crypto_name: str) -> Dict[str, Any]:
        """Get market cap and ranking from CoinGecko."""
        try:
            data = self.coingecko_client.get_coin_by_id(
                id=crypto_name.lower(),
                localization=False,
                tickers=False,
                market_data=True,
                community_data=False,
                developer_data=False
            )
            
            if not data:
                raise Exception(f"Could not find data for {crypto_name}")
            
            return {
                "name": data["name"],
                "symbol": data["symbol"].upper(),
                "market_cap": data["market_data"]["market_cap"]["usd"],
                "market_cap_rank": data["market_cap_rank"],
                "total_volume": data["market_data"]["total_volume"]["usd"],
                "circulating_supply": data["market_data"]["circulating_supply"],
                "total_supply": data["market_data"]["total_supply"]
            }
        except Exception as e:
            raise Exception(f"Failed to get market data: {str(e)}") 