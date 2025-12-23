#!/bin/bash

# 项目初始化脚本

echo "🎉 欢迎使用 LiuYun-Know！"
echo "================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装，请先安装 Python 3.12+"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"
echo "✅ Node.js 版本: $(node --version)"
echo ""

# 设置后端
echo "📦 设置后端环境..."
cd backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 后端依赖安装完成"

# 复制环境变量文件
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  已创建 .env 文件，请编辑配置必要的 API Key"
fi

cd ..

# 设置前端
echo ""
echo "📦 设置前端环境..."
cd frontend

npm install
echo "✅ 前端依赖安装完成"

cd ..

# 创建数据目录
echo ""
echo "📁 创建数据目录..."
mkdir -p data/sqlite
mkdir -p data/minio
mkdir -p data/chroma
mkdir -p data/neo4j
echo "✅ 数据目录创建完成"

# 赋予脚本执行权限
chmod +x backend/run_dev.sh
chmod +x frontend/run_dev.sh

echo ""
echo "================================"
echo "✅ 项目初始化完成！"
echo ""
echo "📝 后续步骤："
echo "1. 编辑 backend/.env 文件，配置必要的 API Key"
echo "2. 启动 Docker 服务: docker-compose up -d"
echo "3. 启动后端: cd backend && ./run_dev.sh"
echo "4. 启动前端: cd frontend && ./run_dev.sh"
echo ""
echo "🌐 访问地址："
echo "  - 前端: http://localhost:5173"
echo "  - 后端 API: http://localhost:8000"
echo "  - API 文档: http://localhost:8000/docs"
echo ""
echo "祝使用愉快！🎊"

