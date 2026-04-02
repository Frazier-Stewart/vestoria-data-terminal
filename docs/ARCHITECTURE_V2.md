# 数据终端 - MVP 后端架构设计（V2）

## MVP 功能范围

1. **标的搜索** - 从各数据源实时搜索标的
2. **数据源浏览** - 列出各数据源支持的标的
3. **关注列表** - 添加标的到关注列表，每日自动更新数据
4. **历史走势** - 日线数据，支持 TradingView 图表格式
5. **指标模板** - 通用模板系统，支持创建新指标

---

## 目录结构

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py            # 全局配置
│   │   ├── database.py          # 数据库连接
│   │   └── exceptions.py        # 自定义异常
│   │
│   ├── models/                  # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── asset.py             # 标的定义
│   │   ├── watchlist.py         # 关注列表
│   │   ├── price_data.py        # 价格数据
│   │   ├── indicator.py         # 指标定义
│   │   ├── indicator_value.py   # 指标数值
│   │   └── data_source.py       # 数据源配置
│   │
│   ├── schemas/                 # Pydantic 模型
│   │   ├── asset.py
│   │   ├── watchlist.py
│   │   ├── price.py
│   │   ├── indicator.py
│   │   └── tradingview.py       # TradingView 数据格式
│   │
│   ├── services/
│   │   ├── asset_service.py     # 标的业务
│   │   ├── watchlist_service.py # 关注列表业务
│   │   ├── price_service.py     # 价格数据业务
│   │   ├── indicator_service.py # 指标计算业务
│   │   ├── search_service.py    # 跨源搜索聚合
│   │   └── scheduler_service.py # 定时更新调度
│   │
│   ├── fetchers/                # 数据源适配器
│   │   ├── __init__.py
│   │   ├── base.py              # 抽象基类
│   │   ├── registry.py          # 注册表
│   │   ├── yfinance_fetcher.py  # Yahoo Finance
│   │   ├── binance_fetcher.py   # 币安
│   │   ├── akshare_fetcher.py   # A股
│   │   └── coingecko_fetcher.py # CoinGecko(情绪指标)
│   │
│   ├── indicators/              # 指标计算引擎
│   │   ├── __init__.py
│   │   ├── base.py              # 指标基类
│   │   ├── registry.py          # 指标注册表
│   │   ├── templates/           # 指标模板
│   │   │   ├── ma_template.py   # 均线模板
│   │   │   ├── pe_template.py   # 估值模板
│   │   │   └── custom_template.py
│   │   └── builtin/             # 内置指标
│   │       ├── ma200.py         # 200周均线
│   │       ├── fear_greed.py    # 恐慌贪婪
│   │       └── pe_valuation.py  # PE估值
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── search.py        # 搜索接口
│   │   │   ├── assets.py        # 标的管理
│   │   │   ├── watchlist.py     # 关注列表
│   │   │   ├── prices.py        # 价格数据
│   │   │   ├── indicators.py    # 指标接口
│   │   │   └── datasources.py   # 数据源接口
│   │   └── router.py
│   │
│   ├── cli/
│   │   └── main.py              # 命令行工具
│   │
│   └── main.py                  # FastAPI 入口
│
├── alembic/                     # 数据库迁移
├── data/
│   └── data_terminal.db
├── tests/
└── pyproject.toml         # Python 项目配置
```

---

## 核心模型设计

### 1. Asset（标的）
```python
class Asset(Base):
    id: str              # 唯一标识，如 "BTC-USD"
    symbol: str          # 代码，如 "BTC"
    name: str            # 名称，如 "Bitcoin USD"
    asset_type: str      # 类型: crypto/stock/etf/commodity/fund/index
    exchange: str        # 交易所，如 "NASDAQ"
    currency: str        # 计价货币，如 "USD"
    country: str         # 所属市场，如 "US"
    data_source: str     # 数据源标识，如 "yfinance"
    source_symbol: str   # 数据源原始代码，如 "BTC-USD"
    is_active: bool      # 是否可交易
    
    watchlists: List[Watchlist]  # 关联的关注列表
```

### 2. Watchlist（关注列表）
```python
class Watchlist(Base):
    id: int
    name: str            # 列表名称，如 "我的组合"
    description: str     # 描述
    is_default: bool     # 是否默认列表
    auto_update: bool    # 是否自动更新
    
    assets: List[Asset]  # 多对多关系
    
    created_at: datetime
    updated_at: datetime
```

### 3. PriceData（价格数据 - 支持多周期）
```python
class PriceData(Base):
    id: int
    asset_id: str        # 关联 Asset
    
    # 时间维度
    timestamp: datetime  # 精确时间
    date: date           # 日期（方便查询）
    interval: str        # 周期: 1d/1w/1m
    
    # OHLCV
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # 元数据
    source: str          # 数据来源
    created_at: datetime
    
    __table_args__ = (
        UniqueConstraint('asset_id', 'date', 'interval'),
        Index('idx_price_query', 'asset_id', 'interval', 'date'),
    )
