# Data Explore - yfinance 数据探索工具集

这个目录包含用于探索 yfinance 数据的各种脚本，方便查看板块、子行业和股票筛选。

## 环境要求

需要在项目虚拟环境中运行：

```bash
cd /path/to/data-terminal/backend
source .venv/bin/activate
python data_explore/<script>.py
```

## 脚本说明

### 1. list_sectors.py - 列出所有板块

列出所有 11 个 GICS 板块及其基本信息。

```bash
python data_explore/list_sectors.py
```

**输出示例：**
```
📊 GICS 板块列表 (共11个)

 1. Technology
    代码: technology
    子行业: 12 个
    龙头公司: 50 家
    代表公司: NVDA, AAPL, MSFT, AVGO, ORCL
...
```

### 2. list_industries.py - 列出板块下的子行业

列出指定板块下的所有子行业及其龙头公司。

```bash
python data_explore/list_industries.py <sector_key>

# 示例
python data_explore/list_industries.py technology
python data_explore/list_industries.py healthcare
python data_explore/list_industries.py financial-services
```

**可用的板块：**
- `technology` - 科技
- `healthcare` - 医疗健康
- `financial-services` - 金融服务
- `consumer-cyclical` - 非必需消费品
- `industrials` - 工业
- `communication-services` - 通信服务
- `consumer-defensive` - 必需消费品
- `energy` - 能源
- `basic-materials` - 基础材料
- `real-estate` - 房地产
- `utilities` - 公用事业

### 3. screen_sector.py - 板块股票筛选

按市值筛选指定板块的股票。

```bash
python data_explore/screen_sector.py <sector_key> [count]

# 示例
python data_explore/screen_sector.py technology 15
python data_explore/screen_sector.py healthcare 20
```

**输出示例：**
```
📊 TECHNOLOGY Sector - 市值 TOP 15

 1. NVDA   | NVIDIA Corporation             | $  165.17 |  -1.40% |   $4.01T | P/E:   33.6
 2. AAPL   | Apple Inc.                     | $  246.63 |  -0.87% |   $3.62T | P/E:   31.3
...

📊 汇总信息:
   • 总市值: $17.18 万亿
   • 万亿俱乐部: 5 家 (NVDA, AAPL, MSFT, TSM, AVGO)
   • 今日涨跌: 1 家上涨, 12 家下跌
```

### 4. screen_predefined.py - 预定义筛选器

使用 yfinance 内置的预定义筛选器。

```bash
python data_explore/screen_predefined.py <screener_name> [count]

# 示例
python data_explore/screen_predefined.py growth_technology_stocks 20
python data_explore/screen_predefined.py most_actives 15
python data_explore/screen_predefined.py day_gainers 10
```

**可用的筛选器：**

| 筛选器 | 说明 |
|--------|------|
| `growth_technology_stocks` | 科技成长股（营收增长≥25%，EPS增长≥25%） |
| `most_actives` | 最活跃股票（成交量最大） |
| `day_gainers` | 当日涨幅>3%的股票 |
| `day_losers` | 当日跌幅>2.5%的股票 |
| `aggressive_small_caps` | 激进小盘股 |
| `small_cap_gainers` | 小盘成长股 |
| `undervalued_growth_stocks` | 被低估的成长股 |
| `undervalued_large_caps` | 被低估的大盘股 |
| `most_shorted_stocks` | 做空最多的股票 |
| `conservative_foreign_funds` | 保守型海外基金 |
| `high_yield_bond` | 高收益债券基金 |
| `portfolio_anchors` | 核心持仓基金 |
| `solid_large_growth_funds` | 稳健大盘成长基金 |
| `solid_midcap_growth_funds` | 稳健中盘成长基金 |
| `top_mutual_funds` | 顶级共同基金 |

## 技术说明

### yfinance 数据结构

1. **Sector (板块)** - GICS 分类的11个一级行业
2. **Industry (子行业)** - 每个板块下的细分领域
3. **Screener (筛选器)** - 基于各种条件的股票筛选

### 数据来源

所有数据来自 Yahoo Finance，覆盖全球主要市场：
- 美股 (NYSE, NASDAQ)
- 港股 (.HK)
- 欧股 (.DE, .L, .PA 等)
- 加密货币 (BTC-USD, ETH-USD)
- 期货和指数

### 限制

- 市值数据可能有延迟
- 部分股票可能因市场关闭而无实时数据
- API 调用频率受限（避免过快请求）

## 扩展建议

可以基于这些脚本进一步开发：

1. **导出功能** - 将筛选结果导出为 CSV/JSON
2. **比较分析** - 跨板块比较估值指标
3. **历史追踪** - 定期运行并记录数据变化
4. **可视化** - 结合 matplotlib/plotly 绘制图表
