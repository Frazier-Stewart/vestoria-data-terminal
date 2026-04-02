# Assets 页面重构开发规划

## 分支
`feature/assets-data-source-refactor`

## 目标架构

```
标的列表 (Assets Page)
├── Equities (股票) ⬅️ Phase 1 先做
│   ├── 数据源: Yahoo Finance (yfinance)
│   ├── 筛选: Sectors, Industries
│   └── 排序: Top Company, Market Cap, Trailing PE
├── Crypto (加密货币) ⬅️ Phase 2
│   ├── 数据源: Binance
│   └── 数据源: On-chain (地址搜索)
└── Commodities (大宗商品) ⬅️ Phase 3
    └── 数据源: Yahoo Finance / 其他
```

## Phase 1: Equities + Yahoo Finance

### 1. 前端修改

#### 1.1 Assets.tsx 重构
- [ ] 添加顶层 Tab: Equities / Crypto / Commodities
- [ ] 创建 `EquitiesPanel.tsx` 子组件
- [ ] 状态管理: `activeCategory: 'equities' | 'crypto' | 'commodities'`

#### 1.2 新建组件
- [ ] `EquitiesPanel.tsx` - 股票面板容器
- [ ] `YFinanceSearch.tsx` - Yahoo Finance 搜索组件
- [ ] `SectorFilter.tsx` - GICS Sector 筛选器
- [ ] `IndustryFilter.tsx` - Industry 筛选器
- [ ] `SortSelector.tsx` - 排序选择器

#### 1.3 新增类型定义
```typescript
// types/assets.ts
export type AssetCategory = 'equities' | 'crypto' | 'commodities';

export interface YFinanceSearchParams {
  query?: string;
  sector?: GicsSector;
  industry?: string;
  sortBy: 'market_cap' | 'trailing_pe' | 'name' | 'ticker';
  sortOrder: 'asc' | 'desc';
}

export type GicsSector = 
  | 'Technology' 
  | 'Financials' 
  | 'Health Care'
  | 'Consumer Discretionary'
  | 'Communication Services'
  | 'Industrials'
  | 'Consumer Staples'
  | 'Energy'
  | 'Utilities'
  | 'Real Estate'
  | 'Materials';
```

### 2. 后端 API 开发

#### 2.1 新增 Endpoint
```
GET /api/v1/assets/search/yfinance
  Query params:
    - q: 搜索关键词 (可选)
    - sector: GICS 板块筛选 (可选)
    - industry: 行业筛选 (可选)
    - sort_by: market_cap | trailing_pe | name
    - sort_order: asc | desc
    - limit: 返回数量 (默认 50, 最大 100)

GET /api/v1/assets/sectors
  返回: GICS 11 个板块列表

GET /api/v1/assets/industries
  Query params:
    - sector: 板块代码 (可选,不传返回全部)
  返回: Industry 列表
```

#### 2.2 服务层实现
- [ ] `YFinanceSearchService` - 封装 yfinance 搜索逻辑
- [ ] 缓存机制: 搜索结果缓存 5 分钟
- [ ] 限流: 防止频繁调用 Yahoo API

#### 2.3 数据模型
```python
# 新增 models
class AssetSearchCache(Base):
    """搜索结果缓存"""
    __tablename__ = "asset_search_cache"
    
    id = Column(Integer, primary_key=True)
    source = Column(String)  # 'yfinance'
    query_hash = Column(String)  # 查询参数哈希
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
```

### 3. 页面布局设计

```
┌─────────────────────────────────────────────────────────────┐
│  标的列表                                                    │
├─────────────────────────────────────────────────────────────┤
│  [ Equities ]  [ Crypto ]  [ Commodities ]                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Search...    │  │ [Sector ▼]   │  │ [Sort: Market ▼] │  │
│  └──────────────┘  │ [Industry ▼] │  └──────────────────┘  │
│                    └──────────────┘                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Symbol    Name         Sector       Market Cap    PE   ││
│  │ AAPL      Apple Inc.   Technology   $3.5T        32.5 ││
│  │ ...                                                     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 4. 开发步骤

#### Step 1: 基础骨架
1. 重构 Assets.tsx，添加顶层 Category Tabs
2. 创建 EquitiesPanel.tsx 空壳
3. 验证切换逻辑

#### Step 2: Yahoo Finance 搜索组件
1. 创建 YFinanceSearch.tsx
2. 实现基础搜索输入框
3. 调用后端 API `/assets/search/yfinance`

#### Step 3: 筛选器
1. SectorFilter: 11 个 GICS Sector 多选/单选
2. IndustryFilter: 动态加载（基于选中 Sector）
3. 筛选与搜索联动

#### Step 4: 排序
1. SortSelector: Market Cap / Trailing PE / Name
2. 升降序切换

#### Step 5: 结果展示
1. 表格展示搜索结果
2. 点击添加到本地标的库
3. 分页/加载更多

#### Step 6: 后端实现
1. 实现 yfinance 搜索接口
2. 添加缓存层
3. 添加 sectors/industries 接口

### 5. 关键技术点

#### yfinance 搜索实现
```python
import yfinance as yf

# 方法1: 使用 search 模块
from yfinance import Search
search = Search("apple", max_results=20)

# 方法2: 使用 ticker.info 获取详细信息
info = yf.Ticker("AAPL").info
# info['sector'] - GICS Sector
# info['industry'] - Industry
# info['marketCap'] - 市值
# info['trailingPE'] - 市盈率
```

#### Sector 和 Industry 映射
需要从 yfinance 返回的字符串映射到标准 GICS 分类。

### 6. 文件变更清单

```
frontend/src/
├── pages/
│   └── Assets.tsx (重构)
├── components/
│   └── assets/
│       ├── CategoryTabs.tsx (新增)
│       ├── EquitiesPanel.tsx (新增)
│       ├── CryptoPanel.tsx (新增, 先空壳)
│       ├── CommoditiesPanel.tsx (新增, 先空壳)
│       ├── YFinanceSearch.tsx (新增)
│       ├── SectorFilter.tsx (新增)
│       ├── IndustryFilter.tsx (新增)
│       └── SortSelector.tsx (新增)
└── types/
    └── assets.ts (新增)

backend/
├── api/
│   └── v1/
│       └── assets.py (新增 search endpoints)
├── services/
│   └── yfinance_search.py (新增)
└── models/
    └── asset_search_cache.py (新增)
```

---

## Phase 2: Crypto (预留)

- Binance API 集成
- On-chain 地址解析
- 按链筛选 (ETH, BSC, Solana...)

## Phase 3: Commodities (预留)

- 黄金、白银、原油等
- Yahoo Finance 期货数据

---

## 立即开始

准备开始 Step 1: 基础骨架重构。