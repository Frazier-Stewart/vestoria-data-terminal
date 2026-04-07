#!/usr/bin/env python3
"""
使用 yfinance 预定义的股票筛选器

Usage:
    python screen_predefined.py [screener_name] [count]
    
Examples:
    python screen_predefined.py growth_technology_stocks 20
    python screen_predefined.py most_actives 15
    python screen_predefined.py day_gainers 10
    
Available screeners:
    - aggressive_small_caps
    - day_gainers
    - day_losers
    - growth_technology_stocks
    - most_actives
    - most_shorted_stocks
    - small_cap_gainers
    - undervalued_growth_stocks
    - undervalued_large_caps
"""

import sys
import yfinance as yf


def format_market_cap(mkt_cap):
    """格式化市值显示"""
    if isinstance(mkt_cap, (int, float)):
        if mkt_cap >= 1e12:
            return f"${mkt_cap/1e12:.2f}T"
        elif mkt_cap >= 1e9:
            return f"${mkt_cap/1e9:.1f}B"
        else:
            return f"${mkt_cap/1e6:.1f}M"
    return 'N/A'


def format_change(change):
    """格式化涨跌幅显示"""
    if isinstance(change, (int, float)):
        return f"{change:+.2f}%"
    return 'N/A'


def screen_predefined(screener_name: str, count: int = 20):
    """使用预定义筛选器"""
    
    # 检查是否是有效的筛选器
    available_screeners = list(yf.PREDEFINED_SCREENER_QUERIES.keys())
    
    if screener_name not in available_screeners:
        print(f"❌ 无效的筛选器: {screener_name}")
        print(f"\n可用的筛选器:")
        for s in available_screeners:
            print(f"  - {s}")
        return
    
    print("=" * 100)
    print(f"🔍 预定义筛选器: {screener_name}")
    print("=" * 100)
    
    # 显示筛选器配置
    config = yf.PREDEFINED_SCREENER_QUERIES[screener_name]
    print(f"\n筛选配置:")
    print(f"  {config}")
    print()
    
    try:
        result = yf.screen(screener_name, count=count)
        quotes = result.get('quotes', [])
        
        print(f"找到 {len(quotes)} 只股票\n")
        print("-" * 100)
        
        for i, item in enumerate(quotes, 1):
            symbol = item.get('symbol', 'N/A')
            name = item.get('longName', item.get('shortName', 'N/A'))
            price = item.get('regularMarketPrice', 'N/A')
            change = item.get('regularMarketChangePercent')
            mkt_cap = item.get('marketCap')
            volume = item.get('regularMarketVolume')
            
            mkt_cap_str = format_market_cap(mkt_cap)
            change_str = format_change(change)
            
            if isinstance(volume, (int, float)):
                volume_str = f"{volume/1e6:.1f}M"
            else:
                volume_str = 'N/A'
            
            print(f"{i:2d}. {symbol:6s} | {name[:35]:35s} | ${str(price):>9} | {change_str:>7} | {mkt_cap_str:>8} | 成交: {volume_str}")
        
        print("-" * 100)
        
        # 统计
        print("\n📊 统计:")
        
        # 市值分布
        valid_caps = [q.get('marketCap', 0) for q in quotes if isinstance(q.get('marketCap'), (int, float))]
        if valid_caps:
            avg_cap = sum(valid_caps) / len(valid_caps)
            print(f"   • 平均市值: {format_market_cap(avg_cap)}")
        
        # 涨跌分布
        up = sum(1 for q in quotes if isinstance(q.get('regularMarketChangePercent'), (int, float)) and q.get('regularMarketChangePercent') > 0)
        down = sum(1 for q in quotes if isinstance(q.get('regularMarketChangePercent'), (int, float)) and q.get('regularMarketChangePercent') < 0)
        print(f"   • 涨跌分布: {up} 家上涨, {down} 家下跌")
        
        print("\n" + "=" * 100)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def print_usage():
    """打印使用说明"""
    print(__doc__)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    screener_name = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    screen_predefined(screener_name, count)
