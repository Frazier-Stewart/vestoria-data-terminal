#!/usr/bin/env python3
"""
实验: 获取现货价格
API: GET /api/v3/ticker/price

功能:
- 获取单个交易对价格
- 获取多个交易对价格
- 获取所有交易对价格
"""

import requests
import json
from typing import List, Dict, Optional

BASE_URL = "https://api.binance.com"


def get_single_price(symbol: str) -> Optional[Dict]:
    """
    获取单个交易对价格
    
    Args:
        symbol: 交易对代码，如 BTCUSDT
    """
    url = f"{BASE_URL}/api/v3/ticker/price"
    params = {"symbol": symbol.upper()}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取 {symbol} 价格失败: {e}")
        return None


def get_multiple_prices(symbols: List[str]) -> List[Dict]:
    """
    获取多个交易对价格
    
    Args:
        symbols: 交易对代码列表
    """
    url = f"{BASE_URL}/api/v3/ticker/price"
    
    # 注意: symbols 参数需要作为 query string 传递
    # 格式: symbols=["BTCUSDT","ETHUSDT"]
    symbols_param = json.dumps([s.upper() for s in symbols])
    params = {"symbols": symbols_param}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取价格失败: {e}")
        return []


def get_all_prices() -> List[Dict]:
    """获取所有交易对价格"""
    url = f"{BASE_URL}/api/v3/ticker/price"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取所有价格失败: {e}")
        return []


def demo_prices():
    """价格获取演示"""
    
    # 1. 单个价格
    print("=== 单个价格 (BTCUSDT) ===")
    price = get_single_price("BTCUSDT")
    if price:
        print(f"  {price['symbol']}: {price['price']}")
    
    # 2. 多个价格
    print("\n=== 多个价格 ===")
    prices = get_multiple_prices(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    for p in prices:
        print(f"  {p['symbol']}: {p['price']}")
    
    # 3. 所有 USDT 价格 (前 10)
    print("\n=== 所有 USDT 价格 (前 10) ===")
    all_prices = get_all_prices()
    usdt_prices = [p for p in all_prices if p['symbol'].endswith('USDT')]
    for p in usdt_prices[:10]:
        print(f"  {p['symbol']}: {p['price']}")
    print(f"  ... 共 {len(usdt_prices)} 个 USDT 交易对")


if __name__ == "__main__":
    demo_prices()
