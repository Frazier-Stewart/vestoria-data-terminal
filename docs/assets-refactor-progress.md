# Assets 页面重构开发记录

## 开发分支
`feature/assets-data-source-refactor`

## 目标架构

```
标的列表 (Assets Page)
├── Equities (股票) ⬅️ Phase 1 进行中
│   ├── 数据源: Yahoo Finance (yfinance)
│   ├── 筛选: Sectors, Industries
│   └── 排序: Top Company, Market Cap, Trailing PE
├── Crypto (加密货币) ⬅️ Phase 2 待开发
│   ├── 数据源: Binance
│   └── 数据源: On-chain (地址搜索)
└── Commodities (大宗商品) ⬅️ Phase 3 待开发
    └── 数据源: Yahoo Finance / 其他
```

## 技术方案

### A + B 结合模式
- **预定义股票池**: GLD, SPY, QQQ, Sector SPDRs 等核心标的
- **实时搜索**: yfinance `EquityQuery` 做板块/行业筛选
- **缓存机制**: 5分钟缓存减少 API 调用

### yfinance 核心 API
```python
# 板块筛选 (screen_sector.py)
yf.Sector(key)                    # 获取板块信息
yf.Industry(key)                  # 获取行业龙头
yf.screen(EquityQuery(...))       # 自定义筛选
yf.PREDEFINED_SCREENER_QUERIES    # 预定义筛选器
```

## 开发进度

### ✅ Phase 1.1: 前端 UI 骨架 (已完成)
- [x] CategoryTabs 组件 (Equities/Crypto/Commodities)
- [x] EquitiesPanel 搜索界面
  - [x] 搜索框 (代码/名称)
  - [x] Sector 筛选器 (11个GICS板块)
  - [x] Industry 筛选器 (动态加载)
  - [x] 排序选择 (市值/PE/名称/代码)
  - [x] 结果表格展示
- [x] CryptoPanel 空壳 (预留 Binance/链上)
- [x] CommoditiesPanel 空壳 (预留 Phase 3)
- [x] 类型定义 (AssetCategory, GicsSector, etc.)

### ✅ Phase 1.2: 后端 API (已完成)
- [x] `GET /api/v1/assets/search/yfinance?q={query}` - 股票搜索
- [x] `GET /api/v1/assets/sectors` - GICS板块列表
- [x] `GET /api/v1/assets/sectors/{key}/industries` - 子行业
- [x] `GET /api/v1/assets/sectors/{key}/top-companies` - 板块龙头
- [x] `GET /api/v1/assets/industries/{key}/top-companies` - 行业龙头
- [x] `GET /api/v1/assets/predefined` - 预定义股票池
- [x] 5分钟缓存机制
- [x] 修复路由顺序问题 (避免 `/sectors` 被匹配为 `asset_id`)

### 🚧 Phase 1.3: 前后端对接 (待完成)
- [ ] 前端调用后端 API 替换 mock 数据
- [ ] Sector/Industry 动态加载
- [ ] 搜索防抖优化
- [ ] 添加「添加到追踪列表」功能
- [ ] 加载状态处理

## 文件变更

### 新增文件
```
frontend/src/
├── types/assets.ts                    # 类型定义
└── components/assets/
    ├── CategoryTabs.tsx               # 三栏切换
    ├── EquitiesPanel.tsx              # 股票面板
    ├── CryptoPanel.tsx                # 加密货币空壳
    └── CommoditiesPanel.tsx           # 大宗商品空壳

backend/app/
├── services/yfinance_search.py        # yfinance 搜索服务
└── api/v1/assets.py                   # 新增 API 端点 (已合并到现有文件)

docs/
└── assets-refactor-plan.md            # 本文件
```

### 修改文件
```
frontend/src/pages/Assets.tsx          # 完全重构
backend/app/api/v1/assets.py           # 新增搜索端点
```

## API 测试记录

### 测试通过 ✅
```bash
# 获取板块列表
GET /api/v1/assets/sectors
Response: [{"key":"technology","name":"Technology","name_zh":"信息技术",...}]

# 其他端点待测试
GET /api/v1/assets/sectors/technology/top-companies?count=20
GET /api/v1/assets/search/yfinance?q=AAPL
GET /api/v1/assets/predefined
```

## 核心代码参考

### 1. 板块筛选 (yfinance)
```python
from yfinance import EquityQuery

query = EquityQuery('and', [
    EquityQuery('eq', ['sector', 'Technology']),
    EquityQuery('eq', ['region', 'us'])
])

result = yf.screen(
    query, 
    size=100, 
    sortField='intradaymarketcap', 
    sortAsc=False
)
```

### 2. 预定义股票池
```python
PREDEFINED_TICKERS = {
    "GLD": {"name": "SPDR Gold Shares", "category": "commodities"},
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "category": "equities"},
    "XLK": {"name": "Technology Select Sector SPDR", "sector": "Technology"},
    # ... 11个Sector SPDRs + 大盘ETF
}
```

### 3. 前端组件结构
```tsx
Assets.tsx
└── CategoryTabs (Equities/Crypto/Commodities)
    └── EquitiesPanel
        ├── SearchInput
        ├── SectorFilter (11 GICS sectors)
        ├── IndustryFilter (dynamic)
        ├── SortSelector (market_cap/pe/name)
        └── ResultsTable
```

## GICS 板块对照表

| Key | 英文名 | 中文名 | Sector SPDR |
|-----|--------|--------|-------------|
| technology | Technology | 信息技术 | XLK |
| financial-services | Financials | 金融 | XLF |
| healthcare | Health Care | 医疗保健 | XLV |
| consumer-cyclical | Consumer Discretionary | 可选消费 | XLY |
| communication-services | Communication Services | 通信服务 | XLC |
| industrials | Industrials | 工业 | XLI |
| consumer-defensive | Consumer Staples | 必需消费 | XLP |
| energy | Energy | 能源 | XLE |
| basic-materials | Materials | 原材料 | XLB |
| real-estate | Real Estate | 房地产 | XLRE |
| utilities | Utilities | 公用事业 | XLU |

## 下一步计划

1. **前端对接** - EquitiesPanel 调用真实 API
2. **搜索优化** - 添加防抖、加载状态
3. **添加到追踪** - 选中股票后添加到本地 asset 库
4. **Phase 2** - Crypto 面板 (Binance API)

---
*创建于 2026-03-31*
