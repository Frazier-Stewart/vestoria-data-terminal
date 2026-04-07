"""Binance fetcher for crypto data."""
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Optional

from app.fetchers.base import BaseFetcher, AssetSearchResult
from app.fetchers.registry import register_fetcher


@register_fetcher
class BinanceFetcher(BaseFetcher):
    """Binance data fetcher for cryptocurrency."""
    
    name = "binance"
    display_name = "Binance"
    supported_asset_types = ["crypto"]
    
    BASE_URL = "https://api.binance.com"
    
    async def search(self, keyword: str, limit: int = 20) -> List[AssetSearchResult]:
        """Search symbols from Binance."""
        try:
            url = f"{self.BASE_URL}/api/v3/exchangeInfo"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            keyword_upper = keyword.upper()
            results = []
            
            for s in data.get("symbols", []):
                if s.get("status") != "TRADING":
                    continue
                    
                base = s.get("baseAsset", "")
                symbol = s.get("symbol", "")
                
                if keyword_upper in base or keyword_upper in symbol:
                    results.append(AssetSearchResult(
                        symbol=base,
                        name=f"{base} / {s.get('quoteAsset', 'USDT')}",
                        asset_type="crypto",
                        exchange="BINANCE",
                        source_symbol=symbol,
                    ))
                    
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            print(f"Binance search error: {e}")
            return []
    
    async def fetch_prices(
        self, 
        source_symbol: str, 
        start: date, 
        end: date,
        interval: str = "1d"
    ) -> List[dict]:
        """
        Fetch price data from Binance.
        
        Uses klines (candlestick) data.
        """
        # Map interval to Binance format
        interval_map = {
            "1d": "1d",
            "1w": "1w",
            "1m": "1M"
        }
        binance_interval = interval_map.get(interval, "1d")
        
        try:
            url = f"{self.BASE_URL}/api/v3/klines"
            
            # Convert dates to milliseconds timestamp
            start_ms = int(datetime.combine(start, datetime.min.time()).timestamp() * 1000)
            end_ms = int(datetime.combine(end, datetime.min.time()).timestamp() * 1000)
            
            params = {
                "symbol": source_symbol.upper(),
                "interval": binance_interval,
                "startTime": start_ms,
                "endTime": end_ms,
                "limit": 1000
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return []
            
            # Binance kline format:
            # [timestamp, open, high, low, close, volume, close_time, ...]
            prices = []
            for kline in data:
                timestamp_ms = kline[0]
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                prices.append({
                    "timestamp": timestamp,
                    "date": timestamp.date(),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                })
            
            return prices
            
        except Exception as e:
            print(f"Binance fetch error for {source_symbol}: {e}")
            return []
    
    async def fetch_latest(self, source_symbol: str) -> Optional[dict]:
        """Fetch latest price."""
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/24hr"
            params = {"symbol": source_symbol.upper()}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "timestamp": datetime.now(),
                "date": datetime.now().date(),
                "open": float(data.get("openPrice", 0)),
                "high": float(data.get("highPrice", 0)),
                "low": float(data.get("lowPrice", 0)),
                "close": float(data.get("lastPrice", 0)),
                "volume": float(data.get("volume", 0)),
            }
            
        except Exception as e:
            print(f"Binance fetch latest error for {source_symbol}: {e}")
            return None