```

### 4. IndicatorTemplate（指标模板）
```python
class IndicatorTemplate(Base):
    id: str              # 模板标识，如 "moving_average"
    name: str            # 显示名称
    description: str     # 描述
    category: str        # 分类: trend/valuation/sentiment/volatility
    
    # 模板配置（JSON Schema）
    config_schema: dict  # 参数定义，如 {"period": {"type": "int", "default": 200}}
    
    # 计算配置
    calculator_path: str # 计算类路径，如 "indicators.builtin.ma200"
    
    is_builtin: bool     # 是否内置
    is_active: bool
```

### 5. Indicator（指标实例）
```python
class Indicator(Base):
    id: str              # 实例标识，如 "BTC_MA200"
    name: str            # 显示名称
    template_id: str     # 关联模板
    asset_id: str        # 关联标的（可为空表示全局指标）
    
    # 实例配置
    config: dict         # 具体参数，如 {"period": 200, "unit": "week"}
    
    # 分档配置（JSON）
    level_config: dict   # 如 {"cheap": -30, "fair": 0, "expensive": 30}
    
    is_active: bool
    auto_update: bool
```

### 6. IndicatorValue（指标数值）
```python
class IndicatorValue(Base):
    id: int
    indicator_id: str    # 关联指标
    date: date           # 日期
    
    value: float         # 原始值
    level: str           # 分档: extreme_cheap/cheap/fair/expensive/extreme_expensive
    
    # 额外数据（JSON）
    metadata: dict       # 如 {"percentile": 0.85, "history_high": 100}
    
    source: str
    created_at: datetime
```

---

## Fetcher 设计（支持搜索）

```python
# fetchers/base.py
class BaseFetcher(ABC):
    name: str
    display_name: str
    supported_asset_types: List[str]
    
    # ========== 搜索能力 ==========
    @abstractmethod
    async def search(self, keyword: str, limit: int = 20) -> List[AssetSearchResult]:
        """从数据源搜索标的"""
        pass
    
    @abstractmethod
    async def list_assets(self, asset_type: Optional[str] = None) -> List[Asset]:
        """列出数据源支持的标的"""
        pass
    
    # ========== 数据获取 ==========
    @abstractmethod
    async def fetch_price(
        self, 
        source_symbol: str, 
        start: date, 
        end: date,
        interval: str = "1d"
    ) -> List[PriceData]:
        pass
    
    async def fetch_latest(self, source_symbol: str) -> Optional[PriceData]:
        """获取最新价格（默认实现可覆盖）"""
        pass

@dataclass
class AssetSearchResult:
    symbol: str
    name: str
    asset_type: str
    exchange: str
    source_symbol: str  # 数据源原始代码
    extra: dict         # 额外信息
```

---

## 指标模板系统

```python
# indicators/base.py
class BaseIndicator(ABC):
    template_id: str
    template_name: str
    
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    async def calculate(
        self, 
        asset: Asset, 
        start: date, 
        end: date
    ) -> List[IndicatorValue]:
        """计算指标值"""
        pass
    
    @abstractmethod
    def classify_level(self, value: float) -> str:
        """分档：extreme_cheap/cheap/fair/expensive/extreme_expensive"""
        pass

# 注册表
INDICATOR_REGISTRY = {}
def register_indicator(cls):
    INDICATOR_REGISTRY[cls.template_id] = cls
    return cls

# 示例：200周均线指标
@register_indicator
class MA200Indicator(BaseIndicator):
    template_id = "ma200"
    template_name = "200周均线偏离度"
    
    async def calculate(self, asset, start, end):
        period = self.config.get("period", 200)
        prices = await get_prices(asset.id, interval="1w")
        ma = calculate_ma(prices, period)
        deviation = (prices[-1].close - ma) / ma * 100
        
        return [IndicatorValue(
            value=deviation,
            level=self.classify_level(deviation)
        )]
    
    def classify_level(self, value):
        if value < -50: return "extreme_cheap"
        if value < -20: return "cheap"
        if value < 20: return "fair"
        if value < 50: return "expensive"
        return "extreme_expensive"
```

---

## API 设计

### 搜索与发现
```
GET  /api/v1/search?q={keyword}&limit=20           # 跨源搜索
GET  /api/v1/datasources                           # 列出数据源
GET  /api/v1/datasources/{name}/assets             # 数据源支持的标的
GET  /api/v1/datasources/{name}/search?q={keyword} # 单源搜索
```

### 关注列表
```
GET    /api/v1/watchlists                          # 列表
POST   /api/v1/watchlists                          # 创建
GET    /api/v1/watchlists/{id}                     # 详情
PUT    /api/v1/watchlists/{id}                     # 更新
DELETE /api/v1/watchlists/{id}                     # 删除

