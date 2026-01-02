#!/bin/bash

# ========================================
# LiuYun-Know Backend Development Server
# Linux 启动脚本
# ========================================

echo "========================================"
echo "Starting LiuYun-Know Backend Server"
echo "========================================"
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please create .env file based on CONFIG_GUIDE.md"
    echo ""
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found."
    echo "Creating virtual environment..."
    python -m venv venv
    echo "Virtual environment created successfully."
    echo ""
fi

# 激活虚拟环境（如果尚未激活）
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment already activated: $VIRTUAL_ENV"
fi

# 检查依赖
echo "Checking dependencies..."
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Dependencies not installed!"
    echo "Installing dependencies from Tsinghua mirror..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies!"
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "Server starting at http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# 启动服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000