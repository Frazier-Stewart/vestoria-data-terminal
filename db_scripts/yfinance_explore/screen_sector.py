#!/usr/bin/env python3
"""
筛选指定板块的股票并按市值排序

Usage:
    python screen_sector.py [sector_key] [count]
    
Examples:
    python screen_sector.py technology 15
    python screen_sector.py healthcare 20
    python screen_sector.py financial-services 10
"""

import sys
import yfinance as yf
from yfinance import EquityQuery

# 有效的 sector keys
VALID_SECTORS = [
    'technology', 'healthcare', 'financial-services', 'consumer-cyclical',
    'industrials', 'communication-services', 'consumer-defensive',
    'energy', 'basic-materials', 'real-estate', 'utilities'
]


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


def screen_sector(sector_key: str, count: int = 15):
    """筛选指定板块的股票并按市值排序"""
    if sector_key not in VALID_SECTORS:
        print(f"❌ 无效的板块: {sector_key}")
        print(f"\n可用的板块: {', '.join(VALID_SECTORS)}")
        return
    
    print("=" * 100)
    print(f"📊 {sector_key.upper()} Sector - 市值 TOP {count}")
    print("=" * 100)
    
    try:
        # 使用自定义 EquityQuery 筛选板块 + 美国市场
        query = EquityQuery('and', [
            EquityQuery('eq', ['sector', sector_key.replace('-', ' ').title().replace(' ', '')]),
            EquityQuery('eq', ['region', 'us'])
        ])
        
        result = yf.screen(query, size=max(count, 100), sortField='intradaymarketcap', sortAsc=False)
        quotes = result.get('quotes', [])
        
        # 如果没有结果，尝试简化查询
        if not quotes:
            query = EquityQuery('eq', ['sector', sector_key.replace('-', ' ').title()])
            result = yf.screen(query, size=max(count, 100), sortField='intradaymarketcap', sortAsc=False)
            quotes = result.get('quotes', [])
        
        print(f"\n✅ 从 {len(quotes)} 只股票中筛选出市值 TOP {count}\n")
        print("-" * 100)
        
        # 显示结果
        for i, item in enumerate(quotes[:count], 1):
            symbol = item.get('symbol', 'N/A')
            name = item.get('longName', item.get('shortName', 'N/A'))
            price = item.get('regularMarketPrice', 'N/A')
            change = item.get('regularMarketChangePercent')
            mkt_cap = item.get('marketCap')
            pe_ratio = item.get('trailingPE', item.get('forwardPE', 'N/A'))
            
            mkt_cap_str = format_market_cap(mkt_cap)
            change_str = format_change(change)
            pe_str = f"{pe_ratio:.1f}" if isinstance(pe_ratio, (int, float)) else 'N/A'
            
            print(f"{i:2d}. {symbol:6s} | {name[:35]:35s} | ${str(price):>9} | {change_str:>7} | {mkt_cap_str:>8} | P/E: {pe_str:>6}")
        
        print("-" * 100)
        
        # 汇总统计
        print("\n📊 汇总信息:")
        
        # 计算总市值
        valid_caps = [q.get('marketCap', 0) for q in quotes[:count] if isinstance(q.get('marketCap'), (int, float))]
        if valid_caps:
            total_cap = sum(valid_caps)
            print(f"   • 总市值: ${total_cap/1e12:.2f} 万亿")
        
        # 市值分层
        trillion_club = [q for q in quotes[:count] if isinstance(q.get('marketCap'), (int, float)) and q.get('marketCap') >= 1e12]
        hundred_billion = [q for q in quotes[:count] if isinstance(q.get('marketCap'), (int, float)) and 1e11 <= q.get('marketCap') < 1e12]
        
        if trillion_club:
            print(f"   • 万亿俱乐部: {len(trillion_club)} 家 ({', '.join([q.get('symbol') for q in trillion_club])})")
        if hundred_billion:
            print(f"   • 千亿俱乐部: {len(hundred_billion)} 家")
        
        # 今日涨跌统计
        up = sum(1 for q in quotes[:count] if isinstance(q.get('regularMarketChangePercent'), (int, float)) and q.get('regularMarketChangePercent') > 0)
        down = sum(1 for q in quotes[:count] if isinstance(q.get('regularMarketChangePercent'), (int, float)) and q.get('regularMarketChangePercent') < 0)
        flat = count - up - down
        print(f"   • 今日涨跌: {up} 家上涨, {down} 家下跌, {flat} 家平盘")
        
        print("\n" + "=" * 100)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def print_usage():
    """打印使用说明"""
    print(__doc__)
    print("\n可用的板块:")
    for s in VALID_SECTORS:
        print(f"  - {s}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    sector_key = sys.argv[1].lower()
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    
    screen_sector(sector_key, count)
