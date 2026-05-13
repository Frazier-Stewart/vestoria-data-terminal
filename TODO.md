# TODO — feature/new-indicators 分支

> 记录本次修改内容和待解决问题。

---

## ✅ 已完成

### 1. 新增波动率指标
- **VXN** — 纳斯达克100波动率指数 (`^VXN`)
- **VXD** — 道琼斯波动率指数 (`^VXD`)
- **OVX** — 原油波动率指数 (`^OVX`)
- **GVZ** — 黄金波动率指数 (`^GVZ`)
- VIX 从独立 `vix.py` 合并到 `volatility_indices.py` 统一管理

### 2. MA200 → MA200W（200周均线）
- 计算逻辑从日数据 rolling 改为：日数据 resample 到周 → 200 周滚动均线 → forward-fill 回日级别
- 指标名称统一改为 "200周均线偏离度"

### 3. 后端 API 增强
- `POST /api/v1/indicators/{id}/recalculate` — 清除旧值，按指定时间范围重新计算并保存
- `GET /api/v1/indicators/{id}/price-data-check` — 检查关联资产价格数据是否满 6 年

### 4. 前端 IndicatorDetail 重构
- 时间窗口选择：1月 / 3月 / 6月 / 1年 / 全部
- "重新计算"按钮（调用 recalculate API）
- 数据不满 6 年时顶部显示红色警告条 + "补充数据"按钮
- 增补数据弹窗（调用 `prices/backfill-range`）

### 5. 工程化
- `uv.lock` 加入 `.gitignore` 并从 git tracking 移除
- `run_service/start_data_terminal.sh` 开发模式启动脚本（含本地 socks5 代理配置）
- 创建 `feature/new-indicators` 分支并提交

---

## ⚠️ 已知问题

### 1. price-data-check 缺少 gap 检测（高优先级）
- **现状**：只判断总天数是否 >= 6 年，不检查中间是否有断档
- **影响**：BTCUSDT 曾经出现 "总天数够但中间缺了 2024 全年"，导致重新计算失败
- **修复方向**：增加最大连续数据区间检测，若连续区间 < 6 年也标记为 `needs_backfill`

### 2. MA200W 对数据连续性要求过高
- **现状**：`rolling(window=200, min_periods=200)` 要求 200 周完全连续无缺口
- **影响**：一旦价格数据有 gap（哪怕只缺 1 周），该 gap 前后所有周均线都是 NaN
- **修复方向**：
  - 方案 A：`dropna()` 后再 rolling，允许用非连续的周计算
  - 方案 B：用日数据的 1000 日滚动均线作为 200 周均线的近似替代
  - 方案 C：降低 `min_periods` 到 150 或 100，允许部分缺失

### 3. 大范围 backfill 可能不完整
- **现状**：用户点击"补充数据"后，API 声称成功但部分年份可能缺失
- **案例**：BTCUSDT 补 6 年数据时，2024 年全年缺失
- **修复方向**：backfill 完成后自动做一次 gap-check，若有缺口提示用户再次补充

### 4. Dashboard "活跃指标"写死为 3
- **现状**：`Dashboard.tsx` 中 `value={3}` 硬编码
- **修复方向**：改为从 `/api/v1/indicators` 动态获取数量

### 5. 后端 API 需认证，后台任务体验不佳
- **现状**：所有 `/api/v1/*` 路由都需要 Bearer token
- **影响**：重新计算、补充数据等操作若 token 过期会 401 跳转登录页
- **修复方向**：考虑给特定操作增加更长的 token 有效期，或在操作前自动刷新 token

### 6. 前端构建警告
- 无（当前使用 Vite dev server，未发现明显 warning）

---

## 📋 下一步建议

1. **修复 price-data-check gap 检测** — 避免"总天数够但算不出"的困惑
2. **优化 MA200W 容错性** — 允许部分缺失数据，或提供降级计算方案
3. **Dashboard 指标数动态化** — 小改动，提升体验
4. **考虑增加更多常用指标**：
   - RSI（相对强弱指数）
   - MACD
   - 布林带 (BOLL)
   - 夏普比率等
