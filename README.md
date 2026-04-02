# 数据终端

统一数据采集与管理系统，支持多数据源价格获取、指标计算和 API 服务。

## 功能特性

- 🔍 **标的搜索** - 跨数据源实时搜索
- 📊 **价格数据** - 日K数据自动采集与存储
- ⭐ **关注列表** - 标的管理与自动更新
- 📈 **指标系统** - 可扩展的指标模板（MA200、估值分档等）
- 🎯 **市场指标** - 恐慌贪婪指数、VIX 等
- 🔌 **多数据源** - Yahoo Finance、Binance、AKShare 等

## 快速开始

### 1. 安装依赖

```bash
cd data-terminal/backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. 初始化数据库

```bash
alembic upgrade head
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

### 4. 添加标的并更新数据

```bash
# 添加 BTC 标的
curl -X POST http://localhost:8000/api/v1/assets \
  -H "Content-Type: application/json" \
  -d '{
    "id": "BTC-USD",
    "symbol": "BTC",
    "name": "Bitcoin USD",
    "asset_type": "crypto",
    "data_source": "yfinance",
    "source_symbol": "BTC-USD"
  }'

# 触发价格更新
curl -X POST http://localhost:8000/api/v1/update?asset_id=BTC-USD

# 查询价格
curl http://localhost:8000/api/v1/prices?asset_id=BTC-USD&start=2025-01-01&end=2025-12-31
```

## 项目结构

```
data-terminal/
├── backend/
│   ├── app/
│   │   ├── core/          # 配置、数据库
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── schemas/       # Pydantic 模型
│   │   ├── api/           # API 路由
│   │   ├── fetchers/      # 数据获取器
│   │   └── main.py        # FastAPI 入口
│   ├── data/              # 数据存储
│   ├── tests/             # 测试
│   └── pyproject.toml     # Python 项目配置
├── docs/                  # 文档
```

## 开发计划

详见 [docs/ROADMAP.md](docs/ROADMAP.md)

## License

MIT
