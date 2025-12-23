#!/bin/bash

# 前端开发环境启动脚本

echo "🚀 启动 LiuYun-Know 前端服务..."

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 启动开发服务器
echo "🌟 启动 Vite 开发服务器..."
npm run dev

