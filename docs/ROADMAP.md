# Data Terminal - 开发路线图

> 最后更新: 2026-03-24

---

## 已完成 ✅

### Phase 1：基础骨架
- [x] 项目结构初始化 (FastAPI + SQLAlchemy + SQLite)
- [x] 数据库模型 (Asset, PriceData)
- [x] 基础 API (assets, prices)
- [x] Yahoo Finance Fetcher
- [x] 数据流验证

### Phase 2：指标系统
- [x] 指标模型 (IndicatorTemplate, Indicator, IndicatorValue)
- [x] 指标计算引擎 (BaseIndicatorProcessor + 注册表)
- [x] 内置指标实现:
  - [x] BTC 恐慌贪婪指数 (alternative.me)
  - [x] VIX 波动率 (Yahoo Finance)
  - [x] MA200 均线偏离度 (本地计算)
- [x] 指标 API (CRUD + calculate + values)

### Phase 3：数据引擎与自动化
- [x] 历史数据回填 (backfill.py)
- [x] 增量更新机制 (price_scheduler.py)
- [x] 指标计算调度 (indicator_scheduler.py)
- [x] CLI 管理工具 (cli.py)
- [x] 过去一年数据填充 (BTC: 366条, SPY: 251条)

---

## 进行中/待开发 🚧

### Phase 4：Watch List & 每日自动化
- [ ] Watchlist 关注列表模型
- [ ] 添加/移除标的到关注列表
- [ ] 关注列表价格聚合查询
- [ ] APScheduler 定时任务集成
- [ ] 每日自动更新价格
- [ ] 更新日志与监控

### Phase 5：多数据源与搜索
- [ ] Fetcher 搜索接口 (search, list_assets)
- [ ] Binance 数据源 (加密货币)
- [ ] AKShare 数据源 (A股)
- [ ] 跨源搜索 API
- [ ] 数据源浏览接口

### Phase 6：前端与可视化
- [ ] TradingView 轻量图表集成
  - [ ] /tv/config
  - [ ] /tv/symbols
  - [ ] /tv/history
- [ ] Dashboard 数据面板
- [ ] 标的搜索页
- [ ] 价格图表页
- [ ] 关注列表页
- [ ] 指标展示页

### Phase 7：监控与告警
- [ ] 指标档位变化通知
- [ ] 数据更新失败告警
- [ ] 系统健康监控

---

## 系统当前状态

### 数据状态 (2026-03-24)
| 资产 | 数据量 | 最新日期 | 最新价格 |
|------|--------|---------|---------|
| BTC-USD | 366条 | 2026-03-24 | 70828.74 |
| SPY | 251条 | 2026-03-24 | 655.38 |

### 指标状态
| 指标 | 当前值 | 档位 | 数据来源 |
|------|--------|------|---------|
| BTC 恐慌贪婪 | 11 | 极度恐惧 | alternative.me |
| VIX | 26.11 | 波动加剧 | Yahoo Finance |

---

## 使用方式

### CLI 命令
```bash
cd backend
source .venv/bin/activate

# 查看状态
python -m app.cli status

# 回填历史数据
python -m app.cli fill-history

# 增量更新价格
python -m app.cli update-prices

# 重新计算指标
python -m app.cli recalc
```

### HTTP API
```bash
# 启动服务
uvicorn app.main:app --port 8000

# 访问文档
open http://localhost:8000/docs
```

---

## 下一步优先级

1. **Phase 4**: 实现 Watchlist 和每日自动更新 (高优先级)
2. **Phase 5**: 添加更多数据源 (中优先级)
3. **Phase 6**: 前端可视化 (中优先级)
4. **Phase 7**: 监控告警 (低优先级)
