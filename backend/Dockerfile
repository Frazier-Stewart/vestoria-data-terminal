# 后端 Dockerfile - 使用 uv 管理依赖

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 复制应用代码（包括 pyproject.toml 依赖的 app 包）
COPY . .

# 使用 uv 安装依赖
RUN uv pip install --system -e .
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
