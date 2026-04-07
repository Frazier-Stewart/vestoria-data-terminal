# Binance 现货数据探索

基于 Binance API 的现货数据获取实验脚本。

## 脚本列表

| 脚本 | 功能 | API Endpoint |
|------|------|--------------|
| `01_list_spot_symbols.py` | 罗列所有现货交易对 | `/api/v3/exchangeInfo` |
| `02_search_spot.py` | 现货交易对搜索 | `/api/v3/exchangeInfo` |
| `03_fetch_prices.py` | 获取现货价格 | `/api/v3/ticker/price` |
| `04_fetch_prices_chunked.py` | 分块获取价格 (大量数据) | `/api/v3/ticker/price` |

## 快速开始

```bash
cd data_explore/binance

# 1. 罗列所有 USDT 交易对
python3 01_list_spot_symbols.py

# 2. 搜索交易对
python3 02_search_spot.py

# 3. 获取价格
python3 03_fetch_prices.py

# 4. 分块获取大量价格
python3 04_fetch_prices_chunked.py
```

## API 说明

### 1. 交易对列表
- Endpoint: `GET /api/v3/exchangeInfo`
- 无需认证
- 返回所有交易对信息

### 2. 价格获取
- Endpoint: `GET /api/v3/ticker/price`
- 无需认证
- 支持单个、多个或全部交易对

### 3. 分块策略
- 每批最多 100 个交易对
- 支持顺序和并发两种模式
- 建议并发数: 5

## 输出文件

- `spot_symbols_usdt.json` - USDT 交易对列表

## 参考

- [Binance API Docs](https://binance-docs.github.io/apidocs/spot/en/)
- [SKILL.md](./skills/spot/SKILL.md) - 详细 API 说明
