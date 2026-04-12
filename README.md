# Data Terminal

统一数据采集与管理系统 - 支持股票、加密货币、大宗商品等多种资产类型的数据终端。

## 快速启动（Docker）

### 1. 环境准备

```bash
cd projects/data-terminal

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，按需修改配置
nano .env
```

### 2. 启动服务

```bash
# 构建并启动（首次运行）
docker compose up -d --build

# 仅启动（已构建过镜像）
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 停止并删除数据卷（谨慎使用）
docker compose down -v
```

### 3. 访问应用

- **前端界面**: http://localhost:20261
- **API 文档**: http://localhost:20261/docs
- **健康检查**: http://localhost:20261/health

### 4. 数据管理

数据文件存储在 `./data` 目录（可通过 `.env` 中的 `DATA_PATH` 修改）：

```bash
# 查看数据目录
ls -la ./data

# 备份数据
cp -r ./data ./data.backup.$(date +%Y%m%d)

# 恢复数据
cp -r ./data.backup.20250412 ./data
```

## 开发模式

### 后端开发

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端开发

```bash
cd frontend
npm run dev
```

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `APP_NAME` | Data Terminal | 应用名称 |
| `DEBUG` | false | 调试模式 |
| `DATABASE_URL` | sqlite:////app/data/data_terminal.db | 数据库路径 |
| `API_V1_PREFIX` | /api/v1 | API 前缀 |
| `SCHEDULER_ENABLED` | true | 定时任务开关 |
| `PROXY_URL` | (空) | 代理服务器地址 |
| `DATA_PATH` | ./data | 数据目录挂载路径 |
| `FRONTEND_PORT` | 20261 | 前端服务端口 |

## 项目结构

```
data-terminal/
├── backend/           # FastAPI 后端
│   ├── app/          # 应用代码
│   ├── data/         # 数据文件
│   ├── Dockerfile    # 后端镜像构建
│   └── pyproject.toml
├── frontend/          # React + Vite 前端
│   ├── src/          # 源代码
│   ├── Dockerfile    # 前端镜像构建
│   └── nginx.conf    # Nginx 配置
├── data_explore/      # 数据探索脚本
├── docs/             # 文档
├── docker-compose.yml # Docker 编排配置
└── .env.example      # 环境变量示例
```

## 主要功能

- 📊 **多资产支持**: 股票 (Equities)、加密货币 (Crypto)、大宗商品 (Commodities)
- 📈 **技术指标**: MA200、BTC 恐慌贪婪指数、VIX 等
- 🔍 **板块行业**: GICS 板块分类、行业龙头筛选
- ⭐ **自选追踪**: 自定义追踪列表
- 🔄 **自动更新**: 定时任务自动采集数据
- 🐳 **Docker 部署**: 一键启动，易于维护
