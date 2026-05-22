#!/usr/bin/env python3
"""
实验: 罗列所有现货交易对
API: GET /api/v3/exchangeInfo

功能:
- 获取 Binance 所有现货交易对列表
- 筛选 USDT 交易对
- 保存到本地 JSON 文件
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://api.binance.com"

def list_all_symbols(quote_asset: str = "USDT"):
    """
    获取所有现货交易对
    
    Args:
        quote_asset: 筛选计价货币，如 USDT、BTC、ETH
    """
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        symbols = data.get("symbols", [])
        
        # 筛选 TRADING 状态的交易对
        trading_symbols = [
            s for s in symbols 
            if s.get("status") == "TRADING" 
            and s.get("quoteAsset") == quote_asset
        ]
        
        print(f"总计交易对: {len(symbols)}")
        print(f"{quote_asset} 交易对 (TRADING): {len(trading_symbols)}")
        print("\n前 10 个交易对:")
        for s in trading_symbols[:10]:
            print(f"  {s['symbol']}: {s['baseAsset']}/{s['quoteAsset']}")
        
        # 保存到文件
        output = {
            "timestamp": datetime.now().isoformat(),
            "total_symbols": len(symbols),
            "trading_symbols": len(trading_symbols),
            "quote_asset": quote_asset,
            "symbols": [
                {
                    "symbol": s["symbol"],
                    "baseAsset": s["baseAsset"],
                    "quoteAsset": s["quoteAsset"],
                    "status": s["status"],
                }
                for s in trading_symbols
            ]
        }
        
        filename = f"spot_symbols_{quote_asset.lower()}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n已保存到: {filename}")
        
        return trading_symbols
        
    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    # 罗列 USDT 交易对
    symbols = list_all_symbols("USDT")
    
    # 也可以尝试其他计价货币
    # symbols = list_all_symbols("BTC")
