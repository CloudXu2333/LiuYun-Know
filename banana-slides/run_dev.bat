@echo off
REM Banana-Slides Development Server
REM Windows 启动脚本 - 后台启动前后端

echo ========================================
echo Starting Banana-Slides Backend & Frontend
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
echo Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [ERROR] Dependencies not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM 创建日志目录
if not exist "logs" mkdir logs

echo.
echo ========================================
echo Starting Backend at http://0.0.0.0:5001
echo Starting Frontend at http://0.0.0.0:5174
echo Backend logs: banana-slides\logs\backend.log
echo Frontend logs: banana-slides\logs\frontend.log
echo ========================================
echo.

REM 启动后端服务器 (后台运行,监听 0.0.0.0:5001,日志保存到 logs/backend.log)
cd backend
start /B cmd /C "set FLASK_RUN_HOST=0.0.0.0 && set PORT=5001 && python app.py > ..\logs\backend.log 2>&1"
cd ..

REM 等待后端启动
timeout /t 3 /nobreak >nul

REM 启动前端服务器 (后台运行,监听 0.0.0.0:5174,日志保存到 logs/frontend.log)
cd frontend
start /B cmd /C "npm run dev -- --host 0.0.0.0 --port 5174 > ..\logs\frontend.log 2>&1"
cd ..

echo.
echo [SUCCESS] Servers started in background!
echo Backend:  http://0.0.0.0:5001 (IPv4)
echo Frontend: http://0.0.0.0:5174 (IPv4)
echo.
echo To stop servers, run stop_dev.bat
echo To view logs: type logs\backend.log or logs\frontend.log
echo.