import os
from typing import Dict, Any
import aiohttp
from pycoingecko import CoinGeckoAPI

class MarketService:
    def __init__(self):
        # Initialize CoinGecko client
        self.coingecko_client = CoinGeckoAPI()
        
        # Initialize CoinMarketCap headers
        self.cmc_headers = {
            'X-CMC_PRO_API_KEY': os.getenv('COINMARKETCAP_API_KEY'),
            'Accept': 'application/json'
        }
        
    async def get_price(self, crypto_name: str) -> Dict[str, Any]:
        """Get current price and 24h change from CoinGecko."""
        try:
            data = self.coingecko_client.get_price(
                ids=crypto_name.lower(),
                vs_currencies="usd",
                include_24hr_change=True,
                include_24hr_vol=True
            )
            
            return {
                "symbol": crypto_name.upper(),
                "price": data[crypto_name.lower()]["usd"],
                "price_change_24h": data[crypto_name.lower()]["usd_24h_change"],
                "volume_24h": data[crypto_name.lower()]["usd_24h_vol"]
            }
        except Exception as e:
            # Fallback to CoinMarketCap if CoinGecko fails
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                        headers=self.cmc_headers,
                        params={'symbol': crypto_name.upper()}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            quote = data['data'][crypto_name.upper()]['quote']['USD']
                            return {
                                "symbol": crypto_name.upper(),
                                "price": quote['price'],
                                "price_change_24h": quote['percent_change_24h'],
                                "volume_24h": quote['volume_24h']
                            }
                        else:
                            raise Exception(f"CoinMarketCap API error: {response.status}")
            except Exception as e2:
                raise Exception(f"Failed to get price data: {str(e2)}")
    
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
            # Fallback to CoinMarketCap if CoinGecko fails
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                        headers=self.cmc_headers,
                        params={'symbol': crypto_name.upper()}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            quote = data['data'][crypto_name.upper()]['quote']['USD']
                            return {
                                "name": data['data'][crypto_name.upper()]['name'],
                                "symbol": crypto_name.upper(),
                                "market_cap": quote['market_cap'],
                                "market_cap_rank": data['data'][crypto_name.upper()]['cmc_rank'],
                                "total_volume": quote['volume_24h'],
                                "circulating_supply": data['data'][crypto_name.upper()]['circulating_supply'],
                                "total_supply": data['data'][crypto_name.upper()]['total_supply']
                            }
                        else:
                            raise Exception(f"CoinMarketCap API error: {response.status}")
            except Exception as e2:
                raise Exception(f"Failed to get market data: {str(e2)}") 