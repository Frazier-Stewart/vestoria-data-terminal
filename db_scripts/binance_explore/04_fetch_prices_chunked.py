#!/usr/bin/env python3
"""
实验: 分块获取现货价格 (处理大量交易对)
API: GET /api/v3/ticker/price (批量)

功能:
- 将大量交易对分批获取
- 避免单次请求过大
- 支持并发请求优化速度
"""

import requests
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://api.binance.com"
CHUNK_SIZE = 100  # 每批最多 100 个交易对


def fetch_price_chunk(symbols: List[str]) -> List[Dict]:
    """
    获取一批交易对的价格
    
    Args:
        symbols: 交易对代码列表 (最多 100 个)
    """
    url = f"{BASE_URL}/api/v3/ticker/price"
    symbols_param = json.dumps([s.upper() for s in symbols])
    params = {"symbols": symbols_param}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取价格失败 ({len(symbols)} 个): {e}")
        return []


def fetch_prices_sequential(symbols: List[str]) -> List[Dict]:
    """
    顺序分块获取价格
    
    Args:
        symbols: 交易对代码列表
    """
    all_prices = []
    chunks = [symbols[i:i + CHUNK_SIZE] for i in range(0, len(symbols), CHUNK_SIZE)]
    
    print(f"共 {len(symbols)} 个交易对，分 {len(chunks)} 批获取")
    
    for i, chunk in enumerate(chunks):
        print(f"  第 {i+1}/{len(chunks)} 批...", end=" ")
        prices = fetch_price_chunk(chunk)
        all_prices.extend(prices)
        print(f"成功 {len(prices)}")
        
        # 避免速率限制，添加延迟
        if i < len(chunks) - 1:
            time.sleep(0.1)
    
    return all_prices


def fetch_prices_concurrent(symbols: List[str], max_workers: int = 5) -> List[Dict]:
    """
    并发分块获取价格
    
    Args:
        symbols: 交易对代码列表
        max_workers: 并发数
    """
    chunks = [symbols[i:i + CHUNK_SIZE] for i in range(0, len(symbols), CHUNK_SIZE)]
    all_prices = []
    
    print(f"共 {len(symbols)} 个交易对，分 {len(chunks)} 批，并发 {max_workers}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {
            executor.submit(fetch_price_chunk, chunk): i 
            for i, chunk in enumerate(chunks)
        }
        
        for future in as_completed(future_to_chunk):
            chunk_idx = future_to_chunk[future]
            try:
                prices = future.result()
                all_prices.extend(prices)
                print(f"  第 {chunk_idx+1} 批完成: {len(prices)} 个")
            except Exception as e:
                print(f"  第 {chunk_idx+1} 批失败: {e}")
    
    return all_prices


def get_all_usdt_symbols() -> List[str]:
    """获取所有 USDT 交易对代码"""
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        symbols = [
            s["symbol"] for s in data.get("symbols", [])
            if s.get("status") == "TRADING" 
            and s.get("quoteAsset") == "USDT"
        ]
        return symbols
    except Exception as e:
        print(f"获取交易对列表失败: {e}")
        return []


def demo_chunked_fetch():
    """分块获取演示"""
    
    # 获取所有 USDT 交易对
    symbols = get_all_usdt_symbols()
    if not symbols:
        print("没有获取到交易对")
        return
    
    print(f"共 {len(symbols)} 个 USDT 交易对\n")
    
    # 1. 顺序获取 (测试前 300 个)
    test_symbols = symbols[:300]
    print("=== 顺序获取 (前 300 个) ===")
    start = time.time()
    prices = fetch_prices_sequential(test_symbols)
    elapsed = time.time() - start
    print(f"成功: {len(prices)} 个，耗时: {elapsed:.2f}s\n")
    
    # 2. 并发获取 (全部)
    print("=== 并发获取 (全部) ===")
    start = time.time()
    prices = fetch_prices_concurrent(symbols, max_workers=5)
    elapsed = time.time() - start
    print(f"成功: {len(prices)} 个，耗时: {elapsed:.2f}s\n")
    
    # 显示前 10 个价格
    print("=== 价格示例 (前 10) ===")
    for p in prices[:10]:
        print(f"  {p['symbol']}: {p['price']}")


if __name__ == "__main__":
    demo_chunked_fetch()
