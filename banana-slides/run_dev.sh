#!/bin/bash
# Banana-Slides Development Server
# Linux/Mac 启动脚本 - 后台启动前后端

echo "========================================"
echo "Starting Banana-Slides Backend & Frontend"
echo "========================================"
echo ""

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
echo "Checking dependencies..."
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# 创建日志目录
mkdir -p logs

echo ""
echo "========================================"
echo "Starting Backend at http://0.0.0.0:5001"
echo "Starting Frontend at http://0.0.0.0:5174"
echo "Backend logs: banana-slides/logs/backend.log"
echo "Frontend logs: banana-slides/logs/frontend.log"
echo "========================================"
echo ""

# 启动后端服务器 (后台运行,监听 0.0.0.0:5001,日志保存到 logs/backend.log)
cd backend
FLASK_RUN_HOST=0.0.0.0 PORT=5001 nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID on 0.0.0.0:5001"
cd ..

# 等待后端启动
sleep 3

# 启动前端服务器 (后台运行,监听 0.0.0.0:5174,日志保存到 logs/frontend.log)
cd frontend
nohup npm run dev -- --host 0.0.0.0 --port 5174 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID on 0.0.0.0:5174"
cd ..

# 保存 PID 到文件
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "[SUCCESS] Servers started in background!"
echo "Backend:  http://0.0.0.0:5001 (IPv4, PID: $BACKEND_PID)"
echo "Frontend: http://0.0.0.0:5174 (IPv4, PID: $FRONTEND_PID)"
echo ""
echo "To stop servers, run stop_dev.sh"
echo "To view logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo ""