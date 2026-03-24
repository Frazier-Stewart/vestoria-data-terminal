# Data Terminal - 当前系统架构

> 最后更新: 2026-03-24 (Phase 3 完成)

---

## 系统概述

数据终端是一个金融数据采集与指标计算系统，支持多标的资产管理、历史价格数据维护、以及可扩展的指标计算引擎。

### 核心能力

| 功能 | 状态 | 说明 |
|------|------|------|
| 资产管理 | ✅ | 添加/查询标的 (BTC, SPY等) |
| 价格数据 | ✅ | OHLCV 存储与查询，支持增量更新 |
| 指标系统 | ✅ | 模板化指标 + 处理器注册表架构 |
| 历史回填 | ✅ | 批量拉取历史数据 (yfinance) |
| 自动更新 | ✅ | 手动/增量更新价格数据 |
| 指标计算 | ✅ | 批量/实时指标计算 |
| CLI 工具 | ✅ | 命令行管理工具 |
| HTTP API | ✅ | FastAPI RESTful 接口 |

---

## 目录结构

```
data-terminal/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── cli.py                  # 命令行工具
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── assets.py       # 资产 API
│   │   │       ├── indicators.py   # 指标 API
│   │   │       ├── prices.py       # 价格数据 API
│   │   │       └── update.py       # 更新操作 API
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # 配置管理
│   │   │   └── database.py         # 数据库连接 (SQLite)
│   │   │
│   │   ├── fetchers/               # 数据源适配器
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # 数据获取基类
│   │   │   ├── registry.py         # 获取器注册表
│   │   │   └── yfinance_fetcher.py # Yahoo Finance 实现
│   │   │
│   │   ├── indicators/             # 指标处理器
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # 指标基类 (BaseIndicatorProcessor)
│   │   │   ├── registry.py         # 处理器注册表 (@register_processor)
│   │   │   ├── btc_fear_greed.py   # BTC 恐慌贪婪指数 (alternative.me)
│   │   │   ├── vix.py              # VIX 波动率指数 (yfinance ^VIX)
│   │   │   └── ma200.py            # MA200 均线偏离度 (本地计算)
│   │   │
│   │   ├── models/                 # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── asset.py            # 资产模型
│   │   │   ├── price_data.py       # 价格数据模型
│   │   │   └── indicator.py        # 指标模型
│   │   │
│   │   ├── schemas/                # Pydantic 模式
│   │   │   ├── __init__.py
│   │   │   ├── asset.py
│   │   │   ├── price.py
│   │   │   └── indicator.py
│   │   │
│   │   └── services/               # 核心服务
│   │       ├── backfill.py         # 历史数据回填
│   │       ├── price_scheduler.py  # 价格更新调度
│   │       └── indicator_scheduler.py # 指标计算调度
│   │
│   ├── data/
│   │   └── fund_manager.db         # SQLite 数据库
│   │
│   ├── .venv/                      # Python 虚拟环境
│   └── requirements.txt
│
├── docs/                           # 文档
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_V2.md
│   ├── CURRENT_ARCHITECTURE.md     # 本文档
│   ├── PRODUCT_SPEC.md
│   └── ROADMAP.md
│
└── README.md
```

---

