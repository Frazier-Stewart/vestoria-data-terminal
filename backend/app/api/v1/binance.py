"""Binance API routes for crypto data."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import requests

router = APIRouter(prefix="/binance", tags=["binance"])

BASE_URL = "https://api.binance.com"


@router.get("/symbols")
def get_symbols(
    quote_asset: str = Query("USDT", description="Quote asset like USDT, BTC"),
    limit: int = Query(100, ge=1, le=500, description="Max symbols to return")
):
    """
    Get trading symbols from Binance.
    
    Returns symbols filtered by quote asset and trading status.
    """
    try:
        url = f"{BASE_URL}/api/v3/exchangeInfo"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        symbols = [
            {
                "symbol": s["symbol"],
                "baseAsset": s["baseAsset"],
                "quoteAsset": s["quoteAsset"],
            }
            for s in data.get("symbols", [])
            if s.get("status") == "TRADING"
            and s.get("quoteAsset") == quote_asset
        ]
        
        return symbols[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch symbols: {str(e)}")


@router.get("/ticker/24hr")
def get_24hr_ticker(
    symbol: Optional[str] = Query(None, description="Specific symbol like BTCUSDT"),
    quote_asset: str = Query("USDT", description="Filter by quote asset"),
    limit: int = Query(50, ge=1, le=500, description="Number of results")
):
    """
    Get 24hr price change statistics.
    
    Returns price, volume, price change percentage, etc.
    Sorted by quote volume (descending) by default.
    """
    try:
        if symbol:
            # Single symbol
            url = f"{BASE_URL}/api/v3/ticker/24hr"
            response = requests.get(url, params={"symbol": symbol.upper()}, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [{
                "symbol": data["symbol"],
                "baseAsset": data["symbol"].replace(quote_asset, ""),
                "quoteAsset": quote_asset,
                "price": float(data["lastPrice"]),
                "priceChange": float(data["priceChange"]),
                "priceChangePercent": float(data["priceChangePercent"]),
                "volume": float(data["volume"]),
                "quoteVolume": float(data["quoteVolume"]),
                "high": float(data["highPrice"]),
                "low": float(data["lowPrice"]),
            }]
        else:
            # All symbols
            url = f"{BASE_URL}/api/v3/ticker/24hr"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Filter and format
            tickers = []
            for item in data:
                if not item["symbol"].endswith(quote_asset):
                    continue
                    
                tickers.append({
                    "symbol": item["symbol"],
                    "baseAsset": item["symbol"].replace(quote_asset, ""),
                    "quoteAsset": quote_asset,
                    "price": float(item["lastPrice"]),
                    "priceChange": float(item["priceChange"]),
                    "priceChangePercent": float(item["priceChangePercent"]),
                    "volume": float(item["volume"]),
                    "quoteVolume": float(item["quoteVolume"]),
                    "high": float(item["highPrice"]),
                    "low": float(item["lowPrice"]),
                })
            
            # Sort by quote volume (descending) as proxy for market cap
            tickers.sort(key=lambda x: x["quoteVolume"], reverse=True)
            
            return tickers[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")


@router.get("/search")
def search_symbols(
    q: str = Query(..., description="Search query"),
    quote_asset: str = Query("USDT", description="Quote asset"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search symbols by keyword.
    
    Searches in base asset name and symbol.
    """
    try:
        # Get all symbols
        url = f"{BASE_URL}/api/v3/exchangeInfo"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        query = q.upper()
        symbols = []
        
        for s in data.get("symbols", []):
            if s.get("status") != "TRADING":
                continue
            if quote_asset and s.get("quoteAsset") != quote_asset:
                continue
                
            base = s.get("baseAsset", "")
            symbol = s.get("symbol", "")
            
            # Match keyword
            if query in base or query in symbol:
                symbols.append({
                    "symbol": symbol,
                    "baseAsset": base,
                    "quoteAsset": s.get("quoteAsset"),
                })
        
        # Limit results
        symbols = symbols[:limit]
        
        # Get prices for matched symbols
        if symbols:
            symbols_param = ",".join([s["symbol"] for s in symbols])
            ticker_url = f"{BASE_URL}/api/v3/ticker/24hr"
            ticker_response = requests.get(
                ticker_url, 
                params={"symbols": f'[{",".join([chr(34)+s["symbol"]+chr(34) for s in symbols])}]'},
                timeout=10
            )
            ticker_response.raise_for_status()
            ticker_data = ticker_response.json()
            
            # Merge data
            ticker_map = {t["symbol"]: t for t in ticker_data}
            results = []
            for s in symbols:
                t = ticker_map.get(s["symbol"], {})
                results.append({
                    "symbol": s["symbol"],
                    "baseAsset": s["baseAsset"],
                    "quoteAsset": s["quoteAsset"],
                    "price": float(t.get("lastPrice", 0)),
                    "priceChange": float(t.get("priceChange", 0)),
                    "priceChangePercent": float(t.get("priceChangePercent", 0)),
                    "volume": float(t.get("volume", 0)),
                    "quoteVolume": float(t.get("quoteVolume", 0)),
                    "high": float(t.get("highPrice", 0)),
                    "low": float(t.get("lowPrice", 0)),
                })
            
            # Sort by quote volume
            results.sort(key=lambda x: x["quoteVolume"], reverse=True)
            return results
        
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
