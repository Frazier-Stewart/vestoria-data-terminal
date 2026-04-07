# 查看 yfinance 支持的所有加密货币

import yfinance as yf

# 方法1：通过搜索功能查找加密货币
# yfinance 的 search 方法可以搜索 ticker
from yfinance import search

# 搜索比特币相关
results = search.search("bitcoin", max_results=20)
print("比特币相关:")
for quote in results.get('quotes', []):
    print(f"  {quote.get('symbol')}: {quote.get('shortname', quote.get('longname', 'N/A'))}")

print("\n" + "="*50 + "\n")

# 搜索以太坊相关
results = search.search("ethereum", max_results=20)
print("以太坊相关:")
for quote in results.get('quotes', []):
    print(f"  {quote.get('symbol')}: {quote.get('shortname', quote.get('longname', 'N/A'))}")

print("\n" + "="*50 + "\n")

# 方法2：常见的加密货币列表手动测试
common_cryptos = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", 
    "ADA-USD", "DOGE-USD", "DOT-USD", "AVAX-USD", "LINK-USD",
    "MATIC-USD", "UNI-USD", "LTC-USD", "BCH-USD", "ETC-USD"
]

print("测试常见加密货币 ticker 可用性:")
for symbol in common_cryptos:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        name = info.get('name', info.get('shortName', 'Unknown'))
        print(f"  ✅ {symbol}: {name}")
    except Exception as e:
        print(f"  ❌ {symbol}: 不可用 ({str(e)[:30]})")