## 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                      用户接口层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   CLI 工具    │  │  FastAPI     │  │   Python API     │  │
│  │  (cli.py)    │  │  (main.py)   │  │  (services/*)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API 路由层                              │
│         (api/v1/assets.py, indicators.py, prices.py)        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      业务服务层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Backfill   │  │   Price      │  │   Indicator      │  │
│  │  Service     │  │  Scheduler   │  │   Scheduler      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      核心引擎层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Indicator   │  │   Fetcher    │  │     Models       │  │
│  │  Processors  │  │  (yfinance)  │  │   (SQLAlchemy)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│                    SQLite (fund_manager.db)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据模型

### 1. Asset (资产)

```python
class Asset(Base):
    id: str              # 唯一标识，如 "BTC-USD"
    symbol: str          # 代码，如 "BTC"
    name: str            # 名称，如 "Bitcoin USD"
    asset_type: str      # 类型: crypto/stock/etf/commodity/fund/index
    exchange: str        # 交易所，如 "NASDAQ"
    currency: str        # 计价货币，如 "USD"
    country: str         # 所属市场，如 "US"
    is_active: bool      # 是否可交易
```

### 2. PriceData (价格数据)

```python
class PriceData(Base):
    id: int
    asset_id: str        # 关联 Asset
    timestamp: datetime  # 精确时间
    date: date           # 日期（方便查询）
    interval: str        # 周期: 1d/1w/1m
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str          # 数据来源
```

### 3. IndicatorTemplate (指标模板)

```python
class IndicatorTemplate(Base):
    id: str              # 模板标识，如 "btc_fear_greed"
    name: str            # 显示名称
    description: str     # 描述
    category: str        # 分类: sentiment/volatility/trend/macro
    processor_class: str # 处理器类名
    default_params: dict # 默认参数 JSON
    output_fields: dict  # 输出字段定义
    level_config: dict   # 分档配置
```

### 4. Indicator (指标实例)

```python
class Indicator(Base):
    id: int
    name: str            # 显示名称
    template_id: str     # 关联模板
    asset_id: str        # 关联标的
    params: dict         # 实例参数
    is_active: bool
    last_calculated_at: datetime
```

### 5. IndicatorValue (指标数值)

```python
class IndicatorValue(Base):
    id: int
    indicator_id: int
    date: date
    timestamp: datetime
    value: float
    value_text: str      # 文本描述
    grade: int           # 档位 (1-5)
    grade_label: str     # 档位标签
    extra_data: dict     # 额外数据
    source: str
```

---

## 指标处理器架构

### 基类设计

```python
class BaseIndicatorProcessor(ABC):
    """指标处理器基类"""
    
    def __init__(self, params: dict = None):
        self.params = params or {}
    
    @abstractmethod
    async def calculate(self, asset_id: str, start: date, end: date) -> List[IndicatorResult]:
        """计算指定日期范围的指标值"""
        pass
    
    @abstractmethod
    async def calculate_latest(self, asset_id: str) -> Optional[IndicatorResult]:
        """计算最新指标值"""
        pass
    
    def classify_grade(self, value: float) -> Tuple[int, str]:
        """分档：返回 (grade, label)"""
        pass
```

### 注册装饰器

```python
# indicators/registry.py
_PROCESSOR_REGISTRY = {}

def register_processor(template_id: str):
    """注册指标处理器"""
    def decorator(cls):
        _PROCESSOR_REGISTRY[template_id] = cls
        return cls
    return decorator

def create_processor(template_id: str, params: dict = None):
    """创建处理器实例"""
    processor_class = _PROCESSOR_REGISTRY.get(template_id)
    if processor_class:
        return processor_class(params)
    return None
```

### 内置指标

| 指标 | 模板ID | 数据源 | 说明 |
|------|--------|--------|------|
| BTC 恐慌贪婪 | `btc_fear_greed` | alternative.me | 0-100 分档评级 |
| VIX 波动率 | `vix` | Yahoo Finance ^VIX | 6档波动评级 |
| MA200 均线 | `ma200` | 本地 price_data | 200日均线偏离度 |

---

## API 接口

### 资产管理
```
GET    /api/v1/assets              # 资产列表
POST   /api/v1/assets              # 创建资产
GET    /api/v1/assets/{id}         # 资产详情
```

### 价格数据
```
GET    /api/v1/prices/{asset_id}   # 价格历史
GET    /api/v1/prices/{id}/latest  # 最新价格
```

### 指标
```
GET    /api/v1/indicators/templates        # 指标模板列表
GET    /api/v1/indicators/templates/{id}   # 模板详情
POST   /api/v1/indicators                  # 创建指标实例
GET    /api/v1/indicators                  # 指标实例列表
GET    /api/v1/indicators/{id}             # 指标详情
POST   /api/v1/indicators/{id}/calculate   # 触发计算
GET    /api/v1/indicators/{id}/values      # 指标数值历史
GET    /api/v1/indicators/{id}/latest      # 最新指标值
PUT    /api/v1/indicators/{id}             # 更新指标
DELETE /api/v1/indicators/{id}             # 删除指标
```

---

## CLI 命令

```bash
cd backend
source .venv/bin/activate

# 查看系统状态
python -m app.cli status

# 回填历史数据（默认过去一年）
python -m app.cli fill-history
python -m app.cli fill-history --start 2024-01-01 --end 2026-03-24
python -m app.cli fill-history --assets BTC-USD,SPY

# 增量更新价格
python -m app.cli update-prices
python -m app.cli update-prices --assets BTC-USD --lookback 5

# 重新计算指标
python -m app.cli recalc                    # 全部指标
python -m app.cli recalc --indicator 1      # 单个指标
```

---

## 启动方式

### 1. CLI 模式（当前主要使用）
```bash
cd backend
source .venv/bin/activate
python -m app.cli status
```

### 2. HTTP API 模式
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 访问文档
open http://localhost:8000/docs
```

### 3. Python 代码调用
```python
from app.services.price_scheduler import run_price_update
from app.services.indicator_scheduler import calculate_all_indicators

# 更新价格
run_price_update()

# 计算所有指标
calculate_all_indicators()
```

---

## 当前数据状态

截至 2026-03-24:

| 资产 | 数据条数 | 日期范围 | 最新价格 |
|------|---------|---------|---------|
| BTC-USD | 366 | 2025-03-24 ~ 2026-03-24 | 70828.74 |
| SPY | 251 | 2025-07-08 ~ 2026-03-24 | 655.38 |

| 指标 | 当前值 | 档位 |
|------|--------|------|
| BTC 恐慌贪婪 | 11 | 极度恐惧 |
| VIX | 26.11 | 波动加剧 |

---

## 后续规划

### Phase 4 - Watch List & 自动化
- [ ] 关注列表 (Watchlist) 功能
- [ ] 每日定时自动更新
- [ ] 指标异常告警

### Phase 5 - 前端与可视化
- [ ] Dashboard 数据面板
- [ ] TradingView 图表集成
- [ ] 指标历史走势

---

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **数据源**: yfinance (Yahoo Finance)
- **指标计算**: pandas + numpy
- **CLI**: argparse
- **部署**: 本地运行 / 可扩展至 Docker
