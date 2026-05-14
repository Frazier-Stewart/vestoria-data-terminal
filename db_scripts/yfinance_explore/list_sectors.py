#!/usr/bin/env python3
"""
列出所有可用的 GICS 板块 (Sectors)

Usage:
    python list_sectors.py
"""

import yfinance as yf

# 完整的11个GICS板块
SECTORS = [
    'technology',
    'healthcare', 
    'financial-services',
    'consumer-cyclical',
    'industrials',
    'communication-services',
    'consumer-defensive',
    'energy',
    'basic-materials',
    'real-estate',
    'utilities'
]

def list_all_sectors():
    """列出所有板块及其基本信息"""
    print("=" * 80)
    print("📊 GICS 板块列表 (共11个)")
    print("=" * 80)

    for i, key in enumerate(SECTORS, 1):
        try:
            sector = yf.Sector(key)
            name = sector.name
            
            # 获取子行业数量
            industries = sector.industries
            ind_count = len(industries) if hasattr(industries, '__len__') else 'N/A'
            
            # 获取龙头公司数量
            top_companies = sector.top_companies
            company_count = len(top_companies) if hasattr(top_companies, '__len__') else 'N/A'
            
            print(f"\n{i:2d}. {name}")
            print(f"    代码: {key}")
            print(f"    子行业: {ind_count} 个")
            print(f"    龙头公司: {company_count} 家")
            
            # 显示前5个龙头公司
            if hasattr(top_companies, 'iterrows'):
                companies = [symbol for symbol, _ in top_companies.head(5).iterrows()]
                print(f"    代表公司: {', '.join(companies)}")
                
        except Exception as e:
            print(f"\n{i:2d}. {key} - 错误: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    list_all_sectors()
