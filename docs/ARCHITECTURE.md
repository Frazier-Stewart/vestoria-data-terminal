# 数据终端 - 后端架构设计

## 架构原则

1. **通用性** - 支持任意标的类型和数据源
2. **可扩展** - 新增标的/数据源只需配置，不改核心代码
3. **单一职责** - 只做数据采集和存储，不做回测/分析
4. **服务化** - 提供 REST API 供外部系统调用

---

## 目录结构

```
backend/
├── app/
│   ├── core/                    # 核心配置
│   │   ├── config.py            # 全局配置
│   │   └── database.py          # 数据库连接
│   │
│   ├── models/                  # SQLAlchemy 模型
│   │   ├── asset.py             # 标的定义表
│   │   ├── price_data.py        # 价格数据表
│   │   ├── market_indicator.py  # 市场指标表
│   │   └── data_source.py       # 数据源配置表
│   │
│   ├── schemas/                 # Pydantic 模型
│   │   ├── asset.py
│   │   ├── price.py
│   │   └── indicator.py
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── asset_service.py     # 标的CRUD
│   │   ├── price_service.py     # 价格数据查询
│   │   ├── fetcher_manager.py   # 采集调度器
│   │   └── indicator_service.py # 指标计算
│   │
│   ├── fetchers/                # 数据获取器（插件化）
│   │   ├── base.py              # 抽象基类
│   │   ├── yfinance_fetcher.py  # Yahoo Finance
│   │   ├── binance_fetcher.py   # 币安
│   │   ├── akshare_fetcher.py   # A股数据源
│   │   └── fear_greed_fetcher.py # 情绪指标
│   │
│   ├── api/                     # API 路由
│   │   ├── v1/
│   │   │   ├── assets.py        # 标的管理
│   │   │   ├── prices.py        # 价格查询
│   │   │   ├── indicators.py    # 指标查询
│   │   │   └── update.py        # 手动触发更新
│   │   └── router.py
│   │
│   ├── cli/                     # 命令行工具
│   │   └── main.py              # 数据采集命令
│   │
│   └── main.py                  # FastAPI 入口
│
├── data/                        # 本地数据存储
│   └── prices.db
│
├── migrations/                  # Alembic 迁移
│
├── tests/
│
└── pyproject.toml         # Python 项目配置
```

---

## 核心模型设计

### 1. Asset（标的）
```python
class Asset:
    id: str              # 唯一标识，如 "BTC-USD"
    symbol: str          # 代码，如 "BTC"
    name: str            # 名称
    asset_type: str      # 类型: crypto/stock/etf/commodity/fund
    exchange: str        # 交易所/市场
    currency: str        # 计价货币
    data_source: str     # 默认数据源
    is_active: bool      # 是否活跃
    config: dict         # 额外配置(JSON)
```

### 2. PriceData（价格数据）
```python
class PriceData:
    id: int
    asset_id: str        # 关联 Asset
    date: datetime       # 日期
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str        # 周期: 1d/1h/1m
    source: str          # 数据来源
```

### 3. MarketIndicator（市场指标）
```python
class MarketIndicator:
    id: int
    indicator_type: str  # 类型: fear_greed/vix/pe/ma200
    asset_id: str        # 关联标的（可选，全局指标为空）
    date: datetime
    value: float
    level: str           # 分档: extreme_fear/fear/neutral/greed/extreme_greed
    source: str
```

---

## Fetcher 插件化设计

```python
# fetchers/base.py
class BaseFetcher(ABC):
    name: str                    # 标识名
    supported_assets: List[str]  # 支持的标的类型
    
    @abstractmethod
    async def fetch_price(self, symbol: str, start: date, end: date) -> List[PriceData]:
        pass
    
    @abstractmethod
    async def fetch_latest(self, symbol: str) -> PriceData:
        pass

# 注册表自动发现
FETCHER_REGISTRY = {}
def register_fetcher(cls):
    FETCHER_REGISTRY[cls.name] = cls
```

---

## API 设计

### 标的管理
```
GET    /api/v1/assets              # 列表
GET    /api/v1/assets/{id}         # 详情
POST   /api/v1/assets              # 创建
PUT    /api/v1/assets/{id}         # 更新
DELETE /api/v1/assets/{id}         # 删除
```

### 价格数据
```
GET /api/v1/prices?asset_id=BTC-USD&start=2025-01-01&end=2025-03-01&interval=1d
GET /api/v1/prices/latest?asset_id=BTC-USD
GET /api/v1/prices/range?asset_id=BTC-USD&days=30  # 最近N天
```

### 市场指标
```
GET /api/v1/indicators?type=fear_greed&limit=30
GET /api/v1/indicators/valuation?asset_id=BTC-USD  # 估值分档
```

### 数据更新
```
POST /api/v1/update/prices?asset_id=BTC-USD        # 手动触发更新
POST /api/v1/update/all                            # 更新全部
```

---

## 采集调度

```python
# 每日定时任务
async def daily_update():
    # 1. 获取所有活跃标的
    assets = await asset_service.get_active_assets()
    
    # 2. 按数据源分组
    by_source = groupby(assets, key=lambda a: a.data_source)
    
    # 3. 并发采集
    tasks = []
    for source, asset_list in by_source:
        fetcher = FETCHER_REGISTRY[source]()
        tasks.append(fetcher.batch_update(asset_list))
    
    await asyncio.gather(*tasks)
    
    # 4. 更新市场指标
    await indicator_service.update_all()
```

---

## 扩展思路

| 扩展点 | 实现方式 |
|-------|---------|
| 新增标的类型 | 修改 asset_type 枚举，无需改代码 |
| 新增数据源 | 继承 BaseFetcher，自动注册 |
| 新增指标 | 新增 indicator_type，复用现有表 |
| 实时数据 | 新增 WebSocket 模块，复用 fetcher |
| 数据缓存 | Redis 层，API 优先读缓存 |

---

## MVP 范围

**Phase 1（当前）**:
- 标的管理 CRUD
- Yahoo Finance fetcher
- 日K价格数据
- REST API

**Phase 2**:
- 多数据源（Binance、AKShare）
- 恐惧贪婪指数
- VIX 指标
- 200周均线计算

**Phase 3**:
- 定时任务（APScheduler）
- 数据质量监控
- 采集日志