POST   /api/v1/watchlists/{id}/assets              # 添加标的
DELETE /api/v1/watchlists/{id}/assets/{asset_id}   # 移除标的
GET    /api/v1/watchlists/{id}/prices              # 获取关注列表所有标的价格
```

### 价格数据
```
GET /api/v1/prices?asset_id=BTC-USD&start=&end=&interval=1d
GET /api/v1/prices/latest?asset_ids=BTC-USD,SPY    # 批量最新价

# TradingView 格式（轻量级图表库）
GET /api/v1/prices/tv/history?symbol=BTC-USD&resolution=D&from=&to=
GET /api/v1/prices/tv/config                       # TradingView 配置
GET /api/v1/prices/tv/symbols?symbol=BTC-USD       # 标的详情
```

### 指标
```
GET  /api/v1/indicators/templates                  # 指标模板列表
POST /api/v1/indicators                            # 创建指标实例
GET  /api/v1/indicators                            # 指标实例列表
GET  /api/v1/indicators/{id}/values?start=&end=   # 指标数值
POST /api/v1/indicators/{id}/calculate             # 手动触发计算
```

### 更新任务
```
POST /api/v1/tasks/update/watchlist/{id}           # 更新关注列表
POST /api/v1/tasks/update/all                      # 更新全部
GET  /api/v1/tasks/status/{task_id}                # 任务状态
```

---

## TradingView 轻量图表集成

TradingView 图表库需要特定格式的数据接口：

```python
# schemas/tradingview.py

class TVConfig(BaseModel):
    """TradingView 配置"""
    supports_search: bool = True
    supports_group_request: bool = False
    supported_resolutions: List[str] = ["D", "W", "M"]
    supports_marks: bool = False
    supports_timescale_marks: bool = False

class TVSymbolInfo(BaseModel):
    """标的详情"""
    name: str
    full_name: str           # 如 "NASDAQ:AAPL"
    description: str
    type: str                # stock/crypto/forex
    session: str = "24x7"    # 交易时段
    timezone: str = "UTC"
    ticker: str
    minmov: float = 1.0
    pricescale: int = 100
    has_intraday: bool = False
    supported_resolutions: List[str]

class TVHistoryData(BaseModel):
    """历史数据格式"""
    s: str                   # 状态: "ok" | "error"
    t: List[int]             # 时间戳数组
    o: List[float]           # open
    h: List[float]           # high
    l: List[float]           # low
    c: List[float]           # close
    v: List[float]           # volume
```

---

## 定时更新调度

```python
# services/scheduler_service.py

class SchedulerService:
    """每日定时更新服务"""
    
    async def daily_update(self):
        """
        每日执行：
        1. 获取所有活跃的关注列表
        2. 提取所有唯一标的
        3. 按数据源分组并发更新
        4. 更新所有活跃指标
        5. 记录更新日志
        """
        # 1. 获取待更新标的
        assets = await self._get_active_assets()
        
        # 2. 按数据源分组
        grouped = defaultdict(list)
        for asset in assets:
            grouped[asset.data_source].append(asset)
        
        # 3. 并发更新价格
        results = await asyncio.gather(*[
            self._update_source(source, assets)
            for source, assets in grouped.items()
        ])
        
        # 4. 更新指标
        await self._update_indicators()
        
        return self._compile_report(results)
    
    async def _update_source(self, source: str, assets: List[Asset]):
        fetcher = FETCHER_REGISTRY[source]()
        updated = 0
        failed = 0
        
        for asset in assets:
            try:
                price = await fetcher.fetch_latest(asset.source_symbol)
                await price_service.save(price)
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update {asset.id}: {e}")
                failed += 1
        
        return {"source": source, "updated": updated, "failed": failed}
```

---

## 数据库索引设计

```sql
-- 价格数据查询优化
CREATE INDEX idx_price_asset_interval_date 
ON price_data(asset_id, interval, date);

-- 最新价格查询
CREATE INDEX idx_price_asset_timestamp 
ON price_data(asset_id, timestamp DESC);

-- 指标值查询
CREATE INDEX idx_indicator_date 
ON indicator_values(indicator_id, date DESC);

-- 关注列表查询
CREATE INDEX idx_watchlist_asset 
ON watchlist_assets(watchlist_id, asset_id);
```

---

## MVP 开发顺序

**Phase 1 - 基础骨架**
- [ ] 数据库模型
- [ ] FastAPI 项目结构
- [ ] 基础 CRUD API

**Phase 2 - 标的与搜索**
- [ ] Fetcher 基类 + Yahoo Finance 实现
- [ ] 跨源搜索 API
- [ ] 关注列表功能

**Phase 3 - 价格数据**
- [ ] 价格采集与存储
- [ ] TradingView 数据接口
- [ ] 历史数据查询

**Phase 4 - 指标系统**
- [ ] 指标模板基类
- [ ] MA200 指标实现
- [ ] 恐惧贪婪指数采集

**Phase 5 - 自动化**
- [ ] APScheduler 定时任务
- [ ] 更新日志与监控
- [ ] 前端对接
