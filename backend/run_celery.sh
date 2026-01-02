#!/bin/bash

# ========================================
# LiuYun-Know Celery Worker
# Linux 启动脚本
# ========================================

echo "Starting Celery Worker..."
echo ""
echo "Multi-worker mode with Redis distributed lock:"
echo "   - Multiple workers can run simultaneously"
echo "   - Same knowledge base tasks are processed sequentially (via Redis lock)"
echo "   - Different knowledge base tasks can be processed in parallel"
echo ""
echo "Usage:"
echo "   ./run_celery.sh           - Start one worker"
echo "   ./run_celery.sh 3         - Start 3 workers"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
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
python -c "import celery" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERROR] Celery not installed!"
    echo "Installing dependencies from Tsinghua mirror..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies!"
        exit 1
    fi
fi

# 获取 worker 数量
NUM_WORKERS=${1:-1}

if [ "$NUM_WORKERS" -eq 1 ]; then
    # 启动单个 worker
    echo "Starting 1 worker..."
    echo ""
    celery -A app.core.celery_app worker --loglevel=info --pool=solo
else
    # 启动多个 workers
    echo "Starting $NUM_WORKERS workers..."
    echo ""

    for ((i=1; i<=NUM_WORKERS; i++)); do
        worker_name="worker${i}"
        echo "Starting worker: $worker_name"

        # 在后台启动 worker
        celery -A app.core.celery_app worker \
            --loglevel=info \
            --pool=solo \
            -n ${worker_name}@%h \
            >> logs/celery_${worker_name}.log 2>&1 &

        # 记录进程 ID
        worker_pids[$i]=$!
        echo "Worker $worker_name started (PID: ${worker_pids[$i]})"
    done

    echo ""
    echo "========================================"
    echo "Started $NUM_WORKERS workers in background"
    echo "========================================"
    echo ""
    echo "Log files:"
    for ((i=1; i<=NUM_WORKERS; i++)); do
        echo "  - logs/celery_worker${i}.log"
    done
    echo ""
    echo "To stop all workers, run:"
    echo "  pkill -f 'celery.*worker'"
    echo ""
    echo "Or stop individual workers by PID:"
    for ((i=1; i<=NUM_WORKERS; i++)); do
        echo "  kill ${worker_pids[$i]}  # worker${i}"
    done
    echo ""

    # 保持脚本运行，等待用户中断
    trap "echo ''; echo 'Stopping all workers...'; pkill -f 'celery.*worker'; exit 0" INT TERM

    # 等待所有 worker 进程
    for pid in "${worker_pids[@]}"; do
        wait $pid 2>/dev/null
    done
fi