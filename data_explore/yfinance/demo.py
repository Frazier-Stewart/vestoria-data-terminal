#!/usr/bin/env python3
"""
快速演示 - Data Explore 工具集

一键运行所有探索功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from list_sectors import list_all_sectors
from list_industries import list_industries
from screen_sector import screen_sector


def main():
    print("=" * 80)
    print("🚀 Data Explore 快速演示")
    print("=" * 80)
    
    # 1. 列出所有板块
    print("\n\n")
    list_all_sectors()
    
    # 2. 列出 Technology 板块的子行业
    print("\n\n")
    print("输入任意键继续查看 Technology 板块子行业...")
    input()
    list_industries("technology")
    
    # 3. 筛选 Technology 板块 TOP 10
    print("\n\n")
    print("输入任意键继续查看 Technology 板块 TOP 10 股票...")
    input()
    screen_sector("technology", 10)
    
    print("\n" + "=" * 80)
    print("✅ 演示完成！")
    print("=" * 80)
    print("\n更多功能请查看 README.md")


if __name__ == "__main__":
    main()
