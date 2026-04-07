#!/usr/bin/env python3
"""
列出指定板块下的所有子行业 (Industries)

Usage:
    python list_industries.py [sector_key]
    
Examples:
    python list_industries.py technology
    python list_industries.py healthcare
    python list_industries.py financial-services
"""

import sys
import yfinance as yf

# 有效的 sector keys
VALID_SECTORS = [
    'technology', 'healthcare', 'financial-services', 'consumer-cyclical',
    'industrials', 'communication-services', 'consumer-defensive',
    'energy', 'basic-materials', 'real-estate', 'utilities'
]


def list_industries(sector_key: str):
    """列出指定板块下的所有子行业"""
    if sector_key not in VALID_SECTORS:
        print(f"❌ 无效的板块: {sector_key}")
        print(f"\n可用的板块: {', '.join(VALID_SECTORS)}")
        return
    
    print("=" * 80)
    print(f"📂 {sector_key.upper()} Sector - 子行业列表")
    print("=" * 80)
    
    try:
        sector = yf.Sector(sector_key)
        industries = sector.industries
        
        print(f"\n共 {len(industries)} 个子行业:\n")
        print("-" * 80)
        
        counter = 1
        for idx, row in industries.iterrows():
            name = str(row.get('name', 'N/A'))
            symbol = str(row.get('symbol', 'N/A'))
            weight = row.get('market weight', 'N/A')
            print(f"{counter:2d}. {name:45s} | 权重: {weight:.2%}" if isinstance(weight, float) else f"{counter:2d}. {name:45s}")
            counter += 1
        
        print("-" * 80)
        
        # 显示每个行业的龙头公司
        print("\n📊 各子行业龙头公司:")
        print("=" * 80)
        
        for idx, row in industries.iterrows():
            name = str(row.get('name', 'N/A'))
            # 从 symbol 或 name 推断 industry key
            # 这里简化处理，使用 name 的小写替换空格和特殊字符
            industry_key = name.lower().replace(' ', '-').replace('&', '').replace('  ', '-').replace('--', '-').strip('-')
            
            print(f"\n{int(idx) if isinstance(idx, (int, float)) else idx}. {name}")
            
            try:
                industry = yf.Industry(industry_key)
                top_companies = industry.top_companies
                
                if hasattr(top_companies, 'iterrows'):
                    companies = [symbol for symbol, _ in top_companies.head(5).iterrows()]
                    print(f"   🏆 龙头: {', '.join(companies)}")
                    
            except Exception as e:
                print(f"   ⚠️ 无法获取龙头公司")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ 错误: {e}")


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
    list_industries(sector_key)
