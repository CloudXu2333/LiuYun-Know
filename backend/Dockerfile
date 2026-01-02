# ====================================
# 后端多阶段构建 Dockerfile
# ====================================

# 阶段1: 基础环境
FROM python:3.10-slim as base

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    # GCC 编译器（用于编译某些 Python 包）
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 阶段2: 依赖安装
FROM base as dependencies

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 阶段3: 最终镜像
FROM base as final

# 重置 ENTRYPOINT（基础镜像可能有默认的 entrypoint）
ENTRYPOINT []

# 复制已安装的依赖
COPY --from=dependencies /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/sqlite /app/data/uploads /app/data/temp

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()" || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
