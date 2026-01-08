#!/bin/bash
# 停止 LiuYun-Know 开发服务器

echo "========================================"
echo "Stopping LiuYun-Know Servers"
echo "========================================"
echo ""

# 从 PID 文件读取并停止进程
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    echo "Stopping backend server (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    rm logs/backend.pid
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    echo "Stopping frontend server (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    rm logs/frontend.pid
fi

# 如果 PID 文件不存在,尝试通过端口停止
echo "Checking for processes on ports..."
pkill -f "uvicorn.*8001" 2>/dev/null
pkill -f "vite.*5173" 2>/dev/null

echo ""
echo "[SUCCESS] All servers stopped!"
echo ""