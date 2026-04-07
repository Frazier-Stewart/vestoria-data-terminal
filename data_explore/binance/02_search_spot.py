#!/usr/bin/env python3
"""
实验: 现货交易对搜索
API: GET /api/v3/exchangeInfo (本地筛选)

功能:
- 根据关键词搜索交易对
- 支持 baseAsset 和 symbol 匹配
- 支持状态筛选 (TRADING/BREAK)
"""

import requests
from typing import List, Dict

BASE_URL = "https://api.binance.com"


class SpotSearchService:
    """现货搜索服务"""
    
    def __init__(self):
        self.symbols = []
        self.last_update = None
        self._load_symbols()
    
    def _load_symbols(self):
        """加载所有交易对"""
        try:
            url = f"{BASE_URL}/api/v3/exchangeInfo"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.symbols = data.get("symbols", [])
            self.last_update = data.get("serverTime")
            print(f"已加载 {len(self.symbols)} 个交易对")
        except Exception as e:
            print(f"加载失败: {e}")
    
    def search(
        self, 
        keyword: str = None, 
        quote_asset: str = None,
        status: str = "TRADING"
    ) -> List[Dict]:
        """
        搜索交易对
        
        Args:
            keyword: 搜索关键词，匹配 symbol 或 baseAsset
            quote_asset: 计价货币，如 USDT、BTC
            status: 交易状态，TRADING/BREAK
        """
        results = self.symbols
        
        # 状态筛选
        if status:
            results = [s for s in results if s.get("status") == status]
        
        # 计价货币筛选
        if quote_asset:
            results = [s for s in results if s.get("quoteAsset") == quote_asset]
        
        # 关键词搜索
        if keyword:
            keyword = keyword.upper()
            results = [
                s for s in results 
                if keyword in s.get("symbol", "") 
                or keyword in s.get("baseAsset", "")
            ]
        
        return results
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """获取单个交易对详情"""
        symbol = symbol.upper()
        for s in self.symbols:
            if s.get("symbol") == symbol:
                return s
        return None


def demo_search():
    """搜索演示"""
    service = SpotSearchService()
    
    # 1. 搜索 BTC 相关
    print("\n=== 搜索 BTC ===")
    results = service.search("BTC", quote_asset="USDT")
    for r in results[:5]:
        print(f"  {r['symbol']}: {r['baseAsset']}/{r['quoteAsset']}")
    
    # 2. 搜索 ETH 相关
    print("\n=== 搜索 ETH ===")
    results = service.search("ETH", quote_asset="USDT")
    for r in results[:5]:
        print(f"  {r['symbol']}: {r['baseAsset']}/{r['quoteAsset']}")
    
    # 3. 获取单个交易对详情
    print("\n=== BTCUSDT 详情 ===")
    info = service.get_symbol_info("BTCUSDT")
    if info:
        print(f"  Symbol: {info['symbol']}")
        print(f"  Status: {info['status']}")
        print(f"  Base: {info['baseAsset']}")
        print(f"  Quote: {info['quoteAsset']}")
        print(f"  Filters: {len(info.get('filters', []))} 个")


if __name__ == "__main__":
    demo_search()
